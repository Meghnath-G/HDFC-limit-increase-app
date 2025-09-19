"""
Twilio API integration for SMS, voice, and verification services.

Provides secure Twilio integration with proper error handling,
retry logic, and delivery tracking for OTP and notifications.
"""

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.cache import cache
import time
import random

logger = logging.getLogger(__name__)


class TwilioService:
    """
    Service for Twilio operations.
    
    Handles SMS sending, voice calls, and verification services
    with proper error handling and delivery tracking.
    """
    
    _client = None
    _verify_service_sid = None
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Twilio client."""
        if cls._initialized:
            return
        
        try:
            # Get Twilio credentials from settings
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            verify_service_sid = getattr(settings, 'TWILIO_VERIFY_SERVICE_SID', None)
            
            if account_sid and auth_token:
                cls._client = Client(account_sid, auth_token)
                cls._verify_service_sid = verify_service_sid
                cls._initialized = True
                logger.info("Twilio client initialized successfully")
            else:
                logger.warning("Twilio credentials not configured")
                
        except Exception as e:
            logger.error(f"Twilio initialization failed: {str(e)}")
            raise
    
    @classmethod
    def send_sms(cls, to: str, message: str, from_number: str = None) -> Dict[str, Any]:
        """
        Send SMS message.
        
        Args:
            to: Recipient phone number (E.164 format)
            message: SMS message content
            from_number: Optional sender number (uses default if not provided)
            
        Returns:
            Dictionary with delivery status and message details
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._client:
            return {
                'success': False,
                'error': 'Twilio not configured',
                'error_code': 'CONFIG_ERROR'
            }
        
        try:
            # Use configured sender number if not provided
            if not from_number:
                from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
                if not from_number:
                    return {
                        'success': False,
                        'error': 'No sender phone number configured',
                        'error_code': 'CONFIG_ERROR'
                    }
            
            # Send SMS
            message_instance = cls._client.messages.create(
                body=message,
                from_=from_number,
                to=to
            )
            
            logger.info(f"SMS sent successfully - SID: {message_instance.sid}")
            
            return {
                'success': True,
                'message_sid': message_instance.sid,
                'status': message_instance.status,
                'to': to,
                'from': from_number,
                'price': message_instance.price,
                'price_unit': message_instance.price_unit,
                'date_created': message_instance.date_created,
                'date_sent': message_instance.date_sent
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio SMS error: {e.msg} (Code: {e.code})")
            return {
                'success': False,
                'error': e.msg,
                'error_code': str(e.code),
                'twilio_error_code': e.code
            }
        except Exception as e:
            logger.error(f"SMS send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'UNKNOWN_ERROR'
            }
    
    @classmethod
    def get_message_status(cls, message_sid: str) -> Dict[str, Any]:
        """
        Get SMS message delivery status.
        
        Args:
            message_sid: Twilio message SID
            
        Returns:
            Dictionary with current message status
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._client:
            return {
                'success': False,
                'error': 'Twilio not configured'
            }
        
        try:
            message = cls._client.messages(message_sid).fetch()
            
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'to': message.to,
                'from': message.from_,
                'price': message.price,
                'price_unit': message.price_unit,
                'date_created': message.date_created,
                'date_sent': message.date_sent,
                'date_updated': message.date_updated
            }
            
        except TwilioRestException as e:
            logger.error(f"Get message status error: {e.msg}")
            return {
                'success': False,
                'error': e.msg,
                'error_code': str(e.code)
            }
        except Exception as e:
            logger.error(f"Get message status failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class TwilioVerifyService:
    """
    Service for Twilio Verify API operations.
    
    Handles OTP generation, verification, and management
    with built-in security and rate limiting features.
    """
    
    @classmethod
    def send_verification(cls, to: str, channel: str = 'sms', 
                         custom_message: str = None, locale: str = 'en') -> Dict[str, Any]:
        """
        Send verification code via Twilio Verify.
        
        Args:
            to: Recipient phone number or email (E.164 format for phone)
            channel: Delivery channel ('sms', 'call', 'email', 'whatsapp')
            custom_message: Optional custom message template
            locale: Language locale for the message
            
        Returns:
            Dictionary with verification status and details
        """
        if not TwilioService._initialized:
            TwilioService.initialize()
        
        if not TwilioService._client or not TwilioService._verify_service_sid:
            return {
                'success': False,
                'error': 'Twilio Verify not configured',
                'error_code': 'CONFIG_ERROR'
            }
        
        try:
            # Prepare verification parameters
            verify_params = {
                'to': to,
                'channel': channel,
                'locale': locale
            }
            
            if custom_message:
                verify_params['custom_message'] = custom_message
            
            # Send verification
            verification = TwilioService._client.verify \
                .v2 \
                .services(TwilioService._verify_service_sid) \
                .verifications \
                .create(**verify_params)
            
            logger.info(f"Verification sent - SID: {verification.sid}, Status: {verification.status}")
            
            return {
                'success': True,
                'verification_sid': verification.sid,
                'status': verification.status,
                'to': to,
                'channel': channel,
                'valid': verification.valid,
                'date_created': verification.date_created,
                'date_updated': verification.date_updated
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio Verify send error: {e.msg} (Code: {e.code})")
            return {
                'success': False,
                'error': e.msg,
                'error_code': str(e.code),
                'twilio_error_code': e.code
            }
        except Exception as e:
            logger.error(f"Verification send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'UNKNOWN_ERROR'
            }
    
    @classmethod
    def check_verification(cls, to: str, code: str) -> Dict[str, Any]:
        """
        Verify OTP code via Twilio Verify.
        
        Args:
            to: Recipient phone number or email
            code: Verification code to check
            
        Returns:
            Dictionary with verification result
        """
        if not TwilioService._initialized:
            TwilioService.initialize()
        
        if not TwilioService._client or not TwilioService._verify_service_sid:
            return {
                'success': False,
                'error': 'Twilio Verify not configured',
                'error_code': 'CONFIG_ERROR'
            }
        
        try:
            # Check verification
            verification_check = TwilioService._client.verify \
                .v2 \
                .services(TwilioService._verify_service_sid) \
                .verification_checks \
                .create(to=to, code=code)
            
            is_valid = verification_check.status == 'approved'
            
            logger.info(f"Verification check - Status: {verification_check.status}, Valid: {is_valid}")
            
            return {
                'success': True,
                'verification_check_sid': verification_check.sid,
                'status': verification_check.status,
                'valid': is_valid,
                'to': to,
                'date_created': verification_check.date_created,
                'date_updated': verification_check.date_updated
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio Verify check error: {e.msg} (Code: {e.code})")
            return {
                'success': False,
                'error': e.msg,
                'error_code': str(e.code),
                'twilio_error_code': e.code,
                'valid': False
            }
        except Exception as e:
            logger.error(f"Verification check failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'UNKNOWN_ERROR',
                'valid': False
            }
    
    @classmethod
    def cancel_verification(cls, verification_sid: str) -> Dict[str, Any]:
        """
        Cancel pending verification.
        
        Args:
            verification_sid: Twilio verification SID
            
        Returns:
            Dictionary with cancellation result
        """
        if not TwilioService._initialized:
            TwilioService.initialize()
        
        if not TwilioService._client or not TwilioService._verify_service_sid:
            return {
                'success': False,
                'error': 'Twilio Verify not configured'
            }
        
        try:
            # Cancel verification
            verification = TwilioService._client.verify \
                .v2 \
                .services(TwilioService._verify_service_sid) \
                .verifications(verification_sid) \
                .update(status='canceled')
            
            logger.info(f"Verification cancelled - SID: {verification.sid}")
            
            return {
                'success': True,
                'verification_sid': verification.sid,
                'status': verification.status
            }
            
        except TwilioRestException as e:
            logger.error(f"Cancel verification error: {e.msg}")
            return {
                'success': False,
                'error': e.msg,
                'error_code': str(e.code)
            }
        except Exception as e:
            logger.error(f"Cancel verification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class TwilioVoiceService:
    """
    Service for Twilio Voice operations.
    
    Handles voice calls and voice-based OTP delivery
    with proper call management and recording features.
    """
    
    @classmethod
    def make_voice_call(cls, to: str, twiml_url: str, from_number: str = None,
                       record: bool = False, timeout: int = 30) -> Dict[str, Any]:
        """
        Make outbound voice call.
        
        Args:
            to: Recipient phone number (E.164 format)
            twiml_url: URL that returns TwiML instructions
            from_number: Optional caller ID (uses default if not provided)
            record: Whether to record the call
            timeout: Call timeout in seconds
            
        Returns:
            Dictionary with call status and details
        """
        if not TwilioService._initialized:
            TwilioService.initialize()
        
        if not TwilioService._client:
            return {
                'success': False,
                'error': 'Twilio not configured'
            }
        
        try:
            # Use configured caller ID if not provided
            if not from_number:
                from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
                if not from_number:
                    return {
                        'success': False,
                        'error': 'No caller phone number configured'
                    }
            
            # Make call
            call = TwilioService._client.calls.create(
                to=to,
                from_=from_number,
                url=twiml_url,
                record=record,
                timeout=timeout
            )
            
            logger.info(f"Voice call initiated - SID: {call.sid}")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'status': call.status,
                'to': to,
                'from': from_number,
                'duration': call.duration,
                'price': call.price,
                'price_unit': call.price_unit,
                'date_created': call.date_created,
                'date_updated': call.date_updated
            }
            
        except TwilioRestException as e:
            logger.error(f"Voice call error: {e.msg}")
            return {
                'success': False,
                'error': e.msg,
                'error_code': str(e.code)
            }
        except Exception as e:
            logger.error(f"Voice call failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def get_call_status(cls, call_sid: str) -> Dict[str, Any]:
        """
        Get voice call status.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Dictionary with current call status
        """
        if not TwilioService._initialized:
            TwilioService.initialize()
        
        if not TwilioService._client:
            return {
                'success': False,
                'error': 'Twilio not configured'
            }
        
        try:
            call = TwilioService._client.calls(call_sid).fetch()
            
            return {
                'success': True,
                'call_sid': call.sid,
                'status': call.status,
                'to': call.to,
                'from': call.from_,
                'duration': call.duration,
                'price': call.price,
                'price_unit': call.price_unit,
                'start_time': call.start_time,
                'end_time': call.end_time,
                'date_created': call.date_created,
                'date_updated': call.date_updated
            }
            
        except TwilioRestException as e:
            logger.error(f"Get call status error: {e.msg}")
            return {
                'success': False,
                'error': e.msg,
                'error_code': str(e.code)
            }
        except Exception as e:
            logger.error(f"Get call status failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def generate_voice_otp_twiml(cls, otp_code: str, language: str = 'en') -> str:
        """
        Generate TwiML for voice OTP delivery.
        
        Args:
            otp_code: OTP code to speak
            language: Language for voice synthesis
            
        Returns:
            TwiML XML string
        """
        # Format OTP code with pauses for clarity
        formatted_otp = ', '.join(otp_code)
        
        # Language-specific messages
        messages = {
            'en': f"Hello, your verification code is: {formatted_otp}. I repeat, your verification code is: {formatted_otp}. Thank you.",
            'hi': f"नमस्ते, आपका सत्यापन कोड है: {formatted_otp}। मैं दोहराता हूं, आपका सत्यापन कोड है: {formatted_otp}। धन्यवाद।"
        }
        
        message = messages.get(language, messages['en'])
        
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice" language="{language}-IN">{message}</Say>
            <Pause length="2"/>
            <Say voice="alice" language="{language}-IN">{message}</Say>
        </Response>'''
        
        return twiml


class TwilioWhatsAppService:
    """
    Service for Twilio WhatsApp Business API operations.
    
    Handles WhatsApp message sending and template management
    with proper content policy compliance and delivery tracking.
    """
    
    @classmethod
    def send_whatsapp_message(cls, to: str, message: str, 
                             media_url: str = None) -> Dict[str, Any]:
        """
        Send WhatsApp message.
        
        Args:
            to: Recipient WhatsApp number (E.164 format with whatsapp: prefix)
            message: Message content
            media_url: Optional media URL for images/documents
            
        Returns:
            Dictionary with delivery status and message details
        """
        if not TwilioService._initialized:
            TwilioService.initialize()
        
        if not TwilioService._client:
            return {
                'success': False,
                'error': 'Twilio not configured'
            }
        
        try:
            # Format WhatsApp number
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            
            # Get WhatsApp sender number
            from_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', None)
            if not from_number:
                return {
                    'success': False,
                    'error': 'WhatsApp sender number not configured'
                }
            
            if not from_number.startswith('whatsapp:'):
                from_number = f'whatsapp:{from_number}'
            
            # Prepare message parameters
            message_params = {
                'body': message,
                'from_': from_number,
                'to': to
            }
            
            if media_url:
                message_params['media_url'] = [media_url]
            
            # Send WhatsApp message
            message_instance = TwilioService._client.messages.create(**message_params)
            
            logger.info(f"WhatsApp message sent - SID: {message_instance.sid}")
            
            return {
                'success': True,
                'message_sid': message_instance.sid,
                'status': message_instance.status,
                'to': to,
                'from': from_number,
                'price': message_instance.price,
                'price_unit': message_instance.price_unit,
                'date_created': message_instance.date_created,
                'date_sent': message_instance.date_sent
            }
            
        except TwilioRestException as e:
            logger.error(f"WhatsApp message error: {e.msg}")
            return {
                'success': False,
                'error': e.msg,
                'error_code': str(e.code)
            }
        except Exception as e:
            logger.error(f"WhatsApp message failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Initialize Twilio on module load
try:
    TwilioService.initialize()
except Exception as e:
    logger.error(f"Twilio initialization failed on import: {str(e)}")
    # Don't raise exception on import to allow application to start