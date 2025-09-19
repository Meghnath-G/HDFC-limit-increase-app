"""
Application monitoring and health check systems for production.

This module provides comprehensive monitoring, alerting, and health check
capabilities for production deployment.
"""

import time
import json
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests

logger = logging.getLogger('card_limit_system')

class HealthStatus(Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Health check result data structure."""
    name: str
    status: HealthStatus
    response_time: float
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None

class HealthChecker:
    """
    Comprehensive health checking system.
    """
    
    def __init__(self):
        self.checks = {}
        self.results = {}
        self._lock = threading.Lock()
        
    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """Register a health check function."""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check."""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                response_time=0.0,
                message=f"Health check '{name}' not found",
                timestamp=datetime.now()
            )
        
        start_time = time.time()
        try:
            result = self.checks[name]()
            result.response_time = time.time() - start_time
            result.timestamp = datetime.now()
        except Exception as e:
            result = HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now()
            )
        
        with self._lock:
            self.results[name] = result
        
        return result
    
    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in self.results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health check summary."""
        return {
            'overall_status': self.get_overall_status().value,
            'timestamp': datetime.now().isoformat(),
            'checks': {
                name: {
                    'status': result.status.value,
                    'response_time': result.response_time,
                    'message': result.message,
                    'timestamp': result.timestamp.isoformat()
                }
                for name, result in self.results.items()
            }
        }

class DatabaseHealthCheck:
    """Database health check implementation."""
    
    @staticmethod
    def check_database_connection() -> HealthCheckResult:
        """Check database connectivity."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    return HealthCheckResult(
                        name="database_connection",
                        status=HealthStatus.HEALTHY,
                        response_time=0.0,
                        message="Database connection successful"
                    )
                else:
                    return HealthCheckResult(
                        name="database_connection",
                        status=HealthStatus.CRITICAL,
                        response_time=0.0,
                        message="Database query returned unexpected result"
                    )
        except Exception as e:
            return HealthCheckResult(
                name="database_connection",
                status=HealthStatus.CRITICAL,
                response_time=0.0,
                message=f"Database connection failed: {str(e)}"
            )
    
    @staticmethod
    def check_database_performance() -> HealthCheckResult:
        """Check database performance."""
        try:
            from django.db import connection
            
            start_time = time.time()
            with connection.cursor() as cursor:
                # Run a simple performance test query
                cursor.execute("SELECT COUNT(*) FROM customer WHERE ROWNUM <= 1000")
                cursor.fetchone()
            
            response_time = time.time() - start_time
            
            if response_time < 1.0:
                status = HealthStatus.HEALTHY
                message = f"Database performance good ({response_time:.3f}s)"
            elif response_time < 3.0:
                status = HealthStatus.WARNING
                message = f"Database performance slow ({response_time:.3f}s)"
            else:
                status = HealthStatus.CRITICAL
                message = f"Database performance critical ({response_time:.3f}s)"
            
            return HealthCheckResult(
                name="database_performance",
                status=status,
                response_time=response_time,
                message=message
            )
        except Exception as e:
            return HealthCheckResult(
                name="database_performance",
                status=HealthStatus.CRITICAL,
                response_time=0.0,
                message=f"Database performance check failed: {str(e)}"
            )

class CacheHealthCheck:
    """Cache health check implementation."""
    
    @staticmethod
    def check_cache_connection() -> HealthCheckResult:
        """Check cache connectivity."""
        try:
            from django.core.cache import cache
            
            test_key = "health_check_test"
            test_value = "test_value"
            
            # Test cache set and get
            cache.set(test_key, test_value, 30)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value == test_value:
                cache.delete(test_key)
                return HealthCheckResult(
                    name="cache_connection",
                    status=HealthStatus.HEALTHY,
                    response_time=0.0,
                    message="Cache connection successful"
                )
            else:
                return HealthCheckResult(
                    name="cache_connection",
                    status=HealthStatus.CRITICAL,
                    response_time=0.0,
                    message="Cache set/get operation failed"
                )
        except Exception as e:
            return HealthCheckResult(
                name="cache_connection",
                status=HealthStatus.CRITICAL,
                response_time=0.0,
                message=f"Cache connection failed: {str(e)}"
            )

