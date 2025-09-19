# Firebase Project Creation - Step by Step Guide

## 🔥 CREATING HDFC FIREBASE PROJECT

Follow these exact steps to create your Firebase project:

---

## Step 1: Create Firebase Project (5 minutes)

### 1.1 Open Firebase Console
- Open your browser
- Go to: **https://console.firebase.google.com/**
- Sign in with your Google account

### 1.2 Create New Project
- Click the **"Create a project"** button
- Enter project details:
  - **Project name**: `HDFC Card Limit System`
  - **Project ID**: `hdfc-card-limit-system` (Firebase will suggest this)
  - Click **"Continue"**

### 1.3 Google Analytics (Optional)
- Choose whether to enable Google Analytics
- For development: **"Not right now"** is fine
- Click **"Create project"**

### 1.4 Wait for Project Creation
- Firebase will set up your project (30-60 seconds)
- Click **"Continue"** when ready

---

## Step 2: Enable Authentication (3 minutes)

### 2.1 Go to Authentication
- In the left sidebar, click **"Authentication"**
- Click **"Get started"** button

### 2.2 Configure Sign-in Methods
- Click **"Sign-in method"** tab
- Enable these methods:

#### Enable Email/Password:
- Click **"Email/Password"**
- Toggle **"Enable"** to ON
- Click **"Save"**

#### Enable Phone Authentication:
- Click **"Phone"**
- Toggle **"Enable"** to ON
- Click **"Save"**

### 2.3 Verify Authentication Setup
- You should see:
  - ✅ Email/Password: Enabled
  - ✅ Phone: Enabled

---

## Step 3: Create Firestore Database (5 minutes)

### 3.1 Go to Firestore
- In left sidebar, click **"Firestore Database"**
- Click **"Create database"** button

### 3.2 Security Rules
- Select **"Start in test mode"** (we'll secure it later)
- Click **"Next"**

### 3.3 Database Location
- Choose **"asia-south1 (Mumbai)"** for Indian users
- Or choose your preferred region
- Click **"Done"**

### 3.4 Wait for Database Creation
- Firestore will initialize (30-60 seconds)
- You'll see an empty database interface

---

## Step 4: Download Service Account Key (IMPORTANT!)

### 4.1 Go to Project Settings
- Click the **gear icon ⚙️** next to "Project Overview"
- Select **"Project settings"**

### 4.2 Service Accounts Tab
- Click **"Service accounts"** tab
- Click **"Generate new private key"** button
- Click **"Generate key"** in the popup

### 4.3 Save the Key File
- A JSON file will download automatically
- **IMPORTANT**: Save this file as:
  - `firebase-service-account-key.json`
- **IMPORTANT**: Keep this file secure and private!

---

## Step 5: Note Your Project Details

Write down these details (you'll need them):

```
Project ID: hdfc-card-limit-system
Project Name: HDFC Card Limit System
Database Location: asia-south1 (or your chosen region)
Service Account Key: Downloaded ✅
```

---

## ✅ Firebase Project Created Successfully!

Your Firebase project is now ready with:
- ✅ Project created and configured
- ✅ Authentication enabled (Email + Phone)
- ✅ Firestore database created
- ✅ Service account key downloaded

## Next: Backend Integration

Once you've completed these steps, let me know and I'll help you:
1. Configure the backend to connect to your new Firebase project
2. Initialize the database collections
3. Test the connection
4. Create your first test user

**Ready for the next step?** 🚀