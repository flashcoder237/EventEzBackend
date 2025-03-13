from django.db import models
from apps.accounts.models import User
from apps.events.models import Event
import uuid

class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=100)  # Ex: Standard, VIP, Early Bird
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Quotas et disponibilité
    quantity_total = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    
    # Période de vente
    sales_start = models.DateTimeField()
    sales_end = models.DateTimeField()
    
    # Options
    is_visible = models.BooleanField(default=True)
    max_per_order = models.PositiveIntegerField(default=10)
    min_per_order = models.PositiveIntegerField(default=1)
    
    def tickets_available(self):
        return self.quantity_total - self.quantity_sold
    
    def is_sold_out(self):
        return self.quantity_sold >= self.quantity_total
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"

class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Pourcentage'),
        ('fixed', 'Montant fixe'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='discounts')
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Validité
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=0)
    times_used = models.PositiveIntegerField(default=0)
    
    # Restrictions
    applicable_ticket_types = models.ManyToManyField(TicketType, blank=True, related_name='discounts')
    
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.valid_from <= now <= self.valid_until and
            (self.max_uses == 0 or self.times_used < self.max_uses)
        )
    
    def __str__(self):
        return self.code

class Registration(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée'),
        ('completed', 'Terminée'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    
    # Informations de base
    registration_type = models.CharField(max_length=20, choices=Event.TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Suivi du temps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Métriques pour tarification formulaires
    form_data_size = models.FloatField(default=0.0)  # En MB
    
    # Référence unique
    reference_code = models.CharField(max_length=20, unique=True)
    
    # Pour les formulaires personnalisés, stockage des données saisies
    form_data = models.JSONField(default=dict, blank=True)
    
    def save(self, *args, **kwargs):
        # Générer un code de référence unique s'il n'existe pas
        if not self.reference_code:
            import random
            import string
            self.reference_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        super(Registration, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.reference_code} - {self.event.title}"

class TicketPurchase(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='tickets')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='purchases')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_code = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name='uses')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Pour la génération et la validation des billets
    qr_code = models.ImageField(upload_to='tickets_qr/', blank=True, null=True)
    is_checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.ticket_type.name} pour {self.registration.reference_code}"