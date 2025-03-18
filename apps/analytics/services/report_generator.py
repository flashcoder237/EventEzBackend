from django.utils import timezone
import datetime
import json
from .event_analytics import EventAnalyticsService
from .payment_analytics import PaymentAnalyticsService
from .user_analytics import UserAnalyticsService
from .registration_analytics import RegistrationAnalyticsService

class ReportGenerator:
    """Service de génération de rapports analytiques"""
    
    @staticmethod
    def generate_report(report_type, filters=None, user=None):
        """Génère un rapport analytique basé sur le type et les filtres spécifiés"""
        if filters is None:
            filters = {}
        
        # Extraction des filtres communs
        event_id = filters.get('event_id')
        organizer_id = filters.get('organizer_id')
        
        # Si l'utilisateur est un organisateur et qu'aucun organizer_id n'est spécifié,
        # utiliser l'ID de l'utilisateur comme organizer_id
        if user and user.role == 'organizer' and not organizer_id:
            organizer_id = str(user.id)
        
        # Dates de début et fin
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        
        if start_date and isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date and isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Génération du rapport selon le type
        if report_type == 'event_performance':
            if event_id:
                # Analyse détaillée d'un événement spécifique
                data = EventAnalyticsService.get_event_performance(event_id)
            else:
                # Résumé de tous les événements
                data = EventAnalyticsService.get_event_summary(
                    organizer_id=organizer_id,
                    start_date=start_date,
                    end_date=end_date
                )
        
        elif report_type == 'revenue_summary':
            data = PaymentAnalyticsService.get_revenue_summary(
                start_date=start_date,
                end_date=end_date,
                event_id=event_id,
                organizer_id=organizer_id
            )
        
        elif report_type == 'user_activity':
            if filters.get('analysis_type') == 'growth':
                interval = filters.get('interval', 'month')
                periods = int(filters.get('periods', 12))
                data = UserAnalyticsService.get_user_growth(interval, periods)
            elif filters.get('analysis_type') == 'segmentation':
                data = UserAnalyticsService.get_user_segmentation()
            elif filters.get('analysis_type') == 'retention':
                cohort_month = filters.get('cohort_month')
                max_months = int(filters.get('max_months', 12))
                data = UserAnalyticsService.get_user_retention(cohort_month, max_months)
            else:
                # Par défaut, retourner les informations de croissance
                data = UserAnalyticsService.get_user_growth()
        
        elif report_type == 'registration_trends':
            if filters.get('analysis_type') == 'tickets':
                data = RegistrationAnalyticsService.get_ticket_sales_analysis(
                    event_id=event_id,
                    organizer_id=organizer_id
                )
            elif filters.get('analysis_type') == 'forms':
                data = RegistrationAnalyticsService.analyze_form_submissions(
                    event_id=event_id,
                    organizer_id=organizer_id
                )
            else:
                # Par défaut, retourner le résumé des inscriptions
                data = RegistrationAnalyticsService.get_registration_summary(
                    start_date=start_date,
                    end_date=end_date,
                    event_id=event_id,
                    organizer_id=organizer_id
                )
        
        elif report_type == 'payment_analysis':
            if filters.get('analysis_type') == 'trends':
                interval = filters.get('interval', 'day')
                periods = int(filters.get('periods', 30))
                data = PaymentAnalyticsService.get_revenue_trends(
                    interval=interval,
                    periods=periods,
                    organizer_id=organizer_id
                )
            elif filters.get('analysis_type') == 'methods':
                data = PaymentAnalyticsService.get_payment_methods_analysis(
                    start_date=start_date,
                    end_date=end_date,
                    organizer_id=organizer_id
                )
            else:
                # Par défaut, retourner le résumé des revenus
                data = PaymentAnalyticsService.get_revenue_summary(
                    start_date=start_date,
                    end_date=end_date,
                    event_id=event_id,
                    organizer_id=organizer_id
                )
        
        elif report_type == 'custom':
            # Rapport personnalisé combinant plusieurs analyses
            data = {
                'event_summary': EventAnalyticsService.get_event_summary(
                    organizer_id=organizer_id,
                    start_date=start_date,
                    end_date=end_date
                ),
                'revenue_summary': PaymentAnalyticsService.get_revenue_summary(
                    start_date=start_date,
                    end_date=end_date,
                    event_id=event_id,
                    organizer_id=organizer_id
                ),
                'registration_summary': RegistrationAnalyticsService.get_registration_summary(
                    start_date=start_date,
                    end_date=end_date,
                    event_id=event_id,
                    organizer_id=organizer_id
                )
            }
        
        else:
            # Type de rapport non reconnu
            data = {'error': 'Type de rapport non valide'}
        
        # Ajouter des métadonnées au rapport
        metadata = {
            'generated_at': timezone.now().isoformat(),
            'report_type': report_type,
            'filters': filters,
            'generated_by': str(user.id) if user else None
        }
        
        # Combiner les données et les métadonnées dans un seul objet
        result = {
            'metadata': metadata,
            'data': data
        }
        
        return result

    @staticmethod
    def export_to_pdf(report_data):
        """Exporte un rapport au format PDF"""
        # Cette fonction nécessiterait une bibliothèque comme ReportLab, WeasyPrint ou xhtml2pdf
        # Exemple d'implémentation avec ReportLab (à adapter selon vos besoins)
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            import io
            
            # Créer un buffer pour stocker le PDF
            buffer = io.BytesIO()
            
            # Créer le document PDF
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Titre du rapport
            metadata = report_data.get('metadata', {})
            report_title = f"Rapport : {metadata.get('report_type', 'Analyse')}"
            elements.append(Paragraph(report_title, title_style))
            elements.append(Spacer(1, 12))
            
            # Métadonnées
            elements.append(Paragraph("Métadonnées", heading_style))
            generated_at = metadata.get('generated_at', '')
            if generated_at:
                try:
                    # Formater la date (ISO 8601 vers format lisible)
                    dt = datetime.datetime.fromisoformat(generated_at)
                    generated_at = dt.strftime("%d/%m/%Y %H:%M:%S")
                except Exception:
                    pass
            
            metadata_text = f"Généré le : {generated_at}"
            elements.append(Paragraph(metadata_text, normal_style))
            elements.append(Spacer(1, 12))
            
            # Contenu du rapport (à adapter selon le type de rapport)
            elements.append(Paragraph("Données du rapport", heading_style))
            
            # Exemple simple : conversion des données en texte
            data = report_data.get('data', {})
            
            # Cette partie devrait être adaptée selon la structure des données
            # Exemple : création d'un tableau pour afficher les données
            for key, value in data.items():
                if isinstance(value, dict):
                    elements.append(Paragraph(f"{key}:", heading_style))
                    for sub_key, sub_value in value.items():
                        elements.append(Paragraph(f"{sub_key}: {sub_value}", normal_style))
                elif isinstance(value, list):
                    elements.append(Paragraph(f"{key}:", heading_style))
                    for item in value:
                        if isinstance(item, dict):
                            for item_key, item_value in item.items():
                                elements.append(Paragraph(f"{item_key}: {item_value}", normal_style))
                            elements.append(Spacer(1, 6))
                else:
                    elements.append(Paragraph(f"{key}: {value}", normal_style))
                
                elements.append(Spacer(1, 12))
            
            # Construire le PDF
            doc.build(elements)
            
            # Récupérer le contenu du buffer
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            # Si ReportLab n'est pas installé
            return None
        except Exception as e:
            print(f"Erreur lors de la génération du PDF: {str(e)}")
            return None
    
    @staticmethod
    def export_to_csv(report_data):
        """Exporte un rapport au format CSV"""
        try:
            import csv
            import io
            
            # Créer un buffer pour stocker le CSV
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            
            # Écrire les en-têtes
            metadata = report_data.get('metadata', {})
            writer.writerow(['Rapport généré le', metadata.get('generated_at', '')])
            writer.writerow(['Type de rapport', metadata.get('report_type', '')])
            writer.writerow([])  # Ligne vide
            
            # Écrire les données
            data = report_data.get('data', {})
            
            # Cette partie devrait être adaptée selon la structure des données
            for key, value in data.items():
                if isinstance(value, dict):
                    writer.writerow([key])
                    for sub_key, sub_value in value.items():
                        writer.writerow([sub_key, sub_value])
                    writer.writerow([])  # Ligne vide
                elif isinstance(value, list):
                    writer.writerow([key])
                    
                    # Si la liste contient des dictionnaires, extraire les clés pour les en-têtes
                    if value and isinstance(value[0], dict):
                        headers = list(value[0].keys())
                        writer.writerow(headers)
                        
                        for item in value:
                            writer.writerow([item.get(header, '') for header in headers])
                    else:
                        # Sinon, écrire chaque élément sur une ligne
                        for item in value:
                            writer.writerow([item])
                    
                    writer.writerow([])  # Ligne vide
                else:
                    writer.writerow([key, value])
            
            # Récupérer le contenu du buffer
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Erreur lors de la génération du CSV: {str(e)}")
            return None