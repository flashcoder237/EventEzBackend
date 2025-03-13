import string
import random
import json
from decimal import Decimal
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from apps.notifications.models import Notification, NotificationTemplate

def generate_unique_code(length=8, prefix=''):
    """Génère un code aléatoire unique"""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(length))
    return f"{prefix}{code}" if prefix else code

def calculate_form_data_size(form_data):
    """Calcule la taille des données de formulaire en MB"""
    json_string = json.dumps(form_data)
    bytes_size = len(json_string.encode('utf-8'))
    mb_size = bytes_size / (1024 * 1024)
    return round(mb_size, 6)

def send_notification(user, notification_type, related_object=None, extra_data=None, channels=None):
    """
    Envoie une notification à l'utilisateur via différents canaux
    
    :param user: L'utilisateur destinataire
    :param notification_type: Type de notification (doit correspondre à un template existant)
    :param related_object: Objet lié à la notification (événement, inscription, etc.)
    :param extra_data: Données supplémentaires pour le template
    :param channels: Liste des canaux à utiliser ('email', 'sms', 'push', 'in_app')
    """
    try:
        # Récupérer le template
        template = NotificationTemplate.objects.get(notification_type=notification_type)
        
        # Définir les canaux par défaut si non spécifiés
        if not channels:
            channels = ['email', 'in_app']
        
        # Préparer les données de contexte
        context = extra_data or {}
        if related_object:
            context['object'] = related_object
            related_object_id = str(related_object.id)
            related_object_type = related_object.__class__.__name__.lower()
        else:
            related_object_id = ''
            related_object_type = ''
        
        # Créer une notification in-app si demandé
        if 'in_app' in channels:
            notification = Notification.objects.create(
                user=user,
                title=template.in_app_title.format(**context) if template.in_app_title else template.name,
                message=template.in_app_body.format(**context) if template.in_app_body else '',
                notification_type=notification_type,
                related_object_id=related_object_id,
                related_object_type=related_object_type,
                channel='in_app',
                is_sent=True,
                sent_at=timezone.now(),
                extra_data=context
            )
        
        # Envoyer un email si demandé
        if 'email' in channels and user.email and template.email_subject and template.email_body:
            subject = template.email_subject.format(**context)
            message = template.email_body.format(**context)
            
            email = EmailMessage(
                subject=subject,
                body=message,
                to=[user.email]
            )
            email.send()
            
            # Enregistrer la notification
            Notification.objects.create(
                user=user,
                title=subject,
                message=message,
                notification_type=notification_type,
                related_object_id=related_object_id,
                related_object_type=related_object_type,
                channel='email',
                is_sent=True,
                sent_at=timezone.now(),
                email_subject=subject,
                extra_data=context
            )
        
        # Envoyer un SMS si demandé
        if 'sms' in channels and user.phone_number and template.sms_body:
            message = template.sms_body.format(**context)
            
            # Intégration SMS à implémenter
            # send_sms(user.phone_number, message)
            
            # Enregistrer la notification
            Notification.objects.create(
                user=user,
                title='SMS Notification',
                message=message,
                notification_type=notification_type,
                related_object_id=related_object_id,
                related_object_type=related_object_type,
                channel='sms',
                is_sent=True,
                sent_at=timezone.now(),
                phone_number=user.phone_number,
                extra_data=context
            )
        
        return True
    
    except NotificationTemplate.DoesNotExist:
        # Log l'erreur
        import logging
        logger = logging.getLogger('apps')
        logger.error(f"Template de notification non trouvé pour le type {notification_type}")
        return False
    except Exception as e:
        # Log l'erreur
        import logging
        logger = logging.getLogger('apps')
        logger.error(f"Erreur lors de l'envoi de la notification: {str(e)}")
        return False