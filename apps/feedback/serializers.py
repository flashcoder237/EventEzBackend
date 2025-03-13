from rest_framework import serializers
from .models import EventFeedback, EventFlag, EventValidation
from apps.events.serializers import EventListSerializer

class EventFeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    event_details = serializers.SerializerMethodField()
    
    class Meta:
        model = EventFeedback
        fields = ['id', 'event', 'user', 'user_name', 'rating', 'comment', 
                  'created_at', 'updated_at', 'is_approved', 'is_featured', 
                  'event_details']
        read_only_fields = ['user', 'created_at', 'updated_at', 'is_approved', 
                           'is_featured']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    
    def get_event_details(self, obj):
        return {
            'title': obj.event.title,
            'slug': obj.event.slug,
            'start_date': obj.event.start_date
        }

class EventFlagSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    event_details = serializers.SerializerMethodField()
    
    class Meta:
        model = EventFlag
        fields = ['id', 'event', 'user', 'user_name', 'reason', 'description', 
                  'created_at', 'is_resolved', 'resolved_at', 'resolved_by', 
                  'resolution_notes', 'event_details']
        read_only_fields = ['user', 'created_at', 'is_resolved', 'resolved_at', 
                           'resolved_by', 'resolution_notes']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    
    def get_event_details(self, obj):
        return {
            'title': obj.event.title,
            'slug': obj.event.slug,
            'organizer': obj.event.organizer.username
        }

class EventValidationSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    event_details = serializers.SerializerMethodField()
    
    class Meta:
        model = EventValidation
        fields = ['id', 'event', 'user', 'user_name', 'created_at', 'notes', 
                  'event_details']
        read_only_fields = ['user', 'created_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    
    def get_event_details(self, obj):
        return {
            'title': obj.event.title,
            'slug': obj.event.slug
        }