"""
Firebase Admin SDK integration for authentication and user management.

Provides secure Firebase authentication integration with proper
token validation, user management, and error handling.
"""

import firebase_admin
from firebase_admin import credentials, auth, messaging
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.cache import cache
import json
import time

logger = logging.getLogger(__name__)


class FirebaseAuthService:
    """
    Service for Firebase Admin SDK operations.
    
    Handles user authentication, token validation,
    and Firebase user management operations.
    """
    
    _app = None
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK."""
        if cls._initialized:
            return
        
        try:
            # Get Firebase credentials from settings
            firebase_credentials = getattr(settings, 'FIREBASE_CREDENTIALS', None)
            
            if firebase_credentials:
                if isinstance(firebase_credentials, str):
                    # File path to service account key
                    cred = credentials.Certificate(firebase_credentials)
                elif isinstance(firebase_credentials, dict):
                    # Service account key as dictionary
                    cred = credentials.Certificate(firebase_credentials)
                else:
                    raise ValueError("Invalid Firebase credentials format")
                
                # Initialize Firebase app
                cls._app = firebase_admin.initialize_app(cred)
                cls._initialized = True
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                logger.warning("Firebase credentials not configured")
                
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            raise
    
    @classmethod
    def verify_token(cls, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Firebase ID token and return decoded claims.
        
        Args:
            id_token: Firebase ID token from client
            
        Returns:
            Decoded token claims or None if invalid
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            # Check cache first
            cache_key = f"firebase_token_{id_token[:20]}"
            cached_claims = cache.get(cache_key)
            if cached_claims:
                return cached_claims
            
            # Verify token with Firebase
            decoded_token = auth.verify_id_token(id_token)
            
            # Cache valid token for 5 minutes
            cache.set(cache_key, decoded_token, 300)
            
            logger.info(f"Token verified for user: {decoded_token.get('uid')}")
            return decoded_token
            
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase ID token")
            return None
        except auth.ExpiredIdTokenError:
            logger.warning("Expired Firebase ID token")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return None
    
    @classmethod
    def get_user(cls, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get Firebase user by UID.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            User record or None if not found
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            # Check cache first
            cache_key = f"firebase_user_{uid}"
            cached_user = cache.get(cache_key)
            if cached_user:
                return cached_user
            
            # Get user from Firebase
            user_record = auth.get_user(uid)
            
            # Convert to dictionary
            user_data = {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'phone_number': user_record.phone_number,
                'display_name': user_record.display_name,
                'photo_url': user_record.photo_url,
                'disabled': user_record.disabled,
                'creation_timestamp': user_record.user_metadata.creation_timestamp,
                'last_sign_in_timestamp': user_record.user_metadata.last_sign_in_timestamp,
                'custom_claims': user_record.custom_claims or {}
            }
            
            # Cache user data for 10 minutes
            cache.set(cache_key, user_data, 600)
            
            return user_data
            
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found: {uid}")
            return None
        except Exception as e:
            logger.error(f"Get user failed: {str(e)}")
            return None
    
    @classmethod
    def create_user(cls, email: str, password: str, phone_number: str = None, 
                   display_name: str = None) -> Optional[str]:
        """
        Create new Firebase user.
        
        Args:
            email: User email address
            password: User password
            phone_number: Optional phone number
            display_name: Optional display name
            
        Returns:
            User UID or None if creation failed
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            user_data = {
                'email': email,
                'password': password,
                'email_verified': False
            }
            
            if phone_number:
                user_data['phone_number'] = phone_number
            if display_name:
                user_data['display_name'] = display_name
            
            user_record = auth.create_user(**user_data)
            
            logger.info(f"Firebase user created: {user_record.uid}")
            return user_record.uid
            
        except auth.EmailAlreadyExistsError:
            logger.warning(f"Email already exists: {email}")
            return None
        except auth.PhoneNumberAlreadyExistsError:
            logger.warning(f"Phone number already exists: {phone_number}")
            return None
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return None
    
    @classmethod
    def update_user(cls, uid: str, updates: Dict[str, Any]) -> bool:
        """
        Update Firebase user.
        
        Args:
            uid: Firebase user UID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            auth.update_user(uid, **updates)
            
            # Clear cache
            cache.delete(f"firebase_user_{uid}")
            
            logger.info(f"Firebase user updated: {uid}")
            return True
            
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found: {uid}")
            return False
        except Exception as e:
            logger.error(f"User update failed: {str(e)}")
            return False
    
    @classmethod
    def disable_user(cls, uid: str) -> bool:
        """
        Disable Firebase user.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            True if successful, False otherwise
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            auth.update_user(uid, disabled=True)
            
            # Clear cache
            cache.delete(f"firebase_user_{uid}")
            
            logger.info(f"Firebase user disabled: {uid}")
            return True
            
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found: {uid}")
            return False
        except Exception as e:
            logger.error(f"User disable failed: {str(e)}")
            return False
    
    @classmethod
    def set_custom_claims(cls, uid: str, custom_claims: Dict[str, Any]) -> bool:
        """
        Set custom claims for Firebase user.
        
        Args:
            uid: Firebase user UID
            custom_claims: Custom claims dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            auth.set_custom_user_claims(uid, custom_claims)
            
            # Clear cache
            cache.delete(f"firebase_user_{uid}")
            
            logger.info(f"Custom claims set for user: {uid}")
            return True
            
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found: {uid}")
            return False
        except Exception as e:
            logger.error(f"Set custom claims failed: {str(e)}")
            return False
    
    @classmethod
    def revoke_refresh_tokens(cls, uid: str) -> bool:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            True if successful, False otherwise
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            auth.revoke_refresh_tokens(uid)
            
            logger.info(f"Refresh tokens revoked for user: {uid}")
            return True
            
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found: {uid}")
            return False
        except Exception as e:
            logger.error(f"Revoke tokens failed: {str(e)}")
            return False
    
    @classmethod
    def delete_user(cls, uid: str) -> bool:
        """
        Delete Firebase user.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            True if successful, False otherwise
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            auth.delete_user(uid)
            
            # Clear cache
            cache.delete(f"firebase_user_{uid}")
            
            logger.info(f"Firebase user deleted: {uid}")
            return True
            
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found: {uid}")
            return False
        except Exception as e:
            logger.error(f"User deletion failed: {str(e)}")
            return False
    
    @classmethod
    def generate_email_verification_link(cls, email: str) -> Optional[str]:
        """
        Generate email verification link.
        
        Args:
            email: User email address
            
        Returns:
            Verification link or None if failed
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            link = auth.generate_email_verification_link(email)
            logger.info(f"Email verification link generated for: {email}")
            return link
            
        except Exception as e:
            logger.error(f"Generate verification link failed: {str(e)}")
            return None
    
    @classmethod
    def generate_password_reset_link(cls, email: str) -> Optional[str]:
        """
        Generate password reset link.
        
        Args:
            email: User email address
            
        Returns:
            Reset link or None if failed
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            link = auth.generate_password_reset_link(email)
            logger.info(f"Password reset link generated for: {email}")
            return link
            
        except Exception as e:
            logger.error(f"Generate password reset link failed: {str(e)}")
            return None


class FirebaseMessagingService:
    """
    Service for Firebase Cloud Messaging operations.
    
    Handles push notification delivery through Firebase FCM
    with proper error handling and delivery tracking.
    """
    
    @classmethod
    def send_to_token(cls, token: str, title: str, body: str, 
                     data: Dict[str, str] = None) -> Optional[str]:
        """
        Send push notification to specific device token.
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Optional data payload
            
        Returns:
            Message ID or None if failed
        """
        if not FirebaseAuthService._initialized:
            FirebaseAuthService.initialize()
        
        try:
            # Build message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(f"FCM message sent: {response}")
            return response
            
        except messaging.InvalidArgumentError as e:
            logger.warning(f"Invalid FCM message: {str(e)}")
            return None
        except messaging.UnregisteredError:
            logger.warning(f"Unregistered FCM token: {token}")
            return None
        except Exception as e:
            logger.error(f"FCM send failed: {str(e)}")
            return None
    
    @classmethod
    def send_to_topic(cls, topic: str, title: str, body: str, 
                     data: Dict[str, str] = None) -> Optional[str]:
        """
        Send push notification to topic subscribers.
        
        Args:
            topic: FCM topic name
            title: Notification title
            body: Notification body
            data: Optional data payload
            
        Returns:
            Message ID or None if failed
        """
        if not FirebaseAuthService._initialized:
            FirebaseAuthService.initialize()
        
        try:
            # Build message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                topic=topic
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(f"FCM topic message sent: {response}")
            return response
            
        except Exception as e:
            logger.error(f"FCM topic send failed: {str(e)}")
            return None
    
    @classmethod
    def send_batch(cls, messages: List[messaging.Message]) -> Dict[str, Any]:
        """
        Send batch of push notifications.
        
        Args:
            messages: List of FCM messages
            
        Returns:
            Batch response with success/failure details
        """
        if not FirebaseAuthService._initialized:
            FirebaseAuthService.initialize()
        
        try:
            response = messaging.send_all(messages)
            
            logger.info(f"FCM batch sent - Success: {response.success_count}, "
                       f"Failure: {response.failure_count}")
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'responses': [
                    {
                        'success': resp.success,
                        'message_id': resp.message_id if resp.success else None,
                        'error': str(resp.exception) if not resp.success else None
                    }
                    for resp in response.responses
                ]
            }
            
        except Exception as e:
            logger.error(f"FCM batch send failed: {str(e)}")
            return {
                'success_count': 0,
                'failure_count': len(messages),
                'error': str(e)
            }
    
    @classmethod
    def subscribe_to_topic(cls, tokens: List[str], topic: str) -> Dict[str, Any]:
        """
        Subscribe device tokens to topic.
        
        Args:
            tokens: List of FCM device tokens
            topic: Topic name
            
        Returns:
            Subscription response
        """
        if not FirebaseAuthService._initialized:
            FirebaseAuthService.initialize()
        
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            
            logger.info(f"Topic subscription - Success: {response.success_count}, "
                       f"Failure: {response.failure_count}")
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'errors': [
                    {'index': error.index, 'reason': error.reason}
                    for error in response.errors
                ]
            }
            
        except Exception as e:
            logger.error(f"Topic subscription failed: {str(e)}")
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'error': str(e)
            }
    
    @classmethod
    def unsubscribe_from_topic(cls, tokens: List[str], topic: str) -> Dict[str, Any]:
        """
        Unsubscribe device tokens from topic.
        
        Args:
            tokens: List of FCM device tokens
            topic: Topic name
            
        Returns:
            Unsubscription response
        """
        if not FirebaseAuthService._initialized:
            FirebaseAuthService.initialize()
        
        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            
            logger.info(f"Topic unsubscription - Success: {response.success_count}, "
                       f"Failure: {response.failure_count}")
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'errors': [
                    {'index': error.index, 'reason': error.reason}
                    for error in response.errors
                ]
            }
            
        except Exception as e:
            logger.error(f"Topic unsubscription failed: {str(e)}")
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'error': str(e)
            }


# Initialize Firebase on module load
try:
    FirebaseAuthService.initialize()
except Exception as e:
    logger.error(f"Firebase initialization failed on import: {str(e)}")
    # Don't raise exception on import to allow application to start