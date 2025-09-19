"""
Django Admin configuration for Customer models.

Provides secure admin interface for managing customers and cards
with proper permission controls and data masking.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Customer, CardDetail


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for Customer model with security features."""
    
    list_display = [
        'customer_id',
        'name', 
        'masked_email',
        'masked_phone',
        'status_badge',
        'kyc_status',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'is_kyc_completed',
        'is_email_verified',
        'is_phone_verified',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'customer_id',
        'firebase_uid',
    ]
    
    readonly_fields = [
        'id',
        'firebase_uid',
        'created_at',
        'updated_at',
        'masked_email_display',
        'masked_phone_display',
        'age_display',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'firebase_uid', 'name', 'date_of_birth', 'age_display')
        }),
        ('Contact Information', {
            'fields': ('masked_email_display', 'email', 'masked_phone_display', 'phone'),
            'description': 'Email and phone are encrypted in database'
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_email_verified', 'is_phone_verified', 'is_kyc_completed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_customers', 'deactivate_customers']
    
    def masked_email(self, obj):
        """Display masked email for list view."""
        return obj.get_masked_email()
    masked_email.short_description = 'Email'
    
    def masked_phone(self, obj):
        """Display masked phone for list view."""
        return obj.get_masked_phone()
    masked_phone.short_description = 'Phone'
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        color = 'green' if obj.is_active else 'red'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    status_badge.short_description = 'Status'
    
    def kyc_status(self, obj):
        """Display KYC status with icon."""
        if obj.is_kyc_completed:
            return format_html('✅ Completed')
        return format_html('❌ Pending')
    kyc_status.short_description = 'KYC Status'
    
    def masked_email_display(self, obj):
        """Display masked email in detail view."""
        return obj.get_masked_email()
    masked_email_display.short_description = 'Email (Masked)'
    
    def masked_phone_display(self, obj):
        """Display masked phone in detail view."""
        return obj.get_masked_phone()
    masked_phone_display.short_description = 'Phone (Masked)'
    
    def age_display(self, obj):
        """Display calculated age."""
        return f"{obj.age} years"
    age_display.short_description = 'Age'
    
    def activate_customers(self, request, queryset):
        """Bulk activate customers."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'Activated {count} customers.')
    activate_customers.short_description = 'Activate selected customers'
    
    def deactivate_customers(self, request, queryset):
        """Bulk deactivate customers."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {count} customers.')
    deactivate_customers.short_description = 'Deactivate selected customers'
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related()
    
    def has_change_permission(self, request, obj=None):
        """Control change permissions."""
        # Add custom permission logic here
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Control delete permissions - generally restricted for banking data."""
        return False  # Disable deletion for compliance


class CardDetailInline(admin.TabularInline):
    """Inline admin for CardDetail in Customer admin."""
    
    model = CardDetail
    extra = 0
    readonly_fields = ['id', 'masked_card_display', 'expiry_status', 'created_at']
    fields = ['card_type', 'masked_card_display', 'last4', 'expiry_month', 'expiry_year', 'current_limit', 'is_active']
    
    def masked_card_display(self, obj):
        """Display masked card number."""
        return obj.get_masked_card_number()
    masked_card_display.short_description = 'Card Number'
    
    def expiry_status(self, obj):
        """Display expiry status."""
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Valid</span>')
    expiry_status.short_description = 'Status'


@admin.register(CardDetail)
class CardDetailAdmin(admin.ModelAdmin):
    """Admin interface for CardDetail model."""
    
    list_display = [
        'customer_name',
        'card_type',
        'masked_card_number',
        'expiry_date',
        'current_limit',
        'status_badge',
        'created_at'
    ]
    
    list_filter = [
        'card_type',
        'is_active',
        'created_at',
        'expiry_year',
    ]
    
    search_fields = [
        'customer__name',
        'customer__customer_id',
        'last4',  # Note: This will search encrypted field
    ]
    
    readonly_fields = [
        'id',
        'masked_card_display',
        'expiry_status',
        'created_at',
    ]
    
    fieldsets = (
        ('Card Information', {
            'fields': ('customer', 'card_type', 'masked_card_display', 'last4')
        }),
        ('Expiry Information', {
            'fields': ('expiry_month', 'expiry_year', 'expiry_status')
        }),
        ('Limits & Status', {
            'fields': ('current_limit', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = ['customer']  # Use popup for customer selection
    
    def customer_name(self, obj):
        """Display customer name."""
        return obj.customer.name
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer__name'
    
    def masked_card_number(self, obj):
        """Display masked card number for list view."""
        return obj.get_masked_card_number()
    masked_card_number.short_description = 'Card Number'
    
    def expiry_date(self, obj):
        """Display formatted expiry date."""
        return f"{obj.expiry_month:02d}/{obj.expiry_year}"
    expiry_date.short_description = 'Expiry'
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        if obj.is_expired():
            return format_html('<span style="color: red; font-weight: bold;">Expired</span>')
        elif obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">Active</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">Inactive</span>')
    status_badge.short_description = 'Status'
    
    def masked_card_display(self, obj):
        """Display masked card number in detail view."""
        return obj.get_masked_card_number()
    masked_card_display.short_description = 'Card Number (Masked)'
    
    def expiry_status(self, obj):
        """Display expiry status with color."""
        if obj.is_expired():
            return format_html('<span style="color: red; font-weight: bold;">Expired</span>')
        return format_html('<span style="color: green; font-weight: bold;">Valid</span>')
    expiry_status.short_description = 'Expiry Status'
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('customer')
    
    def has_delete_permission(self, request, obj=None):
        """Control delete permissions - generally restricted for banking data."""
        return False  # Disable deletion for compliance


# Add CardDetail inline to Customer admin
CustomerAdmin.inlines = [CardDetailInline]


# Custom admin site configuration
admin.site.site_header = 'HDFC Card Limit System Admin'
admin.site.site_title = 'HDFC Admin'
admin.site.index_title = 'Administration Dashboard'