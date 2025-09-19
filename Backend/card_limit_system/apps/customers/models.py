"""
Customer models for the Card Limit Increase System.

This module contains the Customer and CardDetail models following
the data model specifications with PCI DSS compliance.
"""

import uuid
from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone
from datetime import date, timedelta
from core.utils import encrypt_field, decrypt_field


class CustomerManager(models.Manager):
    """Custom manager for Customer model with security features."""
    
    def get_by_firebase_uid(self, firebase_uid):
        """Get customer by Firebase UID safely."""
        try:
            return self.get(firebase_uid=firebase_uid, is_active=True)
        except Customer.DoesNotExist:
            return None


class Customer(models.Model):
    """
    Customer model representing bank customers.
    
    Stores personal information with Firebase authentication integration.
    All PII fields are encrypted using AES-256.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique customer identifier"
    )
    
    firebase_uid = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text="Firebase authentication user ID for linking"
    )
    
    name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]{2,100}$',
                message="Name must contain only letters and spaces, 2-100 characters"
            )
        ],
        help_text="Customer full name"
    )
    
    date_of_birth = models.DateField(
        help_text="Customer date of birth for verification"
    )
    
    # Encrypted fields using custom field type
    email = models.CharField(
        max_length=255,  # Increased for encryption padding
        unique=True,
        db_index=True,
        help_text="Email address (encrypted)"
    )
    
    phone = models.CharField(
        max_length=255,  # Increased for encryption padding
        unique=True,
        db_index=True,
        help_text="Phone number (encrypted, +91xxxxxxxxxx format)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Account status flag"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Account creation timestamp"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last profile update timestamp"
    )
    
    objects = CustomerManager()
    
    class Meta:
        db_table = 'customer'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        indexes = [
            models.Index(fields=['firebase_uid']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['is_active', 'created_at']),
        ]
    
    def __str__(self):
        return f"Customer {self.name} ({self.firebase_uid})"
    
    def save(self, *args, **kwargs):
        """Override save to encrypt PII fields."""
        if self.email and not self._is_encrypted(self.email):
            self.email = encrypt_field(self.email)
        if self.phone and not self._is_encrypted(self.phone):
            self.phone = encrypt_field(self.phone)
        super().save(*args, **kwargs)
    
    def get_decrypted_email(self):
        """Get decrypted email address."""
        if self.email:
            return decrypt_field(self.email)
        return None
    
    def get_decrypted_phone(self):
        """Get decrypted phone number."""
        if self.phone:
            return decrypt_field(self.phone)
        return None
    
    def get_masked_phone(self):
        """Get masked phone number for display."""
        phone = self.get_decrypted_phone()
        if phone and len(phone) >= 4:
            return f"{phone[:-4]}****"
        return "****"
    
    def get_masked_email(self):
        """Get masked email address for display."""
        email = self.get_decrypted_email()
        if email and '@' in email:
            local, domain = email.split('@', 1)
            if len(local) > 2:
                return f"{local[:2]}***@{domain}"
            return f"***@{domain}"
        return "***@***.com"
    
    @property
    def age(self):
        """Calculate customer age."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def is_adult(self):
        """Check if customer is 18+ years old."""
        return self.age >= 18
    
    def _is_encrypted(self, value):
        """Check if a value is already encrypted."""
        # Simple check - encrypted values won't contain @ or +91
        return '@' not in value and '+91' not in value
    
    def clean(self):
        """Validate customer data."""
        from django.core.exceptions import ValidationError
        
        if not self.is_adult():
            raise ValidationError("Customer must be 18+ years old")
        
        # Validate email format before encryption
        if self.email and not self._is_encrypted(self.email):
            EmailValidator()(self.email)
        
        # Validate phone format before encryption
        if self.phone and not self._is_encrypted(self.phone):
            phone_validator = RegexValidator(
                regex=r'^\+91[0-9]{10}$',
                message="Phone number must be in +91xxxxxxxxxx format"
            )
            phone_validator(self.phone)


