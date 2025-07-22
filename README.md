# IntranetComplet

Projet Django complet pour la gestion d'un intranet d'entreprise, incluant :
- Génération de documents RH (attestations, contrats, etc.)
- Gestion des utilisateurs et des groupes (permissions via groupes Django)
- Interface d'administration personnalisée
- Gestion de fichiers statiques et médias
- Interface moderne et responsive

## Fonctionnalités principales
- **Authentification** : Connexion/déconnexion, gestion des sessions
- **Gestion des groupes** : Permissions basées sur les groupes Django (ex : admin)
- **Générateur de documents** : Création d'attestations, contrats, etc. à partir de formulaires
- **Gestion des employés** : Ajout, modification, sélection d'employés
- **Interface admin** : Accessible uniquement aux membres du groupe "admin"
- **Thème clair/sombre** : Bascule via bouton dans la barre de navigation

## Structure du projet
- `caplogy_app/` : Application principale (vues, modèles, formulaires, templates)
- `caplogy_project/` : Configuration du projet Django
- `AutoDocs/` : Générateur de documents, templates et scripts associés
- `media/` : Fichiers médias (photos, logos, etc.)
- `static/` : Fichiers statiques (CSS, JS, images)
- `templates/` : Templates globaux

## Installation
1. **Cloner le dépôt**
2. **Créer un environnement virtuel** :
   ```bash
   python -m venv venv
   source venv/bin/activate  # ou venv\Scripts\activate sous Windows
   ```
3. **Installer les dépendances** :
   ```bash
   pip install -r requirement.txt
   ```
4. **Appliquer les migrations** :
   ```bash
   python manage.py migrate
   ```
5. **Créer un superutilisateur** (optionnel, pour accès admin Django natif) :
   ```bash
   from django.contrib.auth.models import User, Group
    user = User.objects.get(username="ton_nom_utilisateur")  # remplace par ton username
    admin_group = Group.objects.get(name="admin")
    user.groups.add(admin_group)
    user.save()
    print("Ajouté au groupe admin !")
   ```
6. **Lancer le serveur** :
   ```bash
   nohup python moodle/manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &
   ```

## Utilisation
- Accéder à l'intranet via `intranet.caplogy.com`
- L'interface admin personnalisée est accessible uniquement aux membres du groupe "admin"
- Générer des documents via le menu principal
- Ajouter/modifier des employés via les formulaires dédiés

## Gestion des groupes et permissions
- Les droits d'accès sont gérés uniquement via les groupes Django
- Pour donner l'accès admin à un utilisateur :
   1. Aller dans l'admin Django (`/admin/`)
   2. Ajouter l'utilisateur au groupe "admin"

## Déploiement en production
- Adapter les paramètres dans `settings.py` (DEBUG, ALLOWED_HOSTS, etc.)
- Utiliser un serveur WSGI (ex : gunicorn, uwsgi) derrière un reverse proxy (nginx, apache)
- Configurer les fichiers statiques et médias

## Auteurs
- Robin Noble
- Thibault Frescaline
- Jordan Milleville Lino

## Licence
Projet privé, usage interne uniquement.
