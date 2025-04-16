# apps/user_messages/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserMessagingSettings, Message
from apps.notifications.models import Notification

User = get_user_model()

@receiver(post_save, sender=User)
def create_messaging_settings(sender, instance, created, **kwargs):
    """Crée automatiquement les paramètres de messagerie pour les nouveaux utilisateurs"""
    if created:
        UserMessagingSettings.objects.create(user=instance)

@receiver(post_save, sender=Message)
def notify_message_recipients(sender, instance, created, **kwargs):
    """Envoie une notification aux destinataires d'un nouveau message"""
    if created:
        # Ne pas notifier l'expéditeur
        recipients = instance.conversation.participants.exclude(id=instance.sender.id)
        
        for recipient in recipients:
            # Vérifier si le destinataire n'a pas bloqué l'expéditeur
            try:
                settings = UserMessagingSettings.objects.get(user=recipient)
                if settings.messaging_enabled and instance.sender not in settings.blocked_users.all():
                    # Créer une notification
                    sender_name = f"{instance.sender.first_name} {instance.sender.last_name}".strip()
                    if not sender_name:
                        sender_name = instance.sender.username or instance.sender.email
                        
                    message_preview = instance.content[:50] + "..." if len(instance.content) > 50 else instance.content
                    
                    Notification.objects.create(
                        recipient=recipient,
                        actor=instance.sender,
                        verb="message",
                        action_object=instance,
                        target=instance.conversation,
                        description=f"Nouveau message de {sender_name}: {message_preview}"
                    )
            except UserMessagingSettings.DoesNotExist:
                pass  # Si les paramètres n'existent pas, ne pas envoyer de notification