# HDFC Card Limit System - Firebase Migration Guide

## 🔥 Firebase Database Architecture

### Migration Overview
This system has been migrated from Oracle Database to Firebase Firestore for:
- **Better scalability** and real-time capabilities
- **Simplified deployment** without database server management
- **Built-in authentication** and security rules
- **Real-time updates** for instant data synchronization

---

## 🗄️ Firebase Collections Structure

### 1. **customers** Collection
```javascript
{
  "id": "auto-generated-doc-id",
  "firebase_uid": "auth-user-uid",
  "name": "John Doe",
  "email": "john.doe@hdfc.com",
  "phone_number": "+91-9876543210",
  "customer_id": "CUST001",
  "date_of_birth": "1990-01-15",
  "created_at": "2025-09-19T10:30:00Z",
  "updated_at": "2025-09-19T10:30:00Z",
  "is_active": true,
  "profile": {
    "address": {
      "street": "123 Banking Street",
      "city": "Mumbai",
      "state": "Maharashtra",
      "pincode": "400001"
    },
    "kyc_status": "verified",
    "income_range": "5-10L"
  }
}
```

### 2. **limit_requests** Collection
```javascript
{
  "id": "auto-generated-doc-id",
  "customer_id": "CUST001",
  "customer_ref": "/customers/{customer_doc_id}",
  "request_type": "limit_increase",
  "current_limit": 50000,
  "requested_limit": 100000,
  "reason": "Salary increase and improved credit score",
  "income_proof": "salary_slip_2025.pdf",
  "status": "pending",
  "request_date": "2025-09-19T10:30:00Z",
  "last_updated": "2025-09-19T10:30:00Z",
  "processed_by": null,
  "approval_notes": null,
  "risk_assessment": {
    "credit_score": 750,
    "debt_ratio": 0.3,
    "risk_level": "low"
  }
}
```

### 3. **notifications** Collection
```javascript
{
  "id": "auto-generated-doc-id",
  "customer_id": "CUST001",
  "title": "Limit Request Update",
  "message": "Your credit limit request has been approved",
  "notification_type": "limit_approval",
  "status": "sent",
  "sent_at": "2025-09-19T10:30:00Z",
  "read_at": null,
  "fcm_token": "device-fcm-token",
  "delivery_status": "delivered"
}
```

### 4. **audit_log** Collection
```javascript
{
  "id": "auto-generated-doc-id",
  "request_id": "limit_request_doc_id",
  "action": "status_change",
  "old_status": "pending",
  "new_status": "approved",
  "changed_by": "manager@hdfc.com",
  "changed_at": "2025-09-19T10:30:00Z",
  "reason": "Income verification completed",
  "ip_address": "192.168.1.100"
}
```

### 5. **otps** Collection
```javascript
{
  "id": "auto-generated-doc-id",
  "phone_number": "+91-9876543210",
  "otp_code": "123456",
  "purpose": "login_verification",
  "created_at": "2025-09-19T10:30:00Z",
  "expires_at": "2025-09-19T10:35:00Z",
  "verified_at": null,
  "attempts": 0,
  "max_attempts": 3,
  "is_used": false
}
```

---

## 🔧 Firebase Configuration

### Firebase Project Setup
1. **Create Firebase Project**: https://console.firebase.google.com
2. **Enable Services**:
   - Authentication (Phone, Email)
   - Firestore Database
   - Cloud Messaging (FCM)
   - Cloud Functions (optional)

### Service Account Configuration
```bash
# Download serviceAccountKey.json from Firebase Console
# Project Settings > Service Accounts > Generate New Private Key
```

### Environment Variables (.env)
```properties
# Firebase Configuration
FIREBASE_PROJECT_ID=hdfc-card-limit-system
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@hdfc-card-limit-system.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token

# API Configuration (unchanged)
API_BASE_URL=http://localhost:8000/api
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Security (unchanged)
JWT_SECRET_KEY=hdfc-jwt-secret-key-2025
JWT_EXPIRATION_HOURS=24
```

---

## 📊 Firebase Console Access

### Live Data Monitoring
1. **Firebase Console**: https://console.firebase.google.com
2. **Navigate to your project**: hdfc-card-limit-system
3. **Firestore Database**: View all collections and documents
4. **Authentication**: View registered users
5. **Cloud Messaging**: Send push notifications

