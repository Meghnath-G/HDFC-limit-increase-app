# Card Limit Increase System Constitution

## Core Principles

### I. Security-First Architecture
All user data must be protected with industry-standard encryption; Firebase Authentication required for all user sessions; API endpoints must validate JWT tokens; PII data encrypted at rest and in transit; No hardcoded credentials or API keys in source code

### II. Mobile-First Design
Flutter application must support responsive design for multiple screen sizes; Offline capability for form data with sync when online; Intuitive navigation with clear user flow from Customer Info → Selection → Details → OTP → Success; Form validation must provide immediate feedback to users

### III. API-Driven Backend
Django REST Framework provides all data services; RESTful endpoints with proper HTTP status codes; JSON request/response format with standardized error handling; Oracle SQL database as single source of truth; All endpoints must be documented with OpenAPI/Swagger

### IV. Real-Time Communication
Twilio integration for OTP delivery via SMS/email; OneSignal push notifications for status updates; WebSocket connections for real-time status updates (optional); Timeout handling for OTP verification (5-minute expiry)

### V. Production Readiness
Docker containerization for backend deployment; APK generation with proper signing for Android; Environment-specific configuration management; Comprehensive logging for debugging and monitoring; Error tracking and performance monitoring

## Security Requirements

### Authentication & Authorization
- Firebase Auth integration with email/password and phone authentication
- JWT token validation on all protected endpoints
- User can only access their own data (customer_id validation)
- Session management with automatic logout after inactivity

### Data Protection
- Oracle SQL database with encrypted connections
- PII fields encrypted using AES-256
- API rate limiting to prevent abuse
- Input validation and sanitization on all endpoints
- HTTPS/TLS 1.3 for all communications

### Mobile Permissions
- Request notifications permission for OneSignal
- SMS permission for OTP verification
- Phone permission for call-based OTP delivery
- Camera permission for future card scanning (optional)

## Technology Stack Requirements

### Frontend (Flutter)
- Flutter SDK 3.x with Dart 3.x
- Material Design 3 components
- State management using Provider or Riverpod
- HTTP client with retry logic and timeout handling
- Form validation with regex patterns for card numbers, emails, phones

### Backend (Django)
- Django 4.x with Python 3.9+
- Django REST Framework for API development
- cx_Oracle for Oracle database connectivity
- Celery for background task processing
- Redis for caching and session storage

### External Services
- Firebase Authentication for user management
- Twilio API for OTP delivery
- OneSignal for push notifications
- Oracle SQL 19c+ for data persistence

## Development Workflow

### Code Quality Standards
- Dart/Flutter: Follow effective Dart style guide with linting
- Python/Django: PEP 8 compliance with Black formatting
- API documentation using Swagger/OpenAPI 3.0
- Unit tests required for all business logic (80%+ coverage)
- Integration tests for API endpoints and user flows

### Database Migrations
- All schema changes through Django migrations
- Rollback scripts required for production deployments
- Data migration scripts for schema changes
- Performance testing for large data operations

### Deployment Pipeline
- Automated testing on pull requests
- Code review required before merge
- Staging environment for UAT testing
- Blue-green deployment for zero-downtime updates

## Governance

### Non-Negotiable Requirements
- No user data stored in logs or debug output
- All API responses must include request tracking IDs
- OTP attempts limited to 3 per session with cooldown
- Card numbers must be masked in all displays (show last 4 digits only)
- Database transactions for all multi-table operations

### Performance Standards
- API response time < 2 seconds for all endpoints
- Mobile app startup time < 3 seconds
- OTP delivery within 30 seconds
- Database query optimization for sub-second response times

**Version**: 1.0.0 | **Ratified**: 2025-09-17 | **Last Amended**: 2025-09-17