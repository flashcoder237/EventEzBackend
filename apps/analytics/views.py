from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.http import HttpResponse
import datetime
import json
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import AnalyticsReport, DashboardWidget, Dashboard
from .serializers import (
    AnalyticsReportSerializer, 
    DashboardWidgetSerializer, 
    DashboardSerializer,
    ReportGenerationSerializer
)
from .services.event_analytics import EventAnalyticsService
from .services.payment_analytics import PaymentAnalyticsService
from .services.user_analytics import UserAnalyticsService
from .services.registration_analytics import RegistrationAnalyticsService
from .services.report_generator import ReportGenerator

from apps.core.permissions import IsAdminOrOrganizer, IsOwnerOrReadOnly

class AnalyticsViewSet(viewsets.ViewSet):
    """Vues pour accéder aux analyses en temps réel"""
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOrganizer]
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Obtenir un résumé pour le tableau de bord"""
        # Filtres
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Si l'utilisateur est un organisateur, filtrer par ses événements
        organizer_id = None
        if request.user.role == 'organizer':
            organizer_id = str(request.user.id)
        
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Résumé des événements
        event_summary = EventAnalyticsService.get_event_summary(
            organizer_id=organizer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Résumé des revenus
        revenue_summary = PaymentAnalyticsService.get_revenue_summary(
            start_date=start_date,
            end_date=end_date,
            organizer_id=organizer_id
        )
        
        # Résumé des inscriptions
        registration_summary = RegistrationAnalyticsService.get_registration_summary(
            start_date=start_date,
            end_date=end_date,
            organizer_id=organizer_id
        )
        
        return Response({
            'event_summary': event_summary,
            'revenue_summary': revenue_summary,
            'registration_summary': registration_summary,
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'organizer_id': organizer_id
            }
        })
    
    @action(detail=False, methods=['get'])
    def events(self, request):
        """Analyses relatives aux événements"""
        event_id = request.query_params.get('event_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Si l'utilisateur est un organisateur, filtrer par ses événements
        organizer_id = None
        if request.user.role == 'organizer':
            organizer_id = str(request.user.id)
        
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if event_id:
            # Analyse détaillée d'un événement spécifique
            data = EventAnalyticsService.get_event_performance(event_id)
        else:
            # Résumé global des événements
            data = EventAnalyticsService.get_event_summary(
                organizer_id=organizer_id,
                start_date=start_date,
                end_date=end_date
            )
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def event_registrations(self, request):
        """Analyses des inscriptions pour un événement spécifique"""
        event_id = request.query_params.get('event_id')
        interval = request.query_params.get('interval', 'day')
        
        if not event_id:
            return Response(
                {'error': 'ID de l\'événement requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = EventAnalyticsService.get_registration_timeline(
            event_id=event_id,
            interval=interval
        )
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def predict_attendance(self, request):
        """Prédiction du nombre d'inscriptions pour un événement"""
        event_id = request.query_params.get('event_id')
        
        if not event_id:
            return Response(
                {'error': 'ID de l\'événement requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = EventAnalyticsService.predict_attendance(event_id)
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """Analyses relatives aux revenus"""
        analysis_type = request.query_params.get('analysis_type', 'summary')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        event_id = request.query_params.get('event_id')
        
        # Si l'utilisateur est un organisateur, filtrer par ses événements
        organizer_id = None
        if request.user.role == 'organizer':
            organizer_id = str(request.user.id)
        
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if analysis_type == 'trends':
            interval = request.query_params.get('interval', 'day')
            periods = int(request.query_params.get('periods', 30))
            
            data = PaymentAnalyticsService.get_revenue_trends(
                interval=interval,
                periods=periods,
                organizer_id=organizer_id
            )
        elif analysis_type == 'methods':
            data = PaymentAnalyticsService.get_payment_methods_analysis(
                start_date=start_date,
                end_date=end_date,
                organizer_id=organizer_id
            )
        else:
            # Résumé par défaut
            data = PaymentAnalyticsService.get_revenue_summary(
                start_date=start_date,
                end_date=end_date,
                event_id=event_id,
                organizer_id=organizer_id
            )
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """Analyses relatives aux utilisateurs"""
        analysis_type = request.query_params.get('analysis_type', 'growth')
        
        if analysis_type == 'growth':
            interval = request.query_params.get('interval', 'month')
            periods = int(request.query_params.get('periods', 12))
            
            data = UserAnalyticsService.get_user_growth(
                interval=interval,
                periods=periods
            )
        elif analysis_type == 'segmentation':
            data = UserAnalyticsService.get_user_segmentation()
        elif analysis_type == 'retention':
            cohort_month = request.query_params.get('cohort_month')
            max_months = int(request.query_params.get('max_months', 12))
            
            data = UserAnalyticsService.get_user_retention(
                cohort_month=cohort_month,
                max_months=max_months
            )
        else:
            # Type d'analyse non reconnu
            return Response(
                {'error': 'Type d\'analyse non valide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def registrations(self, request):
        """Analyses relatives aux inscriptions"""
        analysis_type = request.query_params.get('analysis_type', 'summary')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        event_id = request.query_params.get('event_id')
        
        # Si l'utilisateur est un organisateur, filtrer par ses événements
        organizer_id = None
        if request.user.role == 'organizer':
            organizer_id = str(request.user.id)
        
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if analysis_type == 'tickets':
            data = RegistrationAnalyticsService.get_ticket_sales_analysis(
                event_id=event_id,
                organizer_id=organizer_id
            )
        elif analysis_type == 'forms':
            data = RegistrationAnalyticsService.analyze_form_submissions(
                event_id=event_id,
                organizer_id=organizer_id
            )
        else:
            # Résumé par défaut
            data = RegistrationAnalyticsService.get_registration_summary(
                start_date=start_date,
                end_date=end_date,
                event_id=event_id,
                organizer_id=organizer_id
            )
        
        return Response(data)

class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """Gestion des widgets de tableau de bord"""
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Filtrer les widgets par propriétaire ou widgets partagés"""
        user = self.request.user
        
        # Administrateurs peuvent voir tous les widgets
        if user.is_staff:
            return DashboardWidget.objects.all()
        
        # Utilisateurs normaux voient leurs widgets et ceux partagés avec eux
        return DashboardWidget.objects.filter(
            Q(user=user) | 
            Q(is_public=True) | 
            Q(shared_with=user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Associer le widget à l'utilisateur actuel"""
        serializer.save(user=self.request.user)

class DashboardViewSet(viewsets.ModelViewSet):
    """Gestion des tableaux de bord"""
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Filtrer les tableaux de bord par propriétaire ou tableaux partagés"""
        user = self.request.user
        
        # Administrateurs peuvent voir tous les tableaux de bord
        if user.is_staff:
            return Dashboard.objects.all()
        
        # Utilisateurs normaux voient leurs tableaux et ceux partagés avec eux
        return Dashboard.objects.filter(
            Q(owner=user) | 
            Q(is_public=True) | 
            Q(shared_with=user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Associer le tableau de bord à l'utilisateur actuel"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def widgets(self, request, pk=None):
        """Obtenir les widgets associés à un tableau de bord"""
        dashboard = self.get_object()
        widgets = DashboardWidget.objects.filter(
            user=dashboard.owner
        ).order_by('position_y', 'position_x')
        
        serializer = DashboardWidgetSerializer(widgets, many=True)
        return Response(serializer.data)

class AnalyticsReportViewSet(viewsets.ModelViewSet):
    """Gestion des rapports d'analyse"""
    queryset = AnalyticsReport.objects.all()
    serializer_class = AnalyticsReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOrganizer]
    
    def get_queryset(self):
        """Filtrer les rapports par générateur ou rapports sur les événements de l'utilisateur"""
        user = self.request.user
        
        # Administrateurs peuvent voir tous les rapports
        if user.is_staff:
            return AnalyticsReport.objects.all()
        
        # Organisateurs voient leurs rapports et ceux liés à leurs événements
        if user.role == 'organizer':
            return AnalyticsReport.objects.filter(
                Q(generated_by=user) | 
                Q(event__organizer=user)
            ).distinct()
        
        # Utilisateurs normaux voient uniquement leurs rapports
        return AnalyticsReport.objects.filter(generated_by=user)
    
    def perform_create(self, serializer):
        """Associer le rapport à l'utilisateur actuel"""
        serializer.save(generated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Générer un nouveau rapport d'analyse"""
        serializer = ReportGenerationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extraire les paramètres validés
        report_type = serializer.validated_data['report_type']
        title = serializer.validated_data['title']
        description = serializer.validated_data.get('description', '')
        filters = serializer.validated_data.get('filters', {})
        event_id = serializer.validated_data.get('event_id')
        is_scheduled = serializer.validated_data.get('is_scheduled', False)
        schedule_frequency = serializer.validated_data.get('schedule_frequency', 'once')
        email_on_generation = serializer.validated_data.get('email_on_generation', False)
        export_format = serializer.validated_data.get('export_format', 'pdf')
        
        # Si le rapport concerne un événement spécifique
        event = None
        if event_id:
            from apps.events.models import Event
            
            try:
                event = Event.objects.get(id=event_id)
                
                # Vérifier les permissions si l'utilisateur est un organisateur
                if request.user.role == 'organizer' and event.organizer != request.user:
                    return Response(
                        {'detail': 'Vous n\'êtes pas autorisé à générer un rapport pour cet événement.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Ajouter l'ID de l'événement aux filtres
                filters['event_id'] = str(event_id)
                
            except Event.DoesNotExist:
                return Response(
                    {'detail': 'Événement non trouvé.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Générer le rapport
        report_data = ReportGenerator.generate_report(
            report_type=report_type,
            filters=filters,
            user=request.user
        )
        
        # Calculer les dates de prochaine exécution si nécessaire
        next_run = None
        if is_scheduled:
            now = timezone.now()
            
            if schedule_frequency == 'daily':
                next_run = now + datetime.timedelta(days=1)
            elif schedule_frequency == 'weekly':
                next_run = now + datetime.timedelta(weeks=1)
            elif schedule_frequency == 'monthly':
                # Approximation du mois prochain
                next_month = now.month + 1
                next_year = now.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                next_run = now.replace(year=next_year, month=next_month, day=1)
        
        # Sauvegarder le rapport
        report = AnalyticsReport.objects.create(
            title=title,
            description=description,
            report_type=report_type,
            data=report_data['data'],
            filters=filters,
            generated_by=request.user,
            event=event,
            is_scheduled=is_scheduled,
            schedule_frequency=schedule_frequency,
            next_run=next_run,
            email_on_generation=email_on_generation,
            export_format=export_format
        )
        
        return Response({
            'id': report.id,
            'title': report.title,
            'report_type': report.report_type,
            'generated_at': report.created_at,
            'is_scheduled': report.is_scheduled,
            'next_run': report.next_run
        })
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Exporter un rapport dans un format spécifique"""
        report = self.get_object()
        export_format = request.query_params.get('format', report.export_format)
        
        # Préparer les données du rapport
        report_data = {
            'metadata': {
                'report_type': report.report_type,
                'generated_at': report.created_at.isoformat(),
                'title': report.title,
                'description': report.description
            },
            'data': report.data
        }
        
        # Exporter selon le format demandé
        if export_format == 'pdf':
            pdf_data = ReportGenerator.export_to_pdf(report_data)
            
            if pdf_data:
                response = HttpResponse(pdf_data, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
                return response
            else:
                return Response(
                    {'detail': 'Erreur lors de la génération du PDF.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        elif export_format == 'csv':
            csv_data = ReportGenerator.export_to_csv(report_data)
            
            if csv_data:
                response = HttpResponse(csv_data, content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{report.title}.csv"'
                return response
            else:
                return Response(
                    {'detail': 'Erreur lors de la génération du CSV.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        elif export_format == 'json':
            # Retourner directement les données JSON
            return Response(report_data)
        
        else:
            return Response(
                {'detail': 'Format d\'export non pris en charge.'},
                status=status.HTTP_400_BAD_REQUEST
            )