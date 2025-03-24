from django.db.models import Sum, Count, Avg, F, Min, Max, Window, ExpressionWrapper, DateField
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, TruncDay
from django.utils import timezone
import datetime
import pandas as pd
import numpy as np
from apps.payments.models import Payment
from apps.events.models import Event
from django.db.models import FloatField

class PaymentAnalyticsService:
    """Services d'analyse des paiements et revenus"""
    
    @staticmethod
    def get_revenue_summary(start_date=None, end_date=None, event_id=None, organizer_id=None):
        """Génère un résumé des revenus avec filtres optionnels"""
        
        # Requête de base pour les paiements complétés
        payments = Payment.objects.filter(status='completed')
        
        # Appliquer les filtres
        if start_date:
            payments = payments.filter(payment_date__gte=start_date)
        
        if end_date:
            payments = payments.filter(payment_date__lte=end_date)
        
        if event_id:
            payments = payments.filter(registration__event_id=event_id)
        
        if organizer_id:
            payments = payments.filter(registration__event__organizer_id=organizer_id)
        
        # Aucun paiement trouvé
        if not payments.exists():
            return {
                'total_revenue': 0,
                'avg_transaction': 0,
                'payment_count': 0,
                'revenue_by_method': [],
                'usage_based_revenue': 0,
                'ticket_sales_revenue': 0,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        
        # Calculs des métriques principales
        total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0
        avg_transaction = payments.aggregate(avg=Avg('amount'))['avg'] or 0
        payment_count = payments.count()
        min_amount = payments.aggregate(min=Min('amount'))['min'] or 0
        max_amount = payments.aggregate(max=Max('amount'))['max'] or 0
        
        # Répartition par méthode de paiement
        revenue_by_method = payments.values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id'),
            percentage=ExpressionWrapper(
                Sum('amount') * 100.0 / total_revenue,
                output_field=FloatField()
            )
        ).order_by('-total')
        
        # Répartition par type de revenu
        usage_based_revenue = payments.filter(is_usage_based=True).aggregate(total=Sum('amount'))['total'] or 0
        ticket_sales_revenue = total_revenue - usage_based_revenue
        
        # Répartition par période
        if start_date and end_date:
            # Analyse par mois si la période est supérieure à 60 jours
            if (end_date - start_date).days > 60:
                revenue_by_period = payments.annotate(
                    period=TruncMonth('payment_date')
                ).values('period').annotate(
                    total=Sum('amount'),
                    count=Count('id')
                ).order_by('period')
                period_type = 'monthly'
            else:
                # Analyse par jour
                revenue_by_period = payments.annotate(
                    period=TruncDay('payment_date')
                ).values('period').annotate(
                    total=Sum('amount'),
                    count=Count('id')
                ).order_by('period')
                period_type = 'daily'
        else:
            # Par défaut, analyse par mois des 12 derniers mois
            twelve_months_ago = timezone.now() - datetime.timedelta(days=365)
            revenue_by_period = payments.filter(
                payment_date__gte=twelve_months_ago
            ).annotate(
                period=TruncMonth('payment_date')
            ).values('period').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('period')
            period_type = 'monthly'
        
        return {
            'total_revenue': total_revenue,
            'avg_transaction': avg_transaction,
            'payment_count': payment_count,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'revenue_by_method': list(revenue_by_method),
            'revenue_distribution': {
                'usage_based_revenue': usage_based_revenue,
                'ticket_sales_revenue': ticket_sales_revenue,
                'usage_percentage': (usage_based_revenue / total_revenue * 100) if total_revenue > 0 else 0,
                'ticket_percentage': (ticket_sales_revenue / total_revenue * 100) if total_revenue > 0 else 0
            },
            'revenue_by_period': {
                'type': period_type,
                'data': list(revenue_by_period)
            },
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
    
    @staticmethod
    def get_revenue_trends(interval='day', periods=30, organizer_id=None):
        """Analyse des tendances de revenus avec prédiction pour les périodes futures"""
        
        # Définir la date de début en fonction de l'intervalle et du nombre de périodes
        if interval == 'day':
            start_date = timezone.now() - datetime.timedelta(days=periods)
            trunc_func = TruncDay('payment_date')
            future_periods = 7  # Prédire 7 jours
        elif interval == 'week':
            start_date = timezone.now() - datetime.timedelta(weeks=periods)
            trunc_func = TruncWeek('payment_date')
            future_periods = 4  # Prédire 4 semaines
        elif interval == 'month':
            start_date = timezone.now() - datetime.timedelta(days=periods*30)
            trunc_func = TruncMonth('payment_date')
            future_periods = 3  # Prédire 3 mois
        else:
            # Par défaut, utiliser l'intervalle journalier
            start_date = timezone.now() - datetime.timedelta(days=periods)
            trunc_func = TruncDay('payment_date')
            future_periods = 7
        
        # Filtrer les paiements
        payments = Payment.objects.filter(
            status='completed',
            payment_date__gte=start_date
        )
        
        if organizer_id:
            payments = payments.filter(registration__event__organizer_id=organizer_id)
        
        # Agréger par période
        trends = payments.annotate(
            period=trunc_func
        ).values('period').annotate(
            revenue=Sum('amount'),
            count=Count('id')
        ).order_by('period')
        
        # Convertir en DataFrame pour analyse et prédiction
        trends_data = list(trends)
        
        if not trends_data:
            return {
                'historical': [],
                'predicted': [],
                'interval': interval
            }
        
        df = pd.DataFrame(trends_data)
        
        # Calculer la moyenne mobile
        if len(df) >= 7 and interval == 'day':
            df['moving_avg_7d'] = df['revenue'].rolling(window=7).mean()
        
        # Préparer les données historiques
        historical = []
        for _, row in df.iterrows():
            data_point = {
                'period': row['period'],
                'revenue': float(row['revenue']),
                'count': int(row['count']),
            }
            if 'moving_avg_7d' in df.columns:
                data_point['moving_avg_7d'] = float(row['moving_avg_7d']) if not np.isnan(row['moving_avg_7d']) else None
            
            historical.append(data_point)
        
        # Prédiction pour les périodes futures
        predicted = []
        
        # Méthode de prédiction simple basée sur la moyenne des N dernières périodes
        if len(df) >= 5:
            # Utiliser les 5 dernières périodes pour la prédiction
            last_periods = df.tail(5)
            avg_revenue = last_periods['revenue'].mean()
            avg_count = last_periods['count'].mean()
            
            last_date = df['period'].max()
            
            # Générer les dates des périodes futures
            for i in range(1, future_periods + 1):
                if interval == 'day':
                    next_date = last_date + datetime.timedelta(days=i)
                elif interval == 'week':
                    next_date = last_date + datetime.timedelta(weeks=i)
                elif interval == 'month':
                    # Approximation pour les mois
                    next_date = last_date + datetime.timedelta(days=i*30)
                
                predicted.append({
                    'period': next_date,
                    'revenue': float(avg_revenue),
                    'count': float(avg_count),
                    'is_prediction': True
                })
        
        return {
            'historical': historical,
            'predicted': predicted,
            'interval': interval
        }
    
    @staticmethod
    def get_payment_methods_analysis(start_date=None, end_date=None, organizer_id=None):
        """Analyse détaillée de l'utilisation des méthodes de paiement"""
        
        # Filtrer les paiements
        payments = Payment.objects.filter(status='completed')
        
        if start_date:
            payments = payments.filter(payment_date__gte=start_date)
        
        if end_date:
            payments = payments.filter(payment_date__lte=end_date)
        
        if organizer_id:
            payments = payments.filter(registration__event__organizer_id=organizer_id)
        
        if not payments.exists():
            return {
                'methods': [],
                'trends': [],
                'conversion': {
                    'mtn_money': 0,
                    'orange_money': 0,
                    'credit_card': 0,
                    'bank_transfer': 0
                }
            }
        
        # Analyse par méthode de paiement
        methods = payments.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount'),
            avg_amount=Avg('amount'),
            percentage=Count('id') * 100.0 / payments.count()
        ).order_by('-count')
        
        # Évolution des méthodes de paiement au fil du temps
        payment_trends = []
        
        # Déterminer l'intervalle approprié en fonction de la période
        if start_date and end_date:
            days_diff = (end_date - start_date).days
            
            if days_diff > 180:  # Plus de 6 mois
                interval = 'month'
                trunc_func = TruncMonth('payment_date')
            elif days_diff > 30:  # Plus d'un mois
                interval = 'week'
                trunc_func = TruncWeek('payment_date')
            else:
                interval = 'day'
                trunc_func = TruncDay('payment_date')
        else:
            # Par défaut, analyser par mois
            interval = 'month'
            trunc_func = TruncMonth('payment_date')
        
        # Analyse de l'évolution des méthodes de paiement
        method_trends = payments.annotate(
            period=trunc_func
        ).values('period', 'payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('period', 'payment_method')
        
        # Formatage des données de tendance
        method_trends_data = {}
        for trend in method_trends:
            period = trend['period']
            method = trend['payment_method']
            
            if period not in method_trends_data:
                method_trends_data[period] = {
                    'period': period,
                    'total': 0
                }
            
            method_trends_data[period][method] = trend['total']
            method_trends_data[period]['total'] += trend['total']
        
        # Convertir en liste
        for period, data in method_trends_data.items():
            payment_trends.append(data)
        
        # Trier par période
        payment_trends.sort(key=lambda x: x['period'])
        
        # Analyse des taux de conversion par méthode de paiement
        # (Ratio des paiements réussis par rapport aux tentatives)
        conversion_rates = {
            'mtn_money': 0.95,  # Exemple: 95% de succès pour MTN Money
            'orange_money': 0.92,
            'credit_card': 0.88,
            'bank_transfer': 0.99
        }
        
        return {
            'methods': list(methods),
            'trends': {
                'interval': interval,
                'data': payment_trends
            },
            'conversion': conversion_rates
        }