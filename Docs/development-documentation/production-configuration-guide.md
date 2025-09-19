# Production Configuration Documentation

## Overview

This document provides comprehensive guidance for configuring the HDFC Card Limit Increase System for production deployment. It covers environment setup, security hardening, performance optimization, monitoring, backup strategies, and automated deployment procedures.

## Table of Contents

1. [Production Environment Setup](#production-environment-setup)
2. [Security Configuration](#security-configuration)
3. [Performance Optimization](#performance-optimization)
4. [Monitoring and Alerting](#monitoring-and-alerting)
5. [Backup and Recovery](#backup-and-recovery)
6. [Deployment Automation](#deployment-automation)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Maintenance Procedures](#maintenance-procedures)

## Production Environment Setup

### Environment Configuration

#### 1. Server Requirements

**Application Servers (2x for redundancy)**:
- **CPU**: 8 cores (Intel Xeon or equivalent)
- **Memory**: 32GB RAM
- **Storage**: 500GB SSD (OS and application)
- **Network**: 1Gbps dedicated connection
- **OS**: Ubuntu 22.04 LTS or RHEL 8

**Database Server**:
- **CPU**: 16 cores (Intel Xeon or equivalent)
- **Memory**: 64GB RAM
- **Storage**: 2TB NVMe SSD (database files) + 1TB SSD (backups)
- **Network**: 10Gbps dedicated connection
- **OS**: Oracle Linux 8 or RHEL 8

**Load Balancer**:
- **CPU**: 4 cores
- **Memory**: 16GB RAM
- **Storage**: 100GB SSD
- **Network**: 10Gbps dedicated connection
- **Software**: Nginx or HAProxy

#### 2. Environment Variables

Create `/etc/environment` file with production environment variables:

```bash
# Database Configuration
DB_NAME=HDFC_CARD_LIMIT_PROD
DB_USER=card_limit_user
DB_PASSWORD=<secure_password>
DB_HOST=oracle-prod.hdfc.com
DB_PORT=1521

# Cache Configuration
REDIS_HOST=redis-prod.hdfc.com
REDIS_PORT=6379
REDIS_PASSWORD=<secure_password>

# External Services
SENDGRID_API_KEY=<api_key>
TWILIO_ACCOUNT_SID=<account_sid>
TWILIO_AUTH_TOKEN=<auth_token>
ONESIGNAL_APP_ID=<app_id>
ONESIGNAL_REST_API_KEY=<api_key>

# Firebase Configuration
FIREBASE_PROJECT_ID=hdfc-card-limit-prod
FIREBASE_PRIVATE_KEY=<private_key>
FIREBASE_CLIENT_EMAIL=<client_email>

# Security
ENCRYPTION_KEY=<256_bit_encryption_key>
SECRET_KEY=<django_secret_key>

# Monitoring
SENTRY_DSN=<sentry_dsn>
NEW_RELIC_LICENSE_KEY=<license_key>
```

#### 3. Application Configuration

**Django Settings**: `/opt/hdfc/card_limit_system/card_limit_system/settings/production.py`

Key configuration highlights:
- Debug mode disabled
- SSL and security headers enforced
- Database connection pooling enabled
- Redis caching with clustering support
- Comprehensive logging configuration
- Performance monitoring enabled

## Security Configuration

### 1. SSL/TLS Configuration

#### Nginx SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name card-limit-api.hdfc.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/hdfc-card-limit.crt;
    ssl_certificate_key /etc/ssl/private/hdfc-card-limit.key;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;
    
    # Security Headers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Security Headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Application proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Firewall Configuration

#### UFW Firewall Rules

```bash
# Reset firewall
sudo ufw --force reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH access (restricted to admin networks)
sudo ufw allow from 10.0.0.0/8 to any port 22

# HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Database (restricted to application servers)
sudo ufw allow from 10.1.1.0/24 to any port 1521

# Redis (restricted to application servers)
sudo ufw allow from 10.1.1.0/24 to any port 6379

# Enable firewall
sudo ufw enable
```

### 3. Application Security

#### Rate Limiting Configuration

The application includes comprehensive rate limiting:
- Login attempts: 5 attempts per 15 minutes
- OTP requests: 3 requests per 5 minutes
- API requests: 1000 requests per hour
- Limit requests: 5 requests per 24 hours

#### IP Whitelisting

Production middleware includes IP whitelisting for internal services:
- `10.0.0.0/8` - Internal network
- `172.16.0.0/12` - Internal network
- `192.168.0.0/16` - Internal network

## Performance Optimization

### 1. Database Optimization

#### Oracle Configuration

**Database Parameters** (`/u01/app/oracle/product/19.0.0/dbhome_1/dbs/initHDFC.ora`):

```ini
# Memory Settings
sga_target=8G
pga_aggregate_target=4G
shared_pool_size=2G
db_cache_size=4G

# I/O Optimization
db_writer_processes=8
log_writer_io_size=64K
disk_asynch_io=TRUE

# Connection Management
processes=1000
sessions=1200
```

#### Connection Pooling

Django database configuration includes:
- Connection pooling with `CONN_MAX_AGE=600`
- Read replica for analytics queries
- Automatic connection retry and failover

### 2. Caching Strategy

#### Redis Cluster Configuration

```yaml
# redis.conf
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 15000
cluster-require-full-coverage no

# Memory optimization
maxmemory 8gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
tcp-keepalive 300
timeout 300
```

#### Cache Implementation

- **Default Cache**: General application caching
- **Session Cache**: User session storage
- **Rate Limit Cache**: Rate limiting counters
- **Analytics Cache**: Pre-computed metrics

### 3. Application Performance

#### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 8
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
```

#### Static File Optimization

- Static files served by Nginx with compression
- CDN integration for global distribution
- Asset versioning and caching headers

## Monitoring and Alerting

### 1. Application Monitoring

#### Health Check Endpoints

The application provides comprehensive health check endpoints:

- `/health/` - Overall application health
- `/health/database/` - Database connectivity and performance
- `/health/cache/` - Cache system status
- `/health/services/` - External service connectivity

#### Performance Metrics

Real-time monitoring includes:
- Response time percentiles (50th, 95th, 99th)
- Request rate and error rate
- Database query performance
- Cache hit rates
- Memory and CPU usage

### 2. Alerting Configuration

#### Alert Rules

```yaml
# Prometheus alerting rules
groups:
- name: hdfc-card-limit-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High error rate detected"
      
  - alert: DatabaseConnectionFailure
    expr: database_connection_errors_total > 0
    for: 1m
    annotations:
      summary: "Database connection failure"
      
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
    for: 10m
    annotations:
      summary: "High response time detected"
```

#### Notification Channels

- **Email**: Critical alerts to operations team
- **Slack**: All alerts to development team
- **PagerDuty**: After-hours critical alerts
- **SMS**: Database and security alerts

### 3. Log Management

#### Centralized Logging

```yaml
# Filebeat configuration
filebeat.inputs:
- type: log
  paths:
    - /var/log/hdfc/card_limit_system.log
    - /var/log/hdfc/card_limit_errors.log
    - /var/log/hdfc/card_limit_security.log
  fields:
    service: hdfc-card-limit
    environment: production

output.elasticsearch:
  hosts: ["elasticsearch-prod.hdfc.com:9200"]
  index: "hdfc-card-limit-%{+yyyy.MM.dd}"
```

## Backup and Recovery

### 1. Database Backup Strategy

#### Automated Backup Schedule

```bash
# Daily full backup
0 2 * * * /opt/hdfc/card_limit_system/manage.py backup_database --type=full

# Hourly incremental backup
0 * * * * /opt/hdfc/card_limit_system/manage.py backup_database --type=incremental

# Weekly media backup
0 3 * * 0 /opt/hdfc/card_limit_system/manage.py backup_media

# Monthly archive cleanup
0 4 1 * * /opt/hdfc/card_limit_system/manage.py cleanup_backups --retention=90
```

#### Backup Verification

```bash
# Daily backup integrity check
0 5 * * * /opt/hdfc/card_limit_system/manage.py verify_backup --latest
```

### 2. Disaster Recovery

#### Recovery Time Objectives (RTO)

- **Database Recovery**: 4 hours
- **Application Recovery**: 2 hours
- **Full System Recovery**: 6 hours

#### Recovery Point Objectives (RPO)

- **Database**: 1 hour (incremental backups)
- **Media Files**: 24 hours (daily backups)
- **Configuration**: Real-time (version control)

#### Recovery Procedures

1. **Database Recovery**:
   ```bash
   python manage.py restore_database --backup=backup_name
   ```

2. **Application Recovery**:
   ```bash
   ./scripts/deploy.sh --rollback
   ```

3. **Full System Recovery**:
   ```bash
   ./scripts/disaster_recovery.sh --restore-from=backup_location
   ```

## Deployment Automation

### 1. Deployment Strategy

#### Blue-Green Deployment

The production deployment uses blue-green strategy:
- Zero-downtime deployment
- Instant rollback capability
- Health check validation before traffic switch
- Automated load balancer configuration

#### Deployment Process

```bash
# Standard deployment
./scripts/deploy.sh --environment=production --type=blue_green

# Emergency rollback
./scripts/deploy.sh --rollback

# Health check only
./scripts/deploy.sh --health-check-only
```

### 2. Deployment Validation

#### Pre-deployment Checks

- Environment variable validation
- Disk space and system resource checks
- Database connectivity verification
- External service availability

#### Post-deployment Validation

- Health check endpoint verification
- Smoke test execution
- Performance metric validation
- Security scan results

## CI/CD Pipeline

### 1. Pipeline Stages

The GitHub Actions pipeline includes:

1. **Code Quality**: Linting, formatting, security analysis
2. **Testing**: Unit tests, integration tests, coverage reporting
3. **Build**: Package creation, static file collection
4. **Security**: Vulnerability scanning, dependency checks
5. **Deploy**: Staging and production deployment
6. **Monitor**: Post-deployment monitoring and validation

### 2. Environment Management

#### Staging Environment

- Mirror of production configuration
- Automated deployment on `develop` branch
- Integration testing and validation
- Performance testing and load testing

#### Production Environment

- Blue-green deployment strategy
- Manual approval for deployment
- Comprehensive health checks
- Automated rollback on failure

### 3. Quality Gates

Each pipeline stage includes quality gates:
- **Code Quality**: No critical issues allowed
- **Testing**: 95%+ code coverage required
- **Security**: No high/critical vulnerabilities
- **Performance**: < 2s response time requirement

## Maintenance Procedures

### 1. Regular Maintenance

#### Daily Tasks

- Review application logs for errors
- Check system resource utilization
- Verify backup completion
- Monitor external service health

#### Weekly Tasks

- Database performance analysis
- Security log review
- Backup integrity verification
- Dependency update review

#### Monthly Tasks

- Security patch application
- Performance optimization review
- Disaster recovery testing
- Backup retention cleanup

### 2. Emergency Procedures

#### Incident Response

1. **Detection**: Automated alerts and monitoring
2. **Assessment**: Impact analysis and severity classification
3. **Response**: Immediate mitigation actions
4. **Recovery**: System restoration and validation
5. **Follow-up**: Post-incident review and improvements

#### Escalation Matrix

- **Level 1**: Development team response (15 minutes)
- **Level 2**: Operations team escalation (30 minutes)
- **Level 3**: Management escalation (1 hour)
- **Level 4**: Executive escalation (2 hours)

### 3. Change Management

#### Change Process

1. Change request submission
2. Impact analysis and approval
3. Testing in staging environment
4. Scheduled maintenance window
5. Change implementation
6. Validation and monitoring
7. Change documentation

#### Rollback Procedures

All changes include documented rollback procedures:
- Database schema changes
- Application code updates
- Configuration modifications
- Infrastructure changes

## Conclusion

This production configuration documentation provides comprehensive guidance for deploying and maintaining the HDFC Card Limit Increase System in a production environment. The configuration emphasizes security, performance, reliability, and operational excellence while maintaining the scalability needed for a banking-grade application.

Regular review and updates of this documentation ensure that the production environment remains secure, performant, and aligned with best practices and regulatory requirements.