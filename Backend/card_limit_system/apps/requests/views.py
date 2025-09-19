"""
Django REST Framework views for Limit Request management.

Provides comprehensive limit request processing with workflow
management, approval/rejection handling, and audit tracking.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import logging
from datetime import timedelta

from .models import LimitRequest, LimitRequestDocument, LimitRequestHistory
from .serializers import (
    LimitRequestCreateSerializer,
    LimitRequestListSerializer,
    LimitRequestDetailSerializer,
    LimitRequestUpdateSerializer,
    LimitRequestApprovalSerializer,
    LimitRequestDocumentSerializer,
    LimitRequestStatsSerializer
)
from apps.customers.models import Customer
from core.permissions import IsOwnerOrAdmin, IsCustomerService, IsLimitApprover
from core.mixins import SecurityMixin, AuditMixin
from core.pagination import StandardResultsSetPagination
from core.throttling import LimitRequestThrottle
from core.utils import generate_reference_number
from apps.notifications.services import NotificationService
from apps.otp.services import OTPService

logger = logging.getLogger(__name__)


class LimitRequestViewSet(SecurityMixin, AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet for limit request management.
    
    Provides comprehensive limit request processing with proper
    workflow management, approval workflows, and audit tracking.
    """
    
    queryset = LimitRequest.objects.select_related('customer').prefetch_related(
        'documents', 'history', 'approvals'
    )
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'status', 'request_type', 'customer__customer_segment',
        'priority', 'requires_manual_review'
    ]
    search_fields = ['reference_number', 'customer__customer_id', 'customer__full_name']
    ordering_fields = ['created_at', 'updated_at', 'requested_amount', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return LimitRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LimitRequestUpdateSerializer
        elif self.action == 'retrieve':
            return LimitRequestDetailSerializer
        elif self.action == 'list':
            return LimitRequestListSerializer
        elif self.action in ['approve', 'reject']:
            return LimitRequestApprovalSerializer
        else:
            return LimitRequestDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name__in=['customer_service', 'limit_approver']).exists():
            # Staff and authorized personnel can see all requests
            return self.queryset
        else:
            # Regular users can only see their own requests
            try:
                customer = Customer.objects.get(firebase_uid=user.username)
                return self.queryset.filter(customer=customer)
            except Customer.DoesNotExist:
                return LimitRequest.objects.none()
    
    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, LimitRequestThrottle]
        elif self.action in ['approve', 'reject', 'assign_reviewer']:
            permission_classes = [permissions.IsAuthenticated, IsLimitApprover]
        elif self.action in ['admin_update', 'bulk_update']:
            permission_classes = [permissions.IsAuthenticated, IsCustomerService]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create new limit request with validation and workflow initiation."""
        # Get customer from Firebase UID
        try:
            customer = Customer.objects.get(firebase_uid=request.user.username)
        except Customer.DoesNotExist:
            return Response(
                {
                    'status': 'error',
                    'message': 'Customer profile not found',
                    'errors': {'customer': ['Please complete your profile first']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if customer has pending requests
        pending_requests = LimitRequest.objects.filter(
            customer=customer,
            status__in=['PENDING', 'UNDER_REVIEW', 'APPROVED_PENDING_IMPLEMENTATION']
        ).count()
        
        if pending_requests >= 3:  # Maximum pending requests limit
            return Response(
                {
                    'status': 'error',
                    'message': 'Maximum pending requests limit reached',
                    'errors': {'limit': ['You can have maximum 3 pending requests']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare data with customer
        data = request.data.copy()
        data['customer'] = customer.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Create limit request
            limit_request = serializer.save(customer=customer)
            
            # Log request creation
            self.log_audit_event(
                action='limit_request_created',
                resource_type='LimitRequest',
                resource_id=limit_request.id,
                user=request.user,
                details={
                    'reference_number': limit_request.reference_number,
                    'request_type': limit_request.request_type,
                    'requested_amount': str(limit_request.requested_amount),
                    'current_limit': str(limit_request.current_limit)
                }
            )
            
            # Send confirmation notification
            NotificationService.send_request_confirmation_notification(limit_request)
            
            # Initialize workflow
            limit_request.initialize_workflow()
            
            # Cache request data
            cache.set(f'limit_request_{limit_request.reference_number}', limit_request, 3600)
            
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    'status': 'success',
                    'message': 'Limit request submitted successfully',
                    'data': LimitRequestDetailSerializer(limit_request).data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
            
        except Exception as e:
            logger.error(f"Limit request creation failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Request submission failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve limit request with cached data and access control."""
        instance = self.get_object()
        
        # Check if user can access this request
        if not request.user.is_staff and instance.customer.firebase_uid != request.user.username:
            raise PermissionDenied("You can only access your own requests")
        
        # Check cache first
        cache_key = f'limit_request_detail_{instance.reference_number}'
        cached_data = cache.get(cache_key)
        
        if cached_data and not request.user.is_staff:
            # Use cache for regular users, but not for staff (they need fresh data)
            return Response({
                'status': 'success',
                'data': cached_data,
                'cached': True
            })
        
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Cache the response
        cache.set(cache_key, data, 1800)  # 30 minutes
        
        # Log request view
        self.log_audit_event(
            action='limit_request_viewed',
            resource_type='LimitRequest',
            resource_id=instance.id,
            user=request.user
        )
        
        return Response({
            'status': 'success',
            'data': data,
            'cached': False
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsLimitApprover])
    def approve(self, request, pk=None):
        """Approve limit request with proper validation and notifications."""
        limit_request = self.get_object()
        
        if limit_request.status not in ['PENDING', 'UNDER_REVIEW']:
            return Response(
                {
                    'status': 'error',
                    'message': 'Request cannot be approved in current status',
                    'errors': {'status': [f'Cannot approve request with status: {limit_request.status}']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = LimitRequestApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # Process approval
                approved_amount = serializer.validated_data.get('approved_amount')
                approval_comments = serializer.validated_data.get('comments', '')
                requires_additional_verification = serializer.validated_data.get(
                    'requires_additional_verification', False
                )
                
                # Update request
                limit_request.status = 'APPROVED_PENDING_IMPLEMENTATION'
                limit_request.approved_amount = approved_amount
                limit_request.approved_by = request.user.username
                limit_request.approved_at = timezone.now()
                limit_request.approval_comments = approval_comments
                limit_request.save()
                
                # Create approval record
                from .models import LimitRequestApproval
                approval = LimitRequestApproval.objects.create(
                    request=limit_request,
                    approver_user_id=request.user.username,
                    approved_amount=approved_amount,
                    comments=approval_comments,
                    requires_additional_verification=requires_additional_verification
                )
                
                # Add history entry
                limit_request.add_history_entry(
                    action='APPROVED',
                    user=request.user.username,
                    comments=approval_comments,
                    metadata={
                        'approved_amount': str(approved_amount),
                        'original_requested': str(limit_request.requested_amount),
                        'requires_additional_verification': requires_additional_verification
                    }
                )
                
                # Log approval
                self.log_audit_event(
                    action='limit_request_approved',
                    resource_type='LimitRequest',
                    resource_id=limit_request.id,
                    user=request.user,
                    details={
                        'reference_number': limit_request.reference_number,
                        'approved_amount': str(approved_amount),
                        'requested_amount': str(limit_request.requested_amount),
                        'approver': request.user.username
                    }
                )
                
                # Send approval notification
                NotificationService.send_request_approved_notification(
                    limit_request, approved_amount
                )
                
                # If additional verification required, send OTP
                if requires_additional_verification:
                    OTPService.generate_limit_approval_otp(limit_request)
                
                # Clear cache
                cache.delete_many([
                    f'limit_request_{limit_request.reference_number}',
                    f'limit_request_detail_{limit_request.reference_number}'
                ])
                
                return Response({
                    'status': 'success',
                    'message': 'Request approved successfully',
                    'data': {
                        'reference_number': limit_request.reference_number,
                        'approved_amount': approved_amount,
                        'status': limit_request.status,
                        'requires_additional_verification': requires_additional_verification
                    }
                })
                
        except Exception as e:
            logger.error(f"Request approval failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Approval failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsLimitApprover])
    def reject(self, request, pk=None):
        """Reject limit request with proper validation and notifications."""
        limit_request = self.get_object()
        
        if limit_request.status not in ['PENDING', 'UNDER_REVIEW']:
            return Response(
                {
                    'status': 'error',
                    'message': 'Request cannot be rejected in current status',
                    'errors': {'status': [f'Cannot reject request with status: {limit_request.status}']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason')
        rejection_comments = request.data.get('comments', '')
        
        if not rejection_reason:
            return Response(
                {
                    'status': 'error',
                    'message': 'Rejection reason is required',
                    'errors': {'rejection_reason': ['This field is required']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Update request
                limit_request.status = 'REJECTED'
                limit_request.rejection_reason = rejection_reason
                limit_request.rejection_comments = rejection_comments
                limit_request.rejected_by = request.user.username
                limit_request.rejected_at = timezone.now()
                limit_request.save()
                
                # Add history entry
                limit_request.add_history_entry(
                    action='REJECTED',
                    user=request.user.username,
                    comments=f"{rejection_reason}. {rejection_comments}".strip(),
                    metadata={
                        'rejection_reason': rejection_reason,
                        'rejector': request.user.username
                    }
                )
                
                # Log rejection
                self.log_audit_event(
                    action='limit_request_rejected',
                    resource_type='LimitRequest',
                    resource_id=limit_request.id,
                    user=request.user,
                    details={
                        'reference_number': limit_request.reference_number,
                        'rejection_reason': rejection_reason,
                        'rejector': request.user.username
                    }
                )
                
                # Send rejection notification
                NotificationService.send_request_rejected_notification(
                    limit_request, rejection_reason
                )
                
                # Clear cache
                cache.delete_many([
                    f'limit_request_{limit_request.reference_number}',
                    f'limit_request_detail_{limit_request.reference_number}'
                ])
                
                return Response({
                    'status': 'success',
                    'message': 'Request rejected successfully',
                    'data': {
                        'reference_number': limit_request.reference_number,
                        'status': limit_request.status,
                        'rejection_reason': rejection_reason
                    }
                })
                
        except Exception as e:
            logger.error(f"Request rejection failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Rejection failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel limit request (customer action)."""
        limit_request = self.get_object()
        
        # Check permissions
        if limit_request.customer.firebase_uid != request.user.username:
            raise PermissionDenied("You can only cancel your own requests")
        
        if limit_request.status not in ['PENDING', 'UNDER_REVIEW']:
            return Response(
                {
                    'status': 'error',
                    'message': 'Request cannot be cancelled in current status',
                    'errors': {'status': [f'Cannot cancel request with status: {limit_request.status}']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cancellation_reason = request.data.get('reason', 'Customer cancellation')
        
        try:
            with transaction.atomic():
                # Update request
                limit_request.status = 'CANCELLED'
                limit_request.cancellation_reason = cancellation_reason
                limit_request.cancelled_at = timezone.now()
                limit_request.save()
                
                # Add history entry
                limit_request.add_history_entry(
                    action='CANCELLED',
                    user=request.user.username,
                    comments=cancellation_reason,
                    metadata={'cancelled_by': 'customer'}
                )
                
                # Log cancellation
                self.log_audit_event(
                    action='limit_request_cancelled',
                    resource_type='LimitRequest',
                    resource_id=limit_request.id,
                    user=request.user,
                    details={
                        'reference_number': limit_request.reference_number,
                        'cancellation_reason': cancellation_reason
                    }
                )
                
                # Send cancellation notification (internal)
                NotificationService.send_request_cancelled_notification(limit_request)
                
                # Clear cache
                cache.delete_many([
                    f'limit_request_{limit_request.reference_number}',
                    f'limit_request_detail_{limit_request.reference_number}'
                ])
                
                return Response({
                    'status': 'success',
                    'message': 'Request cancelled successfully',
                    'data': {
                        'reference_number': limit_request.reference_number,
                        'status': limit_request.status
                    }
                })
                
        except Exception as e:
            logger.error(f"Request cancellation failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Cancellation failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get request history and audit trail."""
        limit_request = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and limit_request.customer.firebase_uid != request.user.username:
            raise PermissionDenied("You can only view history of your own requests")
        
        history_entries = limit_request.history.all().order_by('-created_at')
        
        history_data = []
        for entry in history_entries:
            history_data.append({
                'id': entry.id,
                'action': entry.action,
                'user': entry.user,
                'comments': entry.comments,
                'metadata': entry.metadata,
                'created_at': entry.created_at
            })
        
        return Response({
            'status': 'success',
            'data': history_data,
            'count': len(history_data)
        })
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Upload supporting document for limit request."""
        limit_request = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and limit_request.customer.firebase_uid != request.user.username:
            raise PermissionDenied("You can only upload documents for your own requests")
        
        if limit_request.status not in ['PENDING', 'UNDER_REVIEW', 'ADDITIONAL_INFO_REQUIRED']:
            return Response(
                {
                    'status': 'error',
                    'message': 'Documents cannot be uploaded for this request status',
                    'errors': {'status': ['Document upload not allowed for current status']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document_data = request.data.copy()
        document_data['request'] = limit_request.id
        
        serializer = LimitRequestDocumentSerializer(data=document_data)
        
        if serializer.is_valid():
            try:
                document = serializer.save()
                
                # Log document upload
                self.log_audit_event(
                    action='document_uploaded',
                    resource_type='LimitRequestDocument',
                    resource_id=document.id,
                    user=request.user,
                    details={
                        'request_reference': limit_request.reference_number,
                        'document_type': document.document_type,
                        'file_name': document.file_name
                    }
                )
                
                # Add history entry
                limit_request.add_history_entry(
                    action='DOCUMENT_UPLOADED',
                    user=request.user.username,
                    comments=f"Uploaded {document.document_type}: {document.file_name}",
                    metadata={
                        'document_id': str(document.id),
                        'document_type': document.document_type
                    }
                )
                
                # Send notification if required
                if limit_request.status == 'ADDITIONAL_INFO_REQUIRED':
                    NotificationService.send_document_uploaded_notification(
                        limit_request, document
                    )
                
                return Response({
                    'status': 'success',
                    'message': 'Document uploaded successfully',
                    'data': serializer.data
                })
                
            except Exception as e:
                logger.error(f"Document upload failed: {str(e)}")
                return Response(
                    {
                        'status': 'error',
                        'message': 'Document upload failed',
                        'errors': {'non_field_errors': [str(e)]}
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {
                    'status': 'error',
                    'message': 'Invalid document data',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsCustomerService])
    def statistics(self, request):
        """Get limit request statistics (Admin only)."""
        try:
            # Get query parameters
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Build base queryset
            queryset = LimitRequest.objects.all()
            
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            
            # Calculate statistics
            stats = {
                'total_requests': queryset.count(),
                'pending_requests': queryset.filter(status='PENDING').count(),
                'under_review': queryset.filter(status='UNDER_REVIEW').count(),
                'approved_requests': queryset.filter(status='APPROVED').count(),
                'rejected_requests': queryset.filter(status='REJECTED').count(),
                'by_type': queryset.values('request_type').annotate(
                    count=Count('id')
                ),
                'by_status': queryset.values('status').annotate(
                    count=Count('id')
                ),
                'avg_processing_time': queryset.filter(
                    approved_at__isnull=False
                ).aggregate(
                    avg_time=Avg('approved_at') - Avg('created_at')
                ),
                'total_approved_amount': queryset.filter(
                    status='APPROVED'
                ).aggregate(
                    total=Sum('approved_amount')
                )['total'] or 0,
                'requests_by_month': queryset.extra(
                    select={'month': "to_char(created_at, 'YYYY-MM')"}
                ).values('month').annotate(count=Count('id')).order_by('month')
            }
            
            return Response({
                'status': 'success',
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Statistics retrieval failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve statistics',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )