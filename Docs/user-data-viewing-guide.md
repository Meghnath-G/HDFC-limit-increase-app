# User Data Viewing Guide - HDFC Card Limit System

## 🔍 Where to View User Personal Data

When users enter their personal data through the HDFC Card Limit System mobile app, you can view and manage this data through multiple interfaces.

---

## 1. 🔥 Firebase Firestore Console (Recommended)

### Access Steps:
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your HDFC Card Limit System project
3. Click on "Firestore Database" in the left sidebar
4. Navigate through the collections to view user data

### Collection Structure:
```
📁 firestore_root/
├── 📁 customers/
│   ├── 📄 {customer_document_id}/
│   │   ├── firebase_uid: "firebase_user_id"
│   │   ├── customer_id: "CUST001"
│   │   ├── personal_info: {
│   │   │   ├── first_name: "John"
│   │   │   ├── last_name: "Doe"
│   │   │   ├── email: "encrypted_email"
│   │   │   ├── phone_number: "encrypted_phone"
│   │   │   ├── date_of_birth: "1990-05-15"
│   │   │   └── address: {
│   │   │       ├── street: "encrypted_street"
│   │   │       ├── city: "Mumbai"
│   │   │       ├── state: "Maharashtra"
│   │   │       ├── postal_code: "400001"
│   │   │       └── country: "India"
│   │   │       }
│   │   │   }
│   │   ├── account_info: {
│   │   │   ├── kyc_status: "pending|completed|rejected"
│   │   │   ├── account_type: "savings|current|premium"
│   │   │   ├── annual_income: 800000
│   │   │   └── employment_type: "salaried|business|freelancer"
│   │   │   }
│   │   ├── verification_status: {
│   │   │   ├── email_verified: true
│   │   │   ├── phone_verified: true
│   │   │   └── document_verified: false
│   │   │   }
│   │   └── metadata: {
│   │       ├── created_at: "2024-12-19T10:30:00Z"
│   │       ├── updated_at: "2024-12-19T10:30:00Z"
│   │       ├── last_login: "2024-12-19T09:15:00Z"
│   │       └── status: "active|suspended|closed"
│   │       }
│   │
├── 📁 limit_requests/
│   ├── 📄 {request_document_id}/
│   │   ├── customer_id: "CUST001"
│   │   ├── reference_number: "REQ20241219103000"
│   │   ├── request_details: {
│   │   │   ├── request_type: "credit_limit"
│   │   │   ├── current_limit: 50000
│   │   │   ├── requested_limit: 100000
│   │   │   ├── reason: "Income increase"
│   │   │   └── priority: "normal"
│   │   │   }
│   │   └── status: "pending|under_review|approved|rejected"
│   │
├── 📁 cards/
│   ├── 📄 {card_document_id}/
│   │   ├── customer_id: "CUST001"
│   │   ├── card_number_masked: "****-****-****-1234"
│   │   ├── card_type: "credit|debit"
│   │   └── current_limit: 50000
│   │
└── 📁 audit_logs/
    ├── 📄 {log_document_id}/
    │   ├── user_id: "CUST001"
    │   ├── action: "profile_update"
    │   ├── timestamp: "2024-12-19T10:30:00Z"
    │   └── details: "Updated phone number"
```

---

## 2. 🌐 API Endpoints for Data Retrieval

### Customer Data API Endpoints:
```bash
# Get all customers (Admin only)
GET /api/v1/customers/
Authorization: Bearer {firebase_token}

# Get specific customer
GET /api/v1/customers/{customer_id}/
Authorization: Bearer {firebase_token}

# Get customer profile (self)
GET /api/v1/customers/profile/
Authorization: Bearer {firebase_token}

# Search customers (Admin/CS Agent)
GET /api/v1/customers/search/?email=john@example.com
Authorization: Bearer {firebase_token}
```

### Request Data API Endpoints:
```bash
# Get customer's requests
GET /api/v1/requests/
Authorization: Bearer {firebase_token}

# Get specific request
GET /api/v1/requests/{request_id}/
Authorization: Bearer {firebase_token}

# Get request status history
GET /api/v1/requests/{request_id}/history/
Authorization: Bearer {firebase_token}
```

---

## 3. 🔧 Django Admin Interface

