"""
Unit tests for account models.

Tests the Customer and CustomerProfile models including
validation, business logic, and database operations.
"""

import pytest
import unittest
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from unittest.mock import patch, MagicMock

from accounts.models import Customer, CustomerProfile
from tests.factories import CustomerFactory, CustomerProfileFactory


class CustomerModelTest(TestCase):
    """Test cases for Customer model."""
    
    def setUp(self):
        """Set up test data."""
        self.customer_data = {
            'customer_id': 'CUST123456',
            'phone_number': '+919876543210',
            'email': 'test@example.com',
            'firebase_uid': 'test_firebase_uid'
        }
    
    def test_customer_creation(self):
        """Test customer creation with valid data."""
        customer = Customer.objects.create(**self.customer_data)
        
        self.assertEqual(customer.customer_id, 'CUST123456')
        self.assertEqual(customer.phone_number, '+919876543210')
        self.assertEqual(customer.email, 'test@example.com')
        self.assertTrue(customer.is_active)
        self.assertIsNotNone(customer.created_at)
        self.assertIsNotNone(customer.updated_at)
    
    def test_customer_id_uniqueness(self):
        """Test that customer_id must be unique."""
        Customer.objects.create(**self.customer_data)
        
        with self.assertRaises(IntegrityError):
            Customer.objects.create(**self.customer_data)
    
    def test_phone_number_validation(self):
        """Test phone number validation."""
        # Test invalid phone number
        invalid_data = self.customer_data.copy()
        invalid_data['phone_number'] = 'invalid_phone'
        
        customer = Customer(**invalid_data)
        with self.assertRaises(ValidationError):
            customer.full_clean()
    
    def test_email_validation(self):
        """Test email validation."""
        # Test invalid email
        invalid_data = self.customer_data.copy()
        invalid_data['email'] = 'invalid_email'
        
        customer = Customer(**invalid_data)
        with self.assertRaises(ValidationError):
            customer.full_clean()
    
    def test_customer_str_representation(self):
        """Test string representation of customer."""
        customer = Customer.objects.create(**self.customer_data)
        expected_str = f"{customer.customer_id} - {customer.email}"
        self.assertEqual(str(customer), expected_str)
    
    def test_customer_deactivation(self):
        """Test customer deactivation."""
        customer = Customer.objects.create(**self.customer_data)
        customer.deactivate()
        
        self.assertFalse(customer.is_active)
        self.assertIsNotNone(customer.deactivated_at)
    
    def test_customer_last_login_update(self):
        """Test last login update."""
        customer = Customer.objects.create(**self.customer_data)
        old_last_login = customer.last_login
        
        customer.update_last_login()
        
        self.assertNotEqual(customer.last_login, old_last_login)
        self.assertIsInstance(customer.last_login, datetime)
    
    @patch('core.firebase_service.FirebaseService.create_user')
    def test_firebase_integration(self, mock_firebase):
        """Test Firebase user creation integration."""
        mock_firebase.return_value = {
            'success': True,
            'uid': 'test_firebase_uid'
        }
        
        customer = Customer.objects.create(**self.customer_data)
        result = customer.create_firebase_user()
        
        self.assertTrue(result['success'])
        mock_firebase.assert_called_once()


