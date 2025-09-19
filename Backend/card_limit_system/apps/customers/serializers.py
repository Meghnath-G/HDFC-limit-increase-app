"""
Django REST Framework serializers for Customer models.

Provides secure data serialization with proper validation,
encryption handling, and banking compliance features.
"""

from rest_framework import serializers
from django.core.validators import RegexValidator, EmailValidator
from django.contrib.auth.password_validation import validate_password
from .models import Customer, CardDetail
from core.utils import encrypt_field, decrypt_field, validate_phone_format, validate_email_format


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for customer registration with validation and security.
    
    Handles new customer creation with Firebase UID integration
    and proper PII encryption.
    """
    
    # Input fields (plain text for validation)
    email_plain = serializers.EmailField(write_only=True, source='email')
    phone_plain = serializers.CharField(
        max_length=15,
        write_only=True,
        source='phone',
        validators=[
            RegexValidator(
                regex=r'^\+91[6-9]\d{9}$',
                message="Phone number must be in +91XXXXXXXXXX format with valid Indian mobile number"
            )
        ]
    )
    
    # Confirmation fields
    confirm_email = serializers.EmailField(write_only=True)
    confirm_phone = serializers.CharField(max_length=15, write_only=True)
    
    # Terms acceptance
    accept_terms = serializers.BooleanField(write_only=True)
    accept_privacy = serializers.BooleanField(write_only=True)
    
    # Read-only fields for response
    customer_id = serializers.CharField(read_only=True)
    masked_email = serializers.SerializerMethodField()
    masked_phone = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'firebase_uid', 'name', 'date_of_birth', 'customer_id',
            'email_plain', 'phone_plain', 'confirm_email', 'confirm_phone',
            'accept_terms', 'accept_privacy', 'masked_email', 'masked_phone',
            'age', 'is_email_verified', 'is_phone_verified', 'is_kyc_completed',
            'is_active', 'created_at'
        ]
        read_only_fields = [
            'id', 'customer_id', 'is_email_verified', 'is_phone_verified',
            'is_kyc_completed', 'is_active', 'created_at'
        ]
        extra_kwargs = {
            'firebase_uid': {'write_only': True},
            'name': {
                'validators': [
                    RegexValidator(
                        regex=r'^[a-zA-Z\s]{2,100}$',
                        message="Name must contain only letters and spaces, 2-100 characters"
                    )
                ]
            }
        }
    
    def get_masked_email(self, obj):
        """Return masked email for display."""
        return obj.get_masked_email()
    
    def get_masked_phone(self, obj):
        """Return masked phone for display."""
        return obj.get_masked_phone()
    
    def get_age(self, obj):
        """Return calculated age."""
        return obj.age
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Validate email confirmation
        if attrs.get('email') != attrs.get('confirm_email'):
            raise serializers.ValidationError({
                'confirm_email': 'Email addresses do not match.'
            })
        
        # Validate phone confirmation
        if attrs.get('phone') != attrs.get('confirm_phone'):
            raise serializers.ValidationError({
                'confirm_phone': 'Phone numbers do not match.'
            })
        
        # Validate terms acceptance
        if not attrs.get('accept_terms'):
            raise serializers.ValidationError({
                'accept_terms': 'You must accept the terms and conditions.'
            })
        
        if not attrs.get('accept_privacy'):
            raise serializers.ValidationError({
                'accept_privacy': 'You must accept the privacy policy.'
            })
        
        # Validate age (18+)
        from datetime import date
        if attrs.get('date_of_birth'):
            today = date.today()
            age = today.year - attrs['date_of_birth'].year - (
                (today.month, today.day) < (attrs['date_of_birth'].month, attrs['date_of_birth'].day)
            )
            if age < 18:
                raise serializers.ValidationError({
                    'date_of_birth': 'Customer must be at least 18 years old.'
                })
        
        # Remove confirmation fields before saving
        attrs.pop('confirm_email', None)
        attrs.pop('confirm_phone', None)
        attrs.pop('accept_terms', None)
        attrs.pop('accept_privacy', None)
        
        return attrs
    
    def validate_firebase_uid(self, value):
        """Validate Firebase UID uniqueness and format."""
        if Customer.objects.filter(firebase_uid=value).exists():
            raise serializers.ValidationError("Customer with this Firebase UID already exists.")
        
        if len(value) < 10 or len(value) > 128:
            raise serializers.ValidationError("Invalid Firebase UID format.")
        
        return value
    
    def validate_email_plain(self, value):
        """Validate email format and uniqueness."""
        # Check if email already exists (need to check encrypted values)
        encrypted_email = encrypt_field(value)
        if Customer.objects.filter(email=encrypted_email).exists():
            raise serializers.ValidationError("Customer with this email already exists.")
        
        return value
    
    def validate_phone_plain(self, value):
        """Validate phone format and uniqueness."""
        # Check if phone already exists (need to check encrypted values)
        encrypted_phone = encrypt_field(value)
        if Customer.objects.filter(phone=encrypted_phone).exists():
            raise serializers.ValidationError("Customer with this phone number already exists.")
        
        return value
    
    def create(self, validated_data):
        """Create customer with auto-generated customer ID."""
        # Generate unique customer ID
        import random
        import string
        
        def generate_customer_id():
            prefix = "HDFC"
            suffix = ''.join(random.choices(string.digits, k=8))
            return f"{prefix}{suffix}"
        
        # Ensure unique customer ID
        while True:
            customer_id = generate_customer_id()
            if not Customer.objects.filter(customer_id=customer_id).exists():
                break
        
        validated_data['customer_id'] = customer_id
        
        # The model's save method will handle encryption
        return super().create(validated_data)


class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for customer profile display and updates.
    
    Provides masked PII data for security while allowing
    safe profile updates.
    """
    
    masked_email = serializers.SerializerMethodField()
    masked_phone = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    card_count = serializers.SerializerMethodField()
    active_requests_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'customer_id', 'name', 'date_of_birth', 'age',
            'masked_email', 'masked_phone', 'is_email_verified',
            'is_phone_verified', 'is_kyc_completed', 'is_active',
            'card_count', 'active_requests_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'customer_id', 'masked_email', 'masked_phone', 'age',
            'is_email_verified', 'is_phone_verified', 'is_kyc_completed',
            'is_active', 'card_count', 'active_requests_count',
            'created_at', 'updated_at'
        ]
    
    def get_masked_email(self, obj):
        """Return masked email for display."""
        return obj.get_masked_email()
    
    def get_masked_phone(self, obj):
        """Return masked phone for display."""
        return obj.get_masked_phone()
    
    def get_age(self, obj):
        """Return calculated age."""
        return obj.age
    
    def get_card_count(self, obj):
        """Return number of active cards."""
        return obj.card_details.filter(is_active=True).count()
    
    def get_active_requests_count(self, obj):
        """Return number of active limit requests."""
        return obj.limit_requests.filter(
            status__in=['pending', 'under_review']
        ).count()


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for customer profile updates.
    
    Allows limited profile updates with proper validation
    and security checks.
    """
    
    class Meta:
        model = Customer
        fields = ['name', 'date_of_birth']
        
    def validate_name(self, value):
        """Validate name format."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        
        # Check for valid characters
        import re
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Name must contain only letters and spaces.")
        
        return value.strip().title()
    
    def validate_date_of_birth(self, value):
        """Validate date of birth."""
        from datetime import date
        
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age < 18:
            raise serializers.ValidationError("Customer must be at least 18 years old.")
        
        if age > 120:
            raise serializers.ValidationError("Invalid date of birth.")
        
        return value


class CardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for card details with PCI DSS compliance.
    
    Only exposes safe card information (last 4 digits, expiry)
    and never full card numbers.
    """
    
    masked_card_number = serializers.SerializerMethodField()
    expiry_display = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    last4_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CardDetail
        fields = [
            'id', 'card_type', 'masked_card_number', 'last4_display',
            'expiry_display', 'is_expired', 'current_limit',
            'is_active', 'created_at'
        ]
        read_only_fields = [
            'id', 'masked_card_number', 'last4_display', 'expiry_display',
            'is_expired', 'created_at'
        ]
    
    def get_masked_card_number(self, obj):
        """Return masked card number for display."""
        return obj.get_masked_card_number()
    
    def get_expiry_display(self, obj):
        """Return formatted expiry date."""
        return f"{obj.expiry_month:02d}/{obj.expiry_year}"
    
    def get_is_expired(self, obj):
        """Return expiry status."""
        return obj.is_expired()
    
    def get_last4_display(self, obj):
        """Return decrypted last 4 digits."""
        return obj.get_decrypted_last4()


class CardRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering new cards with validation.
    
    Handles secure card registration with proper validation
    and PCI DSS compliance.
    """
    
    # Input field for last 4 digits validation
    last4_input = serializers.CharField(
        max_length=4,
        min_length=4,
        write_only=True,
        source='last4',
        validators=[
            RegexValidator(
                regex=r'^\d{4}$',
                message="Last 4 digits must be exactly 4 numeric digits"
            )
        ]
    )
    
    # Token ID from bank system (optional)
    token_id_input = serializers.CharField(
        max_length=100,
        required=False,
        write_only=True,
        source='token_id'
    )
    
    class Meta:
        model = CardDetail
        fields = [
            'card_type', 'last4_input', 'expiry_month', 'expiry_year',
            'current_limit', 'token_id_input'
        ]
        extra_kwargs = {
            'current_limit': {'min_value': 0, 'max_value': 10000000}
        }
    
    def validate_expiry_month(self, value):
        """Validate expiry month."""
        if not (1 <= value <= 12):
            raise serializers.ValidationError("Expiry month must be between 1 and 12.")
        return value
    
    def validate_expiry_year(self, value):
        """Validate expiry year."""
        from datetime import date
        current_year = date.today().year
        
        if not (current_year <= value <= current_year + 10):
            raise serializers.ValidationError(
                f"Expiry year must be between {current_year} and {current_year + 10}."
            )
        return value
    
    def validate(self, attrs):
        """Cross-field validation for card expiry."""
        from datetime import date
        
        expiry_month = attrs.get('expiry_month')
        expiry_year = attrs.get('expiry_year')
        
        if expiry_month and expiry_year:
            # Check if card is already expired
            today = date.today()
            
            # Card expires at end of expiry month
            if expiry_year < today.year or (expiry_year == today.year and expiry_month < today.month):
                raise serializers.ValidationError("Cannot register an expired card.")
        
        return attrs
    
    def create(self, validated_data):
        """Create card detail with customer association."""
        customer = self.context['customer']
        validated_data['customer'] = customer
        
        # Check for duplicate cards (same last4 and expiry)
        existing_card = CardDetail.objects.filter(
            customer=customer,
            last4=encrypt_field(validated_data['last4']),
            expiry_month=validated_data['expiry_month'],
            expiry_year=validated_data['expiry_year']
        ).first()
        
        if existing_card:
            raise serializers.ValidationError({
                'non_field_errors': ['This card is already registered.']
            })
        
        return super().create(validated_data)


