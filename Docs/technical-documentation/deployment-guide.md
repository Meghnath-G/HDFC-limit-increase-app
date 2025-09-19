# Deployment Guide

## Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Environment Setup](#environment-setup)
3. [Oracle Database Deployment](#oracle-database-deployment)
4. [Django Application Deployment](#django-application-deployment)
5. [Containerization with Docker](#containerization-with-docker)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [CI/CD Pipeline Setup](#cicd-pipeline-setup)
8. [Environment Configuration](#environment-configuration)
9. [SSL/TLS Configuration](#ssltls-configuration)
10. [Monitoring and Logging](#monitoring-and-logging)
11. [Backup and Recovery](#backup-and-recovery)
12. [Performance Optimization](#performance-optimization)
13. [Security Hardening](#security-hardening)
14. [Troubleshooting Deployment Issues](#troubleshooting-deployment-issues)

---

## Deployment Overview

### 1. Architecture Overview

```yaml
# deployment-architecture.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: deployment-architecture
data:
  architecture: |
    Production Deployment Architecture:
    
    Internet Gateway
    ├── Load Balancer (ALB/ELB)
    │   ├── WAF (Web Application Firewall)
    │   └── SSL Termination
    │
    ├── Kubernetes Cluster
    │   ├── Django Application Pods (3+ replicas)
    │   │   ├── Main API Service
    │   │   ├── Background Task Workers
    │   │   └── Scheduled Jobs
    │   │
    │   ├── Redis Cluster (Caching & Sessions)
    │   ├── Nginx Ingress Controller
    │   └── Service Mesh (Istio)
    │
    ├── Database Tier
    │   ├── Oracle 19c Primary Database
    │   ├── Oracle 19c Standby Database
    │   └── Read Replicas
    │
    ├── External Services
    │   ├── Firebase Authentication
    │   ├── Twilio Communications
    │   ├── SendGrid Email
    │   └── OneSignal Push Notifications
    │
    └── Monitoring & Logging
        ├── Prometheus & Grafana
        ├── ELK Stack (Elasticsearch, Logstash, Kibana)
        └── Application Performance Monitoring
```

### 2. Deployment Environments

```python
# config/environments.py
class DeploymentEnvironments:
    """
    Configuration for different deployment environments
    """
    
    ENVIRONMENTS = {
        'development': {
            'description': 'Local development environment',
            'resources': {
                'cpu_request': '100m',
                'cpu_limit': '500m',
                'memory_request': '128Mi',
                'memory_limit': '512Mi'
            },
            'replicas': 1,
            'database': 'sqlite3',  # For local development
            'cache': 'local_memory',
            'external_services': 'sandbox'
        },
        'staging': {
            'description': 'Pre-production testing environment',
            'resources': {
                'cpu_request': '500m',
                'cpu_limit': '1000m',
                'memory_request': '512Mi',
                'memory_limit': '1Gi'
            },
            'replicas': 2,
            'database': 'oracle_test',
            'cache': 'redis_single',
            'external_services': 'sandbox'
        },
        'production': {
            'description': 'Production environment',
            'resources': {
                'cpu_request': '1000m',
                'cpu_limit': '2000m',
                'memory_request': '1Gi',
                'memory_limit': '4Gi'
            },
            'replicas': 3,
            'database': 'oracle_cluster',
            'cache': 'redis_cluster',
            'external_services': 'production',
            'backup_enabled': True,
            'monitoring_enabled': True,
            'ssl_required': True
        }
    }
    
    @classmethod
    def get_environment_config(cls, env_name: str) -> dict:
        """Get configuration for specific environment"""
        if env_name not in cls.ENVIRONMENTS:
            raise ValueError(f"Unknown environment: {env_name}")
        
        return cls.ENVIRONMENTS[env_name]
    
    @classmethod
    def validate_environment(cls, env_name: str, config: dict) -> bool:
        """Validate environment configuration"""
        required_fields = ['description', 'resources', 'replicas']
        
        for field in required_fields:
            if field not in config:
                return False
        
        # Validate resources
        resource_fields = ['cpu_request', 'cpu_limit', 'memory_request', 'memory_limit']
        for field in resource_fields:
            if field not in config['resources']:
                return False
        
        return True
```

---

## Environment Setup

### 1. System Requirements

```bash
# system-requirements.sh
#!/bin/bash

echo "=== HDFC Card Limit System - Environment Setup ==="

# System Requirements Check
echo "Checking system requirements..."

# Operating System
OS_VERSION=$(lsb_release -d | cut -f2)
echo "Operating System: $OS_VERSION"

# Required: Ubuntu 20.04 LTS or CentOS 8+
if [[ "$OS_VERSION" =~ "Ubuntu 20.04" ]] || [[ "$OS_VERSION" =~ "CentOS 8" ]]; then
    echo "✓ Operating System compatible"
else
    echo "⚠ Warning: Recommended OS is Ubuntu 20.04 LTS or CentOS 8+"
fi

# CPU Requirements
CPU_CORES=$(nproc)
echo "CPU Cores: $CPU_CORES"
if [ $CPU_CORES -ge 4 ]; then
    echo "✓ CPU requirement met (minimum 4 cores)"
else
    echo "✗ Insufficient CPU cores (minimum 4 required)"
fi

# Memory Requirements
MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
echo "Memory: ${MEMORY_GB}GB"
if [ $MEMORY_GB -ge 8 ]; then
    echo "✓ Memory requirement met (minimum 8GB)"
else
    echo "✗ Insufficient memory (minimum 8GB required)"
fi

# Disk Space Requirements
DISK_SPACE=$(df -h / | awk '/\//{print $4}' | sed 's/G//')
echo "Available Disk Space: ${DISK_SPACE}GB"
if [ ${DISK_SPACE%.*} -ge 50 ]; then
    echo "✓ Disk space requirement met (minimum 50GB)"
else
    echo "✗ Insufficient disk space (minimum 50GB required)"
fi

echo "=== System Requirements Check Complete ==="
```

### 2. Prerequisites Installation

```bash
# install-prerequisites.sh
#!/bin/bash

set -e

echo "=== Installing Prerequisites ==="

# Update system packages
echo "Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install essential packages
echo "Installing essential packages..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip \
    python3-venv

# Install Python 3.9+
echo "Installing Python 3.9..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update -y
sudo apt-get install -y python3.9 python3.9-dev python3.9-venv python3.9-distutils

# Install Node.js (for frontend tools)
echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Docker
echo "Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install kubectl
echo "Installing kubectl..."
sudo curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
echo "Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Configure Docker permissions
echo "Configuring Docker permissions..."
sudo usermod -aG docker $USER

echo "=== Prerequisites Installation Complete ==="
echo "Please log out and log back in to apply Docker permissions."
```

### 3. Oracle Client Installation

```bash
# install-oracle-client.sh
#!/bin/bash

set -e

echo "=== Installing Oracle Instant Client ==="

# Create Oracle directory
sudo mkdir -p /opt/oracle

# Download Oracle Instant Client (you need to manually download from Oracle website)
# This script assumes the files are already downloaded
ORACLE_CLIENT_VERSION="21.1.0.0.0"
ORACLE_CLIENT_DIR="/opt/oracle/instantclient_21_1"

# Extract Oracle Instant Client
if [ -f "instantclient-basic-linux.x64-${ORACLE_CLIENT_VERSION}dbru.zip" ]; then
    echo "Extracting Oracle Instant Client Basic..."
    sudo unzip instantclient-basic-linux.x64-${ORACLE_CLIENT_VERSION}dbru.zip -d /opt/oracle/
fi

if [ -f "instantclient-sdk-linux.x64-${ORACLE_CLIENT_VERSION}dbru.zip" ]; then
    echo "Extracting Oracle Instant Client SDK..."
    sudo unzip instantclient-sdk-linux.x64-${ORACLE_CLIENT_VERSION}dbru.zip -d /opt/oracle/
fi

if [ -f "instantclient-sqlplus-linux.x64-${ORACLE_CLIENT_VERSION}dbru.zip" ]; then
    echo "Extracting Oracle SQLPlus..."
    sudo unzip instantclient-sqlplus-linux.x64-${ORACLE_CLIENT_VERSION}dbru.zip -d /opt/oracle/
fi

# Install required libraries
echo "Installing required libraries..."
sudo apt-get install -y libaio1 libaio-dev

# Set up environment variables
echo "Setting up environment variables..."
cat << EOF | sudo tee /etc/profile.d/oracle.sh
export ORACLE_HOME=/opt/oracle/instantclient_21_1
export LD_LIBRARY_PATH=\$ORACLE_HOME:\$LD_LIBRARY_PATH
export PATH=\$ORACLE_HOME:\$PATH
export TNS_ADMIN=\$ORACLE_HOME
EOF

# Source the environment
source /etc/profile.d/oracle.sh

# Create symbolic links if needed
sudo ln -sf ${ORACLE_CLIENT_DIR}/libclntsh.so.21.1 ${ORACLE_CLIENT_DIR}/libclntsh.so
sudo ln -sf ${ORACLE_CLIENT_DIR}/libocci.so.21.1 ${ORACLE_CLIENT_DIR}/libocci.so

# Test Oracle client installation
echo "Testing Oracle client installation..."
${ORACLE_CLIENT_DIR}/sqlplus -version

echo "=== Oracle Instant Client Installation Complete ==="
```

---

## Oracle Database Deployment

### 1. Oracle Database Setup

```sql
-- database-setup.sql
-- HDFC Card Limit System - Oracle Database Setup

-- Create tablespaces
CREATE TABLESPACE hdfc_card_data
DATAFILE '/opt/oracle/oradata/XE/hdfc_card_data01.dbf' SIZE 1G
AUTOEXTEND ON NEXT 100M MAXSIZE 10G
LOGGING
ONLINE
PERMANENT
BLOCKSIZE 8192
EXTENT MANAGEMENT LOCAL AUTOALLOCATE
SEGMENT SPACE MANAGEMENT AUTO;

CREATE TABLESPACE hdfc_card_index
DATAFILE '/opt/oracle/oradata/XE/hdfc_card_index01.dbf' SIZE 500M
AUTOEXTEND ON NEXT 50M MAXSIZE 5G
LOGGING
ONLINE
PERMANENT
BLOCKSIZE 8192
EXTENT MANAGEMENT LOCAL AUTOALLOCATE
SEGMENT SPACE MANAGEMENT AUTO;

CREATE TEMPORARY TABLESPACE hdfc_card_temp
TEMPFILE '/opt/oracle/oradata/XE/hdfc_card_temp01.dbf' SIZE 200M
AUTOEXTEND ON NEXT 50M MAXSIZE 2G
EXTENT MANAGEMENT LOCAL UNIFORM SIZE 1M;

-- Create user
CREATE USER hdfc_card_system IDENTIFIED BY "SecurePassword123!"
DEFAULT TABLESPACE hdfc_card_data
TEMPORARY TABLESPACE hdfc_card_temp
QUOTA UNLIMITED ON hdfc_card_data
QUOTA UNLIMITED ON hdfc_card_index;

-- Grant privileges
GRANT CONNECT TO hdfc_card_system;
GRANT RESOURCE TO hdfc_card_system;
GRANT CREATE VIEW TO hdfc_card_system;
GRANT CREATE SEQUENCE TO hdfc_card_system;
GRANT CREATE SYNONYM TO hdfc_card_system;
GRANT CREATE PROCEDURE TO hdfc_card_system;
GRANT CREATE TRIGGER TO hdfc_card_system;
GRANT CREATE MATERIALIZED VIEW TO hdfc_card_system;

-- Grant system privileges for advanced features
GRANT CREATE JOB TO hdfc_card_system;
GRANT MANAGE SCHEDULER TO hdfc_card_system;

-- Additional grants for monitoring
GRANT SELECT ON V_$SESSION TO hdfc_card_system;
GRANT SELECT ON V_$SQLAREA TO hdfc_card_system;
GRANT SELECT ON V_$SQL TO hdfc_card_system;
GRANT SELECT ON V_$PROCESS TO hdfc_card_system;

-- Create directories for external files
CREATE OR REPLACE DIRECTORY HDFC_IMPORT_DIR AS '/opt/oracle/import';
CREATE OR REPLACE DIRECTORY HDFC_EXPORT_DIR AS '/opt/oracle/export';
CREATE OR REPLACE DIRECTORY HDFC_LOG_DIR AS '/opt/oracle/logs';

GRANT READ, WRITE ON DIRECTORY HDFC_IMPORT_DIR TO hdfc_card_system;
GRANT READ, WRITE ON DIRECTORY HDFC_EXPORT_DIR TO hdfc_card_system;
GRANT READ, WRITE ON DIRECTORY HDFC_LOG_DIR TO hdfc_card_system;

-- Enable database features
ALTER SYSTEM SET open_cursors=1000 SCOPE=BOTH;
ALTER SYSTEM SET processes=500 SCOPE=SPFILE;
ALTER SYSTEM SET sessions=555 SCOPE=SPFILE;
ALTER SYSTEM SET db_files=1000 SCOPE=SPFILE;

-- Configure memory parameters
ALTER SYSTEM SET memory_target=2G SCOPE=SPFILE;
ALTER SYSTEM SET memory_max_target=4G SCOPE=SPFILE;
ALTER SYSTEM SET pga_aggregate_target=512M SCOPE=BOTH;
ALTER SYSTEM SET sga_target=1G SCOPE=SPFILE;

-- Enable auditing
AUDIT ALL ON hdfc_card_system.core_customer BY ACCESS;
AUDIT ALL ON hdfc_card_system.requests_limitrequest BY ACCESS;
AUDIT ALL ON hdfc_card_system.accounts_customercard BY ACCESS;

-- Commit changes
COMMIT;

-- Display setup summary
SELECT 'Database setup completed' AS status FROM dual;
SELECT tablespace_name, status FROM dba_tablespaces WHERE tablespace_name LIKE 'HDFC_CARD%';
SELECT username, default_tablespace, temporary_tablespace FROM dba_users WHERE username = 'HDFC_CARD_SYSTEM';
```

### 2. Database Configuration Script

```bash
# configure-oracle-database.sh
#!/bin/bash

set -e

echo "=== Configuring Oracle Database for HDFC Card Limit System ==="

# Database connection parameters
ORACLE_SID=${ORACLE_SID:-XE}
ORACLE_USER=${ORACLE_USER:-sys}
ORACLE_PASSWORD=${ORACLE_PASSWORD:-oracle}
ORACLE_HOST=${ORACLE_HOST:-localhost}
ORACLE_PORT=${ORACLE_PORT:-1521}

# Application database parameters
APP_USER="hdfc_card_system"
APP_PASSWORD="SecurePassword123!"

echo "Connecting to Oracle database..."

# Test database connection
sqlplus -S "${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_HOST}:${ORACLE_PORT}/${ORACLE_SID} as sysdba" << EOF
SELECT 'Database connection successful' AS status FROM dual;
EXIT;
EOF

if [ $? -eq 0 ]; then
    echo "✓ Database connection successful"
else
    echo "✗ Database connection failed"
    exit 1
fi

# Run database setup script
echo "Running database setup script..."
sqlplus -S "${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_HOST}:${ORACLE_PORT}/${ORACLE_SID} as sysdba" @database-setup.sql

# Test application user connection
echo "Testing application user connection..."
sqlplus -S "${APP_USER}/${APP_PASSWORD}@${ORACLE_HOST}:${ORACLE_PORT}/${ORACLE_SID}" << EOF
SELECT 'Application user connection successful' AS status FROM dual;
SELECT user, sysdate FROM dual;
EXIT;
EOF

if [ $? -eq 0 ]; then
    echo "✓ Application user setup successful"
else
    echo "✗ Application user setup failed"
    exit 1
fi

# Create TNS entry
echo "Creating TNS entry..."
cat << EOF > ${ORACLE_HOME}/network/admin/tnsnames.ora
HDFC_CARD_DB =
  (DESCRIPTION =
    (ADDRESS_LIST =
      (ADDRESS = (PROTOCOL = TCP)(HOST = ${ORACLE_HOST})(PORT = ${ORACLE_PORT}))
    )
    (CONNECT_DATA =
      (SERVICE_NAME = ${ORACLE_SID})
    )
  )
EOF

echo "=== Oracle Database Configuration Complete ==="
```

### 3. Database Migration Deployment

```python
# scripts/deploy_migrations.py
#!/usr/bin/env python3
"""
Deploy database migrations to Oracle database
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection, transaction
import cx_Oracle

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'card_limit_system.settings.production')
django.setup()

class DatabaseMigrationDeployer:
    """
    Deploy database migrations with validation and rollback capability
    """
    
    def __init__(self):
        self.migration_history = []
    
    def validate_database_connection(self):
        """Validate database connection before deployment"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                
            if result[0] == 1:
                print("✓ Database connection validated")
                return True
            else:
                print("✗ Database connection validation failed")
                return False
                
        except Exception as e:
            print(f"✗ Database connection error: {str(e)}")
            return False
    
    def backup_database_schema(self):
        """Create schema backup before migration"""
        try:
            backup_script = f"""
            expdp hdfc_card_system/SecurePassword123! \
            directory=HDFC_EXPORT_DIR \
            dumpfile=schema_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dmp \
            logfile=schema_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log \
            schemas=hdfc_card_system
            """
            
            os.system(backup_script)
            print("✓ Database schema backup created")
            return True
            
        except Exception as e:
            print(f"✗ Schema backup failed: {str(e)}")
            return False
    
    def run_migrations(self, app_name=None, migration_name=None):
        """Run Django migrations"""
        try:
            print("Starting database migrations...")
            
            # Run showmigrations to see current state
            print("Current migration status:")
            execute_from_command_line(['manage.py', 'showmigrations'])
            
            # Run migrations
            if app_name and migration_name:
                execute_from_command_line(['manage.py', 'migrate', app_name, migration_name])
            elif app_name:
                execute_from_command_line(['manage.py', 'migrate', app_name])
            else:
                execute_from_command_line(['manage.py', 'migrate'])
            
            print("✓ Database migrations completed successfully")
            return True
            
        except Exception as e:
            print(f"✗ Migration failed: {str(e)}")
            return False
    
    def validate_migration_results(self):
        """Validate migration results"""
        try:
            # Check if all expected tables exist
            expected_tables = [
                'core_customer',
                'accounts_customercard',
                'accounts_netbankingaccount',
                'requests_limitrequest',
                'requests_otpverification',
                'notifications_notification',
                'analytics_systemmetric'
            ]
            
            with connection.cursor() as cursor:
                for table in expected_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM user_tables WHERE table_name = UPPER('{table}')")
                    count = cursor.fetchone()[0]
                    
                    if count == 1:
                        print(f"✓ Table {table} exists")
                    else:
                        print(f"✗ Table {table} missing")
                        return False
            
            print("✓ Migration validation successful")
            return True
            
        except Exception as e:
            print(f"✗ Migration validation failed: {str(e)}")
            return False
    
    def deploy_stored_procedures(self):
        """Deploy stored procedures and functions"""
        try:
            procedures_dir = os.path.join(project_dir, 'database', 'procedures')
            
            if os.path.exists(procedures_dir):
                for filename in os.listdir(procedures_dir):
                    if filename.endswith('.sql'):
                        procedure_file = os.path.join(procedures_dir, filename)
                        
                        with open(procedure_file, 'r') as f:
                            procedure_sql = f.read()
                        
                        with connection.cursor() as cursor:
                            cursor.execute(procedure_sql)
                        
                        print(f"✓ Deployed procedure: {filename}")
            
            print("✓ Stored procedures deployment completed")
            return True
            
        except Exception as e:
            print(f"✗ Stored procedures deployment failed: {str(e)}")
            return False
    
    def deploy(self, backup=True, validate=True):
        """Main deployment method"""
        print("=== Database Migration Deployment ===")
        
        # Step 1: Validate connection
        if not self.validate_database_connection():
            return False
        
        # Step 2: Create backup (optional)
        if backup and not self.backup_database_schema():
            print("Warning: Schema backup failed, continuing anyway...")
        
        # Step 3: Run migrations
        if not self.run_migrations():
            return False
        
        # Step 4: Validate results
        if validate and not self.validate_migration_results():
            return False
        
        # Step 5: Deploy stored procedures
        if not self.deploy_stored_procedures():
            return False
        
        print("=== Database Migration Deployment Complete ===")
        return True

if __name__ == "__main__":
    deployer = DatabaseMigrationDeployer()
    
    # Parse command line arguments
    backup = '--no-backup' not in sys.argv
    validate = '--no-validate' not in sys.argv
    
    success = deployer.deploy(backup=backup, validate=validate)
    
    if success:
        print("Database deployment successful!")
        sys.exit(0)
    else:
        print("Database deployment failed!")
        sys.exit(1)
```

---

## Django Application Deployment

### 1. Application Build Script

```bash
# build-application.sh
#!/bin/bash

set -e

echo "=== Building HDFC Card Limit System Application ==="

# Configuration
PROJECT_DIR="/opt/hdfc-card-system"
VENV_DIR="${PROJECT_DIR}/venv"
STATIC_DIR="${PROJECT_DIR}/static"
MEDIA_DIR="${PROJECT_DIR}/media"
LOG_DIR="/var/log/hdfc-card-system"

# Create directories
echo "Creating application directories..."
sudo mkdir -p ${PROJECT_DIR}
sudo mkdir -p ${STATIC_DIR}
sudo mkdir -p ${MEDIA_DIR}
sudo mkdir -p ${LOG_DIR}
sudo mkdir -p ${PROJECT_DIR}/config

# Set permissions
sudo chown -R hdfc-app:hdfc-app ${PROJECT_DIR}
sudo chown -R hdfc-app:hdfc-app ${LOG_DIR}
sudo chmod 755 ${PROJECT_DIR}
sudo chmod 755 ${LOG_DIR}

# Clone repository (assuming code is in git)
echo "Cloning application repository..."
cd ${PROJECT_DIR}
git clone https://github.com/hdfc/card-limit-system.git .

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3.9 -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements/production.txt

# Install Oracle client Python library
pip install cx_Oracle

# Collect static files
echo "Collecting static files..."
export DJANGO_SETTINGS_MODULE=card_limit_system.settings.production
python manage.py collectstatic --noinput

# Compile messages (if using internationalization)
echo "Compiling translation messages..."
python manage.py compilemessages

# Run tests
echo "Running application tests..."
python manage.py test --settings=card_limit_system.settings.testing

# Create systemd service file
echo "Creating systemd service file..."
sudo tee /etc/systemd/system/hdfc-card-system.service > /dev/null << EOF
[Unit]
Description=HDFC Card Limit System Django Application
After=network.target oracle.service

[Service]
Type=notify
User=hdfc-app
Group=hdfc-app
WorkingDirectory=${PROJECT_DIR}
Environment=DJANGO_SETTINGS_MODULE=card_limit_system.settings.production
Environment=PYTHONPATH=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/gunicorn card_limit_system.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 120 \
    --keep-alive 2 \
    --log-level info \
    --log-file ${LOG_DIR}/gunicorn.log \
    --access-logfile ${LOG_DIR}/gunicorn-access.log \
    --error-logfile ${LOG_DIR}/gunicorn-error.log \
    --pid /run/hdfc-card-system/gunicorn.pid
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Create Celery worker service
echo "Creating Celery worker service..."
sudo tee /etc/systemd/system/hdfc-card-system-worker.service > /dev/null << EOF
[Unit]
Description=HDFC Card Limit System Celery Worker
After=network.target redis.service oracle.service

[Service]
Type=forking
User=hdfc-app
Group=hdfc-app
WorkingDirectory=${PROJECT_DIR}
Environment=DJANGO_SETTINGS_MODULE=card_limit_system.settings.production
Environment=PYTHONPATH=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/celery -A card_limit_system worker \
    --detach \
    --loglevel=info \
    --logfile=${LOG_DIR}/celery-worker.log \
    --pidfile=/run/hdfc-card-system/celery-worker.pid \
    --concurrency=4
ExecStop=/bin/kill -s TERM \$MAINPID
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Celery beat service (for scheduled tasks)
echo "Creating Celery beat service..."
sudo tee /etc/systemd/system/hdfc-card-system-beat.service > /dev/null << EOF
[Unit]
Description=HDFC Card Limit System Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=hdfc-app
Group=hdfc-app
WorkingDirectory=${PROJECT_DIR}
Environment=DJANGO_SETTINGS_MODULE=card_limit_system.settings.production
Environment=PYTHONPATH=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/celery -A card_limit_system beat \
    --loglevel=info \
    --logfile=${LOG_DIR}/celery-beat.log \
    --pidfile=/run/hdfc-card-system/celery-beat.pid
KillMode=mixed
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create run directory
sudo mkdir -p /run/hdfc-card-system
sudo chown hdfc-app:hdfc-app /run/hdfc-card-system

# Reload systemd and enable services
echo "Enabling systemd services..."
sudo systemctl daemon-reload
sudo systemctl enable hdfc-card-system
sudo systemctl enable hdfc-card-system-worker
sudo systemctl enable hdfc-card-system-beat

echo "=== Application Build Complete ==="
```

### 2. Nginx Configuration

```nginx
# /etc/nginx/sites-available/hdfc-card-system
# HDFC Card Limit System Nginx Configuration

upstream hdfc_card_system {
    server 127.0.0.1:8000;
    # Add more servers for load balancing
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general:10m rate=20r/s;

# Cache zones
proxy_cache_path /var/cache/nginx/hdfc_card_system 
    levels=1:2 
    keys_zone=hdfc_cache:10m 
    max_size=1g 
    inactive=60m 
    use_temp_path=off;

server {
    listen 80;
    server_name api.hdfc-card-limit.com;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.hdfc-card-limit.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/hdfc-card-system.crt;
    ssl_certificate_key /etc/ssl/private/hdfc-card-system.key;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    
    # Modern configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https:; frame-ancestors 'none';" always;
    
    # Basic settings
    root /opt/hdfc-card-system;
    index index.html;
    
    # Maximum file upload size
    client_max_body_size 10M;
    
    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/x-javascript
        application/xml+rss
        application/json;
    
    # API endpoints with rate limiting
    location /api/v1/auth/login/ {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://hdfc_card_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Disable caching for authentication endpoints
        proxy_cache off;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    location /api/v1/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://hdfc_card_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Enable caching for GET requests
        proxy_cache hdfc_cache;
        proxy_cache_methods GET HEAD;
        proxy_cache_valid 200 5m;
        proxy_cache_valid 404 1m;
        proxy_cache_use_stale error timeout http_500 http_502 http_503 http_504;
        proxy_cache_bypass $cookie_nocache $arg_nocache;
        add_header X-Cache-Status $upstream_cache_status;
    }
    
    # Static files
    location /static/ {
        alias /opt/hdfc-card-system/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Compression for static files
        gzip_static on;
    }
    
    # Media files
    location /media/ {
        alias /opt/hdfc-card-system/media/;
        expires 1M;
        add_header Cache-Control "public";
    }
    
    # Health check endpoint
    location /health/ {
        proxy_pass http://hdfc_card_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        access_log off;
    }
    
    # Default location with general rate limiting
    location / {
        limit_req zone=general burst=50 nodelay;
        proxy_pass http://hdfc_card_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    location = /404.html {
        internal;
    }
    
    location = /50x.html {
        internal;
    }
    
    # Access and error logs
    access_log /var/log/nginx/hdfc-card-system-access.log;
    error_log /var/log/nginx/hdfc-card-system-error.log;
}

# Admin interface (if needed, with additional security)
server {
    listen 443 ssl http2;
    server_name admin.hdfc-card-limit.com;
    
    # SSL Configuration (same as API)
    ssl_certificate /etc/ssl/certs/hdfc-card-system.crt;
    ssl_certificate_key /etc/ssl/private/hdfc-card-system.key;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # Additional security for admin interface
    allow 10.0.0.0/8;        # Internal network
    allow 172.16.0.0/12;     # Private network
    allow 192.168.0.0/16;    # Local network
    deny all;                # Deny all other IPs
    
    location /admin/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://hdfc_card_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # No caching for admin
        proxy_cache off;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # Static files for admin
    location /static/ {
        alias /opt/hdfc-card-system/static/;
        expires 1d;
    }
}
```

---

## Containerization with Docker

### 1. Dockerfile

```dockerfile
# Dockerfile
# HDFC Card Limit System - Production Docker Image

# Multi-stage build for optimized image size
FROM python:3.9-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libaio1 \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linuxx64.zip && \
    wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-devel-linuxx64.zip && \
    unzip instantclient-basiclite-linuxx64.zip && \
    unzip instantclient-devel-linuxx64.zip && \
    rm *.zip && \
    echo /opt/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

# Set Oracle environment variables
ENV ORACLE_HOME=/opt/oracle/instantclient_21_1 \
    LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH \
    PATH=/opt/oracle/instantclient_21_1:$PATH

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements/ /tmp/requirements/
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements/production.txt

# Production stage
FROM python:3.9-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libaio1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Oracle Instant Client from builder
COPY --from=builder /opt/oracle /opt/oracle
COPY --from=builder /etc/ld.so.conf.d/oracle-instantclient.conf /etc/ld.so.conf.d/
RUN ldconfig

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set Oracle environment variables
ENV ORACLE_HOME=/opt/oracle/instantclient_21_1 \
    LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH \
    PATH=/opt/oracle/instantclient_21_1:$PATH

# Create app user
RUN groupadd -r hdfc-app && useradd -r -g hdfc-app hdfc-app

# Create application directories
RUN mkdir -p /opt/hdfc-card-system /var/log/hdfc-card-system && \
    chown -R hdfc-app:hdfc-app /opt/hdfc-card-system /var/log/hdfc-card-system

# Set working directory
WORKDIR /opt/hdfc-card-system

# Copy application code
COPY --chown=hdfc-app:hdfc-app . .

# Create necessary directories
RUN mkdir -p static media logs && \
    chown -R hdfc-app:hdfc-app static media logs

# Switch to app user
USER hdfc-app

# Collect static files
RUN python manage.py collectstatic --noinput --settings=card_limit_system.settings.production

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "card_limit_system.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gevent", \
     "--worker-connections", "1000", \
     "--timeout", "120", \
     "--keep-alive", "2", \
     "--log-level", "info"]
```

### 2. Docker Compose Configuration

```yaml
# docker-compose.yml
# HDFC Card Limit System - Docker Compose Configuration

version: '3.8'

services:
  # Django Application
  web:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    image: hdfc-card-system:latest
    container_name: hdfc-card-system-web
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=card_limit_system.settings.production
      - DATABASE_URL=oracle://hdfc_card_system:SecurePassword123!@oracle:1521/XE
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - static_volume:/opt/hdfc-card-system/static
      - media_volume:/opt/hdfc-card-system/media
      - ./logs:/var/log/hdfc-card-system
    depends_on:
      - oracle
      - redis
    networks:
      - hdfc-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.hdfc-api.rule=Host(`api.hdfc-card-limit.com`)"
      - "traefik.http.routers.hdfc-api.tls=true"
      - "traefik.http.routers.hdfc-api.tls.certresolver=letsencrypt"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    image: hdfc-card-system:latest
    container_name: hdfc-card-system-worker
    restart: unless-stopped
    command: celery -A card_limit_system worker --loglevel=info --concurrency=4
    environment:
      - DJANGO_SETTINGS_MODULE=card_limit_system.settings.production
      - DATABASE_URL=oracle://hdfc_card_system:SecurePassword123!@oracle:1521/XE
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - ./logs:/var/log/hdfc-card-system
    depends_on:
      - oracle
      - redis
    networks:
      - hdfc-network

  # Celery Beat Scheduler
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    image: hdfc-card-system:latest
    container_name: hdfc-card-system-beat
    restart: unless-stopped
    command: celery -A card_limit_system beat --loglevel=info
    environment:
      - DJANGO_SETTINGS_MODULE=card_limit_system.settings.production
      - DATABASE_URL=oracle://hdfc_card_system:SecurePassword123!@oracle:1521/XE
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - ./logs:/var/log/hdfc-card-system
    depends_on:
      - oracle
      - redis
    networks:
      - hdfc-network

  # Oracle Database
  oracle:
    image: container-registry.oracle.com/database/express:21.3.0-xe
    container_name: hdfc-card-system-oracle
    restart: unless-stopped
    ports:
      - "1521:1521"
      - "5500:5500"
    environment:
      - ORACLE_PWD=OraclePassword123!
      - ORACLE_CHARACTERSET=AL32UTF8
    volumes:
      - oracle_data:/opt/oracle/oradata
      - ./database/scripts:/opt/oracle/scripts/setup
    networks:
      - hdfc-network
    healthcheck:
      test: ["CMD", "sqlplus", "-s", "sys/OraclePassword123!@localhost:1521/XE as sysdba", "<<<", "SELECT 1 FROM DUAL;"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: hdfc-card-system-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass RedisPassword123!
    volumes:
      - redis_data:/data
    networks:
      - hdfc-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: hdfc-card-system-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/sites-available:/etc/nginx/sites-available:ro
      - ./ssl:/etc/ssl:ro
      - static_volume:/opt/hdfc-card-system/static:ro
      - media_volume:/opt/hdfc-card-system/media:ro
    depends_on:
      - web
    networks:
      - hdfc-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.nginx.rule=Host(`www.hdfc-card-limit.com`)"

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: hdfc-card-system-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - hdfc-network

  # Grafana Dashboard
  grafana:
    image: grafana/grafana:latest
    container_name: hdfc-card-system-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=GrafanaPassword123!
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - hdfc-network

volumes:
  static_volume:
  media_volume:
  oracle_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  hdfc-network:
    driver: bridge
```

### 3. Docker Build Script

```bash
# build-docker-image.sh
#!/bin/bash

set -e

echo "=== Building HDFC Card Limit System Docker Image ==="

# Configuration
IMAGE_NAME="hdfc-card-system"
TAG=${1:-latest}
REGISTRY=${DOCKER_REGISTRY:-}
BUILD_ARGS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --no-cache)
            BUILD_ARGS="$BUILD_ARGS --no-cache"
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${TAG}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"
fi

echo "Building image: $FULL_IMAGE_NAME"

# Build Docker image
docker build $BUILD_ARGS -t $FULL_IMAGE_NAME .

# Tag with latest if not already latest
if [ "$TAG" != "latest" ]; then
    if [ -n "$REGISTRY" ]; then
        docker tag $FULL_IMAGE_NAME "${REGISTRY}/${IMAGE_NAME}:latest"
    else
        docker tag $FULL_IMAGE_NAME "${IMAGE_NAME}:latest"
    fi
fi

# Run security scan
echo "Running security scan..."
if command -v trivy &> /dev/null; then
    trivy image $FULL_IMAGE_NAME
else
    echo "Trivy not found, skipping security scan"
fi

# Push to registry if requested
if [ "$PUSH_IMAGE" = true ] && [ -n "$REGISTRY" ]; then
    echo "Pushing image to registry..."
    docker push $FULL_IMAGE_NAME
    
    if [ "$TAG" != "latest" ]; then
        docker push "${REGISTRY}/${IMAGE_NAME}:latest"
    fi
fi

# Display image information
echo "=== Build Complete ==="
echo "Image: $FULL_IMAGE_NAME"
echo "Size: $(docker images $FULL_IMAGE_NAME --format 'table {{.Size}}' | tail -n 1)"
echo "Created: $(docker images $FULL_IMAGE_NAME --format 'table {{.CreatedAt}}' | tail -n 1)"

# Test container
echo "Testing container startup..."
CONTAINER_ID=$(docker run -d --rm -p 8001:8000 $FULL_IMAGE_NAME)

# Wait for container to start
sleep 10

# Test health endpoint
if curl -f http://localhost:8001/health/ > /dev/null 2>&1; then
    echo "✓ Container health check passed"
else
    echo "✗ Container health check failed"
    docker logs $CONTAINER_ID
fi

# Stop test container
docker stop $CONTAINER_ID

echo "=== Docker Build Complete ==="
```

---

## Kubernetes Deployment

### 1. Kubernetes Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: hdfc-card-system
  labels:
    name: hdfc-card-system
    environment: production

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hdfc-card-system-config
  namespace: hdfc-card-system
data:
  DJANGO_SETTINGS_MODULE: "card_limit_system.settings.production"
  CELERY_BROKER_URL: "redis://redis-service:6379/0"
  REDIS_URL: "redis://redis-service:6379/0"
  ORACLE_HOST: "oracle-service"
  ORACLE_PORT: "1521"
  ORACLE_SERVICE_NAME: "XE"

---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: hdfc-card-system-secrets
  namespace: hdfc-card-system
type: Opaque
data:
  # Base64 encoded values
  ORACLE_USER: aGRmY19jYXJkX3N5c3RlbQ==  # hdfc_card_system
  ORACLE_PASSWORD: U2VjdXJlUGFzc3dvcmQxMjMh  # SecurePassword123!
  REDIS_PASSWORD: UmVkaXNQYXNzd29yZDEyMyE=  # RedisPassword123!
  DJANGO_SECRET_KEY: <base64-encoded-secret-key>
  FIREBASE_SERVICE_ACCOUNT_KEY: <base64-encoded-firebase-key>
  TWILIO_AUTH_TOKEN: <base64-encoded-twilio-token>
  SENDGRID_API_KEY: <base64-encoded-sendgrid-key>
  ONESIGNAL_REST_API_KEY: <base64-encoded-onesignal-key>

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hdfc-card-system-web
  namespace: hdfc-card-system
  labels:
    app: hdfc-card-system
    component: web
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: hdfc-card-system
      component: web
  template:
    metadata:
      labels:
        app: hdfc-card-system
        component: web
    spec:
      serviceAccountName: hdfc-card-system
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: web
        image: hdfc-card-system:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DJANGO_SETTINGS_MODULE
          valueFrom:
            configMapKeyRef:
              name: hdfc-card-system-config
              key: DJANGO_SETTINGS_MODULE
        - name: ORACLE_USER
          valueFrom:
            secretKeyRef:
              name: hdfc-card-system-secrets
              key: ORACLE_USER
        - name: ORACLE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: hdfc-card-system-secrets
              key: ORACLE_PASSWORD
        - name: DJANGO_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: hdfc-card-system-secrets
              key: DJANGO_SECRET_KEY
        - name: DATABASE_URL
          value: "oracle://$(ORACLE_USER):$(ORACLE_PASSWORD)@oracle-service:1521/XE"
        envFrom:
        - configMapRef:
            name: hdfc-card-system-config
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: static-storage
          mountPath: /opt/hdfc-card-system/static
        - name: media-storage
          mountPath: /opt/hdfc-card-system/media
        - name: logs
          mountPath: /var/log/hdfc-card-system
      volumes:
      - name: static-storage
        persistentVolumeClaim:
          claimName: static-pvc
      - name: media-storage
        persistentVolumeClaim:
          claimName: media-pvc
      - name: logs
        emptyDir: {}

---
# k8s/celery-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hdfc-card-system-worker
  namespace: hdfc-card-system
  labels:
    app: hdfc-card-system
    component: worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hdfc-card-system
      component: worker
  template:
    metadata:
      labels:
        app: hdfc-card-system
        component: worker
    spec:
      serviceAccountName: hdfc-card-system
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: worker
        image: hdfc-card-system:latest
        imagePullPolicy: Always
        command: ["celery"]
        args: ["-A", "card_limit_system", "worker", "--loglevel=info", "--concurrency=4"]
        envFrom:
        - configMapRef:
            name: hdfc-card-system-config
        - secretRef:
            name: hdfc-card-system-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: logs
          mountPath: /var/log/hdfc-card-system
      volumes:
      - name: logs
        emptyDir: {}

---
# k8s/celery-beat-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hdfc-card-system-beat
  namespace: hdfc-card-system
  labels:
    app: hdfc-card-system
    component: beat
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hdfc-card-system
      component: beat
  template:
    metadata:
      labels:
        app: hdfc-card-system
        component: beat
    spec:
      serviceAccountName: hdfc-card-system
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: beat
        image: hdfc-card-system:latest
        imagePullPolicy: Always
        command: ["celery"]
        args: ["-A", "card_limit_system", "beat", "--loglevel=info"]
        envFrom:
        - configMapRef:
            name: hdfc-card-system-config
        - secretRef:
            name: hdfc-card-system-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: hdfc-card-system-service
  namespace: hdfc-card-system
  labels:
    app: hdfc-card-system
    component: web
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  selector:
    app: hdfc-card-system
    component: web

---
# k8s/oracle-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: oracle-service
  namespace: hdfc-card-system
spec:
  type: ClusterIP
  ports:
  - port: 1521
    targetPort: 1521
    name: oracle
  selector:
    app: oracle-db

---
# k8s/redis-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: hdfc-card-system
spec:
  type: ClusterIP
  ports:
  - port: 6379
    targetPort: 6379
    name: redis
  selector:
    app: redis

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hdfc-card-system-ingress
  namespace: hdfc-card-system
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "20"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
spec:
  tls:
  - hosts:
    - api.hdfc-card-limit.com
    secretName: hdfc-card-system-tls
  rules:
  - host: api.hdfc-card-limit.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hdfc-card-system-service
            port:
              number: 8000

---
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hdfc-card-system-hpa
  namespace: hdfc-card-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hdfc-card-system-web
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60

---
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: static-pvc
  namespace: hdfc-card-system
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 5Gi
  storageClassName: nfs-client

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: media-pvc
  namespace: hdfc-card-system
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  storageClassName: nfs-client
```

### 2. Kubernetes Deployment Script

```bash
# deploy-kubernetes.sh
#!/bin/bash

set -e

echo "=== Deploying HDFC Card Limit System to Kubernetes ==="

# Configuration
NAMESPACE="hdfc-card-system"
IMAGE_TAG=${1:-latest}
ENVIRONMENT=${2:-production}

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo "✗ kubectl is not configured or cluster is not accessible"
    exit 1
fi

echo "✓ Kubernetes cluster is accessible"

# Create namespace if it doesn't exist
echo "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Apply ConfigMaps and Secrets
echo "Applying configuration..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Apply PVCs
echo "Creating persistent volumes..."
kubectl apply -f k8s/pvc.yaml

# Wait for PVCs to be bound
echo "Waiting for persistent volumes to be ready..."
kubectl wait --for=condition=Bound pvc/static-pvc -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=Bound pvc/media-pvc -n $NAMESPACE --timeout=300s

# Deploy Oracle Database (if not external)
if [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "staging" ]; then
    echo "Deploying Oracle database..."
    kubectl apply -f k8s/oracle-deployment.yaml
    kubectl apply -f k8s/oracle-service.yaml
    
    # Wait for Oracle to be ready
    echo "Waiting for Oracle database to be ready..."
    kubectl wait --for=condition=Available deployment/oracle-db -n $NAMESPACE --timeout=600s
fi

# Deploy Redis
echo "Deploying Redis..."
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=Available deployment/redis -n $NAMESPACE --timeout=300s

# Run database migrations
echo "Running database migrations..."
kubectl run migration-job \
    --image=hdfc-card-system:$IMAGE_TAG \
    --rm -i --restart=Never \
    --namespace=$NAMESPACE \
    --env="DJANGO_SETTINGS_MODULE=card_limit_system.settings.$ENVIRONMENT" \
    --command -- python manage.py migrate

# Deploy main application
echo "Deploying main application..."
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Deploy Celery workers
echo "Deploying Celery workers..."
kubectl apply -f k8s/celery-worker-deployment.yaml
kubectl apply -f k8s/celery-beat-deployment.yaml

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=Available deployment/hdfc-card-system-web -n $NAMESPACE --timeout=600s
kubectl wait --for=condition=Available deployment/hdfc-card-system-worker -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=Available deployment/hdfc-card-system-beat -n $NAMESPACE --timeout=300s

# Apply Ingress
echo "Applying ingress configuration..."
kubectl apply -f k8s/ingress.yaml

# Apply HPA
echo "Applying horizontal pod autoscaler..."
kubectl apply -f k8s/hpa.yaml

# Display deployment status
echo "=== Deployment Status ==="
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE
kubectl get ingress -n $NAMESPACE

# Test deployment
echo "Testing deployment..."
APP_URL=$(kubectl get ingress hdfc-card-system-ingress -n $NAMESPACE -o jsonpath='{.spec.rules[0].host}')

if [ -n "$APP_URL" ]; then
    echo "Application will be available at: https://$APP_URL"
    
    # Wait a bit for ingress to be ready
    sleep 30
    
    # Test health endpoint
    if curl -f -k "https://$APP_URL/health/" > /dev/null 2>&1; then
        echo "✓ Application health check passed"
    else
        echo "⚠ Application health check failed (may take a few minutes to be ready)"
    fi
else
    echo "⚠ Ingress URL not available"
fi

echo "=== Kubernetes Deployment Complete ==="

# Show useful commands
cat << EOF

Useful commands:
- View pods: kubectl get pods -n $NAMESPACE
- View logs: kubectl logs -f deployment/hdfc-card-system-web -n $NAMESPACE
- Scale deployment: kubectl scale deployment hdfc-card-system-web --replicas=5 -n $NAMESPACE
- Delete deployment: kubectl delete namespace $NAMESPACE

EOF
```

This comprehensive Deployment Guide continues with detailed containerization using Docker and Kubernetes deployment configurations. The guide includes multi-stage Docker builds, production-ready Kubernetes manifests, and deployment automation scripts with proper error handling and validation.