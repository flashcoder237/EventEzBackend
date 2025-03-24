from django.db.models import Count, Sum, Avg, F, Q, Case, When, Value, IntegerField
from django.utils import timezone
import datetime
import pandas as pd
from apps.registrations.models import Registration, TicketType, TicketPurchase
from apps.events.models import Event
from apps.accounts.models import User

class RegistrationAnalyticsService:
    """Services d'analyse des inscriptions"""
    
    @staticmethod
    def get_registration_summary(start_date=None, end_date=None, event_id=None, organizer_id=None):
        """Génère un résumé des statistiques d'inscription"""
        # Filtrer les inscriptions
        registrations = Registration.objects.all()
        
        if start_date:
            registrations = registrations.filter(created_at__date__gte=start_date)
        
        if end_date:
            registrations = registrations.filter(created_at__date__lte=end_date)
        
        if event_id:
            registrations = registrations.filter(event_id=event_id)
        
        if organizer_id:
            registrations = registrations.filter(event__organizer_id=organizer_id)
        
        # Calculs des métriques principales
        total_registrations = registrations.count()
        confirmed_registrations = registrations.filter(status='confirmed').count()
        pending_registrations = registrations.filter(status='pending').count()
        cancelled_registrations = registrations.filter(status='cancelled').count()
        
        # Conversion rate
        conversion_rate = (confirmed_registrations / total_registrations * 100) if total_registrations > 0 else 0
        
        # Répartition par type d'inscription
        registration_types = registrations.values('registration_type').annotate(
            count=Count('id'),
            percentage=Count('id') * 100.0 / total_registrations if total_registrations > 0 else 0
        ).order_by('-count')
        
        # Tendance des inscriptions par semaine
        from django.db.models.functions import TruncWeek
        
        registration_trends = registrations.annotate(
            period=TruncWeek('created_at')
        ).values('period', 'status').annotate(
            count=Count('id')
        ).order_by('period', 'status')
        
        # Formater les tendances pour l'affichage
        trends_data = {}
        for trend in registration_trends:
            period = trend['period']
            status = trend['status']
            count = trend['count']
            
            if period not in trends_data:
                trends_data[period] = {
                    'period': period,
                    'total': 0,
                    'confirmed': 0,
                    'pending': 0,
                    'cancelled': 0
                }
            
            trends_data[period][status] = count
            trends_data[period]['total'] += count
        
        # Convertir en liste et trier
        trends = list(trends_data.values())
        trends.sort(key=lambda x: x['period'])
        
        return {
            'summary': {
                'total_registrations': total_registrations,
                'confirmed_registrations': confirmed_registrations,
                'pending_registrations': pending_registrations,
                'cancelled_registrations': cancelled_registrations,
                'conversion_rate': round(conversion_rate, 2)
            },
            'registration_types': list(registration_types),
            'trends': {
                'interval': 'week',
                'data': trends
            }
        }
    
    @staticmethod
    def get_revenue_summary(start_date=None, end_date=None, event_id=None, organizer_id=None):
        from django.db.models.functions import TruncWeek, TruncMonth

        # Filtrer les paiements
        payments = Payment.objects.filter(status='completed')
        
        if start_date:
            payments = payments.filter(created_at__date__gte=start_date)
        
        if end_date:
            payments = payments.filter(created_at__date__lte=end_date)
        
        if event_id:
            payments = payments.filter(registration__event_id=event_id)
        
        if organizer_id:
            payments = payments.filter(registration__event__organizer_id=organizer_id)
        
        # Utiliser TruncMonth pour éviter l'ambiguïté
        revenue_by_period = payments.annotate(period=TruncMonth('created_at')).values('period').annotate(total_revenue=Sum('amount'),count=Count('id') ).order_by('period')
        
        # Calculs des métriques principales
        total_registrations = registrations.count()
        confirmed_registrations = registrations.filter(status='confirmed').count()
        pending_registrations = registrations.filter(status='pending').count()
        cancelled_registrations = registrations.filter(status='cancelled').count()
        
        # Conversion rate
        conversion_rate = (confirmed_registrations / total_registrations * 100) if total_registrations > 0 else 0
        
        # Répartition par type d'inscription
        registration_types = registrations.values('registration_type').annotate(
            count=Count('id'),
            percentage=Count('id') * 100.0 / total_registrations if total_registrations > 0 else 0
        ).order_by('-count')
        
        # Tendance des inscriptions au fil du temps
        if start_date and end_date:
            date_diff = (end_date - start_date).days
            
            if date_diff > 90:
                interval = 'month'
                trunc_sql = "date_trunc('month', created_at)"
            elif date_diff > 30:
                interval = 'week'
                trunc_sql = "date_trunc('week', created_at)"
            else:
                interval = 'day'
                trunc_sql = "date_trunc('day', created_at)"
        else:
            interval = 'week'
            trunc_sql = "date_trunc('week', created_at)"
        
        registration_trends = registrations.extra(
            select={'period': trunc_sql}
        ).values('period', 'status').annotate(
            count=Count('id')
        ).order_by('period', 'status')
        
        # Formater les tendances pour l'affichage
        trends_data = {}
        for trend in registration_trends:
            period = trend['period']
            status = trend['status']
            count = trend['count']
            
            if period not in trends_data:
                trends_data[period] = {
                    'period': period,
                    'total': 0,
                    'confirmed': 0,
                    'pending': 0,
                    'cancelled': 0
                }
            
            trends_data[period][status] = count
            trends_data[period]['total'] += count
        
        # Convertir en liste et trier
        trends = [data for _, data in trends_data.items()]
        trends.sort(key=lambda x: x['period'])
        
        return {
            'summary': {
                'total_registrations': total_registrations,
                'confirmed_registrations': confirmed_registrations,
                'pending_registrations': pending_registrations,
                'cancelled_registrations': cancelled_registrations,
                'conversion_rate': round(conversion_rate, 2)
            },
            'registration_types': list(registration_types),
            'trends': {
                'interval': interval,
                'data': trends
            }
        }
    
    @staticmethod
    def get_ticket_sales_analysis(event_id=None, organizer_id=None):
        """Analyse détaillée des ventes de billets"""
        # Filtrer les achats de billets
        ticket_purchases = TicketPurchase.objects.all()
        
        if event_id:
            ticket_purchases = ticket_purchases.filter(registration__event_id=event_id)
        
        if organizer_id:
            ticket_purchases = ticket_purchases.filter(registration__event__organizer_id=organizer_id)
        
        # Si aucun achat, retourner un résultat vide
        if not ticket_purchases.exists():
            return {
                'summary': {
                    'total_tickets_sold': 0,
                    'total_revenue': 0,
                    'avg_price_per_ticket': 0
                },
                'ticket_types': [],
                'events': []
            }
        
        # Calcul des métriques principales
        total_tickets = ticket_purchases.aggregate(total=Sum('quantity'))['total'] or 0
        total_revenue = ticket_purchases.aggregate(total=Sum('total_price'))['total'] or 0
        avg_price = total_revenue / total_tickets if total_tickets > 0 else 0
        
        # Analyse par type de billet
        ticket_types_analysis = ticket_purchases.values(
            'ticket_type__name', 
            'ticket_type__event__title',
            'ticket_type__event__id'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('total_price'),
            avg_price=Sum('total_price') / Sum('quantity'),
            discount_total=Sum('discount_amount')
        ).order_by('-quantity_sold')
        
        # Analyse par événement
        events_analysis = ticket_purchases.values(
            'registration__event__id',
            'registration__event__title'
        ).annotate(
            tickets_sold=Sum('quantity'),
            revenue=Sum('total_price'),
            avg_price=Sum('total_price') / Sum('quantity'),
            customers=Count('registration__user', distinct=True)
        ).order_by('-tickets_sold')
        
        return {
            'summary': {
                'total_tickets_sold': total_tickets,
                'total_revenue': total_revenue,
                'avg_price_per_ticket': avg_price
            },
            'ticket_types': list(ticket_types_analysis),
            'events': list(events_analysis)
        }
    
    @staticmethod
    def analyze_form_submissions(event_id=None, organizer_id=None):
        """Analyse des soumissions de formulaire pour les événements d'inscription"""
        # Filtrer les inscriptions avec formulaire
        registrations = Registration.objects.filter(
            registration_type='inscription',
            form_data__isnull=False
        )
        
        if event_id:
            registrations = registrations.filter(event_id=event_id)
        
        if organizer_id:
            registrations = registrations.filter(event__organizer_id=organizer_id)
        
        # Si aucune inscription avec formulaire, retourner un résultat vide
        if not registrations.exists():
            return {
                'total_submissions': 0,
                'total_storage': 0,
                'events': [],
                'field_analysis': []
            }
        
        # Calculs globaux
        total_submissions = registrations.count()
        total_storage = registrations.aggregate(total=Sum('form_data_size'))['total'] or 0
        
        # Analyse par événement
        events_with_forms = Event.objects.filter(
            id__in=registrations.values_list('event_id', flat=True)
        )
        
        events_analysis = []
        for event in events_with_forms:
            event_registrations = registrations.filter(event=event)
            submissions_count = event_registrations.count()
            storage_used = event_registrations.aggregate(total=Sum('form_data_size'))['total'] or 0
            
            events_analysis.append({
                'event_id': str(event.id),
                'event_title': event.title,
                'submissions_count': submissions_count,
                'storage_used': storage_used,
                'form_fields': event.form_fields.count(),
                'estimated_cost': (storage_used * 50) + (event.form_active_days * 50)  # 50 XAF par MB et par jour
            })
        
        # Analyse des champs de formulaires
        # Cette partie nécessiterait d'explorer les données JSON des formulaires
        # C'est une opération complexe qui dépend de la structure des formulaires
        
        # Exemple simple: comptage des champs remplis
        field_analysis = []
        
        return {
            'total_submissions': total_submissions,
            'total_storage': total_storage,
            'events': events_analysis,
            'field_analysis': field_analysis
        }