# apps/user_messages/models.py
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)

    def __str__(self):
        participants_str = ", ".join([user.email for user in self.participants.all()[:3]])
        if self.participants.count() > 3:
            participants_str += f" et {self.participants.count() - 3} autres"
        return f"Conversation: {participants_str}"

class UserMessagingSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messaging_settings')
    messaging_enabled = models.BooleanField(default=True)
    blocked_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='blocked_by', blank=True)

    def __str__(self):
        return f"Paramètres de messagerie de {self.user}"
    
    class Meta:
        verbose_name = "Paramètres de messagerie"
        verbose_name_plural = "Paramètres de messagerie"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='user_messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_user_messages', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_user_messages', blank=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    is_starred = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"Message de {self.sender} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"