# Quickstart Guide: Card Limit Increase System

**Generated**: 2025-09-17 | **Feature**: 001-generate-a-flutter

## Overview
This quickstart guide provides step-by-step instructions to test the Card Limit Increase System end-to-end, from customer registration to successful limit increase request submission.

## Prerequisites

### Development Environment
- Python 3.9+ installed
- Flutter SDK 3.x installed
- Oracle SQL database access
- Firebase project setup
- Twilio account with Verify API
- OneSignal account for push notifications

### Environment Variables
```bash
# Backend (.env file)
SECRET_KEY=your_django_secret_key
DEBUG=False
DATABASE_URL=oracle://user:password@host:port/service_name
FIREBASE_ADMIN_SDK_PATH=/path/to/firebase-admin-sdk.json
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_VERIFY_SID=your_verify_service_sid
ONESIGNAL_APP_ID=your_onesignal_app_id
ONESIGNAL_REST_API_KEY=your_onesignal_api_key
ENCRYPTION_KEY=your_aes_encryption_key

# Frontend (firebase_options.dart)
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_APP_ID=your_firebase_app_id
ONESIGNAL_APP_ID=your_onesignal_app_id
API_BASE_URL=https://localhost:8000/api/v1
```

## Quick Setup (5 minutes)

### 1. Backend Setup
```bash
# Clone repository and navigate to backend
cd backend/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver 0.0.0.0:8000
```

### 2. Frontend Setup
```bash
# Navigate to frontend
cd frontend/

# Get dependencies
flutter pub get

# Run code generation (if any)
flutter packages pub run build_runner build

# Start Flutter app
flutter run
```

## End-to-End Test Scenarios

### Test Scenario 1: New Customer Registration
**Objective**: Verify complete customer registration flow

**Steps**:
1. Open the Flutter app
2. Tap "Create Account" button
3. Fill in customer information:
   - **Name**: "John Doe"
   - **Date of Birth**: "1990-01-15"
   - **Email**: "john.doe@example.com"
   - **Phone**: "+919876543210"
4. Tap "Register" button
5. Check for email verification sent
6. Check for SMS verification sent
7. Enter OTP received via SMS
8. Verify successful registration

**Expected Results**:
- ✅ Customer record created in database
- ✅ Firebase user created with UID
- ✅ Email verification sent
- ✅ SMS OTP sent and verified
- ✅ User redirected to dashboard

**API Calls Tested**:
- `POST /auth/register`
- `POST /otp/send`
- `POST /otp/verify`

### Test Scenario 2: Credit Card Limit Increase
**Objective**: Complete credit card limit increase request flow

**Prerequisites**: User logged in from Scenario 1

**Steps**:
1. From dashboard, tap "Request Limit Increase"
2. Select "Credit Card" option
3. Enter card details:
   - **Last 4 digits**: "1234"
   - **Expiry Month**: 12
   - **Expiry Year**: 2027
4. Enter requested limit: "₹50,000"
5. Tap "Submit Request"
6. Receive OTP via SMS
7. Enter OTP on verification screen
8. View success message with reference number

**Expected Results**:
- ✅ Limit request created with "pending" status
- ✅ Reference number generated (REQ-YYYYMMDD-XXXX format)
- ✅ OTP sent and verified successfully
- ✅ Push notification sent for request submission
- ✅ Request visible in history

**API Calls Tested**:
- `POST /requests/submit`
- `POST /otp/send`
- `POST /otp/verify`
- `POST /notifications/send`
- `GET /requests/history`

### Test Scenario 3: NetBanking Limit Increase
**Objective**: Complete netbanking limit increase request flow

**Prerequisites**: User logged in

**Steps**:
1. From dashboard, tap "Request Limit Increase"
2. Select "NetBanking" option
3. Enter netbanking credentials:
   - **Customer ID**: "NB123456789"
   - **Password**: "SecurePass123"
4. Enter requested limit: "₹100,000"
5. Tap "Submit Request"
6. Receive OTP via email
7. Enter OTP on verification screen
8. View success confirmation

**Expected Results**:
- ✅ NetBanking limit request created
- ✅ Email OTP sent and verified
- ✅ Request status updated to "pending"
- ✅ Notification sent to customer

**API Calls Tested**:
- `POST /requests/submit` (NetBanking variant)
- `POST /otp/send` (email channel)
- `POST /otp/verify`

### Test Scenario 4: Request Status Tracking
**Objective**: Verify request status updates and notifications

**Prerequisites**: Previous requests submitted

**Steps**:
1. Navigate to "Request History" screen
2. View list of submitted requests
3. Tap on a specific request
4. View detailed request status
5. Simulate bank approval (backend admin)
6. Verify push notification received
7. Check updated status in app

