from rest_framework import serializers
from .models import Event, EventCategory, EventTag, EventImage, CustomFormField
from apps.accounts.serializers import UserSerializer

class EventTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTag
        fields = ['id', 'name']

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id', 'image', 'caption']

class EventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'description', 'image']

class CustomFormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFormField
        fields = ['id', 'label', 'field_type', 'required', 'placeholder', 
                  'help_text', 'options', 'order']

class EventListSerializer(serializers.ModelSerializer):
    category = EventCategorySerializer(read_only=True)
    organizer_name = serializers.SerializerMethodField()
    tags = EventTagSerializer(many=True, read_only=True)
    ticket_price_range = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'slug', 'short_description', 'event_type', 
                  'start_date', 'end_date', 'location_city', 'banner_image', 
                  'category', 'organizer_name', 'tags', 'ticket_price_range', 
                  'status', 'is_featured', 'registration_count']
    
    def get_organizer_name(self, obj):
        if obj.organizer.organizer_type == 'organization' and obj.organizer.company_name:
            return obj.organizer.company_name
        return f"{obj.organizer.first_name} {obj.organizer.last_name}".strip() or obj.organizer.username
    
    def get_ticket_price_range(self, obj):
        if obj.event_type != 'billetterie' or not hasattr(obj, 'ticket_types'):
            return None
        
        ticket_types = obj.ticket_types.all()
        if not ticket_types:
            return None
        
        min_price = min(ticket.price for ticket in ticket_types)
        max_price = max(ticket.price for ticket in ticket_types)
        
        if min_price == max_price:
            return f"{min_price} XAF"
        return f"{min_price} - {max_price} XAF"

class EventDetailSerializer(serializers.ModelSerializer):
    category = EventCategorySerializer(read_only=True)
    organizer = UserSerializer(read_only=True)
    tags = EventTagSerializer(many=True, read_only=True)
    gallery_images = EventImageSerializer(many=True, read_only=True)
    form_fields = CustomFormFieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = Event
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['slug', 'view_count', 'registration_count', 
                           'form_storage_usage', 'form_active_days', 
                           'organizer', 'created_at', 'updated_at']