#!/usr/bin/env python3
"""
OTP Server - Flask backend for handling OTP operations
Provides APIs for sending, verifying, and resending OTPs via SMS
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import string
import time
import re
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory storage for OTPs (use Redis or database in production)
otp_storage = {}

# Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3

class OTPManager:
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=OTP_LENGTH))
    
    @staticmethod
    def standardize_phone_number(phone):
        """Standardize phone number format"""
        # Remove all non-digit characters
        phone = re.sub(r'\D', '', phone)
        
        # Add country code if not present
        if len(phone) == 10:
            phone = '+91' + phone
        elif len(phone) == 11 and phone.startswith('91'):
            phone = '+' + phone
        elif not phone.startswith('+'):
            phone = '+91' + phone[-10:]
        
        return phone
    
    @staticmethod
    def store_otp(phone, otp):
        """Store OTP with expiry and attempt tracking"""
        expiry_time = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        otp_storage[phone] = {
            'otp': otp,
            'expiry': expiry_time,
            'attempts': 0,
            'created_at': datetime.now()
        }
        logger.info(f"Stored OTP for {phone}: {otp} (expires at {expiry_time})")
    
    @staticmethod
    def verify_otp(phone, provided_otp):
        """Verify OTP and manage attempts"""
        if phone not in otp_storage:
            return False, "OTP not found. Please request a new OTP."
        
        otp_data = otp_storage[phone]
        
        # Check if OTP has expired
        if datetime.now() > otp_data['expiry']:
            del otp_storage[phone]
            return False, "OTP has expired. Please request a new OTP."
        
        # Check if max attempts exceeded
        if otp_data['attempts'] >= MAX_ATTEMPTS:
            del otp_storage[phone]
            return False, "Maximum verification attempts exceeded. Please request a new OTP."
        
        # Increment attempts
        otp_data['attempts'] += 1
        
        # Verify OTP
        if otp_data['otp'] == provided_otp:
            del otp_storage[phone]  # Remove OTP after successful verification
            return True, "OTP verified successfully!"
        else:
            remaining_attempts = MAX_ATTEMPTS - otp_data['attempts']
            if remaining_attempts > 0:
                return False, f"Invalid OTP. {remaining_attempts} attempts remaining."
            else:
                del otp_storage[phone]
                return False, "Invalid OTP. Maximum attempts exceeded."
    
    @staticmethod
    def send_sms(phone, otp):
        """Send SMS using Twilio (simulated for now)"""
        # TODO: Implement actual Twilio SMS sending
        logger.info(f"SIMULATED SMS to {phone}: Your OTP is {otp}. Valid for {OTP_EXPIRY_MINUTES} minutes.")
        
        # For now, just log the OTP
        print(f"\n🚀 SMS SENT TO {phone}")
        print(f"📱 OTP: {otp}")
        print(f"⏰ Valid for {OTP_EXPIRY_MINUTES} minutes")
        print(f"🔄 Max {MAX_ATTEMPTS} verification attempts")
        print("-" * 50)
        
        return True

@app.route('/api/v1/otp/send-otp/', methods=['POST'])
def send_otp():
    """Send OTP to phone number"""
    try:
        data = request.get_json()
        if not data or 'phone_number' not in data:
            return jsonify({
                'success': False,
                'error': 'Phone number is required'
            }), 400
        
        phone = OTPManager.standardize_phone_number(data['phone_number'])
        
        # Validate phone number format
        if not re.match(r'^\+91\d{10}$', phone):
            return jsonify({
                'success': False,
                'error': 'Invalid phone number format'
            }), 400
        
        # Generate and store OTP
        otp = OTPManager.generate_otp()
        OTPManager.store_otp(phone, otp)
        
        # Send SMS
        sms_sent = OTPManager.send_sms(phone, otp)
        
        if sms_sent:
            return jsonify({
                'success': True,
                'message': f'OTP sent successfully to {phone}',
                'phone_number': phone,
                'expires_in_minutes': OTP_EXPIRY_MINUTES
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send SMS'
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/v1/otp/verify-otp/', methods=['POST'])
def verify_otp():
    """Verify OTP"""
    try:
        data = request.get_json()
        if not data or 'phone_number' not in data or 'otp' not in data:
            return jsonify({
                'success': False,
                'error': 'Phone number and OTP are required'
            }), 400
        
        phone = OTPManager.standardize_phone_number(data['phone_number'])
        provided_otp = data['otp'].strip()
        
        # Verify OTP
        is_valid, message = OTPManager.verify_otp(phone, provided_otp)
        
        return jsonify({
            'success': is_valid,
            'message': message,
            'verified': is_valid
        })
        
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/v1/otp/resend-otp/', methods=['POST'])
def resend_otp():
    """Resend OTP to phone number"""
    try:
        data = request.get_json()
        if not data or 'phone_number' not in data:
            return jsonify({
                'success': False,
                'error': 'Phone number is required'
            }), 400
        
        phone = OTPManager.standardize_phone_number(data['phone_number'])
        
        # Remove existing OTP if any
        if phone in otp_storage:
            del otp_storage[phone]
        
        # Generate and store new OTP
        otp = OTPManager.generate_otp()
        OTPManager.store_otp(phone, otp)
        
        # Send SMS
        sms_sent = OTPManager.send_sms(phone, otp)
        
        if sms_sent:
            return jsonify({
                'success': True,
                'message': f'OTP resent successfully to {phone}',
                'phone_number': phone,
                'expires_in_minutes': OTP_EXPIRY_MINUTES
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to resend SMS'
            }), 500
            
    except Exception as e:
        logger.error(f"Error resending OTP: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/v1/health/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'OTP Server',
        'timestamp': datetime.now().isoformat(),
        'active_otps': len(otp_storage)
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'OTP Server is running',
        'version': '1.0.0',
        'endpoints': [
            'POST /api/v1/otp/send-otp/',
            'POST /api/v1/otp/verify-otp/',
            'POST /api/v1/otp/resend-otp/',
            'GET /api/v1/health/'
        ]
    })

if __name__ == '__main__':
    print("🚀 Starting OTP Server...")
    print("📱 SMS Integration: Twilio (Simulated)")
    print("🌐 CORS: Enabled for Flutter web app")
    print("📞 Supported: Indian phone numbers (+91)")
    print("⏰ OTP Expiry: 5 minutes")
    print("🔄 Max Attempts: 3")
    print("-" * 50)
    
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True
    )