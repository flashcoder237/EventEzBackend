from django.db import models
from apps.accounts.models import User
from apps.registrations.models import Registration
import uuid

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
        ('cancelled', 'Annulé'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('mtn_money', 'MTN Mobile Money'),
        ('orange_money', 'Orange Money'),
        ('credit_card', 'Carte bancaire'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Virement bancaire'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    
    # Informations financières
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XAF')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Statut et suivi
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Suivi de la transaction
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Informations de facturation
    billing_name = models.CharField(max_length=255, blank=True)
    billing_email = models.EmailField(blank=True)
    billing_phone = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField(blank=True)
    
    # Pour les formulaires personnalisés (facturation basée sur l'usage)
    is_usage_based = models.BooleanField(default=False)
    storage_amount = models.FloatField(default=0.0)  # en MB
    duration_days = models.PositiveIntegerField(default=0)
    
    # Données de transaction externes
    payment_gateway_response = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.id} - {self.amount} {self.currency} - {self.status}"

class Refund(models.Model):
    REFUND_STATUS_CHOICES = (
        ('requested', 'Demandé'),
        ('processing', 'En cours de traitement'),
        ('completed', 'Complété'),
        ('rejected', 'Rejeté'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='requested')
    
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='processed_refunds')
    
    transaction_id = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Remboursement {self.amount} pour {self.payment.id}"

class Invoice(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    
    # Pour les paiements basés sur l'usage
    billing_period_start = models.DateField(null=True, blank=True)
    billing_period_end = models.DateField(null=True, blank=True)
    
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Générer un numéro de facture unique s'il n'existe pas
        if not self.invoice_number:
            from django.utils import timezone
            year = timezone.now().year
            month = timezone.now().month
            
            # Trouver le numéro de la dernière facture
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f"INV-{year}{month:02d}"
            ).order_by('invoice_number').last()
            
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.invoice_number = f"INV-{year}{month:02d}-{new_number:04d}"
        
        super(Invoice, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.invoice_number