class CustomerCardsSerializer(serializers.ModelSerializer):
    """
    Serializer for customer with their cards.
    
    Provides comprehensive customer view including
    all associated card details.
    """
    
    cards = CardDetailSerializer(source='card_details', many=True, read_only=True)
    masked_email = serializers.SerializerMethodField()
    masked_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'customer_id', 'name', 'masked_email', 'masked_phone',
            'is_kyc_completed', 'cards'
        ]
        read_only_fields = ['id', 'customer_id', 'masked_email', 'masked_phone']
    
    def get_masked_email(self, obj):
        """Return masked email for display."""
        return obj.get_masked_email()
    
    def get_masked_phone(self, obj):
        """Return masked phone for display."""
        return obj.get_masked_phone()


class CustomerSearchSerializer(serializers.Serializer):
    """
    Serializer for customer search functionality.
    
    Provides secure search capabilities without exposing
    sensitive customer information.
    """
    
    query = serializers.CharField(max_length=100, required=True)
    search_type = serializers.ChoiceField(
        choices=[
            ('customer_id', 'Customer ID'),
            ('name', 'Name'),
            ('phone_last4', 'Last 4 digits of phone'),
        ],
        default='customer_id'
    )
    
    def validate_query(self, value):
        """Validate search query."""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Search query must be at least 2 characters long.")
        
        # Sanitize input
        from core.utils import sanitize_input
        return sanitize_input(value)
    
    def validate(self, attrs):
        """Cross-field validation for search."""
        query = attrs.get('query', '').strip()
        search_type = attrs.get('search_type')
        
        if search_type == 'customer_id':
            # Validate customer ID format
            if not query.startswith('HDFC') or len(query) != 12:
                raise serializers.ValidationError({
                    'query': 'Customer ID must be in HDFCXXXXXXXX format.'
                })
        
        elif search_type == 'phone_last4':
            # Validate last 4 digits format
            if not query.isdigit() or len(query) != 4:
                raise serializers.ValidationError({
                    'query': 'Phone last 4 digits must be exactly 4 numeric digits.'
                })
        
        elif search_type == 'name':
            # Validate name format
            import re
            if not re.match(r'^[a-zA-Z\s]+$', query):
                raise serializers.ValidationError({
                    'query': 'Name search must contain only letters and spaces.'
                })
        
        return attrs