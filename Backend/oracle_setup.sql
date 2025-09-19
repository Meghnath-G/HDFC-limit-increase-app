-- =============================================================================
-- HDFC Card Limit System - Oracle Database Setup Script
-- Created: September 19, 2025
-- Purpose: Create tables for live data demonstration
-- =============================================================================

-- Create user and grant permissions (run as SYSTEM user)
-- CREATE USER hdfc_user IDENTIFIED BY hdfc123;
-- GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE TRIGGER TO hdfc_user;
-- GRANT UNLIMITED TABLESPACE TO hdfc_user;

-- Connect as hdfc_user for table creation
-- CONNECT hdfc_user/hdfc123@localhost:1521/XEPDB1;

-- =============================================================================
-- 1. CUSTOMERS TABLE
-- =============================================================================
CREATE TABLE customers (
    id VARCHAR2(36) PRIMARY KEY,
    firebase_uid VARCHAR2(128) UNIQUE NOT NULL,
    name VARCHAR2(100) NOT NULL,
    email VARCHAR2(254) UNIQUE NOT NULL,
    phone_number VARCHAR2(15) NOT NULL,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active NUMBER(1) DEFAULT 1
);

-- Create index for faster lookup
CREATE INDEX idx_customers_firebase_uid ON customers(firebase_uid);
CREATE INDEX idx_customers_email ON customers(email);

