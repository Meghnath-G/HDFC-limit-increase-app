# Implementation Plan: Card Limit Increase System

**Branch**: `001-generate-a-flutter` | **Date**: 2025-09-17 | **Spec**: [D:\IvaR\HDFC\specs\001-generate-a-flutter\spec.md]
**Input**: Feature specification from `/specs/001-generate-a-flutter/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → Feature spec loaded: Card Limit Increase System
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Project Type: mobile (Flutter app + Django API backend)
   → Structure Decision: Option 3 (Mobile + API)
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → Constitution requirements identified and documented
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → Technical stack clarified from user input
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, .github/copilot-instructions.md
7. Re-evaluate Constitution Check section
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Primary requirement: Build a full-stack mobile application for bank customers to request card/netbanking limit increases through secure mobile interface with OTP verification.

Technical approach: Flutter mobile app with Django REST API backend, Firebase Authentication, Oracle SQL database, Twilio OTP service, and OneSignal push notifications. Focus on backend development first, then frontend integration.

## Technical Context
**Language/Version**: Flutter 3.x with Dart 3.x (Frontend), Python 3.9+ with Django 4.x (Backend)
**Primary Dependencies**: Flutter SDK, Django REST Framework, Firebase Auth SDK, cx_Oracle, Twilio SDK, OneSignal SDK
**Storage**: Oracle SQL 19c+ for data persistence, Redis for caching and session storage
**Testing**: Flutter test framework (Frontend), pytest with DRF test cases (Backend)
**Target Platform**: Android mobile app (.apk), Backend hosted on cloud (Docker optional)
**Project Type**: mobile - determines Mobile + API structure
**Performance Goals**: API response < 2s, Mobile app startup < 3s, OTP delivery < 30s
**Constraints**: 95% security compliance, 5-minute OTP expiry, 15-minute session timeout, offline capability
**Scale/Scope**: Bank-grade security, ₹1,000-₹10,00,000 limit range, 12-month request history

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Security-First Architecture**: ✅
- Firebase Authentication for all user sessions
- JWT token validation on API endpoints
- AES-256 encryption for PII data
- TLS 1.3 for all communications
- No hardcoded credentials in source code

**Mobile-First Design**: ✅
- Flutter responsive design for multiple screen sizes
- Offline capability with sync when online
- Clear user flow: Customer Info → Selection → Details → OTP → Success
- Immediate form validation feedback

**API-Driven Backend**: ✅
- Django REST Framework for all data services
- RESTful endpoints with proper HTTP status codes
- JSON request/response with standardized error handling
- Oracle SQL as single source of truth
- OpenAPI/Swagger documentation required

**Real-Time Communication**: ✅
- Twilio integration for OTP delivery via SMS/email
- OneSignal push notifications for status updates
- 5-minute OTP expiry timeout handling

**Production Readiness**: ✅
- Docker containerization for backend deployment
- APK generation with proper signing
- Environment-specific configuration management
- Comprehensive logging and monitoring

## Project Structure

### Documentation (this feature)
```
specs/001-generate-a-flutter/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 3: Mobile + API (Flutter + Django)
backend/
├── src/
│   ├── models/          # Customer, CardDetail, LimitRequest, OTPLog
│   ├── services/        # OTP, Notifications, Authentication
│   ├── api/            # REST endpoints
│   └── utils/          # Encryption, validation helpers
├── tests/
│   ├── contract/       # API contract tests
│   ├── integration/    # End-to-end tests
│   └── unit/          # Model and service tests
├── requirements.txt
├── Dockerfile
└── manage.py

