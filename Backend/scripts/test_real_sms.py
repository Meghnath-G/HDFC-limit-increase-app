#!/usr/bin/env python3
"""
Direct Twilio SMS Test Script

This script tests sending real SMS directly using Twilio API
to verify the OTP functionality works with real phone numbers.
"""

import os
import sys
import random
import json
from datetime import datetime

# Add the Django project to Python path
sys.path.append(r'D:\IvaR\HDFC\Backend\card_limit_system')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'card_limit_system.settings')

try:
    import django
    django.setup()
    
    from core.twilio_service import TwilioService
    from django.conf import settings
    
    def test_twilio_sms():
        """Test sending SMS via Twilio"""
        print("="*60)
        print(" 📱 HDFC CARD LIMIT SYSTEM - REAL SMS TEST")
        print("="*60)
        print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Configuration
        print(f"\n🔧 Twilio Configuration:")
        print(f"   Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}...") 
        print(f"   Phone Number: {settings.TWILIO_PHONE_NUMBER}")
        print(f"   Debug Mode: {settings.DEBUG}")
        
        # Initialize Twilio service
        twilio_service = TwilioService()
        
        # Get phone number from user
        print(f"\n📱 Phone Number Input:")
        phone_number = input("Enter phone number (with country code, e.g., +911234567890): ").strip()
        
        if not phone_number:
            print("❌ No phone number provided. Using default test number.")
            phone_number = "+911234567890"  # Default test number
        
        # Generate OTP
        otp = ''.join(random.choices('0123456789', k=6))
        
        # Create message
        message = f"Your HDFC Credit Card verification OTP is: {otp}. Valid for 5 minutes. Do not share this code with anyone."
        
        print(f"\n🔢 Generated OTP: {otp}")
        print(f"📞 Sending SMS to: {phone_number}")
        print(f"📝 Message: {message}")
        
        # Send SMS
        print(f"\n🚀 Sending SMS...")
        result = twilio_service.send_sms(
            to_number=phone_number,
            message=message
        )
        
        # Display results
        print(f"\n📊 SMS Send Result:")
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print(f"\n✅ SMS sent successfully!")
            print(f"   Message SID: {result.get('sid')}")
            print(f"   Status: {result.get('status')}")
            print(f"   📱 Check your phone for the OTP!")
            
            # Test OTP verification
            print(f"\n🔐 OTP Verification Test:")
            entered_otp = input(f"Enter the OTP you received (or press Enter to skip): ").strip()
            
            if entered_otp:
                if entered_otp == otp:
                    print("✅ OTP verification successful!")
                else:
                    print("❌ OTP verification failed!")
            else:
                print("⏭️  OTP verification skipped.")
                
        else:
            print(f"\n❌ SMS sending failed!")
            print(f"   Error: {result.get('error')}")
            
        print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
    
    if __name__ == "__main__":
        try:
            test_twilio_sms()
        except KeyboardInterrupt:
            print("\n\n⏹️  Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

except ImportError as e:
    print(f"❌ Django setup failed: {e}")
    print("Make sure you're running this from the correct directory with Django installed.")
except Exception as e:
    print(f"❌ Script failed: {e}")
    import traceback
    traceback.print_exc()