"""
Django Admin configuration for Request models.

Provides comprehensive admin interface for managing limit requests
with workflow controls and status tracking.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from .models import LimitRequest, RequestStatusHistory


class RequestStatusHistoryInline(admin.TabularInline):
    """Inline admin for RequestStatusHistory."""
    
    model = RequestStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'changed_at', 'ip_address']
    fields = ['old_status', 'new_status', 'changed_by', 'change_reason', 'changed_at']
    
    def has_add_permission(self, request, obj):
        """Disable manual addition of status history."""
        return False
    
    def has_delete_permission(self, request, obj):
        """Disable deletion of status history."""
        return False


@admin.register(LimitRequest)
class LimitRequestAdmin(admin.ModelAdmin):
    """Admin interface for LimitRequest model."""
    
    list_display = [
        'reference_number',
        'customer_name',
        'request_type_display',
        'current_limit_display',
        'requested_limit_display',
        'status_badge',
        'priority_badge',
        'assigned_officer',
        'processing_days',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'request_type',
        'priority',
        'assigned_officer',
        'created_at',
        'decision_date',
    ]
    
    search_fields = [
        'reference_number',
        'customer__name',
        'customer__customer_id',
        'assigned_officer',
    ]
    
    readonly_fields = [
        'id',
        'reference_number',
        'customer',
        'card_detail',
        'request_type',
        'current_limit',
        'requested_limit',
        'reason',
        'created_at',
        'updated_at',
        'created_by_ip',
        'user_agent',
        'processing_days_display',
        'limit_increase_display',
        'approved_increase_display',
    ]
    
    fieldsets = (
        ('Request Information', {
            'fields': (
                'id', 'reference_number', 'customer', 'card_detail',
                'request_type', 'priority'
            )
        }),
        ('Limit Details', {
            'fields': (
                'current_limit', 'requested_limit', 'limit_increase_display',
                'approved_limit', 'approved_increase_display'
            )
        }),
        ('Request Justification', {
            'fields': ('reason', 'income_proof_uploaded', 'supporting_documents')
        }),
        ('Status & Workflow', {
            'fields': (
                'status', 'assigned_officer', 'processing_days_display',
                'estimated_processing_days', 'actual_processing_days'
            )
        }),
        ('Decision Details', {
            'fields': (
                'decision_date', 'decision_officer',
                'rejection_reason', 'internal_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Implementation', {
            'fields': (
                'implementation_date', 'old_system_limit', 'new_system_limit'
            ),
            'classes': ('collapse',)
        }),
        ('Audit Trail', {
            'fields': (
                'created_at', 'updated_at', 'created_by_ip', 'user_agent'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RequestStatusHistoryInline]
    
    actions = [
        'assign_to_officer',
        'mark_under_review',
        'approve_requests',
        'reject_requests',
    ]
    
    def customer_name(self, obj):
        """Display customer name with link."""
        url = reverse('admin:customers_customer_change', args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.customer.name)
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer__name'
    
    def request_type_display(self, obj):
        """Display request type with icon."""
        icons = {
            'credit_limit': '💳',
            'debit_limit': '🏦',
            'netbanking_limit': '🌐'
        }
        icon = icons.get(obj.request_type, '📋')
        return format_html('{} {}', icon, obj.get_request_type_display())
    request_type_display.short_description = 'Request Type'
    
    def current_limit_display(self, obj):
        """Display formatted current limit."""
        return format_html('₹{:,.2f}', obj.current_limit)
    current_limit_display.short_description = 'Current Limit'
    current_limit_display.admin_order_field = 'current_limit'
    
    def requested_limit_display(self, obj):
        """Display formatted requested limit."""
        return format_html('₹{:,.2f}', obj.requested_limit)
    requested_limit_display.short_description = 'Requested Limit'
    requested_limit_display.admin_order_field = 'requested_limit'
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#ffc107',      # Warning yellow
            'under_review': '#17a2b8', # Info blue
            'approved': '#28a745',     # Success green
            'rejected': '#dc3545',     # Danger red
            'implemented': '#6f42c1',  # Purple
            'cancelled': '#6c757d',    # Secondary gray
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def priority_badge(self, obj):
        """Display priority as colored badge."""
        colors = {
            'low': '#28a745',      # Green
            'normal': '#17a2b8',   # Blue
            'high': '#ffc107',     # Yellow
            'urgent': '#dc3545',   # Red
        }
        color = colors.get(obj.priority, '#17a2b8')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'
    
    def processing_days(self, obj):
        """Display processing days with overdue indication."""
        days = obj.processing_time_days
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} days (Overdue)</span>',
                days
            )
        return f"{days} days"
    processing_days.short_description = 'Processing Days'
    
    def processing_days_display(self, obj):
        """Display processing days for detail view."""
        days = obj.processing_time_days
        estimated = obj.estimated_processing_days
        if obj.is_overdue:
            return format_html(
                '<span style="color: red;">{} days (Overdue by {} days)</span>',
                days, days - estimated
            )
        return f"{days} days (Target: {estimated} days)"
    processing_days_display.short_description = 'Processing Time'
    
    def limit_increase_display(self, obj):
        """Display requested increase amount."""
        increase = obj.limit_increase_amount
        return format_html('₹{:,.2f}', increase)
    limit_increase_display.short_description = 'Requested Increase'
    
    def approved_increase_display(self, obj):
        """Display approved increase amount."""
        if obj.approved_limit:
            increase = obj.approved_increase_amount
            return format_html('₹{:,.2f}', increase)
        return '-'
    approved_increase_display.short_description = 'Approved Increase'
    
    def assign_to_officer(self, request, queryset):
        """Custom action to assign requests to officer."""
        # This would open a form to select officer
        # For now, just update status
        count = queryset.filter(status='pending').update(status='under_review')
        self.message_user(request, f'Moved {count} requests to under review.')
    assign_to_officer.short_description = 'Assign to officer for review'
    
    def mark_under_review(self, request, queryset):
        """Mark selected requests as under review."""
        count = queryset.filter(status='pending').update(status='under_review')
        self.message_user(request, f'Marked {count} requests as under review.')
    mark_under_review.short_description = 'Mark as under review'
    
    def approve_requests(self, request, queryset):
        """Approve selected requests."""
        count = 0
        for req in queryset.filter(status='under_review'):
            req.approve(
                approved_limit=req.requested_limit,
                officer=request.user.username,
                notes='Bulk approved via admin'
            )
            count += 1
        self.message_user(request, f'Approved {count} requests.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Reject selected requests."""
        count = 0
        for req in queryset.filter(status='under_review'):
            req.reject(
                reason='Rejected via admin action',
                officer=request.user.username,
                notes='Bulk rejected via admin'
            )
            count += 1
        self.message_user(request, f'Rejected {count} requests.')
    reject_requests.short_description = 'Reject selected requests'
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related(
            'customer', 'card_detail'
        ).prefetch_related('status_history')
    
    def changelist_view(self, request, extra_context=None):
        """Add custom context to changelist view."""
        extra_context = extra_context or {}
        
        # Add summary statistics
        qs = self.get_queryset(request)
        extra_context['summary_stats'] = {
            'total_requests': qs.count(),
            'pending_requests': qs.filter(status='pending').count(),
            'under_review': qs.filter(status='under_review').count(),
            'approved_today': qs.filter(
                status='approved',
                decision_date__date=timezone.now().date()
            ).count(),
            'overdue_requests': qs.filter(
                status__in=['pending', 'under_review'],
                created_at__lt=timezone.now() - timezone.timedelta(days=7)
            ).count(),
        }
        
        return super().changelist_view(request, extra_context)


