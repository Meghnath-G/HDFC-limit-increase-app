import os
import json
from pathlib import Path

# Firebase Configuration for HDFC Card Limit System
# This file will be updated with your actual Firebase project details

# Path to service account key file
BASE_DIR = Path(__file__).resolve().parent.parent
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = BASE_DIR / 'firebase-service-account-key.json'

# Firebase Project Configuration
# UPDATE THESE VALUES AFTER CREATING YOUR FIREBASE PROJECT:
FIREBASE_CONFIG = {
    'project_id': 'hdfc-card-limit-system',  # Your actual project ID from Firebase
    'type': 'service_account',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
}

# Firestore Database Settings
FIRESTORE_DATABASE_ID = '(default)'
FIRESTORE_PROJECT_ID = 'hdfc-card-limit-system'  # Update with your project ID

# Firebase Admin SDK Configuration
def get_firebase_credentials():
    """
    Get Firebase credentials from service account key file.
    This will be used after you download the service account key.
    """
    if FIREBASE_SERVICE_ACCOUNT_KEY_PATH.exists():
        with open(FIREBASE_SERVICE_ACCOUNT_KEY_PATH, 'r') as f:
            return json.load(f)
    else:
        # Development mode - return None if key file doesn't exist yet
        print("⚠️  Firebase service account key not found. Using mock mode for development.")
        return None

# Environment-specific settings
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    # Production Firebase settings
    FIREBASE_AUTH_DOMAIN = f"{FIRESTORE_PROJECT_ID}.firebaseapp.com"
    FIREBASE_DATABASE_URL = f"https://{FIRESTORE_PROJECT_ID}.firebaseio.com"
    FIREBASE_STORAGE_BUCKET = f"{FIRESTORE_PROJECT_ID}.appspot.com"
else:
    # Development Firebase settings
    FIREBASE_AUTH_DOMAIN = f"{FIRESTORE_PROJECT_ID}.firebaseapp.com"
    FIREBASE_DATABASE_URL = f"https://{FIRESTORE_PROJECT_ID}.firebaseio.com"
    FIREBASE_STORAGE_BUCKET = f"{FIRESTORE_PROJECT_ID}.appspot.com"

# Security settings
FIREBASE_ADMIN_VERIFY_ID_TOKENS = True
FIREBASE_AUTH_CACHE_TIMEOUT = 3600  # 1 hour
FIREBASE_MAX_RETRIES = 3
FIREBASE_TIMEOUT = 30  # seconds

print(f"🔥 Firebase configuration loaded for project: {FIRESTORE_PROJECT_ID}")
print(f"📁 Service account key path: {FIREBASE_SERVICE_ACCOUNT_KEY_PATH}")
print(f"🌍 Environment: {ENVIRONMENT}")