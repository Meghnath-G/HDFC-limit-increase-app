"""
Django REST Framework serializers for OTP models.

Provides secure OTP management with proper validation,
rate limiting, and multi-channel delivery support.
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import OTPLog, OTPTemplate, OTPBlacklist
from core.utils import validate_phone_format, validate_email_format


class OTPGenerateSerializer(serializers.Serializer):
    """
    Serializer for OTP generation requests.
    
    Handles OTP generation with proper validation,
    rate limiting, and security checks.
    """
    
    otp_type = serializers.ChoiceField(
        choices=OTPLog.OTP_TYPE_CHOICES,
        help_text="Purpose of OTP generation"
    )
    
    delivery_method = serializers.ChoiceField(
        choices=OTPLog.DELIVERY_METHOD_CHOICES,
        help_text="Method for OTP delivery"
    )
    
    recipient_identifier = serializers.CharField(
        max_length=255,
        help_text="Phone number (+91XXXXXXXXXX) or email address"
    )
    
    # Optional fields
    otp_length = serializers.IntegerField(
        min_value=4, max_value=8, default=6,
        help_text="Length of OTP (4-8 digits)"
    )
    
    validity_minutes = serializers.IntegerField(
        min_value=1, max_value=30, default=10,
        help_text="OTP validity in minutes (1-30)"
    )
    
    # Context fields
    related_request_id = serializers.UUIDField(required=False)
    related_entity_type = serializers.CharField(max_length=50, required=False)
    
    # Response fields
    otp_reference = serializers.CharField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)
    delivery_status = serializers.CharField(read_only=True)
    
    def validate_recipient_identifier(self, value):
        """Validate recipient identifier format."""
        delivery_method = self.initial_data.get('delivery_method')
        
        if delivery_method in ['SMS', 'WHATSAPP', 'VOICE']:
            # Validate phone number format
            if not validate_phone_format(value):
                raise serializers.ValidationError(
                    "Phone number must be in +91XXXXXXXXXX format with valid Indian mobile number"
                )
        
        elif delivery_method == 'EMAIL':
            # Validate email format
            if not validate_email_format(value):
                raise serializers.ValidationError("Invalid email address format")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation and rate limiting checks."""
        customer = self.context.get('customer')
        request_obj = self.context.get('request')
        
        if not customer:
            raise serializers.ValidationError("Customer context required")
        
        otp_type = attrs['otp_type']
        delivery_method = attrs['delivery_method']
        recipient_identifier = attrs['recipient_identifier']
        
        # Check blacklist
        if OTPBlacklist.is_blocked(recipient_identifier, 'PHONE' if delivery_method in ['SMS', 'WHATSAPP', 'VOICE'] else 'EMAIL'):
            raise serializers.ValidationError({
                'recipient_identifier': 'This recipient is blocked from receiving OTPs.'
            })
        
        # Rate limiting checks
        customer_rate_limit = OTPLog.get_rate_limit_count(
            customer.firebase_uid, otp_type, time_window_minutes=60
        )
        
        if customer_rate_limit >= 5:  # Max 5 OTPs per hour per customer per type
            raise serializers.ValidationError(
                'Maximum OTP limit exceeded. Please try again after an hour.'
            )
        
        # IP-based rate limiting
        if request_obj:
            from core.utils import get_client_ip
            ip_address = get_client_ip(request_obj)
            
            ip_rate_limit = OTPLog.get_ip_rate_limit_count(ip_address, time_window_minutes=60)
            
            if ip_rate_limit >= 10:  # Max 10 OTPs per hour per IP
                raise serializers.ValidationError(
                    'Too many OTP requests from this location. Please try again later.'
                )
        
        # Check for recent OTP to same recipient
        recent_otp = OTPLog.objects.filter(
            customer_firebase_uid=customer.firebase_uid,
            recipient_identifier=recipient_identifier,
            otp_type=otp_type,
            generated_at__gte=timezone.now() - timedelta(minutes=2)
        ).first()
        
        if recent_otp:
            raise serializers.ValidationError(
                'Please wait at least 2 minutes before requesting another OTP.'
            )
        
        return attrs


