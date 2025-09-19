"""
Django management command to check system health and initialize services.

Performs comprehensive health checks for all external services
and database connections, and provides initialization options.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import time
from datetime import datetime

# Import service classes
from core.firebase_service import FirebaseService
from core.twilio_service import TwilioService
from core.sendgrid_service import SendGridService
from core.onesignal_service import OneSignalService
from core.oracle_service import OracleConnectionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Perform system health checks and service initialization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            choices=['all', 'database', 'firebase', 'twilio', 'sendgrid', 'onesignal'],
            default='all',
            help='Specify which services to check'
        )
        parser.add_argument(
            '--init',
            action='store_true',
            help='Initialize all services'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        self.verbosity = 2 if options['verbose'] else 1
        
        self.stdout.write(
            self.style.SUCCESS('🏥 HDFC Card Limit System - Health Check')
        )
        self.stdout.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if options['init']:
            self.initialize_services()
        
        check_type = options['check']
        
        if check_type == 'all':
            self.check_all_services()
        elif check_type == 'database':
            self.check_database()
        elif check_type == 'firebase':
            self.check_firebase()
        elif check_type == 'twilio':
            self.check_twilio()
        elif check_type == 'sendgrid':
            self.check_sendgrid()
        elif check_type == 'onesignal':
            self.check_onesignal()

    def initialize_services(self):
        """Initialize all external services."""
        self.stdout.write(self.style.WARNING('🔧 Initializing Services...'))
        
        services = [
            ('Firebase', FirebaseService.initialize),
            ('Twilio', TwilioService.initialize),
            ('SendGrid', SendGridService.initialize),
            ('OneSignal', OneSignalService.initialize),
            ('Oracle', OracleConnectionService.initialize),
        ]
        
        for service_name, init_method in services:
            try:
                init_method()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {service_name} initialized successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {service_name} initialization failed: {str(e)}')
                )

    def check_all_services(self):
        """Perform comprehensive health checks for all services."""
        self.stdout.write(self.style.WARNING('🔍 Checking All Services...\n'))
        
        results = {}
        
        # Check each service
        results['database'] = self.check_database()
        results['firebase'] = self.check_firebase()
        results['twilio'] = self.check_twilio()
        results['sendgrid'] = self.check_sendgrid()
        results['onesignal'] = self.check_onesignal()
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('📊 HEALTH CHECK SUMMARY'))
        self.stdout.write('='*50)
        
        healthy_count = sum(1 for status in results.values() if status)
        total_count = len(results)
        
        for service, status in results.items():
            status_icon = '✅' if status else '❌'
            status_text = 'HEALTHY' if status else 'UNHEALTHY'
            self.stdout.write(f'{status_icon} {service.upper()}: {status_text}')
        
        self.stdout.write(f'\nOverall Health: {healthy_count}/{total_count} services healthy')
        
        if healthy_count == total_count:
            self.stdout.write(self.style.SUCCESS('🎉 All services are healthy!'))
        else:
            self.stdout.write(self.style.ERROR('⚠️ Some services need attention'))

    def check_database(self):
        """Check Oracle database connection and health."""
        self.stdout.write(self.style.WARNING('🗄️ Checking Database...'))
        
        try:
            # Test connection
            result = OracleConnectionService.test_connection()
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS('✅ Database connection: OK'))
                
                if self.verbosity >= 2:
                    self.stdout.write(f"   Current Time: {result.get('current_time', 'N/A')}")
                    self.stdout.write(f"   Current User: {result.get('current_user', 'N/A')}")
                    self.stdout.write(f"   Server Host: {result.get('server_host', 'N/A')}")
                    self.stdout.write(f"   Response Time: {result.get('response_time', 0):.3f}s")
                
                # Get connection stats
                stats_result = OracleConnectionService.get_connection_stats()
                if stats_result['success'] and self.verbosity >= 2:
                    stats = stats_result['stats']
                    self.stdout.write(f"   Pool Status: {stats.get('pool_opened', 0)}/{stats.get('pool_max', 0)} connections")
                    self.stdout.write(f"   Total Queries: {stats.get('successful_queries', 0)}")
                    self.stdout.write(f"   Avg Query Time: {stats.get('avg_query_time', 0):.3f}s")
                
                return True
            else:
                self.stdout.write(self.style.ERROR(f'❌ Database connection failed: {result.get("error", "Unknown error")}'))
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Database check failed: {str(e)}'))
            return False

    def check_firebase(self):
        """Check Firebase service health."""
        self.stdout.write(self.style.WARNING('🔥 Checking Firebase...'))
        
        try:
            # Check service health
            result = FirebaseService.health_check()
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS('✅ Firebase service: OK'))
                
                if self.verbosity >= 2:
                    health = result['health']
                    self.stdout.write(f"   Status: {health.get('status', 'unknown')}")
                    self.stdout.write(f"   Project ID: {health.get('project_id', 'N/A')}")
                    self.stdout.write(f"   Response Time: {health.get('response_time', 0):.3f}s")
                
                return True
            else:
                self.stdout.write(self.style.ERROR(f'❌ Firebase service failed: {result.get("error", "Unknown error")}'))
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Firebase check failed: {str(e)}'))
            return False

    def check_twilio(self):
        """Check Twilio service health."""
        self.stdout.write(self.style.WARNING('📞 Checking Twilio...'))
        
        try:
            # Check service health
            result = TwilioService.health_check()
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS('✅ Twilio service: OK'))
                
                if self.verbosity >= 2:
                    health = result['health']
                    self.stdout.write(f"   Status: {health.get('status', 'unknown')}")
                    self.stdout.write(f"   Account SID: {health.get('account_sid', 'N/A')}")
                    self.stdout.write(f"   Response Time: {health.get('response_time', 0):.3f}s")
                
                return True
            else:
                self.stdout.write(self.style.ERROR(f'❌ Twilio service failed: {result.get("error", "Unknown error")}'))
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Twilio check failed: {str(e)}'))
            return False

    def check_sendgrid(self):
        """Check SendGrid service health."""
        self.stdout.write(self.style.WARNING('📧 Checking SendGrid...'))
        
        try:
            # Check service health
            result = SendGridService.health_check()
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS('✅ SendGrid service: OK'))
                
                if self.verbosity >= 2:
                    health = result['health']
                    self.stdout.write(f"   Status: {health.get('status', 'unknown')}")
                    self.stdout.write(f"   API Status: {health.get('api_status', 'N/A')}")
                    self.stdout.write(f"   Response Time: {health.get('response_time', 0):.3f}s")
                
                return True
            else:
                self.stdout.write(self.style.ERROR(f'❌ SendGrid service failed: {result.get("error", "Unknown error")}'))
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ SendGrid check failed: {str(e)}'))
            return False

    def check_onesignal(self):
        """Check OneSignal service health."""
        self.stdout.write(self.style.WARNING('🔔 Checking OneSignal...'))
        
        try:
            # Check service health by getting app stats
            result = OneSignalService.get_app_stats()
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS('✅ OneSignal service: OK'))
                
                if self.verbosity >= 2:
                    self.stdout.write(f"   App ID: {result.get('app_id', 'N/A')}")
                    self.stdout.write(f"   Total Players: {result.get('players', 0)}")
                    self.stdout.write(f"   Messageable Players: {result.get('messageable_players', 0)}")
                
                return True
            else:
                self.stdout.write(self.style.ERROR(f'❌ OneSignal service failed: {result.get("error", "Unknown error")}'))
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ OneSignal check failed: {str(e)}'))
            return False