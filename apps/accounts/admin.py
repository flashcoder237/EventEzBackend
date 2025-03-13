from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OrganizerProfile

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Rôle', {'fields': ('role', 'organizer_type')}),
        ('Organisation', {'fields': ('company_name', 'registration_number')}),
        ('Vérification', {'fields': ('is_verified', 'verification_documents')}),
        ('Facturation', {'fields': ('billing_address',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'is_staff', 'is_active'),
        }),
    )
    ordering = ('email',)

class OrganizerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'verified_status', 'rating', 'event_count')
    list_filter = ('verified_status',)
    search_fields = ('user__email', 'user__username')

admin.site.register(User, CustomUserAdmin)
admin.site.register(OrganizerProfile, OrganizerProfileAdmin)