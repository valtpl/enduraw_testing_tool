"""
MongoDB Service - Read-only connection to the Enduraw DB for user lookup.

URI resolution order:
  1. Value passed explicitly to connect(uri=...)
  2. Environment variable  MONGO_URI
  3. .env file at project root  (MONGO_URI=...)
  4. mongo_config.json (legacy, for local convenience only)
"""
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path


def _read_dotenv(base_path: str) -> Dict[str, str]:
    """Read a simple .env file (KEY=VALUE per line). No external deps."""
    env_file = os.path.join(base_path, ".env")
    result: Dict[str, str] = {}
    if not os.path.isfile(env_file):
        return result
    try:
        with open(env_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    result[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return result


class MongoService:
    """
    Manages the connection to MongoDB and provides helpers for
    reading / writing user documents.
    """

    # Persistent config file for the URI (next to sessions/)
    _CONFIG_FILENAME = "mongo_config.json"

    def __init__(self, base_path: str):
        self.base_path = base_path
        self._client = None
        self._db = None
        self._collection = None
        self.uri: str = ""
        self.db_name: str = "enduraw"
        self.collection_name: str = "completeUser"
        self.is_connected: bool = False
        self._users_cache: List[Dict[str, Any]] = []

        # Try to load saved URI
        self._load_config()

    # ------------------------------------------------------------------ #
    #  Config persistence                                                 #
    # ------------------------------------------------------------------ #
    def _config_path(self) -> str:
        return os.path.join(self.base_path, self._CONFIG_FILENAME)

    def _load_config(self):
        """Load MongoDB connection settings.

        Priority: env var > .env file > mongo_config.json (legacy).
        """
        # 1. Environment variable
        env_uri = os.environ.get("MONGO_URI", "")

        # 2. .env file at project root
        if not env_uri:
            dotenv = _read_dotenv(self.base_path)
            env_uri = dotenv.get("MONGO_URI", "")

        if env_uri:
            self.uri = env_uri
            # Also pick db_name / collection from env if provided
            self.db_name = os.environ.get("MONGO_DB", "") or _read_dotenv(self.base_path).get("MONGO_DB", "") or self.db_name
            self.collection_name = os.environ.get("MONGO_COLLECTION", "") or _read_dotenv(self.base_path).get("MONGO_COLLECTION", "") or self.collection_name
            return

        # 3. Legacy JSON config (local convenience)
        path = self._config_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.uri = cfg.get("uri", "")
                self.db_name = cfg.get("db_name", "enduraw")
                self.collection_name = cfg.get("collection_name", "completeUser")
            except Exception:
                pass

    def _save_config(self):
        path = self._config_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "uri": self.uri,
                    "db_name": self.db_name,
                    "collection_name": self.collection_name,
                }, f, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Connection                                                         #
    # ------------------------------------------------------------------ #
    def connect(self, uri: str = "", db_name: str = "", collection_name: str = "") -> bool:
        """
        Connect (or reconnect) to MongoDB.

        Returns True on success, raises on failure.
        """
        try:
            from pymongo import MongoClient
        except ImportError:
            raise RuntimeError(
                "pymongo n'est pas installé.\n"
                "Installez-le avec : pip install pymongo"
            )

        if uri:
            self.uri = uri
        if db_name:
            self.db_name = db_name
        if collection_name:
            self.collection_name = collection_name

        if not self.uri:
            raise ValueError("URI MongoDB non renseigné")

        # Close previous connection if any
        self.disconnect()

        self._client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)

        # Force a server check to validate connection
        self._client.admin.command("ping")

        self._db = self._client[self.db_name]
        self._collection = self._db[self.collection_name]
        self.is_connected = True

        # Persist working config
        self._save_config()

        # Pre-load users cache
        self._refresh_cache()

        return True

    def disconnect(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._db = None
        self._collection = None
        self.is_connected = False
        self._users_cache.clear()

    # ------------------------------------------------------------------ #
    #  Users cache                                                        #
    # ------------------------------------------------------------------ #
    def _refresh_cache(self):
        """Load all users into memory (lightweight projection)."""
        if not self._collection_ready():
            return
        try:
            cursor = self._collection.find(
                {},
                {
                    "_id": 0,
                    "email": 1,
                    "username": 1,
                    "age": 1,
                    "gender": 1,
                    "size": 1,
                    "weight": 1,
                    "altitude": 1,
                    "birthdate": 1,
                    "hr_max": 1,
                    "hr_min": 1,
                    "record_5k": 1,
                    "record_10k": 1,
                    "record_42k": 1,
                    "activities": 1,
                    "creation_date": 1,
                }
            )
            self._users_cache = list(cursor)
        except Exception:
            self._users_cache = []

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Return cached users list."""
        return list(self._users_cache)

    def refresh_users(self):
        """Force-refresh user cache from DB."""
        self._refresh_cache()

    # ------------------------------------------------------------------ #
    #  User lookup                                                        #
    # ------------------------------------------------------------------ #
    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find a user in the DB by email (full document).
        Returns None if not found or not connected.
        """
        if not self._collection_ready() or not email:
            return None
        try:
            doc = self._collection.find_one(
                {"email": email.lower().strip()},
                {"_id": 0, "password": 0, "stravaRefreshToken": 0}
            )
            return doc
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    #  Mapping DB user -> profile form fields                             #
    # ------------------------------------------------------------------ #
    @staticmethod
    def db_user_to_profile(user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a MongoDB user document to the profile form structure.
        Only fills fields that have a non-empty value in the DB doc.
        """
        profile: Dict[str, Any] = {}

        # Email
        if user.get("email"):
            profile["email"] = user["email"]

        # Identity
        identity: Dict[str, Any] = {}
        username = user.get("username", "")
        if username:
            parts = username.split(" ", 1)
            identity["first_name"] = parts[0] if parts else ""
            identity["last_name"] = parts[1] if len(parts) > 1 else ""
        if user.get("age") is not None:
            identity["age"] = user["age"]
        if user.get("birthdate"):
            identity["date_of_birth"] = user["birthdate"]
        # Determine primary sport from activities
        activities = user.get("activities", [])
        if activities:
            # Map DB activity names to human-readable
            sport_map = {
                "running": "Course à pied",
                "trail": "Trail",
                "cycling": "Cyclisme",
                "hiking": "Randonnée",
                "mountain_bike": "VTT",
                "e_bike": "VAE",
            }
            primary = activities[0] if activities else ""
            identity["sport_practiced"] = sport_map.get(primary, primary)
        if identity:
            profile["identity"] = identity

        # Body composition
        body: Dict[str, Any] = {}
        if user.get("size") is not None:
            body["height_cm"] = user["size"]
        if user.get("weight") is not None:
            body["current_weight"] = user["weight"]
        if body:
            profile["body_composition"] = body

        # Altitude
        if user.get("altitude") is not None:
            profile["altitude_vie_m"] = user["altitude"]

        # Equipment & tracking  (FC repos / FC max)
        equip: Dict[str, Any] = {}
        if user.get("hr_min") is not None:
            equip["min_hr_before"] = user["hr_min"]
        if user.get("hr_max") is not None:
            equip["max_hr_ever"] = user["hr_max"]
        if equip:
            profile["equipment_and_tracking"] = equip

        # History – records
        records: Dict[str, Any] = {}
        if user.get("record_5k"):
            records["5k"] = user["record_5k"]
        if user.get("record_10k"):
            records["10k"] = user["record_10k"]
        if user.get("record_42k"):
            records["marathon"] = user["record_42k"]
        history: Dict[str, Any] = {}
        if records:
            history["personal_records"] = records
        if history:
            profile["history_and_goals"] = history

        return profile

    # ------------------------------------------------------------------
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #
    def _collection_ready(self) -> bool:
        return self.is_connected and self._collection is not None
