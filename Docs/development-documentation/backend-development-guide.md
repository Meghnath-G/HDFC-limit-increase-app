# Backend Development Documentation

## Overview

This document provides comprehensive information about the backend development of the Card Limit Increase System, including architecture decisions, implementation details, API specifications, and development guidelines.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Database Design](#database-design)
5. [API Documentation](#api-documentation)
6. [External Integrations](#external-integrations)
7. [Security Implementation](#security-implementation)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Guide](#deployment-guide)
10. [Development Workflow](#development-workflow)

## Architecture Overview

### System Architecture

The Card Limit Increase System follows a microservices-inspired monolithic architecture with clear separation of concerns:

```
┌─────────────────────┐
│   Frontend Layer    │
│   (Flutter Mobile)  │
└──────────┬──────────┘
           │
┌─────────────────────┐
│   API Gateway       │
│   (Django REST)     │
└──────────┬──────────┘
           │
┌─────────────────────┐
│   Business Logic    │
│   (Django Apps)     │
└──────────┬──────────┘
           │
┌─────────────────────┐
│   Data Layer        │
│   (Oracle Database) │
└─────────────────────┘
```

### Design Principles

1. **Single Responsibility**: Each Django app handles a specific domain
2. **Loose Coupling**: Minimal dependencies between components
3. **High Cohesion**: Related functionality grouped together
4. **Scalability**: Designed for horizontal scaling
5. **Security First**: PCI DSS compliance throughout
6. **Testability**: Comprehensive test coverage

## Technology Stack

### Core Technologies

#### Backend Framework
- **Django 4.2**: Web framework
- **Django REST Framework 3.14**: API development
- **Python 3.9+**: Programming language

#### Database
- **Oracle Database 19c**: Primary database
- **cx_Oracle 8.3**: Database connector
- **Redis**: Caching and session storage

#### External Services
- **Firebase Admin SDK**: Authentication and push notifications
- **Twilio**: SMS and voice communications
- **SendGrid**: Email delivery
- **OneSignal**: Push notifications

#### Development Tools
- **pytest**: Testing framework
- **Black**: Code formatting
- **Flake8**: Code linting
- **mypy**: Type checking

### Dependencies

#### Core Requirements
```txt
Django==4.2.7
djangorestframework==3.14.0
cx-Oracle==8.3.0
redis==5.0.1
celery==5.3.4
```

#### Authentication & Security
```txt
firebase-admin==6.2.0
PyJWT==2.8.0
cryptography==41.0.7
django-cors-headers==4.3.1
django-ratelimit==4.1.0
```

#### External Services
```txt
twilio==8.10.0
sendgrid==6.10.0
onesignal-sdk==2.0.0
requests==2.31.0
```

#### Development & Testing
```txt
pytest==7.4.3
pytest-django==4.7.0
factory-boy==3.3.0
coverage==7.3.2
```

## Project Structure

### Directory Layout

```
backend/
├── card_limit_system/          # Main project directory
│   ├── __init__.py
│   ├── settings/               # Configuration
│   │   ├── __init__.py
│   │   ├── base.py            # Base settings
│   │   ├── development.py     # Development settings
│   │   ├── production.py      # Production settings
│   │   └── testing.py         # Test settings
│   ├── urls.py                # Main URL configuration
│   ├── wsgi.py                # WSGI configuration
│   └── asgi.py                # ASGI configuration
├── apps/                       # Django applications
│   ├── accounts/               # Customer management
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── admin.py
│   ├── cards/                  # Card management
│   ├── requests/               # Limit requests
│   ├── notifications/          # Notification system
│   ├── reports/               # Reporting and analytics
│   └── common/                # Shared utilities
├── services/                   # External service integrations
│   ├── firebase_service.py
│   ├── twilio_service.py
│   ├── sendgrid_service.py
│   └── onesignal_service.py
├── utils/                      # Utility functions
│   ├── encryption.py
│   ├── validators.py
│   └── helpers.py
├── tests/                      # Test suite
│   ├── conftest.py
│   ├── factories.py
│   ├── unit/
│   ├── integration/
│   └── api/
├── static/                     # Static files
├── media/                      # Media files
├── requirements/               # Requirement files
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── testing.txt
├── scripts/                    # Management scripts
├── docs/                       # Documentation
└── manage.py                   # Django management
```

### Django Applications

#### accounts/
- **Purpose**: Customer and profile management
- **Models**: Customer, CustomerProfile
- **APIs**: Registration, authentication, profile management
- **Features**: KYC verification, customer analytics

#### cards/
- **Purpose**: Credit card management
- **Models**: Card, CardType, CardLimit
- **APIs**: Card listing, details, status updates
- **Features**: Card verification, limit tracking

#### requests/
- **Purpose**: Limit increase request management
- **Models**: LimitRequest, RequestDocument, ApprovalWorkflow
- **APIs**: Request submission, status tracking, approvals
- **Features**: Auto-approval, manual review, document upload

#### notifications/
- **Purpose**: Communication management
- **Models**: Notification, NotificationTemplate, OTP
- **APIs**: Notification sending, status tracking
- **Features**: Multi-channel delivery, templating

#### reports/
- **Purpose**: Analytics and reporting
- **Models**: Report, Analytics, AuditLog
- **APIs**: Report generation, analytics data
- **Features**: Real-time dashboards, audit trails

#### common/
- **Purpose**: Shared functionality
- **Components**: Base models, mixins, utilities
- **Features**: Encryption, validation, logging

## Database Design

### Entity Relationship Overview

```sql
-- Core Entities
Customer (1) ←→ (1) CustomerProfile
Customer (1) ←→ (*) Card
Card (1) ←→ (*) LimitRequest
Customer (1) ←→ (*) Notification
LimitRequest (1) ←→ (*) RequestDocument
```

### Key Models

#### Customer Model
```python
class Customer(BaseModel):
    customer_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    firebase_uid = models.CharField(max_length=128, unique=True)
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### Card Model
```python
class Card(BaseModel):
    card_number = EncryptedCharField(max_length=19)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES)
    current_limit = models.DecimalField(max_digits=12, decimal_places=2)
    available_limit = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=CARD_STATUS_CHOICES)
    issue_date = models.DateField()
    expiry_date = models.DateField()
```

#### LimitRequest Model
```python
class LimitRequest(BaseModel):
    request_id = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    current_limit = models.DecimalField(max_digits=12, decimal_places=2)
    requested_limit = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES)
    request_reason = models.TextField()
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)
    auto_approved = models.BooleanField(default=False)
```

### Database Optimization

#### Indexing Strategy
```sql
-- Performance indexes
CREATE INDEX idx_customer_firebase_uid ON Customer(firebase_uid);
CREATE INDEX idx_card_customer_status ON Card(customer_id, status);
CREATE INDEX idx_request_customer_status ON LimitRequest(customer_id, status);
CREATE INDEX idx_notification_customer_created ON Notification(customer_id, created_at);

-- Composite indexes
CREATE INDEX idx_card_limit_performance ON Card(customer_id, current_limit, status);
CREATE INDEX idx_request_processing ON LimitRequest(status, created_at, auto_approved);
```

#### Query Optimization
```python
# Optimized queries with select_related and prefetch_related
customers = Customer.objects.select_related('profile').prefetch_related('cards')
requests = LimitRequest.objects.select_related('customer', 'card').order_by('-created_at')
```

## API Documentation

### Authentication

#### Token-Based Authentication
```python
# Header format
Authorization: Bearer <firebase_token>

# Token verification
firebase_service = FirebaseService()
decoded_token = firebase_service.verify_token(token)
user_id = decoded_token['uid']
```

### API Endpoints

#### Customer Management

##### Register Customer
```http
POST /api/v1/customers/register/
Content-Type: application/json

{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "date_of_birth": "1990-01-01",
    "firebase_uid": "firebase_user_id"
}
```

##### Get Customer Profile
```http
GET /api/v1/customers/profile/
Authorization: Bearer <token>

Response:
{
    "customer_id": "CUST123456",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "kyc_status": "verified",
    "profile": {
        "annual_income": 1200000,
        "employment_type": "salaried",
        "credit_score": 750
    }
}
```

#### Card Management

##### List Customer Cards
```http
GET /api/v1/cards/
Authorization: Bearer <token>

Response:
[
    {
        "id": 1,
        "card_type": "credit",
        "current_limit": 50000.00,
        "available_limit": 35000.00,
        "status": "active",
        "masked_number": "****-****-****-1234"
    }
]
```

#### Limit Request Management

##### Submit Limit Request
```http
POST /api/v1/requests/
Authorization: Bearer <token>
Content-Type: application/json

{
    "card_id": 1,
    "requested_limit": 100000.00,
    "request_reason": "Increased monthly expenses"
}
```

##### Track Request Status
```http
GET /api/v1/requests/{request_id}/
Authorization: Bearer <token>

Response:
{
    "request_id": "REQ123456",
    "status": "under_review",
    "current_limit": 50000.00,
    "requested_limit": 100000.00,
    "risk_score": 65.5,
    "created_at": "2024-01-15T10:30:00Z"
}
```

### API Response Formats

#### Success Response
```json
{
    "success": true,
    "data": {
        "customer_id": "CUST123456",
        "status": "active"
    },
    "message": "Operation completed successfully",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Response
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "email": ["This field is required."],
            "phone_number": ["Invalid phone number format."]
        }
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## External Integrations

### Firebase Integration

#### Authentication Service
```python
class FirebaseService:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred)
    
    def verify_token(self, token):
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    def send_push_notification(self, tokens, title, body, data=None):
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            tokens=tokens
        )
        return messaging.send_multicast(message)
```

### Twilio Integration

#### SMS and Voice Service
```python
class TwilioService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    def send_sms(self, to_number, message):
        try:
            message = self.client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_number
            )
            return {'success': True, 'sid': message.sid}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def make_voice_call(self, to_number, twiml_url):
        try:
            call = self.client.calls.create(
                url=twiml_url,
                to=to_number,
                from_=settings.TWILIO_PHONE_NUMBER
            )
            return {'success': True, 'sid': call.sid}
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

### SendGrid Integration

#### Email Service
```python
class SendGridService:
    def __init__(self):
        self.sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    
    def send_email(self, to_email, subject, content, template_id=None):
        mail = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        
        if template_id:
            mail.template_id = template_id
        
        try:
            response = self.sg.send(mail)
            return {'success': True, 'status_code': response.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

## Security Implementation

### Data Encryption

#### Field-Level Encryption
```python
class EncryptedCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        self.encryption_key = settings.FIELD_ENCRYPTION_KEY
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_data(value, self.encryption_key)
    
    def to_python(self, value):
        if isinstance(value, str):
            return value
        return decrypt_data(value, self.encryption_key)
    
    def get_prep_value(self, value):
        if value is None:
            return value
        return encrypt_data(value, self.encryption_key)
```

### Authentication & Authorization

#### Permission Classes
```python
class IsCustomerOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if user owns the resource
        if hasattr(obj, 'customer'):
            return obj.customer.firebase_uid == request.user.firebase_uid
        return obj.firebase_uid == request.user.firebase_uid

class IsVerifiedCustomer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            request.user.kyc_status == 'verified'
        )
```

### Rate Limiting

#### API Rate Limiting
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='100/h', method='GET')
@ratelimit(key='user', rate='10/m', method='POST')
def api_view(request):
    # API logic here
    pass
```

### Audit Logging

#### Security Audit Trail
```python
class AuditLog(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    details = models.JSONField(default=dict)

def log_audit_event(user, action, resource_type, resource_id, request, success=True, details=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        success=success,
        details=details or {}
    )
```

## Testing Strategy

### Test Architecture

#### Test Configuration
```python
# conftest.py
@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(customer):
    client = APIClient()
    token = generate_test_token(customer.firebase_uid)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client

@pytest.fixture
def mock_firebase():
    with patch('services.firebase_service.FirebaseService') as mock:
        mock.verify_token.return_value = {'uid': 'test_user'}
        yield mock
```

#### Test Categories

##### Unit Tests
```python
class TestCustomerModel:
    def test_customer_creation(self):
        customer = CustomerFactory()
        assert customer.customer_id.startswith('CUST')
        assert customer.is_active is True
    
    def test_customer_age_calculation(self):
        customer = CustomerFactory(date_of_birth=date(1990, 1, 1))
        assert customer.age >= 30
```

##### API Tests
```python
class TestCustomerAPI:
    def test_customer_registration(self, api_client):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'firebase_uid': 'test_uid'
        }
        response = api_client.post('/api/v1/customers/register/', data)
        assert response.status_code == 201
        assert response.data['customer_id'].startswith('CUST')
```

##### Integration Tests
```python
class TestExternalServices:
    def test_firebase_token_verification(self, mock_firebase):
        service = FirebaseService()
        result = service.verify_token('test_token')
        assert result['uid'] == 'test_user'
        mock_firebase.verify_token.assert_called_once()
```

### Coverage Requirements

- **Overall Coverage**: 85%+
- **Critical Paths**: 95%+
- **Security Functions**: 100%
- **API Endpoints**: 90%+

## Deployment Guide

### Environment Configuration

#### Development Environment
```python
# settings/development.py
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'localhost:1521/XEPDB1',
        'USER': 'card_limit_dev',
        'PASSWORD': 'dev_password',
    }
}

