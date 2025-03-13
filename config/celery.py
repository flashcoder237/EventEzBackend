# config/celery.py
import os
from celery import Celery

# Définir le module de paramètres par défaut Django pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('eventez')

# Utiliser les paramètres Django comme source de configuration Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charger automatiquement les tâches des applications Django installées
app.autodiscover_tasks()