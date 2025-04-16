# apps/user_messages/apps.py
from django.apps import AppConfig


class UserMessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.user_messages'
    verbose_name = "Messagerie"

    def ready(self):
        import apps.user_messages.signals