@admin.register(RequestStatusHistory)
class RequestStatusHistoryAdmin(admin.ModelAdmin):
    """Admin interface for RequestStatusHistory model."""
    
    list_display = [
        'request_reference',
        'old_status',
        'new_status',
        'changed_by',
        'changed_at',
        'ip_address'
    ]
    
    list_filter = [
        'old_status',
        'new_status',
        'changed_by',
        'changed_at',
    ]
    
    search_fields = [
        'request__reference_number',
        'changed_by',
        'change_reason',
    ]
    
    readonly_fields = [
        'request',
        'old_status',
        'new_status',
        'changed_by',
        'changed_at',
        'ip_address',
    ]
    
    def request_reference(self, obj):
        """Display request reference with link."""
        url = reverse('admin:requests_limitrequest_change', args=[obj.request.pk])
        return format_html('<a href="{}">{}</a>', url, obj.request.reference_number)
    request_reference.short_description = 'Request'
    request_reference.admin_order_field = 'request__reference_number'
    
    def has_add_permission(self, request):
        """Disable manual addition of status history."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of status history."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deletion of status history."""
        return False


# Customize admin site header
admin.site.site_header = 'HDFC Card Limit System - Request Management'
admin.site.site_title = 'Request Admin'
admin.site.index_title = 'Request Administration Dashboard'