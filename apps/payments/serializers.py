from rest_framework import serializers
from .models import Payment, Refund, Invoice
from apps.registrations.serializers import RegistrationSerializer

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'generated_at', 'pdf_file']

class PaymentSerializer(serializers.ModelSerializer):
    invoice = InvoiceSerializer(read_only=True)
    registration_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['user', 'transaction_id', 'payment_date', 
                           'created_at', 'updated_at', 'payment_gateway_response']
    
    def get_registration_details(self, obj):
        from apps.registrations.serializers import RegistrationSerializer
        return RegistrationSerializer(obj.registration).data

class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['registration', 'amount', 'currency', 'payment_method', 
                  'billing_name', 'billing_email', 'billing_phone', 'billing_address', 
                  'is_usage_based', 'storage_amount', 'duration_days']
    
    def validate(self, data):
        registration = data.get('registration')
        
        # Vérifier que l'inscription n'est pas déjà payée
        if registration.status == 'confirmed':
            raise serializers.ValidationError("Cette inscription est déjà confirmée.")
        
        # Pour les paiements basés sur l'usage
        if data.get('is_usage_based'):
            if not data.get('storage_amount') or not data.get('duration_days'):
                raise serializers.ValidationError(
                    "Les champs 'storage_amount' et 'duration_days' sont requis pour les paiements basés sur l'usage."
                )
        
        return data

class RefundSerializer(serializers.ModelSerializer):
    payment_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Refund
        fields = ['id', 'payment', 'payment_details', 'amount', 'reason', 
                  'status', 'requested_at', 'processed_at', 'processed_by', 
                  'transaction_id', 'notes']
        read_only_fields = ['requested_at', 'processed_at', 'processed_by', 
                           'transaction_id']
    
    def get_payment_details(self, obj):
        return {
            'id': str(obj.payment.id),
            'amount': obj.payment.amount,
            'status': obj.payment.status,
            'method': obj.payment.payment_method,
            'date': obj.payment.payment_date
        }
    
    def validate(self, data):
        payment = data.get('payment')
        amount = data.get('amount')
        
        # Vérifier que le montant du remboursement ne dépasse pas le montant du paiement
        if amount > payment.amount:
            raise serializers.ValidationError(
                f"Le montant du remboursement ne peut pas dépasser {payment.amount} {payment.currency}."
            )
        
        return data