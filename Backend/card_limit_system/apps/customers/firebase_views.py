"""
Firebase-compatible Django REST Framework views for Customer management.

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

# Firebase imports
from core.firebase_config import FirebaseService
from core.firebase_schema import CustomerSchema, CardDetailsSchema, validate_document

# Original serializers (will be updated for Firebase)
from .serializers import (
    CustomerRegistrationSerializer,
    CustomerProfileSerializer,
    CustomerDetailSerializer,
    CustomerUpdateSerializer,
    CardDetailSerializer,
    CustomerStatsSerializer,
    CustomerKYCUpdateSerializer,
    CustomerListSerializer
)

# Core utilities
from core.permissions import IsOwnerOrAdmin, IsCustomerService
from core.mixins import SecurityMixin, AuditMixin
from core.pagination import StandardResultsSetPagination
from core.throttling import CustomerRegistrationThrottle
from core.utils import generate_customer_id, encrypt_field
from apps.notifications.services import NotificationService

logger = logging.getLogger(__name__)


class FirebaseCustomerViewSet(SecurityMixin, AuditMixin, viewsets.ViewSet):
    """
    Firebase-based ViewSet for customer management.
    
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
            'create': CustomerRegistrationSerializer,
            'update': CustomerUpdateSerializer,
            'partial_update': CustomerUpdateSerializer,
            'retrieve': CustomerDetailSerializer,
            'list': CustomerListSerializer,
            'update_kyc': CustomerKYCUpdateSerializer,
        }
        return action_serializers.get(self.action, CustomerProfileSerializer)
    
    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action == 'create':
            permission_classes = [CustomerRegistrationThrottle]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
        elif self.action in ['update_kyc', 'admin_actions']:
            permission_classes = [permissions.IsAuthenticated, IsCustomerService]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_customer_by_firebase_uid(self, firebase_uid: str) -> Optional[Dict[str, Any]]:
        """Get customer document by Firebase UID."""
        try:
            # Query Firestore for customer with matching firebase_uid
            customers = self.firebase_service.query_collection(
                'customers',
                field_path='firebase_uid',
                op_string='==',
                value=firebase_uid
            )
            
            if customers:
                return customers[0]  # Should be unique
            return None
            
        except Exception as e:
            logger.error(f"Error fetching customer by Firebase UID {firebase_uid}: {str(e)}")
            return None
    
    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer document by customer_id field."""
        try:
            # Query Firestore for customer with matching customer_id
            customers = self.firebase_service.query_collection(
                'customers',
                field_path='customer_id',
                op_string='==',
                value=customer_id
            )
            
            if customers:
                return customers[0]  # Should be unique
            return None
            
        except Exception as e:
            logger.error(f"Error fetching customer by ID {customer_id}: {str(e)}")
            return None
    
    def list(self, request):
        """List customers with filtering and pagination."""
        try:
            # Get user permissions
            user = request.user
            
            if user.is_staff or user.groups.filter(name='customer_service').exists():
                # Staff can see all customers
                customers = self.firebase_service.get_collection('customers')
            else:
                # Regular users can only see their own profile
                customer = self.get_customer_by_firebase_uid(user.username)
                customers = [customer] if customer else []
            
            # Apply filters (simplified for Firebase)
            search_query = request.query_params.get('search', '')
            if search_query:
                # Filter customers by name, email, or customer_id
                customers = [
                    customer for customer in customers
                    if (search_query.lower() in customer.get('name', '').lower() or
                        search_query.lower() in customer.get('email', '').lower() or
                        search_query.lower() in customer.get('customer_id', '').lower())
                ]
            
            # Apply pagination (simplified)
            page_size = int(request.query_params.get('page_size', 20))
            page = int(request.query_params.get('page', 1))
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            paginated_customers = customers[start_index:end_index]
            
            return Response({
                'status': 'success',
                'count': len(customers),
                'results': paginated_customers,
                'page': page,
                'page_size': page_size
            })
            
        except Exception as e:
            logger.error(f"Error listing customers: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve customers',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Retrieve customer with cached data and audit logging."""
        try:
            # Check cache first
            cache_key = f'firebase_customer_{pk}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return Response({
                    'status': 'success',
                    'data': cached_data,
                    'cached': True
                })
            
            # Get customer from Firebase
            customer = self.firebase_service.get_document('customers', pk)
            
            if not customer:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Customer not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Cache the response
            cache.set(cache_key, customer, 1800)  # 30 minutes
            
            # Log profile view
            self.log_audit_event(
                action='profile_view',
                resource_type='Customer',
                resource_id=pk,
                user=request.user
            )
            
            return Response({
                'status': 'success',
                'data': customer,
                'cached': False
            })
            
        except Exception as e:
            logger.error(f"Error retrieving customer {pk}: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve customer',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """Create new customer with proper validation and notifications."""
        try:
            # Validate input data
            serializer = self.get_serializer_class()(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Convert to Firebase schema
            customer_data = {
                'firebase_uid': request.data.get('firebase_uid'),
                'name': request.data.get('name'),
                'email': request.data.get('email'),
                'phone_number': request.data.get('phone_number'),
                'date_of_birth': request.data.get('date_of_birth'),
                'customer_id': generate_customer_id(),
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'customer_segment': 'STANDARD',
                'kyc_status': 'PENDING',
                'risk_score': 0
            }
            
            # Validate against Firebase schema
            is_valid, errors = validate_document('customers', customer_data)
            if not is_valid:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid customer data',
                        'errors': errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create customer in Firebase
            doc_id = self.firebase_service.create_document('customers', customer_data)
            
            # Log registration event
            self.log_audit_event(
                action='customer_registration',
                resource_type='Customer',
                resource_id=doc_id,
                user=request.user,
                details={
                    'customer_id': customer_data['customer_id'],
                    'registration_method': request.data.get('registration_method', 'mobile_app')
                }
            )
            
            # Send welcome notification (async)
            try:
                NotificationService.send_welcome_notification({
                    'id': doc_id,
                    'name': customer_data['name'],
                    'email': customer_data['email']
                })
            except Exception as e:
                logger.warning(f"Failed to send welcome notification: {str(e)}")
            
            # Cache customer profile
            cache.set(f'firebase_customer_{doc_id}', customer_data, 3600)
            
            # Return success response with Firebase document ID
            response_data = customer_data.copy()
            response_data['id'] = doc_id
            
            return Response(
                {
                    'status': 'success',
                    'message': 'Customer registered successfully',
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
            logger.error(f"Customer registration failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Registration failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, pk=None):
        """Update customer profile with validation and notifications."""
        try:
            # Get existing customer
            customer = self.firebase_service.get_document('customers', pk)
            
            if not customer:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Customer not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Store original values for comparison
            original_data = {
                'phone_number': customer.get('phone_number'),
                'email': customer.get('email'),
                'name': customer.get('name')
            }
            
            # Validate input data
            serializer = self.get_serializer_class()(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            # Update customer data
            updated_data = customer.copy()
            for key, value in request.data.items():
                if key in ['name', 'email', 'phone_number', 'date_of_birth']:
                    updated_data[key] = value
            
            updated_data['updated_at'] = datetime.now()
            
            # Validate against Firebase schema
            is_valid, errors = validate_document('customers', updated_data)
            if not is_valid:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid customer data',
                        'errors': errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update in Firebase
            self.firebase_service.update_document('customers', pk, updated_data)
            
            # Clear cache
            cache.delete(f'firebase_customer_{pk}')
            
            # Log update event
            changes_made = []
            for key in ['phone_number', 'email', 'name']:
                if original_data[key] != updated_data.get(key):
                    changes_made.append(key)
            
            if changes_made:
                self.log_audit_event(
                    action='profile_update',
                    resource_type='Customer',
                    resource_id=pk,
                    user=request.user,
                    details={'fields_changed': changes_made}
                )
            
            return Response({
                'status': 'success',
                'message': 'Customer profile updated successfully',
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
            logger.error(f"Customer update failed for {pk}: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Update failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, pk=None):
        """Soft delete customer (set is_active to False)."""
        try:
            # Get existing customer
            customer = self.firebase_service.get_document('customers', pk)
            
            if not customer:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Customer not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Soft delete by setting is_active to False
            updated_data = customer.copy()
            updated_data['is_active'] = False
            updated_data['updated_at'] = datetime.now()
            
            # Update in Firebase
            self.firebase_service.update_document('customers', pk, updated_data)
            
            # Clear cache
            cache.delete(f'firebase_customer_{pk}')
            
            # Log deletion event
            self.log_audit_event(
                action='customer_deactivation',
                resource_type='Customer',
                resource_id=pk,
                user=request.user
            )
            
            return Response({
                'status': 'success',
                'message': 'Customer account deactivated successfully'
            }, status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Customer deletion failed for {pk}: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Deletion failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'])
    def update_kyc(self, request, pk=None):
        """Update customer KYC status (admin only)."""
        try:
            # Get existing customer
            customer = self.firebase_service.get_document('customers', pk)
            
            if not customer:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Customer not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validate KYC data
            kyc_status = request.data.get('kyc_status')
            if kyc_status not in ['PENDING', 'VERIFIED', 'REJECTED']:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid KYC status'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update KYC status
            updated_data = customer.copy()
            updated_data['kyc_status'] = kyc_status
            updated_data['kyc_updated_at'] = datetime.now()
            updated_data['updated_at'] = datetime.now()
            
            if kyc_status == 'VERIFIED':
                updated_data['kyc_verified_at'] = datetime.now()
            
            # Update in Firebase
            self.firebase_service.update_document('customers', pk, updated_data)
            
            # Clear cache
            cache.delete(f'firebase_customer_{pk}')
            
            # Log KYC update
            self.log_audit_event(
                action='kyc_status_update',
                resource_type='Customer',
                resource_id=pk,
                user=request.user,
                details={'new_status': kyc_status}
            )
            
            return Response({
                'status': 'success',
                'message': f'KYC status updated to {kyc_status}',
                'data': updated_data
            })
            
        except Exception as e:
            logger.error(f"KYC update failed for {pk}: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'KYC update failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get customer statistics (admin only)."""
        try:
            # Get all customers
            customers = self.firebase_service.get_collection('customers')
            
            # Calculate statistics
            total_customers = len(customers)
            active_customers = len([c for c in customers if c.get('is_active', True)])
            kyc_verified = len([c for c in customers if c.get('kyc_status') == 'VERIFIED'])
            
            # Customer segments
            segments = {}
            for customer in customers:
                segment = customer.get('customer_segment', 'STANDARD')
                segments[segment] = segments.get(segment, 0) + 1
            
            stats = {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'inactive_customers': total_customers - active_customers,
                'kyc_verified': kyc_verified,
                'kyc_pending': total_customers - kyc_verified,
                'customer_segments': segments,
                'generated_at': datetime.now().isoformat()
            }
            
            return Response({
                'status': 'success',
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Error generating customer stats: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to generate statistics',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )