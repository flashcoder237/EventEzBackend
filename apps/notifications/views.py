# notifications/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, NotificationTemplate
from .serializers import NotificationSerializer, NotificationTemplateSerializer
from apps.core.permissions import IsAdminOrReadOnly
from django.utils import timezone

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        
        # Vérifier que la notification appartient à l'utilisateur
        if notification.user != request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à accéder à cette notification.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({'success': True})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({'success': True})

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]