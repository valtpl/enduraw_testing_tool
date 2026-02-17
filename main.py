"""
Enduraw Testing Tool - Entry Point
"""
import os
import sys
from pathlib import Path


def _load_dotenv(directory: Path):
    """Load a .env file into os.environ (no external dependency)."""
    env_file = directory / ".env"
    if not env_file.is_file():
        return
    with open(env_file, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)


# Determine project root
if getattr(sys, "frozen", False):
    # Running as a PyInstaller bundle — the exe sits in dist/
    _project_root = Path(sys.executable).parent
else:
    _project_root = Path(__file__).parent

# Load .env from project root so MONGO_URI is available before any import
_load_dotenv(_project_root)

# Add src/ to PYTHONPATH
src_path = _project_root / "src"
sys.path.insert(0, str(src_path))

from src.main_session import TCPDataProcessorSession


if __name__ == "__main__":
    app = TCPDataProcessorSession()
    app.mainloop()
