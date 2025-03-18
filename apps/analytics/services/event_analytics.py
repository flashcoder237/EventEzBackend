from django.db.models import Count, Sum, Avg, F, Case, When, IntegerField, Q
from django.utils import timezone
import datetime
import pandas as pd
import numpy as np
from apps.events.models import Event
from apps.registrations.models import Registration, TicketType, TicketPurchase
from apps.payments.models import Payment

class EventAnalyticsService:
    """Services d'analyse des événements"""
    
    @staticmethod
    def get_event_summary(event_id=None, organizer_id=None, start_date=None, end_date=None):
        """Génère un résumé des statistiques d'événements"""
        
        # Construire la requête de base
        queryset = Event.objects.all()
        
        # Appliquer les filtres
        if event_id:
            queryset = queryset.filter(id=event_id)
        
        if organizer_id:
            queryset = queryset.filter(organizer_id=organizer_id)
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        # Calculer les métriques
        total_events = queryset.count()
        upcoming_events = queryset.filter(start_date__gt=timezone.now()).count()
        ongoing_events = queryset.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).count()
        completed_events = queryset.filter(
            end_date__lt=timezone.now()
        ).count()
        
        # Types d'événements
        event_types = queryset.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Catégories d'événements
        categories = queryset.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Taux de remplissage moyen (inscriptions / capacité)
        events_with_registrations = []
        for event in queryset:
            registrations_count = Registration.objects.filter(event=event).count()
            max_capacity = 0
            
            if event.event_type == 'billetterie':
                # Pour les événements avec billetterie, la capacité est la somme des billets disponibles
                max_capacity = TicketType.objects.filter(event=event).aggregate(
                    total=Sum('quantity_total')
                )['total'] or 0
            
            if max_capacity > 0:
                fill_rate = (registrations_count / max_capacity) * 100
            else:
                fill_rate = 0
            
            events_with_registrations.append({
                'id': str(event.id),
                'title': event.title,
                'registrations_count': registrations_count,
                'max_capacity': max_capacity,
                'fill_rate': round(fill_rate, 2)
            })
        
        # Calculer le taux de remplissage moyen
        if events_with_registrations:
            avg_fill_rate = sum(e['fill_rate'] for e in events_with_registrations) / len(events_with_registrations)
        else:
            avg_fill_rate = 0
        
        return {
            'total_events': total_events,
            'upcoming_events': upcoming_events,
            'ongoing_events': ongoing_events,
            'completed_events': completed_events,
            'event_types': list(event_types),
            'categories': list(categories),
            'avg_fill_rate': round(avg_fill_rate, 2),
            'events_details': events_with_registrations[:10]  # Limiter à 10 événements pour l'aperçu
        }
    
    @staticmethod
    def get_event_performance(event_id):
        """Analyse détaillée des performances d'un événement spécifique"""
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return {'error': 'Événement non trouvé'}
        
        # Inscriptions
        registrations = Registration.objects.filter(event=event)
        total_registrations = registrations.count()
        confirmed_registrations = registrations.filter(status='confirmed').count()
        
        # Conversion des inscriptions
        conversion_rate = (confirmed_registrations / total_registrations * 100) if total_registrations > 0 else 0
        
        # Revenus
        payments = Payment.objects.filter(
            registration__event=event,
            status='completed'
        )
        total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Analyse des inscriptions au fil du temps
        registrations_by_date = registrations.extra(
            select={'date': "DATE(created_at)"}
        ).values('date').annotate(count=Count('id')).order_by('date')
        
        # Pour les événements avec billetterie, analyser les ventes par type de billet
        ticket_sales = {}
        if event.event_type == 'billetterie':
            ticket_purchases = TicketPurchase.objects.filter(registration__event=event)
            
            for ticket_type in TicketType.objects.filter(event=event):
                sales = ticket_purchases.filter(ticket_type=ticket_type)
                quantity_sold = sales.aggregate(total=Sum('quantity'))['total'] or 0
                revenue = sales.aggregate(total=Sum('total_price'))['total'] or 0
                
                ticket_sales[ticket_type.name] = {
                    'quantity_sold': quantity_sold,
                    'quantity_total': ticket_type.quantity_total,
                    'revenue': revenue,
                    'sell_through_rate': (quantity_sold / ticket_type.quantity_total * 100) if ticket_type.quantity_total > 0 else 0
                }
        
        # Pour les événements avec formulaire, analyser l'utilisation de stockage
        form_usage = {}
        if event.event_type == 'inscription':
            form_usage = {
                'storage_usage': event.form_storage_usage,
                'active_days': event.form_active_days,
                'estimated_cost': (event.form_storage_usage * 50) + (event.form_active_days * 50)  # 50 XAF par MB et par jour
            }
        
        return {
            'event_id': str(event.id),
            'title': event.title,
            'event_type': event.event_type,
            'status': event.status,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'registrations': {
                'total': total_registrations,
                'confirmed': confirmed_registrations,
                'conversion_rate': round(conversion_rate, 2),
                'timeline': list(registrations_by_date)
            },
            'revenue': {
                'total': total_revenue,
                'average_per_registration': round(total_revenue / confirmed_registrations, 2) if confirmed_registrations > 0 else 0
            },
            'ticket_sales': ticket_sales,
            'form_usage': form_usage
        }
    
    @staticmethod
    def get_registration_timeline(event_id, interval='day'):
        """Génère une timeline des inscriptions pour un événement"""
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return {'error': 'Événement non trouvé'}
        
        registrations = Registration.objects.filter(event=event).order_by('created_at')
        
        # Convertir en DataFrame pandas pour l'analyse
        if not registrations.exists():
            return []
        
        # Extraire les données nécessaires
        reg_data = []
        for reg in registrations:
            reg_data.append({
                'created_at': reg.created_at,
                'status': reg.status
            })
        
        df = pd.DataFrame(reg_data)
        
        # Définir l'intervalle pour le regroupement
        if interval == 'hour':
            df['interval'] = df['created_at'].dt.floor('H')
        elif interval == 'day':
            df['interval'] = df['created_at'].dt.date
        elif interval == 'week':
            df['interval'] = df['created_at'].dt.to_period('W').dt.start_time
        elif interval == 'month':
            df['interval'] = df['created_at'].dt.to_period('M').dt.start_time
        
        # Grouper et compter
        timeline = df.groupby(['interval', 'status']).size().unstack(fill_value=0).reset_index()
        
        # Formater pour la sortie
        result = []
        for _, row in timeline.iterrows():
            data_point = {
                'interval': row['interval'],
                'pending': int(row.get('pending', 0)),
                'confirmed': int(row.get('confirmed', 0)),
                'cancelled': int(row.get('cancelled', 0)),
                'total': int(row.get('pending', 0) + row.get('confirmed', 0) + row.get('cancelled', 0))
            }
            result.append(data_point)
        
        return result
    
    @staticmethod
    def predict_attendance(event_id):
        """Prédit le nombre d'inscriptions attendues pour un événement à venir"""
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return {'error': 'Événement non trouvé'}
        
        # Vérifier que l'événement est à venir
        if event.start_date < timezone.now():
            return {'error': 'L\'événement a déjà commencé ou est terminé'}
        
        # Trouver des événements similaires (même catégorie, même organisateur)
        similar_events = Event.objects.filter(
            category=event.category,
            organizer=event.organizer,
            status='completed'
        )
        
        if not similar_events.exists():
            # Utiliser tous les événements complétés si aucun événement similaire n'est trouvé
            similar_events = Event.objects.filter(status='completed')
        
        # Collecter les données d'inscription pour les événements similaires
        similar_events_data = []
        for similar_event in similar_events:
            registrations_count = Registration.objects.filter(
                event=similar_event, 
                status='confirmed'
            ).count()
            
            similar_events_data.append({
                'id': str(similar_event.id),
                'title': similar_event.title,
                'registrations_count': registrations_count,
                'category': similar_event.category.name if similar_event.category else None,
                'event_type': similar_event.event_type
            })
        
        # Calculer la prédiction
        if similar_events_data:
            avg_registrations = sum(e['registrations_count'] for e in similar_events_data) / len(similar_events_data)
            predicted_attendance = round(avg_registrations, 0)
        else:
            predicted_attendance = 0
        
        # Obtenir les inscriptions actuelles
        current_registrations = Registration.objects.filter(
            event=event,
            status='confirmed'
        ).count()
        
        return {
            'event_id': str(event.id),
            'title': event.title,
            'prediction': {
                'predicted_attendance': int(predicted_attendance),
                'current_registrations': current_registrations,
                'remaining_to_predict': max(0, int(predicted_attendance) - current_registrations),
                'confidence': 'medium',  # Pourrait être ajusté en fonction du nombre d'événements similaires
                'based_on_similar_events': len(similar_events_data)
            },
            'similar_events': similar_events_data[:5]  # Limiter à 5 événements pour l'aperçu
        }