-- =============================================================================
-- 2. CARD DETAILS TABLE
-- =============================================================================
CREATE TABLE card_details (
    id VARCHAR2(36) PRIMARY KEY,
    customer_id VARCHAR2(36) NOT NULL,
    card_number_hash VARCHAR2(64) NOT NULL, -- Hashed for security
    card_type VARCHAR2(20) NOT NULL CHECK (card_type IN ('CREDIT', 'DEBIT')),
    current_limit NUMBER(12,2) DEFAULT 0,
    available_limit NUMBER(12,2) DEFAULT 0,
    card_status VARCHAR2(20) DEFAULT 'ACTIVE' CHECK (card_status IN ('ACTIVE', 'BLOCKED', 'EXPIRED')),
    issue_date DATE,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_card_details_customer_id ON card_details(customer_id);
CREATE INDEX idx_card_details_card_type ON card_details(card_type);

-- =============================================================================
-- 3. LIMIT REQUESTS TABLE
-- =============================================================================
CREATE TABLE limit_requests (
    id VARCHAR2(36) PRIMARY KEY,
    customer_id VARCHAR2(36) NOT NULL,
    card_detail_id VARCHAR2(36) NOT NULL,
    request_type VARCHAR2(20) NOT NULL CHECK (request_type IN ('credit_limit', 'debit_limit')),
    current_limit NUMBER(12,2) NOT NULL,
    requested_limit NUMBER(12,2) NOT NULL,
    reason VARCHAR2(500),
    annual_income NUMBER(12,2),
    employment_status VARCHAR2(50),
    status VARCHAR2(20) DEFAULT 'pending' CHECK (status IN ('pending', 'under_review', 'approved', 'rejected', 'implemented', 'cancelled')),
    priority VARCHAR2(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_date TIMESTAMP,
    completion_date TIMESTAMP,
    reviewer_comments VARCHAR2(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (card_detail_id) REFERENCES card_details(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_limit_requests_customer_id ON limit_requests(customer_id);
CREATE INDEX idx_limit_requests_status ON limit_requests(status);
CREATE INDEX idx_limit_requests_request_date ON limit_requests(request_date);

-- =============================================================================
-- 4. REQUEST AUDIT LOG TABLE (for tracking changes)
-- =============================================================================
CREATE TABLE request_audit_log (
    id VARCHAR2(36) PRIMARY KEY,
    request_id VARCHAR2(36) NOT NULL,
    action VARCHAR2(50) NOT NULL, -- 'created', 'status_changed', 'updated', 'completed'
    old_status VARCHAR2(20),
    new_status VARCHAR2(20),
    changed_by VARCHAR2(100),
    change_reason VARCHAR2(500),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES limit_requests(id) ON DELETE CASCADE
);

-- Create index
CREATE INDEX idx_audit_log_request_id ON request_audit_log(request_id);
CREATE INDEX idx_audit_log_changed_at ON request_audit_log(changed_at);

-- =============================================================================
-- 5. NOTIFICATIONS TABLE
-- =============================================================================
CREATE TABLE notifications (
    id VARCHAR2(36) PRIMARY KEY,
    customer_id VARCHAR2(36) NOT NULL,
    title VARCHAR2(200) NOT NULL,
    message VARCHAR2(1000) NOT NULL,
    notification_type VARCHAR2(50) NOT NULL CHECK (notification_type IN ('request_status', 'limit_update', 'system_alert', 'promotional')),
    status VARCHAR2(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed')),
    priority VARCHAR2(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_notifications_customer_id ON notifications(customer_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- =============================================================================
-- 6. SAMPLE DATA FOR TESTING
-- =============================================================================

-- Insert sample customer
INSERT INTO customers (id, firebase_uid, name, email, phone_number, date_of_birth) VALUES 
('550e8400-e29b-41d4-a716-446655440001', 'firebase_uid_001', 'Rajesh Kumar', 'rajesh.kumar@email.com', '+911234567890', DATE '1985-06-15');

INSERT INTO customers (id, firebase_uid, name, email, phone_number, date_of_birth) VALUES 
('550e8400-e29b-41d4-a716-446655440002', 'firebase_uid_002', 'Priya Sharma', 'priya.sharma@email.com', '+911234567891', DATE '1990-03-22');

-- Insert sample card details
INSERT INTO card_details (id, customer_id, card_number_hash, card_type, current_limit, available_limit, issue_date, expiry_date) VALUES 
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'hash_1234', 'CREDIT', 50000.00, 35000.00, DATE '2023-01-15', DATE '2028-01-15');

INSERT INTO card_details (id, customer_id, card_number_hash, card_type, current_limit, available_limit, issue_date, expiry_date) VALUES 
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'hash_5678', 'CREDIT', 30000.00, 28000.00, DATE '2024-02-10', DATE '2029-02-10');

-- Insert sample limit request
INSERT INTO limit_requests (id, customer_id, card_detail_id, request_type, current_limit, requested_limit, reason, annual_income, employment_status) VALUES 
('770e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'credit_limit', 50000.00, 75000.00, 'Salary increment and increased expenses', 800000.00, 'FULL_TIME');

-- Insert sample notification
INSERT INTO notifications (id, customer_id, title, message, notification_type) VALUES 
('880e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'Limit Request Received', 'Your credit limit increase request has been received and is under review.', 'request_status');

-- =============================================================================
-- 7. USEFUL QUERIES FOR MONITORING LIVE DATA
-- =============================================================================

-- Query to see all recent limit requests
-- SELECT 
--     lr.id as request_id,
--     c.name as customer_name,
--     c.email,
--     lr.request_type,
--     lr.current_limit,
--     lr.requested_limit,
--     lr.status,
--     lr.request_date
-- FROM limit_requests lr
-- JOIN customers c ON lr.customer_id = c.id
-- ORDER BY lr.request_date DESC;

-- Query to see request status changes
-- SELECT 
--     al.request_id,
--     c.name as customer_name,
--     al.action,
--     al.old_status,
--     al.new_status,
--     al.changed_at
-- FROM request_audit_log al
-- JOIN limit_requests lr ON al.request_id = lr.id
-- JOIN customers c ON lr.customer_id = c.id
-- ORDER BY al.changed_at DESC;

-- Query to see all notifications
-- SELECT 
--     n.title,
--     n.message,
--     c.name as customer_name,
--     n.notification_type,
--     n.status,
--     n.created_at
-- FROM notifications n
-- JOIN customers c ON n.customer_id = c.id
-- ORDER BY n.created_at DESC;

COMMIT;

-- =============================================================================
-- END OF SCRIPT
-- =============================================================================