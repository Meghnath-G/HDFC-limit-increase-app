"""
Django REST Framework serializers for Analytics models.

Provides comprehensive analytics and reporting functionality
with proper aggregation, time-series data, and performance metrics.
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from .models import AnalyticsEvent, DashboardMetrics, PerformanceLog
from core.utils import validate_date_range


class AnalyticsEventSerializer(serializers.ModelSerializer):
    """
    Serializer for analytics events tracking.
    
    Handles event logging for user interactions, system events,
    and business process tracking with proper metadata management.
    """
    
    event_category_display = serializers.CharField(source='get_event_category_display', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    # Calculated fields
    duration_seconds = serializers.SerializerMethodField()
    is_success = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalyticsEvent
        fields = [
            'id', 'event_category', 'event_category_display',
            'event_type', 'event_type_display', 'event_name',
            'session_id', 'page_path', 'referrer', 'user_agent',
            'ip_address', 'custom_properties', 'value',
            'currency', 'duration_seconds', 'is_success',
            'error_code', 'error_message', 'created_at'
        ]
        read_only_fields = [
            'id', 'duration_seconds', 'is_success', 'created_at'
        ]
    
    def get_duration_seconds(self, obj):
        """Get duration in seconds if available."""
        duration = obj.custom_properties.get('duration_ms')
        return duration / 1000 if duration else None
    
    def get_is_success(self, obj):
        """Check if event indicates success."""
        return not bool(obj.error_code)
    
    def validate_event_name(self, value):
        """Validate event name format."""
        # Event names should be descriptive and follow naming convention
        if len(value) < 3:
            raise serializers.ValidationError("Event name must be at least 3 characters")
        
        # Check for valid characters (alphanumeric, underscore, dash)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Event name can only contain letters, numbers, underscores, and dashes"
            )
        
        return value
    
    def validate_custom_properties(self, value):
        """Validate custom properties JSON."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Custom properties must be a valid JSON object")
        
        # Validate property names and values
        for key, val in value.items():
            if not isinstance(key, str):
                raise serializers.ValidationError("Property keys must be strings")
            
            # Limit property value size
            if isinstance(val, str) and len(val) > 1000:
                raise serializers.ValidationError(
                    f"Property '{key}' value too long (max 1000 characters)"
                )
        
        return value
    
    def validate_value(self, value):
        """Validate event value."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Event value cannot be negative")
        return value


class AnalyticsQuerySerializer(serializers.Serializer):
    """
    Serializer for analytics query parameters.
    
    Handles complex analytics queries with filtering,
    grouping, and aggregation options.
    """
    
    # Time range
    start_date = serializers.DateTimeField(required=True)
    end_date = serializers.DateTimeField(required=True)
    
    # Filtering
    event_category = serializers.ChoiceField(
        choices=AnalyticsEvent.EVENT_CATEGORY_CHOICES,
        required=False
    )
    event_type = serializers.ChoiceField(
        choices=AnalyticsEvent.EVENT_TYPE_CHOICES,
        required=False
    )
    event_name = serializers.CharField(max_length=100, required=False)
    
    # Grouping
    group_by = serializers.MultipleChoiceField(
        choices=[
            ('hour', 'Hour'),
            ('day', 'Day'),
            ('week', 'Week'),
            ('month', 'Month'),
            ('event_category', 'Event Category'),
            ('event_type', 'Event Type'),
            ('event_name', 'Event Name'),
        ],
        required=False,
        default=['day']
    )
    
    # Metrics
    metrics = serializers.MultipleChoiceField(
        choices=[
            ('count', 'Event Count'),
            ('unique_users', 'Unique Users'),
            ('total_value', 'Total Value'),
            ('avg_value', 'Average Value'),
            ('success_rate', 'Success Rate'),
            ('avg_duration', 'Average Duration'),
        ],
        required=False,
        default=['count']
    )
    
    # Aggregation options
    include_comparison = serializers.BooleanField(default=False)
    comparison_period_days = serializers.IntegerField(min_value=1, max_value=365, default=7)
    
    def validate(self, attrs):
        """Cross-field validation for analytics queries."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        # Validate date range
        if end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        # Limit query range (max 1 year)
        max_range = timedelta(days=365)
        if end_date - start_date > max_range:
            raise serializers.ValidationError({
                'end_date': 'Date range cannot exceed 1 year'
            })
        
        # Future date validation
        if start_date > timezone.now():
            raise serializers.ValidationError({
                'start_date': 'Start date cannot be in the future'
            })
        
        return attrs


class DashboardMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for dashboard metrics.
    
    Provides essential business metrics for executive
    dashboards with trend analysis and KPI tracking.
    """
    
    # Calculated fields
    success_rate = serializers.SerializerMethodField()
    growth_rate = serializers.SerializerMethodField()
    performance_status = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardMetrics
        fields = [
            'id', 'metric_date', 'total_customers', 'active_customers',
            'new_registrations', 'kyc_completions', 'total_limit_requests',
            'approved_requests', 'rejected_requests', 'pending_requests',
            'avg_processing_time_hours', 'total_notifications_sent',
            'notification_delivery_rate', 'customer_satisfaction_score',
            'system_uptime_percentage', 'peak_concurrent_users',
            'api_response_time_ms', 'error_rate_percentage',
            'success_rate', 'growth_rate', 'performance_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'success_rate', 'growth_rate', 'performance_status',
            'created_at', 'updated_at'
        ]
    
    def get_success_rate(self, obj):
        """Calculate overall success rate."""
        total_requests = obj.total_limit_requests
        if total_requests > 0:
            return round((obj.approved_requests / total_requests) * 100, 2)
        return 0.0
    
    def get_growth_rate(self, obj):
        """Calculate growth rate compared to previous period."""
        # Get previous day's metrics
        previous_date = obj.metric_date - timedelta(days=1)
        try:
            previous_metrics = DashboardMetrics.objects.get(metric_date=previous_date)
            if previous_metrics.total_customers > 0:
                growth = ((obj.total_customers - previous_metrics.total_customers) / 
                         previous_metrics.total_customers) * 100
                return round(growth, 2)
        except DashboardMetrics.DoesNotExist:
            pass
        return 0.0
    
    def get_performance_status(self, obj):
        """Determine overall performance status."""
        # Define thresholds for good performance
        uptime_threshold = 99.5
        response_time_threshold = 200
        error_rate_threshold = 1.0
        
        if (obj.system_uptime_percentage >= uptime_threshold and 
            obj.api_response_time_ms <= response_time_threshold and
            obj.error_rate_percentage <= error_rate_threshold):
            return 'EXCELLENT'
        elif (obj.system_uptime_percentage >= 99.0 and 
              obj.api_response_time_ms <= 500 and
              obj.error_rate_percentage <= 2.0):
            return 'GOOD'
        elif (obj.system_uptime_percentage >= 98.0 and 
              obj.error_rate_percentage <= 5.0):
            return 'FAIR'
        else:
            return 'POOR'


class PerformanceLogSerializer(serializers.ModelSerializer):
    """
    Serializer for performance logging.
    
    Handles system performance tracking with detailed
    metrics for monitoring and optimization.
    """
    
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    
    # Calculated fields
    execution_time_ms = serializers.SerializerMethodField()
    performance_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceLog
        fields = [
            'id', 'operation_type', 'operation_type_display',
            'operation_name', 'execution_time_seconds',
            'execution_time_ms', 'memory_usage_mb',
            'cpu_usage_percentage', 'database_queries',
            'cache_hits', 'cache_misses', 'external_api_calls',
            'error_occurred', 'error_details', 'performance_rating',
            'metadata', 'created_at'
        ]
        read_only_fields = [
            'id', 'execution_time_ms', 'performance_rating', 'created_at'
        ]
    
    def get_execution_time_ms(self, obj):
        """Convert execution time to milliseconds."""
        return round(obj.execution_time_seconds * 1000, 2)
    
    def get_performance_rating(self, obj):
        """Rate performance based on execution time and resource usage."""
        exec_time = obj.execution_time_seconds
        memory_usage = obj.memory_usage_mb
        
        # Define performance thresholds
        if exec_time <= 0.1 and memory_usage <= 50:
            return 'EXCELLENT'
        elif exec_time <= 0.5 and memory_usage <= 100:
            return 'GOOD'
        elif exec_time <= 2.0 and memory_usage <= 200:
            return 'FAIR'
        else:
            return 'POOR'
    
    def validate_execution_time_seconds(self, value):
        """Validate execution time."""
        if value < 0:
            raise serializers.ValidationError("Execution time cannot be negative")
        if value > 300:  # 5 minutes max
            raise serializers.ValidationError("Execution time seems too long (max 300 seconds)")
        return value
    
    def validate_memory_usage_mb(self, value):
        """Validate memory usage."""
        if value < 0:
            raise serializers.ValidationError("Memory usage cannot be negative")
        if value > 10240:  # 10GB max
            raise serializers.ValidationError("Memory usage seems too high (max 10GB)")
        return value
    
    def validate_cpu_usage_percentage(self, value):
        """Validate CPU usage percentage."""
        if not (0 <= value <= 100):
            raise serializers.ValidationError("CPU usage must be between 0 and 100 percent")
        return value


class AnalyticsReportSerializer(serializers.Serializer):
    """
    Serializer for analytics reports.
    
    Provides comprehensive reporting functionality with
    multiple visualization formats and export options.
    """
    
    report_type = serializers.ChoiceField(choices=[
        ('customer_acquisition', 'Customer Acquisition'),
        ('limit_requests', 'Limit Requests'),
        ('notification_performance', 'Notification Performance'),
        ('system_performance', 'System Performance'),
        ('user_engagement', 'User Engagement'),
        ('revenue_impact', 'Revenue Impact'),
    ])
    
    # Time range
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    
    # Filtering options
    customer_segment = serializers.CharField(max_length=50, required=False)
    card_type = serializers.CharField(max_length=20, required=False)
    
    # Grouping and aggregation
    group_by_period = serializers.ChoiceField(
        choices=[('day', 'Daily'), ('week', 'Weekly'), ('month', 'Monthly')],
        default='day'
    )
    
    include_comparison = serializers.BooleanField(default=False)
    
    # Output format
    format_type = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('pdf', 'PDF')],
        default='json'
    )
    
    # Response fields
    report_data = serializers.JSONField(read_only=True)
    summary_stats = serializers.JSONField(read_only=True)
    chart_data = serializers.JSONField(read_only=True)
    export_url = serializers.URLField(read_only=True)
    
    def validate(self, attrs):
        """Cross-field validation for report generation."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        # Validate date range
        if end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        # Limit report range based on period
        group_by_period = attrs.get('group_by_period', 'day')
        max_days = {
            'day': 90,    # 3 months for daily reports
            'week': 365,  # 1 year for weekly reports
            'month': 1095 # 3 years for monthly reports
        }
        
        range_days = (end_date - start_date).days
        if range_days > max_days[group_by_period]:
            raise serializers.ValidationError({
                'end_date': f'Date range too large for {group_by_period} grouping '
                           f'(max {max_days[group_by_period]} days)'
            })
        
        return attrs


