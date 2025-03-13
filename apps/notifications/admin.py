from django.contrib import admin
from .models import Notification, NotificationTemplate

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'notification_type', 'channel', 'is_read', 'is_sent', 'created_at')
    list_filter = ('notification_type', 'channel', 'is_read', 'is_sent')
    search_fields = ('user__email', 'title', 'message')
    readonly_fields = ('created_at', 'sent_at', 'read_at')
    fieldsets = (
        ('Destinataire', {'fields': ('user',)}),
        ('Contenu', {'fields': ('title', 'message', 'notification_type')}),
        ('Référence', {'fields': ('related_object_id', 'related_object_type')}),
        ('Livraison', {'fields': ('channel', 'is_sent', 'is_read')}),
        ('Métadonnées', {'fields': ('created_at', 'scheduled_for', 'sent_at', 'read_at')}),
        ('Email', {'fields': ('email_subject',)}),
        ('SMS', {'fields': ('phone_number',)}),
        ('Données supplémentaires', {'fields': ('extra_data',)})
    )
    actions = ['mark_as_read', 'mark_as_sent']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_read=True, read_at=timezone.now())
    mark_as_read.short_description = "Marquer comme lues"
    
    def mark_as_sent(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_sent=True, sent_at=timezone.now())
    mark_as_sent.short_description = "Marquer comme envoyées"

class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'notification_type')
    search_fields = ('name', 'notification_type', 'email_subject', 'email_body', 'sms_body')
    fieldsets = (
        ('Général', {'fields': ('name', 'notification_type', 'available_variables')}),
        ('Email', {'fields': ('email_subject', 'email_body')}),
        ('SMS', {'fields': ('sms_body',)}),
        ('Push', {'fields': ('push_title', 'push_body')}),
        ('Application', {'fields': ('in_app_title', 'in_app_body')})
    )

admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)