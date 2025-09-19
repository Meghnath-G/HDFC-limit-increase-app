#!/usr/bin/env python3
"""
Minimal OTP Server for HDFC Card Limit System
Handles OTP sending and verification using Twilio
"""

import json
import random
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Simple in-memory storage for OTP (replace with Redis/database in production)
otp_storage = {}

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def standardize_phone_number(phone_number):
    """Standardize phone number to E.164 format"""
    if not phone_number:
        return phone_number
    
    # Remove all non-digit characters
    import re
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Handle Indian phone numbers
    if digits_only.startswith('91') and len(digits_only) == 12:
        return f"+{digits_only}"
    elif len(digits_only) == 10:
        return f"+91{digits_only}"
    elif digits_only.startswith('0') and len(digits_only) == 11:
        return f"+91{digits_only[1:]}"
    else:
        if not phone_number.startswith('+'):
            return f"+{digits_only}"
        return phone_number

def send_sms_simulation(phone_number, message):
    """
    Send real SMS using Twilio or simulate if credentials not available
    """
    logger.info(f"📱 SMS to {phone_number}")
    logger.info(f"   Message: {message}")
    
    # Try to send real SMS with Twilio
    try:
        # These would be your real Twilio credentials
        # For testing, we'll simulate but you can replace with real values
        TWILIO_ACCOUNT_SID = "your_account_sid"  # Replace with real SID
        TWILIO_AUTH_TOKEN = "your_auth_token"    # Replace with real token
        TWILIO_PHONE_NUMBER = "+1234567890"     # Replace with real Twilio number
        
        # Uncomment below lines and add real credentials for real SMS
        """
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        logger.info(f"✅ Real SMS sent via Twilio: {message.sid}")
        return {
            'success': True,
            'sid': message.sid,
            'status': message.status,
            'message': 'Real SMS sent via Twilio'
        }
        """
        
        # For now, simulate SMS sending
        logger.info(f"📱 SMS Simulation (replace with real Twilio)")
        time.sleep(1)  # Simulate network delay
        
        return {
            'success': True,
            'sid': f'SM{random.randint(10000000, 99999999)}',
            'status': 'sent',
            'message': 'SMS sent successfully (simulated - check console for OTP)'
        }
        
    except Exception as e:
        logger.error(f"❌ SMS sending failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/api/v1/otp/send-otp/', methods=['POST', 'OPTIONS'])
def send_otp():
    """Send OTP endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({'success': True})
    
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        card_number = data.get('card_number', '')
        card_type = data.get('card_type', 'Credit Card')
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'Phone number is required'
            }), 400
        
        # Standardize phone number
        standardized_phone = standardize_phone_number(phone_number)
        
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP with expiration
        otp_storage[standardized_phone] = {
            'otp': otp,
            'card_number': card_number[-4:] if card_number else '',
            'card_type': card_type,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=5),
            'attempts': 0
        }
        
        # Create SMS message
        message = f"Your HDFC {card_type} verification OTP is: {otp}. Valid for 5 minutes. Do not share this code with anyone."
        
        # Send SMS (simulated)
        sms_result = send_sms_simulation(standardized_phone, message)
        
        if sms_result.get('success'):
            logger.info(f"✅ OTP sent successfully to {standardized_phone}")
            
            # In development, also print OTP to console for testing
            print(f"\n🔍 DEVELOPMENT MODE - OTP for {standardized_phone}: {otp}")
            print(f"📱 Check console for OTP (SMS simulation active)")
            
            return jsonify({
                'success': True,
                'message': 'OTP sent successfully to your phone',
                'phone_number': standardized_phone,
                'expires_in': 300,
                'message_sid': sms_result.get('sid'),
                'dev_otp': otp  # Only for development - remove in production
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send SMS'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ OTP send error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/v1/otp/verify-otp/', methods=['POST', 'OPTIONS'])
def verify_otp():
    """Verify OTP endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({'success': True})
    
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        entered_otp = data.get('otp')
        
        if not phone_number or not entered_otp:
            return jsonify({
                'success': False,
                'error': 'Phone number and OTP are required'
            }), 400
        
        # Standardize phone number
        standardized_phone = standardize_phone_number(phone_number)
        
        # Get stored OTP data
        otp_data = otp_storage.get(standardized_phone)
        
        if not otp_data:
            return jsonify({
                'success': False,
                'error': 'OTP expired or not found'
            }), 400
        
        # Check expiration
        if datetime.now() > otp_data['expires_at']:
            del otp_storage[standardized_phone]
            return jsonify({
                'success': False,
                'error': 'OTP has expired'
            }), 400
        
        # Check attempt limit
        if otp_data.get('attempts', 0) >= 3:
            del otp_storage[standardized_phone]
            return jsonify({
                'success': False,
                'error': 'Too many failed attempts'
            }), 400
        
        # Verify OTP
        if otp_data['otp'] == entered_otp:
            # Clear OTP after successful verification
            del otp_storage[standardized_phone]
            
            logger.info(f"✅ OTP verified successfully for {standardized_phone}")
            
            return jsonify({
                'success': True,
                'message': 'OTP verified successfully',
                'card_type': otp_data.get('card_type'),
                'card_last_four': otp_data.get('card_number')
            })
        else:
            # Increment attempt counter
            otp_data['attempts'] = otp_data.get('attempts', 0) + 1
            
            logger.warning(f"❌ Invalid OTP for {standardized_phone}. Attempt {otp_data['attempts']}/3")
            
            return jsonify({
                'success': False,
                'error': 'Invalid OTP',
                'attempts_remaining': 3 - otp_data['attempts']
            }), 400
            
    except Exception as e:
        logger.error(f"❌ OTP verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Verification failed'
        }), 500

@app.route('/api/v1/otp/resend-otp/', methods=['POST', 'OPTIONS'])
def resend_otp():
    """Resend OTP endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({'success': True})
    
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        card_number = data.get('card_number', '')
        card_type = data.get('card_type', 'Credit Card')
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'Phone number is required'
            }), 400
        
        # Clear existing OTP
        standardized_phone = standardize_phone_number(phone_number)
        if standardized_phone in otp_storage:
            del otp_storage[standardized_phone]
        
        # Send new OTP (reuse send_otp logic)
        return send_otp()
        
    except Exception as e:
        logger.error(f"❌ OTP resend error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to resend OTP'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'HDFC OTP Service',
        'timestamp': datetime.now().isoformat(),
        'active_otps': len(otp_storage)
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'HDFC Card Limit System - OTP Service',
        'version': '1.0.0',
        'endpoints': [
            '/api/v1/otp/send-otp/',
            '/api/v1/otp/verify-otp/',
            '/api/v1/otp/resend-otp/',
            '/health'
        ]
    })

if __name__ == '__main__':
    print("="*60)
    print(" 🏦 HDFC CARD LIMIT SYSTEM - OTP SERVICE")
    print("="*60)
    print(f"🚀 Starting OTP server...")
    print(f"📡 Server will run on: http://localhost:8000")
    print(f"🔧 CORS enabled for web app connectivity")
    print(f"📱 SMS simulation mode active (check console for OTPs)")
    print("="*60)
    
    app.run(host='0.0.0.0', port=8000, debug=True)