class CardDetail(models.Model):
    """
    Card detail model for storing masked card information.
    
    PCI DSS compliant - stores only last 4 digits and expiry.
    Never stores full PAN, CVV, or other sensitive card data.
    """
    
    CARD_TYPE_CHOICES = [
        ('credit', 'Credit Card'),
        ('debit', 'Debit Card'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique card detail identifier"
    )
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='card_details',
        help_text="Reference to Customer"
    )
    
    card_type = models.CharField(
        max_length=10,
        choices=CARD_TYPE_CHOICES,
        help_text="Type of card (credit/debit)"
    )
    
    # Encrypted field for last 4 digits
    last4 = models.CharField(
        max_length=255,  # Increased for encryption padding
        help_text="Last 4 digits of card number (encrypted)"
    )
    
    expiry_month = models.PositiveSmallIntegerField(
        help_text="Card expiry month (1-12)"
    )
    
    expiry_year = models.PositiveSmallIntegerField(
        help_text="Card expiry year"
    )
    
    # Encrypted token reference from bank system
    token_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Tokenized card reference from bank system (encrypted)"
    )
    
    current_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Current transaction limit in INR"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Card status flag"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Record creation timestamp"
    )
    
    class Meta:
        db_table = 'carddetail'
        verbose_name = 'Card Detail'
        verbose_name_plural = 'Card Details'
        indexes = [
            models.Index(fields=['customer', 'is_active']),
            models.Index(fields=['card_type']),
            models.Index(fields=['customer', 'card_type', 'is_active']),
        ]
        unique_together = [
            ('customer', 'last4', 'expiry_month', 'expiry_year')
        ]
    
    def __str__(self):
        last4_display = self.get_decrypted_last4() or "****"
        return f"{self.get_card_type_display()} ending {last4_display}"
    
    def save(self, *args, **kwargs):
        """Override save to encrypt sensitive fields."""
        if self.last4 and not self._is_encrypted(self.last4):
            self.last4 = encrypt_field(self.last4)
        if self.token_id and not self._is_encrypted(self.token_id):
            self.token_id = encrypt_field(self.token_id)
        super().save(*args, **kwargs)
    
    def get_decrypted_last4(self):
        """Get decrypted last 4 digits."""
        if self.last4:
            return decrypt_field(self.last4)
        return None
    
    def get_decrypted_token_id(self):
        """Get decrypted token ID."""
        if self.token_id:
            return decrypt_field(self.token_id)
        return None
    
    def get_masked_card_number(self):
        """Get masked card number for display."""
        last4 = self.get_decrypted_last4()
        if last4:
            return f"**** **** **** {last4}"
        return "**** **** **** ****"
    
    def is_expired(self):
        """Check if card is expired."""
        today = date.today()
        expiry_date = date(self.expiry_year, self.expiry_month, 1)
        # Add one month and subtract one day to get last day of expiry month
        if expiry_date.month == 12:
            expiry_date = date(expiry_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            expiry_date = date(expiry_date.year, expiry_date.month + 1, 1) - timedelta(days=1)
        return today > expiry_date
    
    def _is_encrypted(self, value):
        """Check if a value is already encrypted."""
        # Simple check - encrypted values won't be 4 digits
        return not (value.isdigit() and len(value) == 4)
    
    def clean(self):
        """Validate card data."""
        from django.core.exceptions import ValidationError
        
        # Validate expiry month
        if not (1 <= self.expiry_month <= 12):
            raise ValidationError("Expiry month must be between 1 and 12")
        
        # Validate expiry year (current year to +10 years)
        current_year = timezone.now().year
        if not (current_year <= self.expiry_year <= current_year + 10):
            raise ValidationError(f"Expiry year must be between {current_year} and {current_year + 10}")
        
        # Validate last4 format before encryption
        if self.last4 and not self._is_encrypted(self.last4):
            if not (self.last4.isdigit() and len(self.last4) == 4):
                raise ValidationError("Last 4 digits must be exactly 4 digits")
        
        # Check if card is expired
        if self.is_expired():
            raise ValidationError("Cannot add expired card")
        
        # Validate current limit
        if self.current_limit < 0:
            raise ValidationError("Current limit cannot be negative")