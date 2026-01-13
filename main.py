"""
Enduraw Testing Tool - Entry Point
Démarrage de l'application principale
"""
import sys
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Importer et lancer l'application
from src.main_session import TCPDataProcessorSession

if __name__ == "__main__":
    app = TCPDataProcessorSession()
    app.mainloop()
