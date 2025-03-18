from django.contrib import admin
from .models import AnalyticsReport, DashboardWidget, Dashboard

@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'generated_by', 'created_at', 'is_scheduled', 'next_run')
    list_filter = ('report_type', 'is_scheduled', 'created_at')
    search_fields = ('title', 'description', 'generated_by__email')
    readonly_fields = ('created_at', 'updated_at', 'last_run')
    fieldsets = (
        ('Informations', {
            'fields': ('title', 'description', 'report_type', 'generated_by', 'event')
        }),
        ('Données', {
            'fields': ('data', 'filters')
        }),
        ('Programmation', {
            'fields': ('is_scheduled', 'schedule_frequency', 'last_run', 'next_run', 'email_on_generation')
        }),
        ('Export', {
            'fields': ('export_format',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'widget_type', 'data_source', 'user', 'created_at')
    list_filter = ('widget_type', 'data_source', 'created_at')
    search_fields = ('title', 'description', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations', {
            'fields': ('title', 'description', 'user')
        }),
        ('Type et source', {
            'fields': ('widget_type', 'chart_type', 'data_source')
        }),
        ('Configuration', {
            'fields': ('config',)
        }),
        ('Mise en page', {
            'fields': ('position_x', 'position_y', 'width', 'height')
        }),
        ('Partage', {
            'fields': ('is_public', 'shared_with')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'is_public')
    list_filter = ('is_public', 'created_at')
    search_fields = ('title', 'description', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations', {
            'fields': ('title', 'description', 'owner')
        }),
        ('Configuration', {
            'fields': ('layout', 'theme')
        }),
        ('Partage', {
            'fields': ('is_public', 'shared_with')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )