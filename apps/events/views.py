from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, EventCategory, EventTag, EventImage, CustomFormField
from .serializers import (
    EventSerializer, 
    EventCategorySerializer, 
    EventTagSerializer,
    EventImageSerializer, 
    CustomFormFieldSerializer,
    EventListSerializer,
    EventDetailSerializer
)
from apps.core.permissions import IsOrganizerOrReadOnly, IsOwnerOrReadOnly

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'event_type', 'status', 'organizer', 'start_date']
    search_fields = ['title', 'description', 'location_city']
    ordering_fields = ['start_date', 'created_at', 'registration_count']

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        elif self.action == 'retrieve':
            return EventDetailSerializer
        return EventSerializer

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def upload_images(self, request, pk=None):
        event = self.get_object()
        
        # Vérifier que l'utilisateur est bien le propriétaire de l'événement
        if event.organizer != request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à modifier cet événement.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Traiter les images téléchargées
        images_data = []
        for image_file in request.FILES.getlist('images'):
            image = EventImage.objects.create(image=image_file)
            event.gallery_images.add(image)
            images_data.append(EventImageSerializer(image).data)
        
        return Response(images_data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_form_fields(self, request, pk=None):
        event = self.get_object()
        
        # Vérifier que l'événement est de type 'inscription'
        if event.event_type != 'inscription':
            return Response(
                {'detail': 'Seuls les événements de type inscription peuvent avoir des champs de formulaire.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Supprimer les champs existants si demandé
        if request.data.get('clear_existing', False):
            event.form_fields.all().delete()
        
        # Ajouter les nouveaux champs
        fields_data = request.data.get('fields', [])
        serializer = CustomFormFieldSerializer(data=fields_data, many=True)
        
        if serializer.is_valid():
            for field_data in serializer.validated_data:
                CustomFormField.objects.create(event=event, **field_data)
            
            # Récupérer les champs mis à jour
            updated_fields = CustomFormFieldSerializer(event.form_fields.all(), many=True).data
            return Response(updated_fields)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_events = Event.objects.filter(is_featured=True, status='validated')
        serializer = EventListSerializer(featured_events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_events(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentification requise.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        events = Event.objects.filter(organizer=request.user)
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)

class EventCategoryViewSet(viewsets.ModelViewSet):
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        category = self.get_object()
        events = Event.objects.filter(category=category, status='validated')
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)

class EventTagViewSet(viewsets.ModelViewSet):
    queryset = EventTag.objects.all()
    serializer_class = EventTagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']