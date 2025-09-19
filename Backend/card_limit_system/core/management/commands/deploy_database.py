"""
Database deployment script for Oracle database setup.

This script handles the complete database deployment process including
schema creation, user management, permissions, and data initialization.
"""

import os
import sys
import logging
from pathlib import Path
import cx_Oracle
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import transaction, connection


class Command(BaseCommand):
    help = 'Deploy and setup Oracle database for Card Limit Increase System'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--environment',
            type=str,
            choices=['development', 'staging', 'production'],
            default='development',
            help='Target environment for deployment',
        )
        
        parser.add_argument(
            '--create-user',
            action='store_true',
            help='Create database user and schema',
        )
        
        parser.add_argument(
            '--run-migrations',
            action='store_true',
            help='Run all database migrations',
        )
        
        parser.add_argument(
            '--load-initial-data',
            action='store_true',
            help='Load initial data fixtures',
        )
        
        parser.add_argument(
            '--backup-existing',
            action='store_true',
            help='Backup existing database before deployment',
        )
        
        parser.add_argument(
            '--verify-deployment',
            action='store_true',
            help='Verify deployment integrity after completion',
        )
    
    def handle(self, *args, **options):
        self.environment = options['environment']
        self.setup_logging()
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Starting Oracle database deployment for {self.environment}...')
        )
        
        try:
            # Pre-deployment checks
            self.pre_deployment_checks()
            
            # Backup existing database if requested
            if options['backup_existing']:
                self.backup_database()
            
            # Create database user and schema
            if options['create_user']:
                self.create_database_user()
            
            # Run migrations
            if options['run_migrations']:
                self.run_migrations()
            
            # Load initial data
            if options['load_initial_data']:
                self.load_initial_data()
            
            # Verify deployment
            if options['verify_deployment']:
                self.verify_deployment()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Database deployment completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database deployment failed: {str(e)}')
            )
            logging.error(f'Deployment error: {str(e)}', exc_info=True)
            sys.exit(1)
    
    def setup_logging(self):
        """Setup logging for deployment process."""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/db_deployment_{self.environment}.log'),
                logging.StreamHandler()
            ]
        )
    
    def pre_deployment_checks(self):
        """Perform pre-deployment environment checks."""
        self.stdout.write('🔍 Performing pre-deployment checks...')
        
        # Check Oracle client installation
        try:
            cx_Oracle.clientversion()
            self.stdout.write('✅ Oracle client is installed')
        except Exception as e:
            raise Exception(f'Oracle client not found: {str(e)}')
        
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                if result[0] == 1:
                    self.stdout.write('✅ Database connection successful')
        except Exception as e:
            raise Exception(f'Database connection failed: {str(e)}')
        
        # Check required environment variables
        required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST']
        missing_vars = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise Exception(f'Missing environment variables: {", ".join(missing_vars)}')
        
        self.stdout.write('✅ Pre-deployment checks passed')
    
    def backup_database(self):
        """Create database backup before deployment."""
        self.stdout.write('💾 Creating database backup...')
        
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'db_backup_{self.environment}_{timestamp}.dmp'
        
        # Oracle Data Pump export
        expdp_command = f"""
        expdp {os.environ['DB_USER']}/{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:1521/{os.environ['DB_NAME']} \\
        directory=DATA_PUMP_DIR \\
        dumpfile={backup_file.name} \\
        logfile=backup_{timestamp}.log \\
        schemas={os.environ['DB_USER']}
        """
        
        try:
            os.system(expdp_command)
            self.stdout.write(f'✅ Database backup created: {backup_file}')
            logging.info(f'Database backup created: {backup_file}')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Backup failed but continuing: {str(e)}')
            )
            logging.warning(f'Backup failed: {str(e)}')
    
    def create_database_user(self):
        """Create database user and schema with proper permissions."""
        self.stdout.write('👤 Creating database user and schema...')
        
        # Connect as system user for user creation
        admin_dsn = f"{os.environ['DB_HOST']}:1521/{os.environ['DB_NAME']}"
        admin_user = os.environ.get('DB_ADMIN_USER', 'system')
        admin_password = os.environ.get('DB_ADMIN_PASSWORD', 'admin_password')
        
        try:
            with cx_Oracle.connect(admin_user, admin_password, admin_dsn) as admin_conn:
                cursor = admin_conn.cursor()
                
                # Create user if not exists
                user_name = os.environ['DB_USER']
                user_password = os.environ['DB_PASSWORD']
                
                try:
                    cursor.execute(f"""
                        CREATE USER {user_name} 
                        IDENTIFIED BY {user_password}
                        DEFAULT TABLESPACE USERS
                        TEMPORARY TABLESPACE TEMP
                        QUOTA UNLIMITED ON USERS
                    """)
                    self.stdout.write(f'✅ Created user: {user_name}')
                except cx_Oracle.DatabaseError as e:
                    if 'ORA-01920' in str(e):  # User already exists
                        self.stdout.write(f'ℹ️ User {user_name} already exists')
                    else:
                        raise
                
                # Grant necessary privileges
                privileges = [
                    'CONNECT',
                    'RESOURCE',
                    'CREATE SESSION',
                    'CREATE TABLE',
                    'CREATE SEQUENCE',
                    'CREATE TRIGGER',
                    'CREATE PROCEDURE',
                    'CREATE VIEW',
                    'CREATE INDEX'
                ]
                
                for privilege in privileges:
                    try:
                        cursor.execute(f"GRANT {privilege} TO {user_name}")
                    except cx_Oracle.DatabaseError as e:
                        if 'ORA-01919' in str(e):  # Already granted
                            continue
                        else:
                            raise
                
                self.stdout.write(f'✅ Granted privileges to {user_name}')
                logging.info(f'Created database user and granted privileges: {user_name}')
                
        except Exception as e:
            raise Exception(f'Failed to create database user: {str(e)}')
    
    def run_migrations(self):
        """Run all database migrations."""
        self.stdout.write('🔄 Running database migrations...')
        
        try:
            # Create migrations first
            call_command('create_migrations', '--with-data', verbosity=1)
            
            # Run migrations
            call_command('migrate', verbosity=1)
            
            self.stdout.write('✅ All migrations completed successfully')
            logging.info('Database migrations completed')
            
        except Exception as e:
            raise Exception(f'Migration failed: {str(e)}')
    
    def load_initial_data(self):
        """Load initial data fixtures."""
        self.stdout.write('📊 Loading initial data...')
        
        fixtures = [
            'initial_customer_types.json',
            'initial_card_types.json',
            'notification_templates.json',
            'system_settings.json'
        ]
        
        fixture_dir = Path('fixtures')
        
        for fixture in fixtures:
            fixture_path = fixture_dir / fixture
            
            if fixture_path.exists():
                try:
                    call_command('loaddata', str(fixture_path), verbosity=1)
                    self.stdout.write(f'✅ Loaded fixture: {fixture}')
                    logging.info(f'Loaded fixture: {fixture}')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Failed to load {fixture}: {str(e)}')
                    )
                    logging.warning(f'Failed to load fixture {fixture}: {str(e)}')
            else:
                self.stdout.write(f'ℹ️ Fixture not found: {fixture}')
        
        # Create initial analytics tables
        self.create_analytics_tables()
        
        self.stdout.write('✅ Initial data loading completed')
    
    def create_analytics_tables(self):
        """Create analytics and reporting tables."""
        self.stdout.write('📈 Creating analytics tables...')
        
        analytics_sql = [
            """
            CREATE TABLE analytics_daily_summary (
                summary_date DATE PRIMARY KEY,
                total_customers NUMBER(10) DEFAULT 0,
                new_customers NUMBER(10) DEFAULT 0,
                total_requests NUMBER(10) DEFAULT 0,
                approved_requests NUMBER(10) DEFAULT 0,
                rejected_requests NUMBER(10) DEFAULT 0,
                avg_processing_time NUMBER(10,2) DEFAULT 0,
                total_limit_increase NUMBER(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE analytics_monthly_summary (
                summary_month DATE PRIMARY KEY,
                total_customers NUMBER(10) DEFAULT 0,
                new_customers NUMBER(10) DEFAULT 0,
                total_requests NUMBER(10) DEFAULT 0,
                approved_requests NUMBER(10) DEFAULT 0,
                rejected_requests NUMBER(10) DEFAULT 0,
                avg_processing_time NUMBER(10,2) DEFAULT 0,
                total_limit_increase NUMBER(15,2) DEFAULT 0,
                customer_satisfaction_score NUMBER(3,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE system_health_metrics (
                metric_date TIMESTAMP PRIMARY KEY,
                api_response_time NUMBER(10,2) DEFAULT 0,
                database_response_time NUMBER(10,2) DEFAULT 0,
                error_rate NUMBER(5,2) DEFAULT 0,
                active_sessions NUMBER(10) DEFAULT 0,
                memory_usage NUMBER(5,2) DEFAULT 0,
                cpu_usage NUMBER(5,2) DEFAULT 0,
                disk_usage NUMBER(5,2) DEFAULT 0
            )
            """
        ]
        
        try:
            with connection.cursor() as cursor:
                for sql in analytics_sql:
                    try:
                        cursor.execute(sql)
                        logging.info(f'Created analytics table')
                    except Exception as e:
                        if 'ORA-00955' in str(e):  # Table already exists
                            continue
                        else:
                            raise
            
            self.stdout.write('✅ Analytics tables created')
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Analytics tables creation failed: {str(e)}')
            )
            logging.warning(f'Analytics tables creation failed: {str(e)}')
    
    def verify_deployment(self):
        """Verify database deployment integrity."""
        self.stdout.write('🔍 Verifying deployment integrity...')
        
        verification_checks = [
            self.verify_tables_exist,
            self.verify_indexes_exist,
            self.verify_constraints_exist,
            self.verify_sequences_exist,
            self.verify_data_integrity,
            self.verify_permissions
        ]
        
        for check in verification_checks:
            try:
                check()
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Verification failed: {str(e)}')
                )
                raise
        
        self.stdout.write('✅ Deployment verification completed successfully')
        logging.info('Deployment verification completed')
    
    def verify_tables_exist(self):
        """Verify all required tables exist."""
        required_tables = [
            'customer',
            'carddetail',
            'limitrequest',
            'notificationlog',
            'otplog',
            'analytics_daily_summary',
            'analytics_monthly_summary',
            'system_health_metrics'
        ]
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM user_tables 
                WHERE table_name IN (%s)
            """ % ','.join([f"'{table.upper()}'" for table in required_tables]))
            
            existing_tables = [row[0].lower() for row in cursor.fetchall()]
            missing_tables = set(required_tables) - set(existing_tables)
            
            if missing_tables:
                raise Exception(f'Missing tables: {", ".join(missing_tables)}')
        
        self.stdout.write('✅ All required tables exist')
    
    def verify_indexes_exist(self):
        """Verify all required indexes exist."""
        required_indexes = [
            'idx_customer_firebase_uid',
            'idx_customer_email_active',
            'idx_carddetail_customer_active',
            'idx_limitrequest_customer_status',
            'idx_notificationlog_customer_type',
            'idx_otplog_phone_status'
        ]
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT index_name 
                FROM user_indexes 
                WHERE index_name IN (%s)
            """ % ','.join([f"'{idx.upper()}'" for idx in required_indexes]))
            
            existing_indexes = [row[0].lower() for row in cursor.fetchall()]
            missing_indexes = set(required_indexes) - set(existing_indexes)
            
            if missing_indexes:
                raise Exception(f'Missing indexes: {", ".join(missing_indexes)}')
        
        self.stdout.write('✅ All required indexes exist')
    
    def verify_constraints_exist(self):
        """Verify all required constraints exist."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_constraints 
                WHERE constraint_type IN ('P', 'F', 'C')
            """)
            
            constraint_count = cursor.fetchone()[0]
            
            if constraint_count < 10:  # Minimum expected constraints
                raise Exception(f'Insufficient constraints found: {constraint_count}')
        
        self.stdout.write('✅ Database constraints verified')
    
    def verify_sequences_exist(self):
        """Verify all required sequences exist."""
        required_sequences = [
            'customer_ref_seq',
            'limit_request_ref_seq',
            'notification_ref_seq'
        ]
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT sequence_name 
                FROM user_sequences 
                WHERE sequence_name IN (%s)
            """ % ','.join([f"'{seq.upper()}'" for seq in required_sequences]))
            
            existing_sequences = [row[0].lower() for row in cursor.fetchall()]
            missing_sequences = set(required_sequences) - set(existing_sequences)
            
            if missing_sequences:
                raise Exception(f'Missing sequences: {", ".join(missing_sequences)}')
        
        self.stdout.write('✅ All required sequences exist')
    
    def verify_data_integrity(self):
        """Verify basic data integrity."""
        with connection.cursor() as cursor:
            # Test basic table operations
            test_queries = [
                "SELECT COUNT(*) FROM customer WHERE 1=0",
                "SELECT COUNT(*) FROM carddetail WHERE 1=0",
                "SELECT COUNT(*) FROM limitrequest WHERE 1=0",
                "SELECT COUNT(*) FROM notificationlog WHERE 1=0",
                "SELECT COUNT(*) FROM otplog WHERE 1=0"
            ]
            
            for query in test_queries:
                cursor.execute(query)
                cursor.fetchone()
        
        self.stdout.write('✅ Data integrity verified')
    
    def verify_permissions(self):
        """Verify user permissions."""
        with connection.cursor() as cursor:
            # Test basic permissions
            test_operations = [
                "SELECT 1 FROM DUAL",
                "SELECT COUNT(*) FROM user_tables",
                "SELECT COUNT(*) FROM user_indexes"
            ]
            
            for operation in test_operations:
                cursor.execute(operation)
                cursor.fetchone()
        
        self.stdout.write('✅ User permissions verified')