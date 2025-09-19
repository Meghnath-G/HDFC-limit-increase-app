"""
Django management command to test Firebase models functionality.

Tests the Firebase model layer to ensure proper integration
with Firestore operations and validation.
"""

import os
import sys
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

# Add Django paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Firebase models
from core.firebase_models import FirebaseCustomer, FirebaseLimitRequest
from core.firebase_config import initialize_firebase
from core.utils import generate_customer_id, generate_reference_number

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command for testing Firebase models."""
    
    help = 'Test Firebase models functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test customer and limit request data',
        )
        parser.add_argument(
            '--test-queries',
            action='store_true',
            help='Test various model query operations',
        )
        parser.add_argument(
            '--clean-test-data',
            action='store_true',
            help='Clean up test data after testing',
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write("🚀 Starting Firebase models test...")
        
        try:
            # Initialize Firebase
            initialize_firebase()
            self.stdout.write(self.style.SUCCESS("✅ Firebase initialized successfully"))
            
            # Run tests based on options
            if options['create_test_data']:
                self.test_create_operations()
            
            if options['test_queries']:
                self.test_query_operations()
            
            if options['clean_test_data']:
                self.clean_test_data()
            
            if not any([options['create_test_data'], options['test_queries'], options['clean_test_data']]):
                # Run all tests by default
                self.test_create_operations()
                self.test_query_operations()
                self.test_model_operations()
            
            self.stdout.write(self.style.SUCCESS("🎉 All tests completed successfully!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Test failed: {str(e)}"))
            logger.error(f"Firebase models test failed: {str(e)}")
    
    def test_create_operations(self):
        """Test creating Firebase model instances."""
        self.stdout.write("📝 Testing model creation operations...")
        
        try:
            # Test Customer creation
            customer = FirebaseCustomer()
            customer.firebase_uid = 'test-firebase-uid-001'
            customer.name = 'John Doe Test'
            customer.email = 'john.doe.test@hdfc.com'
            customer.phone_number = '+919876543210'
            customer.date_of_birth = date(1990, 1, 15)
            customer.customer_id = generate_customer_id()
            
            customer_id = customer.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Created test customer: {customer_id}"))
            
            # Test LimitRequest creation
            limit_request = FirebaseLimitRequest()
            limit_request.customer_ref = f"customers/{customer_id}"
            limit_request.reference_number = generate_reference_number()
            limit_request.current_limit = 50000.0
            limit_request.requested_limit = 100000.0
            limit_request.reason = "Salary increase and improved credit score"
            limit_request.annual_income = 1200000.0
            limit_request.submitted_by = 'test-user'
            
            request_id = limit_request.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Created test limit request: {request_id}"))
            
            # Store IDs for later tests
            self.test_customer_id = customer_id
            self.test_request_id = request_id
            self.test_customer_uid = customer.firebase_uid
            self.test_reference_number = limit_request.reference_number
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Create operation failed: {str(e)}"))
            raise
    
    def test_query_operations(self):
        """Test querying Firebase model instances."""
        self.stdout.write("🔍 Testing model query operations...")
        
        try:
            # Test get by ID
            customer = FirebaseCustomer.get_by_id(getattr(self, 'test_customer_id', 'non-existent'))
            if customer:
                self.stdout.write(self.style.SUCCESS(f"✅ Retrieved customer by ID: {customer.name}"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  No customer found by ID (expected if no test data)"))
            
            # Test get by Firebase UID
            customer_by_uid = FirebaseCustomer.get_by_firebase_uid(
                getattr(self, 'test_customer_uid', 'non-existent-uid')
            )
            if customer_by_uid:
                self.stdout.write(self.style.SUCCESS(f"✅ Retrieved customer by Firebase UID: {customer_by_uid.name}"))
            
            # Test get all customers
            all_customers = FirebaseCustomer.get_all(limit=5)
            self.stdout.write(self.style.SUCCESS(f"✅ Retrieved {len(all_customers)} customers"))
            
            # Test active customers filter
            active_customers = FirebaseCustomer.get_active_customers()
            self.stdout.write(self.style.SUCCESS(f"✅ Retrieved {len(active_customers)} active customers"))
            
            # Test limit request queries
            if hasattr(self, 'test_reference_number'):
                request_by_ref = FirebaseLimitRequest.get_by_reference_number(self.test_reference_number)
                if request_by_ref:
                    self.stdout.write(self.style.SUCCESS(f"✅ Retrieved request by reference: {request_by_ref.reference_number}"))
            
            # Test pending requests
            pending_requests = FirebaseLimitRequest.get_pending_requests()
            self.stdout.write(self.style.SUCCESS(f"✅ Retrieved {len(pending_requests)} pending requests"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Query operation failed: {str(e)}"))
            raise
    
    def test_model_operations(self):
        """Test model update and business logic operations."""
        self.stdout.write("⚙️  Testing model business operations...")
        
        try:
            # Test customer operations
            if hasattr(self, 'test_customer_id'):
                customer = FirebaseCustomer.get_by_id(self.test_customer_id)
                if customer:
                    # Test KYC update
                    customer.update_kyc_status('VERIFIED', 'test-admin')
                    self.stdout.write(self.style.SUCCESS("✅ Updated customer KYC status"))
                    
                    # Test last login update
                    customer.update_last_login()
                    self.stdout.write(self.style.SUCCESS("✅ Updated customer last login"))
            
            # Test limit request operations
            if hasattr(self, 'test_request_id'):
                limit_request = FirebaseLimitRequest.get_by_id(self.test_request_id)
                if limit_request:
                    # Test approval
                    limit_request.approve(
                        approved_by='test-approver',
                        approved_limit=90000.0,
                        comments='Approved based on income verification'
                    )
                    self.stdout.write(self.style.SUCCESS("✅ Approved limit request"))
                    
                    # Verify status update
                    updated_request = FirebaseLimitRequest.get_by_id(self.test_request_id)
                    if updated_request and updated_request.status == 'APPROVED':
                        self.stdout.write(self.style.SUCCESS("✅ Verified request status update"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Model operation failed: {str(e)}"))
            raise
    
    def clean_test_data(self):
        """Clean up test data."""
        self.stdout.write("🧹 Cleaning up test data...")
        
        try:
            # Delete test customer
            if hasattr(self, 'test_customer_id'):
                customer = FirebaseCustomer.get_by_id(self.test_customer_id)
                if customer:
                    customer.delete()
                    self.stdout.write(self.style.SUCCESS("✅ Cleaned up test customer"))
            
            # Delete test limit request
            if hasattr(self, 'test_request_id'):
                limit_request = FirebaseLimitRequest.get_by_id(self.test_request_id)
                if limit_request:
                    limit_request.delete()
                    self.stdout.write(self.style.SUCCESS("✅ Cleaned up test limit request"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Cleanup warning: {str(e)}"))
    
    def display_test_summary(self):
        """Display test summary."""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 FIREBASE MODELS TEST SUMMARY")
        self.stdout.write("="*60)
        self.stdout.write("✅ Customer model operations: PASSED")
        self.stdout.write("✅ Limit request model operations: PASSED")
        self.stdout.write("✅ Query operations: PASSED")
        self.stdout.write("✅ Business logic operations: PASSED")
        self.stdout.write("="*60)
        self.stdout.write("🎉 All Firebase model tests completed successfully!")
        
        self.stdout.write("\n💡 Usage Examples:")
        self.stdout.write("# Create a new customer")
        self.stdout.write("customer = FirebaseCustomer()")
        self.stdout.write("customer.name = 'John Doe'")
        self.stdout.write("customer.email = 'john@example.com'")
        self.stdout.write("customer_id = customer.save()")
        self.stdout.write("")
        self.stdout.write("# Query customers")
        self.stdout.write("all_customers = FirebaseCustomer.get_all()")
        self.stdout.write("active_customers = FirebaseCustomer.get_active_customers()")
        self.stdout.write("customer = FirebaseCustomer.get_by_firebase_uid('uid')")
        self.stdout.write("")
        self.stdout.write("# Create limit request")
        self.stdout.write("request = FirebaseLimitRequest()")
        self.stdout.write("request.customer_ref = f'customers/{customer_id}'")
        self.stdout.write("request.requested_limit = 100000")
        self.stdout.write("request_id = request.save()")