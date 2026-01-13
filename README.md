# Enduraw Testing Tool

Application desktop pour le traitement des données MetaLyzer XML.

## Installation

```bash
pip install -r requirements.txt
```

## Lancer l'application

```bash
# Mode session 
python main_session.py

# Ancien mode
python main.py
```

## Build .exe (Windows)

```bash
# Installer PyInstaller
pip install pyinstaller

# Build l'application
pyinstaller --onefile --windowed --name "Enduraw_Testing_Tool" main_session.py

# L'exécutable sera dans le dossier dist/
```

### Options PyInstaller :
- `--onefile` : Crée un seul fichier .exe
- `--windowed` : Pas de console (app GUI)
- `--icon=icon.ico` : Ajouter une icône (optionnel)

## Structure

```
enduraw_testing_tool/
├── main_session.py     # Point d'entrée principal
├── main.py             # Mode one-shot
├── session_manager.py  # Gestion sessions/profils
├── data_transformer.py # Transformation données
├── xml_parser.py       # Parsing XML
└── requirements.txt    # Dépendances
```
