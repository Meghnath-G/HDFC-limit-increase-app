"""
OTP API Schema Documentation
===========================

OpenAPI schema definitions and examples for OTP verification endpoints.
"""

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status


# OTP Generation Examples
OTP_GENERATE_REQUEST_EXAMPLE = OpenApiExample(
    'OTP Generation Request',
    value={
        'purpose': 'login_verification',
        'delivery_method': 'sms',
        'contact_info': '+919876543210',
        'context': {
            'customer_id': 'CUST123456789',
            'device_id': 'device_12345',
            'ip_address': '192.168.1.100',
            'user_agent': 'HDFC Mobile App/1.0.0'
        },
        'preferences': {
            'language': 'en',
            'template': 'standard',
            'priority': 'normal'
        }
    },
    request_only=True
)

OTP_GENERATE_RESPONSE_EXAMPLE = OpenApiExample(
    'OTP Generation Response',
    value={
        'success': True,
        'data': {
            'otp_id': 'OTP123456789',
            'reference_number': 'REF987654321',
            'delivery_method': 'sms',
            'contact_info': '+91987654****',
            'expires_at': '2024-12-19T10:40:00Z',
            'max_attempts': 3,
            'retry_after': '2024-12-19T10:32:00Z',
            'delivery_status': 'sent',
            'estimated_delivery': '30 seconds'
        },
        'message': 'OTP sent successfully to your registered mobile number',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# Multi-channel OTP Examples
OTP_MULTICHANNEL_REQUEST_EXAMPLE = OpenApiExample(
    'Multi-channel OTP Request',
    value={
        'purpose': 'transaction_verification',
        'delivery_methods': ['sms', 'email'],
        'context': {
            'transaction_id': 'TXN123456789',
            'transaction_amount': 50000.00,
            'transaction_type': 'limit_increase_request',
            'customer_id': 'CUST123456789'
        },
        'fallback_enabled': True,
        'priority': 'high'
    },
    request_only=True
)

OTP_MULTICHANNEL_RESPONSE_EXAMPLE = OpenApiExample(
    'Multi-channel OTP Response',
    value={
        'success': True,
        'data': {
            'otp_id': 'OTP123456789',
            'delivery_channels': [
                {
                    'method': 'sms',
                    'contact': '+91987654****',
                    'status': 'sent',
                    'message_id': 'SMS123456'
                },
                {
                    'method': 'email',
                    'contact': 'cust****@example.com',
                    'status': 'sent',
                    'message_id': 'EMAIL123456'
                }
            ],
            'primary_channel': 'sms',
            'fallback_channels': ['email'],
            'expires_at': '2024-12-19T10:40:00Z',
            'max_attempts': 3
        },
        'message': 'OTP sent via multiple channels for verification',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# OTP Verification Examples
OTP_VERIFY_REQUEST_EXAMPLE = OpenApiExample(
    'OTP Verification Request',
    value={
        'otp_id': 'OTP123456789',
        'otp_code': '123456',
        'context': {
            'device_id': 'device_12345',
            'ip_address': '192.168.1.100',
            'user_agent': 'HDFC Mobile App/1.0.0'
        }
    },
    request_only=True
)

OTP_VERIFY_SUCCESS_RESPONSE_EXAMPLE = OpenApiExample(
    'OTP Verification Success Response',
    value={
        'success': True,
        'data': {
            'verification_status': 'verified',
            'otp_id': 'OTP123456789',
            'verified_at': '2024-12-19T10:35:00Z',
            'purpose': 'login_verification',
            'validity_duration': 300,
            'verification_token': 'VER_TOKEN_123456',
            'next_steps': [
                'Complete login process',
                'Proceed with requested action'
            ]
        },
        'message': 'OTP verified successfully',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:35:00Z'
    },
    response_only=True
)

OTP_VERIFY_FAILED_RESPONSE_EXAMPLE = OpenApiExample(
    'OTP Verification Failed Response',
    value={
        'success': False,
        'error': {
            'code': 'OTP_VERIFICATION_FAILED',
            'message': 'Invalid OTP code provided',
            'details': {
                'otp_id': 'OTP123456789',
                'attempts_remaining': 2,
                'max_attempts': 3,
                'next_retry_after': '2024-12-19T10:37:00Z',
                'expires_at': '2024-12-19T10:40:00Z',
                'can_resend': True
            }
        },
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:35:00Z'
    },
    response_only=True
)

# OTP Resend Examples
OTP_RESEND_REQUEST_EXAMPLE = OpenApiExample(
    'OTP Resend Request',
    value={
        'otp_id': 'OTP123456789',
        'delivery_method': 'email',
        'reason': 'not_received',
        'context': {
            'previous_attempts': 1,
            'customer_feedback': 'SMS not received after 5 minutes'
        }
    },
    request_only=True
)

OTP_RESEND_RESPONSE_EXAMPLE = OpenApiExample(
    'OTP Resend Response',
    value={
        'success': True,
        'data': {
            'otp_id': 'OTP123456789',
            'new_reference': 'REF987654322',
            'delivery_method': 'email',
            'contact_info': 'cust****@example.com',
            'resend_count': 1,
            'max_resends': 3,
            'expires_at': '2024-12-19T10:45:00Z',
            'delivery_status': 'sent',
            'estimated_delivery': '1-2 minutes'
        },
        'message': 'OTP resent successfully via email',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:35:00Z'
    },
    response_only=True
)

# Voice OTP Example
OTP_VOICE_REQUEST_EXAMPLE = OpenApiExample(
    'Voice OTP Request',
    value={
        'purpose': 'high_value_transaction',
        'delivery_method': 'voice',
        'contact_info': '+919876543210',
        'voice_preferences': {
            'language': 'en',
            'voice_type': 'female',
            'repeat_count': 2,
            'speech_rate': 'normal'
        },
        'context': {
            'transaction_amount': 100000.00,
            'urgency': 'high'
        }
    },
    request_only=True
)

# WhatsApp OTP Example
OTP_WHATSAPP_REQUEST_EXAMPLE = OpenApiExample(
    'WhatsApp OTP Request',
    value={
        'purpose': 'account_verification',
        'delivery_method': 'whatsapp',
        'contact_info': '+919876543210',
        'whatsapp_preferences': {
            'message_type': 'template',
            'media_support': True,
            'rich_content': True
        },
        'context': {
            'verification_type': 'account_activation',
            'customer_preference': 'whatsapp_preferred'
        }
    },
    request_only=True
)

# Schema Decorators
otp_generate_schema = extend_schema(
    operation_id='otp_generate',
    summary='Generate OTP',
    description='''
    Generate and send OTP for various verification purposes across multiple channels.
    
    This endpoint supports OTP generation for:
    - Login verification and authentication
    - Transaction verification and approval
    - Account changes and updates
    - Password reset and recovery
    - High-value transaction authorization
    
    **Delivery Channels:**
    - SMS: Quick delivery via SMS gateway
    - Email: Secure delivery with HTML templates
    - Voice: Automated voice call with OTP reading
    - WhatsApp: Rich message via WhatsApp Business API
    - Push: In-app push notification (fallback)
    
    **Purpose Types:**
    - login_verification: User authentication
    - transaction_verification: Transaction approval
    - password_reset: Password change verification
    - account_update: Profile/account changes
    - limit_increase: Limit change verification
    
    **Security Features:**
    - Rate limiting: Maximum 3 OTP requests per 5 minutes
    - IP tracking: Monitor and block suspicious requests
    - Device fingerprinting: Detect unusual devices
    - Attempt tracking: Log all generation attempts
    - Expiry management: Auto-expire after 10 minutes
    
    **Business Rules:**
    - OTP length: 6 digits for standard, 4 digits for voice
    - Validity: 10 minutes standard, 5 minutes for high-value
    - Retry limit: Maximum 3 verification attempts
    - Resend limit: Maximum 3 resends per session
    - Channel fallback: Auto-fallback if primary fails
    ''',
    examples=[
        OTP_GENERATE_REQUEST_EXAMPLE,
        OTP_MULTICHANNEL_REQUEST_EXAMPLE,
        OTP_VOICE_REQUEST_EXAMPLE,
        OTP_WHATSAPP_REQUEST_EXAMPLE,
        OTP_GENERATE_RESPONSE_EXAMPLE,
        OTP_MULTICHANNEL_RESPONSE_EXAMPLE
    ],
    tags=['OTP']
)

otp_verify_schema = extend_schema(
    operation_id='otp_verify',
    summary='Verify OTP',
    description='''
    Verify OTP code and complete the verification process for the intended purpose.
    
    This endpoint handles OTP verification with:
    - Code validation and expiry checking
    - Attempt counting and rate limiting
    - Purpose-specific validation logic
    - Security monitoring and fraud detection
    - Token generation for verified sessions
    
    **Verification Process:**
    1. Validate OTP format and length
    2. Check OTP expiry and attempts remaining
    3. Verify against generated code
    4. Update verification status
    5. Generate verification token if successful
    6. Log verification attempt for audit
    
    **Security Validations:**
    - IP address consistency check
    - Device fingerprint validation
    - Time-window verification
    - Rate limiting enforcement
    - Suspicious pattern detection
    
    **Success Actions:**
    - Mark OTP as verified
    - Generate verification token
    - Update customer verification status
    - Trigger completion workflows
    - Send confirmation notifications
    
    **Failure Handling:**
    - Decrement remaining attempts
    - Log failed verification
    - Apply progressive delays
    - Block after max attempts
    - Trigger security alerts if needed
    ''',
    examples=[
        OTP_VERIFY_REQUEST_EXAMPLE,
        OTP_VERIFY_SUCCESS_RESPONSE_EXAMPLE,
        OTP_VERIFY_FAILED_RESPONSE_EXAMPLE
    ],
    tags=['OTP']
)

otp_resend_schema = extend_schema(
    operation_id='otp_resend',
    summary='Resend OTP',
    description='''
    Resend OTP via same or different delivery method with enhanced delivery options.
    
    This endpoint provides flexible OTP resend capabilities:
    - Resend via same channel (if customer didn't receive)
    - Switch to alternative channel (if primary failed)
    - Enhanced delivery with priority routing
    - Intelligent channel selection based on success rates
    
    **Resend Scenarios:**
    - not_received: Customer didn't receive original OTP
    - delivery_failed: Technical delivery failure
    - expired: OTP expired before verification
    - channel_switch: Customer prefers different channel
    - priority_delivery: High-priority transaction needs faster delivery
    
    **Channel Switching:**
    - SMS to Email: If SMS delivery fails
    - Email to SMS: If email delivery is slow
    - Voice call: For high-value transactions
    - WhatsApp: If customer prefers rich messaging
    
    **Rate Limiting:**
    - Maximum 3 resends per OTP session
    - 2-minute delay between consecutive resends
    - Progressive delay: 2min, 5min, 10min intervals
    - Channel-specific limits to prevent abuse
    
    **Delivery Optimization:**
    - Intelligent routing based on delivery success rates
    - Priority queuing for high-value transactions
    - Fallback routing for failed primary channels
    - Real-time delivery status tracking
    ''',
    examples=[
        OTP_RESEND_REQUEST_EXAMPLE,
        OTP_RESEND_RESPONSE_EXAMPLE
    ],
    tags=['OTP']
)

# Export all OTP schema decorators
__all__ = [
    'otp_generate_schema',
    'otp_verify_schema',
    'otp_resend_schema',
    'OTP_GENERATE_REQUEST_EXAMPLE',
    'OTP_GENERATE_RESPONSE_EXAMPLE',
    'OTP_MULTICHANNEL_REQUEST_EXAMPLE',
    'OTP_MULTICHANNEL_RESPONSE_EXAMPLE',
    'OTP_VERIFY_REQUEST_EXAMPLE',
    'OTP_VERIFY_SUCCESS_RESPONSE_EXAMPLE',
    'OTP_VERIFY_FAILED_RESPONSE_EXAMPLE',
    'OTP_RESEND_REQUEST_EXAMPLE',
    'OTP_RESEND_RESPONSE_EXAMPLE',
    'OTP_VOICE_REQUEST_EXAMPLE',
    'OTP_WHATSAPP_REQUEST_EXAMPLE'
]