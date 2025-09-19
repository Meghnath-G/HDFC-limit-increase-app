# API Contracts: Card Limit Increase System

**Generated**: 2025-09-17 | **Feature**: 001-generate-a-flutter

## Base URL and Versioning
```
Base URL: https://api.hdfc-limits.com/api/v1
Content-Type: application/json
Authorization: Bearer <firebase_jwt_token>
```

## Common Response Format
```json
{
    "success": boolean,
    "data": object | array | null,
    "message": string,
    "request_id": string,
    "timestamp": string,
    "errors": array | null
}
```

## Authentication Endpoints

### POST /auth/register
**Purpose**: Register new customer with Firebase integration

**Request**:
```json
{
    "firebase_token": "string (required)",
    "name": "string (required, 2-100 chars)",
    "date_of_birth": "YYYY-MM-DD (required)",
    "email": "string (required, valid email)",
    "phone": "string (required, +91xxxxxxxxxx format)"
}
```

**Response 201 - Success**:
```json
{
    "success": true,
    "data": {
        "customer_id": "uuid",
        "name": "string",
        "email": "string",
        "phone": "string (masked)",
        "created_at": "ISO 8601 timestamp"
    },
    "message": "Customer registered successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

**Response 400 - Validation Error**:
```json
{
    "success": false,
    "data": null,
    "message": "Validation failed",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z",
    "errors": [
        {
            "field": "email",
            "message": "Email already exists"
        }
    ]
}
```

### POST /auth/login
**Purpose**: Validate Firebase token and get customer profile

**Request**:
```json
{
    "firebase_token": "string (required)"
}
```

**Response 200 - Success**:
```json
{
    "success": true,
    "data": {
        "customer_id": "uuid",
        "name": "string",
        "email": "string",
        "phone": "string (masked)",
        "is_active": boolean
    },
    "message": "Login successful",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

## Customer Management Endpoints

### GET /customers/profile
**Purpose**: Get customer profile information

**Headers**:
```
Authorization: Bearer <firebase_jwt_token>
```

**Response 200 - Success**:
```json
{
    "success": true,
    "data": {
        "customer_id": "uuid",
        "name": "string",
        "date_of_birth": "YYYY-MM-DD",
        "email": "string",
        "phone": "string (masked)",
        "created_at": "ISO 8601 timestamp",
        "card_details": [
            {
                "card_id": "uuid",
                "card_type": "credit|debit",
                "last4": "string",
                "expiry_month": number,
                "expiry_year": number,
                "current_limit": "decimal",
                "is_active": boolean
            }
        ]
    },
    "message": "Profile retrieved successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

### PUT /customers/profile
**Purpose**: Update customer profile information

**Request**:
```json
{
    "name": "string (optional)",
    "email": "string (optional)",
    "phone": "string (optional)"
}
```

**Response 200 - Success**:
```json
{
    "success": true,
    "data": {
        "customer_id": "uuid",
        "name": "string",
        "email": "string",
        "phone": "string (masked)",
        "updated_at": "ISO 8601 timestamp"
    },
    "message": "Profile updated successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

## Limit Request Endpoints

### POST /requests/submit
**Purpose**: Submit new limit increase request

**Request - Credit/Debit Card**:
```json
{
    "request_type": "credit_card|debit_card",
    "card_details": {
        "last4": "string (4 digits)",
        "expiry_month": number,
        "expiry_year": number
    },
    "requested_limit": "decimal (1000-1000000)"
}
```

**Request - NetBanking**:
```json
{
    "request_type": "netbanking",
    "netbanking_details": {
        "customer_id": "string",
        "password": "string"
    },
    "requested_limit": "decimal (1000-1000000)"
}
```

**Response 201 - Success**:
```json
{
    "success": true,
    "data": {
        "request_id": "uuid",
        "reference_number": "REQ-20250917-0001",
        "request_type": "credit_card|debit_card|netbanking",
        "current_limit": "decimal",
        "requested_limit": "decimal",
        "status": "pending",
        "submitted_at": "ISO 8601 timestamp",
        "expires_at": "ISO 8601 timestamp"
    },
    "message": "Limit increase request submitted successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

### GET /requests/history
**Purpose**: Get customer's limit request history

**Query Parameters**:
- `page`: number (default: 1)
- `limit`: number (default: 10, max: 50)
- `status`: string (optional filter)

**Response 200 - Success**:
```json
{
    "success": true,
    "data": {
        "requests": [
            {
                "request_id": "uuid",
                "reference_number": "string",
                "request_type": "credit_card|debit_card|netbanking",
                "requested_limit": "decimal",
                "status": "pending|under_review|approved|rejected|expired",
                "submitted_at": "ISO 8601 timestamp",
                "processed_at": "ISO 8601 timestamp (nullable)"
            }
        ],
        "pagination": {
            "current_page": number,
            "total_pages": number,
            "total_items": number,
            "has_next": boolean,
            "has_previous": boolean
        }
    },
    "message": "Request history retrieved successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

### GET /requests/status/{request_id}
**Purpose**: Get specific request status and details

**Response 200 - Success**:
```json
{
    "success": true,
    "data": {
        "request_id": "uuid",
        "reference_number": "string",
        "request_type": "credit_card|debit_card|netbanking",
        "current_limit": "decimal",
        "requested_limit": "decimal",
        "status": "pending|under_review|approved|rejected|expired",
        "submitted_at": "ISO 8601 timestamp",
        "processed_at": "ISO 8601 timestamp (nullable)",
        "expires_at": "ISO 8601 timestamp",
        "notes": "string (nullable)"
    },
    "message": "Request status retrieved successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

## OTP Management Endpoints

### POST /otp/send
**Purpose**: Generate and send OTP for verification

**Request**:
```json
{
    "purpose": "registration|login|request_verification",
    "channel": "sms|email",
    "limit_request_id": "uuid (optional, required for request_verification)"
}
```

**Response 200 - Success**:
```json
{
    "success": true,
    "data": {
        "otp_id": "uuid",
        "sent_to": "string (masked)",
        "channel": "sms|email",
        "expires_at": "ISO 8601 timestamp",
        "attempts_remaining": number
    },
    "message": "OTP sent successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

### POST /otp/verify
**Purpose**: Verify OTP code

**Request**:
```json
{
    "otp_id": "uuid",
    "otp_code": "string (6 digits)",
    "limit_request_id": "uuid (optional)"
}
```

**Response 200 - Success**:
```json
{
    "success": true,
    "data": {
        "verified": true,
        "verified_at": "ISO 8601 timestamp",
        "limit_request_id": "uuid (if applicable)"
    },
    "message": "OTP verified successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

**Response 400 - Invalid OTP**:
```json
{
    "success": false,
    "data": {
        "verified": false,
        "attempts_remaining": number,
        "locked_until": "ISO 8601 timestamp (nullable)"
    },
    "message": "Invalid OTP code",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z",
    "errors": [
        {
            "field": "otp_code",
            "message": "Invalid or expired OTP"
        }
    ]
}
```

## Notification Endpoints

### POST /notifications/send
**Purpose**: Send push notification to customer (Internal use)

**Request**:
```json
{
    "customer_id": "uuid",
    "notification_type": "status_update|otp_sent|login_alert",
    "title": "string",
    "message": "string",
    "data": {
        "limit_request_id": "uuid (optional)",
        "action": "string (optional)"
    }
}
```

**Response 200 - Success**:
```json
{
    "success": true,
    "data": {
        "notification_id": "uuid",
        "onesignal_id": "string",
        "delivery_status": "sent",
        "sent_at": "ISO 8601 timestamp"
    },
    "message": "Notification sent successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

## Error Response Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Invalid or missing Firebase token |
| 403 | Forbidden - Access denied to resource |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Duplicate request or constraint violation |
| 422 | Unprocessable Entity - Business logic validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - System error |

## Rate Limiting

| Endpoint | Rate Limit |
|----------|------------|
| Authentication | 10 requests/minute |
| OTP Operations | 5 requests/minute |
| Request Submission | 3 requests/hour |
| Profile Updates | 5 requests/minute |
| Other Endpoints | 60 requests/minute |

## Security Headers

All responses include security headers:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```