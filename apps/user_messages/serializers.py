# apps/user_messages/serializers.py
from rest_framework import serializers
from .models import Conversation, Message, UserMessagingSettings
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'content', 
                  'created_at', 'read_by', 'reply_to', 'is_starred']
    
    def get_sender_name(self, obj):
        if obj.sender.first_name and obj.sender.last_name:
            return f"{obj.sender.first_name} {obj.sender.last_name}"
        return obj.sender.username or obj.sender.email

class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    user_messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at', 'updated_at', 'user_messages', 
                  'is_archived', 'is_starred']

    def create(self, validated_data):
        participants = validated_data.pop('participants')
        conversation = Conversation.objects.create(**validated_data)
        for participant in participants:
            conversation.participants.add(participant)
        return conversation

class UserMessagingSettingsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserMessagingSettings
        fields = ['id', 'user', 'messaging_enabled', 'blocked_users']

    def update(self, instance, validated_data):
        blocked_users_data = validated_data.pop('blocked_users', None)
        if blocked_users_data is not None:
            instance.blocked_users.set(blocked_users_data)
        return super().update(instance, validated_data)