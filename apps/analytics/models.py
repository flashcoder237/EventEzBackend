from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.events.models import Event

class AnalyticsReport(models.Model):
    """Rapport d'analyse qui stocke les résultats d'analyse pour référence future"""
    
    REPORT_TYPE_CHOICES = (
        ('event_performance', 'Performance d\'événement'),
        ('revenue_summary', 'Résumé des revenus'),
        ('user_activity', 'Activité utilisateur'),
        ('registration_trends', 'Tendances d\'inscription'),
        ('payment_analysis', 'Analyse des paiements'),
        ('custom', 'Rapport personnalisé'),
    )
    
    FREQUENCY_CHOICES = (
        ('once', 'Une seule fois'),
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    data = models.JSONField(default=dict)
    
    # Filtres utilisés pour la génération
    filters = models.JSONField(default=dict)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='analytics_reports')
    
    # Pour les rapports liés à des événements spécifiques
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='analytics_reports')
    
    # Planning des rapports
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='once')
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Distribution
    recipients = models.ManyToManyField(User, blank=True, related_name='subscribed_reports')
    email_on_generation = models.BooleanField(default=False)
    
    # Export options
    export_format = models.CharField(max_length=20, choices=[('pdf', 'PDF'), ('csv', 'CSV'), ('json', 'JSON')], default='pdf')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Rapport analytique'
        verbose_name_plural = 'Rapports analytiques'
    
    def __str__(self):
        return self.title

class DashboardWidget(models.Model):
    """Widget configurable pour les tableaux de bord"""
    
    WIDGET_TYPE_CHOICES = (
        ('number', 'Indicateur chiffré'),
        ('chart', 'Graphique'),
        ('table', 'Tableau'),
        ('map', 'Carte'),
        ('list', 'Liste'),
    )
    
    CHART_TYPE_CHOICES = (
        ('line', 'Ligne'),
        ('bar', 'Barre'),
        ('pie', 'Camembert'),
        ('doughnut', 'Anneau'),
        ('area', 'Surface'),
        ('radar', 'Radar'),
        ('scatter', 'Nuage de points'),
    )
    
    DATA_SOURCE_CHOICES = (
        ('event_count', 'Nombre d\'événements'),
        ('registration_count', 'Nombre d\'inscriptions'),
        ('revenue', 'Revenus'),
        ('user_count', 'Nombre d\'utilisateurs'),
        ('event_types', 'Types d\'événements'),
        ('payment_methods', 'Méthodes de paiement'),
        ('revenue_trends', 'Tendances des revenus'),
        ('registration_trends', 'Tendances des inscriptions'),
        ('geographical', 'Répartition géographique'),
        ('custom_query', 'Requête personnalisée'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPE_CHOICES, null=True, blank=True)
    data_source = models.CharField(max_length=50, choices=DATA_SOURCE_CHOICES)
    
    # Configuration du widget (filtres, options d'affichage, etc.)
    config = models.JSONField(default=dict)
    
    # Mise en page et positionnement
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=1)  # En unités de grille
    height = models.IntegerField(default=1)  # En unités de grille
    
    # Propriétaire du widget
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_widgets')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Permissions
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_widgets')
    
    class Meta:
        ordering = ['position_y', 'position_x']
        verbose_name = 'Widget de tableau de bord'
        verbose_name_plural = 'Widgets de tableau de bord'
    
    def __str__(self):
        return self.title

class Dashboard(models.Model):
    """Tableau de bord personnalisé regroupant plusieurs widgets"""
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Propriétaire du tableau de bord
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_dashboards')
    
    # Configuration globale
    layout = models.JSONField(default=dict)
    theme = models.CharField(max_length=50, default='default')
    
    # Permissions
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_dashboards')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Tableau de bord'
        verbose_name_plural = 'Tableaux de bord'
    
    def __str__(self):
        return self.title