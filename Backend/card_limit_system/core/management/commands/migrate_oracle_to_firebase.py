"""
Oracle to Firebase Migration Script for HDFC Card Limit System

This script performs a one-time migration of data from Oracle database
to Firebase Firestore collections with data validation and error handling.

Usage:
    python manage.py migrate_oracle_to_firebase [--dry-run] [--batch-size=100]
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback

# Add Django paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'card_limit_system.settings')

import django
django.setup()

from django.core.management.base import BaseCommand
from django.conf import settings
from decouple import config

# Oracle connection (will be removed after migration)
try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    print("⚠️  cx_Oracle not available. Using simulated Oracle data for testing.")

# Firebase imports
from core.firebase_config import FirebaseService, initialize_firebase
from core.firebase_schema import (
    CustomerSchema, CardDetailsSchema, LimitRequestSchema, 
    NotificationSchema, AuditLogSchema, OTPSchema,
    ORACLE_TO_FIREBASE_MAPPING, validate_document
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class OracleToFirebaseMigrator:
    """
    Handles migration from Oracle database to Firebase Firestore.
    """
    
    def __init__(self, dry_run: bool = False, batch_size: int = 100):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.firebase_service = FirebaseService()
        self.oracle_connection = None
        self.migration_stats = {
            'customers': {'migrated': 0, 'errors': 0},
            'card_details': {'migrated': 0, 'errors': 0},
            'limit_requests': {'migrated': 0, 'errors': 0},
            'notifications': {'migrated': 0, 'errors': 0},
            'audit_log': {'migrated': 0, 'errors': 0},
            'otps': {'migrated': 0, 'errors': 0}
        }
        
        # Document references mapping (Oracle ID -> Firebase doc_id)
        self.customer_refs = {}
        self.request_refs = {}
    
    def connect_oracle(self) -> bool:
        """Connect to Oracle database."""
        if not ORACLE_AVAILABLE:
            logger.warning("Oracle not available, using simulated data")
            return True
            
        try:
            dsn = config('ORACLE_DSN', default='localhost:1521/XEPDB1')
            user = config('ORACLE_USER', default='hdfc_user')
            password = config('ORACLE_PASSWORD', default='hdfc123')
            
            self.oracle_connection = cx_Oracle.connect(
                user=user,
                password=password,
                dsn=dsn
            )
            
            logger.info("✅ Connected to Oracle database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Oracle: {str(e)}")
            return False
    
    def get_simulated_oracle_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Get simulated Oracle data for testing when Oracle is not available."""
        simulated_data = {
            'customers': [
                {
                    'id': 'oracle-customer-1',
                    'firebase_uid': 'firebase-uid-1',
                    'name': 'John Doe',
                    'email': 'john.doe@hdfc.com',
                    'phone_number': '+91-9876543210',
                    'customer_id': 'CUST001',
                    'date_of_birth': datetime(1990, 1, 15),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'is_active': 1
                },
                {
                    'id': 'oracle-customer-2',
                    'firebase_uid': 'firebase-uid-2',
                    'name': 'Jane Smith',
                    'email': 'jane.smith@hdfc.com',
                    'phone_number': '+91-9876543211',
                    'customer_id': 'CUST002',
                    'date_of_birth': datetime(1985, 6, 20),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'is_active': 1
                }
            ],
            'limit_requests': [
                {
                    'id': 'oracle-request-1',
                    'customer_id': 'CUST001',
                    'request_type': 'limit_increase',
                    'current_limit': 50000,
                    'requested_limit': 100000,
                    'reason': 'Salary increase and improved credit score',
                    'income_proof': 'salary_slip_2025.pdf',
                    'status': 'pending',
                    'request_date': datetime.now(),
                    'last_updated': datetime.now()
                }
            ],
            'notifications': [
                {
                    'id': 'oracle-notification-1',
                    'customer_id': 'CUST001',
                    'title': 'Limit Request Received',
                    'message': 'Your credit limit increase request has been received',
                    'notification_type': 'limit_request',
                    'status': 'sent',
                    'sent_at': datetime.now(),
                    'created_at': datetime.now()
                }
            ]
        }
        
        return simulated_data.get(table_name, [])
    
    def fetch_oracle_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Fetch data from Oracle table."""
        if not ORACLE_AVAILABLE:
            return self.get_simulated_oracle_data(table_name)
        
        try:
            cursor = self.oracle_connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            
            # Get column names
            columns = [desc[0].lower() for desc in cursor.description]
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                data.append(row_dict)
            
            cursor.close()
            logger.info(f"📊 Fetched {len(data)} rows from {table_name}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error fetching data from {table_name}: {str(e)}")
            return []
    
    def migrate_customers(self) -> bool:
        """Migrate customers table to Firebase."""
        logger.info("🔄 Migrating customers...")
        
        try:
            oracle_data = self.fetch_oracle_data('customers')
            
            for customer_row in oracle_data:
                try:
                    # Convert Oracle row to Firebase schema
                    customer_schema = CustomerSchema.from_oracle_row(customer_row)
                    document_data = customer_schema.to_firestore_document()
                    
                    # Validate document
                    is_valid, errors = validate_document('customers', document_data)
                    if not is_valid:
                        logger.error(f"❌ Customer validation failed: {errors}")
                        self.migration_stats['customers']['errors'] += 1
                        continue
                    
                    if not self.dry_run:
                        # Create Firebase document
                        doc_id = self.firebase_service.create_document(
                            'customers', 
                            document_data
                        )
                        
                        # Store reference mapping
                        self.customer_refs[customer_row['customer_id']] = doc_id
                        
                        logger.info(f"✅ Migrated customer: {customer_row['name']} -> {doc_id}")
                    else:
                        logger.info(f"🔍 [DRY RUN] Would migrate customer: {customer_row['name']}")
                    
                    self.migration_stats['customers']['migrated'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error migrating customer {customer_row.get('name', 'Unknown')}: {str(e)}")
                    self.migration_stats['customers']['errors'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fatal error in customer migration: {str(e)}")
            return False
    
    def migrate_limit_requests(self) -> bool:
        """Migrate limit_requests table to Firebase."""
        logger.info("🔄 Migrating limit requests...")
        
        try:
            oracle_data = self.fetch_oracle_data('limit_requests')
            
            for request_row in oracle_data:
                try:
                    # Get customer reference
                    customer_id = request_row['customer_id']
                    customer_ref = self.customer_refs.get(customer_id)
                    
                    if not customer_ref:
                        logger.warning(f"⚠️  No customer reference found for {customer_id}")
                        customer_ref = f"customers/{customer_id}"  # Fallback
                    
                    # Convert Oracle row to Firebase schema
                    request_schema = LimitRequestSchema.from_oracle_row(
                        request_row, 
                        customer_ref
                    )
                    document_data = request_schema.to_firestore_document()
                    
                    # Validate document
                    is_valid, errors = validate_document('limit_requests', document_data)
                    if not is_valid:
                        logger.error(f"❌ Limit request validation failed: {errors}")
                        self.migration_stats['limit_requests']['errors'] += 1
                        continue
                    
                    if not self.dry_run:
                        # Create Firebase document
                        doc_id = self.firebase_service.create_document(
                            'limit_requests', 
                            document_data
                        )
                        
                        # Store reference mapping
                        self.request_refs[request_row['id']] = doc_id
                        
                        logger.info(f"✅ Migrated limit request: {customer_id} -> {doc_id}")
                    else:
                        logger.info(f"🔍 [DRY RUN] Would migrate limit request for: {customer_id}")
                    
                    self.migration_stats['limit_requests']['migrated'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error migrating limit request {request_row.get('id', 'Unknown')}: {str(e)}")
                    self.migration_stats['limit_requests']['errors'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fatal error in limit request migration: {str(e)}")
            return False
    
    def migrate_notifications(self) -> bool:
        """Migrate notifications table to Firebase."""
        logger.info("🔄 Migrating notifications...")
        
        try:
            oracle_data = self.fetch_oracle_data('notifications')
            
            for notification_row in oracle_data:
                try:
                    # Get customer reference
                    customer_id = notification_row['customer_id']
                    customer_ref = self.customer_refs.get(customer_id)
                    
                    if not customer_ref:
                        logger.warning(f"⚠️  No customer reference found for {customer_id}")
                        customer_ref = f"customers/{customer_id}"  # Fallback
                    
                    # Convert Oracle row to Firebase schema
                    notification_schema = NotificationSchema.from_oracle_row(
                        notification_row, 
                        customer_ref
                    )
                    document_data = notification_schema.to_firestore_document()
                    
                    # Validate document
                    is_valid, errors = validate_document('notifications', document_data)
                    if not is_valid:
                        logger.error(f"❌ Notification validation failed: {errors}")
                        self.migration_stats['notifications']['errors'] += 1
                        continue
                    
                    if not self.dry_run:
                        # Create Firebase document
                        doc_id = self.firebase_service.create_document(
                            'notifications', 
                            document_data
                        )
                        
                        logger.info(f"✅ Migrated notification: {notification_row['title']} -> {doc_id}")
                    else:
                        logger.info(f"🔍 [DRY RUN] Would migrate notification: {notification_row['title']}")
                    
                    self.migration_stats['notifications']['migrated'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error migrating notification {notification_row.get('id', 'Unknown')}: {str(e)}")
                    self.migration_stats['notifications']['errors'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fatal error in notification migration: {str(e)}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration process."""
        logger.info("🚀 Starting Oracle to Firebase migration...")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No data will be actually migrated")
        
        # Initialize Firebase
        try:
            initialize_firebase()
            logger.info("✅ Firebase initialized successfully")
        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {str(e)}")
            return False
        
        # Connect to Oracle
        if not self.connect_oracle():
            return False
        
        # Run migrations in order (dependencies matter)
        migration_steps = [
            ("customers", self.migrate_customers),
            ("limit_requests", self.migrate_limit_requests),
            ("notifications", self.migrate_notifications)
        ]
        
        for step_name, migration_func in migration_steps:
            logger.info(f"📋 Starting {step_name} migration...")
            success = migration_func()
            
            if not success:
                logger.error(f"❌ {step_name} migration failed")
                return False
            
            logger.info(f"✅ {step_name} migration completed")
        
        # Print migration summary
        self.print_migration_summary()
        
        # Close Oracle connection
        if self.oracle_connection:
            self.oracle_connection.close()
            logger.info("🔌 Oracle connection closed")
        
        logger.info("🎉 Migration completed successfully!")
        return True
    
    def print_migration_summary(self):
        """Print migration statistics."""
        logger.info("\n" + "="*60)
        logger.info("📊 MIGRATION SUMMARY")
        logger.info("="*60)
        
        total_migrated = 0
        total_errors = 0
        
        for table_name, stats in self.migration_stats.items():
            migrated = stats['migrated']
            errors = stats['errors']
            total_migrated += migrated
            total_errors += errors
            
            logger.info(f"{table_name.upper():15} | Migrated: {migrated:4} | Errors: {errors:4}")
        
        logger.info("-"*60)
        logger.info(f"{'TOTAL':15} | Migrated: {total_migrated:4} | Errors: {total_errors:4}")
        logger.info("="*60)
        
        if total_errors == 0:
            logger.info("🎉 Migration completed with no errors!")
        else:
            logger.warning(f"⚠️  Migration completed with {total_errors} errors. Check logs for details.")


class Command(BaseCommand):
    """Django management command for Oracle to Firebase migration."""
    
    help = 'Migrate data from Oracle database to Firebase Firestore'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run migration in dry-run mode (no actual data transfer)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for processing records (default: 100)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        migrator = OracleToFirebaseMigrator(dry_run=dry_run, batch_size=batch_size)
        
        try:
            success = migrator.run_migration()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('🎉 Migration completed successfully!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Migration failed! Check logs for details.')
                )
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('⚠️  Migration interrupted by user')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration error: {str(e)}')
            )
            logger.error(f"Migration error: {str(e)}")
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    # Allow running script directly
    migrator = OracleToFirebaseMigrator(dry_run=True)
    migrator.run_migration()