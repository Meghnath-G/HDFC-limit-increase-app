# Frontend - Flutter Mobile Application

## 📱 Card Limit Increase System Mobile App

This folder will contain the Flutter mobile application for the HDFC Card Limit Increase System.

## 🎯 Planned Features

### 📋 **Screens to Implement**
1. **Customer Info Page** - Personal details input with validation
2. **Selection Page** - Credit Card/Debit Card/NetBanking options
3. **Details Page** - Card details or NetBanking credentials
4. **OTP Verification Page** - 6-digit OTP with 5-minute timer
5. **Success Page** - Confirmation with reference number
6. **Request History Page** - Past 12 months of requests
7. **Profile Management Page** - Update customer information

### 🛠️ **Technical Stack**
- **Framework**: Flutter 3.x with Dart 3.x
- **UI**: Material Design 3 components
- **State Management**: Riverpod
- **Authentication**: Firebase Auth SDK
- **HTTP Client**: Dio with retry logic
- **Local Storage**: SQLite for offline capability
- **Push Notifications**: OneSignal Flutter SDK
- **Form Validation**: Real-time with regex patterns

### 🔄 **User Flow**
```
App Launch → Firebase Auth Check → Login/Register
    ↓
Dashboard → Select Request Type → Enter Details
    ↓
OTP Verification → Success Confirmation
    ↓
Push Notification → Status Updates
```

### 🔐 **Security Features**
- Firebase Authentication integration
- Secure API communication with JWT tokens
- Local data encryption for offline storage
- Biometric authentication (where supported)
- Session timeout management

## 📖 **Documentation References**
- **API Contracts**: `../Docs/specs/001-generate-a-flutter/contracts/`
- **Data Models**: `../Docs/specs/001-generate-a-flutter/data-model.md`
- **Quickstart Guide**: `../Docs/specs/001-generate-a-flutter/quickstart.md`

## 🚀 **Getting Started**
1. Install Flutter SDK 3.x
2. Run `flutter pub get` to install dependencies
3. Configure Firebase project
4. Set up OneSignal for push notifications
5. Configure API base URL for backend connection

---

**Status**: Ready for Implementation  
**API Backend**: Available at `../Backend/`