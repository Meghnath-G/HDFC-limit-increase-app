# Twilio OTP Configuration and Testing Guide

## 🚀 Quick Setup Instructions

### Step 1: Get Twilio Credentials

1. **Sign up for Twilio** (if you haven't already):
   - Go to [Twilio Console](https://console.twilio.com/)
   - Sign up or log in to your account

2. **Get your Account SID and Auth Token**:
   - In the Twilio Console dashboard, you'll see:
     - **Account SID**: Your unique account identifier
     - **Auth Token**: Your authentication token (click to reveal)

3. **Get a Twilio Phone Number**:
   - Go to **Phone Numbers** > **Manage** > **Buy a number**
   - Choose a number from your country (India: +91, US: +1, etc.)
   - For India specifically, you might need SMS-enabled numbers

4. **Optional: Set up Verify Service** (Recommended for production):
   - Go to **Verify** > **Services** > **Create new Service**
   - Copy the **Verify SID** for enhanced OTP features

### Step 2: Update .env Configuration

Update your `.env` file with real credentials:

```bash
# Twilio Configuration for SMS/OTP (Production Ready)
TWILIO_ACCOUNT_SID=AC1234567890abcdef1234567890abcdef  # Your actual Account SID
TWILIO_AUTH_TOKEN=your_actual_auth_token_here           # Your actual Auth Token
TWILIO_PHONE_NUMBER=+1234567890                        # Your Twilio phone number
TWILIO_VERIFY_SID=VA1234567890abcdef1234567890abcdef   # Optional: Verify Service SID
```

### Step 3: Test Twilio Integration

## 🧪 Testing Instructions

### Backend Testing

#### 1. Test Twilio Connection
```bash
cd "d:\IvaR\HDFC\Backend\card_limit_system"
python test_twilio_connection.py
```

#### 2. Test OTP Send API
```bash
curl -X POST http://localhost:8000/api/otp/twilio/send/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "customer_id": "test_customer_123",
    "purpose": "authentication"
  }'
```

#### 3. Test OTP Verify API
```bash
curl -X POST http://localhost:8000/api/otp/twilio/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "otp_id": "your_otp_id_from_send_response",
    "otp_code": "123456",
    "phone_number": "+919876543210"
  }'
```

#### 4. Test Health Check
```bash
curl http://localhost:8000/api/otp/twilio/health/
```

### Frontend Testing

#### 1. Test Flutter OTP Widget
```dart
// Add this to your test screen
TwilioOtpWidget(
  phoneNumber: '+919876543210',
  customerId: 'test_customer_123',
  onOtpVerified: (success, customerId) {
    print('OTP Verification: $success for $customerId');
  },
)
```

#### 2. Test OTP Service Directly
```dart
// Test sending OTP
final sendResult = await TwilioOtpService.sendOtp(
  phoneNumber: '+919876543210',
  customerId: 'test_customer_123',
);

if (sendResult.success) {
  print('OTP sent: ${sendResult.otpId}');
  
  // Test verifying OTP
  final verifyResult = await TwilioOtpService.verifyOtp(
    otpId: sendResult.otpId!,
    otpCode: '123456', // Use the OTP you received
  );
  
  print('Verification: ${verifyResult.success}');
}
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Twilio SMS Not Received
**Symptoms**: API returns success but SMS not received
**Solutions**:
- Check if the phone number is in correct international format (+91XXXXXXXXXX)
- Verify Twilio phone number has SMS capabilities
- Check Twilio logs in console for delivery status
- For trial accounts, verify the recipient number is verified in Twilio

#### 2. Invalid Credentials Error
**Symptoms**: "Authentication failed" or "Invalid credentials"
**Solutions**:
- Double-check Account SID and Auth Token in .env file
- Ensure no extra spaces or quotes in credentials
- Verify credentials are for the correct Twilio project

#### 3. Phone Number Format Issues
**Symptoms**: "Invalid phone number" error
**Solutions**:
- Use international format: +91XXXXXXXXXX for India
- Remove any spaces, dashes, or parentheses
- Ensure the number is a valid mobile number

#### 4. Rate Limiting Issues
**Symptoms**: "Rate limited" or "Too many requests"
**Solutions**:
- Wait for the cooldown period (1 minute between requests)
- Check customer OTP attempts in database
- Use the reset API for testing: `POST /api/otp/customer/{customer_id}/reset/`

#### 5. Firebase Connection Issues
**Symptoms**: OTP sent but not logged in Firebase
**Solutions**:
- Verify Firebase service account key is valid
- Check Firebase project permissions
- Ensure collections have proper security rules

### Testing with Trial Account Limitations

If using a Twilio trial account:
1. **Verified Numbers Only**: You can only send SMS to verified phone numbers
2. **Trial Message Prefix**: Messages will have "Sent from your Twilio trial account" prefix
3. **Limited Numbers**: Only one phone number available

To verify a number for trial:
1. Go to Twilio Console > **Phone Numbers** > **Manage** > **Verified Caller IDs**
2. Click **Add a new number**
3. Enter the phone number and verify via call/SMS

## 📱 Test Scenarios

### Scenario 1: New Customer Registration
```bash
# 1. Send OTP for new customer
curl -X POST http://localhost:8000/api/otp/twilio/send/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "purpose": "registration"}'

# 2. Verify OTP
curl -X POST http://localhost:8000/api/otp/twilio/verify/ \
  -H "Content-Type: application/json" \
  -d '{"otp_id": "otp_xxx", "otp_code": "123456", "phone_number": "+919876543210"}'
```

### Scenario 2: Existing Customer Login
```bash
# 1. Check customer OTP status first
curl http://localhost:8000/api/otp/customer/{customer_id}/status/

# 2. Send OTP if allowed
curl -X POST http://localhost:8000/api/otp/twilio/send/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "customer_id": "customer_uuid", "purpose": "authentication"}'
```

### Scenario 3: Rate Limiting Test
```bash
# Send multiple OTP requests quickly to test rate limiting
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/otp/twilio/send/ \
    -H "Content-Type: application/json" \
    -d '{"phone_number": "+919876543210"}' && echo ""
done
```

## 🏭 Production Considerations

### Before Going Live:

1. **Upgrade Twilio Account**: Move from trial to paid account
2. **SMS Compliance**: Ensure SMS content complies with local regulations
3. **Phone Number**: Get a dedicated phone number for your region
4. **Monitoring**: Set up Twilio webhooks for delivery status
5. **Error Handling**: Test all error scenarios thoroughly
6. **Security**: Use environment variables for all credentials
7. **Rate Limiting**: Configure appropriate rate limits for production
8. **Logging**: Ensure comprehensive logging without exposing sensitive data

### Production Environment Variables:
```bash
# Production Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_VERIFY_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Production Security
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
```

## 📊 Monitoring and Analytics

### Twilio Console Monitoring:
1. **SMS Logs**: Check delivery status in Twilio Console
2. **Usage**: Monitor SMS usage and costs
3. **Error Rates**: Track failed deliveries and errors

### Application Monitoring:
1. **OTP Success Rate**: Track verification success rates
2. **Customer Verification**: Monitor phone verification completions
3. **Rate Limiting**: Track rate limit hits and customer experience

## 🎯 Success Criteria

Your OTP system is working correctly if:
- ✅ SMS is received within 30 seconds of request
- ✅ OTP verification succeeds with correct code
- ✅ OTP verification fails with incorrect code
- ✅ Rate limiting prevents spam (max 5 OTP/day per customer)
- ✅ Customer phone is marked as verified in database
- ✅ Firebase logs show OTP activity
- ✅ Error handling works for all edge cases

## 🆘 Support and Resources

### Twilio Resources:
- [Twilio Console](https://console.twilio.com/)
- [Twilio SMS API Documentation](https://www.twilio.com/docs/sms)
- [Twilio Verify API Documentation](https://www.twilio.com/docs/verify)
- [Twilio Error Codes](https://www.twilio.com/docs/api/errors)

### Firebase Resources:
- [Firebase Console](https://console.firebase.google.com/)
- [Firestore Security Rules](https://firebase.google.com/docs/firestore/security/rules-structure)

### Support Contacts:
- Twilio Support: [support.twilio.com](https://support.twilio.com/)
- Firebase Support: [firebase.google.com/support](https://firebase.google.com/support)

---

Ready to test? Start with Step 1 to get your Twilio credentials, then follow the testing instructions! 🚀