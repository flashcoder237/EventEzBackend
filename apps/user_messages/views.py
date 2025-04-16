# apps/user_messages/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Conversation, Message, UserMessagingSettings
from .serializers import ConversationSerializer, MessageSerializer, UserMessagingSettingsSerializer
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

User = get_user_model()

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Renvoie les conversations auxquelles l'utilisateur participe"""
        return Conversation.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        """Ajoute automatiquement l'utilisateur actuel comme participant"""
        conversation = serializer.save()
        if self.request.user not in conversation.participants.all():
            conversation.participants.add(self.request.user)

    def create(self, request, *args, **kwargs):
        # Vérifier si la conversation existe déjà entre ces participants
        if 'participants' in request.data:
            participants = set(request.data['participants'])
            participants.add(request.user.id)  # Ajouter l'utilisateur actuel
            
            # Chercher une conversation existante avec exactement ces participants
            existing_conversations = Conversation.objects.all()
            
            for conv in existing_conversations:
                conv_participants = set(conv.participants.values_list('id', flat=True))
                if conv_participants == participants:
                    # Conversation trouvée, renvoyer l'existante
                    serializer = self.get_serializer(conv)
                    return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Si on n'a pas trouvé de conversation existante, en créer une nouvelle
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Ajoute un participant à la conversation"""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(pk=user_id)
            conversation.participants.add(user)
            return Response({'status': 'participant added'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
            
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive ou désarchive une conversation"""
        conversation = self.get_object()
        conversation.is_archived = not conversation.is_archived
        conversation.save()
        return Response({
            'status': 'success', 
            'is_archived': conversation.is_archived
        })
            
    @action(detail=True, methods=['post'])
    def star(self, request, pk=None):
        """Met en favori ou retire des favoris une conversation"""
        conversation = self.get_object()
        conversation.is_starred = not conversation.is_starred
        conversation.save()
        return Response({
            'status': 'success', 
            'is_starred': conversation.is_starred
        })


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Renvoie les messages des conversations auxquelles l'utilisateur participe"""
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            return Message.objects.filter(
                conversation_id=conversation_id,
                conversation__participants=self.request.user
            )
        return Message.objects.filter(
            conversation__participants=self.request.user
        )

    def perform_create(self, serializer):
        """Définit l'expéditeur comme étant l'utilisateur actuel"""
        serializer.save(sender=self.request.user)
        
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marque un message comme lu par l'utilisateur actuel"""
        message = self.get_object()
        message.read_by.add(request.user)
        return Response({'status': 'message marked as read'})
        
    @action(detail=True, methods=['post'])
    def star(self, request, pk=None):
        """Marque un message comme important ou non"""
        message = self.get_object()
        message.is_starred = not message.is_starred
        message.save()
        return Response({
            'status': 'success', 
            'is_starred': message.is_starred
        })


class UserMessagingSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = UserMessagingSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserMessagingSettings.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        # Get or create settings for the current user
        settings, created = UserMessagingSettings.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # Check if settings already exist
        if UserMessagingSettings.objects.filter(user=self.request.user).exists():
            return Response(
                {"error": "Settings already exist for this user"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save(user=self.request.user)

    def get_object(self):
        # Return the UserMessagingSettings instance for the current user
        return get_object_or_404(UserMessagingSettings, user=self.request.user)