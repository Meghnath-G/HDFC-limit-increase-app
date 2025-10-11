#!/usr/bin/env python3
"""
Twilio OTP Connection Test Script

This script tests the Twilio configuration and basic OTP functionality
without requiring the full Django environment.
"""

import os
import sys
from pathlib import Path
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import json
from datetime import datetime

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

def load_env_file():
    """Load environment variables from .env file."""
    env_file = project_dir / '.env'
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    env_vars[key] = value
                    os.environ[key] = value
    
    return env_vars

def test_twilio_credentials():
    """Test Twilio credentials and connection."""
    print("🔧 Testing Twilio Credentials...")
    
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    # Check if credentials are present
    if not account_sid:
        print("❌ TWILIO_ACCOUNT_SID not found in environment")
        return False
    
    if not auth_token:
        print("❌ TWILIO_AUTH_TOKEN not found in environment")
        return False
    
    if not phone_number:
        print("❌ TWILIO_PHONE_NUMBER not found in environment")
        return False
    
    # Check credential format
    if not account_sid.startswith('AC'):
        print(f"❌ Invalid Account SID format: {account_sid[:10]}...")
        return False
    
    if len(auth_token) < 30:
        print("❌ Auth Token appears to be incomplete")
        return False
    
    if not phone_number.startswith('+'):
        print(f"❌ Phone number should start with '+': {phone_number}")
        return False
    
    print(f"✅ Account SID: {account_sid[:10]}...")
    print(f"✅ Auth Token: {auth_token[:10]}...")
    print(f"✅ Phone Number: {phone_number}")
    
    return True

def test_twilio_connection():
    """Test actual connection to Twilio API."""
    print("\n📞 Testing Twilio API Connection...")
    
    try:
        # Initialize Twilio client
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        client = Client(account_sid, auth_token)
        
        # Test connection by fetching account info
        account = client.api.accounts(account_sid).fetch()
        
        print(f"✅ Connected to Twilio Account: {account.friendly_name}")
        print(f"✅ Account Status: {account.status}")
        print(f"✅ Account Type: {account.type}")
        
        return True
        
    except TwilioException as e:
        print(f"❌ Twilio API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_phone_number_capabilities():
    """Test if the configured phone number has SMS capabilities."""
    print("\n📱 Testing Phone Number Capabilities...")
    
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        client = Client(account_sid, auth_token)
        
        # Get phone number details
        incoming_phone_numbers = client.incoming_phone_numbers.list(
            phone_number=phone_number
        )
        
        if not incoming_phone_numbers:
            print(f"❌ Phone number {phone_number} not found in your account")
            return False
        
        phone_number_info = incoming_phone_numbers[0]
        
        print(f"✅ Phone Number: {phone_number_info.phone_number}")
        print(f"✅ Friendly Name: {phone_number_info.friendly_name or 'N/A'}")
        print(f"✅ SMS Capable: {phone_number_info.capabilities.get('sms', False)}")
        print(f"✅ Voice Capable: {phone_number_info.capabilities.get('voice', False)}")
        
        if not phone_number_info.capabilities.get('sms'):
            print("⚠️  Warning: Phone number doesn't have SMS capabilities")
            return False
        
        return True
        
    except TwilioException as e:
        print(f"❌ Error checking phone number: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def send_test_sms(test_phone_number=None):
    """Send a test SMS to verify everything works."""
    if not test_phone_number:
        test_phone_number = input("\n📲 Enter a phone number to test SMS (format: +1234567890): ").strip()
    
    if not test_phone_number:
        print("❌ No phone number provided")
        return False
    
    print(f"\n📤 Sending test SMS to {test_phone_number}...")
    
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        client = Client(account_sid, auth_token)
        
        # Send test message
        test_message = f"🎉 HDFC OTP Test - {datetime.now().strftime('%H:%M:%S')} - Your OTP system is working!"
        
        message = client.messages.create(
            body=test_message,
            from_=from_phone,
            to=test_phone_number
        )
        
        print(f"✅ SMS Sent Successfully!")
        print(f"✅ Message SID: {message.sid}")
        print(f"✅ Status: {message.status}")
        print(f"✅ To: {message.to}")
        print(f"✅ From: {message.from_}")
        
        return True
        
    except TwilioException as e:
        print(f"❌ SMS Send Error: {e}")
        if "trial" in str(e).lower():
            print("💡 Tip: For trial accounts, the recipient number must be verified in Twilio Console")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generate_test_report():
    """Generate a test report with all results."""
    print("\n" + "="*60)
    print("📋 TWILIO OTP SYSTEM TEST REPORT")
    print("="*60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Load environment variables
    env_vars = load_env_file()
    
    # Run all tests
    tests = [
        ("Credentials Check", test_twilio_credentials),
        ("API Connection", test_twilio_connection),
        ("Phone Number Capabilities", test_phone_number_capabilities),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Twilio OTP system is ready!")
        
        # Offer to send test SMS
        send_test = input("\nWould you like to send a test SMS? (y/n): ").strip().lower()
        if send_test in ['y', 'yes']:
            send_test_sms()
    else:
        print("⚠️  Some tests failed. Please check your configuration.")
        print("\n💡 Common fixes:")
        print("1. Update .env file with real Twilio credentials")
        print("2. Ensure phone number has SMS capabilities")
        print("3. For trial accounts, verify recipient numbers in Twilio Console")
    
    print("\n" + "="*60)

def main():
    """Main function to run all tests."""
    print("🚀 HDFC Twilio OTP System Test")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = project_dir / '.env'
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please create .env file with Twilio configuration")
        sys.exit(1)
    
    # Load environment variables
    load_env_file()
    
    # Generate comprehensive test report
    generate_test_report()

if __name__ == "__main__":
    main()