frontend/
├── lib/
│   ├── models/         # Data models
│   ├── services/       # API clients, Auth service
│   ├── screens/        # UI screens (Customer Info, Selection, etc.)
│   ├── widgets/        # Reusable UI components
│   └── utils/         # Helpers, validators
├── test/
│   ├── widget_test/   # UI tests
│   ├── integration_test/ # E2E tests
│   └── unit_test/     # Logic tests
├── pubspec.yaml
├── android/
└── ios/ (future)
```

**Structure Decision**: Option 3 (Mobile + API) - Flutter frontend with Django backend API

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Firebase Auth integration patterns with Django
   - Oracle database optimization for mobile API responses
   - OneSignal implementation best practices for Flutter
   - Twilio verify API integration patterns
   - Security best practices for banking applications

2. **Generate and dispatch research agents**:
   ```
   Task: "Research Firebase Auth JWT validation in Django REST Framework"
   Task: "Find best practices for Oracle SQL optimization in Django with cx_Oracle"
   Task: "Research OneSignal push notification implementation in Flutter and Django"
   Task: "Find Twilio Verify API integration patterns for OTP delivery"
   Task: "Research PCI DSS compliance requirements for mobile banking apps"
   Task: "Find secure API design patterns for financial applications"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all technical decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Customer: id, firebase_uid, name, dob, email, phone, created_at
   - CardDetail: id, customer_id, card_type, last4, expiry_month, expiry_year, token_id
   - LimitRequest: id, customer_id, card_detail_id, netbanking_id, requested_limit, status, created_at
   - OTPLog: id, customer_id, otp_hash, sent_to, channel, created_at, expires_at, attempts_count
   - Validation rules and state transitions

2. **Generate API contracts** from functional requirements:
   - POST /api/auth/register → Customer registration
   - POST /api/auth/login → Firebase token validation
   - POST /api/customers/profile → Customer profile management
   - POST /api/requests/submit → Limit increase request submission
   - POST /api/otp/send → OTP generation and delivery
   - POST /api/otp/verify → OTP validation
   - GET /api/requests/status/{id} → Request status checking
   - POST /api/notifications/send → Push notification delivery
   - OpenAPI schema output to `/contracts/`

3. **Generate contract tests** from contracts:
   - Test files for each endpoint
   - Assert request/response schemas
   - Authentication and authorization tests
   - Error handling tests

4. **Extract test scenarios** from user stories:
   - Registration and authentication flow
   - Card limit increase request flow
   - NetBanking limit increase request flow
   - OTP verification flow
   - Push notification flow

5. **Update agent file incrementally**:
   - Run update-agent-context.ps1 for GitHub Copilot
   - Add Flutter, Django, Firebase, Oracle, Twilio, OneSignal context
   - Preserve existing manual additions
   - Keep under 150 lines for efficiency

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, .github/copilot-instructions.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Backend-first approach as requested by user
- Generate tasks from Phase 1 design docs
- Each API contract → contract test task [P]
- Each entity → Django model creation task [P]
- Each service → service implementation task
- Authentication and security implementation
- Frontend integration tasks (after user provides designs)

**Ordering Strategy**:
- TDD order: Tests before implementation
- Backend first: Database → Models → Services → API endpoints
- Security layer: Authentication → Authorization → Encryption
- Integration: API tests → Frontend integration
- Mark [P] for parallel execution

**Frontend Integration Notes**:
- User will provide frontend designs
- Backend API contracts will be ready for integration
- Frontend features to implement:
  1. Customer Info Page (name, DOB, email, phone input with validation)
  2. Selection Page (Credit Card/Debit Card/NetBanking options)
  3. Details Page (card details or netbanking credentials input)
  4. OTP Verification Page (6-digit OTP input with timer)
  5. Success Page (confirmation message with reference number)
  6. Request History Page (past 12 months of requests)
  7. Profile Management Page (update customer information)

**Frontend Workflow**:
- App Launch → Firebase Auth Check → Login/Register if needed
- Dashboard → Select Request Type → Enter Details → OTP Verification → Success
- Background: Push notification handling for status updates
- Offline: Form data persistence and sync when online

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations identified - all requirements align with established principles*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (None)

**Artifacts Generated**:
- [x] research.md - Technical research and decisions
- [x] data-model.md - Database schema and entity definitions
- [x] contracts/api-contracts.md - REST API specifications
- [x] contracts/openapi.yaml - OpenAPI 3.0 schema
- [x] quickstart.md - End-to-end testing guide
- [x] .github/copilot-instructions.md - Updated agent context

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*