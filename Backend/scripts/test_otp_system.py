#!/usr/bin/env python3
"""
OTP System Demo Script

This script demonstrates the OTP system functionality for the HDFC Card Limit System.
It simulates the complete flow from card details to OTP verification.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
PHONE_NUMBER = "+911234567890"
CARD_NUMBER = "1234567890123456"
CARD_TYPE = "Credit Card"

def print_section(title):
    """Print a section header."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def send_otp_test():
    """Test sending OTP via SMS."""
    print_section("📱 SENDING OTP")
    
    url = f"{BASE_URL}/otp/send-otp/"
    payload = {
        "phone_number": PHONE_NUMBER,
        "card_number": CARD_NUMBER,
        "card_type": CARD_TYPE,
        "message_type": "card_verification"
    }
    
    print(f"🔄 Sending OTP to: {PHONE_NUMBER}")
    print(f"📋 Card Type: {CARD_TYPE}")
    print(f"💳 Card Number: ***{CARD_NUMBER[-4:]}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📤 Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print("\n✅ OTP sent successfully!")
            if 'otp_debug' in result:
                print(f"🔍 Debug OTP: {result['otp_debug']}")
                return result['otp_debug']
            return "123456"  # Default for demo
        else:
            print(f"❌ Failed to send OTP: {result.get('error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def verify_otp_test(otp):
    """Test OTP verification."""
    print_section("🔐 VERIFYING OTP")
    
    url = f"{BASE_URL}/otp/verify-otp/"
    payload = {
        "phone_number": PHONE_NUMBER,
        "otp": otp
    }
    
    print(f"🔢 Verifying OTP: {otp}")
    print(f"📱 Phone: {PHONE_NUMBER}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📤 Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print("\n✅ OTP verified successfully!")
            return True
        else:
            print(f"❌ OTP verification failed: {result.get('error')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def resend_otp_test():
    """Test resending OTP."""
    print_section("🔄 RESENDING OTP")
    
    url = f"{BASE_URL}/otp/resend-otp/"
    payload = {
        "phone_number": PHONE_NUMBER,
        "card_number": CARD_NUMBER,
        "card_type": CARD_TYPE
    }
    
    print(f"🔄 Resending OTP to: {PHONE_NUMBER}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📤 Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print("\n✅ OTP resent successfully!")
            if 'otp_debug' in result:
                print(f"🔍 New Debug OTP: {result['otp_debug']}")
                return result['otp_debug']
            return "654321"  # Default for demo
        else:
            print(f"❌ Failed to resend OTP: {result.get('error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_invalid_otp():
    """Test invalid OTP verification."""
    print_section("❌ TESTING INVALID OTP")
    
    url = f"{BASE_URL}/otp/verify-otp/"
    payload = {
        "phone_number": PHONE_NUMBER,
        "otp": "000000"  # Invalid OTP
    }
    
    print(f"🔢 Testing invalid OTP: 000000")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📤 Response: {json.dumps(result, indent=2)}")
        
        if not result.get('success'):
            print("\n✅ Invalid OTP correctly rejected!")
            return True
        else:
            print("❌ Invalid OTP was accepted (this shouldn't happen)")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Run the complete OTP system demo."""
    print_section("🏦 HDFC CARD LIMIT SYSTEM - OTP DEMO")
    print(f"🕐 Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BASE_URL}")
    
    # Step 1: Send OTP
    otp = send_otp_test()
    if not otp:
        print("\n❌ Demo failed at OTP sending step")
        return
    
    time.sleep(2)  # Wait a bit
    
    # Step 2: Test invalid OTP
    test_invalid_otp()
    
    time.sleep(2)  # Wait a bit
    
    # Step 3: Verify correct OTP
    if verify_otp_test(otp):
        print("\n🎉 OTP verification successful!")
    else:
        print("\n❌ OTP verification failed")
        
        # Step 4: Test resend OTP
        time.sleep(2)
        new_otp = resend_otp_test()
        if new_otp:
            time.sleep(2)
            verify_otp_test(new_otp)
    
    print_section("✅ DEMO COMPLETED")
    print(f"🕐 Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")