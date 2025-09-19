# HDFC Card Limit System - Live Data Demo Setup

## Step 1: Oracle SQL Developer Setup

### 1.1 Create Oracle Connection
1. Open Oracle SQL Developer
2. Click the "+" button to create a new connection
3. Enter connection details:
   - **Connection Name**: HDFC_Card_System
   - **Username**: hdfc_user
   - **Password**: hdfc123
   - **Hostname**: localhost
   - **Port**: 1521
   - **SID**: XE (or Service Name: XEPDB1)

### 1.2 Create Database Tables
1. Connect to your Oracle database
2. Open the file: `Backend/oracle_setup.sql`
3. Execute the script to create tables and insert sample data

## Step 2: Start Django Backend Server

### 2.1 Simple Python Server (without cx_Oracle)
```bash
cd Backend/card_limit_system
python simple_server.py
```

The server will start on http://localhost:8000

### 2.2 API Endpoints Available
- **Health Check**: GET http://localhost:8000/api/health/
- **Submit Customer Data**: POST http://localhost:8000/api/customers/
- **Submit Limit Request**: POST http://localhost:8000/api/limit-requests/
- **Get Recent Requests**: GET http://localhost:8000/api/limit-requests/recent/
- **Check Request Status**: GET http://localhost:8000/api/limit-requests/{id}/status/

## Step 3: Test Data Flow

### 3.1 Flutter App → API → Database
1. Open Flutter app in Chrome (already running)
2. Fill out a limit request form
3. Submit the request
4. Check Oracle SQL Developer for new data

### 3.2 Monitor Live Data in Oracle SQL Developer

Execute these queries to see live data:

```sql
-- See all recent limit requests
SELECT 
    lr.id as request_id,
    c.name as customer_name,
    c.email,
    lr.request_type,
    lr.current_limit,
    lr.requested_limit,
    lr.status,
    lr.request_date
FROM limit_requests lr
JOIN customers c ON lr.customer_id = c.id
ORDER BY lr.request_date DESC;

-- See request status changes
SELECT 
    al.request_id,
    c.name as customer_name,
    al.action,
    al.old_status,
    al.new_status,
    al.changed_at
FROM request_audit_log al
JOIN limit_requests lr ON al.request_id = lr.id
JOIN customers c ON lr.customer_id = c.id
ORDER BY al.changed_at DESC;

-- See all notifications
SELECT 
    n.title,
    n.message,
    c.name as customer_name,
    n.notification_type,
    n.status,
    n.created_at
FROM notifications n
JOIN customers c ON n.customer_id = c.id
ORDER BY n.created_at DESC;
```

## Step 4: Demo Flow for Client

1. **Show Flutter App**: Open the running Flutter app in Chrome
2. **Show Oracle SQL Developer**: Open with HDFC connection
3. **Submit Data**: Fill and submit a form in Flutter
4. **Show Live Data**: Refresh queries in Oracle SQL Developer to show new entries
5. **Show Real-time Updates**: Demonstrate status changes and notifications

## Troubleshooting

### If Oracle Connection Fails:
1. Ensure Oracle Database is running
2. Check if user `hdfc_user` exists and has correct permissions
3. Verify connection details (hostname, port, SID/service name)

### If API Server Fails:
1. Check Python installation
2. Ensure no other service is using port 8000
3. Check firewall settings

### For Production Setup:
- Install proper Oracle client libraries
- Configure cx_Oracle for Django
- Set up SSL certificates
- Configure production database settings