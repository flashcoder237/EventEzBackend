from rest_framework import serializers
from .models import Conversation, Message, UserMessagingSettings
from django.contrib.auth import get_user_model

User = get_user_model()

class user_messageserializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'content', 'created_at', 'read_by']

class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    user_messages = user_messageserializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at', 'updated_at', 'messages']

class UserMessagingSettingsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserMessagingSettings
        fields = ['user', 'messaging_enabled', 'blocked_users']

    def update(self, instance, validated_data):
        blocked_users_data = validated_data.pop('blocked_users', None)
        if blocked_users_data is not None:
            instance.blocked_users.set(blocked_users_data)
        return super().update(instance, validated_data)
