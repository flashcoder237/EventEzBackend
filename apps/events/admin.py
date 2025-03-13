from django.contrib import admin
from .models import Event, EventCategory, EventTag, EventImage, CustomFormField

class CustomFormFieldInline(admin.TabularInline):
    model = CustomFormField
    extra = 1

class EventImageInline(admin.TabularInline):
    model = Event.gallery_images.through
    extra = 1

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'event_type', 'start_date', 'end_date', 'status', 'registration_count')
    list_filter = ('event_type', 'status', 'category', 'is_featured')
    search_fields = ('title', 'description', 'organizer__email', 'organizer__username')
    date_hierarchy = 'start_date'
    inlines = [CustomFormFieldInline, EventImageInline]
    filter_horizontal = ('tags',)
    readonly_fields = ('slug', 'view_count', 'registration_count', 'form_storage_usage', 'form_active_days')
    fieldsets = (
        ('Informations générales', {'fields': ('title', 'slug', 'description', 'short_description', 'organizer', 'category', 'tags')}),
        ('Type et dates', {'fields': ('event_type', 'start_date', 'end_date', 'registration_deadline')}),
        ('Lieu', {'fields': ('location_name', 'location_address', 'location_city', 'location_country', 'location_latitude', 'location_longitude')}),
        ('Médias', {'fields': ('banner_image',)}),
        ('État', {'fields': ('status', 'is_featured')}),
        ('SEO', {'fields': ('seo_title', 'seo_description')}),
        ('Métriques', {'fields': ('view_count', 'registration_count', 'form_storage_usage', 'form_active_days')})
    )

class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

class EventTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class EventImageAdmin(admin.ModelAdmin):
    list_display = ('caption', 'image')
    search_fields = ('caption',)

class CustomFormFieldAdmin(admin.ModelAdmin):
    list_display = ('label', 'event', 'field_type', 'required', 'order')
    list_filter = ('field_type', 'required')
    search_fields = ('label', 'event__title')

admin.site.register(Event, EventAdmin)
admin.site.register(EventCategory, EventCategoryAdmin)
admin.site.register(EventTag, EventTagAdmin)
admin.site.register(EventImage, EventImageAdmin)
admin.site.register(CustomFormField, CustomFormFieldAdmin)