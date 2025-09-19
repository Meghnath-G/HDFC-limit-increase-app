from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.conf import settings
from core.twilio_service import TwilioService
from core.utils import standardize_phone_number
import random
import string
import logging
from datetime import datetime, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)

class OTPView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Send OTP via SMS for card verification"""
        try:
            phone_number = request.data.get('phone_number')
            card_number = request.data.get('card_number', '')
            card_type = request.data.get('card_type', 'Credit Card')
            otp = request.data.get('otp')
            message_type = request.data.get('message_type', 'card_verification')
            
            if not phone_number:
                return Response({
                    'success': False,
                    'error': 'Phone number is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Standardize phone number format
            standardized_phone = standardize_phone_number(phone_number)
            
            # Generate OTP if not provided
            if not otp:
                otp = self._generate_otp()
            
            # Store OTP in cache with 5-minute expiration
            cache_key = f"otp_{standardized_phone}"
            cache.set(cache_key, {
                'otp': otp,
                'card_number': card_number[-4:],  # Store only last 4 digits
                'card_type': card_type,
                'created_at': datetime.now().isoformat(),
                'attempts': 0,
            }, timeout=300)  # 5 minutes
            
            # Initialize Twilio service
            twilio_service = TwilioService()
            
            # Create SMS message based on message type
            if message_type == 'card_verification':
                message = f"Your HDFC {card_type} verification OTP is: {otp}. Valid for 5 minutes. Do not share this code with anyone."
            else:
                message = f"Your HDFC verification OTP is: {otp}. Valid for 5 minutes. Do not share this code."
            
            # Send SMS
            sms_result = twilio_service.send_sms(
                to_number=standardized_phone,
                message=message
            )
            
            if sms_result.get('success'):
                logger.info(f"✅ OTP sent successfully to {standardized_phone}")
                
                return Response({
                    'success': True,
                    'message': 'OTP sent successfully',
                    'phone_number': standardized_phone,
                    'expires_in': 300,
                    'message_sid': sms_result.get('sid'),
                    'otp_debug': otp if settings.DEBUG else None  # Only in debug mode
                })
            else:
                logger.error(f"❌ Failed to send OTP to {standardized_phone}: {sms_result.get('error')}")
                
                return Response({
                    'success': False,
                    'error': 'Failed to send SMS',
                    'details': sms_result.get('error') if settings.DEBUG else None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"❌ OTP send error: {str(e)}")
            
            return Response({
                'success': False,
                'error': 'Internal server error',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_otp(self):
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP for card verification"""
    try:
        phone_number = request.data.get('phone_number')
        entered_otp = request.data.get('otp')
        
        if not phone_number or not entered_otp:
            return Response({
                'success': False,
                'error': 'Phone number and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Standardize phone number
        standardized_phone = standardize_phone_number(phone_number)
        cache_key = f"otp_{standardized_phone}"
        
        # Get stored OTP data
        otp_data = cache.get(cache_key)
        
        if not otp_data:
            return Response({
                'success': False,
                'error': 'OTP expired or not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check attempt limit
        if otp_data.get('attempts', 0) >= 3:
            cache.delete(cache_key)
            return Response({
                'success': False,
                'error': 'Too many failed attempts. Please request a new OTP.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP
        if otp_data['otp'] == entered_otp:
            # Clear OTP from cache after successful verification
            cache.delete(cache_key)
            
            logger.info(f"✅ OTP verified successfully for {standardized_phone}")
            
            return Response({
                'success': True,
                'message': 'OTP verified successfully',
                'card_type': otp_data.get('card_type'),
                'card_last_four': otp_data.get('card_number')
            })
        else:
            # Increment attempt counter
            otp_data['attempts'] = otp_data.get('attempts', 0) + 1
            cache.set(cache_key, otp_data, timeout=300)
            
            logger.warning(f"❌ Invalid OTP for {standardized_phone}. Attempt {otp_data['attempts']}/3")
            
            return Response({
                'success': False,
                'error': 'Invalid OTP',
                'attempts_remaining': 3 - otp_data['attempts']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"❌ OTP verification error: {str(e)}")
        
        return Response({
            'success': False,
            'error': 'Verification failed',
            'details': str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """Resend OTP to phone number"""
    try:
        phone_number = request.data.get('phone_number')
        card_number = request.data.get('card_number', '')
        card_type = request.data.get('card_type', 'Credit Card')
        
        if not phone_number:
            return Response({
                'success': False,
                'error': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Clear existing OTP
        standardized_phone = standardize_phone_number(phone_number)
        cache_key = f"otp_{standardized_phone}"
        cache.delete(cache_key)
        
        # Send new OTP using the same endpoint
        otp_view = OTPView()
        return otp_view.post(request)
        
    except Exception as e:
        logger.error(f"❌ OTP resend error: {str(e)}")
        
        return Response({
            'success': False,
            'error': 'Failed to resend OTP',
            'details': str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)