"""
Core utility functions for the Card Limit Increase System.

This module provides encryption, validation, and other utility functions
used across the application with security focus.
"""

import base64
import hashlib
import secrets
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def standardize_phone_number(phone_number):
    """
    Standardize phone number to E.164 format for Twilio.
    
    Args:
        phone_number (str): Input phone number in various formats
        
    Returns:
        str: Standardized phone number in E.164 format
    """
    if not phone_number:
        return phone_number
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Handle Indian phone numbers
    if digits_only.startswith('91') and len(digits_only) == 12:
        # Already has country code
        return f"+{digits_only}"
    elif len(digits_only) == 10:
        # Add India country code
        return f"+91{digits_only}"
    elif digits_only.startswith('0') and len(digits_only) == 11:
        # Remove leading 0 and add country code
        return f"+91{digits_only[1:]}"
    else:
        # For other formats, assume it's complete
        if not digits_only.startswith('+'):
            return f"+{digits_only}"
        return digits_only


class EncryptionService:
    """
    Service for handling AES-256 encryption of PII data.
    
    Uses Fernet (AES 128 in CBC mode with HMAC for authentication)
    which provides secure encryption for sensitive data.
    """
    
    _cipher = None
    
    @classmethod
    def get_cipher(cls):
        """Get or create Fernet cipher instance."""
        if cls._cipher is None:
            encryption_key = settings.ENCRYPTION_KEY
            if not encryption_key:
                raise ValueError("ENCRYPTION_KEY not configured in settings")
            
            # Derive key from provided key material
            if len(encryption_key) != 32:  # Fernet requires 32-byte key
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'hdfc_card_limit_salt',  # Fixed salt for consistency
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(encryption_key))
            else:
                key = base64.urlsafe_b64encode(encryption_key)
            
            cls._cipher = Fernet(key)
        return cls._cipher
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        if not plaintext:
            return plaintext
        
        try:
            cipher = cls.get_cipher()
            encrypted_bytes = cipher.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.
        
        Args:
            ciphertext: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ciphertext
        
        try:
            cipher = cls.get_cipher()
            encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise


def encrypt_field(value: str) -> str:
    """
    Encrypt a field value for database storage.
    
    Args:
        value: Plain text value to encrypt
        
    Returns:
        Encrypted value safe for database storage
    """
    return EncryptionService.encrypt(value)


def decrypt_field(value: str) -> str:
    """
    Decrypt a field value from database.
    
    Args:
        value: Encrypted value from database
        
    Returns:
        Plain text value
    """
    return EncryptionService.decrypt(value)


def hash_otp(otp: str) -> str:
    """
    Hash OTP for secure storage.
    
    Uses SHA-256 with salt for one-way hashing.
    
    Args:
        otp: Plain text OTP
        
    Returns:
        Hashed OTP for storage
    """
    salt = b'hdfc_otp_salt_2025'
    return hashlib.sha256(salt + otp.encode('utf-8')).hexdigest()


def verify_otp_hash(otp: str, hashed_otp: str) -> bool:
    """
    Verify OTP against stored hash.
    
    Args:
        otp: Plain text OTP to verify
        hashed_otp: Stored hash to verify against
        
    Returns:
        True if OTP matches hash
    """
    return hash_otp(otp) == hashed_otp


