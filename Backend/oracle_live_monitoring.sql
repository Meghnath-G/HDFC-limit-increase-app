-- HDFC Card Limit System - Live Data Monitoring Queries
-- Execute these in Oracle SQL Developer to see real-time data

-- 1. LIVE DATA DASHBOARD - Execute this every few seconds to see new entries
SELECT 
    '=== RECENT LIMIT REQUESTS ===' as section,
    null as request_id,
    null as customer_name, 
    null as email,
    null as request_type,
    null as current_limit,
    null as requested_limit,
    null as status,
    null as request_date
FROM dual
UNION ALL
SELECT 
    null as section,
    TO_CHAR(lr.id) as request_id,
    c.name as customer_name,
    c.email,
    lr.request_type,
    TO_CHAR(lr.current_limit) as current_limit,
    TO_CHAR(lr.requested_limit) as requested_limit,
    lr.status,
    TO_CHAR(lr.request_date, 'YYYY-MM-DD HH24:MI:SS') as request_date
FROM limit_requests lr
JOIN customers c ON lr.customer_id = c.customer_id
ORDER BY request_date DESC NULLS LAST;

-- 2. CUSTOMER ACTIVITY MONITOR
SELECT 
    '=== CUSTOMER ACTIVITY ===' as section,
    null as customer_name,
    null as email,
    null as total_requests,
    null as latest_request,
    null as account_status
FROM dual
UNION ALL
SELECT 
    null as section,
    c.name as customer_name,
    c.email,
    TO_CHAR(COUNT(lr.id)) as total_requests,
    TO_CHAR(MAX(lr.request_date), 'YYYY-MM-DD HH24:MI:SS') as latest_request,
    c.status as account_status
FROM customers c
LEFT JOIN limit_requests lr ON c.customer_id = lr.customer_id
GROUP BY c.name, c.email, c.status
ORDER BY latest_request DESC NULLS LAST;

-- 3. STATUS TRACKING - Shows progression of request statuses
SELECT 
    '=== STATUS PROGRESSION ===' as section,
    null as request_id,
    null as customer_name,
    null as action,
    null as old_status,
    null as new_status,
    null as changed_at
FROM dual
UNION ALL
SELECT 
    null as section,
    TO_CHAR(al.request_id) as request_id,
    c.name as customer_name,
    al.action,
    al.old_status,
    al.new_status,
    TO_CHAR(al.changed_at, 'YYYY-MM-DD HH24:MI:SS') as changed_at
FROM request_audit_log al
JOIN limit_requests lr ON al.request_id = lr.id
JOIN customers c ON lr.customer_id = c.customer_id
ORDER BY changed_at DESC NULLS LAST;

-- 4. NOTIFICATIONS MONITOR
SELECT 
    '=== RECENT NOTIFICATIONS ===' as section,
    null as customer_name,
    null as title,
    null as message,
    null as type,
    null as status,
    null as sent_at
FROM dual
UNION ALL
SELECT 
    null as section,
    c.name as customer_name,
    n.title,
    SUBSTR(n.message, 1, 50) || '...' as message,
    n.notification_type as type,
    n.status,
    TO_CHAR(n.created_at, 'YYYY-MM-DD HH24:MI:SS') as sent_at
FROM notifications n
JOIN customers c ON n.customer_id = c.id
ORDER BY sent_at DESC NULLS LAST;

-- 5. REAL-TIME STATS SUMMARY
SELECT 
    '=== SYSTEM STATISTICS ===' as metric,
    null as value
FROM dual
UNION ALL
SELECT 
    'Total Customers' as metric,
    TO_CHAR(COUNT(*)) as value
FROM customers
UNION ALL
SELECT 
    'Total Requests Today' as metric,
    TO_CHAR(COUNT(*)) as value
FROM limit_requests 
WHERE DATE(request_date) = DATE(SYSDATE)
UNION ALL
SELECT 
    'Pending Requests' as metric,
    TO_CHAR(COUNT(*)) as value
FROM limit_requests 
WHERE status = 'pending'
UNION ALL
SELECT 
    'Approved Today' as metric,
    TO_CHAR(COUNT(*)) as value
FROM limit_requests 
WHERE status = 'approved' AND DATE(request_date) = DATE(SYSDATE)
UNION ALL
SELECT 
    'Active Customers' as metric,
    TO_CHAR(COUNT(*)) as value
FROM customers 
WHERE status = 'active';

-- 6. REFRESH COMMAND - Run this to see the latest data
-- (Copy and paste the queries above individually for best results)

-- 7. SIMPLE REFRESH QUERIES (Individual queries for easy execution)

-- Latest 5 requests:
SELECT 
    lr.id,
    c.name,
    lr.request_type,
    lr.current_limit,
    lr.requested_limit,
    lr.status,
    lr.request_date
FROM limit_requests lr
JOIN customers c ON lr.customer_id = c.customer_id
ORDER BY lr.request_date DESC
FETCH FIRST 5 ROWS ONLY;

-- Count by status:
SELECT 
    status,
    COUNT(*) as count
FROM limit_requests
GROUP BY status;

-- Recent customers:
SELECT 
    name,
    email,
    customer_id,
    created_at
FROM customers
ORDER BY created_at DESC
FETCH FIRST 5 ROWS ONLY;

-- INSTRUCTIONS FOR LIVE DEMO:
-- 1. Execute oracle_setup.sql first to create tables
-- 2. Start the Python server: python simple_server.py
-- 3. Use Flutter app to submit data
-- 4. Run these queries in Oracle SQL Developer to see live data
-- 5. Refresh queries every few seconds during demo