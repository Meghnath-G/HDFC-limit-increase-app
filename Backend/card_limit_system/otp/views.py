"""
Django REST Framework views for OTP management.

Provides secure OTP generation, verification, and management
with proper rate limiting, security controls, and audit logging.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
import logging
from datetime import timedelta

from .models import OTPLog
from .serializers import (
    OTPGenerateSerializer,
    OTPVerifySerializer,
    OTPResendSerializer,
    OTPListSerializer,
    OTPStatsSerializer
)
from .services import OTPService
from apps.customers.models import Customer
from core.permissions import IsOwnerOrAdmin, IsCustomerService
from core.mixins import SecurityMixin, AuditMixin
from core.pagination import StandardResultsSetPagination
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle
from core.utils import get_client_ip
from apps.notifications.services import NotificationService

logger = logging.getLogger(__name__)


class OTPViewSet(SecurityMixin, AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet for OTP management.
    
    Provides secure OTP operations with proper rate limiting,
    security controls, and comprehensive audit logging.
    """
    
    queryset = OTPLog.objects.select_related('customer')
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['purpose', 'delivery_method', 'is_verified', 'is_expired']
    ordering_fields = ['created_at', 'expires_at', 'verified_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'generate':
            return OTPGenerateSerializer
        elif self.action == 'verify':
            return OTPVerifySerializer
        elif self.action == 'resend':
            return OTPResendSerializer
        elif self.action == 'list':
            return OTPListSerializer
        else:
            return OTPListSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='customer_service').exists():
            # Staff can see all OTP logs (with masked data)
            return self.queryset
        else:
            # Regular users can only see their own OTP logs
            try:
                customer = Customer.objects.get(firebase_uid=user.username)
                return self.queryset.filter(customer=customer)
            except Customer.DoesNotExist:
                return OTPLog.objects.none()
    
    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ['generate', 'verify', 'resend']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['statistics', 'admin_actions']:
            permission_classes = [permissions.IsAuthenticated, IsCustomerService]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request, *args, **kwargs):
        """List OTP logs with proper filtering and security."""
        # Override default list to add security headers
        response = super().list(request, *args, **kwargs)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        
        return response
    
    @action(detail=False, methods=['post'], throttle_classes=[OTPGenerationThrottle])
    def generate(self, request):
        """Generate OTP with proper validation and rate limiting."""
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
        
        # Add customer to request data
        data = request.data.copy()
        data['customer'] = customer.id
        
        # Add request metadata
        data['request_metadata'] = {
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': timezone.now().isoformat()
        }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Check rate limiting
            rate_limit_key = f'otp_rate_limit_{customer.id}'
            recent_requests = cache.get(rate_limit_key, 0)
            
            if recent_requests >= 5:  # Max 5 OTP requests per hour
                return Response(
                    {
                        'status': 'error',
                        'message': 'Rate limit exceeded',
                        'errors': {'rate_limit': ['Too many OTP requests. Please try after 1 hour.']}
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Generate OTP using service
            purpose = serializer.validated_data['purpose']
            delivery_method = serializer.validated_data['delivery_method']
            recipient = serializer.validated_data.get('recipient')
            
            otp_log = OTPService.generate_otp(
                customer=customer,
                purpose=purpose,
                delivery_method=delivery_method,
                recipient=recipient,
                request_metadata=data['request_metadata']
            )
            
            # Update rate limiting
            cache.set(rate_limit_key, recent_requests + 1, 3600)  # 1 hour
            
            # Log OTP generation
            self.log_audit_event(
                action='otp_generated',
                resource_type='OTPLog',
                resource_id=otp_log.id,
                user=request.user,
                details={
                    'purpose': purpose,
                    'delivery_method': delivery_method,
                    'customer_id': customer.customer_id,
                    'ip_address': get_client_ip(request)
                }
            )
            
            # Send OTP via notification service
            NotificationService.send_otp_notification(otp_log)
            
            return Response({
                'status': 'success',
                'message': 'OTP sent successfully',
                'data': {
                    'otp_id': otp_log.id,
                    'purpose': purpose,
                    'delivery_method': delivery_method,
                    'masked_recipient': otp_log.get_masked_recipient(),
                    'expires_at': otp_log.expires_at,
                    'can_resend_after': timezone.now() + timedelta(minutes=2)
                }
            })
            
        except Exception as e:
            logger.error(f"OTP generation failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'OTP generation failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], throttle_classes=[OTPVerificationThrottle])
    def verify(self, request):
        """Verify OTP with proper validation and security checks."""
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
        
        # Add customer to request data
        data = request.data.copy()
        data['customer'] = customer.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Check verification attempts rate limiting
            rate_limit_key = f'otp_verify_rate_limit_{customer.id}'
            recent_attempts = cache.get(rate_limit_key, 0)
            
            if recent_attempts >= 10:  # Max 10 verification attempts per hour
                return Response(
                    {
                        'status': 'error',
                        'message': 'Verification rate limit exceeded',
                        'errors': {'rate_limit': ['Too many verification attempts. Please try after 1 hour.']}
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Verify OTP using service
            otp_code = serializer.validated_data['otp_code']
            purpose = serializer.validated_data['purpose']
            
            verification_result = OTPService.verify_otp(
                customer=customer,
                otp_code=otp_code,
                purpose=purpose,
                ip_address=get_client_ip(request)
            )
            
            # Update rate limiting
            cache.set(rate_limit_key, recent_attempts + 1, 3600)  # 1 hour
            
            if verification_result['success']:
                otp_log = verification_result['otp_log']
                
                # Log successful verification
                self.log_audit_event(
                    action='otp_verified_success',
                    resource_type='OTPLog',
                    resource_id=otp_log.id,
                    user=request.user,
                    details={
                        'purpose': purpose,
                        'customer_id': customer.customer_id,
                        'ip_address': get_client_ip(request),
                        'verification_time': timezone.now().isoformat()
                    }
                )
                
                # Clear verification rate limit on success
                cache.delete(rate_limit_key)
                
                return Response({
                    'status': 'success',
                    'message': 'OTP verified successfully',
                    'data': {
                        'verified': True,
                        'purpose': purpose,
                        'verified_at': otp_log.verified_at,
                        'verification_token': verification_result.get('verification_token')
                    }
                })
            else:
                # Log failed verification
                self.log_audit_event(
                    action='otp_verified_failed',
                    resource_type='OTPLog',
                    resource_id=None,
                    user=request.user,
                    details={
                        'purpose': purpose,
                        'customer_id': customer.customer_id,
                        'ip_address': get_client_ip(request),
                        'failure_reason': verification_result['error']
                    }
                )
                
                return Response(
                    {
                        'status': 'error',
                        'message': verification_result['error'],
                        'errors': {'otp_code': [verification_result['error']]}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"OTP verification failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'OTP verification failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def resend(self, request):
        """Resend OTP with proper validation and rate limiting."""
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
        
        serializer = OTPResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Check resend rate limiting
            rate_limit_key = f'otp_resend_rate_limit_{customer.id}'
            recent_resends = cache.get(rate_limit_key, 0)
            
            if recent_resends >= 3:  # Max 3 resends per hour
                return Response(
                    {
                        'status': 'error',
                        'message': 'Resend rate limit exceeded',
                        'errors': {'rate_limit': ['Too many resend requests. Please try after 1 hour.']}
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Get original OTP log
            otp_id = serializer.validated_data['otp_id']
            try:
                original_otp = OTPLog.objects.get(
                    id=otp_id,
                    customer=customer,
                    is_verified=False
                )
            except OTPLog.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Invalid OTP request',
                        'errors': {'otp_id': ['OTP not found or already verified']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if resend is allowed (minimum 2 minutes gap)
            min_resend_time = original_otp.created_at + timedelta(minutes=2)
            if timezone.now() < min_resend_time:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Please wait before requesting resend',
                        'errors': {'timing': ['You can resend OTP after 2 minutes']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Resend OTP using service
            new_otp_log = OTPService.resend_otp(
                original_otp=original_otp,
                new_delivery_method=serializer.validated_data.get('new_delivery_method'),
                new_recipient=serializer.validated_data.get('new_recipient')
            )
            
            # Update rate limiting
            cache.set(rate_limit_key, recent_resends + 1, 3600)  # 1 hour
            
            # Log OTP resend
            self.log_audit_event(
                action='otp_resent',
                resource_type='OTPLog',
                resource_id=new_otp_log.id,
                user=request.user,
                details={
                    'original_otp_id': str(original_otp.id),
                    'purpose': original_otp.purpose,
                    'delivery_method': new_otp_log.delivery_method,
                    'customer_id': customer.customer_id,
                    'ip_address': get_client_ip(request)
                }
            )
            
            # Send new OTP via notification service
            NotificationService.send_otp_notification(new_otp_log)
            
            return Response({
                'status': 'success',
                'message': 'OTP resent successfully',
                'data': {
                    'otp_id': new_otp_log.id,
                    'delivery_method': new_otp_log.delivery_method,
                    'masked_recipient': new_otp_log.get_masked_recipient(),
                    'expires_at': new_otp_log.expires_at,
                    'can_resend_after': timezone.now() + timedelta(minutes=2)
                }
            })
            
        except Exception as e:
            logger.error(f"OTP resend failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'OTP resend failed. Please try again.',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsCustomerService])
    def statistics(self, request):
        """Get OTP statistics and analytics (Admin only)."""
        try:
            # Get query parameters
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Build base queryset
            queryset = OTPLog.objects.all()
            
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            
            # Calculate statistics
            stats = {
                'total_generated': queryset.count(),
                'total_verified': queryset.filter(is_verified=True).count(),
                'total_expired': queryset.filter(is_expired=True).count(),
                'verification_rate': 0,
                'by_purpose': queryset.values('purpose').annotate(
                    count=Count('id')
                ),
                'by_delivery_method': queryset.values('delivery_method').annotate(
                    count=Count('id')
                ),
                'failed_attempts': queryset.filter(
                    verification_attempts__gt=0,
                    is_verified=False
                ).count(),
                'avg_verification_time': None,
                'peak_hours': queryset.extra(
                    select={'hour': "extract(hour from created_at)"}
                ).values('hour').annotate(count=Count('id')).order_by('-count')[:5]
            }
            
            # Calculate verification rate
            if stats['total_generated'] > 0:
                stats['verification_rate'] = round(
                    (stats['total_verified'] / stats['total_generated']) * 100, 2
                )
            
            # Calculate average verification time
            verified_otps = queryset.filter(
                is_verified=True,
                verified_at__isnull=False
            )
            if verified_otps.exists():
                total_time = sum([
                    (otp.verified_at - otp.created_at).total_seconds()
                    for otp in verified_otps
                ])
                stats['avg_verification_time'] = round(
                    total_time / verified_otps.count(), 2
                )
            
            return Response({
                'status': 'success',
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"OTP statistics retrieval failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve OTP statistics',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsCustomerService])
    def bulk_expire(self, request):
        """Bulk expire OTPs (Admin only)."""
        customer_id = request.data.get('customer_id')
        purpose = request.data.get('purpose')
        
        if not customer_id:
            return Response(
                {
                    'status': 'error',
                    'message': 'Customer ID is required',
                    'errors': {'customer_id': ['This field is required']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {
                    'status': 'error',
                    'message': 'Customer not found',
                    'errors': {'customer_id': ['Customer not found']}
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Build queryset for expiring OTPs
            expire_queryset = OTPLog.objects.filter(
                customer=customer,
                is_verified=False,
                is_expired=False
            )
            
            if purpose:
                expire_queryset = expire_queryset.filter(purpose=purpose)
            
            # Expire OTPs
            expired_count = expire_queryset.count()
            expire_queryset.update(
                is_expired=True,
                expired_at=timezone.now(),
                expiry_reason='Admin bulk expire'
            )
            
            # Log bulk expiry
            self.log_audit_event(
                action='otp_bulk_expired',
                resource_type='OTPLog',
                resource_id=None,
                user=request.user,
                details={
                    'customer_id': customer_id,
                    'purpose': purpose,
                    'expired_count': expired_count,
                    'admin_user': request.user.username
                }
            )
            
            return Response({
                'status': 'success',
                'message': f'Successfully expired {expired_count} OTPs',
                'data': {
                    'expired_count': expired_count,
                    'customer_id': customer_id,
                    'purpose': purpose
                }
            })
            
        except Exception as e:
            logger.error(f"Bulk OTP expiry failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Bulk expiry failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )