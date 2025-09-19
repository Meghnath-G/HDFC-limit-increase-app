"""
Model compatibility layer for transitioning from Oracle to Firebase.

Provides utilities and adapters to ease the migration from Django ORM
to Firebase models while maintaining code compatibility.
"""

from typing import Union, Type, Optional, Dict, Any
from django.conf import settings
import logging

# Import both model types
try:
    from apps.customers.models import Customer as OracleCustomer
    from apps.requests.models import LimitRequest as OracleLimitRequest
    ORACLE_MODELS_AVAILABLE = True
except ImportError:
    ORACLE_MODELS_AVAILABLE = False
    OracleCustomer = None
    OracleLimitRequest = None

from core.firebase_models import FirebaseCustomer, FirebaseLimitRequest

logger = logging.getLogger(__name__)


class ModelFactory:
    """
    Factory class for creating model instances based on backend configuration.
    
    Automatically chooses between Oracle and Firebase models based on
    the USE_FIREBASE_DB setting.
    """
    
    @staticmethod
    def get_customer_model() -> Union[Type[FirebaseCustomer], Type]:
        """
        Get the appropriate Customer model class.
        
        Returns:
            Customer model class (Firebase or Oracle)
        """
        if getattr(settings, 'USE_FIREBASE_DB', False):
            return FirebaseCustomer
        elif ORACLE_MODELS_AVAILABLE:
            return OracleCustomer
        else:
            logger.warning("Oracle models not available, falling back to Firebase")
            return FirebaseCustomer
    
    @staticmethod
    def get_limit_request_model() -> Union[Type[FirebaseLimitRequest], Type]:
        """
        Get the appropriate LimitRequest model class.
        
        Returns:
            LimitRequest model class (Firebase or Oracle)
        """
        if getattr(settings, 'USE_FIREBASE_DB', False):
            return FirebaseLimitRequest
        elif ORACLE_MODELS_AVAILABLE:
            return OracleLimitRequest
        else:
            logger.warning("Oracle models not available, falling back to Firebase")
            return FirebaseLimitRequest
    
    @staticmethod
    def create_customer(**kwargs) -> Union[FirebaseCustomer, Any]:
        """
        Create a new customer instance.
        
        Args:
            **kwargs: Customer field values
            
        Returns:
            Customer instance (Firebase or Oracle)
        """
        CustomerModel = ModelFactory.get_customer_model()
        
        if CustomerModel == FirebaseCustomer:
            customer = CustomerModel()
            for field, value in kwargs.items():
                if hasattr(customer, field):
                    setattr(customer, field, value)
            return customer
        else:
            # Oracle/Django ORM model
            return CustomerModel(**kwargs)
    
    @staticmethod
    def create_limit_request(**kwargs) -> Union[FirebaseLimitRequest, Any]:
        """
        Create a new limit request instance.
        
        Args:
            **kwargs: LimitRequest field values
            
        Returns:
            LimitRequest instance (Firebase or Oracle)
        """
        LimitRequestModel = ModelFactory.get_limit_request_model()
        
        if LimitRequestModel == FirebaseLimitRequest:
            limit_request = LimitRequestModel()
            for field, value in kwargs.items():
                if hasattr(limit_request, field):
                    setattr(limit_request, field, value)
            return limit_request
        else:
            # Oracle/Django ORM model
            return LimitRequestModel(**kwargs)


