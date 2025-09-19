"""
Firebase Authentication for Django REST Framework.

Provides Firebase JWT token validation and user authentication
for the HDFC Card Limit System API.
"""

from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions
from rest_framework.request import Request
from firebase_admin import auth
import logging
from typing import Optional, Tuple, Any

from core.firebase_config import initialize_firebase

logger = logging.getLogger(__name__)


class FirebaseUser:
    """
    Firebase authenticated user representation.
    
    Provides a user-like interface for Firebase authenticated users
    compatible with Django's authentication system.
    """
    
    def __init__(self, firebase_uid: str, email: str = None, email_verified: bool = False):
        self.firebase_uid = firebase_uid
        self.username = firebase_uid  # Use Firebase UID as username
        self.email = email or ''
        self.email_verified = email_verified
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        self.is_staff = False
        self.is_superuser = False
    
    def __str__(self):
        return f"FirebaseUser({self.firebase_uid})"
    
    def __repr__(self):
        return f"<FirebaseUser: {self.firebase_uid}>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        # Can be extended to check custom claims
        return self.is_staff or self.is_superuser
    
    def has_perm(self, perm: str, obj=None) -> bool:
        """Check if user has specific permission."""
        # For now, staff users have all permissions
        return self.is_staff
    
    def has_perms(self, perm_list: list, obj=None) -> bool:
        """Check if user has multiple permissions."""
        return all(self.has_perm(perm, obj) for perm in perm_list)
    
    def has_module_perms(self, module: str) -> bool:
        """Check if user has permissions for a module."""
        return self.is_staff
    
    def get_group_permissions(self, obj=None):
        """Get group permissions (placeholder)."""
        return set()
    
    def get_all_permissions(self, obj=None):
        """Get all permissions (placeholder)."""
        return set()


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Firebase JWT token authentication for Django REST Framework.
    
    Validates Firebase ID tokens and creates FirebaseUser instances
    for authenticated requests.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize Firebase if not already done
        try:
            initialize_firebase()
        except Exception as e:
            logger.error(f"Failed to initialize Firebase for authentication: {str(e)}")
    
    def authenticate(self, request: Request) -> Optional[Tuple[FirebaseUser, str]]:
        """
        Authenticate the request using Firebase ID token.
        
        Args:
            request: Django REST framework request object
            
        Returns:
            Tuple of (user, token) if authenticated, None otherwise
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
        
        try:
            # Extract token from Authorization header
            auth_parts = auth_header.split(' ')
            
            if len(auth_parts) != 2 or auth_parts[0].lower() != 'bearer':
                return None
            
            id_token = auth_parts[1]
            
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(id_token)
            
            # Extract user information
            firebase_uid = decoded_token.get('uid')
            email = decoded_token.get('email', '')
            email_verified = decoded_token.get('email_verified', False)
            
            if not firebase_uid:
                raise exceptions.AuthenticationFailed('Invalid Firebase token: missing UID')
            
            # Create Firebase user instance
            firebase_user = FirebaseUser(
                firebase_uid=firebase_uid,
                email=email,
                email_verified=email_verified
            )
            
            # Check for admin custom claims
            custom_claims = decoded_token.get('custom_claims', {})
            firebase_user.is_staff = custom_claims.get('admin', False)
            firebase_user.is_superuser = custom_claims.get('superuser', False)
            
            logger.info(f"Authenticated Firebase user: {firebase_uid}")
            return (firebase_user, id_token)
            
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid Firebase ID token: {str(e)}")
            raise exceptions.AuthenticationFailed('Invalid Firebase ID token')
        except auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired Firebase ID token: {str(e)}")
            raise exceptions.AuthenticationFailed('Expired Firebase ID token')
        except auth.RevokedIdTokenError as e:
            logger.warning(f"Revoked Firebase ID token: {str(e)}")
            raise exceptions.AuthenticationFailed('Revoked Firebase ID token')
        except auth.CertificateFetchError as e:
            logger.error(f"Firebase certificate fetch error: {str(e)}")
            raise exceptions.AuthenticationFailed('Authentication service unavailable')
        except Exception as e:
            logger.error(f"Firebase authentication error: {str(e)}")
            raise exceptions.AuthenticationFailed('Authentication failed')
    
    def authenticate_header(self, request: Request) -> str:
        """
        Return authentication header for 401 responses.
        
        Args:
            request: Django REST framework request object
            
        Returns:
            Authentication header string
        """
        return 'Bearer'


class FirebaseUserService:
    """
    Service class for Firebase user management operations.
    
    Provides utilities for creating, updating, and managing
    Firebase users with custom claims.
    """
    
    @staticmethod
    def create_user(email: str, password: str, display_name: str = None) -> str:
        """
        Create a new Firebase user.
        
        Args:
            email: User email address
            password: User password
            display_name: Optional display name
            
        Returns:
            Firebase UID of created user
        """
        try:
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False
            )
            
            logger.info(f"Created Firebase user: {user_record.uid}")
            return user_record.uid
            
        except Exception as e:
            logger.error(f"Failed to create Firebase user: {str(e)}")
            raise Exception(f"User creation failed: {str(e)}")
    
    @staticmethod
    def get_user_by_uid(firebase_uid: str) -> dict:
        """
        Get Firebase user by UID.
        
        Args:
            firebase_uid: Firebase user UID
            
        Returns:
            User information dictionary
        """
        try:
            user_record = auth.get_user(firebase_uid)
            
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name,
                'disabled': user_record.disabled,
                'custom_claims': user_record.custom_claims or {},
                'creation_timestamp': user_record.user_metadata.creation_timestamp,
                'last_sign_in_timestamp': user_record.user_metadata.last_sign_in_timestamp,
            }
            
        except Exception as e:
            logger.error(f"Failed to get Firebase user {firebase_uid}: {str(e)}")
            return None
    
    @staticmethod
    def update_user_claims(firebase_uid: str, custom_claims: dict):
        """
        Update custom claims for a Firebase user.
        
        Args:
            firebase_uid: Firebase user UID
            custom_claims: Dictionary of custom claims to set
        """
        try:
            auth.set_custom_user_claims(firebase_uid, custom_claims)
            logger.info(f"Updated custom claims for user {firebase_uid}: {custom_claims}")
            
        except Exception as e:
            logger.error(f"Failed to update custom claims for user {firebase_uid}: {str(e)}")
            raise Exception(f"Claims update failed: {str(e)}")
    
    @staticmethod
    def set_admin_privileges(firebase_uid: str, is_admin: bool = True):
        """
        Set admin privileges for a Firebase user.
        
        Args:
            firebase_uid: Firebase user UID
            is_admin: Whether user should have admin privileges
        """
        custom_claims = {'admin': is_admin}
        FirebaseUserService.update_user_claims(firebase_uid, custom_claims)
    
    @staticmethod
    def disable_user(firebase_uid: str, disabled: bool = True):
        """
        Enable or disable a Firebase user.
        
        Args:
            firebase_uid: Firebase user UID
            disabled: Whether to disable the user
        """
        try:
            auth.update_user(firebase_uid, disabled=disabled)
            status = "disabled" if disabled else "enabled"
            logger.info(f"User {firebase_uid} {status}")
            
        except Exception as e:
            logger.error(f"Failed to update user status {firebase_uid}: {str(e)}")
            raise Exception(f"User status update failed: {str(e)}")
    
    @staticmethod
    def delete_user(firebase_uid: str):
        """
        Delete a Firebase user.
        
        Args:
            firebase_uid: Firebase user UID
        """
        try:
            auth.delete_user(firebase_uid)
            logger.info(f"Deleted Firebase user: {firebase_uid}")
            
        except Exception as e:
            logger.error(f"Failed to delete Firebase user {firebase_uid}: {str(e)}")
            raise Exception(f"User deletion failed: {str(e)}")
    
    @staticmethod
    def verify_id_token(id_token: str) -> dict:
        """
        Verify Firebase ID token and return claims.
        
        Args:
            id_token: Firebase ID token
            
        Returns:
            Token claims dictionary
        """
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
            
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise Exception(f"Invalid token: {str(e)}")


# Utility functions for easy access
def get_firebase_user(request: Request) -> Optional[FirebaseUser]:
    """
    Get Firebase user from request if authenticated.
    
    Args:
        request: Django REST framework request object
        
    Returns:
        FirebaseUser instance or None
    """
    if hasattr(request, 'user') and isinstance(request.user, FirebaseUser):
        return request.user
    return None


def require_firebase_auth(view_func):
    """
    Decorator to require Firebase authentication for view functions.
    
    Args:
        view_func: View function to decorate
        
    Returns:
        Decorated view function
    """
    def wrapper(request, *args, **kwargs):
        firebase_user = get_firebase_user(request)
        if not firebase_user:
            raise exceptions.AuthenticationFailed('Firebase authentication required')
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_admin_auth(view_func):
    """
    Decorator to require admin Firebase authentication for view functions.
    
    Args:
        view_func: View function to decorate
        
    Returns:
        Decorated view function
    """
    def wrapper(request, *args, **kwargs):
        firebase_user = get_firebase_user(request)
        if not firebase_user or not firebase_user.is_admin:
            raise exceptions.PermissionDenied('Admin privileges required')
        return view_func(request, *args, **kwargs)
    
    return wrapper