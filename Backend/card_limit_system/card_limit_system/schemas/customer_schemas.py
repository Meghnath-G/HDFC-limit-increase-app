"""
Customer API Schema Documentation
================================

OpenAPI schema definitions and examples for customer-related endpoints.
"""

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status


# Customer Registration Examples
CUSTOMER_REGISTRATION_REQUEST_EXAMPLE = OpenApiExample(
    'Customer Registration Request',
    value={
        'email': 'customer@example.com',
        'phone_number': '+919876543210',
        'first_name': 'John',
        'last_name': 'Doe',
        'date_of_birth': '1990-01-15',
        'pan_number': 'ABCDE1234F',
        'aadhaar_number': '1234-5678-9012',
        'address': {
            'street': '123 Main Street',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'pincode': '400001',
            'country': 'India'
        },
        'preferred_language': 'en',
        'communication_preferences': {
            'email': True,
            'sms': True,
            'push': True,
            'whatsapp': False
        }
    },
    request_only=True
)

CUSTOMER_REGISTRATION_RESPONSE_EXAMPLE = OpenApiExample(
    'Customer Registration Response',
    value={
        'success': True,
        'data': {
            'customer_id': 'CUST123456789',
            'email': 'customer@example.com',
            'phone_number': '+919876543210',
            'first_name': 'John',
            'last_name': 'Doe',
            'status': 'pending_verification',
            'created_at': '2024-12-19T10:30:00Z',
            'verification_required': {
                'email': True,
                'phone': True,
                'documents': ['pan', 'aadhaar']
            }
        },
        'message': 'Customer registration initiated successfully',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# Customer Login Examples
CUSTOMER_LOGIN_REQUEST_EXAMPLE = OpenApiExample(
    'Customer Login Request',
    value={
        'email': 'customer@example.com',
        'password': 'SecurePassword123!',
        'device_info': {
            'device_id': 'device_12345',
            'device_type': 'mobile',
            'os': 'android',
            'app_version': '1.0.0'
        }
    },
    request_only=True
)

CUSTOMER_LOGIN_RESPONSE_EXAMPLE = OpenApiExample(
    'Customer Login Response',
    value={
        'success': True,
        'data': {
            'access_token': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...',
            'refresh_token': 'refresh_token_here',
            'expires_in': 3600,
            'token_type': 'Bearer',
            'customer': {
                'customer_id': 'CUST123456789',
                'email': 'customer@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'status': 'active',
                'last_login': '2024-12-19T10:30:00Z'
            },
            'permissions': ['view_profile', 'request_limit_increase'],
            'mfa_required': False
        },
        'message': 'Login successful',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# Customer Profile Examples
CUSTOMER_PROFILE_RESPONSE_EXAMPLE = OpenApiExample(
    'Customer Profile Response',
    value={
        'success': True,
        'data': {
            'customer_id': 'CUST123456789',
            'email': 'customer@example.com',
            'phone_number': '+919876543210',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-15',
            'pan_number': 'ABCDE1234F',
            'kyc_status': 'verified',
            'address': {
                'street': '123 Main Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400001',
                'country': 'India'
            },
            'accounts': [
                {
                    'account_number': 'ACC12345678',
                    'account_type': 'savings',
                    'status': 'active',
                    'balance': 50000.00
                }
            ],
            'cards': [
                {
                    'card_number': '****-****-****-1234',
                    'card_type': 'credit',
                    'status': 'active',
                    'current_limit': 100000.00,
                    'available_limit': 75000.00
                }
            ],
            'preferences': {
                'preferred_language': 'en',
                'communication_preferences': {
                    'email': True,
                    'sms': True,
                    'push': True,
                    'whatsapp': False
                }
            },
            'last_login': '2024-12-19T10:30:00Z',
            'created_at': '2024-01-15T08:00:00Z',
            'updated_at': '2024-12-19T10:30:00Z'
        },
        'message': 'Customer profile retrieved successfully',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# Customer Profile Update Examples
CUSTOMER_PROFILE_UPDATE_REQUEST_EXAMPLE = OpenApiExample(
    'Customer Profile Update Request',
    value={
        'first_name': 'John',
        'last_name': 'Smith',
        'phone_number': '+919876543211',
        'address': {
            'street': '456 New Street',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'pincode': '400002',
            'country': 'India'
        },
        'preferences': {
            'preferred_language': 'hi',
            'communication_preferences': {
                'email': True,
                'sms': True,
                'push': True,
                'whatsapp': True
            }
        }
    },
    request_only=True
)

# Customer Verification Examples
CUSTOMER_VERIFICATION_REQUEST_EXAMPLE = OpenApiExample(
    'Customer Verification Request',
    value={
        'verification_type': 'email',
        'verification_code': '123456',
        'verification_id': 'VER123456789'
    },
    request_only=True
)

CUSTOMER_VERIFICATION_RESPONSE_EXAMPLE = OpenApiExample(
    'Customer Verification Response',
    value={
        'success': True,
        'data': {
            'verification_status': 'verified',
            'verification_type': 'email',
            'verified_at': '2024-12-19T10:30:00Z',
            'next_steps': ['verify_phone', 'upload_documents']
        },
        'message': 'Email verification completed successfully',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# Customer Schema Decorators
customer_registration_schema = extend_schema(
    operation_id='customer_register',
    summary='Register New Customer',
    description='''
    Register a new customer account with comprehensive profile information.
    
    This endpoint initiates the customer registration process, which includes:
    - Profile creation with personal and contact information
    - KYC document collection
    - Email and phone verification
    - Account setup and activation
    
    **Business Rules:**
    - Email must be unique across the system
    - Phone number must be valid Indian mobile number
    - PAN and Aadhaar numbers are required for KYC compliance
    - Customer status will be 'pending_verification' until verification is complete
    
    **Security:**
    - All sensitive data is encrypted at rest
    - Registration attempts are rate limited
    - Comprehensive audit logging is maintained
    
    **Next Steps:**
    After successful registration, customers must:
    1. Verify email address
    2. Verify phone number
    3. Upload KYC documents
    4. Complete account activation
    ''',
    examples=[
        CUSTOMER_REGISTRATION_REQUEST_EXAMPLE,
        CUSTOMER_REGISTRATION_RESPONSE_EXAMPLE
    ],
    tags=['Customers']
)

customer_login_schema = extend_schema(
    operation_id='customer_login',
    summary='Customer Authentication',
    description='''
    Authenticate customer and obtain access tokens for API access.
    
    This endpoint handles customer authentication with support for:
    - Email/password authentication
    - Device tracking and management
    - Multi-factor authentication (when enabled)
    - Session management and token issuance
    
    **Authentication Flow:**
    1. Validate email and password credentials
    2. Check account status and permissions
    3. Generate Firebase JWT tokens
    4. Track device information for security
    5. Apply MFA if required by account settings
    
    **Rate Limiting:**
    - Maximum 5 login attempts per 15 minutes per email
    - Account lockout after consecutive failed attempts
    - Device-based tracking for security monitoring
    
    **Response Tokens:**
    - access_token: Short-lived JWT for API authentication
    - refresh_token: Long-lived token for access token renewal
    - expires_in: Token validity period in seconds
    ''',
    examples=[
        CUSTOMER_LOGIN_REQUEST_EXAMPLE,
        CUSTOMER_LOGIN_RESPONSE_EXAMPLE
    ],
    tags=['Authentication']
)

customer_profile_schema = extend_schema(
    operation_id='customer_profile',
    summary='Get Customer Profile',
    description='''
    Retrieve comprehensive customer profile information including accounts and cards.
    
    This endpoint provides complete customer information including:
    - Personal and contact details
    - KYC verification status
    - Account and card information
    - Communication preferences
    - Activity history
    
    **Data Security:**
    - Sensitive information is masked (card numbers, account numbers)
    - Access is restricted to authenticated customer only
    - All access is logged for audit purposes
    
    **Response Data:**
    - customer_id: Unique customer identifier
    - Personal information (name, contact, address)
    - Account details with current balances
    - Card information with limits and availability
    - Preferences and settings
    - Verification and activity status
    ''',
    examples=[CUSTOMER_PROFILE_RESPONSE_EXAMPLE],
    tags=['Customers']
)

customer_profile_update_schema = extend_schema(
    operation_id='customer_profile_update',
    summary='Update Customer Profile',
    description='''
    Update customer profile information with validation and verification requirements.
    
    This endpoint allows customers to update:
    - Personal information (name, contact details)
    - Address and location information
    - Communication preferences
    - Language and notification settings
    
    **Validation Rules:**
    - Email updates require verification
    - Phone number updates require OTP verification
    - Address changes may require document verification
    - Critical changes trigger security notifications
    
    **Business Logic:**
    - Some changes may require approval workflow
    - Audit trail is maintained for all profile changes
    - Verification may be required for sensitive updates
    - Rate limiting applies to prevent abuse
    ''',
    examples=[CUSTOMER_PROFILE_UPDATE_REQUEST_EXAMPLE],
    tags=['Customers']
)

customer_verification_schema = extend_schema(
    operation_id='customer_verify',
    summary='Verify Customer Information',
    description='''
    Verify customer information using OTP or document verification.
    
    This endpoint handles various verification types:
    - Email verification with OTP
    - Phone number verification with SMS OTP
    - Document verification with uploaded files
    - Identity verification for KYC compliance
    
    **Verification Types:**
    - email: Verify email address with OTP
    - phone: Verify phone number with SMS OTP
    - document: Verify uploaded KYC documents
    - identity: Complete identity verification process
    
    **Security Features:**
    - OTP codes expire after 10 minutes
    - Maximum 3 verification attempts
    - Rate limiting to prevent abuse
    - Comprehensive audit logging
    ''',
    examples=[
        CUSTOMER_VERIFICATION_REQUEST_EXAMPLE,
        CUSTOMER_VERIFICATION_RESPONSE_EXAMPLE
    ],
    tags=['Customers']
)

# Export all customer schema decorators
__all__ = [
    'customer_registration_schema',
    'customer_login_schema',
    'customer_profile_schema',
    'customer_profile_update_schema',
    'customer_verification_schema',
    'CUSTOMER_REGISTRATION_REQUEST_EXAMPLE',
    'CUSTOMER_REGISTRATION_RESPONSE_EXAMPLE',
    'CUSTOMER_LOGIN_REQUEST_EXAMPLE',
    'CUSTOMER_LOGIN_RESPONSE_EXAMPLE',
    'CUSTOMER_PROFILE_RESPONSE_EXAMPLE',
    'CUSTOMER_PROFILE_UPDATE_REQUEST_EXAMPLE',
    'CUSTOMER_VERIFICATION_REQUEST_EXAMPLE',
    'CUSTOMER_VERIFICATION_RESPONSE_EXAMPLE'
]