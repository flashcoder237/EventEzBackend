from django.db import models
from django.utils.text import slugify
from apps.accounts.models import User
import uuid

class EventCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class Event(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('validated', 'Validé'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    )
    
    TYPE_CHOICES = (
        ('billetterie', 'Billetterie'),
        ('inscription', 'Inscription Personnalisée'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)
    
    # Organisateur
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    
    # Catégorisation
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, related_name='events')
    tags = models.ManyToManyField('EventTag', blank=True, related_name='events')
    
    # Type d'événement
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Dates importantes
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField(blank=True, null=True)
    
    # Lieu
    location_name = models.CharField(max_length=255)
    location_address = models.TextField()
    location_city = models.CharField(max_length=100)
    location_country = models.CharField(max_length=100, default="Cameroun")
    location_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    location_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Médias
    banner_image = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    gallery_images = models.ManyToManyField('EventImage', blank=True, related_name='events')
    
    # État
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    
    # SEO & visibilité
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    
    # Statistiques
    view_count = models.PositiveIntegerField(default=0)
    registration_count = models.PositiveIntegerField(default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Pour les événements à formulaire personnalisé
    form_storage_usage = models.FloatField(default=0.0)  # en MB
    form_active_days = models.PositiveIntegerField(default=0)  # jours d'activation du formulaire
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Event, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class EventTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class EventImage(models.Model):
    image = models.ImageField(upload_to='event_images/')
    caption = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.caption or "Image sans légende"

class CustomFormField(models.Model):
    FIELD_TYPES = (
        ('text', 'Texte'),
        ('textarea', 'Zone de texte'),
        ('number', 'Nombre'),
        ('email', 'Email'),
        ('phone', 'Téléphone'),
        ('date', 'Date'),
        ('time', 'Heure'),
        ('select', 'Liste déroulante'),
        ('checkbox', 'Case à cocher'),
        ('radio', 'Boutons radio'),
        ('file', 'Fichier'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='form_fields')
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=255, blank=True)
    help_text = models.CharField(max_length=255, blank=True)
    options = models.TextField(blank=True, help_text="Options séparées par des virgules (pour select, checkbox, radio)")
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.label} - {self.event.title}"