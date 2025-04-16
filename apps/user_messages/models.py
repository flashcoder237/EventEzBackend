from django.db import models
from django.conf import settings

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserMessagingSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messaging_settings')
    messaging_enabled = models.BooleanField(default=True)
    blocked_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='blocked_by', blank=True)

    def __str__(self):
        return f"Messaging settings for {self.user}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='user_messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_user_messages', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_user_messages', blank=True)

    class Meta:
        ordering = ['created_at']
