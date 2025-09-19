"""
Test configuration and setup for the Card Limit System.

This module provides test settings, fixtures, and common utilities
for all test modules in the project.
"""

import pytest
import os
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line

# Configure Django settings for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'card_limit_system.test_settings')

# Setup Django
django.setup()

# Test database configuration
TEST_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 30,
        }
    }
}

# Test-specific settings
TEST_SETTINGS = {
    'DEBUG': False,
    'TESTING': True,
    'EMAIL_BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
    'CELERY_TASK_ALWAYS_EAGER': True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'CACHES': {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    },
    'LOGGING_CONFIG': None,
    'PASSWORD_HASHERS': [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ],
}

# Mock external services for testing
MOCK_SERVICES = {
    'FIREBASE_CONFIG': {
        'type': 'service_account',
        'project_id': 'test-project',
        'private_key_id': 'test-key-id',
        'private_key': '-----BEGIN PRIVATE KEY-----\nTEST_KEY\n-----END PRIVATE KEY-----\n',
        'client_email': 'test@test-project.iam.gserviceaccount.com',
        'client_id': 'test-client-id',
    },
    'TWILIO_ACCOUNT_SID': 'test_account_sid',
    'TWILIO_AUTH_TOKEN': 'test_auth_token',
    'TWILIO_PHONE_NUMBER': '+1234567890',
    'SENDGRID_API_KEY': 'test_sendgrid_key',
    'ONESIGNAL_APP_ID': 'test_onesignal_app_id',
    'ONESIGNAL_REST_API_KEY': 'test_onesignal_key',
}

# Test data constants
TEST_DATA = {
    'customer': {
        'customer_id': 'TEST123456',
        'phone_number': '+919876543210',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'Customer',
        'date_of_birth': '1990-01-01',
        'pan_number': 'ABCDE1234F',
        'aadhar_number': '123456789012',
    },
    'card': {
        'card_number': '4111111111111111',
        'card_type': 'CREDIT',
        'current_limit': 50000,
        'available_limit': 30000,
    },
    'netbanking': {
        'account_number': '12345678901234',
        'account_type': 'SAVINGS',
        'daily_limit': 100000,
        'per_transaction_limit': 50000,
    },
    'limit_request': {
        'request_type': 'CREDIT_CARD',
        'current_limit': 50000,
        'requested_limit': 100000,
        'reason': 'Salary increase',
        'income': 800000,
    }
}

# Pytest configuration
@pytest.fixture(scope='session')
def django_db_setup():
    """Setup test database."""
    settings.DATABASES['default'] = TEST_DATABASES['default']

@pytest.fixture
def api_client():
    """Create API client for testing."""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, customer_user):
    """Create authenticated API client."""
    from rest_framework.authtoken.models import Token
    token, created = Token.objects.get_or_create(user=customer_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client

@pytest.fixture
def mock_firebase():
    """Mock Firebase services."""
    import unittest.mock as mock
    with mock.patch('core.firebase_service.FirebaseService') as mock_firebase:
        mock_firebase.verify_token.return_value = {
            'success': True,
            'uid': 'test_uid',
            'email': 'test@example.com'
        }
        yield mock_firebase

@pytest.fixture
def mock_twilio():
    """Mock Twilio services."""
    import unittest.mock as mock
    with mock.patch('core.twilio_service.TwilioService') as mock_twilio:
        mock_twilio.send_sms.return_value = {
            'success': True,
            'message_sid': 'test_message_sid'
        }
        mock_twilio.send_verification.return_value = {
            'success': True,
            'verification_sid': 'test_verification_sid'
        }
        yield mock_twilio

@pytest.fixture
def mock_sendgrid():
    """Mock SendGrid services."""
    import unittest.mock as mock
    with mock.patch('core.sendgrid_service.SendGridService') as mock_sendgrid:
        mock_sendgrid.send_email.return_value = {
            'success': True,
            'message_id': 'test_message_id'
        }
        yield mock_sendgrid

@pytest.fixture
def mock_onesignal():
    """Mock OneSignal services."""
    import unittest.mock as mock
    with mock.patch('core.onesignal_service.OneSignalService') as mock_onesignal:
        mock_onesignal.send_notification.return_value = {
            'success': True,
            'notification_id': 'test_notification_id'
        }
        yield mock_onesignal