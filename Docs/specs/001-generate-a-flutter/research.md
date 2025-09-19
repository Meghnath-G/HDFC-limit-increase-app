# Research: Card Limit Increase System

**Generated**: 2025-09-17 | **Feature**: 001-generate-a-flutter

## Research Summary
This document consolidates technical research for implementing a secure, production-ready Card Limit Increase System with Flutter frontend and Django backend.

## Firebase Authentication Integration

**Decision**: Use Firebase Admin SDK in Django with custom authentication backend
**Rationale**: 
- Seamless token validation between Flutter and Django
- Built-in security features and token refresh handling
- Scalable user management with minimal custom code
- Industry-standard JWT implementation

**Alternatives Considered**:
- Custom JWT implementation: Rejected due to security complexity
- Django built-in auth: Rejected due to mobile app requirements
- OAuth 2.0 providers: Rejected due to Firebase ecosystem benefits

**Implementation Pattern**:
```python
# Django: Firebase token validation middleware
from firebase_admin import auth, initialize_app

class FirebaseAuthenticationBackend:
    def authenticate(self, request, token=None):
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            # Link to Customer model via firebase_uid
        except Exception:
            return None
```

## Oracle Database Optimization

**Decision**: Use cx_Oracle with connection pooling and prepared statements
**Rationale**:
- Native Oracle driver for optimal performance
- Connection pooling reduces latency for mobile API calls
- Prepared statements prevent SQL injection
- Supports Oracle-specific features like encryption

**Alternatives Considered**:
- SQLAlchemy ORM: Added for development speed while keeping cx_Oracle
- Generic database drivers: Rejected due to Oracle-specific requirements

**Implementation Pattern**:
```python
# Django settings optimization
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'xe',  # Oracle service name
        'OPTIONS': {
            'threaded': True,
            'use_returning_into': False,
        },
        'CONN_MAX_AGE': 300,  # Connection pooling
    }
}
```

## OneSignal Push Notifications

**Decision**: OneSignal REST API for backend, OneSignal Flutter SDK for frontend
**Rationale**:
- Cross-platform support (Android/iOS future)
- Rich notification features (action buttons, deep linking)
- Delivery analytics and retry mechanisms
- User segmentation capabilities

**Alternatives Considered**:
- Firebase Cloud Messaging: Rejected due to OneSignal requirement
- Custom push service: Rejected due to complexity

**Implementation Pattern**:
```dart
// Flutter: OneSignal initialization
OneSignal.shared.setAppId("YOUR_ONESIGNAL_APP_ID");
OneSignal.shared.setNotificationWillShowInForegroundHandler((OSNotificationReceivedEvent event) {
    // Handle foreground notifications
});

// Django: Trigger notifications
import requests

def send_push_notification(user_id, message, data={}):
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": "Basic YOUR_REST_API_KEY"
    }
    payload = {
        "app_id": "YOUR_ONESIGNAL_APP_ID",
        "filters": [{"field": "tag", "key": "user_id", "relation": "=", "value": user_id}],
        "contents": {"en": message},
        "data": data
    }
    requests.post("https://onesignal.com/api/v1/notifications", headers=headers, json=payload)
```

## Twilio Verify API Integration

**Decision**: Twilio Verify API for OTP generation and validation
**Rationale**:
- Built-in OTP lifecycle management (generation, delivery, expiry)
- Multiple delivery channels (SMS, email, voice)
- Automatic retry and fallback mechanisms
- Compliance with telecom regulations

**Alternatives Considered**:
- Custom OTP generation: Rejected due to security and delivery complexity
- Alternative SMS providers: Rejected due to Twilio requirement

**Implementation Pattern**:
```python
# Django: Twilio OTP service
from twilio.rest import Client

class OTPService:
    def __init__(self):
        self.client = Client(account_sid, auth_token)
        
    def send_otp(self, phone_number, channel='sms'):
        verification = self.client.verify.services(service_sid) \
            .verifications.create(to=phone_number, channel=channel)
        return verification.status
        
    def verify_otp(self, phone_number, code):
        verification_check = self.client.verify.services(service_sid) \
            .verification_checks.create(to=phone_number, code=code)
        return verification_check.status == 'approved'
```

## Banking Security Best Practices

**Decision**: Multi-layered security with PCI DSS compliance approach
**Rationale**:
- Banking applications require highest security standards
- PCI DSS provides comprehensive security framework
- Multi-factor authentication is industry standard
- Data encryption is regulatory requirement

**Security Layers Implemented**:
1. **Transport Security**: TLS 1.3 for all communications
2. **Authentication**: Firebase Auth + JWT tokens
3. **Authorization**: Role-based access control
4. **Data Protection**: AES-256 encryption for PII
5. **API Security**: Rate limiting and input validation
6. **Audit Logging**: All security events tracked
7. **Session Management**: 15-minute timeout, secure tokens

**Implementation Pattern**:
```python
# Django: Security middleware stack
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.auth.middleware.FirebaseAuthMiddleware',  # Custom
    'django.middleware.csrf.CsrfViewMiddleware',
    'apps.security.middleware.RateLimitMiddleware',  # Custom
    'apps.audit.middleware.AuditLogMiddleware',  # Custom
]

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
```

## API Design Patterns

**Decision**: RESTful API with OpenAPI documentation and versioning
**Rationale**:
- Standard HTTP methods for predictable behavior
- JSON responses for mobile app compatibility
- API versioning for backward compatibility
- OpenAPI schema for client code generation

**API Structure**:
```
/api/v1/auth/          # Authentication endpoints
/api/v1/customers/     # Customer management
/api/v1/requests/      # Limit increase requests
/api/v1/otp/          # OTP operations
/api/v1/notifications/ # Push notifications
```

**Response Format**:
```json
{
    "success": true,
    "data": {...},
    "message": "Operation completed successfully",
    "request_id": "req_12345",
    "timestamp": "2025-09-17T10:30:00Z"
}
```

## State Management (Flutter)

**Decision**: Riverpod for state management
**Rationale**:
- Provider pattern with compile-time safety
- Better testing support than other solutions
- Handles async operations naturally
- Scales well for complex app states

**Alternatives Considered**:
- Provider: Good but Riverpod is evolution with better features
- BLoC: Rejected due to complexity for this use case
- setState: Rejected due to app complexity

## Offline Capability

**Decision**: Local SQLite with sync mechanism
**Rationale**:
- Form data persistence during network issues
- Better user experience with offline drafts
- Sync when connectivity restored
- Flutter sqflite package provides robust local storage

**Implementation Strategy**:
1. Store draft requests locally
2. Sync when online
3. Handle conflicts with server state
4. Show offline indicators to users

## Performance Optimization

**Decision**: Implement caching strategy and lazy loading
**Rationale**:
- API response times must be under 2 seconds
- Mobile data usage optimization
- Better user experience with cached data

**Optimization Techniques**:
1. Redis caching for frequently accessed data
2. Database query optimization with indexes
3. Image optimization and lazy loading
4. API response compression
5. Connection pooling for database

## Research Conclusions

All technical unknowns have been resolved with specific implementation decisions:
- ✅ Firebase Auth integration pattern defined
- ✅ Oracle database optimization strategy chosen
- ✅ OneSignal implementation approach documented
- ✅ Twilio OTP service integration planned
- ✅ Banking security compliance requirements identified
- ✅ API design patterns established
- ✅ Flutter state management decision made
- ✅ Performance optimization strategies defined

Ready to proceed to Phase 1: Design & Contracts.