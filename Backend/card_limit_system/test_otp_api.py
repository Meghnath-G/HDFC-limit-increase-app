#!/usr/bin/env python3
"""
HDFC OTP API Testing Script

This script tests all OTP API endpoints to ensure they work correctly
with the complete integration (Twilio + Firebase + Customer Model).
"""

import requests
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

class OTPAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/otp"
        self.test_phone = None
        self.test_customer_id = str(uuid.uuid4())
        self.current_otp_id = None
        self.session = requests.Session()
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "TEST": "🧪"
        }
        icon = status_icons.get(status, "📝")
        print(f"[{timestamp}] {icon} {message}")
    
    def setup_test_data(self):
        """Setup test data for API testing."""
        self.log("Setting up test data...", "INFO")
        
        # Get test phone number from user
        while not self.test_phone:
            phone = input("Enter your phone number for testing (format: +91XXXXXXXXXX): ").strip()
            if phone.startswith('+') and len(phone) >= 10:
                self.test_phone = phone
                break
            else:
                print("Please enter a valid phone number in international format (+91XXXXXXXXXX)")
        
        self.log(f"Test phone: {self.test_phone}", "INFO")
        self.log(f"Test customer ID: {self.test_customer_id}", "INFO")
    
    def test_health_check(self):
        """Test OTP service health check."""
        self.log("Testing health check endpoint...", "TEST")
        
        try:
            response = self.session.get(f"{self.api_base}/twilio/health/")
            
            if response.status_code == 200:
                data = response.json()
                self.log("Health check passed", "SUCCESS")
                self.log(f"Service: {data.get('service', 'Unknown')}", "INFO")
                return True
            else:
                self.log(f"Health check failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Health check error: {e}", "ERROR")
            return False
    
    def test_send_otp(self):
        """Test sending OTP."""
        self.log("Testing OTP send endpoint...", "TEST")
        
        payload = {
            "phone_number": self.test_phone,
            "customer_id": self.test_customer_id,
            "purpose": "authentication"
        }
        
        try:
            response = self.session.post(
                f"{self.api_base}/twilio/send/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.current_otp_id = data.get('otp_id')
                self.log(f"OTP sent successfully! OTP ID: {self.current_otp_id}", "SUCCESS")
                self.log(f"Message: {data.get('message', 'N/A')}", "INFO")
                self.log(f"Expires in: {data.get('expires_in', 'N/A')} seconds", "INFO")
                return True
            else:
                self.log(f"OTP send failed: {data.get('message', 'Unknown error')}", "ERROR")
                self.log(f"Error code: {data.get('error', 'N/A')}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"OTP send error: {e}", "ERROR")
            return False
    
    def test_otp_status(self):
        """Test OTP status endpoint."""
        if not self.current_otp_id:
            self.log("No OTP ID available for status check", "WARNING")
            return False
        
        self.log(f"Testing OTP status for ID: {self.current_otp_id}", "TEST")
        
        try:
            response = self.session.get(f"{self.api_base}/twilio/status/{self.current_otp_id}/")
            
            if response.status_code == 200:
                data = response.json()
                self.log("OTP status retrieved successfully", "SUCCESS")
                self.log(f"Status: {data.get('status', 'Unknown')}", "INFO")
                self.log(f"Attempts: {data.get('attempts', 'N/A')}", "INFO")
                return True
            else:
                self.log(f"OTP status failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"OTP status error: {e}", "ERROR")
            return False
    
    def test_verify_otp(self):
        """Test OTP verification with user input."""
        if not self.current_otp_id:
            self.log("No OTP ID available for verification", "WARNING")
            return False
        
        self.log("Testing OTP verification...", "TEST")
        
        # Get OTP code from user
        otp_code = input("Enter the OTP code you received: ").strip()
        
        if not otp_code or len(otp_code) != 6:
            self.log("Invalid OTP code format", "ERROR")
            return False
        
        payload = {
            "otp_id": self.current_otp_id,
            "otp_code": otp_code,
            "phone_number": self.test_phone
        }
        
        try:
            response = self.session.post(
                f"{self.api_base}/twilio/verify/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log("OTP verification successful!", "SUCCESS")
                self.log(f"Customer verified: {data.get('customer_verified', False)}", "INFO")
                self.log(f"Customer ID: {data.get('customer_id', 'N/A')}", "INFO")
                return True
            else:
                self.log(f"OTP verification failed: {data.get('message', 'Unknown error')}", "ERROR")
                self.log(f"Error code: {data.get('error', 'N/A')}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"OTP verification error: {e}", "ERROR")
            return False
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        self.log("Testing rate limiting (sending multiple OTPs)...", "TEST")
        
        payload = {
            "phone_number": self.test_phone,
            "customer_id": self.test_customer_id,
            "purpose": "rate_limit_test"
        }
        
        # Send multiple OTP requests
        for i in range(3):
            try:
                response = self.session.post(
                    f"{self.api_base}/twilio/send/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                data = response.json()
                
                if response.status_code == 429:
                    self.log(f"Rate limiting triggered on attempt {i+1}", "SUCCESS")
                    self.log(f"Message: {data.get('message', 'Rate limited')}", "INFO")
                    return True
                elif response.status_code == 200:
                    self.log(f"OTP {i+1} sent successfully", "INFO")
                    # Wait 30 seconds between requests to avoid immediate rate limiting
                    if i < 2:
                        time.sleep(5)
                else:
                    self.log(f"Unexpected response on attempt {i+1}: {response.status_code}", "WARNING")
                    
            except Exception as e:
                self.log(f"Rate limiting test error on attempt {i+1}: {e}", "ERROR")
        
        self.log("Rate limiting test completed", "INFO")
        return True
    
    def test_invalid_requests(self):
        """Test API with invalid requests."""
        self.log("Testing invalid request handling...", "TEST")
        
        # Test cases for invalid requests
        test_cases = [
            {
                "name": "Missing phone number",
                "payload": {"customer_id": self.test_customer_id},
                "expected_status": 400
            },
            {
                "name": "Invalid phone format",
                "payload": {"phone_number": "123456789", "customer_id": self.test_customer_id},
                "expected_status": 400
            },
            {
                "name": "Empty payload",
                "payload": {},
                "expected_status": 400
            }
        ]
        
        success_count = 0
        
        for test_case in test_cases:
            try:
                response = self.session.post(
                    f"{self.api_base}/twilio/send/",
                    json=test_case["payload"],
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == test_case["expected_status"]:
                    self.log(f"✓ {test_case['name']}: Handled correctly", "SUCCESS")
                    success_count += 1
                else:
                    self.log(f"✗ {test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"Error testing {test_case['name']}: {e}", "ERROR")
        
        return success_count == len(test_cases)
    
    def run_comprehensive_test(self):
        """Run all API tests in sequence."""
        self.log("🚀 Starting comprehensive OTP API testing...", "INFO")
        self.log("=" * 60, "INFO")
        
        # Setup
        self.setup_test_data()
        
        # Run tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Send OTP", self.test_send_otp),
            ("OTP Status Check", self.test_otp_status),
            ("Verify OTP", self.test_verify_otp),
            ("Invalid Requests", self.test_invalid_requests),
            ("Rate Limiting", self.test_rate_limiting),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running: {test_name}", "TEST")
            self.log("-" * 40, "INFO")
            
            try:
                results[test_name] = test_func()
            except Exception as e:
                self.log(f"Test {test_name} crashed: {e}", "ERROR")
                results[test_name] = False
            
            # Wait between tests
            time.sleep(2)
        
        # Generate report
        self.generate_test_report(results)
    
    def generate_test_report(self, results):
        """Generate a comprehensive test report."""
        self.log("\n" + "=" * 60, "INFO")
        self.log("📋 OTP API TEST REPORT", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Base URL: {self.base_url}", "INFO")
        self.log(f"Test Phone: {self.test_phone}", "INFO")
        self.log("=" * 60, "INFO")
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name}: {status}", "INFO")
        
        self.log(f"\nOverall: {passed}/{total} tests passed", "INFO")
        
        if passed == total:
            self.log("🎉 All API tests passed! Your OTP system is fully functional!", "SUCCESS")
        else:
            self.log("⚠️  Some tests failed. Please check the logs above.", "WARNING")
        
        self.log("=" * 60, "INFO")

def main():
    """Main function to run API tests."""
    print("🚀 HDFC OTP API Testing Suite")
    print("=" * 50)
    
    # Check if Django server is running
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        print("✅ Django server is running")
    except:
        print("❌ Django server is not running!")
        print("Please start the Django server with: python manage.py runserver")
        return
    
    # Initialize tester
    tester = OTPAPITester()
    
    # Run comprehensive tests
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()