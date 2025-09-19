# Firebase Project Setup Guide - HDFC Card Limit System

## 🚀 Creating Your Firebase Project

Since we've implemented the Firebase backend code, now we need to create the actual Firebase project to store and view user data.

---

## Step 1: Create Firebase Project

### 1. Go to Firebase Console
- Open your browser and go to: https://console.firebase.google.com/
- Sign in with your Google account

### 2. Create New Project
- Click "Create a project" or "Add project"
- Enter project details:
  - **Project name**: `hdfc-card-limit-system`
  - **Project ID**: `hdfc-card-limit-system` (or auto-generated)
  - **Location**: Choose your preferred region (e.g., asia-south1 for India)

### 3. Configure Project Settings
- **Google Analytics**: Enable or disable based on your needs
- **Terms**: Accept Firebase terms of service
- Click "Create project"

---

## Step 2: Enable Required Services

### 1. Enable Authentication
- In Firebase console, go to "Authentication"
- Click "Get started"
- Go to "Sign-in method" tab
- Enable these providers:
  - ✅ Email/Password
  - ✅ Phone (for OTP)
  - ✅ Anonymous (optional, for guest access)

### 2. Enable Firestore Database
- Go to "Firestore Database"
- Click "Create database"
- Choose "Start in test mode" (we'll update security rules later)
- Select location: `asia-south1` (Mumbai) for Indian users
- Click "Done"

### 3. Enable Cloud Messaging (for notifications)
- Go to "Cloud Messaging"
- Click "Get started"
- This will be used for push notifications

---

## Step 3: Generate Service Account Key

### 1. Go to Project Settings
- Click the gear icon ⚙️ next to "Project Overview"
- Select "Project settings"

### 2. Service Accounts Tab
- Click on "Service accounts" tab
- Click "Generate new private key"
- Download the JSON file
- **Important**: Keep this file secure and never commit to version control

### 3. Save Service Account Key
- Rename the downloaded file to: `firebase-service-account-key.json`
- Place it in your backend project root: `d:\IvaR\HDFC\Backend\card_limit_system\`
- Add to `.gitignore`:
```
firebase-service-account-key.json
*.json
```

---

## Step 4: Configure Backend with Real Firebase

### 1. Update Django Settings
Create or update `d:\IvaR\HDFC\Backend\card_limit_system\card_limit_system\firebase_settings.py`:

```python
import os
from pathlib import Path

# Firebase Configuration
FIREBASE_CONFIG = {
    'type': 'service_account',
    'project_id': 'hdfc-card-limit-system',  # Your actual project ID
    'private_key_id': 'your_private_key_id',
    'private_key': 'your_private_key',
    'client_email': 'your_service_account_email',
    'client_id': 'your_client_id',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': 'your_cert_url'
}

# Path to service account key file
BASE_DIR = Path(__file__).resolve().parent.parent
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = BASE_DIR / 'firebase-service-account-key.json'

# Firestore settings
FIRESTORE_DATABASE_ID = '(default)'
FIRESTORE_PROJECT_ID = 'hdfc-card-limit-system'
```

### 2. Update Environment Variables
Create `.env` file in backend root:
```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=hdfc-card-limit-system
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./firebase-service-account-key.json
ENVIRONMENT=development

# Security
SECRET_KEY=your_django_secret_key
DEBUG=True
```

---

## Step 5: Initialize Firestore Collections

### 1. Create Management Command
Save this as `d:\IvaR\HDFC\Backend\card_limit_system\core\management\commands\init_firestore.py`:

```python
from django.core.management.base import BaseCommand
from core.firebase_config import FirebaseService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize Firestore collections and indexes'
    
    def handle(self, *args, **options):
        self.stdout.write("Initializing Firestore collections...")
        
        try:
            firebase_service = FirebaseService()
            db = firebase_service.get_firestore_client()
            
            # Create initial collections with sample documents
            collections = [
                'customers',
                'limit_requests',
                'cards',
                'notifications',
                'otp_codes',
                'audit_logs'
            ]
            
            for collection_name in collections:
                # Create a placeholder document to initialize collection
                doc_ref = db.collection(collection_name).document('_placeholder')
                doc_ref.set({
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'purpose': 'Collection initialization',
                    'delete_me': True
                })
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Initialized collection: {collection_name}')
                )
            
            self.stdout.write(
                self.style.SUCCESS('🎉 Firestore collections initialized successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error initializing Firestore: {str(e)}')
            )
```

### 2. Run Initialization
```bash
cd "d:\IvaR\HDFC\Backend\card_limit_system"
python manage.py init_firestore
```

---

## Step 6: Test Firebase Connection

### 1. Test Firebase Connection
```bash
cd "d:\IvaR\HDFC\Backend\card_limit_system"
python manage.py test_firebase_auth
```

### 2. Create Test Customer
```bash
python manage.py shell
```

In Django shell:
```python
from core.firebase_config import FirebaseService
from datetime import datetime

# Initialize Firebase
firebase_service = FirebaseService()
db = firebase_service.get_firestore_client()

# Create test customer
test_customer = {
    'firebase_uid': 'test_user_123',
    'customer_id': 'CUST001',
    'personal_info': {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@test.com',
        'phone_number': '+919876543210',
        'date_of_birth': '1990-05-15'
    },
    'account_info': {
        'kyc_status': 'pending',
        'account_type': 'savings',
        'annual_income': 800000
    },
    'metadata': {
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'status': 'active'
    }
}

# Add to Firestore
doc_ref = db.collection('customers').add(test_customer)
print(f"Test customer created with ID: {doc_ref[1].id}")
```

---

## Step 7: View Data in Firebase Console

### Now You Can See Data!
1. Go back to Firebase Console: https://console.firebase.google.com/
2. Select your `hdfc-card-limit-system` project
3. Click "Firestore Database"
4. You should now see:
   - 📁 customers collection with your test data
   - 📁 Other collections (limit_requests, cards, etc.)

### Real-Time Data Viewing
- Any new user registrations will appear here automatically
- Data updates in real-time as users interact with your app
- You can edit, delete, or add documents directly from the console

---

## Step 8: Security Rules (Important!)

### 1. Update Firestore Security Rules
In Firebase Console > Firestore Database > Rules, replace with:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Customers can only access their own data
    match /customers/{customerId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == resource.data.firebase_uid;
    }
    
    // Limit requests - customers can only access their own
    match /limit_requests/{requestId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == resource.data.firebase_uid;
    }
    
    // Admin access (add your admin UIDs)
    match /{document=**} {
      allow read, write: if request.auth != null 
        && request.auth.uid in ['admin_uid_1', 'admin_uid_2'];
    }
  }
}
```

### 2. Publish Rules
- Click "Publish" to activate the security rules

---

## 🎉 Project Created Successfully!

Your Firebase project is now ready! You should be able to:

✅ **See the project** in Firebase Console  
✅ **View Firestore collections** with real data  
✅ **Monitor user registrations** in real-time  
✅ **Manage user data** through the console  
✅ **Test the backend integration** with live Firebase  

## Next Steps:
1. Replace the service account key in your backend
2. Test user registration from your mobile app
3. Watch data appear in Firestore console in real-time!

Let me know if you need help with any of these steps!