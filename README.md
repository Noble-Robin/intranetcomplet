# 🏢 Intranet Caplogy

Plateforme intranet intégrée avec deux applications Django :
- **Moodle Manager** : Gestion des cours et formations
- **AutoDocs** : Génération automatique de documents PDF

## 🚀 Démarrage Rapide

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Test des projets (optionnel)
```bash
test_projects.bat
```

### 3. Démarrage de l'intranet
```bash
start_intranet.bat
```

## 📱 Accès aux services

- **Page d'accueil** : http://localhost:3000
- **Moodle Manager** : http://localhost:8000
- **AutoDocs** : http://localhost:8001

## 🔧 Configuration

Les configurations sont dans les fichiers `.env` :
- `moodle/.env` : Configuration du projet Moodle
- `AutoDocs/.env` : Configuration du projet AutoDocs (si existe)

## 📁 Structure du projet

```
intranetcomplet/
├── moodle/                 # Projet Django Moodle Manager
│   ├── caplogy_app/       # Application principale
│   ├── caplogy_project/   # Configuration Django
│   └── manage.py
├── AutoDocs/              # Projet Django AutoDocs
│   ├── myproject/         # Configuration Django
│   └── manage.py
├── index.html             # Page d'accueil
├── start_intranet.bat     # Script de démarrage
├── test_projects.bat      # Script de test
└── requirements.txt       # Dépendances Python
```

## 🛠️ Développement

Pour développer individuellement :

**Moodle Manager :**
```bash
cd moodle
python manage.py runserver 8000
```

**AutoDocs :**
```bash
cd AutoDocs
python manage.py runserver 8001
```

## 🔒 Sécurité

- Modifier les clés secrètes dans les fichiers `.env` en production
- Configurer ALLOWED_HOSTS pour votre domaine
- Utiliser HTTPS en production
