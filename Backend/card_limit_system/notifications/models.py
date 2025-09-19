"""
Notification models for managing customer communications.

This module handles all types of notifications including push notifications,
SMS, email, and in-app notifications with delivery tracking and audit trail.
"""

import uuid
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField


class NotificationLog(models.Model):
    """
    Model for tracking all customer notifications.
    
    Provides comprehensive logging and delivery tracking for all
    communication channels with customer consent management.
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('PUSH', 'Push Notification'),
        ('SMS', 'SMS Message'),
        ('EMAIL', 'Email'),
        ('IN_APP', 'In-App Notification'),
        ('WHATSAPP', 'WhatsApp Message'),
    ]
    
    CATEGORY_CHOICES = [
        ('SECURITY', 'Security Alert'),
        ('TRANSACTION', 'Transaction Update'),
        ('MARKETING', 'Marketing Communication'),
        ('SERVICE', 'Service Notification'),
        ('LIMIT_REQUEST', 'Limit Request Update'),
        ('SYSTEM', 'System Notification'),
        ('REMINDER', 'Reminder'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('QUEUED', 'Queued for Sending'),
        ('SENDING', 'Being Sent'),
        ('SENT', 'Sent Successfully'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read by Recipient'),
        ('FAILED', 'Send Failed'),
        ('BOUNCED', 'Bounced'),
        ('BLOCKED', 'Blocked'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient identification
    customer_firebase_uid = models.CharField(max_length=255, db_index=True)
    recipient_identifier = models.CharField(max_length=255)  # Encrypted phone/email/device_token
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    
    # Content
    title = models.CharField(max_length=200, null=True, blank=True)
    message = models.TextField()
    rich_content = models.JSONField(null=True, blank=True)  # For rich notifications
    
    # Delivery details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='QUEUED')
    scheduled_at = models.DateTimeField(null=True, blank=True)  # For scheduled notifications
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # External service tracking
    external_message_id = models.CharField(max_length=255, null=True, blank=True)
    external_status = models.CharField(max_length=100, null=True, blank=True)
    delivery_attempts = models.IntegerField(default=0)
    max_delivery_attempts = models.IntegerField(default=3)
    
    # Error tracking
    error_code = models.CharField(max_length=50, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    retry_after = models.DateTimeField(null=True, blank=True)
    
    # Related entities
    related_request_id = models.UUIDField(null=True, blank=True)
    related_entity_type = models.CharField(max_length=50, null=True, blank=True)
    related_entity_id = models.UUIDField(null=True, blank=True)
    
    # Template and personalization
    template_code = models.CharField(max_length=50, null=True, blank=True)
    template_variables = models.JSONField(null=True, blank=True)
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    
    # Analytics
    click_count = models.IntegerField(default=0)
    last_clicked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notification_logs'
        indexes = [
            models.Index(fields=['customer_firebase_uid', 'category']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['related_request_id']),
            models.Index(fields=['external_message_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title or self.message[:50]}"
    
    @property
    def is_scheduled(self):
        """Check if notification is scheduled for future delivery."""
        return self.scheduled_at and self.scheduled_at > timezone.now()
    
    @property
    def can_retry(self):
        """Check if notification can be retried."""
        return (
            self.status == 'FAILED' and
            self.delivery_attempts < self.max_delivery_attempts and
            (not self.retry_after or self.retry_after <= timezone.now())
        )
    
    @property
    def delivery_time(self):
        """Calculate delivery time if delivered."""
        if self.sent_at and self.delivered_at:
            return self.delivered_at - self.sent_at
        return None
    
    @property
    def read_time(self):
        """Calculate time from delivery to read."""
        if self.delivered_at and self.read_at:
            return self.read_at - self.delivered_at
        return None
    
    def mark_sent(self, external_id=None):
        """Mark notification as sent."""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.external_message_id = external_id
        self.save(update_fields=['status', 'sent_at', 'external_message_id'])
    
    def mark_delivered(self, external_status=None):
        """Mark notification as delivered."""
        self.status = 'DELIVERED'
        self.delivered_at = timezone.now()
        if external_status:
            self.external_status = external_status
        self.save(update_fields=['status', 'delivered_at', 'external_status'])
    
    def mark_read(self):
        """Mark notification as read."""
        self.status = 'READ'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    def mark_failed(self, error_code=None, error_message=None, retry_after=None):
        """Mark notification as failed."""
        self.status = 'FAILED'
        self.delivery_attempts += 1
        self.error_code = error_code
        self.error_message = error_message
        self.retry_after = retry_after
        self.save(update_fields=['status', 'delivery_attempts', 'error_code', 'error_message', 'retry_after'])
    
    def track_click(self):
        """Track notification click."""
        self.click_count += 1
        self.last_clicked_at = timezone.now()
        self.save(update_fields=['click_count', 'last_clicked_at'])
    
    @classmethod
    def get_pending_notifications(cls):
        """Get notifications pending delivery."""
        now = timezone.now()
        return cls.objects.filter(
            status='QUEUED',
            scheduled_at__lte=now
        ).order_by('priority', 'created_at')
    
    @classmethod
    def get_retry_notifications(cls):
        """Get failed notifications eligible for retry."""
        now = timezone.now()
        return cls.objects.filter(
            status='FAILED',
            delivery_attempts__lt=models.F('max_delivery_attempts'),
            retry_after__lte=now
        ).order_by('priority', 'created_at')
    
    @classmethod
    def cleanup_old_notifications(cls, days=90):
        """Cleanup old notification records."""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = cls.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['SENT', 'DELIVERED', 'READ', 'FAILED', 'CANCELLED']
        ).delete()[0]
        return deleted_count


class NotificationTemplate(models.Model):
    """
    Model for storing notification message templates.
    
    Supports multiple languages, channels, and dynamic content
    with A/B testing capabilities.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Template identification
    template_code = models.CharField(max_length=50, unique=True, db_index=True)
    template_name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=NotificationLog.CATEGORY_CHOICES)
    notification_type = models.CharField(max_length=20, choices=NotificationLog.NOTIFICATION_TYPE_CHOICES)
    
    # Localization
    language_code = models.CharField(max_length=5, default='en')
    
    # Content
    title_template = models.CharField(max_length=200, null=True, blank=True)
    message_template = models.TextField()
    rich_content_template = models.JSONField(null=True, blank=True)
    
    # Template variables
    available_variables = models.JSONField(default=list)
    required_variables = models.JSONField(default=list)
    
    # Settings
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    
    # A/B Testing
    variant_name = models.CharField(max_length=50, null=True, blank=True)
    test_percentage = models.IntegerField(default=100)  # Percentage of users to receive this variant
    
    # Analytics
    send_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    read_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'notification_templates'
        indexes = [
            models.Index(fields=['template_code']),
            models.Index(fields=['category', 'notification_type']),
            models.Index(fields=['is_active', 'priority']),
        ]
        unique_together = [
            ('category', 'notification_type', 'language_code', 'variant_name'),
        ]
        ordering = ['priority', 'template_name']
    
    def __str__(self):
        return f"{self.template_name} ({self.get_notification_type_display()})"
    
    def render_title(self, variables):
        """Render title template with variables."""
        if not self.title_template:
            return None
        try:
            return self.title_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable in title: {e}")
    
    def render_message(self, variables):
        """Render message template with variables."""
        try:
            return self.message_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable in message: {e}")
    
    def render_rich_content(self, variables):
        """Render rich content template with variables."""
        if not self.rich_content_template:
            return None
        
        try:
            # Recursively format JSON content
            def format_json(obj):
                if isinstance(obj, dict):
                    return {k: format_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [format_json(item) for item in obj]
                elif isinstance(obj, str):
                    return obj.format(**variables)
                else:
                    return obj
            
            return format_json(self.rich_content_template)
        except KeyError as e:
            raise ValueError(f"Missing template variable in rich content: {e}")
    
    def validate_variables(self, variables):
        """Validate that all required variables are provided."""
        missing_vars = set(self.required_variables) - set(variables.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        return True
    
    def increment_send_count(self):
        """Increment send count for analytics."""
        self.send_count += 1
        self.save(update_fields=['send_count'])
    
    def increment_click_count(self):
        """Increment click count for analytics."""
        self.click_count += 1
        self.save(update_fields=['click_count'])
    
    def increment_read_count(self):
        """Increment read count for analytics."""
        self.read_count += 1
        self.save(update_fields=['read_count'])
    
    @property
    def click_through_rate(self):
        """Calculate click-through rate."""
        if self.send_count == 0:
            return 0
        return (self.click_count / self.send_count) * 100
    
    @property
    def read_rate(self):
        """Calculate read rate."""
        if self.send_count == 0:
            return 0
        return (self.read_count / self.send_count) * 100
    
    @classmethod
    def get_template(cls, category, notification_type, language='en', customer_id=None):
        """Get active template for category and notification type with A/B testing."""
        templates = cls.objects.filter(
            category=category,
            notification_type=notification_type,
            language_code=language,
            is_active=True
        ).order_by('priority')
        
        if not templates:
            return None
        
        # Simple A/B testing based on customer ID hash
        if customer_id and len(templates) > 1:
            import hashlib
            hash_value = int(hashlib.md5(customer_id.encode()).hexdigest(), 16)
            template_index = hash_value % len(templates)
            selected_template = templates[template_index]
            
            # Check if template is within test percentage
            if hash_value % 100 < selected_template.test_percentage:
                return selected_template
        
        # Return first (highest priority) template
        return templates.first()


class NotificationPreference(models.Model):
    """
    Model for managing customer notification preferences.
    
    Allows customers to control which notifications they receive
    through which channels with consent tracking.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Customer identification
    customer_firebase_uid = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Channel preferences
    push_notifications_enabled = models.BooleanField(default=True)
    sms_notifications_enabled = models.BooleanField(default=True)
    email_notifications_enabled = models.BooleanField(default=True)
    whatsapp_notifications_enabled = models.BooleanField(default=False)
    
    # Category preferences
    security_alerts_enabled = models.BooleanField(default=True)
    transaction_updates_enabled = models.BooleanField(default=True)
    marketing_communications_enabled = models.BooleanField(default=False)
    service_notifications_enabled = models.BooleanField(default=True)
    limit_request_updates_enabled = models.BooleanField(default=True)
    
    # Timing preferences
    quiet_hours_start = models.TimeField(null=True, blank=True)  # e.g., 22:00
    quiet_hours_end = models.TimeField(null=True, blank=True)    # e.g., 08:00
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    
    # Language preference
    preferred_language = models.CharField(max_length=5, default='en')
    
    # Consent tracking
    marketing_consent_given = models.BooleanField(default=False)
    marketing_consent_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'notification_preferences'
        indexes = [
            models.Index(fields=['customer_firebase_uid']),
        ]
    
    def __str__(self):
        return f"Notification preferences for {self.customer_firebase_uid[:8]}..."
    
    def is_channel_enabled(self, notification_type):
        """Check if specific notification channel is enabled."""
        channel_map = {
            'PUSH': self.push_notifications_enabled,
            'SMS': self.sms_notifications_enabled,
            'EMAIL': self.email_notifications_enabled,
            'WHATSAPP': self.whatsapp_notifications_enabled,
        }
        return channel_map.get(notification_type, False)
    
    def is_category_enabled(self, category):
        """Check if specific notification category is enabled."""
        category_map = {
            'SECURITY': self.security_alerts_enabled,
            'TRANSACTION': self.transaction_updates_enabled,
            'MARKETING': self.marketing_communications_enabled,
            'SERVICE': self.service_notifications_enabled,
            'LIMIT_REQUEST': self.limit_request_updates_enabled,
        }
        return category_map.get(category, True)
    
    def is_quiet_hours(self):
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        from datetime import datetime
        import pytz
        
        try:
            tz = pytz.timezone(self.timezone)
            current_time = datetime.now(tz).time()
            
            if self.quiet_hours_start <= self.quiet_hours_end:
                # Same day quiet hours (e.g., 22:00 to 23:59)
                return self.quiet_hours_start <= current_time <= self.quiet_hours_end
            else:
                # Overnight quiet hours (e.g., 22:00 to 08:00)
                return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
        except:
            return False
    
    def should_send_notification(self, notification_type, category, priority='NORMAL'):
        """Check if notification should be sent based on preferences."""
        # Always send critical notifications
        if priority == 'CRITICAL':
            return True
        
        # Check channel preference
        if not self.is_channel_enabled(notification_type):
            return False
        
        # Check category preference
        if not self.is_category_enabled(category):
            return False
        
        # Check marketing consent for marketing notifications
        if category == 'MARKETING' and not self.marketing_consent_given:
            return False
        
        # Check quiet hours for non-critical notifications
        if priority in ['LOW', 'NORMAL'] and self.is_quiet_hours():
            return False
        
        return True
    
    def give_marketing_consent(self):
        """Record marketing consent."""
        self.marketing_consent_given = True
        self.marketing_consent_date = timezone.now()
        self.save(update_fields=['marketing_consent_given', 'marketing_consent_date'])
    
    def revoke_marketing_consent(self):
        """Revoke marketing consent."""
        self.marketing_consent_given = False
        self.marketing_consent_date = None
        self.save(update_fields=['marketing_consent_given', 'marketing_consent_date'])