# External service settings (development)
FIREBASE_CREDENTIALS = 'path/to/dev-firebase-credentials.json'
TWILIO_ACCOUNT_SID = 'dev_account_sid'
```

#### Production Environment
```python
# settings/production.py
DEBUG = False
ALLOWED_HOSTS = ['api.cardlimit.hdfc.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

### Docker Configuration

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libaio1 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linuxx64.zip \
    && unzip instantclient-basiclite-linuxx64.zip \
    && mv instantclient_* /opt/oracle \
    && echo /opt/oracle > /etc/ld.so.conf.d/oracle.conf \
    && ldconfig

# Install Python dependencies
COPY requirements/ requirements/
RUN pip install -r requirements/production.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "card_limit_system.wsgi:application"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=card_limit_system.settings.production
      - DB_HOST=oracle-db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - oracle-db
      - redis
    volumes:
      - ./logs:/app/logs

  oracle-db:
    image: container-registry.oracle.com/database/enterprise:19.3.0.0
    environment:
      - ORACLE_SID=ORCL
      - ORACLE_PDB=ORCLPDB1
      - ORACLE_PWD=StrongPassword123
    ports:
      - "1521:1521"
    volumes:
      - oracle_data:/opt/oracle/oradata

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  oracle_data:
  redis_data:
```

### CI/CD Pipeline

#### GitHub Actions
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements/testing.txt
      - name: Run tests
        run: |
          python run_tests.py --with-coverage
      - name: Check coverage
        run: |
          coverage report --fail-under=85

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Deployment script
          docker build -t card-limit-api .
          docker push ${{ secrets.DOCKER_REGISTRY }}/card-limit-api:latest
```

## Development Workflow

### Code Standards

#### Code Formatting
```bash
# Black formatting
black --line-length=88 .

# Import sorting
isort .

# Linting
flake8 .

# Type checking
mypy .
```

#### Git Workflow
```bash
# Feature development
git checkout -b feature/limit-request-api
git add .
git commit -m "feat: implement limit request API endpoints"
git push origin feature/limit-request-api

# Create pull request
# Code review process
# Merge to main
```

### Database Migrations

#### Creating Migrations
```bash
# Create migration
python manage.py makemigrations accounts

# Review migration
python manage.py sqlmigrate accounts 0001

# Apply migration
python manage.py migrate
```

#### Migration Best Practices
1. **Review SQL**: Always review generated SQL
2. **Backup Data**: Backup before production migrations
3. **Test Migrations**: Test on staging environment
4. **Rollback Plan**: Prepare rollback procedures

### Performance Monitoring

#### Database Query Optimization
```python
# Use select_related for foreign keys
customers = Customer.objects.select_related('profile')

# Use prefetch_related for many-to-many
customers = Customer.objects.prefetch_related('cards')

# Add database indexes
class Meta:
    indexes = [
        models.Index(fields=['customer_id', 'status']),
        models.Index(fields=['created_at']),
    ]
```

#### API Performance Monitoring
```python
# Response time logging
import time
from django.utils.deprecation import MiddlewareMixin

class ResponseTimeMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response['X-Response-Time'] = f"{duration:.2f}s"
        return response
```

## Conclusion

This backend development documentation provides a comprehensive guide for understanding, developing, and maintaining the Card Limit Increase System. The architecture prioritizes security, scalability, and maintainability while ensuring compliance with banking industry standards.

For additional technical details or clarification on any aspect of the backend implementation, refer to the specific module documentation or contact the development team.