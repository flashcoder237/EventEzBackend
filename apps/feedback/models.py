from django.db import models
from apps.accounts.models import User
from apps.events.models import Event

class EventFeedback(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    
    # Évaluation
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    
    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Statut de modération
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('event', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.rating}★"

class EventFlag(models.Model):
    FLAG_REASON_CHOICES = (
        ('inappropriate', 'Contenu inapproprié'),
        ('misleading', 'Information trompeuse'),
        ('scam', 'Arnaque potentielle'),
        ('duplicate', 'Événement en double'),
        ('other', 'Autre raison'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='flags')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flags')
    
    reason = models.CharField(max_length=20, choices=FLAG_REASON_CHOICES)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='resolved_flags')
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('event', 'user')
    
    def __str__(self):
        return f"Signalement pour {self.event.title} - {self.get_reason_display()}"

class EventValidation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='validations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='validations')
    
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('event', 'user')
    
    def __str__(self):
        return f"Validation pour {self.event.title} par {self.user.username}"