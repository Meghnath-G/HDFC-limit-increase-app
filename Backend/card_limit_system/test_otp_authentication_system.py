#!/usr/bin/env python3
"""
Comprehensive OTP Authentication System Test Suite

This script tests the complete end-to-end OTP authentication flow:
- Backend Twilio OTP service integration
- Customer model OTP functionality
- Django REST API endpoints
- Firebase authentication integration
- Error handling and edge cases

Usage:
    python test_otp_authentication_system.py
"""

import os
import sys
import django
import json
import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
import time

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'card_limit_system.settings')
django.setup()

# Import after Django setup
from apps.customers.models import Customer
from core.twilio_otp_service import TwilioOTPService
from core.utils import encrypt_field
from core.firebase_config import get_firebase_auth

class OTPAuthenticationSystemTest:
    """
    Complete test suite for OTP authentication system
    """
    
    def __init__(self):
        self.client = Client()
        self.test_phone = "+919876543210"
        self.test_customer_data = {
            "name": "Test Customer",
            "email": "test@example.com",
            "phone": self.test_phone,
            "date_of_birth": "1990-01-01"
        }
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'details': details
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        if details and not success:
            print(f"    Details: {details}")
        print()
    
    def setup_test_data(self):
        """Set up test data"""
        try:
            # Clean up any existing test data
            Customer.objects.filter(phone=encrypt_field(self.test_phone)).delete()
            cache.clear()
            
            self.log_test("Setup Test Data", True, "Test environment prepared")
            return True
        except Exception as e:
            self.log_test("Setup Test Data", False, f"Setup failed: {e}")
            return False
    
    def test_customer_model_otp_functionality(self):
        """Test Customer model OTP-related functionality"""
        try:
            # Create test customer
            customer = Customer.objects.create(
                firebase_uid=str(uuid.uuid4()),
                name=self.test_customer_data['name'],
                email=self.test_customer_data['email'],
                phone=self.test_customer_data['phone'],
                date_of_birth=self.test_customer_data['date_of_birth']
            )
            
            # Test OTP rate limiting
            can_request, message = customer.can_request_otp()
            if not can_request:
                self.log_test("Customer OTP Rate Limiting", False, 
                            f"Initial rate limit check failed: {message}")
                return False
            
            # Test increment OTP attempts
            initial_count = customer.otp_verification_count
            customer.increment_otp_attempts()
            customer.refresh_from_db()
            
            if customer.otp_verification_count != initial_count + 1:
                self.log_test("Customer OTP Increment", False, 
                            "OTP attempt count not incremented")
                return False
            
            # Test phone verification
            customer.mark_phone_verified()
            customer.refresh_from_db()
            
            if not customer.phone_verified or not customer.phone_verified_at:
                self.log_test("Customer Phone Verification", False, 
                            "Phone verification not marked correctly")
                return False
            
            # Test masked phone
            masked = customer.get_masked_phone()
            if not masked or len(masked) < 8:
                self.log_test("Customer Masked Phone", False, 
                            "Masked phone generation failed")
                return False
            
            self.log_test("Customer Model OTP Functionality", True, 
                        "All customer OTP functions working correctly")
            return True
            
        except Exception as e:
            self.log_test("Customer Model OTP Functionality", False, 
                        f"Customer model test failed: {e}")
            return False
    
    @patch('core.twilio_otp_service.TwilioOTPService._send_twilio_sms')
    @patch('core.twilio_otp_service.TwilioOTPService._store_otp_in_firebase')
    def test_twilio_otp_service(self, mock_firebase, mock_twilio):
        """Test Twilio OTP service functionality"""
        try:
            # Mock successful responses
            mock_twilio.return_value = {
                'success': True,
                'message_sid': 'SM123456789',
                'status': 'sent'
            }
            
            mock_firebase.return_value = {
                'success': True,
                'otp_id': 'otp_123456'
            }
            
            # Test OTP service
            otp_service = TwilioOTPService()
            
            # Test send OTP
            result = otp_service.send_otp(
                phone_number=self.test_phone,
                customer_id=str(uuid.uuid4()),
                purpose='test'
            )
            
            if not result['success']:
                self.log_test("Twilio OTP Send", False, 
                            f"OTP send failed: {result.get('message')}")
                return False
            
            otp_id = result['otp_id']
            
            # Test verify OTP with correct code
            # Simulate the OTP that would be generated
            test_otp = '123456'
            
            with patch.object(otp_service, '_get_stored_otp') as mock_get_otp:
                mock_get_otp.return_value = {
                    'otp_hash': otp_service._hash_otp(test_otp),
                    'expires_at': (timezone.now() + timezone.timedelta(minutes=5)).isoformat(),
                    'attempts': 0,
                    'phone_number': self.test_phone
                }
                
                verify_result = otp_service.verify_otp(
                    otp_id=otp_id,
                    otp_code=test_otp,
                    phone_number=self.test_phone
                )
                
                if not verify_result['success']:
                    self.log_test("Twilio OTP Verify", False, 
                                f"OTP verify failed: {verify_result.get('message')}")
                    return False
            
            self.log_test("Twilio OTP Service", True, 
                        "OTP send and verify working correctly")
            return True
            
        except Exception as e:
            self.log_test("Twilio OTP Service", False, 
                        f"Twilio service test failed: {e}")
            return False
    
    @patch('apps.authentication.otp_auth_views.TwilioOTPService')
    def test_registration_api_flow(self, mock_otp_service):
        """Test OTP registration API flow"""
        try:
            # Mock OTP service
            mock_service = MagicMock()
            mock_otp_service.return_value = mock_service
            
            # Test registration request
            mock_service.send_otp.return_value = {
                'success': True,
                'otp_id': 'test_otp_123',
                'expires_in': 300
            }
            
            response = self.client.post('/api/v1/auth/phone-register/request/', {
                'phone_number': self.test_phone,
                'name': self.test_customer_data['name'],
                'email': self.test_customer_data['email']
            }, content_type='application/json')
            
            if response.status_code != 200:
                self.log_test("Registration Request API", False, 
                            f"Request failed with status {response.status_code}")
                return False
            
            data = response.json()
            if not data.get('success'):
                self.log_test("Registration Request API", False, 
                            f"Request API failed: {data.get('message')}")
                return False
            
            session_id = data.get('session_id')
            
            # Test registration verification
            mock_service.verify_otp.return_value = {
                'success': True,
                'message': 'OTP verified successfully'
            }
            
            with patch('apps.authentication.otp_auth_views.get_firebase_auth') as mock_firebase:
                mock_auth = MagicMock()
                mock_firebase.return_value = mock_auth
                
                # Mock Firebase user creation
                mock_firebase_user = MagicMock()
                mock_firebase_user.uid = f'firebase_uid_{uuid.uuid4()}'
                mock_auth.create_user.return_value = mock_firebase_user
                mock_auth.create_custom_token.return_value = b'mock_firebase_token'
                
                verify_response = self.client.post('/api/v1/auth/phone-register/verify/', {
                    'session_id': session_id,
                    'otp_code': '123456'
                }, content_type='application/json')
                
                if verify_response.status_code != 201:
                    self.log_test("Registration Verify API", False, 
                                f"Verify failed with status {verify_response.status_code}")
                    return False
                
                verify_data = verify_response.json()
                if not verify_data.get('success'):
                    self.log_test("Registration Verify API", False, 
                                f"Verify API failed: {verify_data.get('message')}")
                    return False
            
            self.log_test("Registration API Flow", True, 
                        "Registration request and verify working correctly")
            return True
            
        except Exception as e:
            self.log_test("Registration API Flow", False, 
                        f"Registration API test failed: {e}")
            return False
    
    @patch('apps.authentication.otp_auth_views.TwilioOTPService')
    def test_login_api_flow(self, mock_otp_service):
        """Test OTP login API flow"""
        try:
            # Create test customer first
            customer = Customer.objects.create(
                firebase_uid=str(uuid.uuid4()),
                name=self.test_customer_data['name'],
                email=self.test_customer_data['email'],
                phone=self.test_customer_data['phone'],
                phone_verified=True
            )
            
            # Mock OTP service
            mock_service = MagicMock()
            mock_otp_service.return_value = mock_service
            
            # Test login request
            mock_service.send_otp.return_value = {
                'success': True,
                'otp_id': 'test_login_otp_123',
                'expires_in': 300
            }
            
            response = self.client.post('/api/v1/auth/phone-login/request/', {
                'phone_number': self.test_phone
            }, content_type='application/json')
            
            if response.status_code != 200:
                self.log_test("Login Request API", False, 
                            f"Request failed with status {response.status_code}")
                return False
            
            data = response.json()
            if not data.get('success'):
                self.log_test("Login Request API", False, 
                            f"Request API failed: {data.get('message')}")
                return False
            
            session_id = data.get('session_id')
            
            # Test login verification
            mock_service.verify_otp.return_value = {
                'success': True,
                'message': 'OTP verified successfully'
            }
            
            with patch('apps.authentication.otp_auth_views.get_firebase_auth') as mock_firebase:
                mock_auth = MagicMock()
                mock_firebase.return_value = mock_auth
                mock_auth.create_custom_token.return_value = b'mock_firebase_token'
                
                verify_response = self.client.post('/api/v1/auth/phone-login/verify/', {
                    'session_id': session_id,
                    'otp_code': '123456'
                }, content_type='application/json')
                
                if verify_response.status_code != 200:
                    self.log_test("Login Verify API", False, 
                                f"Verify failed with status {verify_response.status_code}")
                    return False
                
                verify_data = verify_response.json()
                if not verify_data.get('success'):
                    self.log_test("Login Verify API", False, 
                                f"Verify API failed: {verify_data.get('message')}")
                    return False
            
            self.log_test("Login API Flow", True, 
                        "Login request and verify working correctly")
            return True
            
        except Exception as e:
            self.log_test("Login API Flow", False, 
                        f"Login API test failed: {e}")
            return False
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        try:
            # Test invalid phone number
            response = self.client.post('/api/v1/auth/phone-login/request/', {
                'phone_number': 'invalid_phone'
            }, content_type='application/json')
            
            # Should handle gracefully
            if response.status_code not in [400, 404]:
                self.log_test("Error Handling - Invalid Phone", False, 
                            f"Unexpected status code: {response.status_code}")
                return False
            
            # Test missing session ID
            response = self.client.post('/api/v1/auth/phone-login/verify/', {
                'otp_code': '123456'
            }, content_type='application/json')
            
            if response.status_code != 400:
                self.log_test("Error Handling - Missing Session", False, 
                            f"Unexpected status code: {response.status_code}")
                return False
            
            # Test non-existent customer login
            response = self.client.post('/api/v1/auth/phone-login/request/', {
                'phone_number': '+919999999999'
            }, content_type='application/json')
            
            if response.status_code != 404:
                self.log_test("Error Handling - Non-existent Customer", False, 
                            f"Unexpected status code: {response.status_code}")
                return False
            
            self.log_test("Error Handling", True, 
                        "Error scenarios handled correctly")
            return True
            
        except Exception as e:
            self.log_test("Error Handling", False, 
                        f"Error handling test failed: {e}")
            return False
    
    def test_security_features(self):
        """Test security features"""
        try:
            # Test rate limiting
            customer = Customer.objects.create(
                firebase_uid=str(uuid.uuid4()),
                name="Rate Test Customer",
                email="ratetest@example.com",
                phone="+919999888777",
                otp_verification_count=10  # Exceed rate limit
            )
            
            can_request, message = customer.can_request_otp()
            if can_request:
                self.log_test("Security - Rate Limiting", False, 
                            "Rate limiting not enforced")
                return False
            
            # Test phone encryption
            encrypted_phone = encrypt_field(self.test_phone)
            if encrypted_phone == self.test_phone:
                self.log_test("Security - Phone Encryption", False, 
                            "Phone number not encrypted")
                return False
            
            self.log_test("Security Features", True, 
                        "Rate limiting and encryption working correctly")
            return True
            
        except Exception as e:
            self.log_test("Security Features", False, 
                        f"Security test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting OTP Authentication System Tests")
        print("=" * 60)
        print()
        
        # Run setup
        if not self.setup_test_data():
            print("❌ Setup failed. Aborting tests.")
            return False
        
        # Run all tests
        tests = [
            self.test_customer_model_otp_functionality,
            self.test_twilio_otp_service,
            self.test_registration_api_flow,
            self.test_login_api_flow,
            self.test_error_handling,
            self.test_security_features
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                test_name = test.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, False, f"Test execution failed: {e}")
        
        # Generate report
        self.generate_report()
        
        return True
    
    def generate_report(self):
        """Generate test report"""
        print("=" * 60)
        print("📊 TEST REPORT")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result['status'])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result['status'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print()
        
        if failed > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result['status']:
                    print(f"  - {result['test']}: {result['message']}")
            print()
        
        print("📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result['status']}: {result['test']}")
            if result['message']:
                print(f"      {result['message']}")
        
        print()
        print("🎉 OTP Authentication System Test Complete!")
        
        # Save report to file
        report_data = {
            'timestamp': timezone.now().isoformat(),
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'success_rate': f"{(passed/total*100):.1f}%"
            },
            'results': self.test_results
        }
        
        with open('otp_auth_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: otp_auth_test_report.json")


def main():
    """Main test runner"""
    print("🔐 HDFC OTP Authentication System Test Suite")
    print("Testing comprehensive OTP authentication flow with Twilio and Firebase")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: This script must be run from the Django project root directory")
        print("   (where manage.py is located)")
        sys.exit(1)
    
    # Run tests
    test_suite = OTPAuthenticationSystemTest()
    test_suite.run_all_tests()


if __name__ == '__main__':
    main()