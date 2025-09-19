# Data Model: Card Limit Increase System

**Generated**: 2025-09-17 | **Feature**: 001-generate-a-flutter

## Entity Definitions

### Customer
**Purpose**: Represents bank customers with personal information and authentication credentials

**Fields**:
- `id` (UUID, Primary Key): Unique customer identifier
- `firebase_uid` (String, Unique): Firebase authentication user ID for linking
- `name` (String, Required): Customer full name (2-100 characters)
- `date_of_birth` (Date, Required): Customer date of birth for verification
- `email` (String, Required, Unique): Email address for communication and verification
- `phone` (String, Required, Unique): Phone number for OTP delivery (+91xxxxxxxxxx format)
- `created_at` (DateTime): Account creation timestamp
- `updated_at` (DateTime): Last profile update timestamp
- `is_active` (Boolean): Account status flag

**Validation Rules**:
- Name: Must contain only letters and spaces, 2-100 characters
- Email: Must be valid email format, unique across system
- Phone: Must be valid Indian mobile number format (+91xxxxxxxxxx)
- Date of birth: Must be valid date, customer must be 18+ years old

**Relationships**:
- One-to-many with CardDetail
- One-to-many with LimitRequest
- One-to-many with OTPLog

### CardDetail
**Purpose**: Stores masked card information for limit increase requests (PCI DSS compliant)

**Fields**:
- `id` (UUID, Primary Key): Unique card detail identifier
- `customer_id` (UUID, Foreign Key): Reference to Customer
- `card_type` (Enum): Type of card ('credit', 'debit')
- `last4` (String): Last 4 digits of card number (masked display)
- `expiry_month` (Integer): Card expiry month (1-12)
- `expiry_year` (Integer): Card expiry year (current year + 10 max)
- `token_id` (String, Optional): Tokenized card reference from bank system
- `current_limit` (Decimal): Current transaction limit in INR
- `is_active` (Boolean): Card status flag
- `created_at` (DateTime): Record creation timestamp

**Validation Rules**:
- card_type: Must be 'credit' or 'debit'
- last4: Must be exactly 4 digits
- expiry_month: Must be 1-12
- expiry_year: Must be current year or future (max +10 years)
- current_limit: Must be positive decimal, max 2 decimal places

**Security Notes**:
- Never store full card numbers or CVV
- Use token_id for bank system integration
- Encrypt last4 in database storage

**Relationships**:
- Many-to-one with Customer
- One-to-many with LimitRequest

### LimitRequest
**Purpose**: Tracks customer requests for limit increases with status management

**Fields**:
- `id` (UUID, Primary Key): Unique request identifier
- `customer_id` (UUID, Foreign Key): Reference to Customer
- `card_detail_id` (UUID, Foreign Key, Optional): Reference to CardDetail (null for netbanking)
- `netbanking_customer_id` (String, Optional): NetBanking customer ID (null for cards)
- `request_type` (Enum): Type of request ('credit_card', 'debit_card', 'netbanking')
- `current_limit` (Decimal): Current limit before increase
- `requested_limit` (Decimal): Requested new limit amount
- `status` (Enum): Request status ('pending', 'under_review', 'approved', 'rejected', 'expired')
- `reference_number` (String, Unique): User-facing reference number
- `submitted_at` (DateTime): Request submission timestamp
- `processed_at` (DateTime, Optional): Bank processing completion timestamp
- `expires_at` (DateTime): Request expiry timestamp (30 days from submission)
- `notes` (Text, Optional): Bank processing notes or rejection reasons

**Validation Rules**:
- request_type: Must be 'credit_card', 'debit_card', or 'netbanking'
- requested_limit: Must be between ₹1,000 and ₹10,00,000
- requested_limit: Must be greater than current_limit
- status: Must follow valid state transitions
- reference_number: Auto-generated unique alphanumeric (REQ-YYYYMMDD-XXXX format)

**State Transitions**:
```
pending → under_review → approved/rejected
pending → expired (after 30 days)
under_review → approved/rejected
```

**Business Rules**:
- Only one pending request per card/netbanking account at a time
- Requests auto-expire after 30 days
- Minimum 24-hour gap between requests for same card/account

**Relationships**:
- Many-to-one with Customer
- Many-to-one with CardDetail (optional)
- One-to-many with OTPLog

### OTPLog
**Purpose**: Manages OTP verification lifecycle with security controls

**Fields**:
- `id` (UUID, Primary Key): Unique OTP log identifier
- `customer_id` (UUID, Foreign Key): Reference to Customer
- `limit_request_id` (UUID, Foreign Key, Optional): Associated limit request
- `otp_hash` (String): Hashed OTP value (never store plain text)
- `sent_to` (String): Phone/email where OTP was sent (masked for storage)
- `channel` (Enum): Delivery channel ('sms', 'email', 'voice')
- `purpose` (Enum): OTP purpose ('registration', 'login', 'request_verification')
- `attempts_count` (Integer): Number of verification attempts
- `max_attempts` (Integer): Maximum allowed attempts (default: 3)
- `is_verified` (Boolean): Verification status
- `created_at` (DateTime): OTP generation timestamp
- `expires_at` (DateTime): OTP expiry timestamp (5 minutes from creation)
- `verified_at` (DateTime, Optional): Successful verification timestamp

