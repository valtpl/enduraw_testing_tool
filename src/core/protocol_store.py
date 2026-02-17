"""
Protocol Store - Persists reusable test protocol descriptions to a JSON file.
Read-only at runtime: protocols are managed through the settings dialog.
"""
import json
import os
from typing import Dict, List


_FILENAME = "protocols.json"


class ProtocolStore:
    """
    Simple JSON-backed store for named protocol descriptions.

    Data format:
    [
        {"name": "Protocole Course Paliers 1km/h", "description": "Départ à 6 km/h ..."},
        ...
    ]
    """

    def __init__(self, base_path: str):
        self._path = os.path.join(base_path, _FILENAME)
        self._protocols: List[Dict[str, str]] = []
        self._load()

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #
    def list_names(self) -> List[str]:
        """Return sorted list of protocol names."""
        return [p["name"] for p in self._protocols]

    def get_description(self, name: str) -> str:
        """Return the description for a given protocol name, or ''."""
        for p in self._protocols:
            if p["name"] == name:
                return p.get("description", "")
        return ""

    def add(self, name: str, description: str) -> bool:
        """
        Add a new protocol.  Returns False if the name already exists.
        """
        name = name.strip()
        if not name:
            return False
        if any(p["name"] == name for p in self._protocols):
            return False
        self._protocols.append({"name": name, "description": description.strip()})
        self._protocols.sort(key=lambda p: p["name"].lower())
        self._save()
        return True

    def update(self, name: str, description: str):
        """Update the description of an existing protocol."""
        for p in self._protocols:
            if p["name"] == name:
                p["description"] = description.strip()
                self._save()
                return

    def rename(self, old_name: str, new_name: str) -> bool:
        """Rename a protocol.  Returns False if new_name already exists."""
        new_name = new_name.strip()
        if not new_name or old_name == new_name:
            return False
        if any(p["name"] == new_name for p in self._protocols):
            return False
        for p in self._protocols:
            if p["name"] == old_name:
                p["name"] = new_name
                self._protocols.sort(key=lambda p: p["name"].lower())
                self._save()
                return True
        return False

    def delete(self, name: str):
        """Delete a protocol by name."""
        self._protocols = [p for p in self._protocols if p["name"] != name]
        self._save()

    # ------------------------------------------------------------------ #
    #  Persistence                                                        #
    # ------------------------------------------------------------------ #
    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._protocols = data
            except Exception:
                self._protocols = []

    def _save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._protocols, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
