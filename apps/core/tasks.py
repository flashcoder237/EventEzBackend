 # apps/core/tasks.py
from config.celery import app
from django.utils import timezone
from django.db.models import Q
from apps.events.models import Event
from apps.notifications.models import Notification
from apps.registrations.models import Registration
from apps.core.utils import send_notification

@app.task
def send_event_reminders():
    """Envoie des rappels pour les événements à venir"""
    now = timezone.now()
    
    # Événements commençant dans les 24 heures
    tomorrow = now + timezone.timedelta(days=1)
    events = Event.objects.filter(
        status='validated',
        start_date__gte=now,
        start_date__lte=tomorrow
    )
    
    for event in events:
        # Récupérer tous les participants inscrits
        registrations = Registration.objects.filter(
            event=event,
            status='confirmed'
        )
        
        for registration in registrations:
            # Envoyer un rappel
            send_notification(
                user=registration.user,
                notification_type='event_reminder',
                related_object=event,
                extra_data={
                    'event_title': event.title,
                    'event_date': event.start_date.strftime('%d/%m/%Y à %H:%M'),
                    'event_location': event.location_address,
                    'registration_code': registration.reference_code
                },
                channels=['email', 'in_app']
            )

@app.task
def clean_pending_registrations():
    """Nettoie les inscriptions en attente de paiement depuis plus de 30 minutes"""
    expiration_time = timezone.now() - timezone.timedelta(minutes=30)
    
    # Récupérer les inscriptions en attente anciennes
    pending_registrations = Registration.objects.filter(
        status='pending',
        created_at__lt=expiration_time
    )
    
    for registration in pending_registrations:
        # Si c'est un événement avec billetterie, libérer les billets
        if registration.registration_type == 'billetterie':
            for ticket in registration.tickets.all():
                ticket_type = ticket.ticket_type
                ticket_type.quantity_sold -= ticket.quantity
                ticket_type.save()
        
        # Annuler l'inscription
        registration.status = 'cancelled'
        registration.save()
        
        # Notifier l'utilisateur
        send_notification(
            user=registration.user,
            notification_type='registration_expired',
            related_object=registration,
            extra_data={
                'event_title': registration.event.title,
                'registration_code': registration.reference_code
            },
            channels=['email', 'in_app']
        )

@app.task
def send_usage_billing_notifications():
    """Envoie des notifications de facturation pour les événements avec formulaire"""
    now = timezone.now()
    
    # Récupérer les événements actifs avec inscription personnalisée
    active_events = Event.objects.filter(
        event_type='inscription',
        status='validated',
        end_date__gte=now
    )
    
    for event in active_events:
        # Mettre à jour les jours d'activation
        event.form_active_days += 1
        event.save()
        
        # Si c'est un multiple de 7 (chaque semaine), notifier l'organisateur
        if event.form_active_days % 7 == 0:
            # Calculer les frais estimés
            storage_fee = event.form_storage_usage * 0.05  # 0.05 XAF par MB
            duration_fee = event.form_active_days * 50  # 50 XAF par jour
            total_fee = storage_fee + duration_fee
            
            send_notification(
                user=event.organizer,
                notification_type='usage_billing_update',
                related_object=event,
                extra_data={
                    'event_title': event.title,
                    'active_days': event.form_active_days,
                    'storage_usage': f"{event.form_storage_usage:.2f} MB",
                    'estimated_cost': f"{total_fee:.2f} XAF"
                },
                channels=['email', 'in_app']
            )