**Validation Rules**:
- channel: Must be 'sms', 'email', or 'voice'
- purpose: Must be 'registration', 'login', or 'request_verification'
- attempts_count: Must be 0-max_attempts
- max_attempts: Must be positive integer (typically 3)
- expires_at: Must be 5 minutes from created_at

**Security Rules**:
- OTP must be 6-digit numeric
- Hash OTP immediately after generation
- Mask phone/email in sent_to field (show last 4 digits/chars)
- Auto-expire after 5 minutes
- Lock after 3 failed attempts
- 2-minute cooldown after max attempts reached

**Relationships**:
- Many-to-one with Customer
- Many-to-one with LimitRequest (optional)

### NotificationLog
**Purpose**: Tracks push notification delivery and status

**Fields**:
- `id` (UUID, Primary Key): Unique notification identifier
- `customer_id` (UUID, Foreign Key): Reference to Customer
- `limit_request_id` (UUID, Foreign Key, Optional): Associated limit request
- `notification_type` (Enum): Type of notification ('status_update', 'otp_sent', 'login_alert')
- `title` (String): Notification title
- `message` (Text): Notification message content
- `onesignal_id` (String, Optional): OneSignal notification ID
- `delivery_status` (Enum): Delivery status ('sent', 'delivered', 'failed', 'clicked')
- `sent_at` (DateTime): Notification send timestamp
- `delivered_at` (DateTime, Optional): Delivery confirmation timestamp
- `clicked_at` (DateTime, Optional): User click timestamp

**Validation Rules**:
- notification_type: Must be valid notification type
- title: Must be 1-100 characters
- message: Must be 1-500 characters
- delivery_status: Must follow valid status progression

**Relationships**:
- Many-to-one with Customer
- Many-to-one with LimitRequest (optional)

## Database Relationships Diagram

```
Customer (1) ──── (0..*) CardDetail
    │
    │ (1) ──── (0..*) LimitRequest ──── (0..1) CardDetail
    │
    │ (1) ──── (0..*) OTPLog ──── (0..1) LimitRequest
    │
    │ (1) ──── (0..*) NotificationLog ──── (0..1) LimitRequest
```

## Database Indexes

**Performance Optimization Indexes**:
```sql
-- Customer indexes
CREATE INDEX idx_customer_firebase_uid ON customer(firebase_uid);
CREATE INDEX idx_customer_email ON customer(email);
CREATE INDEX idx_customer_phone ON customer(phone);

-- CardDetail indexes
CREATE INDEX idx_carddetail_customer_id ON carddetail(customer_id);
CREATE INDEX idx_carddetail_active ON carddetail(customer_id, is_active);

-- LimitRequest indexes
CREATE INDEX idx_limitrequest_customer_id ON limitrequest(customer_id);
CREATE INDEX idx_limitrequest_status ON limitrequest(status);
CREATE INDEX idx_limitrequest_reference ON limitrequest(reference_number);
CREATE INDEX idx_limitrequest_expires ON limitrequest(expires_at);

-- OTPLog indexes
CREATE INDEX idx_otplog_customer_id ON otplog(customer_id);
CREATE INDEX idx_otplog_expires ON otplog(expires_at);
CREATE INDEX idx_otplog_verification ON otplog(customer_id, is_verified, expires_at);
```

## Data Encryption Requirements

**Fields requiring AES-256 encryption**:
- Customer.email
- Customer.phone
- CardDetail.last4
- CardDetail.token_id
- OTPLog.sent_to
- OTPLog.otp_hash (use bcrypt for hashing)

**Encryption Implementation**:
```python
# Django model field encryption
from cryptography.fernet import Fernet

class EncryptedCharField(models.CharField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_field(value)
    
    def to_python(self, value):
        return decrypt_field(value) if value else value
    
    def get_prep_value(self, value):
        return encrypt_field(value) if value else value
```

## Audit Trail Requirements

**Audit logging required for**:
- All Customer record changes
- LimitRequest status changes
- OTP verification attempts
- Failed authentication attempts
- Data access events

**Audit log format**:
```json
{
    "timestamp": "2025-09-17T10:30:00Z",
    "user_id": "customer_uuid",
    "action": "limit_request_submitted",
    "resource": "limit_request_uuid",
    "ip_address": "192.168.1.1",
    "user_agent": "mobile_app_version",
    "changes": {...}
}
```

## Data Retention Policy

- **Customer data**: Retained for account lifetime + 7 years post-closure
- **LimitRequest data**: Retained for 7 years for regulatory compliance
- **OTPLog data**: Retained for 90 days for security analysis
- **NotificationLog data**: Retained for 1 year for analytics
- **Audit logs**: Retained for 7 years for compliance

## Migration Strategy

**Phase 1**: Create base tables with encryption
**Phase 2**: Add indexes for performance
**Phase 3**: Implement audit triggers
**Phase 4**: Add constraint validations
**Phase 5**: Load test data and validate performance