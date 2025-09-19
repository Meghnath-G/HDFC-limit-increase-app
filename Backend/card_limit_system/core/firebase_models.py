"""
Firebase-compatible Django model adapters for Customer management.

Provides Django-like model interface for Firebase Firestore operations
while maintaining compatibility with existing Django patterns.
"""

import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator
import logging

# Firebase imports
from core.firebase_config import FirebaseService
from core.firebase_schema import CustomerSchema, CardDetailsSchema, validate_document

logger = logging.getLogger(__name__)


class FirebaseModelMixin:
    """
    Mixin providing Firebase model functionality.
    
    Provides Django-like interface for Firebase Firestore operations.
    """
    
    def __init__(self):
        self.firebase_service = FirebaseService()
        self._collection_name = None
        self._doc_id = None
        self._data = {}
    
    @property
    def collection_name(self) -> str:
        """Get the Firestore collection name."""
        if not self._collection_name:
            raise NotImplementedError("Subclasses must define collection_name")
        return self._collection_name
    
    @property
    def id(self) -> Optional[str]:
        """Get the document ID."""
        return self._doc_id
    
    @id.setter
    def id(self, value: str):
        """Set the document ID."""
        self._doc_id = value
    
    def save(self) -> str:
        """
        Save the model to Firebase Firestore.
        
        Returns:
            str: Document ID of the saved document
        """
        try:
            # Validate data before saving
            is_valid, errors = validate_document(self.collection_name, self._data)
            if not is_valid:
                raise ValidationError(f"Invalid document data: {errors}")
            
            # Update timestamp
            self._data['updated_at'] = datetime.now()
            
            if self._doc_id:
                # Update existing document
                self.firebase_service.update_document(
                    self.collection_name, 
                    self._doc_id, 
                    self._data
                )
                logger.info(f"Updated {self.collection_name} document: {self._doc_id}")
                return self._doc_id
            else:
                # Create new document
                self._data['created_at'] = datetime.now()
                doc_id = self.firebase_service.create_document(
                    self.collection_name, 
                    self._data
                )
                self._doc_id = doc_id
                logger.info(f"Created {self.collection_name} document: {doc_id}")
                return doc_id
                
        except Exception as e:
            logger.error(f"Error saving {self.collection_name}: {str(e)}")
            raise ValidationError(f"Failed to save: {str(e)}")
    
    def delete(self):
        """
        Soft delete the model (set is_active to False).
        """
        if not self._doc_id:
            raise ValueError("Cannot delete unsaved model")
        
        try:
            self._data['is_active'] = False
            self._data['updated_at'] = datetime.now()
            
            self.firebase_service.update_document(
                self.collection_name,
                self._doc_id,
                self._data
            )
            
            logger.info(f"Soft deleted {self.collection_name} document: {self._doc_id}")
            
        except Exception as e:
            logger.error(f"Error deleting {self.collection_name}: {str(e)}")
            raise ValidationError(f"Failed to delete: {str(e)}")
    
    @classmethod
    def get_by_id(cls, doc_id: str):
        """
        Get model instance by document ID.
        
        Args:
            doc_id: Firestore document ID
            
        Returns:
            Model instance or None if not found
        """
        instance = cls()
        
        try:
            document_data = instance.firebase_service.get_document(
                instance.collection_name, 
                doc_id
            )
            
            if document_data:
                instance._doc_id = doc_id
                instance._data = document_data
                instance._populate_fields()
                return instance
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting {instance.collection_name} by ID {doc_id}: {str(e)}")
            return None
    
    @classmethod
    def get_all(cls, limit: Optional[int] = None) -> List['FirebaseModelMixin']:
        """
        Get all documents from the collection.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of model instances
        """
        instance = cls()
        instances = []
        
        try:
            documents = instance.firebase_service.get_collection(
                instance.collection_name,
                limit=limit
            )
            
            for doc_id, doc_data in documents.items():
                model_instance = cls()
                model_instance._doc_id = doc_id
                model_instance._data = doc_data
                model_instance._populate_fields()
                instances.append(model_instance)
            
            return instances
            
        except Exception as e:
            logger.error(f"Error getting all {instance.collection_name}: {str(e)}")
            return []
    
    @classmethod
    def filter(cls, field_path: str, op_string: str, value: Any) -> List['FirebaseModelMixin']:
        """
        Filter documents by field value.
        
        Args:
            field_path: Field to filter on
            op_string: Comparison operator ('==', '!=', '<', '<=', '>', '>=')
            value: Value to compare against
            
        Returns:
            List of matching model instances
        """
        instance = cls()
        instances = []
        
        try:
            documents = instance.firebase_service.query_collection(
                instance.collection_name,
                field_path=field_path,
                op_string=op_string,
                value=value
            )
            
            for doc_data in documents:
                model_instance = cls()
                model_instance._doc_id = doc_data.get('id')
                model_instance._data = doc_data
                model_instance._populate_fields()
                instances.append(model_instance)
            
            return instances
            
        except Exception as e:
            logger.error(f"Error filtering {instance.collection_name}: {str(e)}")
            return []
    
    def _populate_fields(self):
        """Populate model fields from Firestore data. Override in subclasses."""
        pass


