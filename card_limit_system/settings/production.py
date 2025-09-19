"""
Production settings for HDFC Card Limit Increase System.

This settings file is optimized for production deployment with
enterprise-grade security, performance, and monitoring configurations.
"""

import os
import logging.config
from pathlib import Path
from .base import *

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Security Configuration
ALLOWED_HOSTS = [
    'card-limit-api.hdfc.com',
    'card-limit-api-prod.hdfc.com',
    'card-limit-api-staging.hdfc.com',
    '10.0.0.0/8',  # Internal network
    '172.16.0.0/12',  # Internal network
    '192.168.0.0/16',  # Internal network
]

# SSL and Security Headers
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Cookie Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Database Configuration - Oracle Production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': os.environ.get('DB_NAME', 'HDFC_CARD_LIMIT_PROD'),
        'USER': os.environ.get('DB_USER', 'card_limit_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'oracle-prod.hdfc.com'),
        'PORT': os.environ.get('DB_PORT', '1521'),
        'OPTIONS': {
            'threaded': True,
            'use_returning_into': False,
            'init_command': "ALTER SESSION SET CURRENT_SCHEMA=card_limit_user",
            'isolation_level': 'read committed',
            'autocommit': True,
        },
        'CONN_MAX_AGE': 600,  # 10 minutes
        'TEST': {
            'NAME': 'test_hdfc_card_limit',
        }
    },
    # Read replica for analytics and reporting
    'analytics': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': os.environ.get('DB_ANALYTICS_NAME', 'HDFC_CARD_LIMIT_ANALYTICS'),
        'USER': os.environ.get('DB_ANALYTICS_USER', 'card_limit_analytics'),
        'PASSWORD': os.environ.get('DB_ANALYTICS_PASSWORD'),
        'HOST': os.environ.get('DB_ANALYTICS_HOST', 'oracle-analytics.hdfc.com'),
        'PORT': os.environ.get('DB_ANALYTICS_PORT', '1521'),
        'OPTIONS': {
            'threaded': True,
            'use_returning_into': False,
            'init_command': "ALTER SESSION SET CURRENT_SCHEMA=card_limit_analytics",
            'isolation_level': 'read committed',
            'autocommit': True,
        },
        'CONN_MAX_AGE': 1200,  # 20 minutes for analytics
    }
}

# Cache Configuration - Redis Production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': [
            f"redis://{os.environ.get('REDIS_HOST', 'redis-prod.hdfc.com')}:6379/0",
            f"redis://{os.environ.get('REDIS_HOST_BACKUP', 'redis-backup.hdfc.com')}:6379/0",
        ],
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.ShardClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 200,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
                'health_check_interval': 30,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'TIMEOUT': 300,  # 5 minutes default
        'VERSION': 1,
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.environ.get('REDIS_SESSION_HOST', 'redis-sessions.hdfc.com')}:6379/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',
        },
        'TIMEOUT': 3600,  # 1 hour
    },
    'rate_limit': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.environ.get('REDIS_RATE_LIMIT_HOST', 'redis-rate-limit.hdfc.com')}:6379/2",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'TIMEOUT': 3600,  # 1 hour
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 3600  # 1 hour

