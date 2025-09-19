# External Service Integration Guide

## Table of Contents
1. [Integration Overview](#integration-overview)
2. [Firebase Authentication Integration](#firebase-authentication-integration)
3. [Twilio Communication Services](#twilio-communication-services)
4. [SendGrid Email Services](#sendgrid-email-services)
5. [OneSignal Push Notifications](#onesignal-push-notifications)
6. [Oracle Database Integration](#oracle-database-integration)
7. [Error Handling & Monitoring](#error-handling--monitoring)
8. [Testing Strategies](#testing-strategies)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Integration Overview

### 1. External Service Architecture

```python
class ExternalServiceManager:
    """
    Centralized management for all external service integrations
    """
    
    def __init__(self):
        self.services = {
            'firebase': FirebaseService(),
            'twilio': TwilioService(),
            'sendgrid': SendGridService(),
            'onesignal': OneSignalService(),
            'oracle': OracleService()
        }
        self.health_monitor = ServiceHealthMonitor()
        self.circuit_breaker = CircuitBreakerManager()
    
    def get_service(self, service_name: str):
        """
        Get service instance with health checking and circuit breaker
        """
        service = self.services.get(service_name)
        if not service:
            raise ServiceNotFoundException(f"Service {service_name} not found")
        
        # Check service health
        if not self.health_monitor.is_healthy(service_name):
            raise ServiceUnavailableException(f"Service {service_name} is unhealthy")
        
        # Check circuit breaker
        if self.circuit_breaker.is_open(service_name):
            raise CircuitBreakerOpenException(f"Circuit breaker open for {service_name}")
        
        return service
    
    def configure_service_dependencies(self):
        """
        Configure service dependencies and fallback strategies
        """
        service_config = {
            'firebase': {
                'primary': True,
                'fallback': None,
                'timeout': 30,
                'retry_count': 3,
                'circuit_breaker': {
                    'failure_threshold': 5,
                    'recovery_timeout': 60,
                    'half_open_max_calls': 3
                }
            },
            'twilio': {
                'primary': True,
                'fallback': 'alternate_sms_provider',
                'timeout': 10,
                'retry_count': 2,
                'circuit_breaker': {
                    'failure_threshold': 3,
                    'recovery_timeout': 30,
                    'half_open_max_calls': 2
                }
            },
            'sendgrid': {
                'primary': True,
                'fallback': 'ses_email_service',
                'timeout': 15,
                'retry_count': 3,
                'circuit_breaker': {
                    'failure_threshold': 5,
                    'recovery_timeout': 45,
                    'half_open_max_calls': 3
                }
            },
            'onesignal': {
                'primary': True,
                'fallback': 'fcm_direct',
                'timeout': 10,
                'retry_count': 2,
                'circuit_breaker': {
                    'failure_threshold': 3,
                    'recovery_timeout': 30,
                    'half_open_max_calls': 2
                }
            },
            'oracle': {
                'primary': True,
                'fallback': 'read_replica',
                'timeout': 5,
                'retry_count': 3,
                'circuit_breaker': {
                    'failure_threshold': 10,
                    'recovery_timeout': 120,
                    'half_open_max_calls': 5
                }
            }
        }
        
        return service_config
```

### 2. Service Integration Patterns

```python
class ServiceIntegrationPatterns:
    """
    Common patterns for external service integration
    """
    
    @staticmethod
    def retry_with_exponential_backoff(func, max_retries=3, base_delay=1):
        """
        Retry pattern with exponential backoff
        """
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay} seconds..."
                    )
            
            raise last_exception
        
        return wrapper
    
    @staticmethod
    def circuit_breaker(failure_threshold=5, recovery_timeout=60):
        """
        Circuit breaker pattern for service resilience
        """
        def decorator(func):
            circuit_state = {
                'failures': 0,
                'last_failure_time': None,
                'state': 'closed'  # closed, open, half-open
            }
            
            def wrapper(*args, **kwargs):
                current_time = time.time()
                
                # Check if circuit should transition from open to half-open
                if (circuit_state['state'] == 'open' and 
                    current_time - circuit_state['last_failure_time'] > recovery_timeout):
                    circuit_state['state'] = 'half-open'
                    logger.info(f"Circuit breaker for {func.__name__} transitioning to half-open")
                
                # If circuit is open, fail fast
                if circuit_state['state'] == 'open':
                    raise CircuitBreakerOpenException(f"Circuit breaker open for {func.__name__}")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Success - reset circuit breaker
                    if circuit_state['state'] == 'half-open':
                        circuit_state['state'] = 'closed'
                        circuit_state['failures'] = 0
                        logger.info(f"Circuit breaker for {func.__name__} reset to closed")
                    
                    return result
                    
                except Exception as e:
                    circuit_state['failures'] += 1
                    circuit_state['last_failure_time'] = current_time
                    
                    # Open circuit if failure threshold reached
                    if circuit_state['failures'] >= failure_threshold:
                        circuit_state['state'] = 'open'
                        logger.error(
                            f"Circuit breaker for {func.__name__} opened after "
                            f"{failure_threshold} failures"
                        )
                    
                    raise e
            
            return wrapper
        return decorator
    
    @staticmethod
    def timeout_handler(timeout_seconds=30):
        """
        Timeout handling pattern
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    # Use signal for timeout (Unix systems)
                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(timeout_seconds)
                    
                    result = func(*args, **kwargs)
                    
                    signal.alarm(0)  # Cancel the alarm
                    return result
                    
                except TimeoutError:
                    logger.error(f"Timeout occurred for {func.__name__} after {timeout_seconds} seconds")
                    raise
                except Exception as e:
                    signal.alarm(0)  # Cancel the alarm
                    raise e
            
            return wrapper
        return decorator
```

---

## Firebase Authentication Integration

### 1. Firebase Setup and Configuration

```python
# config/firebase_config.py
import firebase_admin
from firebase_admin import credentials, auth, messaging
from django.conf import settings
import json

class FirebaseConfiguration:
    """
    Firebase service configuration and initialization
    """
    
    def __init__(self):
        self.app = None
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """
        Initialize Firebase Admin SDK
        """
        try:
            # Load service account key
            service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
            
            # Initialize Firebase app
            cred = credentials.Certificate(service_account_info)
            self.app = firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID,
                'databaseURL': f'https://{settings.FIREBASE_PROJECT_ID}.firebaseio.com',
                'storageBucket': f'{settings.FIREBASE_PROJECT_ID}.appspot.com'
            })
            
            logger.info("Firebase Admin SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            raise FirebaseInitializationException(f"Failed to initialize Firebase: {str(e)}")
    
    def get_firebase_app(self):
        """
        Get Firebase app instance
        """
        if not self.app:
            self.initialize_firebase()
        return self.app

# Environment Variables Configuration
FIREBASE_SETTINGS = {
    'FIREBASE_PROJECT_ID': 'hdfc-card-limit-system',
    'FIREBASE_SERVICE_ACCOUNT_KEY': '''
    {
        "type": "service_account",
        "project_id": "hdfc-card-limit-system",
        "private_key_id": "your-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\\nYour-Private-Key\\n-----END PRIVATE KEY-----\\n",
        "client_email": "firebase-adminsdk-xxxxx@hdfc-card-limit-system.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40hdfc-card-limit-system.iam.gserviceaccount.com"
    }
    ''',
    'FIREBASE_WEB_API_KEY': 'your-web-api-key',
    'FIREBASE_AUTH_DOMAIN': 'hdfc-card-limit-system.firebaseapp.com',
    'FIREBASE_MESSAGING_SENDER_ID': 'your-sender-id'
}
```

### 2. Firebase Authentication Service

```python
# services/firebase_auth_service.py
from firebase_admin import auth
import time
from typing import Dict, Optional

class FirebaseAuthService:
    """
    Comprehensive Firebase Authentication service
    """
    
    def __init__(self):
        self.firebase_config = FirebaseConfiguration()
        self.token_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    @ServiceIntegrationPatterns.circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @ServiceIntegrationPatterns.timeout_handler(timeout_seconds=30)
    def verify_id_token(self, id_token: str) -> Dict:
        """
        Verify Firebase ID token with enhanced validation
        """
        try:
            # Check token cache first
            if id_token in self.token_cache:
                cached_token = self.token_cache[id_token]
                if time.time() - cached_token['cached_at'] < self.cache_ttl:
                    return cached_token['decoded_token']
            
            # Verify token with Firebase
            decoded_token = auth.verify_id_token(
                id_token,
                check_revoked=True,  # Check if token has been revoked
                clock_skew_seconds=10  # Allow 10 seconds clock skew
            )
            
            # Enhanced token validation
            validation_result = self.validate_token_claims(decoded_token)
            if not validation_result['valid']:
                raise InvalidTokenException(validation_result['reason'])
            
            # Cache valid token
            self.token_cache[id_token] = {
                'decoded_token': decoded_token,
                'cached_at': time.time()
            }
            
            # Log successful verification
            logger.info(
                f"Token verified successfully for user: {decoded_token.get('uid')}",
                extra={
                    'user_id': decoded_token.get('uid'),
                    'event_type': 'token_verification_success'
                }
            )
            
            return decoded_token
            
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid ID token: {str(e)}")
            raise InvalidTokenException(f"Invalid ID token: {str(e)}")
        
        except auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired ID token: {str(e)}")
            raise ExpiredTokenException(f"Expired ID token: {str(e)}")
        
        except auth.RevokedIdTokenError as e:
            logger.warning(f"Revoked ID token: {str(e)}")
            raise RevokedTokenException(f"Revoked ID token: {str(e)}")
        
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise TokenVerificationException(f"Token verification failed: {str(e)}")
    
    def validate_token_claims(self, decoded_token: Dict) -> Dict:
        """
        Validate token claims for additional security
        """
        validation_result = {'valid': True, 'reason': None}
        
        # Check required claims
        required_claims = ['uid', 'iss', 'aud', 'exp', 'iat']
        for claim in required_claims:
            if claim not in decoded_token:
                validation_result.update({
                    'valid': False,
                    'reason': f"Missing required claim: {claim}"
                })
                return validation_result
        
        # Validate issuer
        expected_issuer = f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}"
        if decoded_token.get('iss') != expected_issuer:
            validation_result.update({
                'valid': False,
                'reason': f"Invalid issuer: {decoded_token.get('iss')}"
            })
            return validation_result
        
        # Validate audience
        if decoded_token.get('aud') != settings.FIREBASE_PROJECT_ID:
            validation_result.update({
                'valid': False,
                'reason': f"Invalid audience: {decoded_token.get('aud')}"
            })
            return validation_result
        
        # Check token age (additional security measure)
        current_time = int(time.time())
        token_issued_at = decoded_token.get('iat')
        max_token_age = 24 * 60 * 60  # 24 hours
        
        if current_time - token_issued_at > max_token_age:
            validation_result.update({
                'valid': False,
                'reason': "Token is too old"
            })
            return validation_result
        
        return validation_result
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def create_custom_token(self, uid: str, additional_claims: Dict = None) -> str:
        """
        Create custom Firebase token for server-side authentication
        """
        try:
            custom_token = auth.create_custom_token(
                uid=uid,
                additional_claims=additional_claims or {}
            )
            
            logger.info(
                f"Custom token created for user: {uid}",
                extra={'user_id': uid, 'event_type': 'custom_token_created'}
            )
            
            return custom_token.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Custom token creation failed for user {uid}: {str(e)}")
            raise CustomTokenCreationException(f"Failed to create custom token: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def set_custom_user_claims(self, uid: str, custom_claims: Dict):
        """
        Set custom claims for a user
        """
        try:
            auth.set_custom_user_claims(uid, custom_claims)
            
            logger.info(
                f"Custom claims set for user: {uid}",
                extra={
                    'user_id': uid,
                    'custom_claims': custom_claims,
                    'event_type': 'custom_claims_set'
                }
            )
            
        except Exception as e:
            logger.error(f"Setting custom claims failed for user {uid}: {str(e)}")
            raise CustomClaimsException(f"Failed to set custom claims: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def revoke_refresh_tokens(self, uid: str):
        """
        Revoke all refresh tokens for a user
        """
        try:
            auth.revoke_refresh_tokens(uid)
            
            logger.info(
                f"Refresh tokens revoked for user: {uid}",
                extra={'user_id': uid, 'event_type': 'tokens_revoked'}
            )
            
        except Exception as e:
            logger.error(f"Token revocation failed for user {uid}: {str(e)}")
            raise TokenRevocationException(f"Failed to revoke tokens: {str(e)}")
    
    def get_user_info(self, uid: str) -> Dict:
        """
        Get comprehensive user information from Firebase
        """
        try:
            user_record = auth.get_user(uid)
            
            user_info = {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'phone_number': user_record.phone_number,
                'disabled': user_record.disabled,
                'custom_claims': user_record.custom_claims or {},
                'provider_data': [
                    {
                        'uid': provider.uid,
                        'email': provider.email,
                        'phone_number': provider.phone_number,
                        'provider_id': provider.provider_id
                    }
                    for provider in user_record.provider_data
                ],
                'metadata': {
                    'creation_timestamp': user_record.user_metadata.creation_timestamp,
                    'last_sign_in_timestamp': user_record.user_metadata.last_sign_in_timestamp,
                    'last_refresh_timestamp': user_record.user_metadata.last_refresh_timestamp
                }
            }
            
            return user_info
            
        except auth.UserNotFoundError:
            raise UserNotFoundException(f"User not found: {uid}")
        except Exception as e:
            logger.error(f"Failed to get user info for {uid}: {str(e)}")
            raise UserInfoException(f"Failed to get user info: {str(e)}")
```

### 3. Firebase Cloud Messaging Integration

```python
# services/firebase_messaging_service.py
from firebase_admin import messaging
from typing import List, Dict, Optional

class FirebaseMessagingService:
    """
    Firebase Cloud Messaging service for push notifications
    """
    
    def __init__(self):
        self.firebase_config = FirebaseConfiguration()
        self.default_config = self.get_default_message_config()
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    @ServiceIntegrationPatterns.circuit_breaker(failure_threshold=3, recovery_timeout=30)
    def send_notification(self, 
                         token: str, 
                         title: str, 
                         body: str, 
                         data: Dict = None,
                         config: Dict = None) -> str:
        """
        Send push notification to a single device
        """
        try:
            # Build notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token,
                android=self.build_android_config(config),
                apns=self.build_apns_config(config),
                webpush=self.build_webpush_config(config)
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(
                f"Notification sent successfully: {response}",
                extra={
                    'message_id': response,
                    'token': token[:10] + '...',  # Log partial token for privacy
                    'event_type': 'notification_sent'
                }
            )
            
            return response
            
        except messaging.UnregisteredError:
            logger.warning(f"Token unregistered: {token[:10]}...")
            raise UnregisteredTokenException("Device token is unregistered")
        
        except messaging.SenderIdMismatchError:
            logger.error(f"Sender ID mismatch for token: {token[:10]}...")
            raise SenderIdMismatchException("Sender ID mismatch")
        
        except messaging.QuotaExceededError:
            logger.error("Firebase messaging quota exceeded")
            raise QuotaExceededException("Messaging quota exceeded")
        
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            raise NotificationSendException(f"Failed to send notification: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def send_multicast_notification(self, 
                                  tokens: List[str], 
                                  title: str, 
                                  body: str, 
                                  data: Dict = None) -> Dict:
        """
        Send notification to multiple devices
        """
        try:
            # Build multicast message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens,
                android=self.build_android_config(),
                apns=self.build_apns_config(),
                webpush=self.build_webpush_config()
            )
            
            # Send multicast message
            response = messaging.send_multicast(message)
            
            # Process response
            result = {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'successful_tokens': [],
                'failed_tokens': []
            }
            
            for idx, resp in enumerate(response.responses):
                if resp.success:
                    result['successful_tokens'].append({
                        'token': tokens[idx],
                        'message_id': resp.message_id
                    })
                else:
                    result['failed_tokens'].append({
                        'token': tokens[idx],
                        'error': str(resp.exception)
                    })
            
            logger.info(
                f"Multicast notification sent: {result['success_count']} success, "
                f"{result['failure_count']} failed",
                extra={
                    'success_count': result['success_count'],
                    'failure_count': result['failure_count'],
                    'event_type': 'multicast_notification_sent'
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send multicast notification: {str(e)}")
            raise MulticastNotificationException(f"Failed to send multicast notification: {str(e)}")
    
    def build_android_config(self, config: Dict = None) -> messaging.AndroidConfig:
        """
        Build Android-specific configuration
        """
        android_config = config.get('android', {}) if config else {}
        
        return messaging.AndroidConfig(
            collapse_key=android_config.get('collapse_key'),
            priority=android_config.get('priority', 'high'),
            ttl=datetime.timedelta(seconds=android_config.get('ttl', 3600)),
            restricted_package_name=android_config.get('package_name'),
            data=android_config.get('data', {}),
            notification=messaging.AndroidNotification(
                title=android_config.get('notification', {}).get('title'),
                body=android_config.get('notification', {}).get('body'),
                icon=android_config.get('notification', {}).get('icon', 'default'),
                color=android_config.get('notification', {}).get('color', '#1976D2'),
                sound=android_config.get('notification', {}).get('sound', 'default'),
                tag=android_config.get('notification', {}).get('tag'),
                click_action=android_config.get('notification', {}).get('click_action'),
                body_loc_key=android_config.get('notification', {}).get('body_loc_key'),
                body_loc_args=android_config.get('notification', {}).get('body_loc_args'),
                title_loc_key=android_config.get('notification', {}).get('title_loc_key'),
                title_loc_args=android_config.get('notification', {}).get('title_loc_args'),
                channel_id=android_config.get('notification', {}).get('channel_id', 'default')
            )
        )
    
    def build_apns_config(self, config: Dict = None) -> messaging.APNSConfig:
        """
        Build iOS-specific configuration
        """
        apns_config = config.get('apns', {}) if config else {}
        
        return messaging.APNSConfig(
            headers=apns_config.get('headers', {}),
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(
                        title=apns_config.get('alert', {}).get('title'),
                        body=apns_config.get('alert', {}).get('body'),
                        title_loc_key=apns_config.get('alert', {}).get('title_loc_key'),
                        title_loc_args=apns_config.get('alert', {}).get('title_loc_args'),
                        action_loc_key=apns_config.get('alert', {}).get('action_loc_key'),
                        loc_key=apns_config.get('alert', {}).get('loc_key'),
                        loc_args=apns_config.get('alert', {}).get('loc_args'),
                        launch_image=apns_config.get('alert', {}).get('launch_image')
                    ),
                    badge=apns_config.get('badge'),
                    sound=apns_config.get('sound', 'default'),
                    content_available=apns_config.get('content_available', False),
                    category=apns_config.get('category'),
                    thread_id=apns_config.get('thread_id'),
                    mutable_content=apns_config.get('mutable_content', False)
                )
            )
        )
    
    def build_webpush_config(self, config: Dict = None) -> messaging.WebpushConfig:
        """
        Build Web Push configuration
        """
        webpush_config = config.get('webpush', {}) if config else {}
        
        return messaging.WebpushConfig(
            headers=webpush_config.get('headers', {}),
            data=webpush_config.get('data', {}),
            notification=webpush_config.get('notification', {}),
            fcm_options=messaging.WebpushFCMOptions(
                link=webpush_config.get('fcm_options', {}).get('link')
            )
        )
    
    def get_default_message_config(self) -> Dict:
        """
        Get default message configuration
        """
        return {
            'android': {
                'priority': 'high',
                'ttl': 3600,
                'notification': {
                    'icon': 'hdfc_notification_icon',
                    'color': '#ED1C24',  # HDFC Brand Red
                    'channel_id': 'hdfc_card_notifications'
                }
            },
            'apns': {
                'headers': {
                    'apns-priority': '10'
                },
                'sound': 'default',
                'badge': 1
            },
            'webpush': {
                'headers': {
                    'TTL': '3600'
                },
                'notification': {
                    'icon': '/assets/hdfc-icon-192x192.png',
                    'badge': '/assets/hdfc-badge-72x72.png'
                }
            }
        }
```

---

## Twilio Communication Services

### 1. Twilio Service Configuration

```python
# config/twilio_config.py
from twilio.rest import Client
from django.conf import settings
import os

class TwilioConfiguration:
    """
    Twilio service configuration and client management
    """
    
    def __init__(self):
        self.client = None
        self.verify_service_sid = None
        self.initialize_twilio()
    
    def initialize_twilio(self):
        """
        Initialize Twilio client with configuration
        """
        try:
            # Initialize Twilio client
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            
            # Set up Verify service for OTP
            self.verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
            
            # Test connection
            account = self.client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
            
            logger.info(
                f"Twilio client initialized successfully. Account: {account.friendly_name}",
                extra={'event_type': 'twilio_initialization_success'}
            )
            
        except Exception as e:
            logger.error(f"Twilio initialization failed: {str(e)}")
            raise TwilioInitializationException(f"Failed to initialize Twilio: {str(e)}")
    
    def get_client(self):
        """
        Get Twilio client instance
        """
        if not self.client:
            self.initialize_twilio()
        return self.client

# Environment Variables Configuration
TWILIO_SETTINGS = {
    'TWILIO_ACCOUNT_SID': 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    'TWILIO_AUTH_TOKEN': 'your-auth-token-here',
    'TWILIO_VERIFY_SERVICE_SID': 'VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    'TWILIO_PHONE_NUMBER': '+1234567890',
    'TWILIO_WHATSAPP_NUMBER': 'whatsapp:+1234567890',
    'TWILIO_MESSAGING_SERVICE_SID': 'MGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    'TWILIO_WEBHOOK_URL': 'https://your-domain.com/webhooks/twilio/',
    'TWILIO_STATUS_CALLBACK_URL': 'https://your-domain.com/webhooks/twilio/status/'
}
```

### 2. Twilio SMS Service

```python
# services/twilio_sms_service.py
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import phonenumbers
from typing import Dict, Optional

class TwilioSMSService:
    """
    Comprehensive Twilio SMS service with advanced features
    """
    
    def __init__(self):
        self.twilio_config = TwilioConfiguration()
        self.client = self.twilio_config.get_client()
        self.message_templates = self.load_message_templates()
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    @ServiceIntegrationPatterns.circuit_breaker(failure_threshold=3, recovery_timeout=30)
    @ServiceIntegrationPatterns.timeout_handler(timeout_seconds=15)
    def send_sms(self, 
                 to_number: str, 
                 message: str, 
                 template_id: str = None,
                 template_vars: Dict = None) -> Dict:
        """
        Send SMS with enhanced features and validation
        """
        try:
            # Validate and format phone number
            formatted_number = self.validate_and_format_phone_number(to_number)
            
            # Process message template if provided
            if template_id:
                message = self.process_message_template(template_id, template_vars or {})
            
            # Send SMS message
            message_obj = self.client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=formatted_number,
                status_callback=settings.TWILIO_STATUS_CALLBACK_URL,
                messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID if hasattr(settings, 'TWILIO_MESSAGING_SERVICE_SID') else None
            )
            
            # Prepare response
            response = {
                'success': True,
                'message_sid': message_obj.sid,
                'status': message_obj.status,
                'to': formatted_number,
                'body': message,
                'created_at': message_obj.date_created.isoformat(),
                'price': message_obj.price,
                'price_unit': message_obj.price_unit
            }
            
            logger.info(
                f"SMS sent successfully: {message_obj.sid}",
                extra={
                    'message_sid': message_obj.sid,
                    'to_number': formatted_number,
                    'template_id': template_id,
                    'event_type': 'sms_sent_success'
                }
            )
            
            return response
            
        except TwilioRestException as e:
            logger.error(f"Twilio SMS error: {e.msg} (Code: {e.code})")
            raise TwilioSMSException(f"SMS sending failed: {e.msg}")
        
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            raise SMSException(f"SMS sending failed: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def send_bulk_sms(self, recipients: List[Dict], message: str) -> Dict:
        """
        Send bulk SMS messages with batch processing
        """
        try:
            batch_size = 50  # Twilio recommendation
            results = {
                'total': len(recipients),
                'successful': 0,
                'failed': 0,
                'results': []
            }
            
            # Process in batches
            for i in range(0, len(recipients), batch_size):
                batch = recipients[i:i + batch_size]
                
                for recipient in batch:
                    try:
                        phone_number = recipient['phone_number']
                        personalized_message = message.format(**recipient.get('variables', {}))
                        
                        result = self.send_sms(
                            to_number=phone_number,
                            message=personalized_message
                        )
                        
                        results['successful'] += 1
                        results['results'].append({
                            'phone_number': phone_number,
                            'status': 'sent',
                            'message_sid': result['message_sid']
                        })
                        
                    except Exception as e:
                        results['failed'] += 1
                        results['results'].append({
                            'phone_number': recipient['phone_number'],
                            'status': 'failed',
                            'error': str(e)
                        })
                
                # Rate limiting between batches
                time.sleep(1)
            
            logger.info(
                f"Bulk SMS completed: {results['successful']} sent, {results['failed']} failed",
                extra={
                    'total_messages': results['total'],
                    'successful': results['successful'],
                    'failed': results['failed'],
                    'event_type': 'bulk_sms_completed'
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk SMS failed: {str(e)}")
            raise BulkSMSException(f"Bulk SMS failed: {str(e)}")
    
    def validate_and_format_phone_number(self, phone_number: str) -> str:
        """
        Validate and format phone number using phonenumbers library
        """
        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(phone_number, "IN")  # Default to India
            
            # Validate number
            if not phonenumbers.is_valid_number(parsed_number):
                raise InvalidPhoneNumberException(f"Invalid phone number: {phone_number}")
            
            # Format for international use
            formatted_number = phonenumbers.format_number(
                parsed_number, 
                phonenumbers.PhoneNumberFormat.E164
            )
            
            return formatted_number
            
        except phonenumbers.NumberParseException as e:
            raise PhoneNumberParseException(f"Phone number parsing failed: {str(e)}")
    
    def process_message_template(self, template_id: str, variables: Dict) -> str:
        """
        Process message template with variables
        """
        template = self.message_templates.get(template_id)
        if not template:
            raise TemplateNotFoundException(f"Template not found: {template_id}")
        
        try:
            # Process template variables
            processed_message = template['content'].format(**variables)
            
            # Validate message length (SMS limit is 160 characters for single SMS)
            if len(processed_message) > 1600:  # 10 SMS segments max
                logger.warning(f"Message too long: {len(processed_message)} characters")
            
            return processed_message
            
        except KeyError as e:
            raise TemplateVariableException(f"Missing template variable: {str(e)}")
    
    def load_message_templates(self) -> Dict:
        """
        Load SMS message templates
        """
        return {
            'otp_verification': {
                'content': 'Your HDFC Card Limit verification code is: {otp_code}. Do not share this code with anyone. Valid for {expiry_minutes} minutes.',
                'category': 'security'
            },
            'limit_increase_approved': {
                'content': 'Good news! Your {card_type} card limit increase request for ₹{new_limit} has been approved. Reference: {reference_number}',
                'category': 'notification'
            },
            'limit_increase_rejected': {
                'content': 'Your {card_type} card limit increase request has been declined. For details, call 18002586161. Reference: {reference_number}',
                'category': 'notification'
            },
            'netbanking_limit_approved': {
                'content': 'Your netbanking transaction limit has been updated to ₹{new_limit}. Reference: {reference_number}',
                'category': 'notification'
            },
            'account_locked': {
                'content': 'Your HDFC account has been temporarily locked due to security reasons. Please visit nearest branch or call 18002586161.',
                'category': 'security'
            },
            'welcome_message': {
                'content': 'Welcome to HDFC Card Limit System! Your account has been successfully created. Download our app for easy limit management.',
                'category': 'onboarding'
            }
        }
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def get_message_status(self, message_sid: str) -> Dict:
        """
        Get SMS message delivery status
        """
        try:
            message = self.client.messages(message_sid).fetch()
            
            status_info = {
                'message_sid': message.sid,
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'price': message.price,
                'price_unit': message.price_unit,
                'direction': message.direction,
                'created_at': message.date_created.isoformat(),
                'sent_at': message.date_sent.isoformat() if message.date_sent else None,
                'updated_at': message.date_updated.isoformat() if message.date_updated else None
            }
            
            return status_info
            
        except TwilioRestException as e:
            logger.error(f"Failed to get message status: {e.msg}")
            raise MessageStatusException(f"Failed to get message status: {e.msg}")
```

### 3. Twilio Voice Service

```python
# services/twilio_voice_service.py
from twilio.twiml import VoiceResponse
import xml.etree.ElementTree as ET

class TwilioVoiceService:
    """
    Twilio Voice service for voice calls and IVR
    """
    
    def __init__(self):
        self.twilio_config = TwilioConfiguration()
        self.client = self.twilio_config.get_client()
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    @ServiceIntegrationPatterns.circuit_breaker(failure_threshold=3, recovery_timeout=30)
    def make_voice_call(self, 
                       to_number: str, 
                       message: str = None,
                       twiml_url: str = None) -> Dict:
        """
        Make voice call with text-to-speech or TwiML
        """
        try:
            formatted_number = self.validate_and_format_phone_number(to_number)
            
            if message:
                # Create TwiML for text-to-speech
                twiml_response = VoiceResponse()
                twiml_response.say(
                    message,
                    voice='alice',
                    language='en-IN'
                )
                twiml_content = str(twiml_response)
            else:
                twiml_content = twiml_url
            
            call = self.client.calls.create(
                twiml=twiml_content if message else None,
                url=twiml_url if not message else None,
                to=formatted_number,
                from_=settings.TWILIO_PHONE_NUMBER,
                status_callback=settings.TWILIO_STATUS_CALLBACK_URL,
                record=True  # Record call for compliance
            )
            
            response = {
                'success': True,
                'call_sid': call.sid,
                'status': call.status,
                'to': formatted_number,
                'created_at': call.date_created.isoformat()
            }
            
            logger.info(
                f"Voice call initiated: {call.sid}",
                extra={
                    'call_sid': call.sid,
                    'to_number': formatted_number,
                    'event_type': 'voice_call_initiated'
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Voice call failed: {str(e)}")
            raise VoiceCallException(f"Voice call failed: {str(e)}")
    
    def create_ivr_response(self, user_input: str = None) -> str:
        """
        Create IVR response based on user input
        """
        response = VoiceResponse()
        
        if not user_input:
            # Main menu
            gather = response.gather(
                num_digits=1,
                action='/webhooks/twilio/voice/gather/',
                method='POST',
                timeout=10
            )
            
            gather.say(
                "Welcome to HDFC Card Limit System. "
                "Press 1 for card limit increase, "
                "Press 2 for netbanking limit, "
                "Press 3 to speak with representative, "
                "Press 9 to repeat this menu.",
                voice='alice',
                language='en-IN'
            )
            
            response.redirect('/webhooks/twilio/voice/gather/')
            
        else:
            if user_input == '1':
                response.say(
                    "For card limit increase, please use our mobile app or visit our website. "
                    "You can also visit your nearest HDFC branch.",
                    voice='alice',
                    language='en-IN'
                )
            elif user_input == '2':
                response.say(
                    "For netbanking limit changes, please log into your netbanking account "
                    "or use our mobile app.",
                    voice='alice',
                    language='en-IN'
                )
            elif user_input == '3':
                response.say(
                    "Please hold while we connect you to our customer service representative.",
                    voice='alice',
                    language='en-IN'
                )
                response.dial('+1800-258-6161')  # HDFC customer care
            elif user_input == '9':
                response.redirect('/webhooks/twilio/voice/')
            else:
                response.say(
                    "Invalid selection. Please try again.",
                    voice='alice',
                    language='en-IN'
                )
                response.redirect('/webhooks/twilio/voice/')
        
        return str(response)
```

### 4. Twilio WhatsApp Integration

```python
# services/twilio_whatsapp_service.py
class TwilioWhatsAppService:
    """
    Twilio WhatsApp Business API service
    """
    
    def __init__(self):
        self.twilio_config = TwilioConfiguration()
        self.client = self.twilio_config.get_client()
        self.whatsapp_templates = self.load_whatsapp_templates()
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    @ServiceIntegrationPatterns.circuit_breaker(failure_threshold=3, recovery_timeout=30)
    def send_whatsapp_message(self, 
                             to_number: str, 
                             template_name: str,
                             template_vars: Dict = None,
                             media_url: str = None) -> Dict:
        """
        Send WhatsApp message using approved templates
        """
        try:
            formatted_number = f"whatsapp:{self.validate_and_format_phone_number(to_number)}"
            
            # Process template
            template = self.whatsapp_templates.get(template_name)
            if not template:
                raise TemplateNotFoundException(f"WhatsApp template not found: {template_name}")
            
            message_body = template['content'].format(**(template_vars or {}))
            
            # Create message parameters
            message_params = {
                'body': message_body,
                'from_': settings.TWILIO_WHATSAPP_NUMBER,
                'to': formatted_number,
                'status_callback': settings.TWILIO_STATUS_CALLBACK_URL
            }
            
            # Add media if provided
            if media_url:
                message_params['media_url'] = [media_url]
            
            # Send message
            message = self.client.messages.create(**message_params)
            
            response = {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'to': formatted_number,
                'template_name': template_name,
                'created_at': message.date_created.isoformat()
            }
            
            logger.info(
                f"WhatsApp message sent: {message.sid}",
                extra={
                    'message_sid': message.sid,
                    'to_number': formatted_number,
                    'template_name': template_name,
                    'event_type': 'whatsapp_message_sent'
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"WhatsApp message failed: {str(e)}")
            raise WhatsAppMessageException(f"WhatsApp message failed: {str(e)}")
    
    def load_whatsapp_templates(self) -> Dict:
        """
        Load WhatsApp approved message templates
        """
        return {
            'otp_verification': {
                'content': '🔐 Your HDFC verification code: *{}*\n\nDo not share this code with anyone.\nValid for {} minutes.\n\n_This is an automated message from HDFC Bank._',
                'variables': ['otp_code', 'expiry_minutes'],
                'category': 'security'
            },
            'limit_approved': {
                'content': '✅ *Great News!*\n\nYour {} card limit increase to *₹{}* has been approved!\n\n📝 Reference: {}\n\n_HDFC Bank - Your trusted banking partner_',
                'variables': ['card_type', 'new_limit', 'reference_number'],
                'category': 'notification'
            },
            'welcome_message': {
                'content': '🎉 *Welcome to HDFC Card Limit System!*\n\nYour account is ready. You can now:\n• Request card limit increases\n• Manage netbanking limits\n• Track request status\n\nDownload our app for better experience!\n\n_HDFC Bank - We understand your world_',
                'variables': [],
                'category': 'onboarding'
            }
        }
```

---

## SendGrid Email Services

### 1. SendGrid Configuration

```python
# config/sendgrid_config.py
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
from django.conf import settings
import base64

class SendGridConfiguration:
    """
    SendGrid service configuration and client management
    """
    
    def __init__(self):
        self.client = None
        self.initialize_sendgrid()
    
    def initialize_sendgrid(self):
        """
        Initialize SendGrid client
        """
        try:
            self.client = sendgrid.SendGridAPIClient(
                api_key=settings.SENDGRID_API_KEY
            )
            
            # Test API key validity
            response = self.client.user.get()
            
            logger.info(
                "SendGrid client initialized successfully",
                extra={'event_type': 'sendgrid_initialization_success'}
            )
            
        except Exception as e:
            logger.error(f"SendGrid initialization failed: {str(e)}")
            raise SendGridInitializationException(f"Failed to initialize SendGrid: {str(e)}")
    
    def get_client(self):
        """
        Get SendGrid client instance
        """
        if not self.client:
            self.initialize_sendgrid()
        return self.client

# Environment Variables Configuration
SENDGRID_SETTINGS = {
    'SENDGRID_API_KEY': 'SG.your-api-key',
    'SENDGRID_FROM_EMAIL': 'noreply@hdfc.bank',
    'SENDGRID_FROM_NAME': 'HDFC Bank',
    'SENDGRID_REPLY_TO_EMAIL': 'support@hdfc.bank',
    'SENDGRID_TEMPLATE_ID_WELCOME': 'd-1234567890abcdef1234567890abcdef',
    'SENDGRID_TEMPLATE_ID_OTP': 'd-abcdef1234567890abcdef1234567890',
    'SENDGRID_TEMPLATE_ID_APPROVAL': 'd-567890abcdef1234567890abcdef1234',
    'SENDGRID_UNSUBSCRIBE_GROUP_ID': 12345,
    'SENDGRID_WEBHOOK_URL': 'https://your-domain.com/webhooks/sendgrid/'
}
```

### 2. SendGrid Email Service

```python
# services/sendgrid_email_service.py
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Attachment, 
    FileContent, FileName, FileType, Disposition
)
import json
from typing import List, Dict, Optional

class SendGridEmailService:
    """
    Comprehensive SendGrid email service
    """
    
    def __init__(self):
        self.sendgrid_config = SendGridConfiguration()
        self.client = self.sendgrid_config.get_client()
        self.email_templates = self.load_email_templates()
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    @ServiceIntegrationPatterns.circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @ServiceIntegrationPatterns.timeout_handler(timeout_seconds=30)
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   content: str,
                   content_type: str = "text/html",
                   template_id: str = None,
                   template_data: Dict = None,
                   attachments: List[Dict] = None) -> Dict:
        """
        Send email with advanced features
        """
        try:
            # Create email object
            from_email = Email(
                email=settings.SENDGRID_FROM_EMAIL,
                name=settings.SENDGRID_FROM_NAME
            )
            
            # Handle multiple recipients
            to_list = [To(email=email) for email in to_emails]
            
            # Create mail object
            if template_id:
                # Use dynamic template
                mail = Mail(
                    from_email=from_email,
                    to_emails=to_list[0] if len(to_list) == 1 else to_list
                )
                mail.template_id = template_id
                
                if template_data:
                    mail.dynamic_template_data = template_data
            else:
                # Use static content
                content_obj = Content(content_type, content)
                mail = Mail(
                    from_email=from_email,
                    to_emails=to_list[0] if len(to_list) == 1 else to_list,
                    subject=subject,
                    html_content=content_obj
                )
            
            # Add attachments
            if attachments:
                for attachment_data in attachments:
                    attachment = Attachment(
                        FileContent(attachment_data['content']),
                        FileName(attachment_data['filename']),
                        FileType(attachment_data['type']),
                        Disposition('attachment')
                    )
                    mail.attachment = attachment
            
            # Add email settings
            mail.reply_to = Email(settings.SENDGRID_REPLY_TO_EMAIL)
            
            # Add tracking settings
            mail.tracking_settings = {
                "click_tracking": {
                    "enable": True,
                    "enable_text": False
                },
                "open_tracking": {
                    "enable": True,
                    "substitution_tag": "%open-track%"
                },
                "subscription_tracking": {
                    "enable": True,
                    "text": "If you would like to unsubscribe and stop receiving these emails click here: <%unsubscribe%>.",
                    "html": "<p>If you would like to unsubscribe and stop receiving these emails <% click here %>.</p>",
                    "substitution_tag": "<%unsubscribe%>"
                }
            }
            
            # Add ASM (Advanced Suppression Management)
            mail.asm = {
                "group_id": settings.SENDGRID_UNSUBSCRIBE_GROUP_ID
            }
            
            # Send email
            response = self.client.send(mail)
            
            # Process response
            result = {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'message_id': response.headers.get('X-Message-Id'),
                'to_emails': to_emails,
                'template_id': template_id,
                'sent_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Email sent successfully: {result['message_id']}",
                extra={
                    'message_id': result['message_id'],
                    'to_emails': to_emails,
                    'template_id': template_id,
                    'event_type': 'email_sent_success'
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            raise EmailSendException(f"Email sending failed: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def send_bulk_email(self, 
                       recipients: List[Dict], 
                       template_id: str,
                       global_data: Dict = None) -> Dict:
        """
        Send bulk emails using SendGrid's batch functionality
        """
        try:
            # Prepare recipient list with personalization
            personalizations = []
            batch_size = 1000  # SendGrid limit
            
            for i in range(0, len(recipients), batch_size):
                batch = recipients[i:i + batch_size]
                
                for recipient in batch:
                    personalization = {
                        "to": [{"email": recipient['email']}],
                        "dynamic_template_data": {
                            **global_data or {},
                            **recipient.get('data', {})
                        }
                    }
                    personalizations.append(personalization)
            
            # Create mail object
            mail = Mail()
            mail.from_email = Email(
                email=settings.SENDGRID_FROM_EMAIL,
                name=settings.SENDGRID_FROM_NAME
            )
            mail.template_id = template_id
            mail.personalizations = personalizations
            
            # Send batch email
            response = self.client.send(mail)
            
            result = {
                'success': True,
                'status_code': response.status_code,
                'message_id': response.headers.get('X-Message-Id'),
                'batch_id': response.headers.get('X-Batch-Id'),
                'total_recipients': len(recipients),
                'template_id': template_id,
                'sent_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Bulk email sent successfully: {result['message_id']}",
                extra={
                    'message_id': result['message_id'],
                    'batch_id': result['batch_id'],
                    'total_recipients': len(recipients),
                    'template_id': template_id,
                    'event_type': 'bulk_email_sent_success'
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Bulk email sending failed: {str(e)}")
            raise BulkEmailException(f"Bulk email sending failed: {str(e)}")
    
    def load_email_templates(self) -> Dict:
        """
        Load email template configurations
        """
        return {
            'welcome': {
                'template_id': settings.SENDGRID_TEMPLATE_ID_WELCOME,
                'subject': 'Welcome to HDFC Card Limit System',
                'category': 'onboarding'
            },
            'otp_verification': {
                'template_id': settings.SENDGRID_TEMPLATE_ID_OTP,
                'subject': 'Your HDFC Verification Code',
                'category': 'security'
            },
            'limit_approved': {
                'template_id': settings.SENDGRID_TEMPLATE_ID_APPROVAL,
                'subject': 'Card Limit Increase Approved',
                'category': 'notification'
            },
            'monthly_statement': {
                'template_id': 'd-monthly-statement-template',
                'subject': 'Your Monthly Card Statement',
                'category': 'statement'
            }
        }
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def get_email_statistics(self, start_date: str, end_date: str) -> Dict:
        """
        Get email delivery statistics
        """
        try:
            response = self.client.stats.get(
                start_date=start_date,
                end_date=end_date,
                aggregated_by='day'
            )
            
            stats_data = response.body
            
            return {
                'success': True,
                'statistics': stats_data,
                'period': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Failed to get email statistics: {str(e)}")
            raise EmailStatsException(f"Failed to get email statistics: {str(e)}")
```

---

## OneSignal Push Notifications

### 1. OneSignal Configuration

```python
# config/onesignal_config.py
import requests
import json
from django.conf import settings

class OneSignalConfiguration:
    """
    OneSignal service configuration and client management
    """
    
    def __init__(self):
        self.app_id = settings.ONESIGNAL_APP_ID
        self.rest_api_key = settings.ONESIGNAL_REST_API_KEY
        self.user_auth_key = settings.ONESIGNAL_USER_AUTH_KEY
        self.base_url = "https://onesignal.com/api/v1"
        self.validate_configuration()
    
    def validate_configuration(self):
        """
        Validate OneSignal configuration
        """
        try:
            headers = {
                "Authorization": f"Basic {self.rest_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/apps/{self.app_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("OneSignal configuration validated successfully")
            else:
                raise OneSignalConfigException(f"Invalid OneSignal configuration: {response.status_code}")
                
        except Exception as e:
            logger.error(f"OneSignal configuration validation failed: {str(e)}")
            raise OneSignalInitializationException(f"Failed to validate OneSignal: {str(e)}")

# Environment Variables Configuration
ONESIGNAL_SETTINGS = {
    'ONESIGNAL_APP_ID': 'your-app-id',
    'ONESIGNAL_REST_API_KEY': 'your-rest-api-key',
    'ONESIGNAL_USER_AUTH_KEY': 'your-user-auth-key',
    'ONESIGNAL_WEBHOOK_URL': 'https://your-domain.com/webhooks/onesignal/'
}
```

### 2. OneSignal Push Notification Service

```python
# services/onesignal_push_service.py
import requests
import json
from typing import Dict, List, Optional

class OneSignalPushService:
    """
    Comprehensive OneSignal push notification service
    """
    
    def __init__(self):
        self.onesignal_config = OneSignalConfiguration()
        self.notification_templates = self.load_notification_templates()
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    @ServiceIntegrationPatterns.circuit_breaker(failure_threshold=3, recovery_timeout=30)
    @ServiceIntegrationPatterns.timeout_handler(timeout_seconds=15)
    def send_notification(self, 
                         player_ids: List[str] = None,
                         external_user_ids: List[str] = None,
                         segments: List[str] = None,
                         filters: List[Dict] = None,
                         headings: Dict = None,
                         contents: Dict = None,
                         template_id: str = None,
                         template_data: Dict = None,
                         **kwargs) -> Dict:
        """
        Send push notification with advanced targeting
        """
        try:
            # Prepare notification data
            notification_data = {
                "app_id": self.onesignal_config.app_id
            }
            
            # Set targeting
            if player_ids:
                notification_data["include_player_ids"] = player_ids
            elif external_user_ids:
                notification_data["include_external_user_ids"] = external_user_ids
            elif segments:
                notification_data["included_segments"] = segments
            elif filters:
                notification_data["filters"] = filters
            else:
                notification_data["included_segments"] = ["Active Users"]
            
            # Set content
            if template_id:
                template = self.notification_templates.get(template_id)
                if not template:
                    raise NotificationTemplateException(f"Template not found: {template_id}")
                
                notification_data.update(self.process_template(template, template_data or {}))
            else:
                if headings:
                    notification_data["headings"] = headings
                if contents:
                    notification_data["contents"] = contents
            
            # Add additional parameters
            notification_data.update({
                "data": kwargs.get("data", {}),
                "url": kwargs.get("url"),
                "web_url": kwargs.get("web_url"),
                "app_url": kwargs.get("app_url"),
                "ios_badgeType": kwargs.get("ios_badge_type", "Increase"),
                "ios_badgeCount": kwargs.get("ios_badge_count", 1),
                "android_channel_id": kwargs.get("android_channel_id", "hdfc_notifications"),
                "small_icon": kwargs.get("small_icon", "hdfc_notification_icon"),
                "large_icon": kwargs.get("large_icon", "hdfc_large_icon"),
                "big_picture": kwargs.get("big_picture"),
                "adm_big_picture": kwargs.get("adm_big_picture"),
                "chrome_big_picture": kwargs.get("chrome_big_picture"),
                "priority": kwargs.get("priority", 10),
                "ttl": kwargs.get("ttl", 259200),  # 3 days
                "delayed_option": kwargs.get("delayed_option", "immediate"),
                "delivery_time_of_day": kwargs.get("delivery_time_of_day"),
                "send_after": kwargs.get("send_after")
            })
            
            # Remove None values
            notification_data = {k: v for k, v in notification_data.items() if v is not None}
            
            # Send notification
            headers = {
                "Authorization": f"Basic {self.onesignal_config.rest_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.onesignal_config.base_url}/notifications",
                headers=headers,
                data=json.dumps(notification_data),
                timeout=15
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Process response
            notification_response = {
                'success': True,
                'notification_id': result.get('id'),
                'recipients': result.get('recipients'),
                'external_id': result.get('external_id'),
                'errors': result.get('errors'),
                'warnings': result.get('warnings'),
                'sent_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Push notification sent successfully: {notification_response['notification_id']}",
                extra={
                    'notification_id': notification_response['notification_id'],
                    'recipients': notification_response['recipients'],
                    'template_id': template_id,
                    'event_type': 'push_notification_sent'
                }
            )
            
            return notification_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OneSignal API request failed: {str(e)}")
            raise OneSignalAPIException(f"OneSignal API request failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Push notification failed: {str(e)}")
            raise PushNotificationException(f"Push notification failed: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def send_scheduled_notification(self, 
                                  scheduled_time: str,
                                  timezone: str = "Asia/Kolkata",
                                  **notification_params) -> Dict:
        """
        Send scheduled push notification
        """
        try:
            # Add scheduling parameters
            notification_params.update({
                "send_after": scheduled_time,
                "delayed_option": "timezone",
                "delivery_time_of_day": notification_params.get("delivery_time_of_day", "9:00AM")
            })
            
            return self.send_notification(**notification_params)
            
        except Exception as e:
            logger.error(f"Scheduled notification failed: {str(e)}")
            raise ScheduledNotificationException(f"Scheduled notification failed: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def create_player(self, 
                     device_token: str,
                     device_type: int,
                     external_user_id: str = None,
                     tags: Dict = None) -> Dict:
        """
        Create or update a player (device) in OneSignal
        """
        try:
            player_data = {
                "app_id": self.onesignal_config.app_id,
                "device_type": device_type,  # 0=iOS, 1=Android, 5=Web
                "identifier": device_token,
                "timezone": -19800,  # India timezone offset
                "game_version": "1.0.0",
                "device_model": "Unknown",
                "device_os": "Unknown",
                "ad_id": "",
                "sdk": "Custom API"
            }
            
            if external_user_id:
                player_data["external_user_id"] = external_user_id
            
            if tags:
                player_data["tags"] = tags
            
            headers = {
                "Authorization": f"Basic {self.onesignal_config.rest_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.onesignal_config.base_url}/players",
                headers=headers,
                data=json.dumps(player_data),
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            player_response = {
                'success': result.get('success', True),
                'player_id': result.get('id'),
                'external_user_id': external_user_id,
                'device_type': device_type,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Player created successfully: {player_response['player_id']}",
                extra={
                    'player_id': player_response['player_id'],
                    'external_user_id': external_user_id,
                    'device_type': device_type,
                    'event_type': 'player_created'
                }
            )
            
            return player_response
            
        except Exception as e:
            logger.error(f"Player creation failed: {str(e)}")
            raise PlayerCreationException(f"Player creation failed: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def update_player_tags(self, player_id: str, tags: Dict) -> Dict:
        """
        Update player tags for segmentation
        """
        try:
            headers = {
                "Authorization": f"Basic {self.onesignal_config.rest_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.put(
                f"{self.onesignal_config.base_url}/players/{player_id}",
                headers=headers,
                data=json.dumps({"tags": tags}),
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': result.get('success', True),
                'player_id': player_id,
                'tags': tags,
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Player tags update failed: {str(e)}")
            raise PlayerTagsException(f"Player tags update failed: {str(e)}")
    
    def load_notification_templates(self) -> Dict:
        """
        Load push notification templates
        """
        return {
            'otp_verification': {
                'headings': {
                    'en': '🔐 HDFC Verification Code',
                    'hi': '🔐 एचडीएफसी सत्यापन कोड'
                },
                'contents': {
                    'en': 'Your verification code is: {{otp_code}}. Valid for {{expiry_minutes}} minutes.',
                    'hi': 'आपका सत्यापन कोड: {{otp_code}}। {{expiry_minutes}} मिनट के लिए वैध।'
                },
                'android_channel_id': 'hdfc_security',
                'category': 'security'
            },
            'limit_approved': {
                'headings': {
                    'en': '✅ Limit Increase Approved',
                    'hi': '✅ सीमा वृद्धि स्वीकृत'
                },
                'contents': {
                    'en': 'Your {{card_type}} card limit has been increased to ₹{{new_limit}}.',
                    'hi': 'आपकी {{card_type}} कार्ड सीमा ₹{{new_limit}} तक बढ़ा दी गई है।'
                },
                'android_channel_id': 'hdfc_notifications',
                'category': 'approval'
            },
            'welcome': {
                'headings': {
                    'en': '🎉 Welcome to HDFC',
                    'hi': '🎉 एचडीएफसी में आपका स्वागत है'
                },
                'contents': {
                    'en': 'Your account is ready! Start managing your card limits easily.',
                    'hi': 'आपका खाता तैयार है! अपनी कार्ड सीमा आसानी से प्रबंधित करना शुरू करें।'
                },
                'android_channel_id': 'hdfc_onboarding',
                'category': 'onboarding'
            }
        }
    
    def process_template(self, template: Dict, data: Dict) -> Dict:
        """
        Process notification template with data
        """
        processed_template = {}
        
        # Process headings
        if 'headings' in template:
            processed_headings = {}
            for lang, heading in template['headings'].items():
                processed_headings[lang] = self.replace_template_variables(heading, data)
            processed_template['headings'] = processed_headings
        
        # Process contents
        if 'contents' in template:
            processed_contents = {}
            for lang, content in template['contents'].items():
                processed_contents[lang] = self.replace_template_variables(content, data)
            processed_template['contents'] = processed_contents
        
        # Add other template properties
        for key, value in template.items():
            if key not in ['headings', 'contents']:
                processed_template[key] = value
        
        return processed_template
    
    def replace_template_variables(self, text: str, data: Dict) -> str:
        """
        Replace template variables in text
        """
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            text = text.replace(placeholder, str(value))
        
        return text
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def get_notification_history(self, 
                               limit: int = 50,
                               offset: int = 0) -> Dict:
        """
        Get notification send history
        """
        try:
            headers = {
                "Authorization": f"Basic {self.onesignal_config.rest_api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "limit": limit,
                "offset": offset
            }
            
            response = requests.get(
                f"{self.onesignal_config.base_url}/notifications",
                headers=headers,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': True,
                'notifications': result.get('notifications', []),
                'total_count': result.get('total_count', 0),
                'offset': offset,
                'limit': limit
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification history: {str(e)}")
            raise NotificationHistoryException(f"Failed to get notification history: {str(e)}")
```

---

## Oracle Database Integration

### 1. Oracle Database Configuration

```python
# config/oracle_config.py
import cx_Oracle
from django.conf import settings
import threading
import time

class OracleConfiguration:
    """
    Oracle database configuration and connection management
    """
    
    def __init__(self):
        self.connection_pool = None
        self.initialize_oracle()
    
    def initialize_oracle(self):
        """
        Initialize Oracle connection pool
        """
        try:
            # Initialize Oracle client
            cx_Oracle.init_oracle_client(
                lib_dir=settings.ORACLE_CLIENT_LIB_DIR if hasattr(settings, 'ORACLE_CLIENT_LIB_DIR') else None
            )
            
            # Create connection pool
            self.connection_pool = cx_Oracle.SessionPool(
                user=settings.ORACLE_USER,
                password=settings.ORACLE_PASSWORD,
                dsn=settings.ORACLE_DSN,
                min=settings.ORACLE_POOL_MIN,
                max=settings.ORACLE_POOL_MAX,
                increment=settings.ORACLE_POOL_INCREMENT,
                threaded=True,
                encoding="UTF-8",
                nencoding="UTF-8"
            )
            
            logger.info(
                f"Oracle connection pool initialized: {self.connection_pool.opened} connections",
                extra={'event_type': 'oracle_pool_initialized'}
            )
            
        except cx_Oracle.Error as e:
            logger.error(f"Oracle initialization failed: {str(e)}")
            raise OracleInitializationException(f"Failed to initialize Oracle: {str(e)}")
    
    def get_connection(self):
        """
        Get connection from pool
        """
        try:
            return self.connection_pool.acquire()
        except cx_Oracle.Error as e:
            logger.error(f"Failed to acquire Oracle connection: {str(e)}")
            raise OracleConnectionException(f"Failed to acquire connection: {str(e)}")
    
    def release_connection(self, connection):
        """
        Release connection back to pool
        """
        try:
            self.connection_pool.release(connection)
        except cx_Oracle.Error as e:
            logger.error(f"Failed to release Oracle connection: {str(e)}")

# Environment Variables Configuration
ORACLE_SETTINGS = {
    'ORACLE_USER': 'hdfc_card_system',
    'ORACLE_PASSWORD': 'your-password',
    'ORACLE_DSN': 'localhost:1521/XE',
    'ORACLE_POOL_MIN': 5,
    'ORACLE_POOL_MAX': 50,
    'ORACLE_POOL_INCREMENT': 5,
    'ORACLE_CLIENT_LIB_DIR': '/opt/oracle/instantclient_21_1'
}
```

### 2. Oracle Database Service

```python
# services/oracle_db_service.py
import cx_Oracle
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

class OracleDBService:
    """
    Comprehensive Oracle database service
    """
    
    def __init__(self):
        self.oracle_config = OracleConfiguration()
        self.connection_pool = self.oracle_config.connection_pool
    
    @contextmanager
    def get_db_connection(self):
        """
        Context manager for database connections
        """
        connection = None
        try:
            connection = self.oracle_config.get_connection()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                self.oracle_config.release_connection(connection)
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    @ServiceIntegrationPatterns.circuit_breaker(failure_threshold=10, recovery_timeout=120)
    def execute_query(self, 
                     query: str, 
                     params: Dict = None,
                     fetch_mode: str = 'all') -> List[Dict]:
        """
        Execute SELECT query with enhanced error handling
        """
        try:
            with self.get_db_connection() as connection:
                cursor = connection.cursor()
                
                # Set row factory for dictionary results
                cursor.rowfactory = self.row_factory
                
                # Execute query
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Fetch results based on mode
                if fetch_mode == 'one':
                    result = cursor.fetchone()
                    return [result] if result else []
                elif fetch_mode == 'many':
                    return cursor.fetchmany(numRows=1000)
                else:  # 'all'
                    return cursor.fetchall()
                    
        except cx_Oracle.Error as e:
            logger.error(f"Oracle query execution failed: {str(e)}")
            raise OracleQueryException(f"Query execution failed: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def execute_procedure(self, 
                         procedure_name: str, 
                         params: Dict = None) -> Dict:
        """
        Execute stored procedure with parameters
        """
        try:
            with self.get_db_connection() as connection:
                cursor = connection.cursor()
                
                # Prepare parameters
                proc_params = []
                out_params = {}
                
                if params:
                    for key, value in params.items():
                        if isinstance(value, dict) and value.get('direction') == 'out':
                            # Output parameter
                            var = cursor.var(value['type'])
                            proc_params.append(var)
                            out_params[key] = var
                        else:
                            # Input parameter
                            proc_params.append(value)
                
                # Execute procedure
                cursor.callproc(procedure_name, proc_params)
                
                # Extract output parameters
                result = {}
                for key, var in out_params.items():
                    result[key] = var.getvalue()
                
                connection.commit()
                
                logger.info(
                    f"Stored procedure executed successfully: {procedure_name}",
                    extra={
                        'procedure_name': procedure_name,
                        'event_type': 'stored_procedure_executed'
                    }
                )
                
                return result
                
        except cx_Oracle.Error as e:
            logger.error(f"Stored procedure execution failed: {str(e)}")
            raise OracleProcedureException(f"Procedure execution failed: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def execute_transaction(self, operations: List[Dict]) -> Dict:
        """
        Execute multiple operations in a transaction
        """
        try:
            with self.get_db_connection() as connection:
                cursor = connection.cursor()
                results = []
                
                # Begin transaction
                for operation in operations:
                    op_type = operation['type']
                    
                    if op_type == 'query':
                        cursor.execute(operation['sql'], operation.get('params', {}))
                        if operation.get('fetch', False):
                            cursor.rowfactory = self.row_factory
                            results.append(cursor.fetchall())
                    
                    elif op_type == 'procedure':
                        result = self.execute_procedure_in_cursor(
                            cursor, 
                            operation['name'], 
                            operation.get('params', {})
                        )
                        results.append(result)
                    
                    elif op_type == 'bulk_insert':
                        cursor.executemany(operation['sql'], operation['data'])
                        results.append({'rows_affected': cursor.rowcount})
                
                # Commit transaction
                connection.commit()
                
                logger.info(
                    f"Transaction completed successfully: {len(operations)} operations",
                    extra={
                        'operations_count': len(operations),
                        'event_type': 'transaction_completed'
                    }
                )
                
                return {
                    'success': True,
                    'operations_count': len(operations),
                    'results': results
                }
                
        except cx_Oracle.Error as e:
            logger.error(f"Transaction failed: {str(e)}")
            raise OracleTransactionException(f"Transaction failed: {str(e)}")
    
    def row_factory(self, cursor):
        """
        Row factory to convert cursor results to dictionaries
        """
        columns = [col[0].lower() for col in cursor.description]
        
        def create_row(*args):
            return dict(zip(columns, args))
        
        return create_row
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def get_table_statistics(self, table_name: str) -> Dict:
        """
        Get table statistics for monitoring
        """
        try:
            query = """
                SELECT 
                    table_name,
                    num_rows,
                    blocks,
                    empty_blocks,
                    avg_space,
                    chain_cnt,
                    avg_row_len,
                    last_analyzed
                FROM user_tables 
                WHERE table_name = UPPER(:table_name)
            """
            
            result = self.execute_query(query, {'table_name': table_name}, 'one')
            
            if result:
                return result[0]
            else:
                raise TableNotFoundException(f"Table not found: {table_name}")
                
        except Exception as e:
            logger.error(f"Failed to get table statistics: {str(e)}")
            raise TableStatsException(f"Failed to get table statistics: {str(e)}")
    
    @ServiceIntegrationPatterns.retry_with_exponential_backoff
    def get_session_info(self) -> Dict:
        """
        Get current session information
        """
        try:
            query = """
                SELECT 
                    sid,
                    serial#,
                    username,
                    status,
                    machine,
                    program,
                    logon_time,
                    last_call_et
                FROM v$session 
                WHERE username = USER
            """
            
            sessions = self.execute_query(query)
            
            return {
                'active_sessions': len(sessions),
                'sessions': sessions,
                'pool_status': {
                    'opened': self.connection_pool.opened,
                    'busy': self.connection_pool.busy,
                    'max': self.connection_pool.max,
                    'min': self.connection_pool.min
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get session info: {str(e)}")
            raise SessionInfoException(f"Failed to get session info: {str(e)}")
    
    def execute_procedure_in_cursor(self, cursor, procedure_name: str, params: Dict) -> Dict:
        """
        Execute stored procedure within existing cursor (for transactions)
        """
        proc_params = []
        out_params = {}
        
        if params:
            for key, value in params.items():
                if isinstance(value, dict) and value.get('direction') == 'out':
                    var = cursor.var(value['type'])
                    proc_params.append(var)
                    out_params[key] = var
                else:
                    proc_params.append(value)
        
        cursor.callproc(procedure_name, proc_params)
        
        result = {}
        for key, var in out_params.items():
            result[key] = var.getvalue()
        
        return result
```

---

## Error Handling & Monitoring

### 1. Service Health Monitoring

```python
# monitoring/service_health_monitor.py
import time
import threading
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    service_name: str
    status: ServiceStatus
    response_time: float
    last_check: float
    error_message: str = None
    metadata: Dict = None

class ServiceHealthMonitor:
    """
    Monitor health of external services
    """
    
    def __init__(self):
        self.health_checks = {}
        self.monitoring_thread = None
        self.monitoring_interval = 60  # seconds
        self.is_monitoring = False
        self.service_configs = self.get_service_configurations()
    
    def start_monitoring(self):
        """
        Start health monitoring in background thread
        """
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitor_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            logger.info("Service health monitoring started")
    
    def stop_monitoring(self):
        """
        Stop health monitoring
        """
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            
        logger.info("Service health monitoring stopped")
    
    def _monitor_loop(self):
        """
        Main monitoring loop
        """
        while self.is_monitoring:
            try:
                for service_name in self.service_configs.keys():
                    self.check_service_health(service_name)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}")
                time.sleep(self.monitoring_interval)
    
    def check_service_health(self, service_name: str) -> HealthCheck:
        """
        Check health of a specific service
        """
        start_time = time.time()
        
        try:
            config = self.service_configs.get(service_name)
            if not config:
                raise ValueError(f"Unknown service: {service_name}")
            
            # Perform health check based on service type
            if service_name == 'firebase':
                health_result = self._check_firebase_health()
            elif service_name == 'twilio':
                health_result = self._check_twilio_health()
            elif service_name == 'sendgrid':
                health_result = self._check_sendgrid_health()
            elif service_name == 'onesignal':
                health_result = self._check_onesignal_health()
            elif service_name == 'oracle':
                health_result = self._check_oracle_health()
            else:
                raise ValueError(f"Unknown service: {service_name}")
            
            response_time = time.time() - start_time
            
            health_check = HealthCheck(
                service_name=service_name,
                status=health_result['status'],
                response_time=response_time,
                last_check=time.time(),
                error_message=health_result.get('error'),
                metadata=health_result.get('metadata', {})
            )
            
            self.health_checks[service_name] = health_check
            
            # Log health status
            if health_check.status != ServiceStatus.HEALTHY:
                logger.warning(
                    f"Service {service_name} health check: {health_check.status.value}",
                    extra={
                        'service_name': service_name,
                        'status': health_check.status.value,
                        'response_time': response_time,
                        'error': health_check.error_message,
                        'event_type': 'service_health_check'
                    }
                )
            
            return health_check
            
        except Exception as e:
            response_time = time.time() - start_time
            
            health_check = HealthCheck(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                response_time=response_time,
                last_check=time.time(),
                error_message=str(e)
            )
            
            self.health_checks[service_name] = health_check
            
            logger.error(
                f"Health check failed for {service_name}: {str(e)}",
                extra={
                    'service_name': service_name,
                    'error': str(e),
                    'response_time': response_time,
                    'event_type': 'service_health_check_failed'
                }
            )
            
            return health_check
    
    def is_healthy(self, service_name: str) -> bool:
        """
        Check if service is healthy
        """
        health_check = self.health_checks.get(service_name)
        if not health_check:
            # If no health check exists, perform one
            health_check = self.check_service_health(service_name)
        
        # Consider service healthy if status is HEALTHY or DEGRADED
        return health_check.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    def get_service_configurations(self) -> Dict:
        """
        Get service configuration for health checks
        """
        return {
            'firebase': {
                'timeout': 10,
                'retry_count': 2,
                'expected_response_time': 5.0
            },
            'twilio': {
                'timeout': 10,
                'retry_count': 2,
                'expected_response_time': 3.0
            },
            'sendgrid': {
                'timeout': 15,
                'retry_count': 2,
                'expected_response_time': 5.0
            },
            'onesignal': {
                'timeout': 10,
                'retry_count': 2,
                'expected_response_time': 3.0
            },
            'oracle': {
                'timeout': 5,
                'retry_count': 3,
                'expected_response_time': 2.0
            }
        }
    
    def _check_firebase_health(self) -> Dict:
        """Check Firebase service health"""
        try:
            # Simple validation check
            firebase_config = FirebaseConfiguration()
            firebase_config.get_firebase_app()
            
            return {'status': ServiceStatus.HEALTHY}
        except Exception as e:
            return {'status': ServiceStatus.UNHEALTHY, 'error': str(e)}
    
    def _check_twilio_health(self) -> Dict:
        """Check Twilio service health"""
        try:
            twilio_config = TwilioConfiguration()
            client = twilio_config.get_client()
            account = client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
            
            return {
                'status': ServiceStatus.HEALTHY,
                'metadata': {'account_status': account.status}
            }
        except Exception as e:
            return {'status': ServiceStatus.UNHEALTHY, 'error': str(e)}
    
    def _check_sendgrid_health(self) -> Dict:
        """Check SendGrid service health"""
        try:
            sendgrid_config = SendGridConfiguration()
            client = sendgrid_config.get_client()
            response = client.user.get()
            
            if response.status_code == 200:
                return {'status': ServiceStatus.HEALTHY}
            else:
                return {
                    'status': ServiceStatus.DEGRADED,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {'status': ServiceStatus.UNHEALTHY, 'error': str(e)}
    
    def _check_onesignal_health(self) -> Dict:
        """Check OneSignal service health"""
        try:
            onesignal_config = OneSignalConfiguration()
            # OneSignal validation is done in configuration
            
            return {'status': ServiceStatus.HEALTHY}
        except Exception as e:
            return {'status': ServiceStatus.UNHEALTHY, 'error': str(e)}
    
    def _check_oracle_health(self) -> Dict:
        """Check Oracle database health"""
        try:
            oracle_service = OracleDBService()
            result = oracle_service.execute_query("SELECT 1 FROM DUAL", fetch_mode='one')
            
            if result:
                session_info = oracle_service.get_session_info()
                return {
                    'status': ServiceStatus.HEALTHY,
                    'metadata': {
                        'active_sessions': session_info['active_sessions'],
                        'pool_busy': session_info['pool_status']['busy'],
                        'pool_max': session_info['pool_status']['max']
                    }
                }
            else:
                return {'status': ServiceStatus.UNHEALTHY, 'error': 'Query failed'}
                
        except Exception as e:
            return {'status': ServiceStatus.UNHEALTHY, 'error': str(e)}
    
    def get_overall_health_status(self) -> Dict:
        """
        Get overall system health status
        """
        total_services = len(self.service_configs)
        healthy_services = sum(1 for health in self.health_checks.values() 
                             if health.status == ServiceStatus.HEALTHY)
        degraded_services = sum(1 for health in self.health_checks.values() 
                              if health.status == ServiceStatus.DEGRADED)
        unhealthy_services = sum(1 for health in self.health_checks.values() 
                               if health.status == ServiceStatus.UNHEALTHY)
        
        # Determine overall status
        if unhealthy_services > 0:
            overall_status = ServiceStatus.UNHEALTHY
        elif degraded_services > 0:
            overall_status = ServiceStatus.DEGRADED
        else:
            overall_status = ServiceStatus.HEALTHY
        
        return {
            'overall_status': overall_status.value,
            'total_services': total_services,
            'healthy_services': healthy_services,
            'degraded_services': degraded_services,
            'unhealthy_services': unhealthy_services,
            'service_details': {
                name: {
                    'status': health.status.value,
                    'response_time': health.response_time,
                    'last_check': health.last_check,
                    'error': health.error_message
                }
                for name, health in self.health_checks.items()
            }
        }
```

---

## Testing Strategies

### 1. Unit Testing for Service Integrations

```python
# tests/test_external_services.py
import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
from services.firebase_auth_service import FirebaseAuthService
from services.twilio_sms_service import TwilioSMSService
from services.sendgrid_email_service import SendGridEmailService
from services.onesignal_push_service import OneSignalPushService
from services.oracle_db_service import OracleDBService

class TestFirebaseAuthService(unittest.TestCase):
    """
    Test Firebase Authentication Service
    """
    
    def setUp(self):
        self.firebase_service = FirebaseAuthService()
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_verify_id_token_success(self, mock_verify):
        """Test successful token verification"""
        # Arrange
        mock_token = "valid_token"
        mock_decoded = {
            'uid': 'test_user_123',
            'email': 'test@hdfc.bank',
            'iss': 'https://securetoken.google.com/hdfc-card-limit-system',
            'aud': 'hdfc-card-limit-system',
            'exp': int(time.time()) + 3600,
            'iat': int(time.time())
        }
        mock_verify.return_value = mock_decoded
        
        # Act
        result = self.firebase_service.verify_id_token(mock_token)
        
        # Assert
        self.assertEqual(result['uid'], 'test_user_123')
        self.assertEqual(result['email'], 'test@hdfc.bank')
        mock_verify.assert_called_once_with(mock_token, check_revoked=True, clock_skew_seconds=10)
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_verify_id_token_invalid(self, mock_verify):
        """Test invalid token handling"""
        # Arrange
        mock_verify.side_effect = auth.InvalidIdTokenError("Invalid token")
        
        # Act & Assert
        with self.assertRaises(InvalidTokenException):
            self.firebase_service.verify_id_token("invalid_token")
    
    @patch('firebase_admin.auth.create_custom_token')
    def test_create_custom_token(self, mock_create):
        """Test custom token creation"""
        # Arrange
        mock_create.return_value = b"custom_token_bytes"
        
        # Act
        result = self.firebase_service.create_custom_token(
            "test_user_123", 
            {"role": "customer"}
        )
        
        # Assert
        self.assertEqual(result, "custom_token_bytes")
        mock_create.assert_called_once_with("test_user_123", {"role": "customer"})

class TestTwilioSMSService(unittest.TestCase):
    """
    Test Twilio SMS Service
    """
    
    def setUp(self):
        self.twilio_service = TwilioSMSService()
    
    @patch('twilio.rest.Client')
    def test_send_sms_success(self, mock_client):
        """Test successful SMS sending"""
        # Arrange
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "sent"
        mock_message.price = "-0.0075"
        mock_message.price_unit = "USD"
        mock_message.date_created = datetime.utcnow()
        
        mock_client.return_value.messages.create.return_value = mock_message
        self.twilio_service.client = mock_client.return_value
        
        # Act
        result = self.twilio_service.send_sms(
            to_number="+919876543210",
            message="Test message"
        )
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['message_sid'], "SM123456789")
        self.assertEqual(result['status'], "sent")
    
    def test_validate_phone_number_valid(self):
        """Test phone number validation with valid number"""
        # Act
        result = self.twilio_service.validate_and_format_phone_number("+919876543210")
        
        # Assert
        self.assertEqual(result, "+919876543210")
    
    def test_validate_phone_number_invalid(self):
        """Test phone number validation with invalid number"""
        # Act & Assert
        with self.assertRaises(InvalidPhoneNumberException):
            self.twilio_service.validate_and_format_phone_number("invalid_number")

class TestSendGridEmailService(unittest.TestCase):
    """
    Test SendGrid Email Service
    """
    
    def setUp(self):
        self.sendgrid_service = SendGridEmailService()
    
    @patch('sendgrid.SendGridAPIClient.send')
    def test_send_email_success(self, mock_send):
        """Test successful email sending"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_message_id'}
        mock_send.return_value = mock_response
        
        # Act
        result = self.sendgrid_service.send_email(
            to_emails=['test@example.com'],
            subject='Test Subject',
            content='<h1>Test Content</h1>'
        )
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['status_code'], 202)
        self.assertEqual(result['message_id'], 'test_message_id')
    
    @patch('sendgrid.SendGridAPIClient.send')
    def test_send_email_failure(self, mock_send):
        """Test email sending failure"""
        # Arrange
        mock_send.side_effect = Exception("SendGrid API error")
        
        # Act & Assert
        with self.assertRaises(EmailSendException):
            self.sendgrid_service.send_email(
                to_emails=['test@example.com'],
                subject='Test Subject',
                content='Test Content'
            )

class TestOneSignalPushService(unittest.TestCase):
    """
    Test OneSignal Push Service
    """
    
    def setUp(self):
        self.onesignal_service = OneSignalPushService()
    
    @patch('requests.post')
    def test_send_notification_success(self, mock_post):
        """Test successful notification sending"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'notification_123',
            'recipients': 100,
            'errors': []
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Act
        result = self.onesignal_service.send_notification(
            player_ids=['player_123'],
            headings={'en': 'Test Notification'},
            contents={'en': 'Test Content'}
        )
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['notification_id'], 'notification_123')
        self.assertEqual(result['recipients'], 100)
    
    def test_process_template(self):
        """Test template processing"""
        # Arrange
        template = {
            'headings': {'en': 'Hello {{name}}'},
            'contents': {'en': 'Your OTP is {{otp_code}}'}
        }
        data = {'name': 'John', 'otp_code': '123456'}
        
        # Act
        result = self.onesignal_service.process_template(template, data)
        
        # Assert
        self.assertEqual(result['headings']['en'], 'Hello John')
        self.assertEqual(result['contents']['en'], 'Your OTP is 123456')

class TestOracleDBService(unittest.TestCase):
    """
    Test Oracle Database Service
    """
    
    def setUp(self):
        self.oracle_service = OracleDBService()
    
    @patch('cx_Oracle.SessionPool')
    def test_execute_query_success(self, mock_pool):
        """Test successful query execution"""
        # Arrange
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'Test'}]
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.return_value.acquire.return_value = mock_connection
        
        # Act
        result = self.oracle_service.execute_query("SELECT * FROM test_table")
        
        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Test')
    
    @patch('cx_Oracle.SessionPool')
    def test_execute_procedure_success(self, mock_pool):
        """Test successful procedure execution"""
        # Arrange
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_var = Mock()
        mock_var.getvalue.return_value = 'success'
        mock_cursor.var.return_value = mock_var
        mock_connection.cursor.return_value = mock_cursor
        mock_pool.return_value.acquire.return_value = mock_connection
        
        # Act
        result = self.oracle_service.execute_procedure(
            'test_procedure',
            {'output_param': {'direction': 'out', 'type': str}}
        )
        
        # Assert
        self.assertEqual(result['output_param'], 'success')
```

### 2. Integration Testing

```python
# tests/test_integration.py
import pytest
from django.test import TestCase, override_settings
from unittest.mock import patch, Mock

class ExternalServiceIntegrationTest(TestCase):
    """
    Integration tests for external services
    """
    
    @pytest.mark.integration
    @override_settings(
        FIREBASE_PROJECT_ID='test-project',
        TWILIO_ACCOUNT_SID='test-sid',
        SENDGRID_API_KEY='test-key',
        ONESIGNAL_APP_ID='test-app-id'
    )
    def test_end_to_end_user_registration(self):
        """
        Test complete user registration flow with all services
        """
        # This test would cover:
        # 1. Firebase user creation
        # 2. Database record creation
        # 3. Welcome SMS via Twilio
        # 4. Welcome email via SendGrid
        # 5. Push notification setup via OneSignal
        pass
    
    @pytest.mark.integration
    def test_otp_verification_flow(self):
        """
        Test complete OTP verification flow
        """
        # This test would cover:
        # 1. OTP generation and storage in Oracle
        # 2. SMS delivery via Twilio
        # 3. Email delivery via SendGrid (backup)
        # 4. Push notification via OneSignal
        # 5. OTP verification and cleanup
        pass
    
    @pytest.mark.integration
    def test_limit_increase_approval_flow(self):
        """
        Test complete limit increase approval notification flow
        """
        # This test would cover:
        # 1. Database status update
        # 2. Multi-channel notification delivery
        # 3. Audit logging
        # 4. Customer communication
        pass
```

### 3. Load Testing

```python
# tests/load_tests.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
import statistics

class LoadTestExternalServices:
    """
    Load testing for external service integrations
    """
    
    def __init__(self):
        self.results = []
    
    async def test_concurrent_firebase_auth(self, concurrent_users=100):
        """
        Test Firebase authentication under load
        """
        async def verify_token():
            start_time = time.time()
            try:
                # Simulate token verification
                firebase_service = FirebaseAuthService()
                await firebase_service.verify_id_token("test_token")
                
                response_time = time.time() - start_time
                return {'success': True, 'response_time': response_time}
            except Exception as e:
                response_time = time.time() - start_time
                return {'success': False, 'response_time': response_time, 'error': str(e)}
        
        # Run concurrent tests
        tasks = [verify_token() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful = sum(1 for r in results if r.get('success'))
        failed = len(results) - successful
        response_times = [r['response_time'] for r in results if isinstance(r, dict)]
        
        return {
            'service': 'firebase_auth',
            'concurrent_users': concurrent_users,
            'successful_requests': successful,
            'failed_requests': failed,
            'average_response_time': statistics.mean(response_times),
            'p95_response_time': statistics.quantiles(response_times, n=20)[18],  # 95th percentile
            'p99_response_time': statistics.quantiles(response_times, n=100)[98]   # 99th percentile
        }
    
    def test_bulk_sms_performance(self, message_count=1000):
        """
        Test bulk SMS sending performance
        """
        start_time = time.time()
        
        twilio_service = TwilioSMSService()
        
        # Create test recipients
        recipients = [
            {
                'phone_number': f'+9187654321{str(i).zfill(2)}',
                'variables': {'name': f'User{i}', 'code': f'{i:06d}'}
            }
            for i in range(message_count)
        ]
        
        # Send bulk SMS
        result = twilio_service.send_bulk_sms(
            recipients=recipients,
            message="Hello {{name}}, your code is {{code}}"
        )
        
        total_time = time.time() - start_time
        
        return {
            'service': 'twilio_sms',
            'total_messages': message_count,
            'successful_messages': result['successful'],
            'failed_messages': result['failed'],
            'total_time': total_time,
            'messages_per_second': message_count / total_time,
            'success_rate': (result['successful'] / message_count) * 100
        }
```

---

## Performance Optimization

### 1. Connection Pooling and Caching

```python
# optimization/connection_pooling.py
import redis
import memcache
from django.core.cache import cache
import threading
import time

class ServiceConnectionPool:
    """
    Manage connection pooling for external services
    """
    
    def __init__(self):
        self.redis_pool = self.create_redis_pool()
        self.memcache_client = self.create_memcache_client()
        self.connection_stats = {}
        self.stats_lock = threading.Lock()
    
    def create_redis_pool(self):
        """
        Create Redis connection pool for caching
        """
        return redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            max_connections=50,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={}
        )
    
    def create_memcache_client(self):
        """
        Create Memcache client for distributed caching
        """
        return memcache.Client(
            [f"{settings.MEMCACHE_HOST}:{settings.MEMCACHE_PORT}"],
            debug=0
        )
    
    def get_cached_result(self, key: str, service_name: str):
        """
        Get cached result with fallback
        """
        try:
            # Try Redis first
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            result = redis_client.get(key)
            
            if result:
                self.update_cache_stats(service_name, 'redis_hit')
                return json.loads(result)
            
            # Fallback to Memcache
            result = self.memcache_client.get(key)
            if result:
                self.update_cache_stats(service_name, 'memcache_hit')
                return result
            
            self.update_cache_stats(service_name, 'cache_miss')
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval failed: {str(e)}")
            return None
    
    def set_cached_result(self, key: str, value: any, ttl: int = 3600):
        """
        Set cached result in multiple stores
        """
        try:
            # Store in Redis
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            redis_client.setex(key, ttl, json.dumps(value))
            
            # Store in Memcache as backup
            self.memcache_client.set(key, value, time=ttl)
            
        except Exception as e:
            logger.error(f"Cache storage failed: {str(e)}")
    
    def update_cache_stats(self, service_name: str, stat_type: str):
        """
        Update cache statistics
        """
        with self.stats_lock:
            if service_name not in self.connection_stats:
                self.connection_stats[service_name] = {
                    'redis_hits': 0,
                    'memcache_hits': 0,
                    'cache_misses': 0
                }
            
            self.connection_stats[service_name][stat_type] = \
                self.connection_stats[service_name].get(stat_type, 0) + 1

class PerformanceOptimizer:
    """
    Performance optimization utilities for external services
    """
    
    @staticmethod
    def batch_operations(operations: List, batch_size: int = 100):
        """
        Batch operations for better performance
        """
        for i in range(0, len(operations), batch_size):
            yield operations[i:i + batch_size]
    
    @staticmethod
    def async_operation_manager(max_concurrent: int = 10):
        """
        Manage concurrent async operations
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_operation(operation):
            async with semaphore:
                return await operation()
        
        return limited_operation
    
    @staticmethod
    def rate_limiter(calls_per_second: int):
        """
        Rate limiting decorator
        """
        min_interval = 1.0 / calls_per_second
        last_called = [0.0]
        
        def decorator(func):
            def wrapper(*args, **kwargs):
                elapsed = time.time() - last_called[0]
                left_to_wait = min_interval - elapsed
                if left_to_wait > 0:
                    time.sleep(left_to_wait)
                ret = func(*args, **kwargs)
                last_called[0] = time.time()
                return ret
            return wrapper
        return decorator
```

---

## Troubleshooting

### 1. Common Issues and Solutions

```python
# troubleshooting/service_diagnostics.py
import traceback
from typing import Dict, List

class ServiceDiagnostics:
    """
    Diagnostic tools for external service issues
    """
    
    def diagnose_firebase_issues(self, error: Exception) -> Dict:
        """
        Diagnose Firebase-related issues
        """
        diagnostics = {
            'service': 'firebase',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'possible_causes': [],
            'solutions': []
        }
        
        error_msg = str(error).lower()
        
        if 'invalid token' in error_msg:
            diagnostics['possible_causes'].extend([
                'Expired ID token',
                'Invalid token format',
                'Token issued for different project'
            ])
            diagnostics['solutions'].extend([
                'Refresh the ID token',
                'Verify token format and structure',
                'Check Firebase project configuration'
            ])
        
        elif 'permission denied' in error_msg:
            diagnostics['possible_causes'].extend([
                'Insufficient Firebase permissions',
                'Invalid service account key',
                'Firestore security rules blocking access'
            ])
            diagnostics['solutions'].extend([
                'Review Firebase IAM permissions',
                'Verify service account key is correct',
                'Update Firestore security rules'
            ])
        
        elif 'quota exceeded' in error_msg:
            diagnostics['possible_causes'].extend([
                'Firebase usage quota exceeded',
                'Too many requests in short time'
            ])
            diagnostics['solutions'].extend([
                'Check Firebase usage dashboard',
                'Implement rate limiting',
                'Consider upgrading Firebase plan'
            ])
        
        return diagnostics
    
    def diagnose_twilio_issues(self, error: Exception) -> Dict:
        """
        Diagnose Twilio-related issues
        """
        diagnostics = {
            'service': 'twilio',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'possible_causes': [],
            'solutions': []
        }
        
        if hasattr(error, 'code'):
            twilio_error_code = getattr(error, 'code')
            
            if twilio_error_code == 21211:  # Invalid phone number
                diagnostics['possible_causes'].append('Invalid phone number format')
                diagnostics['solutions'].extend([
                    'Validate phone number format',
                    'Use E.164 format (+country_code + number)',
                    'Check for special characters or spaces'
                ])
            
            elif twilio_error_code == 21408:  # Permission denied
                diagnostics['possible_causes'].append('Insufficient account permissions')
                diagnostics['solutions'].extend([
                    'Check Twilio account status',
                    'Verify API credentials',
                    'Review account permissions'
                ])
            
            elif twilio_error_code == 20003:  # Authentication error
                diagnostics['possible_causes'].append('Invalid credentials')
                diagnostics['solutions'].extend([
                    'Verify Account SID and Auth Token',
                    'Check for expired credentials',
                    'Regenerate Auth Token if needed'
                ])
        
        return diagnostics
    
    def diagnose_sendgrid_issues(self, error: Exception) -> Dict:
        """
        Diagnose SendGrid-related issues
        """
        diagnostics = {
            'service': 'sendgrid',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'possible_causes': [],
            'solutions': []
        }
        
        error_msg = str(error).lower()
        
        if '401' in error_msg or 'unauthorized' in error_msg:
            diagnostics['possible_causes'].extend([
                'Invalid API key',
                'Expired API key',
                'API key lacks required permissions'
            ])
            diagnostics['solutions'].extend([
                'Verify API key is correct',
                'Check API key permissions',
                'Generate new API key if needed'
            ])
        
        elif '413' in error_msg or 'too large' in error_msg:
            diagnostics['possible_causes'].extend([
                'Email content too large',
                'Attachment size exceeds limit'
            ])
            diagnostics['solutions'].extend([
                'Reduce email content size',
                'Compress or reduce attachment size',
                'Split large content into multiple emails'
            ])
        
        elif 'rate limit' in error_msg:
            diagnostics['possible_causes'].append('Rate limit exceeded')
            diagnostics['solutions'].extend([
                'Implement rate limiting',
                'Use batch sending for multiple emails',
                'Consider upgrading SendGrid plan'
            ])
        
        return diagnostics
    
    def diagnose_oracle_issues(self, error: Exception) -> Dict:
        """
        Diagnose Oracle database issues
        """
        diagnostics = {
            'service': 'oracle',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'possible_causes': [],
            'solutions': []
        }
        
        error_msg = str(error).lower()
        
        if 'ora-00942' in error_msg:  # Table or view does not exist
            diagnostics['possible_causes'].extend([
                'Table/view name misspelled',
                'Table not created yet',
                'Insufficient privileges'
            ])
            diagnostics['solutions'].extend([
                'Verify table name spelling',
                'Run database migrations',
                'Grant necessary privileges'
            ])
        
        elif 'ora-01017' in error_msg:  # Invalid username/password
            diagnostics['possible_causes'].extend([
                'Wrong database credentials',
                'Account locked or expired'
            ])
            diagnostics['solutions'].extend([
                'Verify database credentials',
                'Check account status',
                'Reset password if needed'
            ])
        
        elif 'ora-12154' in error_msg:  # TNS could not resolve
            diagnostics['possible_causes'].extend([
                'Invalid TNS service name',
                'Network connectivity issues',
                'TNS configuration problems'
            ])
            diagnostics['solutions'].extend([
                'Verify TNS service name',
                'Check network connectivity',
                'Review TNS configuration'
            ])
        
        return diagnostics
    
    def generate_troubleshooting_report(self, service_name: str, error: Exception) -> Dict:
        """
        Generate comprehensive troubleshooting report
        """
        # Get service-specific diagnostics
        if service_name == 'firebase':
            diagnostics = self.diagnose_firebase_issues(error)
        elif service_name == 'twilio':
            diagnostics = self.diagnose_twilio_issues(error)
        elif service_name == 'sendgrid':
            diagnostics = self.diagnose_sendgrid_issues(error)
        elif service_name == 'oracle':
            diagnostics = self.diagnose_oracle_issues(error)
        else:
            diagnostics = {
                'service': service_name,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'possible_causes': ['Unknown service'],
                'solutions': ['Contact support']
            }
        
        # Add common troubleshooting information
        report = {
            **diagnostics,
            'timestamp': datetime.utcnow().isoformat(),
            'stack_trace': traceback.format_exc(),
            'environment_info': {
                'python_version': sys.version,
                'django_version': django.VERSION,
                'system_info': platform.platform()
            },
            'general_solutions': [
                'Check network connectivity',
                'Verify service credentials',
                'Review service status pages',
                'Check application logs',
                'Restart application if needed'
            ]
        }
        
        return report
```

### 2. Health Check Endpoints

```python
# api/health_check_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from monitoring.service_health_monitor import ServiceHealthMonitor

class HealthCheckView(APIView):
    """
    Health check endpoint for external services
    """
    
    def __init__(self):
        super().__init__()
        self.health_monitor = ServiceHealthMonitor()
    
    def get(self, request):
        """
        Get overall system health status
        """
        try:
            # Get overall health status
            health_status = self.health_monitor.get_overall_health_status()
            
            # Determine HTTP status code
            if health_status['overall_status'] == 'healthy':
                http_status = status.HTTP_200_OK
            elif health_status['overall_status'] == 'degraded':
                http_status = status.HTTP_206_PARTIAL_CONTENT
            else:
                http_status = status.HTTP_503_SERVICE_UNAVAILABLE
            
            return Response(health_status, status=http_status)
            
        except Exception as e:
            return Response(
                {
                    'overall_status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ServiceHealthDetailView(APIView):
    """
    Detailed health check for specific service
    """
    
    def __init__(self):
        super().__init__()
        self.health_monitor = ServiceHealthMonitor()
    
    def get(self, request, service_name):
        """
        Get detailed health status for specific service
        """
        try:
            # Perform health check for specific service
            health_check = self.health_monitor.check_service_health(service_name)
            
            # Prepare detailed response
            response_data = {
                'service_name': health_check.service_name,
                'status': health_check.status.value,
                'response_time': health_check.response_time,
                'last_check': health_check.last_check,
                'error_message': health_check.error_message,
                'metadata': health_check.metadata or {}
            }
            
            # Determine HTTP status
            if health_check.status.value == 'healthy':
                http_status = status.HTTP_200_OK
            elif health_check.status.value == 'degraded':
                http_status = status.HTTP_206_PARTIAL_CONTENT
            else:
                http_status = status.HTTP_503_SERVICE_UNAVAILABLE
            
            return Response(response_data, status=http_status)
            
        except ValueError as e:
            return Response(
                {'error': f'Unknown service: {service_name}'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

---

## Conclusion

This External Service Integration Guide provides comprehensive implementation strategies for integrating with critical external services in the HDFC Card Limit Increase System. The guide covers:

### Key Integration Components:
1. **Firebase Authentication** - Secure user authentication and token management
2. **Twilio Communication Services** - SMS, Voice, and WhatsApp messaging
3. **SendGrid Email Services** - Transactional and marketing email delivery
4. **OneSignal Push Notifications** - Cross-platform push notification delivery
5. **Oracle Database Integration** - Enterprise database connectivity and management

### Implementation Best Practices:
- **Comprehensive Error Handling** - Robust exception handling with specific error types
- **Circuit Breaker Pattern** - Fault tolerance and service resilience
- **Retry Mechanisms** - Exponential backoff and intelligent retry logic
- **Connection Pooling** - Optimized resource utilization and performance
- **Health Monitoring** - Continuous service health tracking and alerting
- **Caching Strategies** - Multi-tier caching for improved performance
- **Security Measures** - Secure credential management and data protection

### Testing and Monitoring:
- **Unit Testing** - Comprehensive test coverage for all service integrations
- **Integration Testing** - End-to-end workflow validation
- **Load Testing** - Performance validation under high load
- **Health Check Endpoints** - Real-time service status monitoring
- **Diagnostic Tools** - Automated troubleshooting and issue resolution

This guide ensures reliable, secure, and performant integration with external services while maintaining banking-grade standards for the HDFC Card Limit Increase System.

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Next Review:** February 2025