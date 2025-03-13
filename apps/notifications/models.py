from django.db import models
from apps.accounts.models import User
import uuid

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ('event_update', 'Mise à jour d\'événement'),
        ('registration_confirmation', 'Confirmation d\'inscription'),
        ('payment_confirmation', 'Confirmation de paiement'),
        ('event_reminder', 'Rappel d\'événement'),
        ('system_message', 'Message système'),
        ('custom_message', 'Message personnalisé'),
    )
    
    CHANNEL_CHOICES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Notification push'),
        ('in_app', 'Dans l\'application'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Contenu
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    
    # Cible et référence
    related_object_id = models.CharField(max_length=50, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    
    # Canal et statut
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Pour les emails
    email_subject = models.CharField(max_length=255, blank=True)
    
    # Pour les SMS
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Pour les notifications personnalisées
    extra_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.notification_type} pour {self.user.email} - {self.title}"

class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(max_length=30, choices=Notification.NOTIFICATION_TYPE_CHOICES)
    
    # Contenu par canal
    email_subject = models.CharField(max_length=255, blank=True)
    email_body = models.TextField(blank=True)
    sms_body = models.TextField(blank=True)
    push_title = models.CharField(max_length=255, blank=True)
    push_body = models.TextField(blank=True)
    in_app_title = models.CharField(max_length=255, blank=True)
    in_app_body = models.TextField(blank=True)
    
    # Variables disponibles
    available_variables = models.TextField(blank=True, help_text="Liste des variables utilisables dans ce modèle")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name