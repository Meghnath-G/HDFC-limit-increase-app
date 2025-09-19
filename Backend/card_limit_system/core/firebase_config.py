"""
Firebase Configuration Module for HDFC Card Limit System

This module initializes Firebase Admin SDK and provides utilities for
Firestore database operations, authentication, and cloud messaging.

Usage:
    from core.firebase_config import firebase_app, firestore_db, auth_client
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from decouple import config
import firebase_admin
from firebase_admin import credentials, firestore, auth, messaging
from google.cloud.firestore import Client

logger = logging.getLogger(__name__)

# Global Firebase instances
firebase_app: Optional[firebase_admin.App] = None
firestore_db: Optional[Client] = None
auth_client = None


def initialize_firebase() -> firebase_admin.App:
    """
    Initialize Firebase Admin SDK with service account credentials.
    
    Returns:
        firebase_admin.App: Initialized Firebase app instance
        
    Raises:
        ValueError: If Firebase credentials are not properly configured
        Exception: If Firebase initialization fails
    """
    global firebase_app, firestore_db, auth_client
    
    if firebase_app:
        logger.info("Firebase already initialized")
        return firebase_app
    
    try:
        # Method 1: Use serviceAccountKey.json file (if available)
        service_account_path = os.path.join(settings.BASE_DIR, 'serviceAccountKey.json')
        
        if os.path.exists(service_account_path):
            logger.info("Using serviceAccountKey.json file for Firebase authentication")
            cred = credentials.Certificate(service_account_path)
        else:
            # Method 2: Use Django settings (more secure for production)
            logger.info("Using Django settings for Firebase authentication")
            
            # Get Firebase configuration from Django settings
            firebase_config = getattr(settings, 'FIREBASE_CONFIG', {})
            
            if not firebase_config.get('project_id'):
                raise ValueError("Firebase project_id not configured in Django settings")
            
            # Validate required fields
            required_fields = ['project_id', 'private_key', 'client_email']
            for field in required_fields:
                if not firebase_config.get(field):
                    raise ValueError(f"Missing required Firebase config: {field}")
            
            cred = credentials.Certificate(firebase_config)
        
        # Initialize Firebase app
        firebase_app = firebase_admin.initialize_app(cred, {
            'projectId': config('FIREBASE_PROJECT_ID')
        })
        
        # Initialize Firestore
        firestore_db = firestore.client()
        
        # Initialize Auth
        auth_client = auth
        
        logger.info("✅ Firebase initialized successfully")
        logger.info(f"🔥 Project ID: {config('FIREBASE_PROJECT_ID')}")
        logger.info(f"📊 Firestore client ready")
        
        return firebase_app
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {str(e)}")
        raise


def get_firestore_client() -> Client:
    """
    Get Firestore database client.
    
    Returns:
        Client: Firestore database client
    """
    if not firestore_db:
        initialize_firebase()
    return firestore_db


def get_auth_client():
    """
    Get Firebase Auth client.
    
    Returns:
        Firebase Auth client
    """
    if not auth_client:
        initialize_firebase()
    return auth_client


class FirestoreCollections:
    """
    Firestore collection names and utilities.
    """
    CUSTOMERS = 'customers'
    LIMIT_REQUESTS = 'limit_requests'
    NOTIFICATIONS = 'notifications'
    AUDIT_LOG = 'audit_log'
    OTPS = 'otps'
    CARDS = 'card_details'
    
    @classmethod
    def get_collection_ref(cls, collection_name: str):
        """
        Get reference to a Firestore collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            CollectionReference: Firestore collection reference
        """
        db = get_firestore_client()
        return db.collection(collection_name)


class FirebaseService:
    """
    Service class for Firebase operations.
    """
    
    def __init__(self):
        self.db = get_firestore_client()
        self.auth = get_auth_client()
    
    def create_document(self, collection: str, data: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Create a new document in Firestore.
        
        Args:
            collection (str): Collection name
            data (Dict[str, Any]): Document data
            doc_id (Optional[str]): Document ID (auto-generated if None)
            
        Returns:
            str: Document ID
        """
        try:
            collection_ref = self.db.collection(collection)
            
            if doc_id:
                doc_ref = collection_ref.document(doc_id)
                doc_ref.set(data)
                return doc_id
            else:
                doc_ref = collection_ref.add(data)[1]
                return doc_ref.id
                
        except Exception as e:
            logger.error(f"Error creating document in {collection}: {str(e)}")
            raise
    
    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from Firestore.
        
        Args:
            collection (str): Collection name
            doc_id (str): Document ID
            
        Returns:
            Optional[Dict[str, Any]]: Document data or None if not found
        """
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {doc_id} from {collection}: {str(e)}")
            raise
    
    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a document in Firestore.
        
        Args:
            collection (str): Collection name
            doc_id (str): Document ID
            data (Dict[str, Any]): Updated data
            
        Returns:
            bool: True if successful
        """
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.update(data)
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id} in {collection}: {str(e)}")
            raise
    
    def delete_document(self, collection: str, doc_id: str) -> bool:
        """
        Delete a document from Firestore.
        
        Args:
            collection (str): Collection name
            doc_id (str): Document ID
            
        Returns:
            bool: True if successful
        """
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.delete()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id} from {collection}: {str(e)}")
            raise
    
    def query_collection(self, collection: str, filters: Optional[list] = None, 
                         order_by: Optional[str] = None, limit: Optional[int] = None) -> list:
        """
        Query a collection with filters.
        
        Args:
            collection (str): Collection name
            filters (Optional[list]): List of filter tuples (field, operator, value)
            order_by (Optional[str]): Field to order by
            limit (Optional[int]): Maximum number of documents to return
            
        Returns:
            list: List of document data
        """
        try:
            collection_ref = self.db.collection(collection)
            query = collection_ref
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying collection {collection}: {str(e)}")
            raise
    
    def create_user(self, email: str, password: str, display_name: str = None) -> str:
        """
        Create a new Firebase user.
        
        Args:
            email (str): User email
            password (str): User password
            display_name (str, optional): User display name
            
        Returns:
            str: User UID
        """
        try:
            user_record = self.auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            
            logger.info(f"Created Firebase user: {user_record.uid}")
            return user_record.uid
            
        except Exception as e:
            logger.error(f"Error creating Firebase user: {str(e)}")
            raise
    
    def send_notification(self, token: str, title: str, body: str, data: Dict[str, str] = None):
        """
        Send push notification via Firebase Cloud Messaging.
        
        Args:
            token (str): FCM device token
            title (str): Notification title
            body (str): Notification body
            data (Dict[str, str], optional): Additional data
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent message: {response}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            raise


# Initialize Firebase when module is imported
try:
    initialize_firebase()
    logger.info("🔥 Firebase configuration module loaded successfully")
except Exception as e:
    logger.warning(f"⚠️  Firebase initialization deferred: {str(e)}")
    logger.warning("Firebase will be initialized when first accessed")


# Export main components
__all__ = [
    'initialize_firebase',
    'get_firestore_client', 
    'get_auth_client',
    'FirestoreCollections',
    'FirebaseService',
    'firebase_app',
    'firestore_db',
    'auth_client'
]