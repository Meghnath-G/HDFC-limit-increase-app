"""
Firebase-compatible Django REST Framework views for Limit Request management.

Replaces Oracle-based Django ORM with Firebase Firestore operations
while maintaining the same API interface and functionality.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid

# Firebase imports
from core.firebase_config import FirebaseService
from core.firebase_schema import LimitRequestSchema, validate_document

# Original serializers (will be updated for Firebase)
from .serializers import (
    LimitRequestCreateSerializer,
    LimitRequestListSerializer,
    LimitRequestDetailSerializer,
    LimitRequestUpdateSerializer,
    LimitRequestApprovalSerializer,
    LimitRequestDocumentSerializer,
    LimitRequestStatsSerializer
)

# Core utilities
from core.permissions import IsOwnerOrAdmin, IsCustomerService, IsLimitApprover
from core.mixins import SecurityMixin, AuditMixin
from core.pagination import StandardResultsSetPagination
from core.throttling import LimitRequestThrottle
from core.utils import generate_reference_number
from apps.notifications.services import NotificationService
from apps.otp.services import OTPService

logger = logging.getLogger(__name__)


class FirebaseLimitRequestViewSet(SecurityMixin, AuditMixin, viewsets.ViewSet):
    """
    Firebase-based ViewSet for limit request management.
    
    Replaces Django ORM operations with Firebase Firestore while
    maintaining the same API interface and functionality.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.firebase_service = FirebaseService()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        action_serializers = {
            'create': LimitRequestCreateSerializer,
            'update': LimitRequestUpdateSerializer,
            'partial_update': LimitRequestUpdateSerializer,
            'retrieve': LimitRequestDetailSerializer,
            'list': LimitRequestListSerializer,
            'approve': LimitRequestApprovalSerializer,
            'reject': LimitRequestApprovalSerializer,
        }
        return action_serializers.get(self.action, LimitRequestDetailSerializer)
    
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
    
    def get_customer_by_firebase_uid(self, firebase_uid: str) -> Optional[Dict[str, Any]]:
        """Get customer document by Firebase UID."""
        try:
            customers = self.firebase_service.query_collection(
                'customers',
                field_path='firebase_uid',
                op_string='==',
                value=firebase_uid
            )
            return customers[0] if customers else None
        except Exception as e:
            logger.error(f"Error fetching customer by Firebase UID {firebase_uid}: {str(e)}")
            return None
    
    def get_customer_requests(self, customer_ref: str) -> List[Dict[str, Any]]:
        """Get all requests for a specific customer."""
        try:
            return self.firebase_service.query_collection(
                'limit_requests',
                field_path='customer_ref',
                op_string='==',
                value=customer_ref
            )
        except Exception as e:
            logger.error(f"Error fetching requests for customer {customer_ref}: {str(e)}")
            return []
    
    def list(self, request):
        """List limit requests with filtering and pagination."""
        try:
            user = request.user
            
            if user.is_staff or user.groups.filter(name__in=['customer_service', 'limit_approver']).exists():
                # Staff can see all requests
                limit_requests = self.firebase_service.get_collection('limit_requests')
            else:
                # Regular users can only see their own requests
                customer = self.get_customer_by_firebase_uid(user.username)
                if not customer:
                    return Response({
                        'status': 'success',
                        'count': 0,
                        'results': [],
                        'message': 'Customer profile not found'
                    })
                
                customer_ref = f"customers/{customer.get('id')}"
                limit_requests = self.get_customer_requests(customer_ref)
            
            # Apply filters
            status_filter = request.query_params.get('status')
            if status_filter:
                limit_requests = [
                    req for req in limit_requests
                    if req.get('status') == status_filter
                ]
            
            request_type_filter = request.query_params.get('request_type')
            if request_type_filter:
                limit_requests = [
                    req for req in limit_requests
                    if req.get('request_type') == request_type_filter
                ]
            
            # Apply search
            search_query = request.query_params.get('search', '')
            if search_query:
                limit_requests = [
                    req for req in limit_requests
                    if (search_query.lower() in req.get('reference_number', '').lower() or
                        search_query.lower() in req.get('reason', '').lower())
                ]
            
            # Sort by created_at (newest first)
            limit_requests.sort(
                key=lambda x: x.get('created_at', datetime.min),
                reverse=True
            )
            
            # Apply pagination
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            paginated_requests = limit_requests[start_index:end_index]
            
            return Response({
                'status': 'success',
                'count': len(limit_requests),
                'results': paginated_requests,
                'page': page,
                'page_size': page_size
            })
            
        except Exception as e:
            logger.error(f"Error listing limit requests: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve limit requests',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Retrieve limit request with audit logging."""
        try:
            # Check cache first
            cache_key = f'firebase_limit_request_{pk}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return Response({
                    'status': 'success',
                    'data': cached_data,
                    'cached': True
                })
            
            # Get request from Firebase
            limit_request = self.firebase_service.get_document('limit_requests', pk)
            
            if not limit_request:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Limit request not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check permissions - users can only see their own requests
            user = request.user
            if not (user.is_staff or user.groups.filter(name__in=['customer_service', 'limit_approver']).exists()):
                customer = self.get_customer_by_firebase_uid(user.username)
                if not customer:
                    return Response(
                        {'status': 'error', 'message': 'Access denied'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                customer_ref = f"customers/{customer.get('id')}"
                if limit_request.get('customer_ref') != customer_ref:
                    return Response(
                        {'status': 'error', 'message': 'Access denied'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Cache the response
            cache.set(cache_key, limit_request, 1800)  # 30 minutes
            
            # Log request view
            self.log_audit_event(
                action='limit_request_view',
                resource_type='LimitRequest',
                resource_id=pk,
                user=request.user
            )
            
            return Response({
                'status': 'success',
                'data': limit_request,
                'cached': False
            })
            
        except Exception as e:
            logger.error(f"Error retrieving limit request {pk}: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve limit request',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """Create new limit request with validation and workflow initiation."""
        try:
            # Get customer from Firebase UID
            customer = self.get_customer_by_firebase_uid(request.user.username)
            if not customer:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Customer profile not found',
                        'errors': {'customer': ['Please complete your profile first']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if customer has pending requests
            customer_ref = f"customers/{customer.get('id')}"
            pending_requests = self.firebase_service.query_collection(
                'limit_requests',
                field_path='customer_ref',
                op_string='==',
                value=customer_ref
            )
            
            # Filter for pending statuses
            pending_count = len([
                req for req in pending_requests
                if req.get('status') in ['PENDING', 'UNDER_REVIEW', 'APPROVED_PENDING_IMPLEMENTATION']
            ])
            
            if pending_count >= 3:  # Maximum pending requests limit
                return Response(
                    {
                        'status': 'error',
                        'message': 'Maximum pending requests limit reached',
                        'errors': {'limit': ['You can have maximum 3 pending requests']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate input data
            serializer = self.get_serializer_class()(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Prepare limit request data
            request_data = {
                'customer_ref': customer_ref,
                'reference_number': generate_reference_number(),
                'request_type': request.data.get('request_type', 'limit_increase'),
                'current_limit': float(request.data.get('current_limit', 0)),
                'requested_limit': float(request.data.get('requested_limit', 0)),
                'reason': request.data.get('reason', ''),
                'income_proof': request.data.get('income_proof'),
                'annual_income': float(request.data.get('annual_income', 0)),
                'employment_type': request.data.get('employment_type', 'salaried'),
                'status': 'PENDING',
                'priority': 'medium',
                'requires_manual_review': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'submitted_by': request.user.username,
                'workflow_stage': 'initial_review'
            }
            
            # Validate against Firebase schema
            is_valid, errors = validate_document('limit_requests', request_data)
            if not is_valid:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid request data',
                        'errors': errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create limit request in Firebase
            doc_id = self.firebase_service.create_document('limit_requests', request_data)
            
            # Log request creation
            self.log_audit_event(
                action='limit_request_creation',
                resource_type='LimitRequest',
                resource_id=doc_id,
                user=request.user,
                details={
                    'reference_number': request_data['reference_number'],
                    'requested_amount': request_data['requested_limit'],
                    'customer_ref': customer_ref
                }
            )
            
            # Send confirmation notification
            try:
                NotificationService.send_limit_request_confirmation({
                    'id': doc_id,
                    'customer': customer,
                    'reference_number': request_data['reference_number'],
                    'requested_limit': request_data['requested_limit']
                })
            except Exception as e:
                logger.warning(f"Failed to send confirmation notification: {str(e)}")
            
            # Return success response
            response_data = request_data.copy()
            response_data['id'] = doc_id
            
            return Response(
                {
                    'status': 'success',
                    'message': 'Limit request submitted successfully',
                    'data': response_data
                },
                status=status.HTTP_201_CREATED
            )
            
        except ValidationError as e:
            return Response(
                {
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
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
    
    def update(self, request, pk=None):
        """Update limit request (admin only for most fields)."""
        try:
            # Get existing request
            limit_request = self.firebase_service.get_document('limit_requests', pk)
            
            if not limit_request:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Limit request not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if request can be updated
            if limit_request.get('status') in ['APPROVED', 'REJECTED', 'CANCELLED']:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Cannot update request in current status'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate input data
            serializer = self.get_serializer_class()(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            # Update request data
            updated_data = limit_request.copy()
            
            # Only allow certain fields to be updated
            updatable_fields = ['reason', 'annual_income', 'employment_type', 'income_proof']
            for field in updatable_fields:
                if field in request.data:
                    updated_data[field] = request.data[field]
            
            updated_data['updated_at'] = datetime.now()
            
            # Validate against Firebase schema
            is_valid, errors = validate_document('limit_requests', updated_data)
            if not is_valid:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid request data',
                        'errors': errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update in Firebase
            self.firebase_service.update_document('limit_requests', pk, updated_data)
            
            # Clear cache
            cache.delete(f'firebase_limit_request_{pk}')
            
            # Log update event
            self.log_audit_event(
                action='limit_request_update',
                resource_type='LimitRequest',
                resource_id=pk,
                user=request.user,
                details={'fields_updated': list(request.data.keys())}
            )
            
            return Response({
                'status': 'success',
                'message': 'Limit request updated successfully',
                'data': updated_data
            })
            
        except ValidationError as e:
            return Response(
                {
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Limit request update failed for {pk}: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Update failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve limit request (admin only)."""
        try:
            # Get existing request
            limit_request = self.firebase_service.get_document('limit_requests', pk)
            
            if not limit_request:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Limit request not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if request can be approved
            if limit_request.get('status') not in ['PENDING', 'UNDER_REVIEW']:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Request cannot be approved in current status'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update request status
            updated_data = limit_request.copy()
            updated_data.update({
                'status': 'APPROVED',
                'approved_at': datetime.now(),
                'approved_by': request.user.username,
                'approval_comments': request.data.get('comments', ''),
                'approved_limit': request.data.get('approved_limit', limit_request.get('requested_limit')),
                'updated_at': datetime.now(),
                'workflow_stage': 'approved'
            })
            
            # Update in Firebase
            self.firebase_service.update_document('limit_requests', pk, updated_data)
            
            # Clear cache
            cache.delete(f'firebase_limit_request_{pk}')
            
            # Log approval event
            self.log_audit_event(
                action='limit_request_approval',
                resource_type='LimitRequest',
                resource_id=pk,
                user=request.user,
                details={
                    'approved_limit': updated_data['approved_limit'],
                    'comments': updated_data['approval_comments']
                }
            )
            
            # Send approval notification
            try:
                customer_id = limit_request.get('customer_ref', '').split('/')[-1]
                customer = self.firebase_service.get_document('customers', customer_id)
                
                NotificationService.send_limit_request_approval({
                    'customer': customer,
                    'request': updated_data,
                    'approved_limit': updated_data['approved_limit']
                })
            except Exception as e:
                logger.warning(f"Failed to send approval notification: {str(e)}")
            
            return Response({
                'status': 'success',
                'message': 'Limit request approved successfully',
                'data': updated_data
            })
            
        except Exception as e:
            logger.error(f"Limit request approval failed for {pk}: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Approval failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject limit request (admin only)."""
        try:
            # Get existing request
            limit_request = self.firebase_service.get_document('limit_requests', pk)
            
            if not limit_request:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Limit request not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if request can be rejected
            if limit_request.get('status') not in ['PENDING', 'UNDER_REVIEW']:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Request cannot be rejected in current status'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate rejection reason
            rejection_reason = request.data.get('rejection_reason')
            if not rejection_reason:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Rejection reason is required'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update request status
            updated_data = limit_request.copy()
            updated_data.update({
                'status': 'REJECTED',
                'rejected_at': datetime.now(),
                'rejected_by': request.user.username,
                'rejection_reason': rejection_reason,
                'rejection_comments': request.data.get('comments', ''),
                'updated_at': datetime.now(),
                'workflow_stage': 'rejected'
            })
            
            # Update in Firebase
            self.firebase_service.update_document('limit_requests', pk, updated_data)
            
            # Clear cache
            cache.delete(f'firebase_limit_request_{pk}')
            
            # Log rejection event
            self.log_audit_event(
                action='limit_request_rejection',
                resource_type='LimitRequest',
                resource_id=pk,
                user=request.user,
                details={
                    'rejection_reason': rejection_reason,
                    'comments': updated_data['rejection_comments']
                }
            )
            
            # Send rejection notification
            try:
                customer_id = limit_request.get('customer_ref', '').split('/')[-1]
                customer = self.firebase_service.get_document('customers', customer_id)
                
                NotificationService.send_limit_request_rejection({
                    'customer': customer,
                    'request': updated_data,
                    'rejection_reason': rejection_reason
                })
            except Exception as e:
                logger.warning(f"Failed to send rejection notification: {str(e)}")
            
            return Response({
                'status': 'success',
                'message': 'Limit request rejected successfully',
                'data': updated_data
            })
            
        except Exception as e:
            logger.error(f"Limit request rejection failed for {pk}: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Rejection failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get limit request statistics (admin only)."""
        try:
            # Get all limit requests
            limit_requests = self.firebase_service.get_collection('limit_requests')
            
            # Calculate statistics
            total_requests = len(limit_requests)
            
            # Status breakdown
            status_stats = {}
            for req in limit_requests:
                status = req.get('status', 'UNKNOWN')
                status_stats[status] = status_stats.get(status, 0) + 1
            
            # Request type breakdown
            type_stats = {}
            for req in limit_requests:
                req_type = req.get('request_type', 'limit_increase')
                type_stats[req_type] = type_stats.get(req_type, 0) + 1
            
            # Average processing time for completed requests
            completed_requests = [
                req for req in limit_requests
                if req.get('status') in ['APPROVED', 'REJECTED']
            ]
            
            avg_processing_time = None
            if completed_requests:
                total_time = 0
                count = 0
                for req in completed_requests:
                    created_at = req.get('created_at')
                    completed_at = req.get('approved_at') or req.get('rejected_at')
                    if created_at and completed_at:
                        if isinstance(created_at, str):
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if isinstance(completed_at, str):
                            completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                        
                        processing_time = (completed_at - created_at).total_seconds() / 3600  # hours
                        total_time += processing_time
                        count += 1
                
                if count > 0:
                    avg_processing_time = round(total_time / count, 2)
            
            stats = {
                'total_requests': total_requests,
                'status_breakdown': status_stats,
                'request_type_breakdown': type_stats,
                'average_processing_time_hours': avg_processing_time,
                'pending_requests': status_stats.get('PENDING', 0),
                'under_review': status_stats.get('UNDER_REVIEW', 0),
                'approved_requests': status_stats.get('APPROVED', 0),
                'rejected_requests': status_stats.get('REJECTED', 0),
                'generated_at': datetime.now().isoformat()
            }
            
            return Response({
                'status': 'success',
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Error generating limit request stats: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to generate statistics',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )