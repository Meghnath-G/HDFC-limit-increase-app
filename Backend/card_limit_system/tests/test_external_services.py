"""
Tests for external service integrations.

Tests Firebase, Twilio, SendGrid, and OneSignal service integrations
with proper mocking and error handling scenarios.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase
from django.conf import settings

from core.firebase_service import FirebaseService
from core.twilio_service import TwilioService
from core.sendgrid_service import SendGridService
from core.onesignal_service import OneSignalService
from tests.factories import CustomerFactory


class FirebaseServiceTest(TestCase):
    """Test cases for Firebase service integration."""
    
    def setUp(self):
        """Set up test data."""
        self.customer = CustomerFactory()
        self.test_token = 'test_firebase_token'
        self.test_uid = 'test_firebase_uid'
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_verify_token_success(self, mock_verify):
        """Test successful token verification."""
        mock_verify.return_value = {
            'uid': self.test_uid,
            'email': self.customer.email,
            'email_verified': True
        }
        
        result = FirebaseService.verify_token(self.test_token)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['uid'], self.test_uid)
        self.assertEqual(result['email'], self.customer.email)
        mock_verify.assert_called_once_with(self.test_token)
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_verify_token_invalid(self, mock_verify):
        """Test token verification with invalid token."""
        mock_verify.side_effect = Exception('Invalid token')
        
        result = FirebaseService.verify_token('invalid_token')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('firebase_admin.auth.create_user')
    def test_create_user_success(self, mock_create):
        """Test successful user creation."""
        mock_create.return_value = Mock(uid=self.test_uid)
        
        result = FirebaseService.create_user(
            email=self.customer.email,
            phone_number=self.customer.phone_number
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['uid'], self.test_uid)
        mock_create.assert_called_once()
    
    @patch('firebase_admin.auth.create_user')
    def test_create_user_failure(self, mock_create):
        """Test user creation failure."""
        mock_create.side_effect = Exception('User creation failed')
        
        result = FirebaseService.create_user(
            email=self.customer.email,
            phone_number=self.customer.phone_number
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('firebase_admin.messaging.send')
    def test_send_push_notification_success(self, mock_send):
        """Test successful push notification sending."""
        mock_send.return_value = 'test_message_id'
        
        result = FirebaseService.send_push_notification(
            token='device_token',
            title='Test Title',
            body='Test Message'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'test_message_id')
        mock_send.assert_called_once()
    
    @patch('firebase_admin.messaging.send')
    def test_send_push_notification_failure(self, mock_send):
        """Test push notification sending failure."""
        mock_send.side_effect = Exception('Send failed')
        
        result = FirebaseService.send_push_notification(
            token='device_token',
            title='Test Title',
            body='Test Message'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TwilioServiceTest(TestCase):
    """Test cases for Twilio service integration."""
    
    def setUp(self):
        """Set up test data."""
        self.customer = CustomerFactory()
        self.phone_number = '+919876543210'
        self.message = 'Test SMS message'
    
    @patch('twilio.rest.Client')
    def test_send_sms_success(self, mock_client):
        """Test successful SMS sending."""
        mock_messages = Mock()
        mock_messages.create.return_value = Mock(sid='test_message_sid')
        mock_client.return_value.messages = mock_messages
        
        result = TwilioService.send_sms(
            to=self.phone_number,
            message=self.message
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_sid'], 'test_message_sid')
        mock_messages.create.assert_called_once()
    
    @patch('twilio.rest.Client')
    def test_send_sms_failure(self, mock_client):
        """Test SMS sending failure."""
        mock_messages = Mock()
        mock_messages.create.side_effect = Exception('SMS failed')
        mock_client.return_value.messages = mock_messages
        
        result = TwilioService.send_sms(
            to=self.phone_number,
            message=self.message
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('twilio.rest.Client')
    def test_send_verification_success(self, mock_client):
        """Test successful verification sending."""
        mock_verify = Mock()
        mock_verify.verifications.create.return_value = Mock(
            sid='test_verification_sid',
            status='pending'
        )
        mock_client.return_value.verify.v2.services.return_value = mock_verify
        
        result = TwilioService.send_verification(
            to=self.phone_number,
            channel='sms'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['verification_sid'], 'test_verification_sid')
    
    @patch('twilio.rest.Client')
    def test_check_verification_success(self, mock_client):
        """Test successful verification check."""
        mock_verify = Mock()
        mock_verify.verification_checks.create.return_value = Mock(
            status='approved'
        )
        mock_client.return_value.verify.v2.services.return_value = mock_verify
        
        result = TwilioService.check_verification(
            to=self.phone_number,
            code='123456'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'approved')
    
    @patch('twilio.rest.Client')
    def test_make_voice_call_success(self, mock_client):
        """Test successful voice call."""
        mock_calls = Mock()
        mock_calls.create.return_value = Mock(sid='test_call_sid')
        mock_client.return_value.calls = mock_calls
        
        result = TwilioService.make_voice_call(
            to=self.phone_number,
            message='Test voice message'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['call_sid'], 'test_call_sid')
    
    @patch('twilio.rest.Client')
    def test_send_whatsapp_message_success(self, mock_client):
        """Test successful WhatsApp message sending."""
        mock_messages = Mock()
        mock_messages.create.return_value = Mock(sid='test_whatsapp_sid')
        mock_client.return_value.messages = mock_messages
        
        result = TwilioService.send_whatsapp_message(
            to=f'whatsapp:{self.phone_number}',
            message=self.message
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_sid'], 'test_whatsapp_sid')


class SendGridServiceTest(TestCase):
    """Test cases for SendGrid service integration."""
    
    def setUp(self):
        """Set up test data."""
        self.customer = CustomerFactory()
        self.email_data = {
            'to_email': self.customer.email,
            'subject': 'Test Email',
            'html_content': '<h1>Test HTML Content</h1>',
            'plain_content': 'Test plain content'
        }
    
    @patch('sendgrid.SendGridAPIClient.send')
    def test_send_email_success(self, mock_send):
        """Test successful email sending."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'x-message-id': 'test_message_id'}
        mock_send.return_value = mock_response
        
        result = SendGridService.send_email(**self.email_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'test_message_id')
        mock_send.assert_called_once()
    
    @patch('sendgrid.SendGridAPIClient.send')
    def test_send_email_failure(self, mock_send):
        """Test email sending failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.body = '{"errors": ["Invalid email"]}'
        mock_send.return_value = mock_response
        
        result = SendGridService.send_email(**self.email_data)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('sendgrid.SendGridAPIClient.send')
    def test_send_template_email_success(self, mock_send):
        """Test successful template email sending."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'x-message-id': 'test_template_id'}
        mock_send.return_value = mock_response
        
        result = SendGridService.send_template_email(
            to_email=self.customer.email,
            template_id='test_template_id',
            template_data={'name': 'John Doe'}
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'test_template_id')
    
    @patch('sendgrid.SendGridAPIClient.client.mail.send.post')
    def test_send_bulk_email_success(self, mock_post):
        """Test successful bulk email sending."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_post.return_value = mock_response
        
        recipients = [
            {'email': 'user1@example.com', 'name': 'User 1'},
            {'email': 'user2@example.com', 'name': 'User 2'}
        ]
        
        result = SendGridService.send_bulk_email(
            recipients=recipients,
            subject='Bulk Test',
            html_content='<h1>Bulk Email</h1>'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['sent_count'], 2)


class OneSignalServiceTest(TestCase):
    """Test cases for OneSignal service integration."""
    
    def setUp(self):
        """Set up test data."""
        self.customer = CustomerFactory()
        self.notification_data = {
            'title': 'Test Notification',
            'message': 'Test notification message',
            'player_ids': ['test_player_id']
        }
    
    @patch('requests.request')
    def test_send_notification_success(self, mock_request):
        """Test successful notification sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'test_notification_id',
            'recipients': 1
        }
        mock_request.return_value = mock_response
        
        result = OneSignalService.send_notification(**self.notification_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['notification_id'], 'test_notification_id')
        self.assertEqual(result['recipients'], 1)
    
    @patch('requests.request')
    def test_send_notification_failure(self, mock_request):
        """Test notification sending failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'errors': ['Invalid player ID']
        }
        mock_request.return_value = mock_response
        
        result = OneSignalService.send_notification(**self.notification_data)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('requests.request')
    def test_create_player_success(self, mock_request):
        """Test successful player creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'test_player_id',
            'success': True
        }
        mock_request.return_value = mock_response
        
        result = OneSignalService.create_player(
            device_token='test_device_token',
            device_type=1,
            user_id=self.customer.customer_id
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['player_id'], 'test_player_id')
    
    @patch('requests.request')
    def test_send_to_user_success(self, mock_request):
        """Test successful notification to specific user."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'test_notification_id',
            'recipients': 1
        }
        mock_request.return_value = mock_response
        
        result = OneSignalService.send_to_user(
            user_id=self.customer.customer_id,
            title='User Notification',
            message='Message for specific user'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['notification_id'], 'test_notification_id')
    
    @patch('requests.request')
    def test_get_notification_status_success(self, mock_request):
        """Test getting notification status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'successful': 1,
            'failed': 0,
            'converted': 0,
            'completed_at': '2025-09-17T10:00:00.000Z'
        }
        mock_request.return_value = mock_response
        
        result = OneSignalService.get_notification_status('test_notification_id')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['successful'], 1)
        self.assertEqual(result['failed'], 0)


class ExternalServiceIntegrationTest(TestCase):
    """Integration tests for multiple external services."""
    
    def setUp(self):
        """Set up test data."""
        self.customer = CustomerFactory()
    
    @patch('core.firebase_service.FirebaseService.verify_token')
    @patch('core.twilio_service.TwilioService.send_sms')
    @patch('core.sendgrid_service.SendGridService.send_email')
    @patch('core.onesignal_service.OneSignalService.send_notification')
    def test_multi_channel_notification_flow(self, mock_onesignal, mock_sendgrid, 
                                           mock_twilio, mock_firebase):
        """Test sending notifications across multiple channels."""
        # Mock all external services
        mock_firebase.return_value = {'success': True, 'uid': 'test_uid'}
        mock_twilio.return_value = {'success': True, 'message_sid': 'sms_123'}
        mock_sendgrid.return_value = {'success': True, 'message_id': 'email_123'}
        mock_onesignal.return_value = {'success': True, 'notification_id': 'push_123'}
        
        # Simulate notification sending
        from notifications.models import NotificationLog
        
        # Create notification records
        sms_result = TwilioService.send_sms(
            to=self.customer.phone_number,
            message='Test SMS notification'
        )
        
        email_result = SendGridService.send_email(
            to_email=self.customer.email,
            subject='Test Email',
            html_content='<h1>Test</h1>'
        )
        
        push_result = OneSignalService.send_notification(
            player_ids=['test_player'],
            title='Test Push',
            message='Test push notification'
        )
        
        # Verify all services were called successfully
        self.assertTrue(sms_result['success'])
        self.assertTrue(email_result['success'])
        self.assertTrue(push_result['success'])
        
        # Verify service calls
        mock_twilio.assert_called_once()
        mock_sendgrid.assert_called_once()
        mock_onesignal.assert_called_once()
    
    @patch('core.twilio_service.TwilioService.send_verification')
    @patch('core.sendgrid_service.SendGridService.send_email')
    def test_otp_verification_flow(self, mock_sendgrid, mock_twilio):
        """Test OTP verification across SMS and email."""
        mock_twilio.return_value = {
            'success': True,
            'verification_sid': 'test_verification_sid'
        }
        mock_sendgrid.return_value = {
            'success': True,
            'message_id': 'test_email_id'
        }
        
        # Send OTP via SMS
        sms_result = TwilioService.send_verification(
            to=self.customer.phone_number,
            channel='sms'
        )
        
        # Send OTP via email
        email_result = SendGridService.send_email(
            to_email=self.customer.email,
            subject='Your OTP Code',
            html_content='Your OTP: 123456'
        )
        
        self.assertTrue(sms_result['success'])
        self.assertTrue(email_result['success'])
        mock_twilio.assert_called_once()
        mock_sendgrid.assert_called_once()


class ExternalServiceErrorHandlingTest(TestCase):
    """Test error handling for external services."""
    
    @patch('core.firebase_service.FirebaseService.verify_token')
    def test_firebase_network_error(self, mock_verify):
        """Test Firebase network error handling."""
        mock_verify.side_effect = ConnectionError('Network error')
        
        result = FirebaseService.verify_token('test_token')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertEqual(result['error_code'], 'CONNECTION_ERROR')
    
    @patch('core.twilio_service.TwilioService.send_sms')
    def test_twilio_rate_limit_error(self, mock_send):
        """Test Twilio rate limit error handling."""
        from twilio.base.exceptions import TwilioRestException
        
        mock_send.side_effect = TwilioRestException(
            status=429,
            uri='test_uri',
            method='POST',
            code=20429,
            msg='Too Many Requests'
        )
        
        result = TwilioService.send_sms(
            to='+919876543210',
            message='Test message'
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_code'], 'RATE_LIMIT_EXCEEDED')
    
    @patch('core.sendgrid_service.SendGridService.send_email')
    def test_sendgrid_authentication_error(self, mock_send):
        """Test SendGrid authentication error handling."""
        mock_send.side_effect = Exception('Unauthorized: Invalid API key')
        
        result = SendGridService.send_email(
            to_email='test@example.com',
            subject='Test',
            html_content='Test content'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('Unauthorized', result['error'])


if __name__ == '__main__':
    unittest.main()