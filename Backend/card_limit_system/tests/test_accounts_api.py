"""
API tests for customer endpoints.

Tests all customer-related API endpoints including
authentication, permissions, and business logic.
"""

import json
import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token

from accounts.models import Customer, CustomerProfile
from tests.factories import CustomerFactory, CustomerProfileFactory


class CustomerAPITest(APITestCase):
    """Test cases for Customer API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.customer = CustomerFactory()
        self.profile = CustomerProfileFactory(customer=self.customer)
        
        # Create authentication token
        self.token = Token.objects.create(user_id=self.customer.id)
        
    def authenticate(self):
        """Authenticate the test client."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_customer_registration(self):
        """Test customer registration endpoint."""
        url = reverse('customer-register')
        data = {
            'phone_number': '+919876543210',
            'email': 'newcustomer@example.com',
            'firebase_uid': 'new_firebase_uid'
        }
        
        with patch('core.firebase_service.FirebaseService.verify_token') as mock_verify:
            mock_verify.return_value = {
                'success': True,
                'uid': 'new_firebase_uid',
                'email': 'newcustomer@example.com'
            }
            
            response = self.client.post(url, data, format='json')
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('customer_id', response.data)
        self.assertEqual(response.data['email'], data['email'])
        
        # Verify customer was created in database
        customer = Customer.objects.get(email=data['email'])
        self.assertEqual(customer.phone_number, data['phone_number'])
    
    def test_customer_registration_duplicate_email(self):
        """Test registration with duplicate email fails."""
        url = reverse('customer-register')
        data = {
            'phone_number': '+919876543211',
            'email': self.customer.email,  # Duplicate email
            'firebase_uid': 'another_firebase_uid'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_customer_profile_creation(self):
        """Test customer profile creation."""
        # Create a customer without profile
        new_customer = CustomerFactory()
        new_token = Token.objects.create(user_id=new_customer.id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {new_token.key}')
        
        url = reverse('customer-profile')
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'pan_number': 'ABCDE1234F',
            'aadhar_number': '123456789012',
            'address_line1': '123 Test Street',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'pincode': '400001',
            'annual_income': '500000',
            'employment_type': 'SALARIED'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], data['first_name'])
        
        # Verify profile was created in database
        profile = CustomerProfile.objects.get(customer=new_customer)
        self.assertEqual(profile.pan_number, data['pan_number'])
    
    def test_customer_profile_get(self):
        """Test getting customer profile."""
        self.authenticate()
        url = reverse('customer-profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], self.profile.first_name)
        self.assertEqual(response.data['customer_id'], self.customer.customer_id)
    
    def test_customer_profile_update(self):
        """Test updating customer profile."""
        self.authenticate()
        url = reverse('customer-profile')
        data = {
            'first_name': 'Updated',
            'annual_income': '600000'
        }
        
        with patch('core.firebase_service.FirebaseService.update_user') as mock_update:
            mock_update.return_value = {'success': True}
            
            response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], data['first_name'])
        
        # Verify database was updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.first_name, data['first_name'])
        self.assertEqual(str(self.profile.annual_income), data['annual_income'])
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        url = reverse('customer-profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_customer_deactivation(self):
        """Test customer deactivation endpoint."""
        self.authenticate()
        url = reverse('customer-deactivate')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify customer was deactivated
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_active)
        self.assertIsNotNone(self.customer.deactivated_at)
    
    @patch('core.twilio_service.TwilioService.send_verification')
    def test_phone_verification_request(self, mock_twilio):
        """Test phone number verification request."""
        mock_twilio.return_value = {
            'success': True,
            'verification_sid': 'test_verification_sid'
        }
        
        self.authenticate()
        url = reverse('customer-verify-phone')
        data = {'phone_number': '+919876543210'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_twilio.assert_called_once()
    
    @patch('core.twilio_service.TwilioService.check_verification')
    def test_phone_verification_confirm(self, mock_twilio):
        """Test phone number verification confirmation."""
        mock_twilio.return_value = {
            'success': True,
            'status': 'approved'
        }
        
        self.authenticate()
        url = reverse('customer-verify-phone-confirm')
        data = {
            'phone_number': '+919876543210',
            'verification_code': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['verified'])
        mock_twilio.assert_called_once()


class CustomerListAPITest(APITestCase):
    """Test cases for Customer list endpoints (admin only)."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.customers = CustomerFactory.create_batch(5)
        
        # Create admin user
        self.admin_customer = CustomerFactory(is_staff=True)
        self.admin_token = Token.objects.create(user_id=self.admin_customer.id)
    
    def authenticate_admin(self):
        """Authenticate as admin."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
    
    def test_customer_list_admin_access(self):
        """Test that admin can access customer list."""
        self.authenticate_admin()
        url = reverse('customer-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)  # 5 + 1 admin
    
    def test_customer_list_regular_user_denied(self):
        """Test that regular users cannot access customer list."""
        regular_token = Token.objects.create(user_id=self.customers[0].id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {regular_token.key}')
        
        url = reverse('customer-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_customer_search(self):
        """Test customer search functionality."""
        self.authenticate_admin()
        url = reverse('customer-list')
        
        # Search by email
        response = self.client.get(url, {'search': self.customers[0].email})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['email'], self.customers[0].email)
    
    def test_customer_filtering(self):
        """Test customer filtering by status."""
        # Deactivate one customer
        self.customers[0].deactivate()
        
        self.authenticate_admin()
        url = reverse('customer-list')
        
        # Filter active customers
        response = self.client.get(url, {'is_active': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have 4 active customers + 1 admin
        self.assertEqual(len(response.data['results']), 5)
    
    def test_customer_ordering(self):
        """Test customer list ordering."""
        self.authenticate_admin()
        url = reverse('customer-list')
        
        # Order by creation date (newest first)
        response = self.client.get(url, {'ordering': '-created_at'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check ordering
        results = response.data['results']
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i]['created_at'],
                results[i + 1]['created_at']
            )


class CustomerAPIValidationTest(APITestCase):
    """Test cases for API validation and error handling."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
    
    def test_invalid_phone_number_format(self):
        """Test validation for invalid phone number format."""
        url = reverse('customer-register')
        data = {
            'phone_number': 'invalid_phone',
            'email': 'test@example.com',
            'firebase_uid': 'test_uid'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
    
    def test_invalid_email_format(self):
        """Test validation for invalid email format."""
        url = reverse('customer-register')
        data = {
            'phone_number': '+919876543210',
            'email': 'invalid_email',
            'firebase_uid': 'test_uid'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_missing_required_fields(self):
        """Test validation for missing required fields."""
        url = reverse('customer-register')
        data = {
            'email': 'test@example.com'
            # Missing phone_number and firebase_uid
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
        self.assertIn('firebase_uid', response.data)
    
    def test_invalid_pan_number_format(self):
        """Test validation for invalid PAN number format."""
        customer = CustomerFactory()
        token = Token.objects.create(user_id=customer.id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        url = reverse('customer-profile')
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'pan_number': 'INVALID_PAN',  # Invalid format
            'aadhar_number': '123456789012'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('pan_number', response.data)
    
    def test_invalid_aadhar_number_format(self):
        """Test validation for invalid Aadhar number format."""
        customer = CustomerFactory()
        token = Token.objects.create(user_id=customer.id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        url = reverse('customer-profile')
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'pan_number': 'ABCDE1234F',
            'aadhar_number': '123'  # Too short
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('aadhar_number', response.data)


class CustomerAPIRateLimitTest(APITestCase):
    """Test cases for API rate limiting."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.customer = CustomerFactory()
        self.token = Token.objects.create(user_id=self.customer.id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    @patch('core.middleware.RateLimitMiddleware.is_rate_limited')
    def test_rate_limit_enforcement(self, mock_rate_limit):
        """Test that rate limiting is enforced."""
        mock_rate_limit.return_value = True
        
        url = reverse('customer-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    @patch('core.twilio_service.TwilioService.send_verification')
    def test_otp_rate_limiting(self, mock_twilio):
        """Test OTP request rate limiting."""
        mock_twilio.return_value = {
            'success': True,
            'verification_sid': 'test_sid'
        }
        
        url = reverse('customer-verify-phone')
        data = {'phone_number': '+919876543210'}
        
        # Make multiple rapid requests
        responses = []
        for _ in range(5):
            response = self.client.post(url, data, format='json')
            responses.append(response)
        
        # Some requests should be rate limited
        rate_limited_count = sum(
            1 for r in responses 
            if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        )
        
        self.assertGreater(rate_limited_count, 0)


if __name__ == '__main__':
    unittest.main()