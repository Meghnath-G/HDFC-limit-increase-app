"""
OTP (One-Time Password) models for secure authentication.

This module handles OTP generation, storage, and verification
with security best practices including rate limiting and audit logging.
"""

import uuid
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator


class OTPLog(models.Model):
    """
    Model for tracking OTP generation and verification attempts.
    
    Stores hashed OTPs (never plaintext) and provides comprehensive
    audit trail for security monitoring and compliance.
    """
    
    OTP_TYPE_CHOICES = [
        ('LOGIN', 'Login Verification'),
        ('TRANSACTION', 'Transaction Verification'),
        ('PROFILE_UPDATE', 'Profile Update'),
        ('LIMIT_REQUEST', 'Limit Request'),
        ('PASSWORD_RESET', 'Password Reset'),
    ]
    
    STATUS_CHOICES = [
        ('GENERATED', 'Generated'),
        ('SENT', 'Sent Successfully'),
        ('SEND_FAILED', 'Send Failed'),
        ('VERIFIED', 'Successfully Verified'),
        ('EXPIRED', 'Expired'),
        ('FAILED_ATTEMPT', 'Failed Verification'),
        ('BLOCKED', 'Blocked due to max attempts'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('SMS', 'SMS to Phone'),
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('VOICE', 'Voice Call'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # OTP identification
    otp_token = models.CharField(max_length=255, unique=True, db_index=True)  # Hashed OTP
    otp_reference = models.CharField(max_length=100, unique=True, db_index=True)
    
    # User identification (encrypted)
    customer_firebase_uid = models.CharField(max_length=255, db_index=True)
    recipient_identifier = models.CharField(max_length=255)  # Encrypted phone/email
    
    # OTP details
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES)
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHOD_CHOICES)
    otp_length = models.IntegerField(default=6)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GENERATED')
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    # Timing
    generated_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Security context
    request_ip = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    device_fingerprint = models.CharField(max_length=255, null=True, blank=True)
    
    # External service tracking
    external_message_id = models.CharField(max_length=255, null=True, blank=True)
    delivery_status = models.CharField(max_length=50, null=True, blank=True)
    delivery_error = models.TextField(null=True, blank=True)
    
    # Related entities
    related_request_id = models.UUIDField(null=True, blank=True)  # Link to LimitRequest
    related_entity_type = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'otp_logs'
        indexes = [
            models.Index(fields=['customer_firebase_uid', 'otp_type']),
            models.Index(fields=['otp_reference']),
            models.Index(fields=['status', 'generated_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['request_ip', 'generated_at']),
        ]
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"OTP {self.otp_reference} - {self.get_otp_type_display()}"
    
    @property
    def is_expired(self):
        """Check if OTP has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if OTP is still valid for verification."""
        return (
            self.status in ['GENERATED', 'SENT'] and
            not self.is_expired and
            self.attempt_count < self.max_attempts
        )
    
    @property
    def time_remaining(self):
        """Get remaining time before expiry."""
        if self.is_expired:
            return timedelta(0)
        return self.expires_at - timezone.now()
    
    @property
    def attempts_remaining(self):
        """Get remaining verification attempts."""
        return max(0, self.max_attempts - self.attempt_count)
    
    def mark_sent(self, external_id=None, delivery_status=None):
        """Mark OTP as sent successfully."""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.external_message_id = external_id
        self.delivery_status = delivery_status
        self.save(update_fields=['status', 'sent_at', 'external_message_id', 'delivery_status'])
    
    def mark_send_failed(self, error_message=None):
        """Mark OTP send as failed."""
        self.status = 'SEND_FAILED'
        self.delivery_error = error_message
        self.save(update_fields=['status', 'delivery_error'])
    
    def increment_attempt(self):
        """Increment verification attempt counter."""
        self.attempt_count += 1
        if self.attempt_count >= self.max_attempts:
            self.status = 'BLOCKED'
        else:
            self.status = 'FAILED_ATTEMPT'
        self.save(update_fields=['attempt_count', 'status'])
    
    def mark_verified(self):
        """Mark OTP as successfully verified."""
        self.status = 'VERIFIED'
        self.verified_at = timezone.now()
        self.save(update_fields=['status', 'verified_at'])
    
    def mark_expired(self):
        """Mark OTP as expired."""
        self.status = 'EXPIRED'
        self.save(update_fields=['status'])
    
    @classmethod
    def cleanup_expired(cls):
        """Cleanup expired OTP records (run via management command)."""
        cutoff_date = timezone.now() - timedelta(days=30)  # Keep for 30 days
        expired_count = cls.objects.filter(
            expires_at__lt=cutoff_date
        ).delete()[0]
        return expired_count
    
    @classmethod
    def get_rate_limit_count(cls, customer_uid, otp_type, time_window_minutes=60):
        """Get OTP generation count for rate limiting."""
        since = timezone.now() - timedelta(minutes=time_window_minutes)
        return cls.objects.filter(
            customer_firebase_uid=customer_uid,
            otp_type=otp_type,
            generated_at__gte=since
        ).count()
    
    @classmethod
    def get_ip_rate_limit_count(cls, ip_address, time_window_minutes=60):
        """Get OTP generation count per IP for rate limiting."""
        since = timezone.now() - timedelta(minutes=time_window_minutes)
        return cls.objects.filter(
            request_ip=ip_address,
            generated_at__gte=since
        ).count()


class OTPTemplate(models.Model):
    """
    Model for storing OTP message templates.
    
    Supports multiple languages and delivery methods
    with template variables for personalization.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Template identification
    template_code = models.CharField(max_length=50, unique=True, db_index=True)
    template_name = models.CharField(max_length=100)
    otp_type = models.CharField(max_length=20, choices=OTPLog.OTP_TYPE_CHOICES)
    delivery_method = models.CharField(max_length=10, choices=OTPLog.DELIVERY_METHOD_CHOICES)
    
    # Localization
    language_code = models.CharField(max_length=5, default='en')
    
    # Content
    subject = models.CharField(max_length=200, null=True, blank=True)  # For email/push
    message_template = models.TextField()
    
    # Template variables (JSON)
    available_variables = models.JSONField(default=list)
    
    # Settings
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)  # For template selection
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'otp_templates'
        indexes = [
            models.Index(fields=['template_code']),
            models.Index(fields=['otp_type', 'delivery_method']),
            models.Index(fields=['is_active', 'priority']),
        ]
        unique_together = [
            ('otp_type', 'delivery_method', 'language_code'),
        ]
        ordering = ['priority', 'template_name']
    
    def __str__(self):
        return f"{self.template_name} ({self.get_delivery_method_display()})"
    
    def render_message(self, variables):
        """Render template with provided variables."""
        try:
            return self.message_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def render_subject(self, variables):
        """Render subject with provided variables."""
        if not self.subject:
            return None
        try:
            return self.subject.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable in subject: {e}")
    
    @classmethod
    def get_template(cls, otp_type, delivery_method, language='en'):
        """Get active template for OTP type and delivery method."""
        try:
            return cls.objects.filter(
                otp_type=otp_type,
                delivery_method=delivery_method,
                language_code=language,
                is_active=True
            ).order_by('priority').first()
        except cls.DoesNotExist:
            # Fallback to English
            if language != 'en':
                return cls.get_template(otp_type, delivery_method, 'en')
            return None


class OTPBlacklist(models.Model):
    """
    Model for managing blocked phone numbers/emails.
    
    Prevents OTP sending to blocked recipients for
    security and compliance purposes.
    """
    
    BLOCK_TYPE_CHOICES = [
        ('PHONE', 'Phone Number'),
        ('EMAIL', 'Email Address'),
        ('FIREBASE_UID', 'Firebase UID'),
    ]
    
    BLOCK_REASON_CHOICES = [
        ('SPAM', 'Spam/Abuse'),
        ('FRAUD', 'Fraudulent Activity'),
        ('CUSTOMER_REQUEST', 'Customer Request'),
        ('REGULATORY', 'Regulatory Requirement'),
        ('TECHNICAL', 'Technical Issues'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Blocked identifier (encrypted)
    blocked_identifier = models.CharField(max_length=255, unique=True, db_index=True)
    block_type = models.CharField(max_length=20, choices=BLOCK_TYPE_CHOICES)
    
    # Block details
    block_reason = models.CharField(max_length=20, choices=BLOCK_REASON_CHOICES)
    block_notes = models.TextField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timing
    blocked_at = models.DateTimeField(auto_now_add=True)
    blocked_until = models.DateTimeField(null=True, blank=True)  # Temporary blocks
    unblocked_at = models.DateTimeField(null=True, blank=True)
    
    # Audit
    blocked_by = models.CharField(max_length=100)
    unblocked_by = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'otp_blacklist'
        indexes = [
            models.Index(fields=['blocked_identifier']),
            models.Index(fields=['block_type', 'is_active']),
            models.Index(fields=['blocked_until']),
        ]
        ordering = ['-blocked_at']
    
    def __str__(self):
        return f"Blocked {self.get_block_type_display()}: {self.blocked_identifier[:10]}..."
    
    @property
    def is_temporary(self):
        """Check if this is a temporary block."""
        return self.blocked_until is not None
    
    @property
    def is_expired(self):
        """Check if temporary block has expired."""
        if not self.is_temporary:
            return False
        return timezone.now() > self.blocked_until
    
    def unblock(self, unblocked_by):
        """Unblock the identifier."""
        self.is_active = False
        self.unblocked_at = timezone.now()
        self.unblocked_by = unblocked_by
        self.save()
    
    @classmethod
    def is_blocked(cls, identifier, block_type):
        """Check if identifier is currently blocked."""
        from core.utils import encrypt_field
        encrypted_identifier = encrypt_field(identifier)
        
        now = timezone.now()
        active_blocks = cls.objects.filter(
            blocked_identifier=encrypted_identifier,
            block_type=block_type,
            is_active=True
        )
        
        # Check for permanent blocks
        permanent_block = active_blocks.filter(blocked_until__isnull=True).exists()
        if permanent_block:
            return True
        
        # Check for non-expired temporary blocks
        temporary_block = active_blocks.filter(
            blocked_until__isnull=False,
            blocked_until__gt=now
        ).exists()
        
        return temporary_block
    
    @classmethod
    def cleanup_expired_blocks(cls):
        """Cleanup expired temporary blocks."""
        now = timezone.now()
        expired_count = cls.objects.filter(
            is_active=True,
            blocked_until__isnull=False,
            blocked_until__lt=now
        ).update(
            is_active=False,
            unblocked_at=now,
            unblocked_by='SYSTEM_EXPIRY'
        )
        return expired_count