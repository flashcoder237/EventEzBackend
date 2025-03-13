# README - Backend Eventez

## Présentation

Bienvenue sur le backend de l'application Eventez, une plateforme de gestion d'événements complète pour le Cameroun. Cette API, développée avec Django REST Framework, prend en charge la gestion des événements, des inscriptions (via billetterie ou formulaires personnalisés), des paiements (MTN Money, Orange Money, etc.), et plus encore.

## Prérequis

- Python 3.8+ 
- PostgreSQL
- Virtualenv (recommandé)

## Installation

1. **Cloner le dépôt**

```bash
git clone https://github.com/flashcoder237/EventEzBackend.git
cd eventez-backend
```

2. **Créer et activer un environnement virtuel**

```bash
python -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# ou
venv\Scripts\activate     # Sur Windows
```

3. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

4. **Configurer la base de données**

```bash
# Créer une base de données PostgreSQL
createdb eventez_db

# Ou manuellement avec psql
psql
CREATE DATABASE eventez_db;
\q
```

5. **Configurer les variables d'environnement**

Créez un fichier `.env` à la racine du projet:

```
DEBUG=True
SECRET_KEY=votre-clé-secrète-ici
DB_NAME=eventez_db
DB_USER=postgres
DB_PASSWORD=votre-mot-de-passe
DB_HOST=localhost
DB_PORT=5432
```

## Lancement du serveur

1. **Appliquer les migrations**

```bash
python manage.py migrate
```

2. **Créer un super utilisateur**

```bash
python manage.py createsuperuser
```

3. **Charger les données de test (facultatif)**

```bash
python manage.py seed_data
```

4. **Lancer le serveur de développement**

```bash
python manage.py runserver
```

Le serveur sera accessible à l'adresse http://localhost:8000/

L'API REST sera disponible à http://localhost:8000/api/

Le panneau d'administration à http://localhost:8000/admin/

## Structure du projet

```
eventez/
├── config/                 # Configuration principale
├── apps/                   # Applications modulaires
│   ├── accounts/           # Gestion des utilisateurs
│   ├── events/             # Gestion des événements
│   ├── registrations/      # Inscriptions et billetterie
│   ├── payments/           # Paiements
│   ├── feedback/           # Feedback et validations
│   ├── notifications/      # Notifications
│   └── core/               # Fonctionnalités partagées
├── static/                 # Fichiers statiques
├── media/                  # Médias uploadés
└── manage.py               # Script de gestion Django
```

## Points d'API principaux

- `/api/events/` - Gestion des événements
- `/api/users/` - Gestion des utilisateurs
- `/api/registrations/` - Gestion des inscriptions
- `/api/ticket-types/` - Types de billets
- `/api/payments/` - Gestion des paiements
- `/api/feedbacks/` - Avis et retours
- `/api/auth/token/` - Authentification JWT

## Interface d'administration

Une interface d'administration complète est disponible à l'adresse `/admin/` avec une interface moderne personnalisée grâce à Django Jazzmin.

## Développement et tests

Pour lancer les tests:

```bash
python manage.py test
```

Pour vérifier la couverture de code:

```bash
coverage run --source='.' manage.py test
coverage report
```

## Support et problèmes courants

Si vous rencontrez l'erreur `django.db.utils.ProgrammingError: ERREUR: la relation « accounts_user » n'existe pas`, assurez-vous d'avoir bien exécuté les migrations:

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

## Ressources

- Documentation Django REST Framework: https://www.django-rest-framework.org/
- Documentation Django: https://docs.djangoproject.com/
- Documentation Jazzmin: https://django-jazzmin.readthedocs.io/