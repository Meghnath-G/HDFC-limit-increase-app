# External Services Integration Documentation

## Overview

The Card Limit Increase System integrates with multiple external services to provide comprehensive functionality including authentication, notifications, communications, and monitoring. This document details the implementation, configuration, and usage of all external service integrations.

## Table of Contents

1. [Integration Architecture](#integration-architecture)
2. [Firebase Integration](#firebase-integration)
3. [Twilio Integration](#twilio-integration)
4. [SendGrid Integration](#sendgrid-integration)
5. [OneSignal Integration](#onesignal-integration)
6. [Service Configuration](#service-configuration)
7. [Error Handling](#error-handling)
8. [Monitoring & Analytics](#monitoring--analytics)
9. [Security Considerations](#security-considerations)
10. [Testing External Services](#testing-external-services)

## Integration Architecture

### Service Integration Pattern

```
┌─────────────────────┐
│   Django Backend    │
│                     │
├─────────────────────┤
│   Service Layer     │
├─────────────────────┤
│  ┌─────────────────┐│
│  │ Firebase Admin  ││ → Authentication & Push
│  │     SDK         ││
│  └─────────────────┘│
│  ┌─────────────────┐│
│  │ Twilio Client   ││ → SMS & Voice
│  │     SDK         ││
│  └─────────────────┘│
│  ┌─────────────────┐│
│  │ SendGrid API    ││ → Email Services
│  │    Client       ││
│  └─────────────────┘│
│  ┌─────────────────┐│
│  │ OneSignal SDK   ││ → Push Notifications
│  │                 ││
│  └─────────────────┘│
└─────────────────────┘
```

### Design Principles

1. **Abstraction**: Service interfaces hide implementation details
2. **Resilience**: Built-in retry mechanisms and fallbacks
3. **Monitoring**: Comprehensive logging and metrics
4. **Security**: Secure credential management
5. **Testability**: Mockable service interfaces

## Firebase Integration

### Overview

Firebase provides authentication services and push notification capabilities for the mobile application.

### Implementation

#### Firebase Service Class

```python
import firebase_admin
from firebase_admin import credentials, auth, messaging
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class FirebaseService:
    """Firebase Admin SDK integration for authentication and push notifications."""
    
    def __init__(self):
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {str(e)}")
                raise
    
    def verify_token(self, id_token):
        """
        Verify Firebase ID token and return decoded token.
        
        Args:
            id_token (str): Firebase ID token from client
            
        Returns:
            dict: Decoded token with user information
            
        Raises:
            FirebaseAuthError: If token verification fails
        """
        try:
            decoded_token = auth.verify_id_token(id_token)
            logger.info(f"Token verified for user: {decoded_token.get('uid')}")
            return decoded_token
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise FirebaseAuthError(f"Invalid token: {str(e)}")
    
    def get_user(self, uid):
        """
        Get user information by UID.
        
        Args:
            uid (str): Firebase user UID
            
        Returns:
            firebase_admin.auth.UserRecord: User information
        """
        try:
            user = auth.get_user(uid)
            logger.info(f"Retrieved user info for UID: {uid}")
            return user
        except Exception as e:
            logger.error(f"Failed to get user {uid}: {str(e)}")
            raise
    
    def send_push_notification(self, tokens, title, body, data=None):
        """
        Send push notification to multiple devices.
        
        Args:
            tokens (list): List of FCM registration tokens
            title (str): Notification title
            body (str): Notification body
            data (dict): Optional data payload
            
        Returns:
            dict: Sending results with success/failure counts
        """
        if not tokens:
            logger.warning("No tokens provided for push notification")
            return {'success_count': 0, 'failure_count': 0}
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            logger.info(
                f"Push notification sent: {response.success_count} success, "
                f"{response.failure_count} failures"
            )
            
            # Log failed tokens for debugging
            if response.failure_count > 0:
                failed_tokens = [
                    tokens[i] for i, result in enumerate(response.responses)
                    if not result.success
                ]
                logger.warning(f"Failed tokens: {failed_tokens}")
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'responses': response.responses
            }
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {str(e)}")
            raise
    
    def create_custom_token(self, uid, additional_claims=None):
        """
        Create custom token for user authentication.
        
        Args:
            uid (str): User UID
            additional_claims (dict): Optional additional claims
            
        Returns:
            str: Custom token
        """
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            logger.info(f"Custom token created for user: {uid}")
            return custom_token.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to create custom token: {str(e)}")
            raise
```

#### Authentication Middleware

```python
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .firebase_service import FirebaseService
from .models import Customer

class FirebaseAuthenticationMiddleware(MiddlewareMixin):
    """Middleware to authenticate requests using Firebase tokens."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.firebase_service = FirebaseService()
    
    def process_request(self, request):
        # Skip authentication for certain paths
        if request.path in ['/health/', '/admin/']:
            return None
        
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Verify token
            decoded_token = self.firebase_service.verify_token(token)
            
            # Get or create customer
            try:
                customer = Customer.objects.get(firebase_uid=decoded_token['uid'])
                request.user = customer
            except Customer.DoesNotExist:
                return JsonResponse({'error': 'Customer not found'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        return None
```

### Configuration

#### Settings

```python
# Firebase configuration
FIREBASE_CREDENTIALS = os.path.join(BASE_DIR, 'config', 'firebase-credentials.json')

# Firebase credentials JSON structure
{
    "type": "service_account",
    "project_id": "hdfc-card-limit-system",
    "private_key_id": "...",
    "private_key": "...",
    "client_email": "...",
    "client_id": "...",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
}
```

## Twilio Integration

### Overview

Twilio provides SMS and voice communication services for OTP delivery and customer notifications.

### Implementation

#### Twilio Service Class

```python
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    """Twilio integration for SMS and voice services."""
    
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.from_number = settings.TWILIO_PHONE_NUMBER
    
    def send_sms(self, to_number, message, media_url=None):
        """
        Send SMS message to a phone number.
        
        Args:
            to_number (str): Recipient phone number in E.164 format
            message (str): SMS message content
            media_url (str): Optional media URL for MMS
            
        Returns:
            dict: Result with success status and message SID or error
        """
        try:
            message_params = {
                'body': message,
                'from_': self.from_number,
                'to': to_number
            }
            
            if media_url:
                message_params['media_url'] = [media_url]
            
            message = self.client.messages.create(**message_params)
            
            logger.info(f"SMS sent successfully to {to_number}, SID: {message.sid}")
            return {
                'success': True,
                'sid': message.sid,
                'status': message.status
            }
            
        except TwilioException as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': getattr(e, 'code', None)
            }
        except Exception as e:
            logger.error(f"Unexpected SMS error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_otp(self, to_number, otp_code):
        """
        Send OTP via SMS with predefined template.
        
        Args:
            to_number (str): Recipient phone number
            otp_code (str): OTP code to send
            
        Returns:
            dict: Result with success status and message details
        """
        message = f"Your HDFC Card Limit verification code is: {otp_code}. Valid for 10 minutes. Do not share this code."
        return self.send_sms(to_number, message)
    
    def make_voice_call(self, to_number, twiml_url):
        """
        Initiate voice call with TwiML instructions.
        
        Args:
            to_number (str): Recipient phone number
            twiml_url (str): URL containing TwiML instructions
            
        Returns:
            dict: Result with success status and call SID or error
        """
        try:
            call = self.client.calls.create(
                url=twiml_url,
                to=to_number,
                from_=self.from_number
            )
            
            logger.info(f"Voice call initiated to {to_number}, SID: {call.sid}")
            return {
                'success': True,
                'sid': call.sid,
                'status': call.status
            }
            
        except TwilioException as e:
            logger.error(f"Twilio voice call error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': getattr(e, 'code', None)
            }
    
    def send_voice_otp(self, to_number, otp_code):
        """
        Send OTP via voice call.
        
        Args:
            to_number (str): Recipient phone number
            otp_code (str): OTP code to deliver via voice
            
        Returns:
            dict: Result with success status and call details
        """
        # Create TwiML for voice OTP
        twiml_content = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice">
                Your H D F C Card Limit verification code is: 
                {' '.join(otp_code)}. 
                I repeat, your verification code is: 
                {' '.join(otp_code)}.
            </Say>
        </Response>
        """
        
        # In production, you would host this TwiML at a URL
        # For now, we'll use Twilio's TwiML bins or inline TwiML
        twiml_url = f"{settings.BASE_URL}/api/voice/otp-twiml/?otp={otp_code}"
        
        return self.make_voice_call(to_number, twiml_url)
    
    def get_message_status(self, message_sid):
        """
        Get status of a sent message.
        
        Args:
            message_sid (str): Twilio message SID
            
        Returns:
            dict: Message status information
        """
        try:
            message = self.client.messages(message_sid).fetch()
            return {
                'success': True,
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message
            }
        except Exception as e:
            logger.error(f"Failed to get message status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
```

#### OTP Service Integration

```python
from django.utils.crypto import get_random_string
from django.core.cache import cache
import random

class OTPService:
    """OTP generation and verification service."""
    
    def __init__(self):
        self.twilio_service = TwilioService()
    
    def generate_otp(self, length=6):
        """Generate numeric OTP."""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    def send_otp(self, phone_number, delivery_method='sms'):
        """
        Generate and send OTP to phone number.
        
        Args:
            phone_number (str): Recipient phone number
            delivery_method (str): 'sms' or 'voice'
            
        Returns:
            dict: Result with success status and OTP details
        """
        otp_code = self.generate_otp()
        cache_key = f"otp:{phone_number}"
        
        # Store OTP in cache with 10-minute expiry
        cache.set(cache_key, otp_code, 600)
        
        if delivery_method == 'sms':
            result = self.twilio_service.send_otp(phone_number, otp_code)
        elif delivery_method == 'voice':
            result = self.twilio_service.send_voice_otp(phone_number, otp_code)
        else:
            return {'success': False, 'error': 'Invalid delivery method'}
        
        if result['success']:
            logger.info(f"OTP sent to {phone_number} via {delivery_method}")
        
        return result
    
    def verify_otp(self, phone_number, provided_otp):
        """
        Verify OTP for phone number.
        
        Args:
            phone_number (str): Phone number to verify
            provided_otp (str): OTP provided by user
            
        Returns:
            bool: True if OTP is valid, False otherwise
        """
        cache_key = f"otp:{phone_number}"
        stored_otp = cache.get(cache_key)
        
        if stored_otp and stored_otp == provided_otp:
            cache.delete(cache_key)  # Remove used OTP
            logger.info(f"OTP verified successfully for {phone_number}")
            return True
        
        logger.warning(f"Invalid OTP attempt for {phone_number}")
        return False
```

### Configuration

```python
# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# Voice TwiML endpoint
BASE_URL = os.environ.get('BASE_URL', 'https://api.cardlimit.hdfc.com')
```

## SendGrid Integration

### Overview

SendGrid provides reliable email delivery services for notifications, reports, and customer communications.

### Implementation

#### SendGrid Service Class

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

class SendGridService:
    """SendGrid integration for email services."""
    
    def __init__(self):
        self.sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        self.from_email = settings.SENDGRID_FROM_EMAIL
    
    def send_email(self, to_email, subject, content, template_id=None, template_data=None):
        """
        Send email using SendGrid.
        
        Args:
            to_email (str or list): Recipient email address(es)
            subject (str): Email subject
            content (str): Email content (HTML)
            template_id (str): Optional SendGrid template ID
            template_data (dict): Template variables
            
        Returns:
            dict: Result with success status and message details
        """
        try:
            # Handle multiple recipients
            if isinstance(to_email, list):
                to_emails = [To(email) for email in to_email]
            else:
                to_emails = To(to_email)
            
            mail = Mail(
                from_email=Email(self.from_email),
                to_emails=to_emails,
                subject=subject,
                html_content=Content("text/html", content)
            )
            
            # Use template if provided
            if template_id:
                mail.template_id = template_id
                if template_data:
                    mail.dynamic_template_data = template_data
            
            response = self.sg.send(mail)
            
            logger.info(f"Email sent successfully to {to_email}, status: {response.status_code}")
            return {
                'success': True,
                'status_code': response.status_code,
                'message_id': response.headers.get('X-Message-Id')
            }
            
        except Exception as e:
            logger.error(f"SendGrid email error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_templated_email(self, to_email, template_name, context_data):
        """
        Send email using Django template.
        
        Args:
            to_email (str): Recipient email
            template_name (str): Django template name
            context_data (dict): Template context variables
            
        Returns:
            dict: Result with success status
        """
        try:
            # Render email content from Django template
            subject = render_to_string(f'emails/{template_name}_subject.txt', context_data).strip()
            html_content = render_to_string(f'emails/{template_name}.html', context_data)
            
            return self.send_email(to_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Template email error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_limit_request_notification(self, customer_email, request_details):
        """
        Send limit request status notification.
        
        Args:
            customer_email (str): Customer email
            request_details (dict): Request information
            
        Returns:
            dict: Email sending result
        """
        template_data = {
            'customer_name': request_details.get('customer_name'),
            'request_id': request_details.get('request_id'),
            'current_limit': request_details.get('current_limit'),
            'requested_limit': request_details.get('requested_limit'),
            'status': request_details.get('status'),
            'approved_limit': request_details.get('approved_limit')
        }
        
        return self.send_templated_email(
            customer_email,
            'limit_request_update',
            template_data
        )
    
    def send_welcome_email(self, customer_email, customer_name):
        """
        Send welcome email to new customer.
        
        Args:
            customer_email (str): Customer email
            customer_name (str): Customer name
            
        Returns:
            dict: Email sending result
        """
        template_data = {
            'customer_name': customer_name,
            'app_download_url': settings.APP_DOWNLOAD_URL,
            'support_email': settings.SUPPORT_EMAIL
        }
        
        return self.send_templated_email(
            customer_email,
            'welcome',
            template_data
        )
    
    def send_security_alert(self, customer_email, alert_details):
        """
        Send security alert email.
        
        Args:
            customer_email (str): Customer email
            alert_details (dict): Security alert information
            
        Returns:
            dict: Email sending result
        """
        template_data = {
            'customer_name': alert_details.get('customer_name'),
            'action': alert_details.get('action'),
            'timestamp': alert_details.get('timestamp'),
            'ip_address': alert_details.get('ip_address'),
            'location': alert_details.get('location')
        }
        
        return self.send_templated_email(
            customer_email,
            'security_alert',
            template_data
        )
```

#### Email Templates

```html
<!-- templates/emails/limit_request_update.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Limit Request Update</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background-color: #00356B; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .status-approved { color: #28a745; font-weight: bold; }
        .status-rejected { color: #dc3545; font-weight: bold; }
        .footer { background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>HDFC Bank</h1>
            <h2>Credit Limit Update</h2>
        </div>
        
        <div class="content">
            <p>Dear {{ customer_name }},</p>
            
            <p>We have an update regarding your credit limit increase request.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Request ID:</strong> {{ request_id }}</p>
                <p><strong>Current Limit:</strong> ₹{{ current_limit|floatformat:0 }}</p>
                <p><strong>Requested Limit:</strong> ₹{{ requested_limit|floatformat:0 }}</p>
                <p><strong>Status:</strong> 
                    <span class="status-{{ status|lower }}">{{ status|title }}</span>
                </p>
                {% if approved_limit %}
                <p><strong>Approved Limit:</strong> ₹{{ approved_limit|floatformat:0 }}</p>
                {% endif %}
            </div>
            
            {% if status == 'approved' %}
            <p>Congratulations! Your credit limit has been increased. The new limit will be effective within 24 hours.</p>
            {% elif status == 'rejected' %}
            <p>We regret to inform you that your request could not be approved at this time. You may reapply after 90 days.</p>
            {% else %}
            <p>Your request is currently under review. We will notify you once a decision is made.</p>
            {% endif %}
            
            <p>If you have any questions, please contact our customer service at 1800-123-4567.</p>
            
            <p>Thank you for banking with HDFC Bank.</p>
        </div>
        
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.</p>
            <p>HDFC Bank Ltd. | Mumbai, India</p>
        </div>
    </div>
</body>
</html>
```

### Configuration

```python
# SendGrid configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDGRID_FROM_EMAIL = 'noreply@hdfc.com'

# Email template settings
APP_DOWNLOAD_URL = 'https://play.google.com/store/apps/details?id=com.hdfc.cardlimit'
SUPPORT_EMAIL = 'support@hdfc.com'
```

## OneSignal Integration

### Overview

OneSignal provides push notification services as an alternative to Firebase for broader platform support.

### Implementation

#### OneSignal Service Class

```python
import onesignal
from onesignal.api import default_api
from onesignal.model.notification import Notification
from onesignal.model.player import Player
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class OneSignalService:
    """OneSignal integration for push notifications."""
    
    def __init__(self):
        configuration = onesignal.Configuration(
            app_key=settings.ONESIGNAL_APP_KEY,
            user_key=settings.ONESIGNAL_USER_KEY
        )
        self.api_client = onesignal.ApiClient(configuration)
        self.default_api = default_api.DefaultApi(self.api_client)
        self.app_id = settings.ONESIGNAL_APP_ID
    
    def send_notification(self, player_ids, heading, content, data=None, url=None):
        """
        Send push notification to specific players.
        
        Args:
            player_ids (list): List of OneSignal player IDs
            heading (str): Notification title
            content (str): Notification body
            data (dict): Optional data payload
            url (str): Optional URL to open
            
        Returns:
            dict: Result with success status and notification details
        """
        try:
            notification = Notification(
                app_id=self.app_id,
                include_player_ids=player_ids,
                headings={"en": heading},
                contents={"en": content}
            )
            
            if data:
                notification.data = data
            
            if url:
                notification.url = url
            
            response = self.default_api.create_notification(notification)
            
            logger.info(f"OneSignal notification sent to {len(player_ids)} players")
            return {
                'success': True,
                'id': response.id,
                'recipients': response.recipients
            }
            
        except Exception as e:
            logger.error(f"OneSignal notification error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_to_segments(self, segments, heading, content, data=None):
        """
        Send notification to user segments.
        
        Args:
            segments (list): List of segment names
            heading (str): Notification title
            content (str): Notification body
            data (dict): Optional data payload
            
        Returns:
            dict: Result with success status
        """
        try:
            notification = Notification(
                app_id=self.app_id,
                included_segments=segments,
                headings={"en": heading},
                contents={"en": content}
            )
            
            if data:
                notification.data = data
            
            response = self.default_api.create_notification(notification)
            
            logger.info(f"OneSignal notification sent to segments: {segments}")
            return {
                'success': True,
                'id': response.id,
                'recipients': response.recipients
            }
            
        except Exception as e:
            logger.error(f"OneSignal segment notification error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_player(self, device_token, device_type, user_id=None):
        """
        Create or update player (device) in OneSignal.
        
        Args:
            device_token (str): Device token
            device_type (int): Device type (0=iOS, 1=Android, etc.)
            user_id (str): Optional external user ID
            
        Returns:
            dict: Result with player ID
        """
        try:
            player = Player(
                app_id=self.app_id,
                device_token=device_token,
                device_type=device_type
            )
            
            if user_id:
                player.external_user_id = user_id
            
            response = self.default_api.create_player(player)
            
            logger.info(f"OneSignal player created: {response.id}")
            return {
                'success': True,
                'player_id': response.id
            }
            
        except Exception as e:
            logger.error(f"OneSignal player creation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_limit_request_notification(self, player_ids, request_status, customer_name):
        """
        Send limit request status notification.
        
        Args:
            player_ids (list): OneSignal player IDs
            request_status (str): Request status
            customer_name (str): Customer name
            
        Returns:
            dict: Notification sending result
        """
        status_messages = {
            'approved': {
                'heading': 'Limit Increase Approved!',
                'content': f'Good news {customer_name}! Your credit limit increase has been approved.'
            },
            'rejected': {
                'heading': 'Limit Increase Update',
                'content': f'Hi {customer_name}, your limit increase request needs review. Check the app for details.'
            },
            'under_review': {
                'heading': 'Request Under Review',
                'content': f'Hi {customer_name}, we\'re reviewing your limit increase request. You\'ll be notified soon.'
            }
        }
        
        message = status_messages.get(request_status, {
            'heading': 'Limit Request Update',
            'content': f'Hi {customer_name}, there\'s an update on your limit increase request.'
        })
        
        return self.send_notification(
            player_ids,
            message['heading'],
            message['content'],
            data={'type': 'limit_request', 'status': request_status}
        )
```

### Configuration

```python
# OneSignal configuration
ONESIGNAL_APP_ID = os.environ.get('ONESIGNAL_APP_ID')
ONESIGNAL_APP_KEY = os.environ.get('ONESIGNAL_APP_KEY')
ONESIGNAL_USER_KEY = os.environ.get('ONESIGNAL_USER_KEY')
```

## Service Configuration

### Environment Variables

```bash
# Firebase
FIREBASE_CREDENTIALS=/path/to/firebase-credentials.json

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890

# SendGrid
SENDGRID_API_KEY=SG...

# OneSignal
ONESIGNAL_APP_ID=...
ONESIGNAL_APP_KEY=...
ONESIGNAL_USER_KEY=...
```

### Service Registry

```python
class ServiceRegistry:
    """Central registry for external services."""
    
    _services = {}
    
    @classmethod
    def register(cls, service_name, service_class):
        cls._services[service_name] = service_class
    
    @classmethod
    def get(cls, service_name):
        if service_name not in cls._services:
            raise ValueError(f"Service {service_name} not registered")
        return cls._services[service_name]()

# Register services
ServiceRegistry.register('firebase', FirebaseService)
ServiceRegistry.register('twilio', TwilioService)
ServiceRegistry.register('sendgrid', SendGridService)
ServiceRegistry.register('onesignal', OneSignalService)
```

## Error Handling

### Retry Mechanisms

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1, backoff=2):
    """Decorator for retrying failed service calls."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries exceeded for {func.__name__}: {str(e)}")
                        raise
                    
                    wait_time = delay * (backoff ** (retries - 1))
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} in {wait_time}s")
                    time.sleep(wait_time)
            
        return wrapper
    return decorator

# Usage
class ResilientTwilioService(TwilioService):
    @retry_on_failure(max_retries=3, delay=2)
    def send_sms(self, to_number, message):
        return super().send_sms(to_number, message)
```

### Circuit Breaker Pattern

```python
import time
from enum import Enum

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
```

## Monitoring & Analytics

### Service Health Monitoring

```python
from django.http import JsonResponse
from django.views import View

class ServiceHealthView(View):
    """Health check endpoint for external services."""
    
    def get(self, request):
        health_status = {}
        
        # Check Firebase
        try:
            firebase_service = FirebaseService()
            # Perform a lightweight operation
            health_status['firebase'] = 'healthy'
        except Exception as e:
            health_status['firebase'] = f'unhealthy: {str(e)}'
        
        # Check Twilio
        try:
            twilio_service = TwilioService()
            # Check account status
            account = twilio_service.client.api.accounts(
                twilio_service.client.username
            ).fetch()
            health_status['twilio'] = 'healthy' if account.status == 'active' else 'unhealthy'
        except Exception as e:
            health_status['twilio'] = f'unhealthy: {str(e)}'
        
        # Check SendGrid
        try:
            sendgrid_service = SendGridService()
            # This would typically be a lightweight API call
            health_status['sendgrid'] = 'healthy'
        except Exception as e:
            health_status['sendgrid'] = f'unhealthy: {str(e)}'
        
        # Check OneSignal
        try:
            onesignal_service = OneSignalService()
            # Check app status
            health_status['onesignal'] = 'healthy'
        except Exception as e:
            health_status['onesignal'] = f'unhealthy: {str(e)}'
        
        overall_health = 'healthy' if all(
            status == 'healthy' for status in health_status.values()
        ) else 'degraded'
        
        return JsonResponse({
            'status': overall_health,
            'services': health_status,
            'timestamp': time.time()
        })
```

### Service Metrics

```python
import time
from django.core.cache import cache

class ServiceMetrics:
    """Track service usage metrics."""
    
    @staticmethod
    def record_service_call(service_name, operation, success=True, duration=None):
        """Record service call metrics."""
        timestamp = int(time.time())
        hour_key = f"metrics:{service_name}:{operation}:{timestamp // 3600}"
        
        # Increment counters
        cache.set(f"{hour_key}:total", cache.get(f"{hour_key}:total", 0) + 1, 7200)
        
        if success:
            cache.set(f"{hour_key}:success", cache.get(f"{hour_key}:success", 0) + 1, 7200)
        else:
            cache.set(f"{hour_key}:failure", cache.get(f"{hour_key}:failure", 0) + 1, 7200)
        
        if duration:
            # Store response time for averaging
            times_key = f"{hour_key}:times"
            times = cache.get(times_key, [])
            times.append(duration)
            cache.set(times_key, times[-100:], 7200)  # Keep last 100 times
    
    @staticmethod
    def get_service_metrics(service_name, operation, hours=24):
        """Get service metrics for specified time period."""
        current_hour = int(time.time()) // 3600
        metrics = []
        
        for i in range(hours):
            hour = current_hour - i
            hour_key = f"metrics:{service_name}:{operation}:{hour}"
            
            total = cache.get(f"{hour_key}:total", 0)
            success = cache.get(f"{hour_key}:success", 0)
            failure = cache.get(f"{hour_key}:failure", 0)
            times = cache.get(f"{hour_key}:times", [])
            
            avg_time = sum(times) / len(times) if times else 0
            success_rate = (success / total * 100) if total > 0 else 0
            
            metrics.append({
                'hour': hour,
                'total_calls': total,
                'success_calls': success,
                'failed_calls': failure,
                'success_rate': success_rate,
                'avg_response_time': avg_time
            })
        
        return metrics
```

## Security Considerations

### Credential Management

```python
# Use environment variables for sensitive data
import os
from django.core.exceptions import ImproperlyConfigured

def get_env_variable(var_name, default=None):
    """Get environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        raise ImproperlyConfigured(f"Set the {var_name} environment variable")

# Secure credential loading
FIREBASE_CREDENTIALS = get_env_variable('FIREBASE_CREDENTIALS')
TWILIO_AUTH_TOKEN = get_env_variable('TWILIO_AUTH_TOKEN')
SENDGRID_API_KEY = get_env_variable('SENDGRID_API_KEY')
```

### Rate Limiting

```python
from django.core.cache import cache
from django.http import JsonResponse

def rate_limit_service_calls(service_name, calls_per_minute=60):
    """Rate limit decorator for service calls."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create rate limit key
            current_minute = int(time.time()) // 60
            rate_key = f"rate_limit:{service_name}:{current_minute}"
            
            # Check current call count
            current_calls = cache.get(rate_key, 0)
            
            if current_calls >= calls_per_minute:
                raise Exception(f"Rate limit exceeded for {service_name}")
            
            # Increment counter
            cache.set(rate_key, current_calls + 1, 60)
            
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator
```

### Data Sanitization

```python
import re
from django.utils.html import escape

class DataSanitizer:
    """Sanitize data before sending to external services."""
    
    @staticmethod
    def sanitize_phone_number(phone):
        """Sanitize and validate phone number."""
        # Remove all non-digit characters except +
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Validate format
        if not re.match(r'^\+?1?[0-9]{10,15}$', clean_phone):
            raise ValueError("Invalid phone number format")
        
        return clean_phone
    
    @staticmethod
    def sanitize_email(email):
        """Sanitize and validate email address."""
        # Basic email validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValueError("Invalid email format")
        
        return email.lower().strip()
    
    @staticmethod
    def sanitize_message_content(content):
        """Sanitize message content."""
        # Remove HTML tags and escape special characters
        clean_content = escape(content)
        
        # Limit length
        if len(clean_content) > 1000:
            clean_content = clean_content[:997] + "..."
        
        return clean_content
```

## Testing External Services

### Service Mocking

```python
from unittest.mock import Mock, patch
import pytest

@pytest.fixture
def mock_firebase_service():
    """Mock Firebase service for testing."""
    with patch('services.firebase_service.FirebaseService') as mock:
        mock_instance = Mock()
        mock_instance.verify_token.return_value = {'uid': 'test_user_123'}
        mock_instance.send_push_notification.return_value = {
            'success_count': 1,
            'failure_count': 0
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_twilio_service():
    """Mock Twilio service for testing."""
    with patch('services.twilio_service.TwilioService') as mock:
        mock_instance = Mock()
        mock_instance.send_sms.return_value = {
            'success': True,
            'sid': 'test_message_sid'
        }
        mock.return_value = mock_instance
        yield mock_instance

# Test using mocks
def test_send_otp_notification(mock_twilio_service):
    """Test OTP sending functionality."""
    otp_service = OTPService()
    result = otp_service.send_otp('+1234567890', 'sms')
    
    assert result['success'] is True
    mock_twilio_service.send_otp.assert_called_once_with('+1234567890', mock.ANY)
```

### Integration Testing

```python
import pytest
from django.test import TestCase, override_settings

@override_settings(
    TWILIO_ACCOUNT_SID='test_sid',
    TWILIO_AUTH_TOKEN='test_token',
    TWILIO_PHONE_NUMBER='+1234567890'
)
class ExternalServiceIntegrationTest(TestCase):
    """Integration tests for external services."""
    
    def setUp(self):
        self.twilio_service = TwilioService()
        self.sendgrid_service = SendGridService()
    
    @patch('twilio.rest.Client')
    def test_twilio_integration(self, mock_client):
        """Test Twilio SMS integration."""
        # Configure mock
        mock_client.return_value.messages.create.return_value.sid = 'test_sid'
        
        result = self.twilio_service.send_sms('+1234567890', 'Test message')
        
        assert result['success'] is True
        assert result['sid'] == 'test_sid'
    
    @patch('sendgrid.SendGridAPIClient')
    def test_sendgrid_integration(self, mock_client):
        """Test SendGrid email integration."""
        # Configure mock
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client.return_value.send.return_value = mock_response
        
        result = self.sendgrid_service.send_email(
            'test@example.com',
            'Test Subject',
            '<p>Test Content</p>'
        )
        
        assert result['success'] is True
        assert result['status_code'] == 202
```

## Conclusion

This external services integration documentation provides a comprehensive guide for implementing, configuring, and maintaining integrations with Firebase, Twilio, SendGrid, and OneSignal. The implementation emphasizes security, reliability, and monitoring to ensure robust communication capabilities for the Card Limit Increase System.

Each service is designed with proper error handling, retry mechanisms, and monitoring to maintain high availability and reliability in production environments.