### Access Steps:
1. Navigate to: `http://your-backend-url/admin/`
2. Login with Django superuser credentials
3. View customer data through Django admin models

### Available Admin Sections:
- **Customers**: View and edit customer profiles
- **Limit Requests**: Manage limit increase requests  
- **Cards**: View card information
- **Audit Logs**: Track user activities
- **Notifications**: View notification history

---

## 4. 📊 Database Query Tools

### Direct Firestore Queries:
```python
# Python script to query user data
from firebase_admin import firestore
import firebase_admin

# Initialize Firebase
firebase_admin.initialize_app()
db = firestore.client()

# Get customer by email
customers = db.collection('customers').where('personal_info.email', '==', 'john@example.com').get()
for customer in customers:
    print(customer.to_dict())

# Get all requests for a customer
requests = db.collection('limit_requests').where('customer_id', '==', 'CUST001').get()
for request in requests:
    print(request.to_dict())
```

### Firebase CLI Queries:
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and set project
firebase login
firebase use your-project-id

# Query data
firebase firestore:query customers --where "personal_info.email == john@example.com"
```

---

## 5. 🔍 Real-Time Data Monitoring

### Firebase Console Real-Time View:
- In Firestore console, data updates automatically
- See live changes as users submit data
- View document creation timestamps
- Monitor data modification history

### Custom Monitoring Dashboard:
```javascript
// Real-time listener for new customer registrations
const db = firebase.firestore();

db.collection('customers')
  .orderBy('metadata.created_at', 'desc')
  .limit(10)
  .onSnapshot((snapshot) => {
    snapshot.docChanges().forEach((change) => {
      if (change.type === 'added') {
        console.log('New customer:', change.doc.data());
      }
    });
  });
```

---

## 6. 🛠️ Data Management Tools

### Django Management Commands:
```bash
# View customer data via Django command
python manage.py shell

# In Django shell:
from apps.customers.models import Customer
customers = Customer.objects.all()
for customer in customers:
    print(f"Customer: {customer.first_name} {customer.last_name}")
```

### Custom Admin Commands:
```bash
# Export customer data
python manage.py export_customers --format json --output customers.json

# View recent registrations
python manage.py list_recent_customers --days 7

# Customer statistics
python manage.py customer_stats
```

---

## 7. 🔐 Data Security and Access Control

### Role-Based Access:
- **Customer**: Can only view their own data
- **Customer Service Agent**: Can view customer data for support
- **Admin**: Full access to all customer data
- **Manager**: Can view aggregated reports and statistics

### Data Encryption:
- **Sensitive Fields**: Email, phone, address are encrypted
- **PII Protection**: Personal data masked in logs
- **Audit Trail**: All data access is logged

### GDPR Compliance:
- **Data Export**: Users can request their data
- **Data Deletion**: Users can request account deletion
- **Data Portability**: Data can be exported in standard formats

---

## 8. 📱 Mobile App Admin Panel

### Flutter Admin Interface (if implemented):
- View customer profiles
- Manage limit requests
- Send notifications
- View analytics and reports

---

## 🎯 Quick Access Summary

| **What You Want to See** | **Best Tool** | **Access Method** |
|---------------------------|---------------|-------------------|
| Latest user registrations | Firebase Console | Firestore > customers collection |
| Specific customer details | API Endpoint | GET /api/v1/customers/{id}/ |
| Limit requests | Firebase Console | Firestore > limit_requests collection |
| Real-time data changes | Firebase Console | Live updates in Firestore |
| Bulk data analysis | Django Admin | Admin interface |
| User activity logs | Firebase Console | Firestore > audit_logs collection |

---

## 🚨 Important Notes

### Data Privacy:
- Always access data through proper authentication
- Sensitive data (email, phone) is encrypted
- Follow GDPR and banking compliance requirements
- Log all administrative data access

### Performance:
- Firebase Console is best for real-time viewing
- API endpoints are best for programmatic access
- Django Admin is best for bulk operations
- Direct Firestore queries are best for complex filtering

### Security:
- All access requires proper authentication
- Role-based permissions are enforced
- Audit logs track all data access
- Use HTTPS for all data transmission

The Firebase Firestore Console is your primary interface for viewing user data in real-time, with the flexibility to use API endpoints for programmatic access and Django Admin for administrative tasks.