class ExternalServiceHealthCheck:
    """External service health check implementation."""
    
    @staticmethod
    def check_firebase_service() -> HealthCheckResult:
        """Check Firebase service connectivity."""
        try:
            import firebase_admin
            from firebase_admin import auth
            
            # Try to get a user (this validates the connection)
            start_time = time.time()
            try:
                auth.get_user('test_health_check_user')
            except auth.UserNotFoundError:
                # This is expected and means the service is working
                pass
            
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                name="firebase_service",
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message="Firebase service accessible"
            )
        except Exception as e:
            return HealthCheckResult(
                name="firebase_service",
                status=HealthStatus.WARNING,
                response_time=0.0,
                message=f"Firebase service check failed: {str(e)}"
            )
    
    @staticmethod
    def check_twilio_service() -> HealthCheckResult:
        """Check Twilio service connectivity."""
        try:
            from twilio.rest import Client
            import os
            
            account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            
            if not account_sid or not auth_token:
                return HealthCheckResult(
                    name="twilio_service",
                    status=HealthStatus.WARNING,
                    response_time=0.0,
                    message="Twilio credentials not configured"
                )
            
            start_time = time.time()
            client = Client(account_sid, auth_token)
            
            # Test by fetching account info
            account = client.api.account.fetch()
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                name="twilio_service",
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message=f"Twilio service accessible (Account: {account.friendly_name})"
            )
        except Exception as e:
            return HealthCheckResult(
                name="twilio_service",
                status=HealthStatus.WARNING,
                response_time=0.0,
                message=f"Twilio service check failed: {str(e)}"
            )
    
    @staticmethod
    def check_sendgrid_service() -> HealthCheckResult:
        """Check SendGrid service connectivity."""
        try:
            import sendgrid
            import os
            
            api_key = os.environ.get('SENDGRID_API_KEY')
            if not api_key:
                return HealthCheckResult(
                    name="sendgrid_service",
                    status=HealthStatus.WARNING,
                    response_time=0.0,
                    message="SendGrid API key not configured"
                )
            
            start_time = time.time()
            sg = sendgrid.SendGridAPIClient(api_key=api_key)
            
            # Test by getting API key permissions
            response = sg.client.scopes.get()
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return HealthCheckResult(
                    name="sendgrid_service",
                    status=HealthStatus.HEALTHY,
                    response_time=response_time,
                    message="SendGrid service accessible"
                )
            else:
                return HealthCheckResult(
                    name="sendgrid_service",
                    status=HealthStatus.WARNING,
                    response_time=response_time,
                    message=f"SendGrid API returned status {response.status_code}"
                )
        except Exception as e:
            return HealthCheckResult(
                name="sendgrid_service",
                status=HealthStatus.WARNING,
                response_time=0.0,
                message=f"SendGrid service check failed: {str(e)}"
            )