def generate_otp(length: int = 6) -> str:
    """
    Generate secure random OTP.
    
    Args:
        length: Length of OTP (default 6)
        
    Returns:
        Random numeric OTP
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def generate_reference_number(prefix: str = "REQ") -> str:
    """
    Generate unique reference number for requests.
    
    Format: REQ-YYYYMMDD-XXXX
    
    Args:
        prefix: Prefix for reference number
        
    Returns:
        Unique reference number
    """
    from datetime import datetime
    
    date_part = datetime.now().strftime("%Y%m%d")
    
    # Generate 4-digit random number
    random_part = ''.join([str(secrets.randbelow(10)) for _ in range(4)])
    
    return f"{prefix}-{date_part}-{random_part}"


def mask_card_number(card_number: str) -> str:
    """
    Mask card number for display.
    
    Args:
        card_number: Full or partial card number
        
    Returns:
        Masked card number
    """
    if not card_number:
        return "**** **** **** ****"
    
    if len(card_number) >= 4:
        return f"**** **** **** {card_number[-4:]}"
    
    return "**** **** **** ****"


def mask_phone_number(phone: str) -> str:
    """
    Mask phone number for display.
    
    Args:
        phone: Full phone number
        
    Returns:
        Masked phone number
    """
    if not phone or len(phone) < 4:
        return "+91****"
    
    if phone.startswith('+91'):
        return f"+91****{phone[-4:]}"
    
    return f"****{phone[-4:]}"


def mask_email(email: str) -> str:
    """
    Mask email address for display.
    
    Args:
        email: Full email address
        
    Returns:
        Masked email address
    """
    if not email or '@' not in email:
        return "***@***.com"
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        return f"***@{domain}"
    
    return f"{local[:2]}***@{domain}"


def validate_phone_format(phone: str) -> bool:
    """
    Validate Indian phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid format
    """
    import re
    pattern = r'^\+91[6-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_email_format(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_client_ip(request) -> str:
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
        
    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request) -> str:
    """
    Get user agent from request.
    
    Args:
        request: Django request object
        
    Returns:
        User agent string
    """
    return request.META.get('HTTP_USER_AGENT', '')


def rate_limit_key(identifier: str, action: str) -> str:
    """
    Generate rate limiting cache key.
    
    Args:
        identifier: User identifier (IP, user ID, etc.)
        action: Action being rate limited
        
    Returns:
        Cache key for rate limiting
    """
    return f"rate_limit:{action}:{identifier}"


def is_rate_limited(identifier: str, action: str, limit: int, window: int) -> bool:
    """
    Check if action is rate limited.
    
    Args:
        identifier: User identifier
        action: Action being checked
        limit: Maximum requests allowed
        window: Time window in seconds
        
    Returns:
        True if rate limited
    """
    key = rate_limit_key(identifier, action)
    current_count = cache.get(key, 0)
    
    if current_count >= limit:
        return True
    
    # Increment counter
    cache.set(key, current_count + 1, window)
    return False


def log_security_event(event_type: str, user_id: str = None, ip_address: str = None, 
                      details: dict = None) -> None:
    """
    Log security-related events for audit trail.
    
    Args:
        event_type: Type of security event
        user_id: User identifier (optional)
        ip_address: Client IP address (optional)
        details: Additional event details (optional)
    """
    from datetime import datetime
    
    event_data = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip_address,
        'details': details or {}
    }
    
    logger.info(f"SECURITY_EVENT: {event_data}")


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        value: Input value to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized input value
    """
    if not value:
        return ""
    
    # Truncate to max length
    value = value[:max_length]
    
    # Remove null bytes and control characters
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
    
    return value.strip()


class AuditLogger:
    """
    Utility class for audit logging with standardized format.
    """
    
    @staticmethod
    def log_customer_action(customer_id: str, action: str, ip_address: str = None,
                           user_agent: str = None, details: dict = None) -> None:
        """Log customer actions for audit trail."""
        log_security_event(
            event_type=f"customer_{action}",
            user_id=customer_id,
            ip_address=ip_address,
            details={
                'user_agent': user_agent,
                **(details or {})
            }
        )
    
    @staticmethod
    def log_api_access(endpoint: str, method: str, customer_id: str = None,
                      ip_address: str = None, status_code: int = None) -> None:
        """Log API access for monitoring."""
        log_security_event(
            event_type="api_access",
            user_id=customer_id,
            ip_address=ip_address,
            details={
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code
            }
        )
    
    @staticmethod
    def log_authentication_attempt(firebase_uid: str = None, success: bool = True,
                                 ip_address: str = None, error: str = None) -> None:
        """Log authentication attempts."""
        log_security_event(
            event_type="authentication_attempt",
            user_id=firebase_uid,
            ip_address=ip_address,
            details={
                'success': success,
                'error': error
            }
        )