class ModelAdapter:
    """
    Adapter class to provide uniform interface for both Oracle and Firebase models.
    
    Translates method calls to work with both model types.
    """
    
    @staticmethod
    def get_customer_by_firebase_uid(firebase_uid: str) -> Optional[Union[FirebaseCustomer, Any]]:
        """
        Get customer by Firebase UID for both model types.
        
        Args:
            firebase_uid: Firebase authentication user ID
            
        Returns:
            Customer instance or None
        """
        CustomerModel = ModelFactory.get_customer_model()
        
        if CustomerModel == FirebaseCustomer:
            return CustomerModel.get_by_firebase_uid(firebase_uid)
        elif ORACLE_MODELS_AVAILABLE:
            try:
                return CustomerModel.objects.get(firebase_uid=firebase_uid, is_active=True)
            except CustomerModel.DoesNotExist:
                return None
        
        return None
    
    @staticmethod
    def get_customer_by_id(customer_id: str) -> Optional[Union[FirebaseCustomer, Any]]:
        """
        Get customer by ID for both model types.
        
        Args:
            customer_id: Customer ID or document ID
            
        Returns:
            Customer instance or None
        """
        CustomerModel = ModelFactory.get_customer_model()
        
        if CustomerModel == FirebaseCustomer:
            return CustomerModel.get_by_id(customer_id)
        elif ORACLE_MODELS_AVAILABLE:
            try:
                return CustomerModel.objects.get(id=customer_id, is_active=True)
            except CustomerModel.DoesNotExist:
                return None
        
        return None
    
    @staticmethod
    def get_all_customers(limit: Optional[int] = None) -> list:
        """
        Get all customers for both model types.
        
        Args:
            limit: Maximum number of customers to return
            
        Returns:
            List of customer instances
        """
        CustomerModel = ModelFactory.get_customer_model()
        
        if CustomerModel == FirebaseCustomer:
            return CustomerModel.get_all(limit=limit)
        elif ORACLE_MODELS_AVAILABLE:
            queryset = CustomerModel.objects.filter(is_active=True)
            if limit:
                queryset = queryset[:limit]
            return list(queryset)
        
        return []
    
    @staticmethod
    def get_limit_request_by_reference(reference_number: str) -> Optional[Union[FirebaseLimitRequest, Any]]:
        """
        Get limit request by reference number for both model types.
        
        Args:
            reference_number: Request reference number
            
        Returns:
            LimitRequest instance or None
        """
        LimitRequestModel = ModelFactory.get_limit_request_model()
        
        if LimitRequestModel == FirebaseLimitRequest:
            return LimitRequestModel.get_by_reference_number(reference_number)
        elif ORACLE_MODELS_AVAILABLE:
            try:
                return LimitRequestModel.objects.get(reference_number=reference_number)
            except LimitRequestModel.DoesNotExist:
                return None
        
        return None
    
    @staticmethod
    def get_customer_requests(customer: Union[FirebaseCustomer, Any]) -> list:
        """
        Get all requests for a customer for both model types.
        
        Args:
            customer: Customer instance
            
        Returns:
            List of LimitRequest instances
        """
        LimitRequestModel = ModelFactory.get_limit_request_model()
        
        if LimitRequestModel == FirebaseLimitRequest:
            if hasattr(customer, 'id'):
                customer_ref = f"customers/{customer.id}"
                return LimitRequestModel.get_by_customer_ref(customer_ref)
            return []
        elif ORACLE_MODELS_AVAILABLE:
            return list(LimitRequestModel.objects.filter(customer=customer))
        
        return []
    
    @staticmethod
    def get_pending_requests() -> list:
        """
        Get all pending requests for both model types.
        
        Returns:
            List of pending LimitRequest instances
        """
        LimitRequestModel = ModelFactory.get_limit_request_model()
        
        if LimitRequestModel == FirebaseLimitRequest:
            return LimitRequestModel.get_pending_requests()
        elif ORACLE_MODELS_AVAILABLE:
            return list(LimitRequestModel.objects.filter(status='PENDING'))
        
        return []


class DataMigrationHelper:
    """
    Helper class for migrating data between Oracle and Firebase models.
    """
    
    @staticmethod
    def oracle_customer_to_firebase_data(oracle_customer) -> Dict[str, Any]:
        """
        Convert Oracle customer to Firebase customer data.
        
        Args:
            oracle_customer: Oracle Customer model instance
            
        Returns:
            Dictionary of Firebase customer data
        """
        if not oracle_customer:
            return {}
        
        return {
            'firebase_uid': getattr(oracle_customer, 'firebase_uid', ''),
            'name': getattr(oracle_customer, 'name', ''),
            'email': getattr(oracle_customer, 'email', ''),
            'phone_number': getattr(oracle_customer, 'phone_number', ''),
            'date_of_birth': getattr(oracle_customer, 'date_of_birth', None),
            'customer_id': getattr(oracle_customer, 'customer_id', ''),
            'customer_segment': getattr(oracle_customer, 'customer_segment', 'STANDARD'),
            'kyc_status': getattr(oracle_customer, 'kyc_status', 'PENDING'),
            'risk_score': getattr(oracle_customer, 'risk_score', 0),
            'is_active': getattr(oracle_customer, 'is_active', True),
            'created_at': getattr(oracle_customer, 'created_at', None),
            'updated_at': getattr(oracle_customer, 'updated_at', None),
        }
    
    @staticmethod
    def oracle_request_to_firebase_data(oracle_request, customer_ref: str) -> Dict[str, Any]:
        """
        Convert Oracle limit request to Firebase limit request data.
        
        Args:
            oracle_request: Oracle LimitRequest model instance
            customer_ref: Firebase customer document reference
            
        Returns:
            Dictionary of Firebase limit request data
        """
        if not oracle_request:
            return {}
        
        return {
            'customer_ref': customer_ref,
            'reference_number': getattr(oracle_request, 'reference_number', ''),
            'request_type': getattr(oracle_request, 'request_type', 'limit_increase'),
            'current_limit': float(getattr(oracle_request, 'current_limit', 0)),
            'requested_limit': float(getattr(oracle_request, 'requested_limit', 0)),
            'reason': getattr(oracle_request, 'reason', ''),
            'income_proof': getattr(oracle_request, 'income_proof', None),
            'annual_income': float(getattr(oracle_request, 'annual_income', 0)),
            'employment_type': getattr(oracle_request, 'employment_type', 'salaried'),
            'status': getattr(oracle_request, 'status', 'PENDING'),
            'priority': getattr(oracle_request, 'priority', 'medium'),
            'created_at': getattr(oracle_request, 'created_at', None),
            'updated_at': getattr(oracle_request, 'updated_at', None),
        }
    
    @staticmethod
    def firebase_customer_to_oracle_data(firebase_customer: FirebaseCustomer) -> Dict[str, Any]:
        """
        Convert Firebase customer to Oracle customer data.
        
        Args:
            firebase_customer: Firebase Customer model instance
            
        Returns:
            Dictionary of Oracle customer data
        """
        return {
            'firebase_uid': firebase_customer.firebase_uid,
            'name': firebase_customer.name,
            'email': firebase_customer.email,
            'phone_number': firebase_customer.phone_number,
            'date_of_birth': firebase_customer.date_of_birth,
            'customer_id': firebase_customer.customer_id,
            'customer_segment': firebase_customer.customer_segment,
            'kyc_status': firebase_customer.kyc_status,
            'risk_score': firebase_customer.risk_score,
            'is_active': firebase_customer.is_active,
        }


# Convenience functions for easy model access
def get_customer_model():
    """Get the configured Customer model class."""
    return ModelFactory.get_customer_model()


def get_limit_request_model():
    """Get the configured LimitRequest model class."""
    return ModelFactory.get_limit_request_model()


def create_customer(**kwargs):
    """Create a new customer using the configured model."""
    return ModelFactory.create_customer(**kwargs)


def create_limit_request(**kwargs):
    """Create a new limit request using the configured model."""
    return ModelFactory.create_limit_request(**kwargs)


# Model adapter instance for easy access
adapter = ModelAdapter()


# Export commonly used functions
__all__ = [
    'ModelFactory',
    'ModelAdapter', 
    'DataMigrationHelper',
    'get_customer_model',
    'get_limit_request_model',
    'create_customer',
    'create_limit_request',
    'adapter'
]