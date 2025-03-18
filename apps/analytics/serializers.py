from rest_framework import serializers
from .models import AnalyticsReport, DashboardWidget, Dashboard
from apps.accounts.serializers import UserSerializer

class DashboardWidgetSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = DashboardWidget
        fields = '__all__'
        read_only_fields = ['user']

class DashboardSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source='owner', read_only=True)
    widgets_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Dashboard
        fields = '__all__'
        read_only_fields = ['owner']
    
    def get_widgets_count(self, obj):
        return obj.dashboardwidget_set.count()

class AnalyticsReportSerializer(serializers.ModelSerializer):
    generated_by_details = UserSerializer(source='generated_by', read_only=True)
    
    class Meta:
        model = AnalyticsReport
        fields = '__all__'
        read_only_fields = ['generated_by', 'created_at', 'updated_at', 'last_run']

class ReportGenerationSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=AnalyticsReport.REPORT_TYPE_CHOICES)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    filters = serializers.JSONField(required=False, default=dict)
    event_id = serializers.UUIDField(required=False)
    is_scheduled = serializers.BooleanField(default=False)
    schedule_frequency = serializers.ChoiceField(
        choices=AnalyticsReport.FREQUENCY_CHOICES, 
        default='once'
    )
    email_on_generation = serializers.BooleanField(default=False)
    export_format = serializers.ChoiceField(
        choices=[('pdf', 'PDF'), ('csv', 'CSV'), ('json', 'JSON')], 
        default='pdf'
    )