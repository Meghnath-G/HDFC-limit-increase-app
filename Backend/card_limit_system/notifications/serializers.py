"""
Django REST Framework serializers for Notification models.

Provides comprehensive notification management with multi-channel
delivery, template support, and customer preference handling.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import NotificationLog, NotificationTemplate, NotificationPreference
from core.utils import validate_phone_format, validate_email_format


class NotificationSendSerializer(serializers.Serializer):
    """
    Serializer for sending notifications.
    
    Handles notification creation and delivery with proper
    validation, template support, and preference checking.
    """
    
    notification_type = serializers.ChoiceField(
        choices=NotificationLog.NOTIFICATION_TYPE_CHOICES,
        help_text="Type of notification to send"
    )
    
    category = serializers.ChoiceField(
        choices=NotificationLog.CATEGORY_CHOICES,
        help_text="Category of notification"
    )
    
    priority = serializers.ChoiceField(
        choices=NotificationLog.PRIORITY_CHOICES,
        default='NORMAL',
        help_text="Priority level of notification"
    )
    
    # Content (either direct or template-based)
    title = serializers.CharField(max_length=200, required=False)
    message = serializers.CharField(required=False)
    rich_content = serializers.JSONField(required=False)
    
    # Template-based content
    template_code = serializers.CharField(max_length=50, required=False)
    template_variables = serializers.JSONField(required=False, default=dict)
    
    # Delivery options
    recipient_identifier = serializers.CharField(
        max_length=255, required=False,
        help_text="Specific recipient (phone/email/device_token)"
    )
    
    scheduled_at = serializers.DateTimeField(
        required=False,
        help_text="Schedule notification for future delivery"
    )
    
    # Context fields
    related_request_id = serializers.UUIDField(required=False)
    related_entity_type = serializers.CharField(max_length=50, required=False)
    related_entity_id = serializers.UUIDField(required=False)
    
    # Response fields
    notification_id = serializers.UUIDField(read_only=True)
    delivery_status = serializers.CharField(read_only=True)
    
    def validate(self, attrs):
        """Cross-field validation for notification sending."""
        notification_type = attrs.get('notification_type')
        category = attrs.get('category')
        template_code = attrs.get('template_code')
        title = attrs.get('title')
        message = attrs.get('message')
        recipient_identifier = attrs.get('recipient_identifier')
        scheduled_at = attrs.get('scheduled_at')
        
        # Content validation - either direct content or template
        if template_code:
            # Template-based notification
            try:
                template = NotificationTemplate.objects.get(
                    template_code=template_code,
                    notification_type=notification_type,
                    category=category,
                    is_active=True
                )
                attrs['_template'] = template
            except NotificationTemplate.DoesNotExist:
                raise serializers.ValidationError({
                    'template_code': 'Invalid or inactive template code.'
                })
            
            # Validate template variables
            template_variables = attrs.get('template_variables', {})
            try:
                template.validate_variables(template_variables)
            except ValueError as e:
                raise serializers.ValidationError({
                    'template_variables': str(e)
                })
        else:
            # Direct content notification
            if not message:
                raise serializers.ValidationError({
                    'message': 'Message is required when not using template.'
                })
        
        # Recipient validation for direct sends
        if recipient_identifier:
            if notification_type in ['SMS', 'WHATSAPP']:
                if not validate_phone_format(recipient_identifier):
                    raise serializers.ValidationError({
                        'recipient_identifier': 'Invalid phone number format for SMS/WhatsApp.'
                    })
            elif notification_type == 'EMAIL':
                if not validate_email_format(recipient_identifier):
                    raise serializers.ValidationError({
                        'recipient_identifier': 'Invalid email address format.'
                    })
        
        # Schedule validation
        if scheduled_at:
            if scheduled_at <= timezone.now():
                raise serializers.ValidationError({
                    'scheduled_at': 'Scheduled time must be in the future.'
                })
            
            # Maximum schedule window (30 days)
            max_schedule = timezone.now() + timezone.timedelta(days=30)
            if scheduled_at > max_schedule:
                raise serializers.ValidationError({
                    'scheduled_at': 'Cannot schedule more than 30 days in advance.'
                })
        
        return attrs


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing notifications.
    
    Provides essential notification information for
    list views with status and delivery tracking.
    """
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Calculated fields
    is_scheduled = serializers.SerializerMethodField()
    delivery_time_seconds = serializers.SerializerMethodField()
    read_time_seconds = serializers.SerializerMethodField()
    
    # Masked recipient
    masked_recipient = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'category', 'category_display', 'priority', 'priority_display',
            'title', 'message', 'masked_recipient', 'status', 'status_display',
            'is_scheduled', 'scheduled_at', 'sent_at', 'delivered_at',
            'read_at', 'delivery_time_seconds', 'read_time_seconds',
            'click_count', 'created_at'
        ]
        read_only_fields = '__all__'
    
    def get_is_scheduled(self, obj):
        """Check if notification is scheduled."""
        return obj.is_scheduled
    
    def get_delivery_time_seconds(self, obj):
        """Get delivery time in seconds."""
        delivery_time = obj.delivery_time
        return int(delivery_time.total_seconds()) if delivery_time else None
    
    def get_read_time_seconds(self, obj):
        """Get read time in seconds."""
        read_time = obj.read_time
        return int(read_time.total_seconds()) if read_time else None
    
    def get_masked_recipient(self, obj):
        """Get masked recipient identifier."""
        from core.utils import decrypt_field, mask_phone_number, mask_email
        
        try:
            decrypted = decrypt_field(obj.recipient_identifier)
            
            if obj.notification_type in ['SMS', 'WHATSAPP']:
                return mask_phone_number(decrypted)
            elif obj.notification_type == 'EMAIL':
                return mask_email(decrypted)
            else:
                return "***"
        except:
            return "***"


class NotificationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed notification view.
    
    Provides comprehensive notification information including
    delivery tracking, analytics, and related context.
    """
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Calculated fields
    is_scheduled = serializers.SerializerMethodField()
    can_retry = serializers.SerializerMethodField()
    delivery_time_seconds = serializers.SerializerMethodField()
    read_time_seconds = serializers.SerializerMethodField()
    
    # Masked recipient
    masked_recipient = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'category', 'category_display', 'priority', 'priority_display',
            'title', 'message', 'rich_content', 'masked_recipient',
            'status', 'status_display', 'is_scheduled', 'can_retry',
            'scheduled_at', 'sent_at', 'delivered_at', 'read_at',
            'external_message_id', 'external_status', 'delivery_attempts',
            'max_delivery_attempts', 'error_code', 'error_message',
            'retry_after', 'template_code', 'template_variables',
            'related_request_id', 'related_entity_type', 'related_entity_id',
            'delivery_time_seconds', 'read_time_seconds', 'click_count',
            'last_clicked_at', 'created_at', 'updated_at'
        ]
        read_only_fields = '__all__'
    
    def get_is_scheduled(self, obj):
        """Check if notification is scheduled."""
        return obj.is_scheduled
    
    def get_can_retry(self, obj):
        """Check if notification can be retried."""
        return obj.can_retry
    
    def get_delivery_time_seconds(self, obj):
        """Get delivery time in seconds."""
        delivery_time = obj.delivery_time
        return int(delivery_time.total_seconds()) if delivery_time else None
    
    def get_read_time_seconds(self, obj):
        """Get read time in seconds."""
        read_time = obj.read_time
        return int(read_time.total_seconds()) if read_time else None
    
    def get_masked_recipient(self, obj):
        """Get masked recipient identifier."""
        from core.utils import decrypt_field, mask_phone_number, mask_email
        
        try:
            decrypted = decrypt_field(obj.recipient_identifier)
            
            if obj.notification_type in ['SMS', 'WHATSAPP']:
                return mask_phone_number(decrypted)
            elif obj.notification_type == 'EMAIL':
                return mask_email(decrypted)
            else:
                return "***"
        except:
            return "***"


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for notification preferences.
    
    Handles customer notification preferences with
    proper validation and consent management.
    """
    
    # Calculated fields
    is_quiet_hours_active = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationPreference
        fields = [
            'push_notifications_enabled', 'sms_notifications_enabled',
            'email_notifications_enabled', 'whatsapp_notifications_enabled',
            'security_alerts_enabled', 'transaction_updates_enabled',
            'marketing_communications_enabled', 'service_notifications_enabled',
            'limit_request_updates_enabled', 'quiet_hours_start',
            'quiet_hours_end', 'timezone', 'preferred_language',
            'marketing_consent_given', 'marketing_consent_date',
            'is_quiet_hours_active', 'updated_at'
        ]
        read_only_fields = ['marketing_consent_date', 'is_quiet_hours_active', 'updated_at']
    
    def get_is_quiet_hours_active(self, obj):
        """Check if quiet hours are currently active."""
        return obj.is_quiet_hours()
    
    def validate_quiet_hours_start(self, value):
        """Validate quiet hours start time."""
        if value:
            # Ensure it's a valid time
            if not (0 <= value.hour <= 23 and 0 <= value.minute <= 59):
                raise serializers.ValidationError("Invalid time format")
        return value
    
    def validate_quiet_hours_end(self, value):
        """Validate quiet hours end time."""
        if value:
            # Ensure it's a valid time
            if not (0 <= value.hour <= 23 and 0 <= value.minute <= 59):
                raise serializers.ValidationError("Invalid time format")
        return value
    
    def validate_timezone(self, value):
        """Validate timezone."""
        import pytz
        try:
            pytz.timezone(value)
        except pytz.exceptions.UnknownTimeZoneError:
            raise serializers.ValidationError("Invalid timezone")
        return value
    
    def validate_preferred_language(self, value):
        """Validate language code."""
        supported_languages = ['en', 'hi', 'mr', 'gu', 'ta', 'te', 'kn', 'ml']
        if value not in supported_languages:
            raise serializers.ValidationError(
                f"Language must be one of: {', '.join(supported_languages)}"
            )
        return value
    
    def update(self, instance, validated_data):
        """Update preferences with consent tracking."""
        user = self.context.get('user')
        if user:
            validated_data['last_updated_by'] = user.username
        
        # Handle marketing consent
        marketing_enabled = validated_data.get('marketing_communications_enabled', instance.marketing_communications_enabled)
        
        if marketing_enabled and not instance.marketing_consent_given:
            # First time enabling marketing - record consent
            instance.give_marketing_consent()
        elif not marketing_enabled and instance.marketing_consent_given:
            # Disabling marketing - revoke consent
            instance.revoke_marketing_consent()
        
        return super().update(instance, validated_data)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for notification templates.
    
    Handles template management with multi-language support,
    A/B testing, and performance analytics.
    """
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    # Analytics
    click_through_rate = serializers.SerializerMethodField()
    read_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'template_code', 'template_name',
            'category', 'category_display',
            'notification_type', 'notification_type_display',
            'language_code', 'title_template', 'message_template',
            'rich_content_template', 'available_variables',
            'required_variables', 'is_active', 'priority',
            'variant_name', 'test_percentage', 'send_count',
            'click_count', 'read_count', 'click_through_rate',
            'read_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'send_count', 'click_count', 'read_count',
            'click_through_rate', 'read_rate', 'created_at', 'updated_at'
        ]
    
    def get_click_through_rate(self, obj):
        """Calculate click-through rate."""
        return obj.click_through_rate
    
    def get_read_rate(self, obj):
        """Calculate read rate."""
        return obj.read_rate
    
    def validate_template_code(self, value):
        """Validate template code uniqueness."""
        if self.instance:
            # Update case - exclude current instance
            existing = NotificationTemplate.objects.filter(
                template_code=value
            ).exclude(pk=self.instance.pk)
        else:
            # Create case
            existing = NotificationTemplate.objects.filter(template_code=value)
        
        if existing.exists():
            raise serializers.ValidationError("Template code must be unique")
        
        return value
    
    def validate_message_template(self, value):
        """Validate message template format."""
        # Basic template syntax validation
        try:
            # Test with dummy variables
            test_vars = {var: f"test_{var}" for var in ['customer_name', 'amount', 'reference_number']}
            value.format(**test_vars)
        except KeyError as e:
            raise serializers.ValidationError(
                f"Template contains undefined variable: {e}"
            )
        except ValueError as e:
            raise serializers.ValidationError(
                f"Invalid template syntax: {e}"
            )
        
        return value
    
    def validate_test_percentage(self, value):
        """Validate A/B test percentage."""
        if not (0 <= value <= 100):
            raise serializers.ValidationError("Test percentage must be between 0 and 100")
        return value


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for notification statistics and analytics.
    
    Provides comprehensive analytics for notification delivery,
    engagement rates, and performance metrics.
    """
    
    # Delivery stats
    total_sent = serializers.IntegerField(read_only=True)
    total_delivered = serializers.IntegerField(read_only=True)
    total_read = serializers.IntegerField(read_only=True)
    total_clicked = serializers.IntegerField(read_only=True)
    total_failed = serializers.IntegerField(read_only=True)
    
    # Success rates
    delivery_rate = serializers.FloatField(read_only=True)
    read_rate = serializers.FloatField(read_only=True)
    click_through_rate = serializers.FloatField(read_only=True)
    
    # By notification type
    push_count = serializers.IntegerField(read_only=True)
    sms_count = serializers.IntegerField(read_only=True)
    email_count = serializers.IntegerField(read_only=True)
    whatsapp_count = serializers.IntegerField(read_only=True)
    
    # By category
    security_count = serializers.IntegerField(read_only=True)
    transaction_count = serializers.IntegerField(read_only=True)
    marketing_count = serializers.IntegerField(read_only=True)
    service_count = serializers.IntegerField(read_only=True)
    limit_request_count = serializers.IntegerField(read_only=True)
    
    # Performance metrics
    avg_delivery_time_seconds = serializers.FloatField(read_only=True)
    avg_read_time_seconds = serializers.FloatField(read_only=True)
    
    # Time period
    period_start = serializers.DateTimeField(read_only=True)
    period_end = serializers.DateTimeField(read_only=True)


