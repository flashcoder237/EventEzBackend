from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Payment, Refund, Invoice
from .serializers import PaymentSerializer, RefundSerializer, InvoiceSerializer, PaymentCreateSerializer
from apps.core.permissions import IsOwnerOrReadOnly
from django.shortcuts import get_object_or_404
from apps.registrations.models import Registration
from django.utils import timezone

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        
        # Si l'utilisateur est un organisateur, montrer les paiements de ses événements
        if user.role == 'organizer':
            return Payment.objects.filter(registration__event__organizer=user)
        
        # Sinon, montrer seulement les paiements de l'utilisateur
        return Payment.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def perform_create(self, serializer):
        registration_id = self.request.data.get('registration')
        registration = get_object_or_404(Registration, id=registration_id)
        
        # Vérifier que l'utilisateur est bien le propriétaire de l'inscription
        if registration.user != self.request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à effectuer un paiement pour cette inscription.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def process_mtn_money(self, request, pk=None):
        payment = self.get_object()
        
        # Vérifier que le paiement appartient à l'utilisateur
        if payment.user != request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à traiter ce paiement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Simuler l'intégration avec MTN Money API
        # Dans une implémentation réelle, vous intégreriez ici l'API de MTN Money
        
        # Mettre à jour le statut du paiement (simulation)
        payment.status = 'completed'
        payment.payment_date = timezone.now()
        payment.transaction_id = f"MTN-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        payment.save()
        
        # Mettre à jour le statut de l'inscription
        registration = payment.registration
        registration.status = 'confirmed'
        registration.confirmed_at = timezone.now()
        registration.save()
        
        # Générer une facture
        invoice = Invoice.objects.create(
            payment=payment,
            due_date=None  # Payé immédiatement
        )
        
        return Response({
            'success': True,
            'payment': PaymentSerializer(payment).data,
            'invoice': InvoiceSerializer(invoice).data
        })
    
    @action(detail=True, methods=['post'])
    def process_orange_money(self, request, pk=None):
        # Logique similaire à MTN Money, adaptée pour Orange Money
        payment = self.get_object()
        
        # Vérifier que le paiement appartient à l'utilisateur
        if payment.user != request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à traiter ce paiement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Simuler l'intégration avec Orange Money API
        
        # Mettre à jour le statut du paiement (simulation)
        payment.status = 'completed'
        payment.payment_date = timezone.now()
        payment.transaction_id = f"ORANGE-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        payment.save()
        
        # Mettre à jour le statut de l'inscription
        registration = payment.registration
        registration.status = 'confirmed'
        registration.confirmed_at = timezone.now()
        registration.save()
        
        # Générer une facture
        invoice = Invoice.objects.create(
            payment=payment,
            due_date=None  # Payé immédiatement
        )
        
        return Response({
            'success': True,
            'payment': PaymentSerializer(payment).data,
            'invoice': InvoiceSerializer(invoice).data
        })
    
    @action(detail=True, methods=['post'])
    def calculate_usage_fees(self, request, pk=None):
        payment = self.get_object()
        registration = payment.registration
        event = registration.event
        
        # Vérifier que c'est un événement de type inscription avec facturation basée sur l'usage
        if event.event_type != 'inscription' or not payment.is_usage_based:
            return Response(
                {'detail': 'Ce paiement ne concerne pas un événement avec facturation à l\'usage.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculer les frais en fonction du stockage et de la durée
        storage_fee = payment.storage_amount * 0.05  # 0.05 XAF par MB
        duration_fee = payment.duration_days * 50  # 50 XAF par jour
        total_fee = storage_fee + duration_fee
        
        # Mettre à jour le montant du paiement
        payment.amount = total_fee
        payment.save()
        
        return Response({
            'storage_amount': payment.storage_amount,
            'storage_fee': storage_fee,
            'duration_days': payment.duration_days,
            'duration_fee': duration_fee,
            'total_fee': total_fee
        })

class RefundViewSet(viewsets.ModelViewSet):
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Refund.objects.all()
        
        # Si l'utilisateur est un organisateur, montrer les remboursements de ses événements
        if user.role == 'organizer':
            return Refund.objects.filter(payment__registration__event__organizer=user)
        
        # Sinon, montrer seulement les remboursements de l'utilisateur
        return Refund.objects.filter(payment__user=user)
    
    def perform_create(self, serializer):
        payment_id = self.request.data.get('payment')
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Vérifier que l'utilisateur est autorisé à demander un remboursement
        if payment.user != self.request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à demander un remboursement pour ce paiement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que le paiement peut être remboursé
        if payment.status != 'completed':
            return Response(
                {'detail': 'Seuls les paiements complétés peuvent être remboursés.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def process_refund(self, request, pk=None):
        refund = self.get_object()
        payment = refund.payment
        
        # Vérifier que l'utilisateur est un administrateur ou l'organisateur de l'événement
        if not request.user.is_staff and payment.registration.event.organizer != request.user:
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à traiter ce remboursement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mettre à jour le statut du remboursement
        refund.status = 'completed'
        refund.processed_at = timezone.now()
        refund.processed_by = request.user
        refund.save()
        
        # Mettre à jour le statut du paiement
        payment.status = 'refunded'
        payment.save()
        
        return Response({
            'success': True,
            'refund': RefundSerializer(refund).data
        })

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Invoice.objects.all()
        
        # Si l'utilisateur est un organisateur, montrer les factures de ses événements
        if user.role == 'organizer':
            return Invoice.objects.filter(payment__registration__event__organizer=user)
        
        # Sinon, montrer seulement les factures de l'utilisateur
        return Invoice.objects.filter(payment__user=user)
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        invoice = self.get_object()
        
        # Vérifier que l'utilisateur est autorisé à télécharger cette facture
        if (invoice.payment.user != request.user and 
            invoice.payment.registration.event.organizer != request.user and 
            not request.user.is_staff):
            return Response(
                {'detail': 'Vous n\'êtes pas autorisé à télécharger cette facture.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Générer le PDF de la facture si nécessaire
        if not invoice.pdf_file:
            # Logique pour générer le PDF (utiliserait une bibliothèque comme ReportLab)
            # Pour l'exemple, nous simulons simplement la génération
            invoice.pdf_file = 'generated_invoice.pdf'  # Simulation
            invoice.save()
        
        # Renvoyer l'URL du fichier PDF
        return Response({
            'pdf_url': request.build_absolute_uri(invoice.pdf_file.url)
        })