"""
Firebase Schema Mapping for HDFC Card Limit System

This module defines the schema mapping from Oracle tables to Firebase collections
and provides utilities for data transformation and validation.

Oracle Tables → Firebase Collections Mapping:
- customers → customers
- card_details → card_details  
- limit_requests → limit_requests
- request_audit_log → audit_log
- notifications → notifications
- otps → otps
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import uuid


@dataclass
class CustomerSchema:
    """Customer document schema for Firebase."""
    firebase_uid: str
    name: str
    email: str
    phone_number: str
    customer_id: str
    date_of_birth: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    is_active: bool = True
    profile: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
        if not self.profile:
            self.profile = {
                "address": {},
                "kyc_status": "pending",
                "income_range": "not_specified"
            }
    
    @classmethod
    def from_oracle_row(cls, oracle_data: Dict[str, Any]) -> 'CustomerSchema':
        """Convert Oracle customer row to Firebase document schema."""
        return cls(
            firebase_uid=oracle_data.get('firebase_uid', ''),
            name=oracle_data.get('name', ''),
            email=oracle_data.get('email', ''),
            phone_number=oracle_data.get('phone_number', ''),
            customer_id=oracle_data.get('customer_id', ''),
            date_of_birth=oracle_data.get('date_of_birth').isoformat() if oracle_data.get('date_of_birth') else None,
            created_at=oracle_data.get('created_at').isoformat() if oracle_data.get('created_at') else None,
            updated_at=oracle_data.get('updated_at').isoformat() if oracle_data.get('updated_at') else None,
            is_active=bool(oracle_data.get('is_active', True))
        )
    
    def to_firestore_document(self) -> Dict[str, Any]:
        """Convert to Firestore document format."""
        return asdict(self)


@dataclass
class CardDetailsSchema:
    """Card details document schema for Firebase."""
    customer_id: str
    customer_ref: str  # Reference to customer document
    card_number_hash: str
    card_type: str  # 'CREDIT' or 'DEBIT'
    current_limit: float
    available_limit: float
    card_status: str  # 'ACTIVE', 'BLOCKED', 'EXPIRED'
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
    
    @classmethod
    def from_oracle_row(cls, oracle_data: Dict[str, Any], customer_ref: str) -> 'CardDetailsSchema':
        """Convert Oracle card_details row to Firebase document schema."""
        return cls(
            customer_id=oracle_data.get('customer_id', ''),
            customer_ref=customer_ref,
            card_number_hash=oracle_data.get('card_number_hash', ''),
            card_type=oracle_data.get('card_type', 'CREDIT'),
            current_limit=float(oracle_data.get('current_limit', 0)),
            available_limit=float(oracle_data.get('available_limit', 0)),
            card_status=oracle_data.get('card_status', 'ACTIVE'),
            issue_date=oracle_data.get('issue_date').isoformat() if oracle_data.get('issue_date') else None,
            expiry_date=oracle_data.get('expiry_date').isoformat() if oracle_data.get('expiry_date') else None,
            created_at=oracle_data.get('created_at').isoformat() if oracle_data.get('created_at') else None,
            updated_at=oracle_data.get('updated_at').isoformat() if oracle_data.get('updated_at') else None
        )
    
    def to_firestore_document(self) -> Dict[str, Any]:
        """Convert to Firestore document format."""
        return asdict(self)


@dataclass
class LimitRequestSchema:
    """Limit request document schema for Firebase."""
    customer_id: str
    customer_ref: str  # Reference to customer document
    request_type: str  # 'limit_increase', 'limit_decrease'
    current_limit: float
    requested_limit: float
    reason: str
    income_proof: Optional[str] = None
    status: str = 'pending'  # 'pending', 'approved', 'rejected', 'processing'
    request_date: str = None
    last_updated: str = None
    processed_by: Optional[str] = None
    approval_notes: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.request_date:
            self.request_date = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
        if not self.risk_assessment:
            self.risk_assessment = {
                "credit_score": None,
                "debt_ratio": None,
                "risk_level": "pending_assessment"
            }
    
    @classmethod
    def from_oracle_row(cls, oracle_data: Dict[str, Any], customer_ref: str) -> 'LimitRequestSchema':
        """Convert Oracle limit_requests row to Firebase document schema."""
        return cls(
            customer_id=oracle_data.get('customer_id', ''),
            customer_ref=customer_ref,
            request_type=oracle_data.get('request_type', 'limit_increase'),
            current_limit=float(oracle_data.get('current_limit', 0)),
            requested_limit=float(oracle_data.get('requested_limit', 0)),
            reason=oracle_data.get('reason', ''),
            income_proof=oracle_data.get('income_proof'),
            status=oracle_data.get('status', 'pending'),
            request_date=oracle_data.get('request_date').isoformat() if oracle_data.get('request_date') else None,
            last_updated=oracle_data.get('last_updated').isoformat() if oracle_data.get('last_updated') else None,
            processed_by=oracle_data.get('processed_by'),
            approval_notes=oracle_data.get('approval_notes')
        )
    
    def to_firestore_document(self) -> Dict[str, Any]:
        """Convert to Firestore document format."""
        return asdict(self)


@dataclass
class NotificationSchema:
    """Notification document schema for Firebase."""
    customer_id: str
    customer_ref: str  # Reference to customer document
    title: str
    message: str
    notification_type: str  # 'limit_approval', 'limit_rejection', 'otp', 'general'
    status: str = 'pending'  # 'pending', 'sent', 'delivered', 'failed'
    sent_at: Optional[str] = None
    read_at: Optional[str] = None
    fcm_token: Optional[str] = None
    delivery_status: str = 'pending'
    created_at: str = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    @classmethod
    def from_oracle_row(cls, oracle_data: Dict[str, Any], customer_ref: str) -> 'NotificationSchema':
        """Convert Oracle notifications row to Firebase document schema."""
        return cls(
            customer_id=oracle_data.get('customer_id', ''),
            customer_ref=customer_ref,
            title=oracle_data.get('title', ''),
            message=oracle_data.get('message', ''),
            notification_type=oracle_data.get('notification_type', 'general'),
            status=oracle_data.get('status', 'pending'),
            sent_at=oracle_data.get('sent_at').isoformat() if oracle_data.get('sent_at') else None,
            read_at=oracle_data.get('read_at').isoformat() if oracle_data.get('read_at') else None,
            fcm_token=oracle_data.get('fcm_token'),
            delivery_status=oracle_data.get('delivery_status', 'pending'),
            created_at=oracle_data.get('created_at').isoformat() if oracle_data.get('created_at') else None
        )
    
    def to_firestore_document(self) -> Dict[str, Any]:
        """Convert to Firestore document format."""
        return asdict(self)


@dataclass
class AuditLogSchema:
    """Audit log document schema for Firebase."""
    request_id: str
    request_ref: str  # Reference to limit_request document
    action: str  # 'status_change', 'created', 'updated', 'viewed'
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    changed_by: str = ''
    changed_at: str = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.changed_at:
            self.changed_at = datetime.now().isoformat()
    
    @classmethod
    def from_oracle_row(cls, oracle_data: Dict[str, Any], request_ref: str) -> 'AuditLogSchema':
        """Convert Oracle request_audit_log row to Firebase document schema."""
        return cls(
            request_id=oracle_data.get('request_id', ''),
            request_ref=request_ref,
            action=oracle_data.get('action', ''),
            old_status=oracle_data.get('old_status'),
            new_status=oracle_data.get('new_status'),
            changed_by=oracle_data.get('changed_by', ''),
            changed_at=oracle_data.get('changed_at').isoformat() if oracle_data.get('changed_at') else None,
            reason=oracle_data.get('reason'),
            ip_address=oracle_data.get('ip_address')
        )
    
    def to_firestore_document(self) -> Dict[str, Any]:
        """Convert to Firestore document format."""
        return asdict(self)


@dataclass
class OTPSchema:
    """OTP document schema for Firebase."""
    phone_number: str
    otp_code: str
    purpose: str  # 'login_verification', 'transaction_verification', 'password_reset'
    created_at: str = None
    expires_at: str = None
    verified_at: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    is_used: bool = False
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.expires_at:
            # OTP expires in 5 minutes
            expire_time = datetime.now().timestamp() + (5 * 60)
            self.expires_at = datetime.fromtimestamp(expire_time).isoformat()
    
    @classmethod
    def from_oracle_row(cls, oracle_data: Dict[str, Any]) -> 'OTPSchema':
        """Convert Oracle otps row to Firebase document schema."""
        return cls(
            phone_number=oracle_data.get('phone_number', ''),
            otp_code=oracle_data.get('otp_code', ''),
            purpose=oracle_data.get('purpose', 'login_verification'),
            created_at=oracle_data.get('created_at').isoformat() if oracle_data.get('created_at') else None,
            expires_at=oracle_data.get('expires_at').isoformat() if oracle_data.get('expires_at') else None,
            verified_at=oracle_data.get('verified_at').isoformat() if oracle_data.get('verified_at') else None,
            attempts=int(oracle_data.get('attempts', 0)),
            max_attempts=int(oracle_data.get('max_attempts', 3)),
            is_used=bool(oracle_data.get('is_used', False))
        )
    
    def to_firestore_document(self) -> Dict[str, Any]:
        """Convert to Firestore document format."""
        return asdict(self)


class FirebaseSchemaValidator:
    """Utility class for validating Firebase document schemas."""
    
    @staticmethod
    def validate_customer(data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate customer document schema."""
        errors = []
        required_fields = ['firebase_uid', 'name', 'email', 'phone_number', 'customer_id']
        
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        if data.get('email') and '@' not in data['email']:
            errors.append("Invalid email format")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_limit_request(data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate limit request document schema."""
        errors = []
        required_fields = ['customer_id', 'customer_ref', 'request_type', 'current_limit', 'requested_limit', 'reason']
        
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        if data.get('requested_limit', 0) <= 0:
            errors.append("Requested limit must be greater than 0")
        
        if data.get('request_type') not in ['limit_increase', 'limit_decrease']:
            errors.append("Invalid request type")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_notification(data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate notification document schema."""
        errors = []
        required_fields = ['customer_id', 'customer_ref', 'title', 'message', 'notification_type']
        
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        valid_types = ['limit_approval', 'limit_rejection', 'otp', 'general']
        if data.get('notification_type') not in valid_types:
            errors.append(f"Invalid notification type. Must be one of: {valid_types}")
        
        return len(errors) == 0, errors


# Collection name constants
COLLECTIONS = {
    'CUSTOMERS': 'customers',
    'CARD_DETAILS': 'card_details',
    'LIMIT_REQUESTS': 'limit_requests',
    'NOTIFICATIONS': 'notifications',
    'AUDIT_LOG': 'audit_log',
    'OTPS': 'otps'
}

# Oracle to Firebase table mapping
ORACLE_TO_FIREBASE_MAPPING = {
    'customers': COLLECTIONS['CUSTOMERS'],
    'card_details': COLLECTIONS['CARD_DETAILS'],
    'limit_requests': COLLECTIONS['LIMIT_REQUESTS'],
    'notifications': COLLECTIONS['NOTIFICATIONS'],
    'request_audit_log': COLLECTIONS['AUDIT_LOG'],
    'otps': COLLECTIONS['OTPS']
}

# Schema classes mapping
SCHEMA_CLASSES = {
    COLLECTIONS['CUSTOMERS']: CustomerSchema,
    COLLECTIONS['CARD_DETAILS']: CardDetailsSchema,
    COLLECTIONS['LIMIT_REQUESTS']: LimitRequestSchema,
    COLLECTIONS['NOTIFICATIONS']: NotificationSchema,
    COLLECTIONS['AUDIT_LOG']: AuditLogSchema,
    COLLECTIONS['OTPS']: OTPSchema
}

# Validators mapping
VALIDATORS = {
    COLLECTIONS['CUSTOMERS']: FirebaseSchemaValidator.validate_customer,
    COLLECTIONS['LIMIT_REQUESTS']: FirebaseSchemaValidator.validate_limit_request,
    COLLECTIONS['NOTIFICATIONS']: FirebaseSchemaValidator.validate_notification
}


def get_schema_class(collection_name: str):
    """Get schema class for a collection."""
    return SCHEMA_CLASSES.get(collection_name)


def validate_document(collection_name: str, data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate document data for a collection."""
    validator = VALIDATORS.get(collection_name)
    if validator:
        return validator(data)
    return True, []  # No validation available, assume valid


def generate_document_id() -> str:
    """Generate a unique document ID."""
    return str(uuid.uuid4())


__all__ = [
    'CustomerSchema',
    'CardDetailsSchema', 
    'LimitRequestSchema',
    'NotificationSchema',
    'AuditLogSchema',
    'OTPSchema',
    'FirebaseSchemaValidator',
    'COLLECTIONS',
    'ORACLE_TO_FIREBASE_MAPPING',
    'SCHEMA_CLASSES',
    'get_schema_class',
    'validate_document',
    'generate_document_id'
]