class NotificationBulkSendSerializer(serializers.Serializer):
    """
    Serializer for bulk notification sending.
    
    Handles bulk notification operations with proper
    validation, segmentation, and scheduling support.
    """
    
    notification_type = serializers.ChoiceField(
        choices=NotificationLog.NOTIFICATION_TYPE_CHOICES
    )
    
    category = serializers.ChoiceField(
        choices=NotificationLog.CATEGORY_CHOICES
    )
    
    template_code = serializers.CharField(max_length=50)
    
    # Recipient segmentation
    recipient_filter = serializers.JSONField(
        help_text="Filter criteria for recipient selection"
    )
    
    # Scheduling
    scheduled_at = serializers.DateTimeField(required=False)
    
    # Batch processing
    batch_size = serializers.IntegerField(min_value=1, max_value=1000, default=100)
    
    # Response fields
    estimated_recipients = serializers.IntegerField(read_only=True)
    bulk_job_id = serializers.UUIDField(read_only=True)
    
    def validate_template_code(self, value):
        """Validate template exists and is active."""
        try:
            template = NotificationTemplate.objects.get(
                template_code=value,
                is_active=True
            )
            return value
        except NotificationTemplate.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive template code")
    
    def validate_recipient_filter(self, value):
        """Validate recipient filter criteria."""
        allowed_filters = [
            'customer_segment', 'is_kyc_completed', 'card_type',
            'limit_request_status', 'last_login_days'
        ]
        
        for key in value.keys():
            if key not in allowed_filters:
                raise serializers.ValidationError(
                    f"Invalid filter criteria: {key}. "
                    f"Allowed filters: {', '.join(allowed_filters)}"
                )
        
        return value
    
    def validate_scheduled_at(self, value):
        """Validate scheduled time for bulk send."""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        
        return value