# Email Configuration - SendGrid Production
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDGRID_SANDBOX_MODE_IN_DEBUG = False
DEFAULT_FROM_EMAIL = 'noreply@hdfc.com'
SERVER_EMAIL = 'alerts@hdfc.com'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/hdfc/card_limit_system.log',
            'maxBytes': 50 * 1024 * 1024,  # 50 MB
            'backupCount': 10,
            'formatter': 'json',
            'filters': ['require_debug_false'],
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/hdfc/card_limit_errors.log',
            'maxBytes': 50 * 1024 * 1024,  # 50 MB
            'backupCount': 5,
            'formatter': 'json',
            'filters': ['require_debug_false'],
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/hdfc/card_limit_security.log',
            'maxBytes': 100 * 1024 * 1024,  # 100 MB
            'backupCount': 20,
            'formatter': 'json',
            'filters': ['require_debug_false'],
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['require_debug_false'],
        },
        'syslog': {
            'level': 'INFO',
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log',
            'formatter': 'json',
            'filters': ['require_debug_false'],
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console', 'syslog'],
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'card_limit_system': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'accounts': {
            'handlers': ['file', 'security_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'requests': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'notifications': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'otp': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'analytics': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Static Files Configuration
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/hdfc/card_limit_system/static/'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Media Files Configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/hdfc/card_limit_system/media/'
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB

# Performance Settings
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
CONN_MAX_AGE = 600  # 10 minutes

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Firebase Configuration - Production
FIREBASE_CONFIG = {
    'type': 'service_account',
    'project_id': os.environ.get('FIREBASE_PROJECT_ID', 'hdfc-card-limit-prod'),
    'private_key_id': os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
    'private_key': os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
    'client_email': os.environ.get('FIREBASE_CLIENT_EMAIL'),
    'client_id': os.environ.get('FIREBASE_CLIENT_ID'),
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': os.environ.get('FIREBASE_CLIENT_CERT_URL'),
}

# Twilio Configuration - Production
TWILIO_CONFIG = {
    'account_sid': os.environ.get('TWILIO_ACCOUNT_SID'),
    'auth_token': os.environ.get('TWILIO_AUTH_TOKEN'),
    'verify_service_sid': os.environ.get('TWILIO_VERIFY_SERVICE_SID'),
    'phone_number': os.environ.get('TWILIO_PHONE_NUMBER'),
    'whatsapp_number': os.environ.get('TWILIO_WHATSAPP_NUMBER'),
    'webhook_url': 'https://card-limit-api.hdfc.com/webhooks/twilio/',
    'rate_limit': {
        'sms_per_minute': 100,
        'voice_per_minute': 10,
        'whatsapp_per_minute': 50,
    }
}

# OneSignal Configuration - Production
ONESIGNAL_CONFIG = {
    'app_id': os.environ.get('ONESIGNAL_APP_ID'),
    'rest_api_key': os.environ.get('ONESIGNAL_REST_API_KEY'),
    'user_auth_key': os.environ.get('ONESIGNAL_USER_AUTH_KEY'),
    'rate_limit': {
        'notifications_per_minute': 1000,
        'api_calls_per_minute': 100,
    }
}

# Rate Limiting Configuration
RATE_LIMITING = {
    'login_attempts': {
        'limit': 5,
        'window': 900,  # 15 minutes
        'block_duration': 3600,  # 1 hour
    },
    'otp_requests': {
        'limit': 3,
        'window': 300,  # 5 minutes
        'block_duration': 1800,  # 30 minutes
    },
    'api_requests': {
        'limit': 1000,
        'window': 3600,  # 1 hour
        'block_duration': 300,  # 5 minutes
    },
    'limit_requests': {
        'limit': 5,
        'window': 86400,  # 24 hours
        'block_duration': 86400,  # 24 hours
    }
}

# Encryption Configuration
ENCRYPTION_CONFIG = {
    'algorithm': 'AES-256-GCM',
    'key': os.environ.get('ENCRYPTION_KEY'),
    'key_rotation_days': 90,
    'backup_keys': [
        os.environ.get('ENCRYPTION_KEY_BACKUP_1'),
        os.environ.get('ENCRYPTION_KEY_BACKUP_2'),
    ]
}

# Monitoring and Health Checks
HEALTH_CHECK_CONFIG = {
    'database_timeout': 5,
    'cache_timeout': 3,
    'external_service_timeout': 10,
    'check_interval': 30,  # seconds
    'alert_threshold': 3,  # consecutive failures
}

# Audit Configuration
AUDIT_CONFIG = {
    'log_all_requests': True,
    'log_sensitive_data': False,
    'retention_days': 2555,  # 7 years for banking compliance
    'alert_on_suspicious_activity': True,
    'sensitive_fields': [
        'password', 'token', 'card_number', 'cvv', 'pin',
        'ssn', 'pan_number', 'aadhaar_number'
    ]
}

# Security Headers Middleware
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Additional Security Settings
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Performance Monitoring
PERFORMANCE_CONFIG = {
    'enable_profiling': True,
    'slow_query_threshold': 1.0,  # seconds
    'memory_usage_threshold': 80,  # percentage
    'response_time_threshold': 2.0,  # seconds
}

# Backup Configuration
BACKUP_CONFIG = {
    'database_backup_schedule': '0 2 * * *',  # Daily at 2 AM
    'media_backup_schedule': '0 3 * * *',  # Daily at 3 AM
    'retention_days': 30,
    'backup_location': '/backup/hdfc/card_limit_system/',
    'encryption_enabled': True,
    'compression_enabled': True,
}

# Environment Variables Validation
required_env_vars = [
    'DB_PASSWORD',
    'SENDGRID_API_KEY',
    'FIREBASE_PRIVATE_KEY',
    'FIREBASE_CLIENT_EMAIL',
    'TWILIO_ACCOUNT_SID',
    'TWILIO_AUTH_TOKEN',
    'ONESIGNAL_APP_ID',
    'ONESIGNAL_REST_API_KEY',
    'ENCRYPTION_KEY',
]

for var in required_env_vars:
    if not os.environ.get(var):
        raise ValueError(f"Required environment variable {var} is not set")

# Application-specific settings
APPEND_SLASH = True
PREPEND_WWW = False

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom settings for production optimization
DJANGO_SETTINGS_MODULE = 'card_limit_system.settings.production'