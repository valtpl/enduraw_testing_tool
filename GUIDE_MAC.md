# Enduraw Testing Data - Guide d'installation Mac

## 📋 Prérequis

Vous devez installer Python 3 sur votre Mac.

---

## 🚀 Installation 

### Étape 1 : Installer Python

### Étape 2 : Installer les dépendances

1. Copiez-collez cette commande et appuyez sur Entrée :

```bash
pip3 install customtkinter pillow
```

---

## ▶️ Lancer l'application

### Première fois

1. Décompressez le dossier `tcp_data_processor.zip` 
2. Ouvrez **Terminal**
3. Tapez `cd ` puis **glissez-déposez** le dossier `tcp_data_processor` dans le Terminal
4. Appuyez sur Entrée
5. Tapez cette commande :

```bash
python3 main.py
```

6. L'application s'ouvre !

### Les fois suivantes

Vous pouvez créer un raccourci :

1. Ouvrez **TextEdit**
2. Allez dans Format > Convertir au format Texte
3. Collez ce script (remplacez le chemin par le vôtre) :

```bash
#!/bin/bash
cd /Users/VOTRE_NOM/Downloads/tcp_data_processor
python3 main.py
```

4. Enregistrez sous `LancerEnduraw.command` sur le Bureau
5. Dans Terminal, rendez-le exécutable :

```bash
chmod +x ~/Desktop/LancerEnduraw.command
```

6. Double-cliquez sur le fichier pour lancer l'app !

---

## 📋 Utilisation de l'application

1. **Sélectionner un dossier** contenant les fichiers XML MetaLyzer
2. **Cliquer sur un test** dans la liste de gauche
3. **Remplir le formulaire** avec les données manuelles
   - L'email est **obligatoire** (c'est l'identifiant utilisateur)
4. **Sauvegarder** les données avec le bouton "Enregistrer les données"
5. **Exporter** en JSON avec "Exporter Sélectionné" ou "Exporter Tous"

---

## 📁 Où trouver les fichiers exportés ?

Les fichiers JSON sont créés dans un dossier `Output` à côté des fichiers XML source.

---

## 🆘 Problèmes fréquents

### "command not found: pip3"
→ Python n'est pas installé. Refaites l'étape 1.

### "ModuleNotFoundError: No module named 'customtkinter'"
→ Les dépendances ne sont pas installées. Refaites l'étape 2.

### L'application ne s'ouvre pas
→ Vérifiez que vous êtes bien dans le bon dossier avec `cd`.

---

