"""
OpenAPI Specification Configuration for HDFC Card Limit System
=============================================================

This module configures the OpenAPI 3.0 specification using drf-spectacular
for comprehensive API documentation with authentication, examples, and schemas.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.conf import settings
from rest_framework import status


# OpenAPI Schema Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'HDFC Card Limit Increase System API',
    'DESCRIPTION': '''
# HDFC Card Limit Increase System API

A comprehensive REST API for HDFC Bank customers to request card and netbanking limit increases.

## Overview

The HDFC Card Limit Increase System provides a secure, scalable platform for:
- Customer authentication and profile management
- Card and netbanking limit increase requests
- Multi-channel OTP verification (SMS, Email, Voice, WhatsApp)
- Real-time notifications and status tracking
- Comprehensive analytics and reporting
- Administrative dashboard and controls

## Security

This API implements banking-grade security including:
- Firebase JWT authentication with custom claims
- Multi-factor authentication (MFA) with OTP verification
- Rate limiting and DDoS protection
- Field-level encryption for sensitive data
- Comprehensive audit logging
- PCI DSS Level 1 compliance

## Rate Limiting

API endpoints are protected with rate limiting:
- Authentication: 5 attempts per 15 minutes
- OTP requests: 3 requests per 5 minutes
- General API: 1000 requests per hour per user
- Limit requests: 5 requests per 24 hours per customer

## Response Format

All API responses follow a consistent format:
```json
{
    "success": true,
    "data": { ... },
    "message": "Operation completed successfully",
    "request_id": "req_1234567890",
    "timestamp": "2024-12-19T10:30:00Z"
}
```

Error responses include detailed error information:
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": { ... }
    },
    "request_id": "req_1234567890",
    "timestamp": "2024-12-19T10:30:00Z"
}
```

## Authentication

Most endpoints require Firebase JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <firebase_jwt_token>
```

## Pagination

List endpoints support cursor-based pagination:
```json
{
    "results": [...],
    "next": "cursor_token_for_next_page",
    "previous": "cursor_token_for_previous_page",
    "count": 150
}
```
''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'displayRequestDuration': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'filter': True,
        'tryItOutEnabled': True,
    },
    'REDOC_UI_SETTINGS': {
        'nativeScrollbars': True,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#004c97'  # HDFC Blue
                }
            }
        }
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': [],
    'SCHEMA_PATH_PREFIX': '/api/v1/',
    'SCHEMA_PATH_PREFIX_TRIM': True,
    'SERVERS': [
        {
            'url': 'https://card-limit-api.hdfc.com',
            'description': 'Production Server'
        },
        {
            'url': 'https://staging-card-limit-api.hdfc.com',
            'description': 'Staging Server'
        },
        {
            'url': 'http://localhost:8000',
            'description': 'Development Server'
        }
    ],
    'EXTERNAL_DOCS': {
        'description': 'HDFC Card Limit System Documentation',
        'url': 'https://docs.hdfc.com/card-limit-system/'
    },
    'TAGS': [
        {
            'name': 'Authentication',
            'description': 'User authentication and session management'
        },
        {
            'name': 'Customers',
            'description': 'Customer profile and account management'
        },
        {
            'name': 'Cards',
            'description': 'Credit and debit card information'
        },
        {
            'name': 'Requests',
            'description': 'Limit increase request management'
        },
        {
            'name': 'OTP',
            'description': 'One-time password verification'
        },
        {
            'name': 'Notifications',
            'description': 'Multi-channel notification delivery'
        },
        {
            'name': 'Analytics',
            'description': 'System metrics and reporting'
        },
        {
            'name': 'Admin',
            'description': 'Administrative functions and controls'
        }
    ],
    'CONTACT': {
        'name': 'HDFC Bank API Support',
        'url': 'https://support.hdfc.com/api',
        'email': 'api-support@hdfc.com'
    },
    'LICENSE': {
        'name': 'Proprietary',
        'url': 'https://hdfc.com/license'
    }
}


# Common OpenAPI Parameters
FIREBASE_TOKEN_PARAMETER = OpenApiParameter(
    name='Authorization',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.HEADER,
    required=True,
    description='Firebase JWT token. Format: Bearer <token>',
    examples=[
        OpenApiExample(
            'Valid Token',
            value='Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...',
            description='Valid Firebase JWT token'
        )
    ]
)

REQUEST_ID_PARAMETER = OpenApiParameter(
    name='X-Request-ID',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.HEADER,
    required=False,
    description='Optional request ID for tracking'
)

CORRELATION_ID_PARAMETER = OpenApiParameter(
    name='X-Correlation-ID',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.HEADER,
    required=False,
    description='Optional correlation ID for distributed tracing'
)

# Common Response Examples
SUCCESS_RESPONSE_EXAMPLE = OpenApiExample(
    'Success Response',
    value={
        'success': True,
        'data': {'id': 123, 'status': 'completed'},
        'message': 'Operation completed successfully',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

ERROR_RESPONSE_EXAMPLE = OpenApiExample(
    'Error Response',
    value={
        'success': False,
        'error': {
            'code': 'VALIDATION_ERROR',
            'message': 'Invalid input data',
            'details': {
                'field_name': ['This field is required.']
            }
        },
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

AUTHENTICATION_ERROR_EXAMPLE = OpenApiExample(
    'Authentication Error',
    value={
        'success': False,
        'error': {
            'code': 'AUTHENTICATION_FAILED',
            'message': 'Invalid or expired token',
            'details': {
                'token_status': 'expired',
                'required_action': 'refresh_token'
            }
        },
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

RATE_LIMIT_ERROR_EXAMPLE = OpenApiExample(
    'Rate Limit Error',
    value={
        'success': False,
        'error': {
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Too many requests',
            'details': {
                'limit': 1000,
                'window': '1 hour',
                'retry_after': 3600
            }
        },
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# Security Schemes
SECURITY_SCHEMES = {
    'FirebaseAuth': {
        'type': 'http',
        'scheme': 'bearer',
        'bearerFormat': 'JWT',
        'description': 'Firebase JWT token authentication'
    },
    'ApiKeyAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-Key',
        'description': 'API key for server-to-server authentication'
    }
}


def get_error_responses():
    """Get common error responses for API endpoints."""
    return {
        400: {
            'description': 'Bad Request - Invalid input data',
            'examples': {
                'application/json': {
                    'summary': 'Validation Error',
                    'value': {
                        'success': False,
                        'error': {
                            'code': 'VALIDATION_ERROR',
                            'message': 'Invalid input data',
                            'details': {
                                'field_name': ['This field is required.']
                            }
                        },
                        'request_id': 'req_1234567890',
                        'timestamp': '2024-12-19T10:30:00Z'
                    }
                }
            }
        },
        401: {
            'description': 'Unauthorized - Authentication required',
            'examples': {
                'application/json': {
                    'summary': 'Authentication Required',
                    'value': {
                        'success': False,
                        'error': {
                            'code': 'AUTHENTICATION_REQUIRED',
                            'message': 'Authentication credentials were not provided',
                            'details': {
                                'required_header': 'Authorization: Bearer <token>'
                            }
                        },
                        'request_id': 'req_1234567890',
                        'timestamp': '2024-12-19T10:30:00Z'
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Insufficient permissions',
            'examples': {
                'application/json': {
                    'summary': 'Permission Denied',
                    'value': {
                        'success': False,
                        'error': {
                            'code': 'PERMISSION_DENIED',
                            'message': 'You do not have permission to perform this action',
                            'details': {
                                'required_permission': 'admin_access'
                            }
                        },
                        'request_id': 'req_1234567890',
                        'timestamp': '2024-12-19T10:30:00Z'
                    }
                }
            }
        },
        404: {
            'description': 'Not Found - Resource does not exist',
            'examples': {
                'application/json': {
                    'summary': 'Resource Not Found',
                    'value': {
                        'success': False,
                        'error': {
                            'code': 'NOT_FOUND',
                            'message': 'The requested resource was not found',
                            'details': {
                                'resource_type': 'customer',
                                'resource_id': '12345'
                            }
                        },
                        'request_id': 'req_1234567890',
                        'timestamp': '2024-12-19T10:30:00Z'
                    }
                }
            }
        },
        429: {
            'description': 'Too Many Requests - Rate limit exceeded',
            'examples': {
                'application/json': {
                    'summary': 'Rate Limit Exceeded',
                    'value': {
                        'success': False,
                        'error': {
                            'code': 'RATE_LIMIT_EXCEEDED',
                            'message': 'Too many requests',
                            'details': {
                                'limit': 1000,
                                'window': '1 hour',
                                'retry_after': 3600
                            }
                        },
                        'request_id': 'req_1234567890',
                        'timestamp': '2024-12-19T10:30:00Z'
                    }
                }
            }
        },
        500: {
            'description': 'Internal Server Error',
            'examples': {
                'application/json': {
                    'summary': 'Server Error',
                    'value': {
                        'success': False,
                        'error': {
                            'code': 'INTERNAL_ERROR',
                            'message': 'An internal server error occurred',
                            'details': {
                                'error_id': 'err_1234567890',
                                'contact_support': True
                            }
                        },
                        'request_id': 'req_1234567890',
                        'timestamp': '2024-12-19T10:30:00Z'
                    }
                }
            }
        }
    }


def get_authenticated_responses():
    """Get responses that require authentication."""
    return {
        **get_error_responses(),
        401: {
            'description': 'Unauthorized - Invalid or expired token',
            'examples': {
                'application/json': {
                    'summary': 'Token Expired',
                    'value': {
                        'success': False,
                        'error': {
                            'code': 'TOKEN_EXPIRED',
                            'message': 'Authentication token has expired',
                            'details': {
                                'expired_at': '2024-12-19T09:30:00Z',
                                'required_action': 'refresh_token'
                            }
                        },
                        'request_id': 'req_1234567890',
                        'timestamp': '2024-12-19T10:30:00Z'
                    }
                }
            }
        }
    }


def extend_schema_with_examples(operation_id, description, examples=None, **kwargs):
    """
    Extended schema decorator with common examples and responses.
    
    Args:
        operation_id: Unique operation identifier
        description: Operation description
        examples: Dictionary of request/response examples
        **kwargs: Additional extend_schema arguments
    
    Returns:
        Configured extend_schema decorator
    """
    if examples is None:
        examples = {}
    
    # Add common examples
    if 'success' not in examples:
        examples['success'] = SUCCESS_RESPONSE_EXAMPLE
    
    if 'error' not in examples:
        examples['error'] = ERROR_RESPONSE_EXAMPLE
    
    return extend_schema(
        operation_id=operation_id,
        description=description,
        examples=list(examples.values()),
        **kwargs
    )


# API Version Configuration
API_VERSION = 'v1'
API_BASE_PATH = f'/api/{API_VERSION}/'

# Documentation URLs
DOCS_URLS = {
    'swagger': f'{API_BASE_PATH}docs/',
    'redoc': f'{API_BASE_PATH}redoc/',
    'schema': f'{API_BASE_PATH}schema/',
    'schema_yaml': f'{API_BASE_PATH}schema.yaml',
    'schema_json': f'{API_BASE_PATH}schema.json'
}

# Export configuration for Django settings
__all__ = [
    'SPECTACULAR_SETTINGS',
    'FIREBASE_TOKEN_PARAMETER',
    'REQUEST_ID_PARAMETER',
    'CORRELATION_ID_PARAMETER',
    'SUCCESS_RESPONSE_EXAMPLE',
    'ERROR_RESPONSE_EXAMPLE',
    'AUTHENTICATION_ERROR_EXAMPLE',
    'RATE_LIMIT_ERROR_EXAMPLE',
    'SECURITY_SCHEMES',
    'get_error_responses',
    'get_authenticated_responses',
    'extend_schema_with_examples',
    'API_VERSION',
    'API_BASE_PATH',
    'DOCS_URLS'
]