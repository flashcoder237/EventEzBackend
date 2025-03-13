from django.contrib import admin
from .models import Payment, Refund, Invoice

class InvoiceInline(admin.StackedInline):
    model = Invoice
    extra = 0
    readonly_fields = ('invoice_number', 'generated_at')

class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ('requested_at', 'processed_at', 'processed_by')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'registration', 'user', 'amount', 'currency', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'is_usage_based')
    search_fields = ('id', 'registration__reference_code', 'user__email', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [InvoiceInline, RefundInline]
    fieldsets = (
        ('Informations générales', {'fields': ('registration', 'user', 'amount', 'currency', 'payment_method')}),
        ('Statut', {'fields': ('status', 'transaction_id', 'payment_date')}),
        ('Facturation', {'fields': ('billing_name', 'billing_email', 'billing_phone', 'billing_address')}),
        ('Usage', {'fields': ('is_usage_based', 'storage_amount', 'duration_days')}),
        ('Données de transaction', {'fields': ('payment_gateway_response',)}),
        ('Métadonnées', {'fields': ('created_at', 'updated_at')})
    )

class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'amount', 'status', 'requested_at', 'processed_at')
    list_filter = ('status',)
    search_fields = ('payment__id', 'payment__transaction_id', 'transaction_id')
    readonly_fields = ('requested_at', 'processed_at')

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'payment', 'generated_at', 'due_date')
    search_fields = ('invoice_number', 'payment__id', 'payment__transaction_id')
    readonly_fields = ('invoice_number', 'generated_at')

admin.site.register(Payment, PaymentAdmin)
admin.site.register(Refund, RefundAdmin)
admin.site.register(Invoice, InvoiceAdmin)