class MetricsTrendSerializer(serializers.Serializer):
    """
    Serializer for metrics trend analysis.
    
    Provides trend analysis with statistical calculations,
    forecasting, and anomaly detection.
    """
    
    metric_name = serializers.CharField(max_length=100)
    time_period = serializers.ChoiceField(choices=[
        ('7d', 'Last 7 days'),
        ('30d', 'Last 30 days'),
        ('90d', 'Last 90 days'),
        ('1y', 'Last year'),
    ])
    
    # Analysis options
    include_forecast = serializers.BooleanField(default=False)
    detect_anomalies = serializers.BooleanField(default=False)
    include_seasonality = serializers.BooleanField(default=False)
    
    # Response data
    trend_data = serializers.JSONField(read_only=True)
    statistical_summary = serializers.JSONField(read_only=True)
    trend_direction = serializers.CharField(read_only=True)
    confidence_score = serializers.FloatField(read_only=True)
    forecast_data = serializers.JSONField(read_only=True)
    anomalies = serializers.JSONField(read_only=True)
    
    def validate_metric_name(self, value):
        """Validate metric name."""
        allowed_metrics = [
            'total_customers', 'active_customers', 'new_registrations',
            'limit_requests', 'approval_rate', 'processing_time',
            'notification_delivery_rate', 'api_response_time',
            'error_rate', 'customer_satisfaction'
        ]
        
        if value not in allowed_metrics:
            raise serializers.ValidationError(
                f"Invalid metric. Allowed metrics: {', '.join(allowed_metrics)}"
            )
        
        return value


class UserBehaviorAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for user behavior analytics.
    
    Provides user journey analysis, conversion funnels,
    and behavioral pattern identification.
    """
    
    analysis_type = serializers.ChoiceField(choices=[
        ('user_journey', 'User Journey Analysis'),
        ('conversion_funnel', 'Conversion Funnel'),
        ('feature_usage', 'Feature Usage Analysis'),
        ('session_analysis', 'Session Analysis'),
        ('retention_cohort', 'Retention Cohort Analysis'),
    ])
    
    # Time range
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    
    # Filtering
    customer_segment = serializers.CharField(max_length=50, required=False)
    app_version = serializers.CharField(max_length=20, required=False)
    device_type = serializers.CharField(max_length=20, required=False)
    
    # Analysis parameters
    funnel_steps = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text="List of events for funnel analysis"
    )
    
    cohort_period = serializers.ChoiceField(
        choices=[('day', 'Daily'), ('week', 'Weekly'), ('month', 'Monthly')],
        required=False,
        default='week'
    )
    
    # Response data
    analysis_results = serializers.JSONField(read_only=True)
    insights = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    
    def validate_funnel_steps(self, value):
        """Validate funnel steps."""
        if len(value) < 2:
            raise serializers.ValidationError("Funnel analysis requires at least 2 steps")
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 funnel steps allowed")
        return value