### Real-time Queries in Firebase Console
```javascript
// Get recent limit requests
db.collection('limit_requests')
  .orderBy('request_date', 'desc')
  .limit(10)
  .get()

// Get pending requests
db.collection('limit_requests')
  .where('status', '==', 'pending')
  .get()

// Get customer by ID
db.collection('customers')
  .where('customer_id', '==', 'CUST001')
  .get()
```

---

## 🔄 Migration Process

### Step 1: Pre-Migration Checklist
- [x] Firebase project created and configured
- [x] Service account key downloaded
- [x] Environment variables configured
- [x] Firebase Admin SDK installed

### Step 2: Data Migration
```bash
# Run the migration script
cd Backend/card_limit_system
python manage.py migrate_oracle_to_firebase

# Verify migration
python manage.py verify_firebase_data
```

### Step 3: Switch to Firebase
```bash
# Update Django settings
# Change database configuration to use Firebase
# Restart application servers
```

---

## 🔍 Viewing Live Data

### Option 1: Firebase Console (Recommended for Managers)
- **URL**: https://console.firebase.google.com/project/hdfc-card-limit-system/firestore
- **Real-time updates**: Data appears instantly
- **Filtering**: Built-in query interface
- **Export**: Download data as JSON/CSV

### Option 2: Django Admin Dashboard
- **URL**: http://localhost:8000/admin/firebase/
- **Features**: 
  - View all collections
  - Search and filter data
  - Export reports
  - User management

### Option 3: API Endpoints (Unchanged)
```bash
# Recent requests
GET http://localhost:8000/api/limit-requests/recent/

# Customer data
GET http://localhost:8000/api/customers/

# Real-time status
GET http://localhost:8000/api/status/live/
```

---

## 🚀 Benefits of Firebase Migration

### For Development Team:
- **No database server** management required
- **Real-time synchronization** out of the box
- **Automatic scaling** based on usage
- **Built-in security** rules and authentication

### For Business Team:
- **Real-time dashboards** with instant updates
- **Mobile-first** architecture for better app performance
- **Global availability** with Firebase's CDN
- **Cost-effective** pay-per-use model

### For Operations Team:
- **Firebase Console** for easy data monitoring
- **Cloud Functions** for automated workflows
- **Integrated analytics** and performance monitoring
- **Backup and restore** built-in

---

## 📈 Performance Improvements

### Before (Oracle):
- Database server setup and maintenance
- Connection pooling management
- Manual scaling and optimization
- Complex backup procedures

### After (Firebase):
- ✅ **Zero server management**
- ✅ **Automatic scaling**
- ✅ **Real-time updates**
- ✅ **Built-in backup**
- ✅ **Global CDN**
- ✅ **Mobile optimization**

---

## 🔒 Security Features

### Firebase Authentication:
- Phone number verification
- Email/password authentication
- Multi-factor authentication (optional)
- Custom claims for role-based access

### Firestore Security Rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Customers can only read/write their own data
    match /customers/{customerId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == resource.data.firebase_uid;
    }
    
    // Only authenticated users can create limit requests
    match /limit_requests/{requestId} {
      allow read, create: if request.auth != null;
      allow update: if request.auth != null 
        && (request.auth.uid == resource.data.customer_ref.firebase_uid
            || hasRole('manager'));
    }
    
    // Only managers can access audit logs
    match /audit_log/{logId} {
      allow read, write: if request.auth != null 
        && hasRole('manager');
    }
  }
}
```

---

## 📞 Support and Troubleshooting

### Common Issues:
1. **Service Account Key**: Ensure proper JSON format and file permissions
2. **Firestore Rules**: Check security rules don't block legitimate requests
3. **API Quotas**: Monitor Firebase usage in console
4. **Real-time Updates**: Verify WebSocket connections for live features

### Migration Rollback Plan:
1. Keep Oracle database running during transition period
2. Implement dual-write to both Firebase and Oracle
3. Gradual traffic migration with monitoring
4. Rollback scripts ready if needed

**🎉 Your HDFC Card Limit System is now powered by Firebase for better scalability and real-time capabilities!**