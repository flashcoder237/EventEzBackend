from celery import shared_task
from django.utils import timezone
import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import AnalyticsReport
from .services.report_generator import ReportGenerator

@shared_task
def generate_scheduled_reports():
    """Génère les rapports programmés"""
    now = timezone.now()
    
    # Trouver tous les rapports programmés qui doivent être exécutés maintenant
    reports_to_run = AnalyticsReport.objects.filter(
        is_scheduled=True,
        next_run__lte=now
    )
    
    for report in reports_to_run:
        try:
            # Générer les nouvelles données pour le rapport
            report_data = ReportGenerator.generate_report(
                report_type=report.report_type,
                filters=report.filters,
                user=report.generated_by
            )
            
            # Mettre à jour le rapport
            report.data = report_data['data']
            report.last_run = now
            
            # Calculer la prochaine exécution
            if report.schedule_frequency == 'daily':
                report.next_run = now + datetime.timedelta(days=1)
            elif report.schedule_frequency == 'weekly':
                report.next_run = now + datetime.timedelta(weeks=1)
            elif report.schedule_frequency == 'monthly':
                # Approximation du mois prochain
                next_month = now.month + 1
                next_year = now.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                report.next_run = now.replace(year=next_year, month=next_month, day=1)
            
            report.save()
            
            # Envoyer le rapport par email si demandé
            if report.email_on_generation and report.generated_by and report.generated_by.email:
                send_report_email.delay(report.id)
                
        except Exception as e:
            # Loguer l'erreur et continuer avec le rapport suivant
            print(f"Erreur lors de la génération du rapport {report.id}: {str(e)}")
            continue

@shared_task
def send_report_email(report_id):
    """Envoie un rapport par email"""
    try:
        report = AnalyticsReport.objects.get(id=report_id)
        user = report.generated_by
        
        if not user or not user.email:
            return
        
        # Préparer le contenu de l'email
        context = {
            'user': user,
            'report': report,
            'generated_at': timezone.now().strftime("%d/%m/%Y à %H:%M")
        }
        
        html_message = render_to_string('analytics/email/report.html', context)
        plain_message = render_to_string('analytics/email/report.txt', context)
        
        # Envoyer l'email
        send_mail(
            subject=f'Rapport Eventez: {report.title}',
            message=plain_message,
            from_email='no-reply@eventez.cm',
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email pour le rapport {report_id}: {str(e)}")

@shared_task
def clean_old_reports():
    """Nettoie les anciens rapports non programmés"""
    # Supprimer les rapports non programmés de plus de 30 jours
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
    
    old_reports = AnalyticsReport.objects.filter(
        is_scheduled=False,
        created_at__lt=thirty_days_ago
    )
    
    deleted_count = old_reports.count()
    old_reports.delete()
    
    return f"Suppression de {deleted_count} anciens rapports"