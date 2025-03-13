from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Registration, TicketType, TicketPurchase, Discount
from .serializers import (
    RegistrationSerializer,
    TicketTypeSerializer,
    TicketPurchaseSerializer,
    DiscountSerializer,
    RegistrationCreateSerializer
)
from apps.core.permissions import IsOwnerOrReadOnly
from django.shortcuts import get_object_or_404
from apps.events.models import Event
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

class TicketTypeViewSet(viewsets.ModelViewSet):
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return TicketType.objects.all()
        return TicketType.objects.filter(event__organizer=user)

    def perform_create(self, serializer):
        event_id = self.request.data.get('event')
        event = get_object_or_404(Event, id=event_id)
        
        # Vérifier que l'utilisateur est l'organisateur de l'événement
        if event.organizer != self.request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à créer des billets pour cet événement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save()

class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Discount.objects.all()
        return Discount.objects.filter(event__organizer=user)
    
    def perform_create(self, serializer):
        event_id = self.request.data.get('event')
        event = get_object_or_404(Event, id=event_id)
        
        # Vérifier que l'utilisateur est l'organisateur de l'événement
        if event.organizer != self.request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à créer des codes promo pour cet événement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        discount = self.get_object()
        code = request.data.get('code')
        
        if code != discount.code:
            return Response({'valid': False, 'message': 'Code invalide.'})
        
        if not discount.is_valid():
            return Response({'valid': False, 'message': 'Ce code n\'est plus valide.'})
        
        return Response({
            'valid': True,
            'discount': DiscountSerializer(discount).data
        })

class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Registration.objects.all()
        
        # Si l'utilisateur est un organisateur, montrer les inscriptions à ses événements
        if user.role == 'organizer':
            return Registration.objects.filter(event__organizer=user)
        
        # Sinon, montrer seulement les inscriptions de l'utilisateur
        return Registration.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RegistrationCreateSerializer
        return RegistrationSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate_qr_codes(self, request, pk=None):
        registration = self.get_object()
        
        # Vérifier que l'utilisateur est autorisé
        if registration.user != request.user and registration.event.organizer != request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à accéder à cette inscription.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Générer les QR codes pour chaque billet
        for ticket in registration.tickets.all():
            if not ticket.qr_code:
                # Créer le QR code avec les informations du billet
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data({
                    'registration_id': str(registration.id),
                    'ticket_id': ticket.id,
                    'ticket_type': ticket.ticket_type.name,
                    'event_id': str(registration.event.id),
                    'reference': registration.reference_code
                })
                qr.make(fit=True)
                
                # Créer une image à partir du QR code
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                
                # Sauvegarder l'image dans le champ qr_code
                filename = f"qr-{registration.reference_code}-{ticket.id}.png"
                ticket.qr_code.save(filename, ContentFile(buffer.getvalue()), save=True)
        
        # Renvoyer les billets mis à jour
        tickets = TicketPurchaseSerializer(registration.tickets.all(), many=True).data
        return Response({'tickets': tickets})
    
    @action(detail=False, methods=['get'])
    def my_registrations(self, request):
        registrations = Registration.objects.filter(user=request.user)
        serializer = self.get_serializer(registrations, many=True)
        return Response(serializer.data)

class TicketPurchaseViewSet(viewsets.ModelViewSet):
    queryset = TicketPurchase.objects.all()
    serializer_class = TicketPurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return TicketPurchase.objects.all()
        
        # Si l'utilisateur est un organisateur, montrer les billets de ses événements
        if user.role == 'organizer':
            return TicketPurchase.objects.filter(registration__event__organizer=user)
        
        # Sinon, montrer seulement les billets de l'utilisateur
        return TicketPurchase.objects.filter(registration__user=user)
    
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        ticket = self.get_object()
        event = ticket.registration.event
        
        # Vérifier que l'utilisateur est l'organisateur de l'événement
        if event.organizer != request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à valider les billets pour cet événement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier si le billet a déjà été utilisé
        if ticket.is_checked_in:
            return Response(
                {'detail': 'Ce billet a déjà été utilisé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Marquer le billet comme utilisé
        from django.utils import timezone
        ticket.is_checked_in = True
        ticket.checked_in_at = timezone.now()
        ticket.save()
        
        return Response({
            'success': True,
            'ticket': TicketPurchaseSerializer(ticket).data
        })