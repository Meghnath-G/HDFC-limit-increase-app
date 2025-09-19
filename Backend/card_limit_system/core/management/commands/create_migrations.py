"""
Django management command to create comprehensive migrations for Oracle database.

This command generates all necessary migrations for the Card Limit Increase System
with Oracle-specific optimizations, indexes, and constraints.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
import os
import sys


class Command(BaseCommand):
    help = 'Create comprehensive database migrations for Oracle deployment'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what migrations would be created without actually creating them',
        )
        
        parser.add_argument(
            '--with-data',
            action='store_true',
            help='Include data migrations for initial setup',
        )
        
        parser.add_argument(
            '--app',
            type=str,
            help='Create migrations for specific app only',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Creating comprehensive migrations for Oracle database...')
        )
        
        apps_to_migrate = [
            'apps.customers',
            'apps.requests', 
            'notifications',
            'otp',
            'analytics'
        ]
        
        if options['app']:
            apps_to_migrate = [options['app']]
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No migrations will be created')
            )
        
        try:
            for app in apps_to_migrate:
                self.create_app_migrations(app, options)
            
            if options['with_data']:
                self.create_data_migrations(options)
            
            self.create_custom_migrations(options)
            
            self.stdout.write(
                self.style.SUCCESS('✅ All migrations created successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating migrations: {str(e)}')
            )
            sys.exit(1)
    
    def create_app_migrations(self, app_name, options):
        """Create migrations for a specific app."""
        self.stdout.write(f'Creating migrations for {app_name}...')
        
        if not options['dry_run']:
            try:
                call_command('makemigrations', app_name, verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created migrations for {app_name}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create migrations for {app_name}: {str(e)}')
                )
        else:
            self.stdout.write(f'Would create migrations for {app_name}')
    
    def create_data_migrations(self, options):
        """Create data migrations for initial setup."""
        self.stdout.write('Creating data migrations...')
        
        data_migrations = [
            ('apps.customers', 'add_initial_customer_data'),
            ('notifications', 'add_notification_templates'),
            ('analytics', 'add_initial_analytics_config')
        ]
        
        for app, migration_name in data_migrations:
            if not options['dry_run']:
                self.create_data_migration(app, migration_name)
            else:
                self.stdout.write(f'Would create data migration: {app}.{migration_name}')
    
    def create_data_migration(self, app, migration_name):
        """Create a specific data migration."""
        try:
            call_command('makemigrations', app, '--empty', name=migration_name)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created data migration: {app}.{migration_name}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create data migration {migration_name}: {str(e)}')
            )
    
    def create_custom_migrations(self, options):
        """Create custom migrations for Oracle-specific optimizations."""
        self.stdout.write('Creating Oracle optimization migrations...')
        
        if not options['dry_run']:
            self.create_oracle_indexes_migration(options)
            self.create_oracle_constraints_migration(options)
            self.create_oracle_sequences_migration(options)
        else:
            self.stdout.write('Would create Oracle optimization migrations')
    
    def create_oracle_indexes_migration(self, options):
        """Create migration for Oracle-specific indexes."""
        migration_content = '''
from django.db import migrations, models

class Migration(migrations.Migration):
    
    dependencies = [
        ('apps_customers', '0001_initial'),
        ('apps_requests', '0001_initial'),
        ('notifications', '0001_initial'),
        ('otp', '0001_initial'),
    ]
    
    operations = [
        # Customer table indexes
        migrations.RunSQL(
            "CREATE INDEX idx_customer_firebase_uid ON customer(firebase_uid)",
            reverse_sql="DROP INDEX idx_customer_firebase_uid"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_customer_email_active ON customer(email, is_active)",
            reverse_sql="DROP INDEX idx_customer_email_active"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_customer_phone_active ON customer(phone, is_active)",
            reverse_sql="DROP INDEX idx_customer_phone_active"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_customer_created_date ON customer(created_at)",
            reverse_sql="DROP INDEX idx_customer_created_date"
        ),
        
        # CardDetail table indexes
        migrations.RunSQL(
            "CREATE INDEX idx_carddetail_customer_active ON carddetail(customer_id, is_active)",
            reverse_sql="DROP INDEX idx_carddetail_customer_active"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_carddetail_type_active ON carddetail(card_type, is_active)",
            reverse_sql="DROP INDEX idx_carddetail_type_active"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_carddetail_limit ON carddetail(current_limit)",
            reverse_sql="DROP INDEX idx_carddetail_limit"
        ),
        
        # LimitRequest table indexes
        migrations.RunSQL(
            "CREATE INDEX idx_limitrequest_customer_status ON limitrequest(customer_id, status)",
            reverse_sql="DROP INDEX idx_limitrequest_customer_status"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_limitrequest_reference ON limitrequest(reference_number)",
            reverse_sql="DROP INDEX idx_limitrequest_reference"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_limitrequest_created_status ON limitrequest(created_at, status)",
            reverse_sql="DROP INDEX idx_limitrequest_created_status"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_limitrequest_priority ON limitrequest(priority, status)",
            reverse_sql="DROP INDEX idx_limitrequest_priority"
        ),
        
        # NotificationLog table indexes
        migrations.RunSQL(
            "CREATE INDEX idx_notificationlog_customer_type ON notificationlog(customer_id, notification_type)",
            reverse_sql="DROP INDEX idx_notificationlog_customer_type"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_notificationlog_status_created ON notificationlog(status, created_at)",
            reverse_sql="DROP INDEX idx_notificationlog_status_created"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_notificationlog_category ON notificationlog(category, created_at)",
            reverse_sql="DROP INDEX idx_notificationlog_category"
        ),
        
        # OTPLog table indexes
        migrations.RunSQL(
            "CREATE INDEX idx_otplog_phone_status ON otplog(phone_number, status)",
            reverse_sql="DROP INDEX idx_otplog_phone_status"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_otplog_created_type ON otplog(created_at, otp_type)",
            reverse_sql="DROP INDEX idx_otplog_created_type"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_otplog_expires_status ON otplog(expires_at, status)",
            reverse_sql="DROP INDEX idx_otplog_expires_status"
        ),
        
        # Composite indexes for common queries
        migrations.RunSQL(
            "CREATE INDEX idx_customer_search ON customer(firebase_uid, email, is_active)",
            reverse_sql="DROP INDEX idx_customer_search"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_request_processing ON limitrequest(status, priority, created_at)",
            reverse_sql="DROP INDEX idx_request_processing"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_notification_delivery ON notificationlog(customer_id, status, notification_type)",
            reverse_sql="DROP INDEX idx_notification_delivery"
        ),
    ]
'''
        
        # Write migration file
        migration_file = 'D:/IvaR/HDFC/Backend/card_limit_system/core/migrations/0001_oracle_indexes.py'
        os.makedirs(os.path.dirname(migration_file), exist_ok=True)
        
        with open(migration_file, 'w') as f:
            f.write(migration_content)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Created Oracle indexes migration')
        )
    
    def create_oracle_constraints_migration(self, options):
        """Create migration for Oracle-specific constraints."""
        migration_content = '''
from django.db import migrations

class Migration(migrations.Migration):
    
    dependencies = [
        ('core', '0001_oracle_indexes'),
    ]
    
    operations = [
        # Add check constraints for data validation
        migrations.RunSQL(
            "ALTER TABLE customer ADD CONSTRAINT chk_customer_email_format CHECK (email LIKE '%@%')",
            reverse_sql="ALTER TABLE customer DROP CONSTRAINT chk_customer_email_format"
        ),
        migrations.RunSQL(
            "ALTER TABLE customer ADD CONSTRAINT chk_customer_phone_format CHECK (LENGTH(phone) >= 10)",
            reverse_sql="ALTER TABLE customer DROP CONSTRAINT chk_customer_phone_format"
        ),
        migrations.RunSQL(
            "ALTER TABLE customer ADD CONSTRAINT chk_customer_age CHECK (date_of_birth < SYSDATE - INTERVAL '18' YEAR)",
            reverse_sql="ALTER TABLE customer DROP CONSTRAINT chk_customer_age"
        ),
        
        # CardDetail constraints
        migrations.RunSQL(
            "ALTER TABLE carddetail ADD CONSTRAINT chk_card_limit_positive CHECK (current_limit >= 0)",
            reverse_sql="ALTER TABLE carddetail DROP CONSTRAINT chk_card_limit_positive"
        ),
        migrations.RunSQL(
            "ALTER TABLE carddetail ADD CONSTRAINT chk_card_expiry_month CHECK (expiry_month BETWEEN 1 AND 12)",
            reverse_sql="ALTER TABLE carddetail DROP CONSTRAINT chk_card_expiry_month"
        ),
        migrations.RunSQL(
            "ALTER TABLE carddetail ADD CONSTRAINT chk_card_expiry_year CHECK (expiry_year >= EXTRACT(YEAR FROM SYSDATE))",
            reverse_sql="ALTER TABLE carddetail DROP CONSTRAINT chk_card_expiry_year"
        ),
        
        # LimitRequest constraints
        migrations.RunSQL(
            "ALTER TABLE limitrequest ADD CONSTRAINT chk_request_limits CHECK (requested_limit > current_limit)",
            reverse_sql="ALTER TABLE limitrequest DROP CONSTRAINT chk_request_limits"
        ),
        migrations.RunSQL(
            "ALTER TABLE limitrequest ADD CONSTRAINT chk_request_positive_limits CHECK (current_limit >= 0 AND requested_limit > 0)",
            reverse_sql="ALTER TABLE limitrequest DROP CONSTRAINT chk_request_positive_limits"
        ),
        
        # OTPLog constraints
        migrations.RunSQL(
            "ALTER TABLE otplog ADD CONSTRAINT chk_otp_expiry CHECK (expires_at > created_at)",
            reverse_sql="ALTER TABLE otplog DROP CONSTRAINT chk_otp_expiry"
        ),
        migrations.RunSQL(
            "ALTER TABLE otplog ADD CONSTRAINT chk_otp_attempts CHECK (attempt_count >= 0 AND attempt_count <= 10)",
            reverse_sql="ALTER TABLE otplog DROP CONSTRAINT chk_otp_attempts"
        ),
        
        # Add foreign key constraints with proper naming
        migrations.RunSQL(
            "ALTER TABLE carddetail ADD CONSTRAINT fk_carddetail_customer FOREIGN KEY (customer_id) REFERENCES customer(id)",
            reverse_sql="ALTER TABLE carddetail DROP CONSTRAINT fk_carddetail_customer"
        ),
        migrations.RunSQL(
            "ALTER TABLE limitrequest ADD CONSTRAINT fk_limitrequest_customer FOREIGN KEY (customer_id) REFERENCES customer(id)",
            reverse_sql="ALTER TABLE limitrequest DROP CONSTRAINT fk_limitrequest_customer"
        ),
        migrations.RunSQL(
            "ALTER TABLE limitrequest ADD CONSTRAINT fk_limitrequest_carddetail FOREIGN KEY (card_detail_id) REFERENCES carddetail(id)",
            reverse_sql="ALTER TABLE limitrequest DROP CONSTRAINT fk_limitrequest_carddetail"
        ),
    ]
'''
        
        # Write migration file
        migration_file = 'D:/IvaR/HDFC/Backend/card_limit_system/core/migrations/0002_oracle_constraints.py'
        
        with open(migration_file, 'w') as f:
            f.write(migration_content)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Created Oracle constraints migration')
        )
    
    def create_oracle_sequences_migration(self, options):
        """Create migration for Oracle sequences and triggers."""
        migration_content = '''
from django.db import migrations

class Migration(migrations.Migration):
    
    dependencies = [
        ('core', '0002_oracle_constraints'),
    ]
    
    operations = [
        # Create sequences for reference number generation
        migrations.RunSQL(
            """
            CREATE SEQUENCE customer_ref_seq
            START WITH 100000
            INCREMENT BY 1
            NOCACHE
            NOCYCLE
            """,
            reverse_sql="DROP SEQUENCE customer_ref_seq"
        ),
        
        migrations.RunSQL(
            """
            CREATE SEQUENCE limit_request_ref_seq
            START WITH 1000000
            INCREMENT BY 1
            NOCACHE
            NOCYCLE
            """,
            reverse_sql="DROP SEQUENCE limit_request_ref_seq"
        ),
        
        migrations.RunSQL(
            """
            CREATE SEQUENCE notification_ref_seq
            START WITH 10000000
            INCREMENT BY 1
            NOCACHE
            NOCYCLE
            """,
            reverse_sql="DROP SEQUENCE notification_ref_seq"
        ),
        
        # Create triggers for automatic reference number generation
        migrations.RunSQL(
            """
            CREATE OR REPLACE TRIGGER trg_customer_ref_num
            BEFORE INSERT ON customer
            FOR EACH ROW
            WHEN (NEW.customer_reference IS NULL)
            BEGIN
                SELECT 'CUST' || LPAD(customer_ref_seq.NEXTVAL, 6, '0') INTO :NEW.customer_reference FROM DUAL;
            END;
            """,
            reverse_sql="DROP TRIGGER trg_customer_ref_num"
        ),
        
        migrations.RunSQL(
            """
            CREATE OR REPLACE TRIGGER trg_limit_request_ref_num
            BEFORE INSERT ON limitrequest
            FOR EACH ROW
            WHEN (NEW.reference_number IS NULL)
            BEGIN
                SELECT 'LR' || LPAD(limit_request_ref_seq.NEXTVAL, 8, '0') INTO :NEW.reference_number FROM DUAL;
            END;
            """,
            reverse_sql="DROP TRIGGER trg_limit_request_ref_num"
        ),
        
        # Create audit triggers for tracking changes
        migrations.RunSQL(
            """
            CREATE OR REPLACE TRIGGER trg_customer_audit
            BEFORE UPDATE ON customer
            FOR EACH ROW
            BEGIN
                :NEW.updated_at := SYSTIMESTAMP;
            END;
            """,
            reverse_sql="DROP TRIGGER trg_customer_audit"
        ),
        
        migrations.RunSQL(
            """
            CREATE OR REPLACE TRIGGER trg_limitrequest_audit
            BEFORE UPDATE ON limitrequest
            FOR EACH ROW
            BEGIN
                :NEW.updated_at := SYSTIMESTAMP;
            END;
            """,
            reverse_sql="DROP TRIGGER trg_limitrequest_audit"
        ),
        
        # Create partitioning for large tables
        migrations.RunSQL(
            """
            ALTER TABLE notificationlog MODIFY
            PARTITION BY RANGE (created_at)
            (
                PARTITION p_current VALUES LESS THAN (SYSDATE + 1),
                PARTITION p_older VALUES LESS THAN (MAXVALUE)
            )
            """,
            reverse_sql="-- Partitioning cannot be easily reversed"
        ),
    ]
'''
        
        # Write migration file
        migration_file = 'D:/IvaR/HDFC/Backend/card_limit_system/core/migrations/0003_oracle_sequences.py'
        
        with open(migration_file, 'w') as f:
            f.write(migration_content)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Created Oracle sequences and triggers migration')
        )