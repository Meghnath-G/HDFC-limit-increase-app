# Card Limit Increase System

**HDFC Bank - Digital Limit Increase Platform**

A secure, production-ready mobile application that allows bank customers to request increases in their debit card, credit card, or netbanking transaction limits through a Flutter mobile app with Django backend.

## 📁 Project Structure

```
HDFC/
├── Docs/                   # 📋 All documentation, plans, and specifications
│   ├── .github/           # GitHub prompts and Copilot instructions
│   ├── .specify/          # Project templates, scripts, and constitution
│   └── specs/             # Feature specifications and implementation plans
│       └── 001-generate-a-flutter/
│           ├── plan.md              # Implementation plan
│           ├── spec.md              # Feature specification
│           ├── research.md          # Technical research
│           ├── data-model.md        # Database schema
│           ├── quickstart.md        # Testing guide
│           └── contracts/           # API contracts
│               ├── api-contracts.md
│               └── openapi.yaml
├── Frontend/              # 📱 Flutter mobile application
│   └── (To be implemented)
└── Backend/               # ⚙️ Django REST API server
    └── (To be implemented)
```

## 🎯 Project Overview

### **Business Goal**
Enable HDFC Bank customers to request card/netbanking limit increases digitally, reducing customer service calls by 60% and improving customer satisfaction through 24/7 self-service capability.

### **Technical Architecture**
- **Frontend**: Flutter 3.x mobile app with Material Design 3
- **Backend**: Django 4.x REST API with Django REST Framework
- **Database**: Oracle SQL 19c+ with AES-256 encryption
- **Authentication**: Firebase Auth with JWT validation
- **OTP Service**: Twilio Verify API for SMS/email delivery
- **Notifications**: OneSignal push notifications
- **Security**: Banking-grade security with PCI DSS compliance

## 🔄 User Workflow

```
1. Customer Registration → Firebase Auth + Email/SMS verification
2. Dashboard → Select request type (Credit Card/Debit Card/NetBanking)
3. Enter Details → Card info or NetBanking credentials
4. OTP Verification → 6-digit code via SMS/email (5-min expiry)
5. Success Confirmation → Reference number + push notification
6. Status Tracking → Real-time updates via notifications
```

## 🛡️ Security Features

- **Multi-Factor Authentication**: Firebase Auth + OTP verification
- **Data Encryption**: AES-256 for PII, TLS 1.3 for transmission
- **PCI DSS Compliance**: No full card numbers or CVV stored
- **Rate Limiting**: API protection against abuse
- **Audit Logging**: All security events tracked
- **Session Management**: 15-minute timeout, secure tokens

## 📋 Implementation Status

### ✅ Completed
- [x] **Constitutional Framework** - Security and development principles established
- [x] **Feature Specification** - Complete business requirements documented
- [x] **Technical Planning** - Architecture design and implementation plan
- [x] **API Contracts** - REST endpoints with OpenAPI 3.0 schema
- [x] **Database Design** - Oracle schema with encryption requirements
- [x] **Security Framework** - Banking compliance and protection measures

### 🚧 In Progress
- [ ] **Backend Development** - Django REST API implementation
- [ ] **Frontend Development** - Flutter mobile app creation
- [ ] **Database Setup** - Oracle schema deployment
- [ ] **Service Integration** - Firebase, Twilio, OneSignal setup

### 📚 Key Documents

| Document | Purpose | Location |
|----------|---------|----------|
| **Constitution** | Development principles & security standards | `Docs/.specify/memory/constitution.md` |
| **Feature Spec** | Business requirements & acceptance criteria | `Docs/specs/001-generate-a-flutter/spec.md` |
| **Implementation Plan** | Technical architecture & development approach | `Docs/specs/001-generate-a-flutter/plan.md` |
| **API Contracts** | REST endpoint specifications | `Docs/specs/001-generate-a-flutter/contracts/` |
| **Data Model** | Database schema & entity relationships | `Docs/specs/001-generate-a-flutter/data-model.md` |
| **Quickstart Guide** | Testing & validation procedures | `Docs/specs/001-generate-a-flutter/quickstart.md` |

## 🚀 Next Steps

1. **Backend Development** - Start with Django project setup and API implementation
2. **Database Setup** - Deploy Oracle schema with security configurations
3. **Service Integration** - Configure Firebase, Twilio, and OneSignal
4. **Frontend Development** - Create Flutter app with provided design integration
5. **Testing & Validation** - Execute quickstart guide and security validation
6. **Production Deployment** - APK generation and backend containerization

## 📞 Contact & Support

For technical questions or clarifications, refer to the detailed documentation in the `Docs/` folder or contact the development team.

---

**Last Updated**: September 17, 2025  
**Project Status**: Ready for Implementation  
**Branch**: `001-generate-a-flutter`