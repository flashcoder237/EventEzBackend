from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import EventFeedback, EventFlag, EventValidation
from .serializers import EventFeedbackSerializer, EventFlagSerializer, EventValidationSerializer
from apps.core.permissions import IsOwnerOrReadOnly
from django.shortcuts import get_object_or_404
from apps.events.models import Event
from django.db.models import Count, Avg
from django.utils import timezone

class EventFeedbackViewSet(viewsets.ModelViewSet):
    queryset = EventFeedback.objects.all()
    serializer_class = EventFeedbackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']
    
    def get_queryset(self):
        event_id = self.request.query_params.get('event')
        if event_id:
            return EventFeedback.objects.filter(event__id=event_id, is_approved=True)
        return EventFeedback.objects.filter(is_approved=True)
    
    def perform_create(self, serializer):
        event_id = self.request.data.get('event')
        event = get_object_or_404(Event, id=event_id)
        
        # Vérifier si l'utilisateur a déjà laissé un commentaire pour cet événement
        if EventFeedback.objects.filter(event=event, user=self.request.user).exists():
            return Response(
                {'detail': 'Vous avez déjà laissé un commentaire pour cet événement.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_feedback(self, request):
        feedback = EventFeedback.objects.filter(user=request.user)
        serializer = self.get_serializer(feedback, many=True)
        return Response(serializer.data)

class EventFlagViewSet(viewsets.ModelViewSet):
    queryset = EventFlag.objects.all()
    serializer_class = EventFlagSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        event_id = self.request.data.get('event')
        event = get_object_or_404(Event, id=event_id)
        
        # Vérifier si l'utilisateur a déjà signalé cet événement
        if EventFlag.objects.filter(event=event, user=self.request.user).exists():
            return Response(
                {'detail': 'Vous avez déjà signalé cet événement.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        flag = self.get_object()
        
        # Vérifier que l'utilisateur est un administrateur
        if not request.user.is_staff:
            return Response(
                {'detail': 'Seuls les administrateurs peuvent résoudre les signalements.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        flag.is_resolved = True
        flag.resolved_at = timezone.now()
        flag.resolved_by = request.user
        flag.resolution_notes = request.data.get('resolution_notes', '')
        flag.save()
        
        return Response({
            'success': True,
            'flag': EventFlagSerializer(flag).data
        })
    
    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        # Accessible uniquement aux administrateurs
        if not request.user.is_staff:
            return Response(
                {'detail': 'Accès non autorisé.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        flags = EventFlag.objects.filter(is_resolved=False)
        serializer = self.get_serializer(flags, many=True)
        return Response(serializer.data)

class EventValidationViewSet(viewsets.ModelViewSet):
    queryset = EventValidation.objects.all()
    serializer_class = EventValidationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        event_id = self.request.data.get('event')
        event = get_object_or_404(Event, id=event_id)
        
        # Vérifier si l'utilisateur a déjà validé cet événement
        if EventValidation.objects.filter(event=event, user=self.request.user).exists():
            return Response(
                {'detail': 'Vous avez déjà validé cet événement.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def event_stats(self, request):
        event_id = request.query_params.get('event')
        if not event_id:
            return Response(
                {'detail': 'Veuillez spécifier un événement.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event = get_object_or_404(Event, id=event_id)
        
        # Récupérer les statistiques
        validations_count = EventValidation.objects.filter(event=event).count()
        flags_count = EventFlag.objects.filter(event=event).count()
        feedback_stats = EventFeedback.objects.filter(event=event).aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        
        return Response({
            'event_id': str(event.id),
            'event_title': event.title,
            'validations_count': validations_count,
            'flags_count': flags_count,
            'feedback_count': feedback_stats['count'],
            'average_rating': feedback_stats['avg_rating']
        })