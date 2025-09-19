"""
Test settings for the Card Limit System.

Optimized settings for running tests with proper database,
caching, and external service configurations.
"""

from .settings import *

# Test database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 30,
        }
    }
}

# Disable migrations for faster testing
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
DEBUG = False
TESTING = True

# Use local memory cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Use console email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable logging during tests
LOGGING_CONFIG = None
LOGGING = {}

# Use fast password hasher for testing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Mock external service configurations
FIREBASE_CONFIG = {
    'type': 'service_account',
    'project_id': 'test-project',
    'private_key_id': 'test-key-id',
    'private_key': '-----BEGIN PRIVATE KEY-----\nTEST_KEY\n-----END PRIVATE KEY-----\n',
    'client_email': 'test@test-project.iam.gserviceaccount.com',
    'client_id': 'test-client-id',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': 'https://example.com/test-cert',
}

TWILIO_ACCOUNT_SID = 'test_account_sid'
TWILIO_AUTH_TOKEN = 'test_auth_token'
TWILIO_PHONE_NUMBER = '+1234567890'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
TWILIO_VERIFY_SERVICE_SID = 'test_verify_service_sid'

SENDGRID_API_KEY = 'test_sendgrid_api_key'
SENDGRID_FROM_EMAIL = 'test@hdfc.com'
SENDGRID_FROM_NAME = 'HDFC Bank Test'

ONESIGNAL_APP_ID = 'test_onesignal_app_id'
ONESIGNAL_REST_API_KEY = 'test_onesignal_rest_key'
ONESIGNAL_USER_AUTH_KEY = 'test_onesignal_user_key'

# Test Redis configuration
REDIS_URL = 'redis://localhost:6379/15'  # Use different DB for tests

# Disable rate limiting in tests
RATE_LIMIT_SETTINGS = {
    'login_attempts': {'limit': 1000, 'window': 1, 'block_duration': 1},
    'otp_requests': {'limit': 1000, 'window': 1, 'block_duration': 1},
    'api_requests': {'limit': 1000, 'window': 1, 'block_duration': 1},
    'limit_requests': {'limit': 1000, 'window': 1, 'block_duration': 1},
}

# Test encryption key
ENCRYPTION_KEY = b'test_encryption_key_32_bytes_long!'

# Disable security features for testing
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Test media settings
MEDIA_ROOT = '/tmp/test_media'
STATIC_ROOT = '/tmp/test_static'

# Test business rules (more lenient for testing)
BUSINESS_RULES = {
    'card_limits': {
        'min_credit_limit': 1000,
        'max_credit_limit': 10000000,
        'min_increase_amount': 1000,
        'max_increase_percentage': 1000,
    },
    'netbanking_limits': {
        'min_daily_limit': 100,
        'max_daily_limit': 10000000,
        'min_per_transaction_limit': 10,
        'max_per_transaction_limit': 5000000,
    },
    'approval_workflow': {
        'auto_approve_threshold': 100000,
        'manager_approval_threshold': 1000000,
        'senior_manager_approval_threshold': 5000000,
    },
    'risk_assessment': {
        'min_account_age_days': 30,
        'min_credit_score': 500,
        'max_utilization_ratio': 0.9,
        'min_income': 100000,
    },
}