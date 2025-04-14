from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Utilisateur'),
        ('organizer', 'Organisateur'),
        ('admin', 'Administrateur'),
    )
    
    TYPE_CHOICES = (
        ('individual', 'Individuel'),
        ('organization', 'Organisation'),
    )
    
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    organizer_type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True, null=True)
    
    # Champs pour organisateurs de type organisation
    company_name = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    
    # Champs de vérification
    is_verified = models.BooleanField(default=False)
    verification_documents = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    
    # Champs de facturation
    billing_address = models.TextField(blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email

class OrganizerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organizer_profile')
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='organizer_logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    verified_status = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    event_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Profil de {self.user.email}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_valid(self):
        return timezone.now() <= self.expires_at
    
    def __str__(self):
        return f"Token de réinitialisation pour {self.user.email} (expire: {self.expires_at})"