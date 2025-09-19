"""
Limit Request models for the Card Limit Increase System.

This module contains models for managing limit increase requests
with comprehensive workflow and status tracking.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from apps.customers.models import Customer, CardDetail


class LimitRequestManager(models.Manager):
    """Custom manager for LimitRequest with query optimizations."""
    
    def active_requests(self):
        """Get all active (non-completed) requests."""
        return self.filter(status__in=['pending', 'under_review'])
    
    def completed_requests(self):
        """Get all completed requests."""
        return self.filter(status__in=['approved', 'rejected', 'implemented'])
    
    def pending_approval(self):
        """Get requests pending approval."""
        return self.filter(status='under_review')


class LimitRequest(models.Model):
    """
    Model representing a limit increase request.
    
    Tracks the complete lifecycle of limit increase requests
    with proper state management and audit trail.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
        ('cancelled', 'Cancelled'),
    ]
    
    REQUEST_TYPE_CHOICES = [
        ('credit_limit', 'Credit Card Limit'),
        ('debit_limit', 'Debit Card Limit'),
        ('netbanking_limit', 'Net Banking Limit'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique request identifier"
    )
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='limit_requests',
        help_text="Customer making the request"
    )
    
    card_detail = models.ForeignKey(
        CardDetail,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='limit_requests',
        help_text="Related card for card limit requests"
    )
    
    # Request identification
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique reference number for tracking"
    )
    
    # Request details
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        help_text="Type of limit increase request"
    )
    
    current_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Current limit amount in INR"
    )
    
    requested_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Requested new limit amount in INR"
    )
    
    # Request justification
    reason = models.TextField(
        max_length=1000,
        help_text="Customer's reason for limit increase"
    )
    
    income_proof_uploaded = models.BooleanField(
        default=False,
        help_text="Whether income proof document is uploaded"
    )
    
    # Document references (file paths/IDs stored separately)
    supporting_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="List of supporting document references"
    )
    
    # Status and workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current request status"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        help_text="Request priority level"
    )
    
    assigned_officer = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Bank officer assigned to review"
    )
    
    # Decision details
    approved_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Finally approved limit amount"
    )
    
    rejection_reason = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Reason for rejection if applicable"
    )
    
    decision_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when decision was made"
    )
    
    decision_officer = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Officer who made the decision"
    )
    
    # Implementation tracking
    implementation_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when limit was actually updated"
    )
    
    old_system_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Previous limit in banking system"
    )
    
    new_system_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Updated limit in banking system"
    )
    
    # Audit trail
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Request creation timestamp"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )
    
    created_by_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of request creator"
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User agent string of request creator"
    )
    
    # Processing time tracking
    estimated_processing_days = models.PositiveIntegerField(
        default=7,
        help_text="Estimated processing time in days"
    )
    
    actual_processing_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Actual processing time in days"
    )
    
    # Internal notes
    internal_notes = models.TextField(
        null=True,
        blank=True,
        help_text="Internal bank officer notes"
    )
    
    objects = LimitRequestManager()
    
    class Meta:
        db_table = 'limitrequest'
        verbose_name = 'Limit Request'
        verbose_name_plural = 'Limit Requests'
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['request_type', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_officer']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(requested_limit__gt=models.F('current_limit')),
                name='requested_limit_greater_than_current'
            ),
            models.CheckConstraint(
                check=models.Q(
                    models.Q(request_type__in=['credit_limit', 'debit_limit'], card_detail__isnull=False) |
                    models.Q(request_type='netbanking_limit', card_detail__isnull=True)
                ),
                name='card_detail_required_for_card_requests'
            ),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reference_number} - {self.get_request_type_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to generate reference number and handle business logic."""
        # Generate reference number if not set
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()
        
        # Calculate actual processing days when status changes to completed
        if self.status in ['approved', 'rejected'] and not self.actual_processing_days:
            if self.decision_date:
                delta = self.decision_date - self.created_at
                self.actual_processing_days = delta.days
        
        super().save(*args, **kwargs)
    
    def _generate_reference_number(self):
        """Generate unique reference number."""
        from datetime import datetime
        import random
        
        date_part = datetime.now().strftime("%Y%m%d")
        random_part = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        prefix = "LMT"
        
        return f"{prefix}-{date_part}-{random_part}"
    
    @property
    def is_pending(self):
        """Check if request is in pending state."""
        return self.status in ['pending', 'under_review']
    
    @property
    def is_completed(self):
        """Check if request is completed."""
        return self.status in ['approved', 'rejected', 'implemented', 'cancelled']
    
    @property
    def limit_increase_amount(self):
        """Calculate requested increase amount."""
        return self.requested_limit - self.current_limit
    
    @property
    def approved_increase_amount(self):
        """Calculate approved increase amount."""
        if self.approved_limit:
            return self.approved_limit - self.current_limit
        return None
    
    @property
    def processing_time_days(self):
        """Calculate current processing time in days."""
        if self.decision_date:
            delta = self.decision_date - self.created_at
            return delta.days
        else:
            delta = timezone.now() - self.created_at
            return delta.days
    
    @property
    def is_overdue(self):
        """Check if request is overdue based on estimated processing time."""
        return self.processing_time_days > self.estimated_processing_days and self.is_pending
    
    def can_be_cancelled(self):
        """Check if request can be cancelled by customer."""
        return self.status in ['pending', 'under_review']
    
    def can_be_modified(self):
        """Check if request can be modified."""
        return self.status == 'pending'
    
    def approve(self, approved_limit, officer, notes=None):
        """Approve the request with specified limit."""
        self.status = 'approved'
        self.approved_limit = approved_limit
        self.decision_officer = officer
        self.decision_date = timezone.now()
        if notes:
            self.internal_notes = notes
        self.save()
    
    def reject(self, reason, officer, notes=None):
        """Reject the request with reason."""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.decision_officer = officer
        self.decision_date = timezone.now()
        if notes:
            self.internal_notes = notes
        self.save()
    
    def cancel(self):
        """Cancel the request (customer initiated)."""
        if not self.can_be_cancelled():
            raise ValueError("Request cannot be cancelled in current status")
        self.status = 'cancelled'
        self.save()
    
    def implement(self, old_limit, new_limit):
        """Mark request as implemented in banking system."""
        if self.status != 'approved':
            raise ValueError("Only approved requests can be implemented")
        
        self.status = 'implemented'
        self.implementation_date = timezone.now()
        self.old_system_limit = old_limit
        self.new_system_limit = new_limit
        self.save()
    
    def assign_officer(self, officer):
        """Assign request to bank officer."""
        self.assigned_officer = officer
        if self.status == 'pending':
            self.status = 'under_review'
        self.save()
    
    def clean(self):
        """Validate request data."""
        from django.core.exceptions import ValidationError
        
        # Validate requested limit is greater than current
        if self.requested_limit <= self.current_limit:
            raise ValidationError("Requested limit must be greater than current limit")
        
        # Validate card_detail requirement for card requests
        if self.request_type in ['credit_limit', 'debit_limit'] and not self.card_detail:
            raise ValidationError("Card detail is required for card limit requests")
        
        # Validate netbanking requests don't have card_detail
        if self.request_type == 'netbanking_limit' and self.card_detail:
            raise ValidationError("Card detail should not be provided for netbanking requests")
        
        # Validate approved limit if set
        if self.approved_limit and self.approved_limit < self.current_limit:
            raise ValidationError("Approved limit cannot be less than current limit")
        
        # Validate status transitions
        if self.pk:  # Only for existing records
            old_instance = LimitRequest.objects.get(pk=self.pk)
            if not self._is_valid_status_transition(old_instance.status, self.status):
                raise ValidationError(f"Invalid status transition from {old_instance.status} to {self.status}")
    
    def _is_valid_status_transition(self, old_status, new_status):
        """Check if status transition is valid."""
        valid_transitions = {
            'pending': ['under_review', 'cancelled'],
            'under_review': ['approved', 'rejected', 'cancelled'],
            'approved': ['implemented'],
            'rejected': [],  # Terminal state
            'implemented': [],  # Terminal state
            'cancelled': [],  # Terminal state
        }
        
        return new_status in valid_transitions.get(old_status, [])
    
    def get_status_display_color(self):
        """Get color for status display in UI."""
        color_map = {
            'pending': 'warning',
            'under_review': 'info',
            'approved': 'success',
            'rejected': 'danger',
            'implemented': 'success',
            'cancelled': 'secondary',
        }
        return color_map.get(self.status, 'secondary')
    
    def get_timeline_events(self):
        """Get timeline of events for this request."""
        events = []
        
        events.append({
            'date': self.created_at,
            'event': 'Request Created',
            'description': f'Limit increase request submitted for {self.get_request_type_display()}',
            'status': 'pending'
        })
        
        if self.status != 'pending':
            if self.assigned_officer:
                events.append({
                    'date': self.updated_at,  # This is approximate
                    'event': 'Under Review',
                    'description': f'Request assigned to {self.assigned_officer}',
                    'status': 'under_review'
                })
            
            if self.decision_date:
                if self.status == 'approved':
                    events.append({
                        'date': self.decision_date,
                        'event': 'Approved',
                        'description': f'Request approved for ₹{self.approved_limit:,.2f}',
                        'status': 'approved'
                    })
                elif self.status == 'rejected':
                    events.append({
                        'date': self.decision_date,
                        'event': 'Rejected',
                        'description': self.rejection_reason or 'Request rejected',
                        'status': 'rejected'
                    })
            
            if self.implementation_date:
                events.append({
                    'date': self.implementation_date,
                    'event': 'Implemented',
                    'description': f'Limit updated to ₹{self.new_system_limit:,.2f}',
                    'status': 'implemented'
                })
        
        return sorted(events, key=lambda x: x['date'])


class RequestStatusHistory(models.Model):
    """
    Model to track status change history for requests.
    
    Provides detailed audit trail of all status changes
    with timestamps and responsible parties.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    request = models.ForeignKey(
        LimitRequest,
        on_delete=models.CASCADE,
        related_name='status_history',
        help_text="Related limit request"
    )
    
    old_status = models.CharField(
        max_length=20,
        choices=LimitRequest.STATUS_CHOICES,
        null=True,
        blank=True,
        help_text="Previous status"
    )
    
    new_status = models.CharField(
        max_length=20,
        choices=LimitRequest.STATUS_CHOICES,
        help_text="New status"
    )
    
    changed_by = models.CharField(
        max_length=100,
        help_text="User who made the change"
    )
    
    change_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for status change"
    )
    
    changed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of status change"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of user making change"
    )
    
    class Meta:
        db_table = 'request_status_history'
        verbose_name = 'Request Status History'
        verbose_name_plural = 'Request Status Histories'
        indexes = [
            models.Index(fields=['request', 'changed_at']),
            models.Index(fields=['new_status', 'changed_at']),
        ]
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.request.reference_number}: {self.old_status} → {self.new_status}"