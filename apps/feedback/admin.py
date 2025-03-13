from django.contrib import admin
from .models import EventFeedback, EventFlag, EventValidation

class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'user', 'rating', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('rating', 'is_approved', 'is_featured')
    search_fields = ('event__title', 'user__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_feedbacks', 'feature_feedbacks']
    
    def approve_feedbacks(self, request, queryset):
        queryset.update(is_approved=True)
    approve_feedbacks.short_description = "Approuver les commentaires sélectionnés"
    
    def feature_feedbacks(self, request, queryset):
        queryset.update(is_featured=True)
    feature_feedbacks.short_description = "Mettre en avant les commentaires sélectionnés"

class EventFlagAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'user', 'reason', 'is_resolved', 'created_at')
    list_filter = ('reason', 'is_resolved')
    search_fields = ('event__title', 'user__email', 'description')
    readonly_fields = ('created_at',)
    actions = ['resolve_flags']
    
    def resolve_flags(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_at=timezone.now(), resolved_by=request.user)
    resolve_flags.short_description = "Marquer les signalements comme résolus"

class EventValidationAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'user', 'created_at')
    search_fields = ('event__title', 'user__email', 'notes')
    readonly_fields = ('created_at',)

admin.site.register(EventFeedback, EventFeedbackAdmin)
admin.site.register(EventFlag, EventFlagAdmin)
admin.site.register(EventValidation, EventValidationAdmin)