class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    
    Handles OTP verification with proper security checks,
    attempt limiting, and audit logging.
    """
    
    otp_reference = serializers.CharField(
        max_length=100,
        help_text="OTP reference number received during generation"
    )
    
    otp_code = serializers.CharField(
        min_length=4, max_length=8,
        help_text="OTP code received via SMS/Email/WhatsApp"
    )
    
    # Response fields
    verification_status = serializers.CharField(read_only=True)
    verified_at = serializers.DateTimeField(read_only=True)
    attempts_remaining = serializers.IntegerField(read_only=True)
    
    def validate_otp_code(self, value):
        """Validate OTP code format."""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")
        return value
    
    def validate(self, attrs):
        """Validate OTP verification request."""
        customer = self.context.get('customer')
        
        if not customer:
            raise serializers.ValidationError("Customer context required")
        
        otp_reference = attrs['otp_reference']
        otp_code = attrs['otp_code']
        
        # Find OTP record
        try:
            otp_log = OTPLog.objects.get(
                otp_reference=otp_reference,
                customer_firebase_uid=customer.firebase_uid
            )
        except OTPLog.DoesNotExist:
            raise serializers.ValidationError({
                'otp_reference': 'Invalid OTP reference number.'
            })
        
        # Check OTP validity
        if not otp_log.is_valid:
            if otp_log.is_expired:
                raise serializers.ValidationError('OTP has expired. Please request a new one.')
            elif otp_log.attempt_count >= otp_log.max_attempts:
                raise serializers.ValidationError('Maximum verification attempts exceeded.')
            elif otp_log.status in ['VERIFIED']:
                raise serializers.ValidationError('OTP has already been verified.')
            else:
                raise serializers.ValidationError('OTP is no longer valid.')
        
        # Store OTP log in context for view processing
        attrs['_otp_log'] = otp_log
        
        return attrs


class OTPStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for OTP status information.
    
    Provides OTP status details without exposing
    sensitive information like actual OTP codes.
    """
    
    otp_type_display = serializers.CharField(source='get_otp_type_display', read_only=True)
    delivery_method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Calculated fields
    is_expired = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    attempts_remaining = serializers.SerializerMethodField()
    
    # Masked recipient
    masked_recipient = serializers.SerializerMethodField()
    
    class Meta:
        model = OTPLog
        fields = [
            'otp_reference', 'otp_type', 'otp_type_display',
            'delivery_method', 'delivery_method_display',
            'status', 'status_display', 'masked_recipient',
            'attempt_count', 'max_attempts', 'attempts_remaining',
            'generated_at', 'expires_at', 'verified_at',
            'is_expired', 'is_valid', 'time_remaining'
        ]
        read_only_fields = '__all__'
    
    def get_is_expired(self, obj):
        """Check if OTP is expired."""
        return obj.is_expired
    
    def get_is_valid(self, obj):
        """Check if OTP is valid for verification."""
        return obj.is_valid
    
    def get_time_remaining(self, obj):
        """Get remaining time in seconds."""
        if obj.is_expired:
            return 0
        
        remaining = obj.expires_at - timezone.now()
        return max(0, int(remaining.total_seconds()))
    
    def get_attempts_remaining(self, obj):
        """Get remaining verification attempts."""
        return obj.attempts_remaining
    
    def get_masked_recipient(self, obj):
        """Get masked recipient identifier."""
        from core.utils import decrypt_field, mask_phone_number, mask_email
        
        try:
            decrypted = decrypt_field(obj.recipient_identifier)
            
            if obj.delivery_method in ['SMS', 'WHATSAPP', 'VOICE']:
                return mask_phone_number(decrypted)
            else:
                return mask_email(decrypted)
        except:
            return "***"


class OTPResendSerializer(serializers.Serializer):
    """
    Serializer for OTP resend requests.
    
    Handles OTP resend with rate limiting and
    delivery method changes.
    """
    
    otp_reference = serializers.CharField(
        max_length=100,
        help_text="Original OTP reference number"
    )
    
    delivery_method = serializers.ChoiceField(
        choices=OTPLog.DELIVERY_METHOD_CHOICES,
        required=False,
        help_text="New delivery method (optional)"
    )
    
    # Response fields
    new_otp_reference = serializers.CharField(read_only=True)
    delivery_status = serializers.CharField(read_only=True)
    
    def validate(self, attrs):
        """Validate resend request."""
        customer = self.context.get('customer')
        
        if not customer:
            raise serializers.ValidationError("Customer context required")
        
        otp_reference = attrs['otp_reference']
        
        # Find original OTP record
        try:
            original_otp = OTPLog.objects.get(
                otp_reference=otp_reference,
                customer_firebase_uid=customer.firebase_uid
            )
        except OTPLog.DoesNotExist:
            raise serializers.ValidationError({
                'otp_reference': 'Invalid OTP reference number.'
            })
        
        # Check if resend is allowed
        if original_otp.status == 'VERIFIED':
            raise serializers.ValidationError('Cannot resend verified OTP.')
        
        # Rate limiting for resends
        recent_resends = OTPLog.objects.filter(
            customer_firebase_uid=customer.firebase_uid,
            otp_type=original_otp.otp_type,
            generated_at__gte=timezone.now() - timedelta(minutes=60)
        ).count()
        
        if recent_resends >= 3:  # Max 3 resends per hour
            raise serializers.ValidationError(
                'Maximum resend limit exceeded. Please try again after an hour.'
            )
        
        # Store original OTP for processing
        attrs['_original_otp'] = original_otp
        
        return attrs


class OTPTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for OTP message templates.
    
    Handles template management with multi-language
    support and variable validation.
    """
    
    otp_type_display = serializers.CharField(source='get_otp_type_display', read_only=True)
    delivery_method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)
    
    class Meta:
        model = OTPTemplate
        fields = [
            'id', 'template_code', 'template_name',
            'otp_type', 'otp_type_display',
            'delivery_method', 'delivery_method_display',
            'language_code', 'subject', 'message_template',
            'available_variables', 'is_active', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_message_template(self, value):
        """Validate message template format."""
        # Check for required OTP placeholder
        if '{otp}' not in value:
            raise serializers.ValidationError(
                "Message template must contain {otp} placeholder"
            )
        
        # Validate template syntax
        try:
            value.format(otp='123456', customer_name='Test')
        except KeyError as e:
            raise serializers.ValidationError(
                f"Invalid template variable: {e}"
            )
        
        return value
    
    def validate_template_code(self, value):
        """Validate template code uniqueness."""
        if self.instance:
            # Update case - exclude current instance
            existing = OTPTemplate.objects.filter(
                template_code=value
            ).exclude(pk=self.instance.pk)
        else:
            # Create case
            existing = OTPTemplate.objects.filter(template_code=value)
        
        if existing.exists():
            raise serializers.ValidationError("Template code must be unique")
        
        return value


class OTPBlacklistSerializer(serializers.ModelSerializer):
    """
    Serializer for OTP blacklist management.
    
    Handles blacklist operations with proper
    security and audit trail features.
    """
    
    block_type_display = serializers.CharField(source='get_block_type_display', read_only=True)
    block_reason_display = serializers.CharField(source='get_block_reason_display', read_only=True)
    
    # Calculated fields
    is_temporary = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    
    # Input field for new blocks
    identifier_plain = serializers.CharField(write_only=True, source='blocked_identifier')
    
    class Meta:
        model = OTPBlacklist
        fields = [
            'id', 'identifier_plain', 'block_type', 'block_type_display',
            'block_reason', 'block_reason_display', 'block_notes',
            'is_active', 'blocked_at', 'blocked_until', 'unblocked_at',
            'blocked_by', 'unblocked_by', 'is_temporary', 'is_expired',
            'time_remaining'
        ]
        read_only_fields = [
            'id', 'blocked_at', 'unblocked_at', 'blocked_by', 'unblocked_by',
            'is_temporary', 'is_expired', 'time_remaining'
        ]
    
    def get_is_temporary(self, obj):
        """Check if block is temporary."""
        return obj.is_temporary
    
    def get_is_expired(self, obj):
        """Check if temporary block has expired."""
        return obj.is_expired
    
    def get_time_remaining(self, obj):
        """Get remaining time for temporary blocks."""
        if not obj.is_temporary or obj.is_expired:
            return None
        
        remaining = obj.blocked_until - timezone.now()
        return max(0, int(remaining.total_seconds()))
    
    def validate_identifier_plain(self, value):
        """Validate identifier format."""
        block_type = self.initial_data.get('block_type')
        
        if block_type == 'PHONE':
            if not validate_phone_format(value):
                raise serializers.ValidationError(
                    "Phone number must be in +91XXXXXXXXXX format"
                )
        elif block_type == 'EMAIL':
            if not validate_email_format(value):
                raise serializers.ValidationError("Invalid email address format")
        elif block_type == 'FIREBASE_UID':
            if len(value) < 10 or len(value) > 128:
                raise serializers.ValidationError("Invalid Firebase UID format")
        
        return value
    
    def create(self, validated_data):
        """Create blacklist entry with encryption."""
        user = self.context.get('user')
        if user:
            validated_data['blocked_by'] = user.username
        
        return super().create(validated_data)


class OTPAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for OTP analytics and statistics.
    
    Provides comprehensive analytics for OTP usage,
    delivery success rates, and security metrics.
    """
    
    # Generation stats
    total_generated = serializers.IntegerField(read_only=True)
    total_sent = serializers.IntegerField(read_only=True)
    total_verified = serializers.IntegerField(read_only=True)
    total_failed = serializers.IntegerField(read_only=True)
    
    # Success rates
    send_success_rate = serializers.FloatField(read_only=True)
    verification_success_rate = serializers.FloatField(read_only=True)
    
    # By delivery method
    sms_count = serializers.IntegerField(read_only=True)
    email_count = serializers.IntegerField(read_only=True)
    whatsapp_count = serializers.IntegerField(read_only=True)
    voice_count = serializers.IntegerField(read_only=True)
    
    # By OTP type
    login_count = serializers.IntegerField(read_only=True)
    transaction_count = serializers.IntegerField(read_only=True)
    profile_update_count = serializers.IntegerField(read_only=True)
    limit_request_count = serializers.IntegerField(read_only=True)
    
    # Security stats
    blocked_attempts = serializers.IntegerField(read_only=True)
    rate_limited_requests = serializers.IntegerField(read_only=True)
    
    # Time period
    period_start = serializers.DateTimeField(read_only=True)
    period_end = serializers.DateTimeField(read_only=True)