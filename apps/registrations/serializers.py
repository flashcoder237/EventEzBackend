from rest_framework import serializers
from .models import Registration, TicketType, TicketPurchase, Discount
from apps.events.serializers import EventListSerializer

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = '__all__'
        read_only_fields = ['times_used']

class TicketTypeSerializer(serializers.ModelSerializer):
    available_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketType
        fields = '__all__'
        read_only_fields = ['quantity_sold']
    
    def get_available_quantity(self, obj):
        return obj.quantity_total - obj.quantity_sold

class TicketPurchaseSerializer(serializers.ModelSerializer):
    ticket_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketPurchase
        fields = ['id', 'registration', 'ticket_type', 'ticket_type_name', 'quantity', 
                  'unit_price', 'discount_code', 'discount_amount', 'total_price', 
                  'qr_code', 'is_checked_in', 'checked_in_at']
        read_only_fields = ['qr_code', 'is_checked_in', 'checked_in_at']
    
    def get_ticket_type_name(self, obj):
        return obj.ticket_type.name

class RegistrationSerializer(serializers.ModelSerializer):
    event_detail = EventListSerializer(source='event', read_only=True)
    tickets = TicketPurchaseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Registration
        fields = ['id', 'event', 'event_detail', 'user', 'registration_type', 
                  'status', 'created_at', 'updated_at', 'confirmed_at', 
                  'reference_code', 'form_data', 'form_data_size', 'tickets']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 
                           'confirmed_at', 'reference_code']

class RegistrationCreateSerializer(serializers.ModelSerializer):
    tickets = serializers.ListField(
        child=serializers.DictField(), 
        required=False, 
        write_only=True
    )
    form_data = serializers.JSONField(required=False)
    
    class Meta:
        model = Registration
        fields = ['id', 'event', 'registration_type', 'form_data', 'tickets', 'reference_code', 'user']
        read_only_fields = ['reference_code', 'user']  # Ces champs seront définis dans la méthode create
    
    def validate(self, data):
        event = data.get('event')
        registration_type = data.get('registration_type')
        
        # Vérifier que le type d'inscription correspond au type d'événement
        if event.event_type != registration_type:
            raise serializers.ValidationError(
                f"Le type d'inscription doit être {event.event_type}"
            )
        
        # Valider les billets pour les événements de type billetterie
        if registration_type == 'billetterie':
            tickets = data.get('tickets', [])
            if not tickets:
                raise serializers.ValidationError(
                    "Vous devez sélectionner au moins un billet"
                )
            
            # Vérifier chaque billet
            for ticket_data in tickets:
                ticket_type_id = ticket_data.get('ticket_type')
                quantity = ticket_data.get('quantity', 0)
                
                try:
                    ticket_type = TicketType.objects.get(id=ticket_type_id, event=event)
                except TicketType.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Type de billet {ticket_type_id} non trouvé pour cet événement"
                    )
                
                if quantity < ticket_type.min_per_order or quantity > ticket_type.max_per_order:
                    raise serializers.ValidationError(
                        f"La quantité pour {ticket_type.name} doit être entre "
                        f"{ticket_type.min_per_order} et {ticket_type.max_per_order}"
                    )
                
                if ticket_type.tickets_available() < quantity:
                    raise serializers.ValidationError(
                        f"Il ne reste que {ticket_type.tickets_available()} billets de type {ticket_type.name}"
                    )
        
        # Valider les données de formulaire pour les événements de type inscription
        elif registration_type == 'inscription':
            form_data = data.get('form_data')
            if not form_data:
                raise serializers.ValidationError(
                    "Vous devez remplir le formulaire d'inscription"
                )
            
            # Vérifier que tous les champs requis sont présents
            required_fields = event.form_fields.filter(required=True)
            for field in required_fields:
                if field.label not in form_data:
                    raise serializers.ValidationError(
                        f"Le champ requis '{field.label}' n'est pas renseigné"
                    )
            
            # Calculer la taille des données du formulaire (en MB)
            import json
            data_size = len(json.dumps(form_data)) / (1024 * 1024)  # Taille en MB
            data['form_data_size'] = data_size
        
        return data
    
    def create(self, validated_data):
        tickets_data = validated_data.pop('tickets', [])
        user = self.context['request'].user
        
        # Créer l'inscription
        registration = Registration.objects.create(
            user=user,
            **validated_data
        )
        
        # Ajouter les billets pour les événements de type billetterie
        if registration.registration_type == 'billetterie':
            for ticket_data in tickets_data:
                ticket_type_id = ticket_data.get('ticket_type')
                quantity = ticket_data.get('quantity')
                
                ticket_type = TicketType.objects.get(id=ticket_type_id)
                
                # Vérifier s'il y a un code de réduction
                discount_code = ticket_data.get('discount_code')
                discount_amount = 0
                
                if discount_code:
                    try:
                        discount = Discount.objects.get(code=discount_code, event=registration.event)
                        
                        if discount.is_valid() and (not discount.applicable_ticket_types.exists() or 
                                                  discount.applicable_ticket_types.filter(id=ticket_type.id).exists()):
                            # Calculer la réduction
                            if discount.discount_type == 'percentage':
                                discount_amount = (ticket_type.price * discount.value / 100) * quantity
                            else:  # montant fixe
                                discount_amount = discount.value * quantity
                            
                            # Mettre à jour le compteur d'utilisation
                            discount.times_used += 1
                            discount.save()
                    except Discount.DoesNotExist:
                        pass
                
                # Calculer le prix total
                total_price = (ticket_type.price * quantity) - discount_amount
                
                # Créer l'achat de billet
                TicketPurchase.objects.create(
                    registration=registration,
                    ticket_type=ticket_type,
                    quantity=quantity,
                    unit_price=ticket_type.price,
                    discount_code=discount if discount_code and 'discount' in locals() else None,
                    discount_amount=discount_amount,
                    total_price=total_price
                )
                
                # Ne pas mettre à jour le nombre de billets vendus ici
                # Cette mise à jour sera faite lors de la validation du paiement
        
        # Mettre à jour le compteur d'inscriptions de l'événement
        event = registration.event
        event.registration_count += 1
        event.save()
        
        return registration