**Expected Results**:
- ✅ Request history displays correctly
- ✅ Request details show accurate information
- ✅ Status updates reflect in real-time
- ✅ Push notifications delivered
- ✅ UI updates without app restart

**API Calls Tested**:
- `GET /requests/history`
- `GET /requests/status/{id}`
- Push notification delivery

## Error Handling Test Cases

### Test Case 1: Invalid OTP
**Steps**:
1. Submit a limit request
2. Enter incorrect OTP three times
3. Verify account lockout behavior

**Expected Results**:
- ✅ Error message after each failed attempt
- ✅ Account locked after 3 attempts
- ✅ 2-minute cooldown period enforced
- ✅ New OTP can be requested after cooldown

### Test Case 2: Duplicate Requests
**Steps**:
1. Submit a credit card limit request
2. Immediately try to submit another request for same card
3. Verify rejection behavior

**Expected Results**:
- ✅ Second request rejected with error message
- ✅ 24-hour restriction enforced
- ✅ Clear error message displayed to user

### Test Case 3: Network Connectivity Issues
**Steps**:
1. Start filling limit request form
2. Disable internet connection
3. Complete form and attempt submission
4. Re-enable internet connection

**Expected Results**:
- ✅ Form data saved locally
- ✅ Offline indicator displayed
- ✅ Data synced when connection restored
- ✅ User notified of sync completion

## Performance Benchmarks

### API Response Times
Run these tests to verify performance requirements:

```bash
# Load testing with curl
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"firebase_token":"test_token"}' \
  -w "Time: %{time_total}s\n"

# Expected: < 2 seconds
```

### Mobile App Performance
1. **App Startup Time**: Should be < 3 seconds
2. **Form Validation**: Should be immediate (< 100ms)
3. **API Calls**: Should complete < 2 seconds
4. **OTP Delivery**: Should arrive < 30 seconds

## Security Validation

### Security Checklist
- [ ] All API endpoints require authentication
- [ ] JWT tokens properly validated
- [ ] PII data encrypted in database
- [ ] HTTPS enforced for all communications
- [ ] Rate limiting working correctly
- [ ] Input validation preventing injection attacks
- [ ] Audit logs capturing security events

### Security Test Commands
```bash
# Test rate limiting
for i in {1..20}; do curl -X POST http://localhost:8000/api/v1/auth/login; done

# Test SQL injection prevention
curl -X POST http://localhost:8000/api/v1/auth/register \
  -d '{"name":"'; DROP TABLE customer; --"}'

# Test unauthorized access
curl -X GET http://localhost:8000/api/v1/customers/profile
# Should return 401 Unauthorized
```

## Database Verification

### Verify Data Integrity
```sql
-- Check customer data encryption
SELECT customer_id, 
       CASE WHEN email LIKE '%@%' THEN 'UNENCRYPTED' ELSE 'ENCRYPTED' END as email_status,
       CASE WHEN phone LIKE '+91%' THEN 'UNENCRYPTED' ELSE 'ENCRYPTED' END as phone_status
FROM customer;

-- Check limit request constraints
SELECT request_id, requested_limit, status
FROM limitrequest 
WHERE requested_limit < 1000 OR requested_limit > 1000000;
-- Should return 0 rows

-- Check OTP expiry enforcement
SELECT COUNT(*) as expired_otps
FROM otplog 
WHERE expires_at < NOW() AND is_verified = false;
```

## Troubleshooting

### Common Issues

**1. Firebase Token Validation Fails**
```
Error: Invalid Firebase token
Solution: Check Firebase Admin SDK configuration and token format
```

**2. Oracle Connection Issues**
```
Error: ORA-12541: TNS:no listener
Solution: Verify Oracle service is running and connection string is correct
```

**3. OTP Not Received**
```
Error: OTP delivery failed
Solution: Check Twilio credentials and phone number format
```

**4. Push Notifications Not Working**
```
Error: OneSignal delivery failed
Solution: Verify OneSignal app ID and device registration
```

## Success Criteria

✅ **Functional Requirements Met**:
- Customer registration and authentication working
- All three request types (credit, debit, netbanking) functional
- OTP verification working for SMS and email
- Push notifications delivering successfully
- Request history and status tracking operational

✅ **Performance Requirements Met**:
- API responses under 2 seconds
- App startup under 3 seconds
- OTP delivery under 30 seconds

✅ **Security Requirements Met**:
- All data encrypted and secure
- Authentication and authorization working
- Rate limiting operational
- Audit logging functional

✅ **Ready for Production**:
- All tests passing
- Performance benchmarks met
- Security validation complete
- Documentation up to date

## Next Steps

After successful quickstart completion:
1. Run comprehensive test suite
2. Perform security penetration testing
3. Load testing with realistic user volumes
4. User acceptance testing with bank stakeholders
5. Production deployment preparation