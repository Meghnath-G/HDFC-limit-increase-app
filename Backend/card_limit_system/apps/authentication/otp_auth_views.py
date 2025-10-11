"""
OTP-based Authentication Views for HDFC Banking System

These views provide OTP-based authentication that integrates with
the existing Firebase authentication system and customer management.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
import uuid
import logging
import json

from core.twilio_otp_service import TwilioOTPService
from apps.customers.models import Customer
from apps.customers.serializers import CustomerRegistrationSerializer, CustomerDisplaySerializer
from core.utils import encrypt_field, decrypt_field
from core.authentication import FirebaseUser
from core.firebase_config import get_firebase_auth

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def phone_login_request(request):
    """
    Step 1: Request OTP for phone-based login
    
    POST /api/auth/phone-login/request/
    {
        "phone_number": "+919876543210"
    }
    """
    try:
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                'success': False,
                'error': 'MISSING_PHONE',
                'message': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if customer exists with this phone
        try:
            encrypted_phone = encrypt_field(phone_number)
            customer = Customer.objects.get(phone=encrypted_phone, is_active=True)
            
            # Check rate limits
            can_request, rate_limit_message = customer.can_request_otp()
            if not can_request:
                return Response({
                    'success': False,
                    'error': 'RATE_LIMITED',
                    'message': rate_limit_message
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            customer_id = str(customer.id)
            
        except Customer.DoesNotExist:
            return Response({
                'success': False,
                'error': 'CUSTOMER_NOT_FOUND',
                'message': 'No account found with this phone number. Please register first.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Send OTP
        otp_service = TwilioOTPService()
        result = otp_service.send_otp(
            phone_number=phone_number,
            customer_id=customer_id,
            purpose='authentication'
        )
        
        if result['success']:
            # Update customer OTP attempts
            customer.increment_otp_attempts()
            
            # Store login session info in cache
            session_id = str(uuid.uuid4())
            cache.set(f'otp_login_session_{session_id}', {
                'customer_id': customer_id,
                'phone_number': phone_number,
                'otp_id': result['otp_id'],
                'created_at': timezone.now().isoformat()
            }, 600)  # 10 minutes
            
            return Response({
                'success': True,
                'message': 'OTP sent successfully',
                'session_id': session_id,
                'masked_phone': customer.get_masked_phone(),
                'expires_in': result.get('expires_in', 300)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'OTP_SEND_FAILED'),
                'message': result.get('message', 'Failed to send OTP')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Phone login request error: {e}")
        return Response({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def phone_login_verify(request):
    """
    Step 2: Verify OTP and complete phone-based login
    
    POST /api/auth/phone-login/verify/
    {
        "session_id": "uuid-session-id",
        "otp_code": "123456"
    }
    """
    try:
        session_id = request.data.get('session_id')
        otp_code = request.data.get('otp_code')
        
        if not session_id or not otp_code:
            return Response({
                'success': False,
                'error': 'MISSING_FIELDS',
                'message': 'Session ID and OTP code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get session data
        session_data = cache.get(f'otp_login_session_{session_id}')
        if not session_data:
            return Response({
                'success': False,
                'error': 'SESSION_EXPIRED',
                'message': 'Login session has expired. Please request a new OTP.'
            }, status=status.HTTP_410_GONE)
        
        # Verify OTP
        otp_service = TwilioOTPService()
        result = otp_service.verify_otp(
            otp_id=session_data['otp_id'],
            otp_code=otp_code,
            phone_number=session_data['phone_number']
        )
        
        if result['success']:
            # Get customer
            customer = Customer.objects.get(id=session_data['customer_id'])
            
            # Mark phone as verified
            customer.mark_phone_verified()
            
            # Update last login
            customer.updated_at = timezone.now()
            customer.save(update_fields=['updated_at'])
            
            # Generate Firebase custom token for the customer
            try:
                firebase_auth = get_firebase_auth()
                
                # Create custom token with customer claims
                custom_claims = {
                    'customer_id': str(customer.id),
                    'phone_verified': True,
                    'phone_number': customer.get_masked_phone(),
                    'customer_segment': getattr(customer, 'customer_segment', 'standard'),
                    'kyc_completed': getattr(customer, 'is_kyc_completed', False)
                }
                
                firebase_token = firebase_auth.create_custom_token(
                    uid=customer.firebase_uid,
                    developer_claims=custom_claims
                )
                
                # Clear session
                cache.delete(f'otp_login_session_{session_id}')
                
                # Get customer profile data
                customer_serializer = CustomerDisplaySerializer(customer)
                
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'auth_token': firebase_token.decode() if isinstance(firebase_token, bytes) else firebase_token,
                    'customer': customer_serializer.data,
                    'login_timestamp': timezone.now().isoformat()
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Firebase token generation error: {e}")
                return Response({
                    'success': False,
                    'error': 'TOKEN_GENERATION_FAILED',
                    'message': 'Authentication successful but token generation failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'INVALID_OTP'),
                'message': result.get('message', 'Invalid OTP code')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Customer.DoesNotExist:
        return Response({
            'success': False,
            'error': 'CUSTOMER_NOT_FOUND',
            'message': 'Customer not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Phone login verify error: {e}")
        return Response({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def phone_register_request(request):
    """
    Step 1: Request OTP for phone-based registration
    
    POST /api/auth/phone-register/request/
    {
        "phone_number": "+919876543210",
        "name": "John Doe",
        "email": "john@example.com",
        "date_of_birth": "1990-01-01"
    }
    """
    try:
        phone_number = request.data.get('phone_number')
        name = request.data.get('name')
        email = request.data.get('email')
        
        if not phone_number or not name:
            return Response({
                'success': False,
                'error': 'MISSING_FIELDS',
                'message': 'Phone number and name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if customer already exists
        try:
            encrypted_phone = encrypt_field(phone_number)
            existing_customer = Customer.objects.get(phone=encrypted_phone)
            
            return Response({
                'success': False,
                'error': 'CUSTOMER_EXISTS',
                'message': 'Account with this phone number already exists. Please use login instead.'
            }, status=status.HTTP_409_CONFLICT)
            
        except Customer.DoesNotExist:
            pass  # Good, customer doesn't exist
        
        # Send OTP for registration
        otp_service = TwilioOTPService()
        result = otp_service.send_otp(
            phone_number=phone_number,
            customer_id=None,  # No customer ID yet
            purpose='registration'
        )
        
        if result['success']:
            # Store registration session info in cache
            session_id = str(uuid.uuid4())
            cache.set(f'otp_register_session_{session_id}', {
                'phone_number': phone_number,
                'name': name,
                'email': email,
                'date_of_birth': request.data.get('date_of_birth'),
                'otp_id': result['otp_id'],
                'created_at': timezone.now().isoformat()
            }, 600)  # 10 minutes
            
            return Response({
                'success': True,
                'message': 'OTP sent for registration verification',
                'session_id': session_id,
                'expires_in': result.get('expires_in', 300)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'OTP_SEND_FAILED'),
                'message': result.get('message', 'Failed to send OTP')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Phone register request error: {e}")
        return Response({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@transaction.atomic
def phone_register_verify(request):
    """
    Step 2: Verify OTP and complete phone-based registration
    
    POST /api/auth/phone-register/verify/
    {
        "session_id": "uuid-session-id",
        "otp_code": "123456"
    }
    """
    try:
        session_id = request.data.get('session_id')
        otp_code = request.data.get('otp_code')
        
        if not session_id or not otp_code:
            return Response({
                'success': False,
                'error': 'MISSING_FIELDS',
                'message': 'Session ID and OTP code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get session data
        session_data = cache.get(f'otp_register_session_{session_id}')
        if not session_data:
            return Response({
                'success': False,
                'error': 'SESSION_EXPIRED',
                'message': 'Registration session has expired. Please start registration again.'
            }, status=status.HTTP_410_GONE)
        
        # Verify OTP
        otp_service = TwilioOTPService()
        result = otp_service.verify_otp(
            otp_id=session_data['otp_id'],
            otp_code=otp_code,
            phone_number=session_data['phone_number']
        )
        
        if result['success']:
            # Create Firebase user first
            try:
                firebase_auth = get_firebase_auth()
                
                # Create Firebase user
                firebase_user = firebase_auth.create_user(
                    phone_number=session_data['phone_number'],
                    email=session_data.get('email'),
                    display_name=session_data['name'],
                    email_verified=False,
                    phone_number_verified=True
                )
                
                # Create customer in database
                customer_data = {
                    'firebase_uid': firebase_user.uid,
                    'name': session_data['name'],
                    'email': session_data.get('email', ''),
                    'phone': session_data['phone_number'],
                    'date_of_birth': session_data.get('date_of_birth'),
                    'phone_verified': True,
                    'phone_verified_at': timezone.now(),
                    'otp_verification_count': 1
                }
                
                # Use the registration serializer
                serializer = CustomerRegistrationSerializer(data=customer_data)
                if serializer.is_valid():
                    customer = serializer.save()
                    
                    # Generate Firebase custom token
                    custom_claims = {
                        'customer_id': str(customer.id),
                        'phone_verified': True,
                        'phone_number': customer.get_masked_phone(),
                        'customer_segment': 'standard',
                        'kyc_completed': False,
                        'new_user': True
                    }
                    
                    firebase_token = firebase_auth.create_custom_token(
                        uid=customer.firebase_uid,
                        developer_claims=custom_claims
                    )
                    
                    # Clear session
                    cache.delete(f'otp_register_session_{session_id}')
                    
                    # Get customer profile data
                    customer_serializer = CustomerDisplaySerializer(customer)
                    
                    logger.info(f"New customer registered: {customer.id}")
                    
                    return Response({
                        'success': True,
                        'message': 'Registration completed successfully',
                        'auth_token': firebase_token.decode() if isinstance(firebase_token, bytes) else firebase_token,
                        'customer': customer_serializer.data,
                        'registration_timestamp': timezone.now().isoformat()
                    }, status=status.HTTP_201_CREATED)
                else:
                    # Delete Firebase user if customer creation fails
                    firebase_auth.delete_user(firebase_user.uid)
                    return Response({
                        'success': False,
                        'error': 'CUSTOMER_CREATION_FAILED',
                        'message': 'Customer registration failed',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                logger.error(f"Firebase user creation error: {e}")
                return Response({
                    'success': False,
                    'error': 'USER_CREATION_FAILED',
                    'message': 'Failed to create user account'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'INVALID_OTP'),
                'message': result.get('message', 'Invalid OTP code')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Phone register verify error: {e}")
        return Response({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    """
    Logout user and invalidate tokens
    
    POST /api/auth/logout/
    """
    try:
        # Get customer
        try:
            customer = Customer.objects.get(firebase_uid=request.user.username)
            
            # Clear any cached customer data
            cache.delete(f'customer_profile_{customer.id}')
            cache.delete(f'customer_detail_{customer.id}')
            
        except Customer.DoesNotExist:
            pass
        
        # Note: Firebase tokens can't be invalidated server-side
        # Client should discard the token
        
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return Response({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def auth_status(request):
    """
    Get current authentication status
    
    GET /api/auth/status/
    """
    try:
        # Get customer
        customer = Customer.objects.get(firebase_uid=request.user.username)
        
        return Response({
            'success': True,
            'authenticated': True,
            'customer_id': str(customer.id),
            'phone_verified': customer.phone_verified,
            'phone_verified_at': customer.phone_verified_at.isoformat() if customer.phone_verified_at else None,
            'last_login': customer.updated_at.isoformat() if customer.updated_at else None,
            'firebase_uid': customer.firebase_uid
        }, status=status.HTTP_200_OK)
        
    except Customer.DoesNotExist:
        return Response({
            'success': False,
            'error': 'CUSTOMER_NOT_FOUND',
            'message': 'Customer profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Auth status error: {e}")
        return Response({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to get auth status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)