class FirebaseCustomer(FirebaseModelMixin):
    """
    Firebase-compatible Customer model.
    
    Provides Django-like interface for customer operations
    using Firebase Firestore as the backend.
    """
    
    def __init__(self):
        super().__init__()
        self._collection_name = 'customers'
        
        # Customer fields
        self.firebase_uid = None
        self.name = None
        self.email = None
        self.phone_number = None
        self.date_of_birth = None
        self.customer_id = None
        self.customer_segment = 'STANDARD'
        self.kyc_status = 'PENDING'
        self.risk_score = 0
        self.is_active = True
        self.created_at = None
        self.updated_at = None
        
        # Additional fields
        self.kyc_verified_at = None
        self.kyc_updated_at = None
        self.last_login = None
        self.notes = ''
    
    def _populate_fields(self):
        """Populate customer fields from Firestore data."""
        if not self._data:
            return
        
        self.firebase_uid = self._data.get('firebase_uid')
        self.name = self._data.get('name')
        self.email = self._data.get('email')
        self.phone_number = self._data.get('phone_number')
        self.date_of_birth = self._data.get('date_of_birth')
        self.customer_id = self._data.get('customer_id')
        self.customer_segment = self._data.get('customer_segment', 'STANDARD')
        self.kyc_status = self._data.get('kyc_status', 'PENDING')
        self.risk_score = self._data.get('risk_score', 0)
        self.is_active = self._data.get('is_active', True)
        self.created_at = self._data.get('created_at')
        self.updated_at = self._data.get('updated_at')
        self.kyc_verified_at = self._data.get('kyc_verified_at')
        self.kyc_updated_at = self._data.get('kyc_updated_at')
        self.last_login = self._data.get('last_login')
        self.notes = self._data.get('notes', '')
    
    def _prepare_data(self):
        """Prepare customer data for Firestore."""
        self._data = {
            'firebase_uid': self.firebase_uid,
            'name': self.name,
            'email': self.email,
            'phone_number': self.phone_number,
            'date_of_birth': self.date_of_birth,
            'customer_id': self.customer_id,
            'customer_segment': self.customer_segment,
            'kyc_status': self.kyc_status,
            'risk_score': self.risk_score,
            'is_active': self.is_active,
            'kyc_verified_at': self.kyc_verified_at,
            'kyc_updated_at': self.kyc_updated_at,
            'last_login': self.last_login,
            'notes': self.notes
        }
        
        # Remove None values
        self._data = {k: v for k, v in self._data.items() if v is not None}
    
    def save(self) -> str:
        """Save customer to Firebase with validation."""
        # Validate required fields
        if not self.firebase_uid:
            raise ValidationError("firebase_uid is required")
        if not self.name:
            raise ValidationError("name is required")
        if not self.email:
            raise ValidationError("email is required")
        if not self.phone_number:
            raise ValidationError("phone_number is required")
        
        # Validate email format
        email_validator = EmailValidator()
        try:
            email_validator(self.email)
        except ValidationError:
            raise ValidationError("Invalid email format")
        
        # Validate phone number format (basic)
        phone_regex = RegexValidator(
            regex=r'^\+91[6-9]\d{9}$',
            message="Phone number must be in format +91xxxxxxxxxx"
        )
        try:
            phone_regex(self.phone_number)
        except ValidationError:
            raise ValidationError("Invalid phone number format")
        
        # Prepare data for saving
        self._prepare_data()
        
        # Call parent save method
        return super().save()
    
    @classmethod
    def get_by_firebase_uid(cls, firebase_uid: str) -> Optional['FirebaseCustomer']:
        """
        Get customer by Firebase UID.
        
        Args:
            firebase_uid: Firebase authentication user ID
            
        Returns:
            FirebaseCustomer instance or None
        """
        customers = cls.filter('firebase_uid', '==', firebase_uid)
        return customers[0] if customers else None
    
    @classmethod
    def get_by_customer_id(cls, customer_id: str) -> Optional['FirebaseCustomer']:
        """
        Get customer by customer ID.
        
        Args:
            customer_id: HDFC customer ID
            
        Returns:
            FirebaseCustomer instance or None
        """
        customers = cls.filter('customer_id', '==', customer_id)
        return customers[0] if customers else None
    
    @classmethod
    def get_active_customers(cls) -> List['FirebaseCustomer']:
        """Get all active customers."""
        return cls.filter('is_active', '==', True)
    
    @classmethod
    def get_kyc_verified_customers(cls) -> List['FirebaseCustomer']:
        """Get all KYC verified customers."""
        return cls.filter('kyc_status', '==', 'VERIFIED')
    
    def update_kyc_status(self, status: str, verified_by: str = None):
        """
        Update customer KYC status.
        
        Args:
            status: New KYC status ('PENDING', 'VERIFIED', 'REJECTED')
            verified_by: User who verified the KYC (optional)
        """
        if status not in ['PENDING', 'VERIFIED', 'REJECTED']:
            raise ValidationError("Invalid KYC status")
        
        self.kyc_status = status
        self.kyc_updated_at = datetime.now()
        
        if status == 'VERIFIED':
            self.kyc_verified_at = datetime.now()
        
        if verified_by:
            self.notes += f"\nKYC {status} by {verified_by} on {datetime.now()}"
        
        return self.save()
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.now()
        return self.save()
    
    def __str__(self):
        return f"Customer({self.customer_id}: {self.name})"
    
    def __repr__(self):
        return f"<FirebaseCustomer: {self.customer_id} - {self.name}>"


