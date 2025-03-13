from django.contrib import admin
from .models import Registration, TicketType, TicketPurchase, Discount

class TicketPurchaseInline(admin.TabularInline):
    model = TicketPurchase
    extra = 0
    readonly_fields = ('qr_code', 'is_checked_in', 'checked_in_at')

class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('reference_code', 'event', 'user', 'registration_type', 'status', 'created_at')
    list_filter = ('registration_type', 'status')
    search_fields = ('reference_code', 'event__title', 'user__email', 'user__username')
    readonly_fields = ('reference_code', 'created_at', 'updated_at', 'confirmed_at')
    inlines = [TicketPurchaseInline]
    fieldsets = (
        ('Informations générales', {'fields': ('reference_code', 'event', 'user', 'registration_type', 'status')}),
        ('Dates', {'fields': ('created_at', 'updated_at', 'confirmed_at')}),
        ('Données formulaire', {'fields': ('form_data', 'form_data_size')})
    )

class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'quantity_total', 'quantity_sold', 'sales_start', 'sales_end')
    list_filter = ('is_visible',)
    search_fields = ('name', 'event__title')
    readonly_fields = ('quantity_sold',)

class TicketPurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'registration', 'ticket_type', 'quantity', 'total_price', 'is_checked_in')
    list_filter = ('is_checked_in',)
    search_fields = ('registration__reference_code', 'ticket_type__name')
    readonly_fields = ('qr_code', 'is_checked_in', 'checked_in_at')

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'event', 'discount_type', 'value', 'valid_from', 'valid_until', 'max_uses', 'times_used')
    list_filter = ('discount_type',)
    search_fields = ('code', 'event__title')
    readonly_fields = ('times_used',)
    filter_horizontal = ('applicable_ticket_types',)

admin.site.register(Registration, RegistrationAdmin)
admin.site.register(TicketType, TicketTypeAdmin)
admin.site.register(TicketPurchase, TicketPurchaseAdmin)
admin.site.register(Discount, DiscountAdmin)