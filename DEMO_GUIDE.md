# HDFC Card Limit System - Live Demo Guide

## 🎯 Objective
Demonstrate live data flow from Flutter app to Oracle SQL Developer for client presentation

## 📋 Demo Setup Checklist

### ✅ Phase 1: Prerequisites
- [x] Flutter app running in Chrome
- [x] Oracle SQL Developer downloaded
- [x] Python server ready
- [x] Oracle database connection configured

### 🔧 Phase 2: Database Setup

#### 2.1 Oracle SQL Developer Connection
1. **Open Oracle SQL Developer**
2. **Create New Connection:**
   - Connection Name: `HDFC_Card_System`
   - Username: `hdfc_user`
   - Password: `hdfc123`
   - Hostname: `localhost`
   - Port: `1521`
   - SID: `XE` (or Service Name: `XEPDB1`)

#### 2.2 Create Database Schema
1. **Connect to Oracle**
2. **Execute:** `Backend/oracle_setup.sql`
3. **Verify tables created:**
   ```sql
   SELECT table_name FROM user_tables;
   ```

### 🚀 Phase 3: Start Backend Server

#### 3.1 Start Python API Server
```powershell
cd "D:\IvaR\HDFC"
py Backend\card_limit_system\simple_server.py
```

#### 3.2 Verify Server Status
- Server URL: http://localhost:8000
- Health Check: http://localhost:8000/api/health/

### 📱 Phase 4: Flutter App Configuration

#### 4.1 Update Flutter API Endpoint
In your Flutter app, ensure API calls point to:
```dart
const String baseUrl = 'http://localhost:8000/api';
```

#### 4.2 Test API Endpoints
- Submit Customer: POST `/customers/`
- Submit Request: POST `/limit-requests/`
- Get Status: GET `/limit-requests/recent/`

### 🔍 Phase 5: Live Data Monitoring

#### 5.1 Oracle SQL Developer Queries
Execute these queries to monitor live data:

```sql
-- Real-time request monitoring
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
ORDER BY lr.request_date DESC;

-- System statistics
SELECT 
    'Total Requests' as metric,
    COUNT(*) as count
FROM limit_requests
UNION ALL
SELECT 
    'Pending Requests' as metric,
    COUNT(*) as count
FROM limit_requests 
WHERE status = 'pending'
UNION ALL
SELECT 
    'Active Customers' as metric,
    COUNT(*) as count
FROM customers 
WHERE status = 'active';
```

#### 5.2 Refresh Commands
- Press F5 or Ctrl+R to refresh queries
- Use `oracle_live_monitoring.sql` for comprehensive monitoring

## 🎬 Demo Presentation Flow

### Step 1: Show System Overview
1. **Display Flutter App** (running in Chrome)
2. **Display Oracle SQL Developer** (connected and ready)
3. **Display Backend Server** (console showing running status)

### Step 2: Submit Test Data
1. **In Flutter App:**
   - Fill customer information form
   - Submit limit increase request
   - Show success confirmation

### Step 3: Show Live Data
1. **In Oracle SQL Developer:**
   - Execute monitoring queries
   - Show new customer record
   - Show new limit request
   - Demonstrate real-time data flow

### Step 4: Demonstrate Processing
1. **Show request progression:**
   - Initial status: 'pending'
   - Update status to 'under_review'
   - Show audit trail

### Step 5: Complete Workflow
1. **Show notifications generated**
2. **Show system statistics update**
3. **Demonstrate reporting capabilities**

## 🛠️ Troubleshooting

### Server Issues
- **Port in use:** Change port with `py simple_server.py 8001`
- **Python not found:** Use `py` instead of `python`
- **CORS errors:** Server includes CORS headers

### Database Issues
- **Connection failed:** Check Oracle service running
- **User not found:** Run oracle_setup.sql first
- **Permission denied:** Ensure user has CREATE privileges

### Flutter Issues
- **API connection failed:** Check server is running
- **CORS blocked:** Use Chrome with --disable-web-security flag
- **Network error:** Verify localhost:8000 accessible

## 📊 Expected Demo Outcomes

### Client Will See:
1. **Real-time data entry** from mobile-like interface
2. **Immediate database updates** in Oracle SQL Developer
3. **Professional system architecture** with proper data flow
4. **Scalable backend design** ready for production

### Technical Demonstration:
1. **Flutter → REST API → Database** complete pipeline
2. **Live monitoring capabilities** for operations team
3. **Audit trail functionality** for compliance
4. **Notification system** for customer updates

## 🔄 Demo Reset Instructions

### Between Demo Sessions:
1. **Clear test data:**
   ```sql
   DELETE FROM request_audit_log;
   DELETE FROM notifications;
   DELETE FROM limit_requests;
   DELETE FROM customers;
   ```

2. **Reset sequences:**
   ```sql
   DROP SEQUENCE customer_id_seq;
   DROP SEQUENCE request_id_seq;
   CREATE SEQUENCE customer_id_seq START WITH 1;
   CREATE SEQUENCE request_id_seq START WITH 1;
   ```

3. **Restart server:** Ctrl+C then restart python server

## 📈 Success Metrics

### Demo Successful When:
- [ ] Flutter app submits data successfully
- [ ] Backend server processes requests
- [ ] Oracle database shows new records immediately
- [ ] Client can see end-to-end data flow
- [ ] System demonstrates professional reliability

---

**Ready for Client Demonstration! 🎉**