class FirebaseLimitRequest(FirebaseModelMixin):
    """
    Firebase-compatible Limit Request model.
    
    Provides Django-like interface for limit request operations
    using Firebase Firestore as the backend.
    """
    
    def __init__(self):
        super().__init__()
        self._collection_name = 'limit_requests'
        
        # Limit request fields
        self.customer_ref = None  # Reference to customer document
        self.reference_number = None
        self.request_type = 'limit_increase'
        self.current_limit = 0.0
        self.requested_limit = 0.0
        self.reason = ''
        self.income_proof = None
        self.annual_income = 0.0
        self.employment_type = 'salaried'
        self.status = 'PENDING'
        self.priority = 'medium'
        self.requires_manual_review = True
        self.workflow_stage = 'initial_review'
        
        # Approval/Rejection fields
        self.approved_at = None
        self.approved_by = None
        self.approval_comments = ''
        self.approved_limit = None
        self.rejected_at = None
        self.rejected_by = None
        self.rejection_reason = ''
        self.rejection_comments = ''
        
        # Timestamps
        self.created_at = None
        self.updated_at = None
        self.submitted_by = None
    
    def _populate_fields(self):
        """Populate limit request fields from Firestore data."""
        if not self._data:
            return
        
        self.customer_ref = self._data.get('customer_ref')
        self.reference_number = self._data.get('reference_number')
        self.request_type = self._data.get('request_type', 'limit_increase')
        self.current_limit = self._data.get('current_limit', 0.0)
        self.requested_limit = self._data.get('requested_limit', 0.0)
        self.reason = self._data.get('reason', '')
        self.income_proof = self._data.get('income_proof')
        self.annual_income = self._data.get('annual_income', 0.0)
        self.employment_type = self._data.get('employment_type', 'salaried')
        self.status = self._data.get('status', 'PENDING')
        self.priority = self._data.get('priority', 'medium')
        self.requires_manual_review = self._data.get('requires_manual_review', True)
        self.workflow_stage = self._data.get('workflow_stage', 'initial_review')
        
        # Approval/Rejection fields
        self.approved_at = self._data.get('approved_at')
        self.approved_by = self._data.get('approved_by')
        self.approval_comments = self._data.get('approval_comments', '')
        self.approved_limit = self._data.get('approved_limit')
        self.rejected_at = self._data.get('rejected_at')
        self.rejected_by = self._data.get('rejected_by')
        self.rejection_reason = self._data.get('rejection_reason', '')
        self.rejection_comments = self._data.get('rejection_comments', '')
        
        # Timestamps
        self.created_at = self._data.get('created_at')
        self.updated_at = self._data.get('updated_at')
        self.submitted_by = self._data.get('submitted_by')
    
    def _prepare_data(self):
        """Prepare limit request data for Firestore."""
        self._data = {
            'customer_ref': self.customer_ref,
            'reference_number': self.reference_number,
            'request_type': self.request_type,
            'current_limit': self.current_limit,
            'requested_limit': self.requested_limit,
            'reason': self.reason,
            'income_proof': self.income_proof,
            'annual_income': self.annual_income,
            'employment_type': self.employment_type,
            'status': self.status,
            'priority': self.priority,
            'requires_manual_review': self.requires_manual_review,
            'workflow_stage': self.workflow_stage,
            'approved_at': self.approved_at,
            'approved_by': self.approved_by,
            'approval_comments': self.approval_comments,
            'approved_limit': self.approved_limit,
            'rejected_at': self.rejected_at,
            'rejected_by': self.rejected_by,
            'rejection_reason': self.rejection_reason,
            'rejection_comments': self.rejection_comments,
            'submitted_by': self.submitted_by
        }
        
        # Remove None values
        self._data = {k: v for k, v in self._data.items() if v is not None}
    
    def save(self) -> str:
        """Save limit request to Firebase with validation."""
        # Validate required fields
        if not self.customer_ref:
            raise ValidationError("customer_ref is required")
        if not self.reference_number:
            raise ValidationError("reference_number is required")
        if self.requested_limit <= 0:
            raise ValidationError("requested_limit must be greater than 0")
        
        # Prepare data for saving
        self._prepare_data()
        
        # Call parent save method
        return super().save()
    
    @classmethod
    def get_by_reference_number(cls, reference_number: str) -> Optional['FirebaseLimitRequest']:
        """
        Get limit request by reference number.
        
        Args:
            reference_number: Request reference number
            
        Returns:
            FirebaseLimitRequest instance or None
        """
        requests = cls.filter('reference_number', '==', reference_number)
        return requests[0] if requests else None
    
    @classmethod
    def get_by_customer_ref(cls, customer_ref: str) -> List['FirebaseLimitRequest']:
        """
        Get all limit requests for a customer.
        
        Args:
            customer_ref: Customer document reference
            
        Returns:
            List of FirebaseLimitRequest instances
        """
        return cls.filter('customer_ref', '==', customer_ref)
    
    @classmethod
    def get_pending_requests(cls) -> List['FirebaseLimitRequest']:
        """Get all pending limit requests."""
        return cls.filter('status', '==', 'PENDING')
    
    @classmethod
    def get_approved_requests(cls) -> List['FirebaseLimitRequest']:
        """Get all approved limit requests."""
        return cls.filter('status', '==', 'APPROVED')
    
    def approve(self, approved_by: str, approved_limit: Optional[float] = None, comments: str = ''):
        """
        Approve the limit request.
        
        Args:
            approved_by: User who approved the request
            approved_limit: Approved limit amount (defaults to requested_limit)
            comments: Approval comments
        """
        if self.status not in ['PENDING', 'UNDER_REVIEW']:
            raise ValidationError("Request cannot be approved in current status")
        
        self.status = 'APPROVED'
        self.approved_at = datetime.now()
        self.approved_by = approved_by
        self.approved_limit = approved_limit or self.requested_limit
        self.approval_comments = comments
        self.workflow_stage = 'approved'
        
        return self.save()
    
    def reject(self, rejected_by: str, rejection_reason: str, comments: str = ''):
        """
        Reject the limit request.
        
        Args:
            rejected_by: User who rejected the request
            rejection_reason: Reason for rejection
            comments: Additional comments
        """
        if self.status not in ['PENDING', 'UNDER_REVIEW']:
            raise ValidationError("Request cannot be rejected in current status")
        
        if not rejection_reason:
            raise ValidationError("Rejection reason is required")
        
        self.status = 'REJECTED'
        self.rejected_at = datetime.now()
        self.rejected_by = rejected_by
        self.rejection_reason = rejection_reason
        self.rejection_comments = comments
        self.workflow_stage = 'rejected'
        
        return self.save()
    
    def __str__(self):
        return f"LimitRequest({self.reference_number}: {self.status})"
    
    def __repr__(self):
        return f"<FirebaseLimitRequest: {self.reference_number} - {self.status}>"


# Model registry for easy access
FIREBASE_MODELS = {
    'Customer': FirebaseCustomer,
    'LimitRequest': FirebaseLimitRequest,
}


def get_firebase_model(model_name: str):
    """Get Firebase model class by name."""
    return FIREBASE_MODELS.get(model_name)