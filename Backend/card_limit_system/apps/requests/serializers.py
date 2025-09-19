"""
Django REST Framework serializers for Request models.

Provides secure request management with proper validation,
workflow controls, and audit trail features.
"""

from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import LimitRequest, RequestStatusHistory
from apps.customers.models import Customer, CardDetail
from apps.customers.serializers import CustomerProfileSerializer, CardDetailSerializer


class LimitRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new limit increase requests.
    
    Handles request creation with proper validation and
    business rule enforcement.
    """
    
    # Card selection (for card-related requests)
    card_detail_id = serializers.UUIDField(write_only=True, required=False)
    
    # Supporting documents
    supporting_documents = serializers.ListField(
        child=serializers.CharField(max_length=255),
        required=False,
        allow_empty=True
    )
    
    # Read-only fields for response
    reference_number = serializers.CharField(read_only=True)
    limit_increase_amount = serializers.SerializerMethodField()
    processing_days = serializers.SerializerMethodField()
    
    class Meta:
        model = LimitRequest
        fields = [
            'request_type', 'card_detail_id', 'current_limit', 'requested_limit',
            'reason', 'income_proof_uploaded', 'supporting_documents',
            'priority', 'reference_number', 'limit_increase_amount',
            'processing_days', 'estimated_processing_days', 'created_at'
        ]
        read_only_fields = [
            'reference_number', 'limit_increase_amount', 'processing_days',
            'created_at'
        ]
        extra_kwargs = {
            'current_limit': {'min_value': Decimal('0.00')},
            'requested_limit': {'min_value': Decimal('0.01')},
            'reason': {'max_length': 1000, 'min_length': 10},
        }
    
    def get_limit_increase_amount(self, obj):
        """Calculate requested increase amount."""
        return obj.limit_increase_amount
    
    def get_processing_days(self, obj):
        """Get current processing days."""
        return obj.processing_time_days
    
    def validate_requested_limit(self, value):
        """Validate requested limit amount."""
        if value <= 0:
            raise serializers.ValidationError("Requested limit must be greater than 0.")
        
        # Maximum limit validation (business rule)
        max_limit = Decimal('10000000.00')  # 1 Crore
        if value > max_limit:
            raise serializers.ValidationError(f"Requested limit cannot exceed ₹{max_limit:,.2f}")
        
        return value
    
    def validate_reason(self, value):
        """Validate request reason."""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Please provide a detailed reason (minimum 10 characters).")
        
        # Sanitize input
        from core.utils import sanitize_input
        return sanitize_input(value)
    
    def validate_supporting_documents(self, value):
        """Validate supporting documents list."""
        if value and len(value) > 10:
            raise serializers.ValidationError("Maximum 10 supporting documents allowed.")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        request_type = attrs.get('request_type')
        card_detail_id = attrs.get('card_detail_id')
        current_limit = attrs.get('current_limit')
        requested_limit = attrs.get('requested_limit')
        
        # Validate card requirement for card requests
        if request_type in ['credit_limit', 'debit_limit']:
            if not card_detail_id:
                raise serializers.ValidationError({
                    'card_detail_id': 'Card selection is required for card limit requests.'
                })
        else:
            if card_detail_id:
                raise serializers.ValidationError({
                    'card_detail_id': 'Card should not be selected for netbanking requests.'
                })
        
        # Validate requested limit is greater than current
        if requested_limit <= current_limit:
            raise serializers.ValidationError({
                'requested_limit': 'Requested limit must be greater than current limit.'
            })
        
        # Validate reasonable increase (business rule)
        increase_amount = requested_limit - current_limit
        max_increase = current_limit * Decimal('5.0')  # Max 5x current limit
        
        if increase_amount > max_increase:
            raise serializers.ValidationError({
                'requested_limit': f'Increase amount cannot exceed 5x current limit (₹{max_increase:,.2f}).'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create limit request with customer association."""
        customer = self.context['customer']
        validated_data['customer'] = customer
        
        # Set card detail if provided
        card_detail_id = validated_data.pop('card_detail_id', None)
        if card_detail_id:
            try:
                card_detail = CardDetail.objects.get(
                    id=card_detail_id,
                    customer=customer,
                    is_active=True
                )
                validated_data['card_detail'] = card_detail
            except CardDetail.DoesNotExist:
                raise serializers.ValidationError({
                    'card_detail_id': 'Invalid card selection.'
                })
        
        # Set audit fields
        request_obj = self.context.get('request')
        if request_obj:
            from core.utils import get_client_ip, get_user_agent
            validated_data['created_by_ip'] = get_client_ip(request_obj)
            validated_data['user_agent'] = get_user_agent(request_obj)
        
        # Check for existing pending requests
        existing_request = LimitRequest.objects.filter(
            customer=customer,
            status__in=['pending', 'under_review'],
            request_type=validated_data['request_type']
        ).first()
        
        if existing_request:
            raise serializers.ValidationError({
                'non_field_errors': [
                    f'You already have a pending {validated_data["request_type"]} request '
                    f'({existing_request.reference_number}). Please wait for it to be processed.'
                ]
            })
        
        return super().create(validated_data)


class LimitRequestListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing limit requests.
    
    Provides essential request information for list views
    with status and progress indicators.
    """
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    card_display = serializers.SerializerMethodField()
    limit_increase_amount = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    processing_days = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = LimitRequest
        fields = [
            'id', 'reference_number', 'customer_name', 'request_type',
            'card_display', 'current_limit', 'requested_limit',
            'limit_increase_amount', 'status', 'status_display',
            'priority', 'priority_display', 'processing_days',
            'is_overdue', 'created_at', 'decision_date'
        ]
        read_only_fields = '__all__'
    
    def get_card_display(self, obj):
        """Return card display information."""
        if obj.card_detail:
            return obj.card_detail.get_masked_card_number()
        return None
    
    def get_limit_increase_amount(self, obj):
        """Calculate requested increase amount."""
        return obj.limit_increase_amount
    
    def get_processing_days(self, obj):
        """Get current processing days."""
        return obj.processing_time_days
    
    def get_is_overdue(self, obj):
        """Check if request is overdue."""
        return obj.is_overdue


class LimitRequestDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed limit request view.
    
    Provides comprehensive request information including
    status history and timeline events.
    """
    
    customer = CustomerProfileSerializer(read_only=True)
    card_detail = CardDetailSerializer(read_only=True)
    
    # Calculated fields
    limit_increase_amount = serializers.SerializerMethodField()
    approved_increase_amount = serializers.SerializerMethodField()
    processing_days = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()
    can_be_modified = serializers.SerializerMethodField()
    
    # Status displays
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    
    # Timeline
    timeline_events = serializers.SerializerMethodField()
    
    class Meta:
        model = LimitRequest
        fields = [
            'id', 'reference_number', 'customer', 'card_detail',
            'request_type', 'request_type_display', 'current_limit',
            'requested_limit', 'limit_increase_amount', 'reason',
            'income_proof_uploaded', 'supporting_documents',
            'status', 'status_display', 'priority', 'priority_display',
            'assigned_officer', 'approved_limit', 'approved_increase_amount',
            'rejection_reason', 'decision_date', 'decision_officer',
            'implementation_date', 'old_system_limit', 'new_system_limit',
            'estimated_processing_days', 'actual_processing_days',
            'processing_days', 'is_overdue', 'can_be_cancelled',
            'can_be_modified', 'timeline_events', 'created_at', 'updated_at'
        ]
        read_only_fields = '__all__'
    
    def get_limit_increase_amount(self, obj):
        """Calculate requested increase amount."""
        return obj.limit_increase_amount
    
    def get_approved_increase_amount(self, obj):
        """Calculate approved increase amount."""
        return obj.approved_increase_amount
    
    def get_processing_days(self, obj):
        """Get current processing days."""
        return obj.processing_time_days
    
    def get_is_overdue(self, obj):
        """Check if request is overdue."""
        return obj.is_overdue
    
    def get_can_be_cancelled(self, obj):
        """Check if request can be cancelled."""
        return obj.can_be_cancelled()
    
    def get_can_be_modified(self, obj):
        """Check if request can be modified."""
        return obj.can_be_modified()
    
    def get_timeline_events(self, obj):
        """Get timeline events for request."""
        return obj.get_timeline_events()


class LimitRequestUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating limit requests (customer side).
    
    Allows limited updates for pending requests with
    proper validation and business rules.
    """
    
    class Meta:
        model = LimitRequest
        fields = ['requested_limit', 'reason', 'supporting_documents']
        extra_kwargs = {
            'requested_limit': {'min_value': Decimal('0.01')},
            'reason': {'max_length': 1000, 'min_length': 10},
        }
    
    def validate_requested_limit(self, value):
        """Validate requested limit update."""
        instance = self.instance
        
        if value <= instance.current_limit:
            raise serializers.ValidationError(
                "Requested limit must be greater than current limit."
            )
        
        # Validate reasonable increase
        increase_amount = value - instance.current_limit
        max_increase = instance.current_limit * Decimal('5.0')
        
        if increase_amount > max_increase:
            raise serializers.ValidationError(
                f'Increase amount cannot exceed 5x current limit (₹{max_increase:,.2f}).'
            )
        
        return value
    
    def validate(self, attrs):
        """Validate update permissions."""
        instance = self.instance
        
        if not instance.can_be_modified():
            raise serializers.ValidationError(
                'This request cannot be modified in its current status.'
            )
        
        return attrs


class LimitRequestStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating request status (admin side).
    
    Handles status transitions with proper validation
    and business rule enforcement.
    """
    
    action = serializers.ChoiceField(choices=[
        ('assign', 'Assign to Officer'),
        ('approve', 'Approve Request'),
        ('reject', 'Reject Request'),
        ('implement', 'Mark as Implemented'),
        ('cancel', 'Cancel Request'),
    ])
    
    # Fields for approval
    approved_limit = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, min_value=Decimal('0.01')
    )
    
    # Fields for rejection
    rejection_reason = serializers.CharField(max_length=500, required=False)
    
    # Fields for assignment
    assigned_officer = serializers.CharField(max_length=100, required=False)
    
    # Fields for implementation
    old_system_limit = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, min_value=Decimal('0.00')
    )
    new_system_limit = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, min_value=Decimal('0.01')
    )
    
    # Common fields
    internal_notes = serializers.CharField(max_length=1000, required=False)
    
    def validate(self, attrs):
        """Validate action-specific requirements."""
        action = attrs.get('action')
        
        if action == 'approve':
            if not attrs.get('approved_limit'):
                raise serializers.ValidationError({
                    'approved_limit': 'Approved limit is required for approval.'
                })
        
        elif action == 'reject':
            if not attrs.get('rejection_reason'):
                raise serializers.ValidationError({
                    'rejection_reason': 'Rejection reason is required for rejection.'
                })
        
        elif action == 'assign':
            if not attrs.get('assigned_officer'):
                raise serializers.ValidationError({
                    'assigned_officer': 'Officer assignment is required.'
                })
        
        elif action == 'implement':
            if not attrs.get('new_system_limit'):
                raise serializers.ValidationError({
                    'new_system_limit': 'New system limit is required for implementation.'
                })
        
        return attrs


class RequestStatusHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for request status history.
    
    Provides audit trail information for status changes
    with proper security and compliance features.
    """
    
    request_reference = serializers.CharField(source='request.reference_number', read_only=True)
    old_status_display = serializers.SerializerMethodField()
    new_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = RequestStatusHistory
        fields = [
            'id', 'request_reference', 'old_status', 'old_status_display',
            'new_status', 'new_status_display', 'changed_by',
            'change_reason', 'changed_at', 'ip_address'
        ]
        read_only_fields = '__all__'
    
    def get_old_status_display(self, obj):
        """Get display name for old status."""
        if obj.old_status:
            return dict(LimitRequest.STATUS_CHOICES).get(obj.old_status, obj.old_status)
        return None
    
    def get_new_status_display(self, obj):
        """Get display name for new status."""
        return dict(LimitRequest.STATUS_CHOICES).get(obj.new_status, obj.new_status)


class RequestStatsSerializer(serializers.Serializer):
    """
    Serializer for request statistics and analytics.
    
    Provides summary statistics for dashboard views
    and reporting purposes.
    """
    
    total_requests = serializers.IntegerField(read_only=True)
    pending_requests = serializers.IntegerField(read_only=True)
    under_review = serializers.IntegerField(read_only=True)
    approved_requests = serializers.IntegerField(read_only=True)
    rejected_requests = serializers.IntegerField(read_only=True)
    implemented_requests = serializers.IntegerField(read_only=True)
    cancelled_requests = serializers.IntegerField(read_only=True)
    
    # Processing time stats
    avg_processing_days = serializers.FloatField(read_only=True)
    overdue_requests = serializers.IntegerField(read_only=True)
    
    # Amount stats
    total_requested_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_approved_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    # Time period
    period_start = serializers.DateTimeField(read_only=True)
    period_end = serializers.DateTimeField(read_only=True)


class RequestCancellationSerializer(serializers.Serializer):
    """
    Serializer for request cancellation by customer.
    
    Handles customer-initiated request cancellations with
    proper validation and confirmation.
    """
    
    cancellation_reason = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Please provide reason for cancellation"
    )
    
    confirm_cancellation = serializers.BooleanField(
        required=True,
        help_text="Confirm that you want to cancel this request"
    )
    
    def validate_confirm_cancellation(self, value):
        """Validate cancellation confirmation."""
        if not value:
            raise serializers.ValidationError("You must confirm the cancellation.")
        return value
    
    def validate_cancellation_reason(self, value):
        """Validate cancellation reason."""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Please provide a detailed reason for cancellation (minimum 5 characters)."
            )
        
        # Sanitize input
        from core.utils import sanitize_input
        return sanitize_input(value)
    
    def validate(self, attrs):
        """Validate cancellation request."""
        request_obj = self.context.get('request_obj')
        
        if not request_obj.can_be_cancelled():
            raise serializers.ValidationError(
                'This request cannot be cancelled in its current status.'
            )
        
        return attrs