from rest_framework import viewsets, permissions
from .models import Conversation, Message, UserMessagingSettings
from .serializers import ConversationSerializer, user_messageserializer, UserMessagingSettingsSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

User = get_user_model()

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        conversation = serializer.save()
        conversation.participants.add(self.request.user)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
            conversation.participants.add(user)
            return Response({'status': 'participant added'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = user_messageserializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(conversation__participants=self.request.user)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class UserMessagingSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = UserMessagingSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserMessagingSettings.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_object(self):
        # Return the UserMessagingSettings instance for the current user
        obj, created = UserMessagingSettings.objects.get_or_create(user=self.request.user)
        return obj