class CustomerProfileModelTest(TestCase):
    """Test cases for CustomerProfile model."""
    
    def setUp(self):
        """Set up test data."""
        self.customer = CustomerFactory()
        self.profile_data = {
            'customer': self.customer,
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': datetime(1990, 1, 1).date(),
            'pan_number': 'ABCDE1234F',
            'aadhar_number': '123456789012',
            'address_line1': '123 Test Street',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'pincode': '400001',
            'annual_income': Decimal('500000'),
            'employment_type': 'SALARIED',
            'kyc_status': 'PENDING'
        }
    
    def test_profile_creation(self):
        """Test customer profile creation."""
        profile = CustomerProfile.objects.create(**self.profile_data)
        
        self.assertEqual(profile.first_name, 'John')
        self.assertEqual(profile.last_name, 'Doe')
        self.assertEqual(profile.annual_income, Decimal('500000'))
        self.assertEqual(profile.kyc_status, 'PENDING')
    
    def test_pan_number_validation(self):
        """Test PAN number validation."""
        # Test invalid PAN format
        invalid_data = self.profile_data.copy()
        invalid_data['pan_number'] = 'INVALID_PAN'
        
        profile = CustomerProfile(**invalid_data)
        with self.assertRaises(ValidationError):
            profile.full_clean()
    
    def test_aadhar_number_validation(self):
        """Test Aadhar number validation."""
        # Test invalid Aadhar format
        invalid_data = self.profile_data.copy()
        invalid_data['aadhar_number'] = '123'  # Too short
        
        profile = CustomerProfile(**invalid_data)
        with self.assertRaises(ValidationError):
            profile.full_clean()
    
    def test_age_calculation(self):
        """Test age calculation."""
        profile = CustomerProfile.objects.create(**self.profile_data)
        expected_age = datetime.now().year - 1990
        
        self.assertEqual(profile.get_age(), expected_age)
    
    def test_full_name_property(self):
        """Test full name property."""
        profile = CustomerProfile.objects.create(**self.profile_data)
        expected_name = "John Doe"
        
        self.assertEqual(profile.full_name, expected_name)
    
    def test_complete_address_property(self):
        """Test complete address property."""
        profile = CustomerProfile.objects.create(**self.profile_data)
        expected_address = "123 Test Street, Mumbai, Maharashtra - 400001"
        
        self.assertEqual(profile.complete_address, expected_address)
    
    def test_kyc_verification(self):
        """Test KYC status update."""
        profile = CustomerProfile.objects.create(**self.profile_data)
        
        profile.verify_kyc()
        
        self.assertEqual(profile.kyc_status, 'VERIFIED')
        self.assertIsNotNone(profile.kyc_verified_at)
    
    def test_credit_score_update(self):
        """Test credit score update."""
        profile = CustomerProfile.objects.create(**self.profile_data)
        
        profile.update_credit_score(750)
        
        self.assertEqual(profile.credit_score, 750)
        self.assertIsNotNone(profile.credit_score_updated_at)
    
    def test_income_validation(self):
        """Test income validation."""
        # Test negative income
        invalid_data = self.profile_data.copy()
        invalid_data['annual_income'] = Decimal('-1000')
        
        profile = CustomerProfile(**invalid_data)
        with self.assertRaises(ValidationError):
            profile.full_clean()
    
    def test_employment_type_choices(self):
        """Test employment type choices validation."""
        valid_types = ['SALARIED', 'SELF_EMPLOYED', 'BUSINESS', 'RETIRED']
        
        for emp_type in valid_types:
            data = self.profile_data.copy()
            data['employment_type'] = emp_type
            profile = CustomerProfile(**data)
            profile.full_clean()  # Should not raise exception
    
    def test_profile_str_representation(self):
        """Test string representation of profile."""
        profile = CustomerProfile.objects.create(**self.profile_data)
        expected_str = f"{profile.full_name} ({profile.customer.customer_id})"
        
        self.assertEqual(str(profile), expected_str)


class CustomerModelFactoryTest(TestCase):
    """Test cases for Customer model factories."""
    
    def test_customer_factory(self):
        """Test CustomerFactory creates valid instances."""
        customer = CustomerFactory()
        
        self.assertIsNotNone(customer.customer_id)
        self.assertIsNotNone(customer.phone_number)
        self.assertIsNotNone(customer.email)
        self.assertTrue(customer.is_active)
        self.assertIsNotNone(customer.firebase_uid)
    
    def test_customer_profile_factory(self):
        """Test CustomerProfileFactory creates valid instances."""
        profile = CustomerProfileFactory()
        
        self.assertIsNotNone(profile.customer)
        self.assertIsNotNone(profile.first_name)
        self.assertIsNotNone(profile.last_name)
        self.assertIsNotNone(profile.pan_number)
        self.assertIsNotNone(profile.aadhar_number)
        self.assertGreater(profile.annual_income, 0)
    
    def test_factory_batch_creation(self):
        """Test creating multiple instances with factories."""
        customers = CustomerFactory.create_batch(5)
        profiles = CustomerProfileFactory.create_batch(3)
        
        self.assertEqual(len(customers), 5)
        self.assertEqual(len(profiles), 3)
        
        # Check uniqueness
        customer_ids = [c.customer_id for c in customers]
        self.assertEqual(len(customer_ids), len(set(customer_ids)))


class CustomerModelIntegrationTest(TestCase):
    """Integration tests for Customer model with external services."""
    
    @patch('core.firebase_service.FirebaseService.create_user')
    @patch('core.twilio_service.TwilioService.send_sms')
    def test_customer_registration_flow(self, mock_sms, mock_firebase):
        """Test complete customer registration flow."""
        # Mock external services
        mock_firebase.return_value = {
            'success': True,
            'uid': 'test_firebase_uid'
        }
        mock_sms.return_value = {
            'success': True,
            'message_sid': 'test_message_sid'
        }
        
        # Create customer
        customer = CustomerFactory()
        profile = CustomerProfileFactory(customer=customer)
        
        # Test Firebase user creation
        firebase_result = customer.create_firebase_user()
        self.assertTrue(firebase_result['success'])
        
        # Test SMS notification
        sms_result = customer.send_welcome_sms()
        self.assertTrue(sms_result['success'])
        
        # Verify database state
        self.assertTrue(customer.is_active)
        self.assertEqual(profile.kyc_status, 'VERIFIED')
    
    @patch('core.firebase_service.FirebaseService.update_user')
    def test_customer_profile_update_flow(self, mock_firebase):
        """Test customer profile update with Firebase sync."""
        mock_firebase.return_value = {'success': True}
        
        customer = CustomerFactory()
        profile = CustomerProfileFactory(customer=customer)
        
        # Update profile
        profile.first_name = 'Updated'
        profile.annual_income = Decimal('600000')
        profile.save()
        
        # Test Firebase sync
        sync_result = customer.sync_with_firebase()
        self.assertTrue(sync_result['success'])
        
        mock_firebase.assert_called_once()


if __name__ == '__main__':
    unittest.main()