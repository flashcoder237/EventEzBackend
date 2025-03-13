# notifications/serializers.py
from rest_framework import serializers
from .models import Notification, NotificationTemplate

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'sent_at', 'read_at']

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']