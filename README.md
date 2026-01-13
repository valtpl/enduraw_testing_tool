# Enduraw Testing Tool

Application desktop pour le traitement des données MetaLyzer XML.

## Installation

```bash
pip install -r requirements.txt
```

## Lancer l'application

```bash
python main.py
```

## Build .exe (Windows)

### Méthode automatique 
```powershell
.\scripts\build.ps1
```

Le script build automatique :
- Vérifie et installe PyInstaller si nécessaire
- Nettoie les anciens builds
- Crée l'exécutable avec toutes les options
- L'exécutable sera dans `dist/Enduraw_Testing_Tool.exe`

### Méthode manuelle
```bash
# Installer PyInstaller
pip install pyinstaller

# Build l'application
pyinstaller --onefile --windowed --name "Enduraw_Testing_Tool" --add-data "src;src" --icon=icon.ico main.py
```

Options PyInstaller :
- `--onefile` : Crée un seul fichier .exe
- `--windowed` : Pas de console (app GUI)
- `--icon=icon.ico` : Ajoute une icône personnalisée
- `--add-data "src;src"` : Inclut le dossier src dans l'exe

## Structure du projet

```
enduraw_testing_tool/
├── main.py              # Point d'entrée principal
├── requirements.txt     # Dépendances Python
├── README.md           # Documentation
├── .gitignore          # Fichiers ignorés par git
├── src/                # Code source
│   ├── main_session.py # Application principale (mode session)
│   ├── main.py        # Application mode one-shot
│   ├── config.py      # Configuration
│   ├── core/          # Logique métier
│   │   ├── models.py
│   │   ├── data_transformer.py
│   │   ├── session_manager.py
│   │   └── profile_template.py
│   ├── ui/            # Interface utilisateur
│   │   └── app_tabs.py
│   └── utils/         # Utilitaires
│       ├── xml_parser.py
│       └── json_exporter.py
├── docs/              # Documentation
├── Output/            # Fichiers de sortie générés
├── build/             # Fichiers de build PyInstaller
└── dist/              # Exécutables compilés
```
