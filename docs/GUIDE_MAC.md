# Enduraw Testing Tool - Guide Mac

## 1. Installer Python

Ouvrir le **Terminal** (Applications > Utilitaires > Terminal) et coller :

```bash
# Installer Homebrew (gestionnaire de paquets) si pas encore fait
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installer Python 3
brew install python3

# Verifier
python3 --version
```

Si Homebrew est deja installe, passer directement a `brew install python3`.

---

## 2. Installer les dependances

Dans le Terminal, aller dans le dossier du projet :

```bash
# Remplacer le chemin par celui ou se trouve le projet sur votre Mac
cd /chemin/vers/enduraw_testing_tool

# Installer tout d'un coup
pip3 install -r requirements.txt
```

---

## 3. Configurer MongoDB

```bash
# Copier le template
cp .env.example .env

# Editer avec nano (ou n'importe quel editeur)
nano .env
```

Remplir la ligne `MONGO_URI=` avec l'URI fournie, puis sauvegarder :
- `Ctrl + O` pour sauvegarder
- `Ctrl + X` pour quitter

---

## 4. Lancer l'app (methode rapide)

```bash
cd /chemin/vers/enduraw_testing_tool
python3 main.py
```

---

## 5. Creer une vraie App Mac avec Automator

C'est la methode recommandee pour avoir une icone cliquable dans le Dock,
comme n'importe quelle application.

### Etape 1 : Ouvrir Automator

- Ouvrir **Finder**
- Aller dans **Applications**
- Ouvrir **Automator** (icone robot)

### Etape 2 : Creer une Application

- Automator demande quel type de document creer
- Choisir **"Application"**
- Cliquer sur **"Choisir"**

### Etape 3 : Ajouter l'action Shell

- Dans la barre de recherche en haut a gauche, taper : `shell`
- Double-cliquer sur **"Executer un script Shell"** (ou "Run Shell Script")
- Un editeur de texte apparait a droite

### Etape 4 : Coller le script

Effacer le contenu par defaut (`cat`) et coller ceci :

```bash
#!/bin/bash

# IMPORTANT : modifier ce chemin vers votre dossier projet
PROJECT_DIR="/Users/VOTRE_NOM/chemin/vers/enduraw_testing_tool"

cd "$PROJECT_DIR"

# Charger les variables d'environnement (.env)
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Lancer l'application
/usr/local/bin/python3 main.py
```

**IMPORTANT** : Remplacer `/Users/VOTRE_NOM/chemin/vers/enduraw_testing_tool`
par le vrai chemin du projet sur votre Mac.

Pour trouver le chemin : ouvrir le Terminal, taper `cd `, puis faire
glisser le dossier du projet dans le Terminal. Le chemin s'affiche.

**Note sur le chemin Python** : selon votre installation, Python peut etre a :
- `/usr/local/bin/python3` (Homebrew Intel)
- `/opt/homebrew/bin/python3` (Homebrew Apple Silicon M1/M2/M3)
- `/usr/bin/python3` (Python systeme)

Pour savoir : taper `which python3` dans le Terminal et utiliser ce chemin.

### Etape 5 : Sauvegarder l'application

- Fichier > Enregistrer (Cmd + S)
- Nom : **Enduraw**
- Emplacement : **Applications** (ou Bureau)
- Format de fichier : **Application** (deja selectionne)

### Etape 6 : Utiliser l'app

- Aller dans le dossier ou vous avez sauvegarde
- **Double-cliquer** sur `Enduraw.app` pour lancer
- Pour l'ajouter au **Dock** : faire glisser l'icone vers le Dock
- Pour l'ajouter au **Launchpad** : si sauvegardee dans Applications, elle y apparait automatiquement

---

## 6. Ajouter une icone personnalisee (optionnel)

1. Trouver une image PNG pour l'icone
2. Clic droit sur `Enduraw.app` > **Lire les informations**
3. Faire glisser l'image sur la petite icone en haut a gauche de la fenetre d'informations

---

## Problemes frequents

### "command not found: python3"
Python n'est pas installe. Reprendre l'etape 1.

### "ModuleNotFoundError: No module named 'customtkinter'"
Les dependances ne sont pas installees. Reprendre l'etape 2.

### L'app Automator s'ouvre mais se ferme aussitot
Le chemin du projet dans le script est incorrect. Verifier avec
`ls /chemin/vers/enduraw_testing_tool/main.py` dans le Terminal.

### "Permission denied"
Executer une fois dans le Terminal :
```bash
chmod +x /chemin/vers/enduraw_testing_tool/run.sh
```

