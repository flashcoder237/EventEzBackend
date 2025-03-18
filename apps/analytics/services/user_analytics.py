from django.db.models import Count, Sum, Avg, F, Q, Case, When, Value, IntegerField
from django.utils import timezone
import datetime
from apps.accounts.models import User
from apps.events.models import Event
from apps.registrations.models import Registration
from apps.payments.models import Payment

class UserAnalyticsService:
    """Services d'analyse des utilisateurs"""
    
    @staticmethod
    def get_user_growth(interval='month', periods=12):
        """Analyse la croissance des utilisateurs au fil du temps"""
        # Définir la date de début en fonction de l'intervalle et du nombre de périodes
        if interval == 'day':
            start_date = timezone.now() - datetime.timedelta(days=periods)
        elif interval == 'week':
            start_date = timezone.now() - datetime.timedelta(weeks=periods)
        elif interval == 'month':
            start_date = timezone.now() - datetime.timedelta(days=periods*30)
        elif interval == 'year':
            start_date = timezone.now() - datetime.timedelta(days=periods*365)
        else:
            # Par défaut, utiliser l'intervalle mensuel
            start_date = timezone.now() - datetime.timedelta(days=periods*30)
            interval = 'month'
        
        # Sélectionner la fonction de troncature appropriée
        if interval == 'day':
            trunc_sql = "date_trunc('day', date_joined)"
        elif interval == 'week':
            trunc_sql = "date_trunc('week', date_joined)"
        elif interval == 'month':
            trunc_sql = "date_trunc('month', date_joined)"
        elif interval == 'year':
            trunc_sql = "date_trunc('year', date_joined)"
        
        # Obtenir les nouveaux utilisateurs par période
        new_users = User.objects.filter(
            date_joined__gte=start_date
        ).extra(
            select={'period': trunc_sql}
        ).values('period').annotate(
            count=Count('id')
        ).order_by('period')
        
        # Calculer le nombre cumulatif d'utilisateurs
        result = []
        cumulative_count = User.objects.filter(date_joined__lt=start_date).count()
        
        for item in new_users:
            cumulative_count += item['count']
            result.append({
                'period': item['period'],
                'new_users': item['count'],
                'cumulative_users': cumulative_count
            })
        
        return {
            'interval': interval,
            'data': result,
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(last_login__gte=timezone.now() - datetime.timedelta(days=30)).count(),
            'verified_users': User.objects.filter(is_verified=True).count()
        }
    
    @staticmethod
    def get_user_segmentation():
        """Segmente les utilisateurs par rôle, activité et engagement"""
        # Nombre total d'utilisateurs
        total_users = User.objects.count()
        
        # Segmentation par rôle
        roles = User.objects.values('role').annotate(
            count=Count('id'),
            percentage=Count('id') * 100.0 / total_users
        ).order_by('-count')
        
        # Segmentation par type d'organisateur
        organizer_types = User.objects.filter(
            role='organizer'
        ).values('organizer_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Segmentation par statut de vérification
        verification = [
            {
                'status': 'verified',
                'count': User.objects.filter(is_verified=True).count(),
                'percentage': User.objects.filter(is_verified=True).count() * 100.0 / total_users
            },
            {
                'status': 'not_verified',
                'count': User.objects.filter(is_verified=False).count(),
                'percentage': User.objects.filter(is_verified=False).count() * 100.0 / total_users
            }
        ]
        
        # Segmentation par activité (dernière connexion)
        activity = [
            {
                'segment': 'active_7d',
                'description': 'Actifs ces 7 derniers jours',
                'count': User.objects.filter(last_login__gte=timezone.now() - datetime.timedelta(days=7)).count()
            },
            {
                'segment': 'active_30d',
                'description': 'Actifs ces 30 derniers jours',
                'count': User.objects.filter(
                    last_login__gte=timezone.now() - datetime.timedelta(days=30),
                    last_login__lt=timezone.now() - datetime.timedelta(days=7)
                ).count()
            },
            {
                'segment': 'inactive_30d',
                'description': 'Inactifs depuis plus de 30 jours',
                'count': User.objects.filter(
                    Q(last_login__lt=timezone.now() - datetime.timedelta(days=30)) | 
                    Q(last_login__isnull=True)
                ).count()
            }
        ]
        
        # Segmentation par engagement (nombre d'inscriptions)
        # Créer des segments: 0, 1-2, 3-5, 6+
        engagement = []
        
        users_with_no_registrations = User.objects.annotate(
            registration_count=Count('registrations')
        ).filter(registration_count=0).count()
        
        engagement.append({
            'segment': 'no_registrations',
            'description': 'Aucune inscription',
            'count': users_with_no_registrations,
            'percentage': users_with_no_registrations * 100.0 / total_users
        })
        
        users_with_1_2_registrations = User.objects.annotate(
            registration_count=Count('registrations')
        ).filter(registration_count__gte=1, registration_count__lte=2).count()
        
        engagement.append({
            'segment': '1_2_registrations',
            'description': '1-2 inscriptions',
            'count': users_with_1_2_registrations,
            'percentage': users_with_1_2_registrations * 100.0 / total_users
        })
        
        users_with_3_5_registrations = User.objects.annotate(
            registration_count=Count('registrations')
        ).filter(registration_count__gte=3, registration_count__lte=5).count()
        
        engagement.append({
            'segment': '3_5_registrations',
            'description': '3-5 inscriptions',
            'count': users_with_3_5_registrations,
            'percentage': users_with_3_5_registrations * 100.0 / total_users
        })
        
        users_with_6plus_registrations = User.objects.annotate(
            registration_count=Count('registrations')
        ).filter(registration_count__gte=6).count()
        
        engagement.append({
            'segment': '6plus_registrations',
            'description': '6+ inscriptions',
            'count': users_with_6plus_registrations,
            'percentage': users_with_6plus_registrations * 100.0 / total_users
        })
        
        return {
            'total_users': total_users,
            'roles': list(roles),
            'organizer_types': list(organizer_types),
            'verification': verification,
            'activity': activity,
            'engagement': engagement
        }
    
    @staticmethod
    def get_user_retention(cohort_month=None, max_months=12):
        """Analyse la rétention des utilisateurs par cohorte mensuelle"""
        # Si aucun mois de cohorte n'est spécifié, analyser les 12 derniers mois
        if not cohort_month:
            end_date = timezone.now().replace(day=1) - datetime.timedelta(days=1)  # Mois précédent
            start_date = end_date - datetime.timedelta(days=365)  # 12 mois avant
        else:
            # Cohort_month devrait être au format 'YYYY-MM'
            year, month = map(int, cohort_month.split('-'))
            start_date = datetime.date(year, month, 1)
            end_date = datetime.date(year + (month + max_months - 1) // 12, (month + max_months - 1) % 12 + 1, 1) - datetime.timedelta(days=1)
        
        # Créer des cohortes mensuelles
        cohorts = []
        current_date = start_date
        
        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            
            # Obtenir les utilisateurs qui se sont inscrits ce mois-ci
            cohort_users = User.objects.filter(
                date_joined__year=year,
                date_joined__month=month
            )
            
            cohort_size = cohort_users.count()
            
            if cohort_size > 0:
                cohort_data = {
                    'cohort': f"{year}-{month:02d}",
                    'cohort_size': cohort_size,
                    'retention': []
                }
                
                # Calculer la rétention pour chaque mois suivant (jusqu'à max_months)
                for i in range(max_months):
                    next_month = month + i
                    next_year = year + (next_month - 1) // 12
                    next_month = (next_month - 1) % 12 + 1
                    
                    # Utilisateurs actifs ce mois-ci (qui ont eu une connexion)
                    active_users = cohort_users.filter(
                        last_login__year=next_year,
                        last_login__month=next_month
                    ).count()
                    
                    retention_rate = (active_users / cohort_size) * 100 if cohort_size > 0 else 0
                    
                    cohort_data['retention'].append({
                        'month': i,
                        'active_users': active_users,
                        'retention_rate': round(retention_rate, 2)
                    })
                
                cohorts.append(cohort_data)
            
            # Passer au mois suivant
            if month == 12:
                current_date = datetime.date(year + 1, 1, 1)
            else:
                current_date = datetime.date(year, month + 1, 1)
        
        return {
            'cohorts': cohorts,
            'start_date': start_date,
            'end_date': end_date
        }