"""
Django REST Framework views for Notification management.

Provides comprehensive notification management with delivery
tracking, preference management, and analytics.
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
from datetime import timedelta

from .models import NotificationLog, NotificationTemplate, NotificationPreference
from .serializers import (
    NotificationSendSerializer,
    NotificationListSerializer,
    NotificationDetailSerializer,
    NotificationPreferenceSerializer,
    NotificationTemplateSerializer,
    NotificationStatsSerializer,
    NotificationBulkSendSerializer
)
from .services import NotificationService
from apps.customers.models import Customer
from core.permissions import IsOwnerOrAdmin, IsCustomerService
from core.mixins import SecurityMixin, AuditMixin
from core.pagination import StandardResultsSetPagination
from core.throttling import NotificationThrottle
from core.utils import get_client_ip

logger = logging.getLogger(__name__)


class NotificationViewSet(SecurityMixin, AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet for notification management.
    
    Provides comprehensive notification operations with proper
    delivery tracking, analytics, and customer preference handling.
    """
    
    queryset = NotificationLog.objects.select_related('customer')
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'notification_type', 'category', 'priority', 'status',
        'customer__customer_segment'
    ]
    search_fields = ['title', 'message', 'customer__customer_id']
    ordering_fields = ['created_at', 'sent_at', 'delivered_at', 'read_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'send':
            return NotificationSendSerializer
        elif self.action == 'bulk_send':
            return NotificationBulkSendSerializer
        elif self.action == 'retrieve':
            return NotificationDetailSerializer
        elif self.action == 'list':
            return NotificationListSerializer
        else:
            return NotificationListSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='customer_service').exists():
            # Staff can see all notifications
            return self.queryset
        else:
            # Regular users can only see their own notifications
            try:
                customer = Customer.objects.get(firebase_uid=user.username)
                return self.queryset.filter(customer=customer)
            except Customer.DoesNotExist:
                return NotificationLog.objects.none()
    
    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ['send', 'bulk_send']:
            permission_classes = [permissions.IsAuthenticated, IsCustomerService]
        elif self.action in ['statistics', 'admin_actions']:
            permission_classes = [permissions.IsAuthenticated, IsCustomerService]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['post'], permission_classes=[IsCustomerService])
    def send(self, request):
        """Send notification with proper validation and delivery tracking."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Extract validated data
            notification_type = serializer.validated_data['notification_type']
            category = serializer.validated_data['category']
            priority = serializer.validated_data.get('priority', 'NORMAL')
            
            # Content handling
            template_code = serializer.validated_data.get('template_code')
            template_variables = serializer.validated_data.get('template_variables', {})
            
            # Direct content
            title = serializer.validated_data.get('title')
            message = serializer.validated_data.get('message')
            rich_content = serializer.validated_data.get('rich_content')
            
            # Delivery options
            recipient_identifier = serializer.validated_data.get('recipient_identifier')
            scheduled_at = serializer.validated_data.get('scheduled_at')
            
            # Context fields
            related_request_id = serializer.validated_data.get('related_request_id')
            related_entity_type = serializer.validated_data.get('related_entity_type')
            related_entity_id = serializer.validated_data.get('related_entity_id')
            
            # Send notification using service
            if template_code:
                # Template-based notification
                template = serializer.validated_data['_template']
                notification_log = NotificationService.send_template_notification(
                    template=template,
                    template_variables=template_variables,
                    notification_type=notification_type,
                    recipient=recipient_identifier,
                    priority=priority,
                    scheduled_at=scheduled_at,
                    related_request_id=related_request_id,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id
                )
            else:
                # Direct content notification
                notification_log = NotificationService.send_direct_notification(
                    notification_type=notification_type,
                    category=category,
                    title=title,
                    message=message,
                    rich_content=rich_content,
                    recipient=recipient_identifier,
                    priority=priority,
                    scheduled_at=scheduled_at,
                    related_request_id=related_request_id,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id
                )
            
            # Log notification send
            self.log_audit_event(
                action='notification_sent',
                resource_type='NotificationLog',
                resource_id=notification_log.id,
                user=request.user,
                details={
                    'notification_type': notification_type,
                    'category': category,
                    'priority': priority,
                    'template_code': template_code,
                    'admin_user': request.user.username
                }
            )
            
            return Response({
                'status': 'success',
                'message': 'Notification sent successfully',
                'data': {
                    'notification_id': notification_log.id,
                    'delivery_status': notification_log.status,
                    'scheduled_at': notification_log.scheduled_at,
                    'external_message_id': notification_log.external_message_id
                }
            })
            
        except Exception as e:
            logger.error(f"Notification send failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Notification send failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsCustomerService])
    def bulk_send(self, request):
        """Send bulk notifications with segmentation and scheduling."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Extract validated data
            notification_type = serializer.validated_data['notification_type']
            category = serializer.validated_data['category']
            template_code = serializer.validated_data['template_code']
            recipient_filter = serializer.validated_data['recipient_filter']
            scheduled_at = serializer.validated_data.get('scheduled_at')
            batch_size = serializer.validated_data.get('batch_size', 100)
            
            # Initiate bulk send using service
            bulk_job = NotificationService.send_bulk_notification(
                notification_type=notification_type,
                category=category,
                template_code=template_code,
                recipient_filter=recipient_filter,
                scheduled_at=scheduled_at,
                batch_size=batch_size,
                initiated_by=request.user.username
            )
            
            # Log bulk send initiation
            self.log_audit_event(
                action='bulk_notification_initiated',
                resource_type='BulkNotificationJob',
                resource_id=bulk_job['job_id'],
                user=request.user,
                details={
                    'notification_type': notification_type,
                    'template_code': template_code,
                    'estimated_recipients': bulk_job['estimated_recipients'],
                    'admin_user': request.user.username
                }
            )
            
            return Response({
                'status': 'success',
                'message': 'Bulk notification job initiated',
                'data': {
                    'bulk_job_id': bulk_job['job_id'],
                    'estimated_recipients': bulk_job['estimated_recipients'],
                    'scheduled_at': scheduled_at,
                    'batch_size': batch_size
                }
            })
            
        except Exception as e:
            logger.error(f"Bulk notification failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Bulk notification failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and notification.customer.firebase_uid != request.user.username:
            raise PermissionDenied("You can only mark your own notifications as read")
        
        try:
            if not notification.read_at:
                notification.read_at = timezone.now()
                notification.save(update_fields=['read_at'])
                
                # Log read action
                self.log_audit_event(
                    action='notification_read',
                    resource_type='NotificationLog',
                    resource_id=notification.id,
                    user=request.user,
                    details={
                        'notification_type': notification.notification_type,
                        'read_time': notification.read_at.isoformat()
                    }
                )
            
            return Response({
                'status': 'success',
                'message': 'Notification marked as read',
                'data': {
                    'read_at': notification.read_at,
                    'read_time_seconds': notification.read_time.total_seconds() if notification.read_time else None
                }
            })
            
        except Exception as e:
            logger.error(f"Mark notification read failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to mark notification as read',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def track_click(self, request, pk=None):
        """Track notification click/interaction."""
        notification = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and notification.customer.firebase_uid != request.user.username:
            raise PermissionDenied("You can only track clicks on your own notifications")
        
        try:
            # Increment click count
            notification.click_count += 1
            notification.last_clicked_at = timezone.now()
            notification.save(update_fields=['click_count', 'last_clicked_at'])
            
            # Log click action
            self.log_audit_event(
                action='notification_clicked',
                resource_type='NotificationLog',
                resource_id=notification.id,
                user=request.user,
                details={
                    'notification_type': notification.notification_type,
                    'click_count': notification.click_count,
                    'clicked_at': notification.last_clicked_at.isoformat()
                }
            )
            
            return Response({
                'status': 'success',
                'message': 'Click tracked successfully',
                'data': {
                    'click_count': notification.click_count,
                    'last_clicked_at': notification.last_clicked_at
                }
            })
            
        except Exception as e:
            logger.error(f"Track notification click failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to track notification click',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsCustomerService])
    def statistics(self, request):
        """Get notification statistics and analytics (Admin only)."""
        try:
            # Get query parameters
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Build base queryset
            queryset = NotificationLog.objects.all()
            
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            
            # Calculate statistics
            stats = {
                'total_sent': queryset.count(),
                'total_delivered': queryset.filter(status='DELIVERED').count(),
                'total_read': queryset.filter(read_at__isnull=False).count(),
                'total_clicked': queryset.filter(click_count__gt=0).count(),
                'total_failed': queryset.filter(status='FAILED').count(),
                'delivery_rate': 0,
                'read_rate': 0,
                'click_through_rate': 0,
                'by_type': queryset.values('notification_type').annotate(
                    count=Count('id')
                ),
                'by_category': queryset.values('category').annotate(
                    count=Count('id')
                ),
                'by_status': queryset.values('status').annotate(
                    count=Count('id')
                ),
                'avg_delivery_time': None,
                'avg_read_time': None,
                'peak_hours': queryset.extra(
                    select={'hour': "extract(hour from created_at)"}
                ).values('hour').annotate(count=Count('id')).order_by('-count')[:5]
            }
            
            # Calculate rates
            if stats['total_sent'] > 0:
                stats['delivery_rate'] = round(
                    (stats['total_delivered'] / stats['total_sent']) * 100, 2
                )
                stats['read_rate'] = round(
                    (stats['total_read'] / stats['total_sent']) * 100, 2
                )
                
            if stats['total_delivered'] > 0:
                stats['click_through_rate'] = round(
                    (stats['total_clicked'] / stats['total_delivered']) * 100, 2
                )
            
            # Calculate average times
            delivered_notifications = queryset.filter(
                status='DELIVERED',
                delivered_at__isnull=False
            )
            if delivered_notifications.exists():
                total_delivery_time = sum([
                    (notif.delivered_at - notif.sent_at).total_seconds()
                    for notif in delivered_notifications
                    if notif.sent_at
                ])
                stats['avg_delivery_time'] = round(
                    total_delivery_time / delivered_notifications.count(), 2
                )
            
            read_notifications = queryset.filter(read_at__isnull=False)
            if read_notifications.exists():
                total_read_time = sum([
                    (notif.read_at - notif.delivered_at).total_seconds()
                    for notif in read_notifications
                    if notif.delivered_at
                ])
                stats['avg_read_time'] = round(
                    total_read_time / read_notifications.count(), 2
                )
            
            return Response({
                'status': 'success',
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Notification statistics retrieval failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve notification statistics',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationPreferenceViewSet(SecurityMixin, AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet for notification preferences management.
    
    Handles customer notification preferences with proper
    consent management and preference validation.
    """
    
    queryset = NotificationPreference.objects.select_related('customer')
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='customer_service').exists():
            # Staff can see all preferences
            return self.queryset
        else:
            # Regular users can only see their own preferences
            try:
                customer = Customer.objects.get(firebase_uid=user.username)
                return self.queryset.filter(customer=customer)
            except Customer.DoesNotExist:
                return NotificationPreference.objects.none()
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve notification preferences."""
        # For regular users, get their own preferences
        if not request.user.is_staff:
            try:
                customer = Customer.objects.get(firebase_uid=request.user.username)
                instance, created = NotificationPreference.objects.get_or_create(
                    customer=customer
                )
                serializer = self.get_serializer(instance)
                return Response({
                    'status': 'success',
                    'data': serializer.data
                })
            except Customer.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Customer profile not found',
                        'errors': {'customer': ['Please complete your profile first']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return super().retrieve(request, *args, **kwargs)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update notification preferences with consent tracking."""
        if not request.user.is_staff:
            # For regular users, update their own preferences
            try:
                customer = Customer.objects.get(firebase_uid=request.user.username)
                instance, created = NotificationPreference.objects.get_or_create(
                    customer=customer
                )
            except Customer.DoesNotExist:
                return Response(
                    {
                        'status': 'error',
                        'message': 'Customer profile not found',
                        'errors': {'customer': ['Please complete your profile first']}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            instance = self.get_object()
        
        # Store original preferences for comparison
        original_preferences = {
            'marketing_enabled': instance.marketing_communications_enabled,
            'push_enabled': instance.push_notifications_enabled,
            'sms_enabled': instance.sms_notifications_enabled,
            'email_enabled': instance.email_notifications_enabled
        }
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_preferences = serializer.save()
            
            # Track preference changes
            changes = []
            if updated_preferences.marketing_communications_enabled != original_preferences['marketing_enabled']:
                changes.append('marketing_communications')
            if updated_preferences.push_notifications_enabled != original_preferences['push_enabled']:
                changes.append('push_notifications')
            if updated_preferences.sms_notifications_enabled != original_preferences['sms_enabled']:
                changes.append('sms_notifications')
            if updated_preferences.email_notifications_enabled != original_preferences['email_enabled']:
                changes.append('email_notifications')
            
            # Log preference update
            self.log_audit_event(
                action='notification_preferences_updated',
                resource_type='NotificationPreference',
                resource_id=updated_preferences.id,
                user=request.user,
                details={
                    'changed_preferences': changes,
                    'customer_id': updated_preferences.customer.customer_id
                }
            )
            
            # Send confirmation if marketing preferences changed
            if 'marketing_communications' in changes:
                NotificationService.send_marketing_preference_change_notification(
                    updated_preferences.customer,
                    updated_preferences.marketing_communications_enabled
                )
            
            return Response({
                'status': 'success',
                'message': 'Notification preferences updated successfully',
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Notification preferences update failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Preferences update failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationTemplateViewSet(SecurityMixin, AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet for notification template management.
    
    Handles template creation, editing, and A/B testing
    with proper version control and analytics.
    """
    
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomerService]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'notification_type', 'language_code', 'is_active']
    search_fields = ['template_name', 'template_code']
    ordering_fields = ['created_at', 'updated_at', 'send_count']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate notification template."""
        template = self.get_object()
        
        try:
            template.is_active = True
            template.save(update_fields=['is_active'])
            
            # Log activation
            self.log_audit_event(
                action='template_activated',
                resource_type='NotificationTemplate',
                resource_id=template.id,
                user=request.user,
                details={
                    'template_code': template.template_code,
                    'template_name': template.template_name,
                    'admin_user': request.user.username
                }
            )
            
            return Response({
                'status': 'success',
                'message': 'Template activated successfully'
            })
            
        except Exception as e:
            logger.error(f"Template activation failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Template activation failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate notification template."""
        template = self.get_object()
        
        try:
            template.is_active = False
            template.save(update_fields=['is_active'])
            
            # Log deactivation
            self.log_audit_event(
                action='template_deactivated',
                resource_type='NotificationTemplate',
                resource_id=template.id,
                user=request.user,
                details={
                    'template_code': template.template_code,
                    'template_name': template.template_name,
                    'admin_user': request.user.username
                }
            )
            
            return Response({
                'status': 'success',
                'message': 'Template deactivated successfully'
            })
            
        except Exception as e:
            logger.error(f"Template deactivation failed: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': 'Template deactivation failed',
                    'errors': {'non_field_errors': [str(e)]}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )