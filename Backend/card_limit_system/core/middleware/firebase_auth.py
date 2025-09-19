"""
Firebase Authentication Middleware for Django.

Provides Firebase authentication middleware to automatically
authenticate users with Firebase ID tokens.
"""

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from rest_framework.request import Request
import logging

from core.authentication import FirebaseAuthentication, FirebaseUser

logger = logging.getLogger(__name__)


class FirebaseAuthMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate users using Firebase ID tokens.
    
    Automatically authenticates requests with valid Firebase tokens
    and sets request.user to a FirebaseUser instance.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.firebase_auth = FirebaseAuthentication()
    
    def process_request(self, request):
        """
        Process incoming request and authenticate with Firebase.
        
        Args:
            request: Django HttpRequest object
        """
        # Skip authentication for certain paths
        skip_paths = [
            '/admin/',
            '/api/docs/',
            '/api/redoc/',
            '/api/schema/',
            '/health/',
            '/static/',
            '/media/',
        ]
        
        # Check if path should skip authentication
        if any(request.path.startswith(path) for path in skip_paths):
            request.user = AnonymousUser()
            return None
        
        try:
            # Try to authenticate with Firebase
            auth_result = self.firebase_auth.authenticate(request)
            
            if auth_result:
                user, token = auth_result
                request.user = user
                request.firebase_token = token
                logger.debug(f"Authenticated user: {user.firebase_uid}")
            else:
                request.user = AnonymousUser()
                request.firebase_token = None
                
        except Exception as e:
            logger.warning(f"Firebase authentication failed: {str(e)}")
            request.user = AnonymousUser()
            request.firebase_token = None
        
        return None