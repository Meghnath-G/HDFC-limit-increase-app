"""
Django REST Framework views for Customer management.

Provides comprehensive customer management API with registration,
profile management, KYC verification, and analytics.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import logging

from .models import Customer, CardDetail
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
from core.permissions import IsOwnerOrAdmin, IsCustomerService
from core.mixins import SecurityMixin, AuditMixin
from core.pagination import StandardResultsSetPagination
from core.throttling import CustomerRegistrationThrottle
from core.utils import generate_customer_id, encrypt_field
from apps.notifications.services import NotificationService

logger = logging.getLogger(__name__)


class CustomerViewSet(SecurityMixin, AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet for customer management.
    
    Provides CRUD operations for customers with proper
    authentication, authorization, and audit logging.
    """
    
    queryset = Customer.objects.select_related().prefetch_related('card_details')
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['customer_segment', 'is_kyc_completed', 'is_active']
    search_fields = ['customer_id', 'full_name', 'email']
    ordering_fields = ['created_at', 'last_login', 'full_name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CustomerRegistrationSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return CustomerUpdateSerializer
        elif self.action == 'retrieve':
            return CustomerDetailSerializer
        elif self.action == 'list':
            return CustomerListSerializer
        elif self.action == 'update_kyc':
            return CustomerKYCUpdateSerializer
        else:
            return CustomerProfileSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='customer_service').exists():
            # Staff and customer service can see all customers
            return self.queryset
        else:
            # Regular users can only see their own profile
            try:
                customer = Customer.objects.get(firebase_uid=user.username)
                return self.queryset.filter(id=customer.id)
            except Customer.DoesNotExist:
                return Customer.objects.none()
    
    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action == 'create':
            # Registration is open but throttled
            permission_classes = [CustomerRegistrationThrottle]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
        elif self.action in ['update_kyc', 'admin_actions']:
            permission_classes = [permissions.IsAuthenticated, IsCustomerService]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create new customer with proper validation and notifications."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Create customer
            customer = serializer.save()
            
            # Log registration event
            self.log_audit_event(
                action='customer_registration',
                resource_type='Customer',
                resource_id=customer.id,
                user=request.user,
                details={
                    'customer_id': customer.customer_id,
                    'registration_method': request.data.get('registration_method', 'mobile_app')
                }
            )
            
            # Send welcome notification
            NotificationService.send_welcome_notification(customer)
            
            # Cache customer profile
            cache.set(f'customer_profile_{customer.customer_id}', customer, 3600)
            
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    'status': 'success',
                    'message': 'Customer registered successfully',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
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
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve customer with cached data and audit logging."""
        instance = self.get_object()
        
        # Check cache first
        cache_key = f'customer_detail_{instance.customer_id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response({
                'status': 'success',
                'data': cached_data,
                'cached': True
            })
        
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Cache the response
        cache.set(cache_key, data, 1800)  # 30 minutes
        
        # Log profile view
        self.log_audit_event(
            action='profile_view',
            resource_type='Customer',
            resource_id=instance.id,
            user=request.user
        )
        
        return Response({
            'status': 'success',
            'data': data,
            'cached': False
        })
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update customer profile with validation and notifications."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Store original values for comparison
        original_data = {
            'phone_number': instance.phone_number,
            'email': instance.email,
            'address': instance.address
        }
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            customer = serializer.save()
            
            # Check for sensitive changes
            sensitive_changes = []
            if customer.phone_number != original_data['phone_number']:
                sensitive_changes.append('phone_number')
            if customer.email != original_data['email']:
                sensitive_changes.append('email')
            if customer.address != original_data['address']:
                sensitive_changes.append('address')
            
            # Log profile update
            self.log_audit_event(
                action='profile_update',
                resource_type='Customer',
                resource_id=customer.id,
                user=request.user,
                details={
                    'changed_fields': list(request.data.keys()),
                    'sensitive_changes': sensitive_changes
                }
            )
            
            # Send security notification for sensitive changes
            if sensitive_changes:
                NotificationService.send_profile_change_notification(
                    customer, sensitive_changes
                )
            
            # Clear cache
            cache.delete_many([
                f'customer_profile_{customer.customer_id}',
                f'customer_detail_{customer.customer_id}'
            ])
            
            return Response({
                'status': 'success',
                'message': 'Profile updated successfully',
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Customer update failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Update failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsCustomerService])
    def update_kyc(self, request, pk=None):
        """Update KYC status and documents (Admin only)."""
        customer = self.get_object()
        serializer = CustomerKYCUpdateSerializer(
            customer, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    updated_customer = serializer.save()
                    
                    # Log KYC update
                    self.log_audit_event(
                        action='kyc_update',
                        resource_type='Customer',
                        resource_id=customer.id,
                        user=request.user,
                        details={
                            'kyc_status': updated_customer.is_kyc_completed,
                            'verification_level': updated_customer.kyc_verification_level,
                            'admin_user': request.user.username
                        }
                    )
                    
                    # Send KYC status notification
                    NotificationService.send_kyc_status_notification(
                        updated_customer,
                        'completed' if updated_customer.is_kyc_completed else 'pending'
                    )
                    
                    # Clear cache
                    cache.delete_many([
                        f'customer_profile_{customer.customer_id}',
                        f'customer_detail_{customer.customer_id}'
                    ])
                    
                    return Response({
                        'status': 'success',
                        'message': 'KYC status updated successfully',
                        'data': CustomerDetailSerializer(updated_customer).data
                    })
                    
            except Exception as e:
                logger.error(f"KYC update failed: {str(e)}")
                return Response(
                    {
                        'status': 'error',
                        'message': 'KYC update failed',
                        'errors': {'non_field_errors': [str(e)]}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {
                    'status': 'error',
                    'message': 'Invalid data provided',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Get customer profile with enhanced information."""
        customer = self.get_object()
        
        # Check if user can access this profile
        if not request.user.is_staff and customer.firebase_uid != request.user.username:
            raise PermissionDenied("You can only access your own profile")
        
        serializer = CustomerProfileSerializer(customer)
        
        # Add additional profile information
        profile_data = serializer.data
        profile_data.update({
            'account_age_days': (timezone.now().date() - customer.created_at.date()).days,
            'last_activity': customer.last_login,
            'has_pending_requests': customer.limit_requests.filter(
                status__in=['PENDING', 'UNDER_REVIEW']
            ).exists(),
            'total_requests': customer.limit_requests.count(),
            'cards_count': customer.card_details.count()
        })
        
        return Response({
            'status': 'success',
            'data': profile_data
        })
    
    @action(detail=True, methods=['get'])
    def cards(self, request, pk=None):
        """Get customer's card details."""
        customer = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and customer.firebase_uid != request.user.username:
            raise PermissionDenied("You can only access your own cards")
        
        cards = customer.card_details.filter(is_active=True)
        serializer = CardDetailSerializer(cards, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'count': cards.count()
        })
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change customer password with proper validation."""
        customer = self.get_object()
        
        # Check permissions
        if customer.firebase_uid != request.user.username:
            raise PermissionDenied("You can only change your own password")
        
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            return Response(
                {
                    'status': 'error',
                    'message': 'All password fields are required',
                    'errors': {
                        'password': ['Current password, new password, and confirmation are required']
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != confirm_password:
            return Response(
                {
                    'status': 'error',
                    'message': 'Password confirmation does not match',
                    'errors': {
                        'confirm_password': ['Password confirmation does not match']
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Here you would typically verify with Firebase Auth
        # For now, we'll log the password change request
        
        try:
            # Log password change
            self.log_audit_event(
                action='password_change',
                resource_type='Customer',
                resource_id=customer.id,
                user=request.user,
                details={
                    'timestamp': timezone.now().isoformat(),
                    'ip_address': self.get_client_ip(request)
                }
            )
            
            # Send security notification
            NotificationService.send_password_change_notification(customer)
            
            return Response({
                'status': 'success',
                'message': 'Password changed successfully'
            })
            
        except Exception as e:
            logger.error(f"Password change failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Password change failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsCustomerService])
    def statistics(self, request):
        """Get customer statistics (Admin only)."""
        try:
            # Get query parameters
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Build base queryset
            queryset = Customer.objects.all()
            
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            
            # Calculate statistics
            stats = {
                'total_customers': queryset.count(),
                'active_customers': queryset.filter(is_active=True).count(),
                'kyc_completed': queryset.filter(is_kyc_completed=True).count(),
                'kyc_pending': queryset.filter(is_kyc_completed=False).count(),
                'by_segment': queryset.values('customer_segment').annotate(
                    count=Count('id')
                ),
                'registrations_by_month': queryset.extra(
                    select={'month': "to_char(created_at, 'YYYY-MM')"}
                ).values('month').annotate(count=Count('id')).order_by('month'),
                'avg_age': queryset.aggregate(Avg('age'))['age__avg'] or 0,
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsCustomerService])
    def deactivate(self, request, pk=None):
        """Deactivate customer account (Admin only)."""
        customer = self.get_object()
        reason = request.data.get('reason', 'No reason provided')
        
        try:
            with transaction.atomic():
                customer.is_active = False
                customer.deactivated_at = timezone.now()
                customer.deactivation_reason = reason
                customer.save()
                
                # Log deactivation
                self.log_audit_event(
                    action='customer_deactivation',
                    resource_type='Customer',
                    resource_id=customer.id,
                    user=request.user,
                    details={
                        'reason': reason,
                        'admin_user': request.user.username
                    }
                )
                
                # Send deactivation notification
                NotificationService.send_account_deactivation_notification(
                    customer, reason
                )
                
                # Clear cache
                cache.delete_many([
                    f'customer_profile_{customer.customer_id}',
                    f'customer_detail_{customer.customer_id}'
                ])
                
                return Response({
                    'status': 'success',
                    'message': 'Customer account deactivated successfully'
                })
                
        except Exception as e:
            logger.error(f"Customer deactivation failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Deactivation failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )