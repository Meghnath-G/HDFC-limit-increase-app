from django.core.management.base import BaseCommand
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import os
from pathlib import Path
from datetime import datetime

class Command(BaseCommand):
    help = 'Initialize Firebase connection and create Firestore collections'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-collections',
            action='store_true',
            help='Create initial Firestore collections'
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true', 
            help='Create test data in Firestore'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🔥 Initializing Firebase for HDFC Card Limit System...")
        
        try:
            # Check if service account key exists
            key_path = Path(__file__).resolve().parent.parent.parent.parent / 'firebase-service-account-key.json'
            
            if not key_path.exists():
                self.stdout.write(
                    self.style.ERROR('❌ Firebase service account key not found!')
                )
                self.stdout.write(f"Expected location: {key_path}")
                self.stdout.write("Please download the service account key from Firebase Console:")
                self.stdout.write("1. Go to Project Settings > Service Accounts")
                self.stdout.write("2. Click 'Generate new private key'")
                self.stdout.write(f"3. Save as: {key_path}")
                return
            
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                cred = credentials.Certificate(str(key_path))
                firebase_admin.initialize_app(cred)
                self.stdout.write(
                    self.style.SUCCESS('✅ Firebase Admin SDK initialized successfully!')
                )
            else:
                self.stdout.write("ℹ️  Firebase already initialized")
            
            # Get Firestore client
            db = firestore.client()
            self.stdout.write("✅ Firestore client connected")
            
            # Test connection
            test_ref = db.collection('_test').document('connection_test')
            test_ref.set({
                'timestamp': firestore.SERVER_TIMESTAMP,
                'message': 'Firebase connection test successful',
                'project': 'HDFC Card Limit System'
            })
            self.stdout.write("✅ Firebase connection test successful")
            
            # Clean up test document
            test_ref.delete()
            
            # Create collections if requested
            if options['create_collections']:
                self.create_collections(db)
            
            # Create test data if requested
            if options['create_test_data']:
                self.create_test_data(db)
                
            self.stdout.write(
                self.style.SUCCESS('🎉 Firebase initialization completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error initializing Firebase: {str(e)}')
            )
            self.stdout.write("Please check:")
            self.stdout.write("1. Service account key file exists and is valid")
            self.stdout.write("2. Firebase project ID is correct")
            self.stdout.write("3. Firestore is enabled in your Firebase project")
    
    def create_collections(self, db):
        """Create initial Firestore collections with proper structure."""
        self.stdout.write("\n📁 Creating Firestore collections...")
        
        collections = {
            'customers': {
                'description': 'Customer profiles and personal information',
                'sample_fields': ['firebase_uid', 'customer_id', 'personal_info', 'account_info', 'metadata']
            },
            'limit_requests': {
                'description': 'Credit/debit limit increase requests',
                'sample_fields': ['customer_id', 'reference_number', 'request_details', 'workflow', 'metadata']
            },
            'cards': {
                'description': 'Customer card information (masked)',
                'sample_fields': ['customer_id', 'card_number_masked', 'card_type', 'current_limit', 'metadata']
            },
            'notifications': {
                'description': 'Notification delivery tracking',
                'sample_fields': ['customer_id', 'notification_type', 'content', 'delivery_status', 'metadata']
            },
            'otp_codes': {
                'description': 'OTP generation and verification logs',
                'sample_fields': ['customer_id', 'otp_hash', 'delivery_method', 'status', 'metadata']
            },
            'audit_logs': {
                'description': 'System activity and security audit trail',
                'sample_fields': ['user_id', 'action', 'resource', 'details', 'metadata']
            }
        }
        
        for collection_name, collection_info in collections.items():
            # Create a metadata document to initialize the collection
            doc_ref = db.collection(collection_name).document('_collection_info')
            doc_ref.set({
                'collection_name': collection_name,
                'description': collection_info['description'],
                'sample_fields': collection_info['sample_fields'],
                'created_at': firestore.SERVER_TIMESTAMP,
                'created_by': 'django_management_command',
                'purpose': 'Collection initialization',
                'delete_after_first_real_document': True
            })
            
            self.stdout.write(f"  ✅ Created collection: {collection_name}")
        
        self.stdout.write("📁 All collections created successfully!")
    
    def create_test_data(self, db):
        """Create test data for development and testing."""
        self.stdout.write("\n🧪 Creating test data...")
        
        # Test customer
        test_customer = {
            'firebase_uid': 'test_customer_123',
            'customer_id': 'CUST001',
            'personal_info': {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@test.com',
                'phone_number': '+919876543210',
                'date_of_birth': '1990-05-15',
                'address': {
                    'street': '123 Test Street',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'postal_code': '400001',
                    'country': 'India'
                }
            },
            'account_info': {
                'kyc_status': 'completed',
                'account_type': 'savings',
                'annual_income': 800000,
                'employment_type': 'salaried'
            },
            'verification_status': {
                'email_verified': True,
                'phone_verified': True,
                'document_verified': True
            },
            'metadata': {
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'is_test_data': True
            }
        }
        
        # Add test customer
        customer_ref = db.collection('customers').add(test_customer)
        customer_doc_id = customer_ref[1].id
        self.stdout.write(f"  ✅ Created test customer: {customer_doc_id}")
        
        # Test limit request
        test_request = {
            'customer_id': 'CUST001',
            'reference_number': f'REQ{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'request_details': {
                'request_type': 'credit_limit',
                'current_limit': 50000,
                'requested_limit': 100000,
                'reason': 'Income increase and higher expenses',
                'priority': 'normal'
            },
            'workflow': {
                'status': 'pending',
                'assigned_to': None,
                'approval_notes': '',
                'status_history': [
                    {
                        'status': 'pending',
                        'timestamp': firestore.SERVER_TIMESTAMP,
                        'changed_by': 'system'
                    }
                ]
            },
            'documents': {
                'supporting_documents': ['salary_slip_sample.pdf', 'bank_statement_sample.pdf'],
                'income_proof': 'income_certificate_sample.pdf'
            },
            'metadata': {
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'estimated_completion': None,
                'is_test_data': True
            }
        }
        
        # Add test request
        request_ref = db.collection('limit_requests').add(test_request)
        request_doc_id = request_ref[1].id
        self.stdout.write(f"  ✅ Created test limit request: {request_doc_id}")
        
        # Test card
        test_card = {
            'customer_id': 'CUST001',
            'card_number_masked': '****-****-****-1234',
            'card_type': 'credit',
            'current_limit': 50000,
            'available_limit': 45000,
            'metadata': {
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'is_active': True,
                'is_test_data': True
            }
        }
        
        # Add test card
        card_ref = db.collection('cards').add(test_card)
        card_doc_id = card_ref[1].id
        self.stdout.write(f"  ✅ Created test card: {card_doc_id}")
        
        self.stdout.write("🧪 Test data created successfully!")
        self.stdout.write("\n📊 You can now view this data in Firebase Console:")
        self.stdout.write("1. Go to https://console.firebase.google.com/")
        self.stdout.write("2. Select your 'hdfc-card-limit-system' project")
        self.stdout.write("3. Click 'Firestore Database'")
        self.stdout.write("4. Browse the collections to see your test data")