class SystemHealthCheck:
    """System resource health check implementation."""
    
    @staticmethod
    def check_disk_space() -> HealthCheckResult:
        """Check disk space usage."""
        try:
            import psutil
            
            disk_usage = psutil.disk_usage('/')
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            if used_percent < 80:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal ({used_percent:.1f}%)"
            elif used_percent < 90:
                status = HealthStatus.WARNING
                message = f"Disk usage high ({used_percent:.1f}%)"
            else:
                status = HealthStatus.CRITICAL
                message = f"Disk usage critical ({used_percent:.1f}%)"
            
            return HealthCheckResult(
                name="disk_space",
                status=status,
                response_time=0.0,
                message=message,
                details={
                    'used_percent': used_percent,
                    'free_gb': disk_usage.free / (1024**3),
                    'total_gb': disk_usage.total / (1024**3)
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                response_time=0.0,
                message=f"Disk space check failed: {str(e)}"
            )
    
    @staticmethod
    def check_memory_usage() -> HealthCheckResult:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            if used_percent < 80:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal ({used_percent:.1f}%)"
            elif used_percent < 90:
                status = HealthStatus.WARNING
                message = f"Memory usage high ({used_percent:.1f}%)"
            else:
                status = HealthStatus.CRITICAL
                message = f"Memory usage critical ({used_percent:.1f}%)"
            
            return HealthCheckResult(
                name="memory_usage",
                status=status,
                response_time=0.0,
                message=message,
                details={
                    'used_percent': used_percent,
                    'available_gb': memory.available / (1024**3),
                    'total_gb': memory.total / (1024**3)
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="memory_usage",
                status=HealthStatus.UNKNOWN,
                response_time=0.0,
                message=f"Memory usage check failed: {str(e)}"
            )

class AlertManager:
    """
    Alert management system for production monitoring.
    """
    
    def __init__(self):
        self.alert_rules = []
        self.notification_channels = []
        self._lock = threading.Lock()
    
    def add_alert_rule(self, name: str, condition: Callable[[Dict[str, Any]], bool],
                      severity: str = "warning", cooldown: int = 300):
        """Add an alert rule."""
        rule = {
            'name': name,
            'condition': condition,
            'severity': severity,
            'cooldown': cooldown,
            'last_triggered': None
        }
        
        with self._lock:
            self.alert_rules.append(rule)
        
        logger.info(f"Added alert rule: {name}")
    
    def add_notification_channel(self, channel_type: str, config: Dict[str, Any]):
        """Add a notification channel."""
        channel = {
            'type': channel_type,
            'config': config
        }
        
        with self._lock:
            self.notification_channels.append(channel)
        
        logger.info(f"Added notification channel: {channel_type}")
    
    def check_alerts(self, health_data: Dict[str, Any]):
        """Check alert conditions and trigger notifications."""
        current_time = datetime.now()
        
        for rule in self.alert_rules:
            try:
                if rule['condition'](health_data):
                    # Check cooldown period
                    if (rule['last_triggered'] and 
                        (current_time - rule['last_triggered']).total_seconds() < rule['cooldown']):
                        continue
                    
                    # Trigger alert
                    self._trigger_alert(rule, health_data)
                    rule['last_triggered'] = current_time
                    
            except Exception as e:
                logger.error(f"Error checking alert rule {rule['name']}: {e}")
    
    def _trigger_alert(self, rule: Dict[str, Any], health_data: Dict[str, Any]):
        """Trigger an alert notification."""
        alert_data = {
            'rule_name': rule['name'],
            'severity': rule['severity'],
            'timestamp': datetime.now().isoformat(),
            'health_data': health_data
        }
        
        logger.error(f"ALERT TRIGGERED: {rule['name']} - {rule['severity']}")
        
        # Send notifications through all channels
        for channel in self.notification_channels:
            try:
                self._send_notification(channel, alert_data)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel['type']}: {e}")
    
    def _send_notification(self, channel: Dict[str, Any], alert_data: Dict[str, Any]):
        """Send notification through specific channel."""
        if channel['type'] == 'email':
            self._send_email_alert(channel['config'], alert_data)
        elif channel['type'] == 'webhook':
            self._send_webhook_alert(channel['config'], alert_data)
        elif channel['type'] == 'slack':
            self._send_slack_alert(channel['config'], alert_data)
    
    def _send_email_alert(self, config: Dict[str, Any], alert_data: Dict[str, Any]):
        """Send email alert."""
        msg = MimeMultipart()
        msg['From'] = config['from_email']
        msg['To'] = ', '.join(config['to_emails'])
        msg['Subject'] = f"HDFC Card Limit System Alert - {alert_data['severity'].upper()}"
        
        body = f"""
        Alert: {alert_data['rule_name']}
        Severity: {alert_data['severity']}
        Timestamp: {alert_data['timestamp']}
        
        Health Data:
        {json.dumps(alert_data['health_data'], indent=2)}
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        if config.get('use_tls'):
            server.starttls()
        if config.get('username'):
            server.login(config['username'], config['password'])
        
        server.send_message(msg)
        server.quit()
    
    def _send_webhook_alert(self, config: Dict[str, Any], alert_data: Dict[str, Any]):
        """Send webhook alert."""
        response = requests.post(
            config['url'],
            json=alert_data,
            headers=config.get('headers', {}),
            timeout=10
        )
        response.raise_for_status()
    
    def _send_slack_alert(self, config: Dict[str, Any], alert_data: Dict[str, Any]):
        """Send Slack alert."""
        payload = {
            "text": f"🚨 HDFC Card Limit System Alert",
            "attachments": [
                {
                    "color": "danger" if alert_data['severity'] == 'critical' else "warning",
                    "fields": [
                        {
                            "title": "Alert",
                            "value": alert_data['rule_name'],
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": alert_data['severity'].upper(),
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": alert_data['timestamp'],
                            "short": False
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(
            config['webhook_url'],
            json=payload,
            timeout=10
        )
        response.raise_for_status()

# Global health checker and alert manager instances
health_checker = HealthChecker()
alert_manager = AlertManager()

# Register default health checks
health_checker.register_check("database_connection", DatabaseHealthCheck.check_database_connection)
health_checker.register_check("database_performance", DatabaseHealthCheck.check_database_performance)
health_checker.register_check("cache_connection", CacheHealthCheck.check_cache_connection)
health_checker.register_check("firebase_service", ExternalServiceHealthCheck.check_firebase_service)
health_checker.register_check("twilio_service", ExternalServiceHealthCheck.check_twilio_service)
health_checker.register_check("sendgrid_service", ExternalServiceHealthCheck.check_sendgrid_service)
health_checker.register_check("disk_space", SystemHealthCheck.check_disk_space)
health_checker.register_check("memory_usage", SystemHealthCheck.check_memory_usage)

# Default alert rules
def database_critical_alert(health_data: Dict[str, Any]) -> bool:
    """Alert if database is critical."""
    db_checks = ['database_connection', 'database_performance']
    return any(
        health_data.get('checks', {}).get(check, {}).get('status') == 'critical'
        for check in db_checks
    )

def high_resource_usage_alert(health_data: Dict[str, Any]) -> bool:
    """Alert if system resources are critical."""
    resource_checks = ['disk_space', 'memory_usage']
    return any(
        health_data.get('checks', {}).get(check, {}).get('status') == 'critical'
        for check in resource_checks
    )

# Register default alert rules
alert_manager.add_alert_rule(
    "database_critical",
    database_critical_alert,
    severity="critical",
    cooldown=300
)

alert_manager.add_alert_rule(
    "high_resource_usage",
    high_resource_usage_alert,
    severity="warning",
    cooldown=600
)