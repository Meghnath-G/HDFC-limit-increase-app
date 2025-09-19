# Troubleshooting Guide

## Table of Contents
1. [Troubleshooting Overview](#troubleshooting-overview)
2. [Common Issues and Solutions](#common-issues-and-solutions)
3. [Database-Related Issues](#database-related-issues)
4. [Application Performance Issues](#application-performance-issues)
5. [External Service Integration Issues](#external-service-integration-issues)
6. [Authentication and Authorization Issues](#authentication-and-authorization-issues)
7. [Deployment and Infrastructure Issues](#deployment-and-infrastructure-issues)
8. [Monitoring and Alerting](#monitoring-and-alerting)
9. [Log Analysis and Debugging](#log-analysis-and-debugging)
10. [Performance Tuning Guidelines](#performance-tuning-guidelines)
11. [Emergency Response Procedures](#emergency-response-procedures)
12. [Support Escalation Procedures](#support-escalation-procedures)

---

## Troubleshooting Overview

### 1. Troubleshooting Methodology

```python
# troubleshooting/methodology.py
class TroubleshootingMethodology:
    """
    Systematic approach to troubleshooting HDFC Card Limit System issues
    """
    
    def __init__(self):
        self.troubleshooting_steps = [
            "Identify the problem",
            "Gather information",
            "Analyze symptoms",
            "Isolate the issue",
            "Implement solution",
            "Test the fix",
            "Document the resolution"
        ]
    
    def identify_problem(self, issue_description: str) -> dict:
        """
        Step 1: Identify and categorize the problem
        """
        categories = {
            'performance': ['slow', 'timeout', 'lag', 'delay', 'response time'],
            'error': ['error', 'exception', 'failure', 'crash', 'bug'],
            'connectivity': ['connection', 'network', 'unreachable', 'offline'],
            'authentication': ['login', 'auth', 'permission', 'access', 'unauthorized'],
            'data': ['database', 'data', 'record', 'query', 'migration'],
            'integration': ['external', 'service', 'api', 'third-party']
        }
        
        issue_lower = issue_description.lower()
        identified_categories = []
        
        for category, keywords in categories.items():
            if any(keyword in issue_lower for keyword in keywords):
                identified_categories.append(category)
        
        return {
            'categories': identified_categories,
            'priority': self.assess_priority(issue_description),
            'urgency': self.assess_urgency(issue_description)
        }
    
    def gather_information(self, issue_type: str) -> dict:
        """
        Step 2: Gather relevant information based on issue type
        """
        information_checklist = {
            'general': [
                'Timestamp of the issue',
                'Affected users/systems',
                'Error messages',
                'Recent changes',
                'Environment details'
            ],
            'performance': [
                'Response times',
                'System resource usage',
                'Database performance metrics',
                'External service response times',
                'Network latency'
            ],
            'error': [
                'Complete error stack trace',
                'Log entries around the time of error',
                'User actions leading to error',
                'Frequency of occurrence',
                'Affected functionality'
            ],
            'connectivity': [
                'Network configuration',
                'Firewall settings',
                'DNS resolution',
                'Port accessibility',
                'Certificate validity'
            ]
        }
        
        return information_checklist.get(issue_type, information_checklist['general'])
    
    def assess_priority(self, issue_description: str) -> str:
        """
        Assess issue priority based on impact and urgency
        """
        critical_keywords = ['down', 'offline', 'crash', 'security', 'data loss']
        high_keywords = ['slow', 'error', 'failure', 'timeout']
        
        issue_lower = issue_description.lower()
        
        if any(keyword in issue_lower for keyword in critical_keywords):
            return 'Critical'
        elif any(keyword in issue_lower for keyword in high_keywords):
            return 'High'
        else:
            return 'Medium'
    
    def assess_urgency(self, issue_description: str) -> str:
        """
        Assess issue urgency
        """
        urgent_keywords = ['production', 'customer', 'payment', 'security']
        issue_lower = issue_description.lower()
        
        if any(keyword in issue_lower for keyword in urgent_keywords):
            return 'Urgent'
        else:
            return 'Normal'
```

### 2. Issue Classification System

```python
# troubleshooting/classification.py
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict

class IssueSeverity(Enum):
    CRITICAL = "critical"      # System down, data loss, security breach
    HIGH = "high"             # Major functionality impacted
    MEDIUM = "medium"         # Minor functionality impacted
    LOW = "low"               # Cosmetic or enhancement

class IssueCategory(Enum):
    APPLICATION = "application"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    INTEGRATION = "integration"
    SECURITY = "security"
    PERFORMANCE = "performance"

@dataclass
class TroubleshootingTicket:
    ticket_id: str
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    reporter: str
    assignee: str = None
    status: str = "Open"
    created_at: str = None
    updated_at: str = None
    resolution: str = None
    tags: List[str] = None
    
    def escalate(self):
        """Escalate issue to higher severity"""
        escalation_map = {
            IssueSeverity.LOW: IssueSeverity.MEDIUM,
            IssueSeverity.MEDIUM: IssueSeverity.HIGH,
            IssueSeverity.HIGH: IssueSeverity.CRITICAL
        }
        
        if self.severity in escalation_map:
            self.severity = escalation_map[self.severity]
            self.status = "Escalated"

class TroubleshootingKnowledgeBase:
    """
    Knowledge base for common issues and solutions
    """
    
    def __init__(self):
        self.known_issues = self.load_known_issues()
    
    def load_known_issues(self) -> Dict:
        """Load known issues and their solutions"""
        return {
            "database_connection_timeout": {
                "description": "Database connection times out",
                "symptoms": ["Connection timeout", "cx_Oracle.DatabaseError", "TNS timeout"],
                "category": IssueCategory.DATABASE,
                "severity": IssueSeverity.HIGH,
                "solutions": [
                    "Check database server status",
                    "Verify network connectivity",
                    "Review connection pool settings",
                    "Check firewall rules",
                    "Validate TNS configuration"
                ],
                "related_logs": ["/var/log/hdfc-card-system/django.log", "/opt/oracle/diag/"]
            },
            "firebase_auth_token_expired": {
                "description": "Firebase authentication token expired",
                "symptoms": ["InvalidIdTokenError", "ExpiredIdTokenError", "401 Unauthorized"],
                "category": IssueCategory.INTEGRATION,
                "severity": IssueSeverity.MEDIUM,
                "solutions": [
                    "Refresh ID token on client side",
                    "Check token expiration handling",
                    "Verify Firebase configuration",
                    "Review token refresh logic"
                ],
                "related_logs": ["/var/log/hdfc-card-system/django.log"]
            },
            "high_memory_usage": {
                "description": "Application consuming excessive memory",
                "symptoms": ["Out of memory", "Memory usage > 80%", "Slow response"],
                "category": IssueCategory.PERFORMANCE,
                "severity": IssueSeverity.HIGH,
                "solutions": [
                    "Analyze memory usage patterns",
                    "Check for memory leaks",
                    "Review database query efficiency",
                    "Optimize caching strategy",
                    "Scale application instances"
                ],
                "related_logs": ["/var/log/hdfc-card-system/django.log", "system logs"]
            }
        }
    
    def search_solutions(self, symptoms: List[str]) -> List[Dict]:
        """Search for solutions based on symptoms"""
        matches = []
        
        for issue_id, issue_data in self.known_issues.items():
            issue_symptoms = [s.lower() for s in issue_data['symptoms']]
            user_symptoms = [s.lower() for s in symptoms]
            
            # Calculate match score
            matching_symptoms = sum(1 for symptom in user_symptoms 
                                  if any(symptom in issue_symptom for issue_symptom in issue_symptoms))
            
            if matching_symptoms > 0:
                match_score = matching_symptoms / len(issue_symptoms)
                matches.append({
                    'issue_id': issue_id,
                    'issue_data': issue_data,
                    'match_score': match_score
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches
```

---

## Common Issues and Solutions

### 1. Application Startup Issues

```python
# troubleshooting/startup_issues.py
class StartupTroubleshooting:
    """
    Troubleshoot common application startup issues
    """
    
    def diagnose_startup_failure(self, error_log: str) -> Dict:
        """
        Diagnose application startup failures
        """
        common_startup_issues = {
            'import_error': {
                'patterns': ['ImportError', 'ModuleNotFoundError', 'No module named'],
                'solutions': [
                    'Check Python virtual environment activation',
                    'Verify all dependencies are installed',
                    'Check PYTHONPATH configuration',
                    'Reinstall missing packages'
                ],
                'commands': [
                    'pip list',
                    'pip install -r requirements.txt',
                    'python -c "import django; print(django.VERSION)"'
                ]
            },
            'database_connection': {
                'patterns': ['cx_Oracle.DatabaseError', 'ORACLE not available', 'TNS'],
                'solutions': [
                    'Verify Oracle database is running',
                    'Check database connection parameters',
                    'Validate Oracle client installation',
                    'Test database connectivity'
                ],
                'commands': [
                    'sqlplus hdfc_card_system/password@localhost:1521/XE',
                    'tnsping XE',
                    'ldd $ORACLE_HOME/lib/libclntsh.so'
                ]
            },
            'settings_error': {
                'patterns': ['ImproperlyConfigured', 'DJANGO_SETTINGS_MODULE'],
                'solutions': [
                    'Set DJANGO_SETTINGS_MODULE environment variable',
                    'Check settings file exists and is valid',
                    'Verify environment-specific settings',
                    'Check for syntax errors in settings'
                ],
                'commands': [
                    'export DJANGO_SETTINGS_MODULE=card_limit_system.settings.production',
                    'python manage.py check',
                    'python -c "import django; django.setup()"'
                ]
            },
            'port_binding': {
                'patterns': ['Address already in use', 'Port 8000', 'bind()'],
                'solutions': [
                    'Check if port is already in use',
                    'Kill process using the port',
                    'Use different port number',
                    'Check firewall settings'
                ],
                'commands': [
                    'netstat -tlnp | grep :8000',
                    'lsof -ti:8000',
                    'kill -9 $(lsof -ti:8000)'
                ]
            }
        }
        
        diagnosis = {
            'identified_issues': [],
            'recommended_solutions': [],
            'diagnostic_commands': []
        }
        
        for issue_type, issue_data in common_startup_issues.items():
            for pattern in issue_data['patterns']:
                if pattern.lower() in error_log.lower():
                    diagnosis['identified_issues'].append(issue_type)
                    diagnosis['recommended_solutions'].extend(issue_data['solutions'])
                    diagnosis['diagnostic_commands'].extend(issue_data['commands'])
                    break
        
        return diagnosis
    
    def validate_environment(self) -> Dict:
        """
        Validate environment configuration
        """
        checks = {
            'python_version': self.check_python_version(),
            'django_installation': self.check_django_installation(),
            'oracle_client': self.check_oracle_client(),
            'environment_variables': self.check_environment_variables(),
            'database_connectivity': self.check_database_connectivity(),
            'redis_connectivity': self.check_redis_connectivity()
        }
        
        return checks
    
    def check_python_version(self) -> Dict:
        """Check Python version compatibility"""
        import sys
        
        required_version = (3, 9)
        current_version = sys.version_info[:2]
        
        return {
            'status': 'pass' if current_version >= required_version else 'fail',
            'current_version': f"{current_version[0]}.{current_version[1]}",
            'required_version': f"{required_version[0]}.{required_version[1]}",
            'message': f"Python {current_version[0]}.{current_version[1]} {'meets' if current_version >= required_version else 'does not meet'} requirement"
        }
    
    def check_django_installation(self) -> Dict:
        """Check Django installation and version"""
        try:
            import django
            return {
                'status': 'pass',
                'version': django.VERSION,
                'message': f"Django {django.get_version()} is installed"
            }
        except ImportError:
            return {
                'status': 'fail',
                'version': None,
                'message': "Django is not installed"
            }
    
    def check_oracle_client(self) -> Dict:
        """Check Oracle client installation"""
        try:
            import cx_Oracle
            return {
                'status': 'pass',
                'version': cx_Oracle.version,
                'client_version': cx_Oracle.clientversion(),
                'message': "Oracle client is properly installed"
            }
        except ImportError:
            return {
                'status': 'fail',
                'message': "cx_Oracle module not found"
            }
        except Exception as e:
            return {
                'status': 'fail',
                'message': f"Oracle client error: {str(e)}"
            }
```

### 2. Runtime Error Handling

```python
# troubleshooting/runtime_errors.py
import traceback
import logging
from typing import Dict, List

class RuntimeErrorAnalyzer:
    """
    Analyze and provide solutions for runtime errors
    """
    
    def __init__(self):
        self.error_patterns = self.load_error_patterns()
    
    def analyze_exception(self, exception: Exception, context: Dict = None) -> Dict:
        """
        Analyze exception and provide troubleshooting information
        """
        error_info = {
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'stack_trace': traceback.format_exc(),
            'context': context or {},
            'solutions': [],
            'related_issues': []
        }
        
        # Find matching error patterns
        for pattern_name, pattern_data in self.error_patterns.items():
            if self.matches_pattern(exception, pattern_data):
                error_info['solutions'].extend(pattern_data['solutions'])
                error_info['related_issues'].append(pattern_name)
        
        # Add specific analysis based on error type
        if isinstance(exception, DatabaseError):
            error_info.update(self.analyze_database_error(exception))
        elif isinstance(exception, ConnectionError):
            error_info.update(self.analyze_connection_error(exception))
        elif isinstance(exception, TimeoutError):
            error_info.update(self.analyze_timeout_error(exception))
        
        return error_info
    
    def load_error_patterns(self) -> Dict:
        """Load common error patterns and solutions"""
        return {
            'database_lock': {
                'patterns': ['ORA-00054', 'resource busy', 'lock'],
                'solutions': [
                    'Check for long-running transactions',
                    'Identify blocking sessions',
                    'Review transaction isolation levels',
                    'Optimize query performance',
                    'Consider query timeout settings'
                ],
                'queries': [
                    "SELECT * FROM v$lock WHERE block > 0",
                    "SELECT * FROM v$session WHERE blocking_session IS NOT NULL"
                ]
            },
            'memory_error': {
                'patterns': ['MemoryError', 'OutOfMemoryError', 'Cannot allocate memory'],
                'solutions': [
                    'Increase available memory',
                    'Optimize query result processing',
                    'Implement pagination for large datasets',
                    'Review memory usage patterns',
                    'Add memory monitoring'
                ],
                'monitoring': [
                    'Check application memory usage',
                    'Monitor garbage collection',
                    'Review database connection pool size'
                ]
            },
            'validation_error': {
                'patterns': ['ValidationError', 'Invalid input', 'does not exist'],
                'solutions': [
                    'Validate input data format',
                    'Check field constraints',
                    'Review model validation rules',
                    'Verify foreign key relationships',
                    'Check data migration status'
                ],
                'checks': [
                    'Review model field definitions',
                    'Check database constraints',
                    'Validate input serialization'
                ]
            }
        }
    
    def matches_pattern(self, exception: Exception, pattern_data: Dict) -> bool:
        """Check if exception matches error pattern"""
        exception_str = str(exception).lower()
        
        for pattern in pattern_data['patterns']:
            if pattern.lower() in exception_str:
                return True
        
        return False
    
    def analyze_database_error(self, exception: Exception) -> Dict:
        """Specific analysis for database errors"""
        error_code = getattr(exception, 'code', None)
        
        oracle_errors = {
            'ORA-00001': {
                'description': 'Unique constraint violated',
                'solutions': [
                    'Check for duplicate values',
                    'Review unique constraints',
                    'Implement proper validation',
                    'Handle duplicate key errors gracefully'
                ]
            },
            'ORA-00054': {
                'description': 'Resource busy and acquire with NOWAIT specified',
                'solutions': [
                    'Retry operation after delay',
                    'Check for blocking transactions',
                    'Optimize transaction timing',
                    'Consider using SELECT FOR UPDATE SKIP LOCKED'
                ]
            },
            'ORA-01017': {
                'description': 'Invalid username/password',
                'solutions': [
                    'Verify database credentials',
                    'Check account status',
                    'Reset password if needed',
                    'Review connection string'
                ]
            }
        }
        
        if error_code and error_code in oracle_errors:
            return {
                'database_error_code': error_code,
                'database_error_info': oracle_errors[error_code]
            }
        
        return {}
    
    def analyze_connection_error(self, exception: Exception) -> Dict:
        """Specific analysis for connection errors"""
        return {
            'connection_checks': [
                'Verify network connectivity',
                'Check firewall settings',
                'Validate DNS resolution',
                'Test port accessibility',
                'Review proxy settings'
            ],
            'diagnostic_commands': [
                'ping hostname',
                'telnet hostname port',
                'nslookup hostname',
                'netstat -an | grep port'
            ]
        }
    
    def analyze_timeout_error(self, exception: Exception) -> Dict:
        """Specific analysis for timeout errors"""
        return {
            'timeout_checks': [
                'Review timeout configuration',
                'Check network latency',
                'Analyze operation complexity',
                'Monitor resource usage',
                'Consider async processing'
            ],
            'optimizations': [
                'Increase timeout values',
                'Optimize query performance',
                'Implement caching',
                'Use connection pooling',
                'Add retry mechanisms'
            ]
        }
```

---

## Database-Related Issues

### 1. Oracle Database Troubleshooting

```python
# troubleshooting/oracle_troubleshooting.py
import cx_Oracle
from typing import Dict, List

class OracleTroubleshooting:
    """
    Comprehensive Oracle database troubleshooting utilities
    """
    
    def __init__(self):
        self.connection = None
        self.diagnostic_queries = self.load_diagnostic_queries()
    
    def connect_to_database(self, connection_string: str) -> bool:
        """Establish database connection for diagnostics"""
        try:
            self.connection = cx_Oracle.connect(connection_string)
            return True
        except Exception as e:
            print(f"Database connection failed: {str(e)}")
            return False
    
    def diagnose_connection_issues(self, connection_params: Dict) -> Dict:
        """Diagnose database connection issues"""
        diagnosis = {
            'connection_test': False,
            'tns_resolution': False,
            'credential_validation': False,
            'network_connectivity': False,
            'recommendations': []
        }
        
        # Test basic connectivity
        try:
            test_connection = cx_Oracle.connect(
                user=connection_params['user'],
                password=connection_params['password'],
                dsn=connection_params['dsn']
            )
            test_connection.close()
            diagnosis['connection_test'] = True
        except cx_Oracle.DatabaseError as e:
            error_obj, = e.args
            diagnosis['connection_error'] = {
                'code': error_obj.code,
                'message': error_obj.message,
                'context': error_obj.context
            }
            
            # Specific error code analysis
            if error_obj.code == 1017:  # Invalid username/password
                diagnosis['recommendations'].append('Verify database credentials')
            elif error_obj.code == 12154:  # TNS could not resolve service name
                diagnosis['recommendations'].append('Check TNS configuration')
            elif error_obj.code == 12541:  # TNS no listener
                diagnosis['recommendations'].append('Verify Oracle listener is running')
        
        return diagnosis
    
    def check_database_performance(self) -> Dict:
        """Check database performance metrics"""
        if not self.connection:
            return {'error': 'No database connection available'}
        
        performance_checks = {}
        
        try:
            cursor = self.connection.cursor()
            
            # Check session count
            cursor.execute("SELECT COUNT(*) FROM v$session")
            performance_checks['active_sessions'] = cursor.fetchone()[0]
            
            # Check tablespace usage
            cursor.execute("""
                SELECT tablespace_name, 
                       ROUND((used_space/total_space)*100, 2) as usage_percent
                FROM (
                    SELECT tablespace_name,
                           SUM(bytes)/1024/1024 as total_space
                    FROM dba_data_files
                    GROUP BY tablespace_name
                ) total,
                (
                    SELECT tablespace_name,
                           SUM(bytes)/1024/1024 as used_space
                    FROM dba_segments
                    GROUP BY tablespace_name
                ) used
                WHERE total.tablespace_name = used.tablespace_name
            """)
            
            tablespace_usage = cursor.fetchall()
            performance_checks['tablespace_usage'] = [
                {'name': row[0], 'usage_percent': row[1]} 
                for row in tablespace_usage
            ]
            
            # Check for blocking sessions
            cursor.execute("""
                SELECT blocking_session, sid, serial#, username, program
                FROM v$session 
                WHERE blocking_session IS NOT NULL
            """)
            
            blocking_sessions = cursor.fetchall()
            performance_checks['blocking_sessions'] = [
                {
                    'blocking_session': row[0],
                    'blocked_session': row[1],
                    'serial': row[2],
                    'username': row[3],
                    'program': row[4]
                }
                for row in blocking_sessions
            ]
            
            # Check for long-running transactions
            cursor.execute("""
                SELECT s.sid, s.serial#, s.username, s.program,
                       ROUND((SYSDATE - s.logon_time) * 24 * 60, 2) as minutes_connected
                FROM v$session s, v$transaction t
                WHERE s.saddr = t.ses_addr
                AND (SYSDATE - s.logon_time) * 24 * 60 > 30
            """)
            
            long_transactions = cursor.fetchall()
            performance_checks['long_transactions'] = [
                {
                    'sid': row[0],
                    'serial': row[1],
                    'username': row[2],
                    'program': row[3],
                    'minutes_connected': row[4]
                }
                for row in long_transactions
            ]
            
            cursor.close()
            
        except Exception as e:
            performance_checks['error'] = str(e)
        
        return performance_checks
    
    def analyze_slow_queries(self) -> Dict:
        """Analyze slow-running queries"""
        if not self.connection:
            return {'error': 'No database connection available'}
        
        try:
            cursor = self.connection.cursor()
            
            # Get top slow queries
            cursor.execute("""
                SELECT sql_id, sql_text, executions, 
                       ROUND(elapsed_time/1000000, 2) as elapsed_seconds,
                       ROUND(cpu_time/1000000, 2) as cpu_seconds,
                       disk_reads, buffer_gets
                FROM v$sql
                WHERE executions > 0
                AND elapsed_time/executions > 1000000  -- More than 1 second average
                ORDER BY elapsed_time/executions DESC
                FETCH FIRST 10 ROWS ONLY
            """)
            
            slow_queries = cursor.fetchall()
            
            query_analysis = []
            for query in slow_queries:
                analysis = {
                    'sql_id': query[0],
                    'sql_text': query[1][:100] + '...' if len(query[1]) > 100 else query[1],
                    'executions': query[2],
                    'elapsed_seconds': query[3],
                    'cpu_seconds': query[4],
                    'disk_reads': query[5],
                    'buffer_gets': query[6],
                    'avg_elapsed': round(query[3] / query[2], 2) if query[2] > 0 else 0
                }
                query_analysis.append(analysis)
            
            cursor.close()
            
            return {
                'slow_queries': query_analysis,
                'recommendations': self.generate_query_recommendations(query_analysis)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def generate_query_recommendations(self, query_analysis: List[Dict]) -> List[str]:
        """Generate recommendations based on query analysis"""
        recommendations = []
        
        for query in query_analysis:
            if query['disk_reads'] > 10000:
                recommendations.append(f"SQL_ID {query['sql_id']}: High disk reads - consider adding indexes")
            
            if query['avg_elapsed'] > 5:
                recommendations.append(f"SQL_ID {query['sql_id']}: Long execution time - review query logic")
            
            if query['buffer_gets'] / query['executions'] > 100000:
                recommendations.append(f"SQL_ID {query['sql_id']}: High buffer gets - optimize query efficiency")
        
        if not recommendations:
            recommendations.append("No specific query optimization recommendations at this time")
        
        return recommendations
    
    def check_database_health(self) -> Dict:
        """Comprehensive database health check"""
        health_status = {
            'overall_status': 'healthy',
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        # Connection check
        if self.connection:
            health_status['checks']['connection'] = 'pass'
        else:
            health_status['checks']['connection'] = 'fail'
            health_status['errors'].append('Database connection not available')
            health_status['overall_status'] = 'unhealthy'
            return health_status
        
        try:
            cursor = self.connection.cursor()
            
            # Check database status
            cursor.execute("SELECT status FROM v$instance")
            db_status = cursor.fetchone()[0]
            health_status['checks']['database_status'] = db_status
            
            if db_status != 'OPEN':
                health_status['errors'].append(f'Database status is {db_status}, expected OPEN')
                health_status['overall_status'] = 'unhealthy'
            
            # Check tablespace usage
            cursor.execute("""
                SELECT tablespace_name, 
                       ROUND((used_space/total_space)*100, 2) as usage_percent
                FROM (
                    SELECT tablespace_name,
                           SUM(bytes)/1024/1024 as total_space
                    FROM dba_data_files
                    GROUP BY tablespace_name
                ) total,
                (
                    SELECT tablespace_name,
                           SUM(bytes)/1024/1024 as used_space
                    FROM dba_segments
                    GROUP BY tablespace_name
                ) used
                WHERE total.tablespace_name = used.tablespace_name
            """)
            
            for tablespace, usage in cursor.fetchall():
                if usage > 90:
                    health_status['errors'].append(f'Tablespace {tablespace} is {usage}% full')
                    health_status['overall_status'] = 'unhealthy'
                elif usage > 80:
                    health_status['warnings'].append(f'Tablespace {tablespace} is {usage}% full')
                    if health_status['overall_status'] == 'healthy':
                        health_status['overall_status'] = 'degraded'
            
            # Check for invalid objects
            cursor.execute("SELECT COUNT(*) FROM dba_objects WHERE status = 'INVALID'")
            invalid_objects = cursor.fetchone()[0]
            
            if invalid_objects > 0:
                health_status['warnings'].append(f'{invalid_objects} invalid database objects found')
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'degraded'
            
            cursor.close()
            
        except Exception as e:
            health_status['errors'].append(f'Health check error: {str(e)}')
            health_status['overall_status'] = 'unhealthy'
        
        return health_status
    
    def load_diagnostic_queries(self) -> Dict:
        """Load useful diagnostic queries"""
        return {
            'session_info': """
                SELECT sid, serial#, username, status, machine, program, 
                       logon_time, last_call_et
                FROM v$session 
                WHERE username IS NOT NULL
                ORDER BY logon_time DESC
            """,
            'active_sessions': """
                SELECT COUNT(*) as active_sessions
                FROM v$session 
                WHERE status = 'ACTIVE'
            """,
            'lock_info': """
                SELECT l.sid, s.serial#, s.username, s.program,
                       o.object_name, l.locked_mode
                FROM v$locked_object l, v$session s, dba_objects o
                WHERE l.session_id = s.sid
                AND l.object_id = o.object_id
            """,
            'tablespace_usage': """
                SELECT df.tablespace_name,
                       ROUND(df.bytes/1024/1024, 2) as total_mb,
                       ROUND(NVL(fs.bytes, 0)/1024/1024, 2) as free_mb,
                       ROUND((df.bytes - NVL(fs.bytes, 0))/1024/1024, 2) as used_mb,
                       ROUND(((df.bytes - NVL(fs.bytes, 0))/df.bytes)*100, 2) as used_percent
                FROM (SELECT tablespace_name, SUM(bytes) as bytes
                      FROM dba_data_files
                      GROUP BY tablespace_name) df,
                     (SELECT tablespace_name, SUM(bytes) as bytes
                      FROM dba_free_space
                      GROUP BY tablespace_name) fs
                WHERE df.tablespace_name = fs.tablespace_name(+)
                ORDER BY used_percent DESC
            """
        }
```

---

## Application Performance Issues

### 1. Performance Monitoring and Analysis

```python
# troubleshooting/performance_analysis.py
import time
import psutil
import threading
from typing import Dict, List
from collections import deque
import statistics

class PerformanceMonitor:
    """
    Monitor and analyze application performance
    """
    
    def __init__(self, sample_interval=1, history_size=300):
        self.sample_interval = sample_interval
        self.history_size = history_size
        self.metrics_history = {
            'cpu_usage': deque(maxlen=history_size),
            'memory_usage': deque(maxlen=history_size),
            'response_times': deque(maxlen=history_size),
            'request_count': deque(maxlen=history_size),
            'error_count': deque(maxlen=history_size)
        }
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory_info = psutil.virtual_memory()
                
                self.metrics_history['cpu_usage'].append(cpu_percent)
                self.metrics_history['memory_usage'].append(memory_info.percent)
                
                time.sleep(self.sample_interval)
                
            except Exception as e:
                print(f"Monitoring error: {str(e)}")
                time.sleep(self.sample_interval)
    
    def record_request_metrics(self, response_time: float, status_code: int):
        """Record request-specific metrics"""
        self.metrics_history['response_times'].append(response_time)
        self.metrics_history['request_count'].append(1)
        
        if status_code >= 400:
            self.metrics_history['error_count'].append(1)
        else:
            self.metrics_history['error_count'].append(0)
    
    def get_performance_summary(self, time_window: int = 60) -> Dict:
        """Get performance summary for specified time window"""
        window_size = min(time_window, len(self.metrics_history['cpu_usage']))
        
        if window_size == 0:
            return {'error': 'No metrics available'}
        
        # Calculate statistics for the time window
        cpu_values = list(self.metrics_history['cpu_usage'])[-window_size:]
        memory_values = list(self.metrics_history['memory_usage'])[-window_size:]
        response_times = list(self.metrics_history['response_times'])[-window_size:]
        
        summary = {
            'time_window_seconds': time_window,
            'cpu_usage': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': statistics.mean(cpu_values) if cpu_values else 0,
                'peak': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0
            },
            'memory_usage': {
                'current': memory_values[-1] if memory_values else 0,
                'average': statistics.mean(memory_values) if memory_values else 0,
                'peak': max(memory_values) if memory_values else 0
            },
            'response_times': {
                'average': statistics.mean(response_times) if response_times else 0,
                'p95': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0,
                'p99': statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else 0,
                'max': max(response_times) if response_times else 0
            },
            'request_metrics': {
                'total_requests': sum(self.metrics_history['request_count'][-window_size:]),
                'error_count': sum(self.metrics_history['error_count'][-window_size:]),
                'error_rate': (sum(self.metrics_history['error_count'][-window_size:]) / 
                             max(sum(self.metrics_history['request_count'][-window_size:]), 1)) * 100
            }
        }
        
        # Add performance assessment
        summary['assessment'] = self.assess_performance(summary)
        
        return summary
    
    def assess_performance(self, metrics: Dict) -> Dict:
        """Assess overall performance based on metrics"""
        issues = []
        recommendations = []
        severity = 'good'
        
        # CPU usage assessment
        if metrics['cpu_usage']['average'] > 80:
            issues.append('High CPU usage detected')
            recommendations.append('Investigate CPU-intensive operations')
            severity = 'critical'
        elif metrics['cpu_usage']['average'] > 60:
            issues.append('Elevated CPU usage')
            recommendations.append('Monitor CPU usage trends')
            severity = 'warning' if severity == 'good' else severity
        
        # Memory usage assessment
        if metrics['memory_usage']['average'] > 85:
            issues.append('High memory usage detected')
            recommendations.append('Check for memory leaks or optimize memory usage')
            severity = 'critical'
        elif metrics['memory_usage']['average'] > 70:
            issues.append('Elevated memory usage')
            recommendations.append('Monitor memory usage patterns')
            severity = 'warning' if severity == 'good' else severity
        
        # Response time assessment
        if metrics['response_times']['average'] > 2000:  # 2 seconds
            issues.append('Slow response times detected')
            recommendations.append('Optimize database queries and application logic')
            severity = 'critical'
        elif metrics['response_times']['average'] > 1000:  # 1 second
            issues.append('Elevated response times')
            recommendations.append('Review performance bottlenecks')
            severity = 'warning' if severity == 'good' else severity
        
        # Error rate assessment
        if metrics['request_metrics']['error_rate'] > 5:
            issues.append('High error rate detected')
            recommendations.append('Investigate application errors')
            severity = 'critical'
        elif metrics['request_metrics']['error_rate'] > 1:
            issues.append('Elevated error rate')
            recommendations.append('Monitor error patterns')
            severity = 'warning' if severity == 'good' else severity
        
        return {
            'severity': severity,
            'issues': issues,
            'recommendations': recommendations,
            'overall_score': self.calculate_performance_score(metrics)
        }
    
    def calculate_performance_score(self, metrics: Dict) -> int:
        """Calculate overall performance score (0-100)"""
        score = 100
        
        # Deduct points based on metrics
        cpu_penalty = max(0, (metrics['cpu_usage']['average'] - 50) * 2)
        memory_penalty = max(0, (metrics['memory_usage']['average'] - 60) * 2)
        response_penalty = max(0, (metrics['response_times']['average'] - 500) / 20)
        error_penalty = metrics['request_metrics']['error_rate'] * 10
        
        total_penalty = cpu_penalty + memory_penalty + response_penalty + error_penalty
        score = max(0, score - total_penalty)
        
        return int(score)

class PerformanceTuningRecommendations:
    """
    Generate performance tuning recommendations
    """
    
    def __init__(self):
        self.tuning_strategies = self.load_tuning_strategies()
    
    def generate_recommendations(self, performance_data: Dict) -> Dict:
        """Generate performance tuning recommendations"""
        recommendations = {
            'immediate_actions': [],
            'short_term_optimizations': [],
            'long_term_improvements': [],
            'monitoring_enhancements': []
        }
        
        # Analyze different performance aspects
        cpu_analysis = self.analyze_cpu_performance(performance_data)
        memory_analysis = self.analyze_memory_performance(performance_data)
        response_analysis = self.analyze_response_performance(performance_data)
        
        # Merge recommendations
        for category in recommendations.keys():
            recommendations[category].extend(cpu_analysis.get(category, []))
            recommendations[category].extend(memory_analysis.get(category, []))
            recommendations[category].extend(response_analysis.get(category, []))
        
        return recommendations
    
    def analyze_cpu_performance(self, data: Dict) -> Dict:
        """Analyze CPU performance and generate recommendations"""
        cpu_usage = data.get('cpu_usage', {})
        recommendations = {
            'immediate_actions': [],
            'short_term_optimizations': [],
            'long_term_improvements': []
        }
        
        if cpu_usage.get('average', 0) > 80:
            recommendations['immediate_actions'].extend([
                'Scale up application instances',
                'Check for CPU-intensive operations',
                'Review background task processing'
            ])
            recommendations['short_term_optimizations'].extend([
                'Optimize database queries',
                'Implement caching strategies',
                'Profile application bottlenecks'
            ])
        elif cpu_usage.get('average', 0) > 60:
            recommendations['short_term_optimizations'].extend([
                'Monitor CPU usage trends',
                'Consider horizontal scaling',
                'Optimize inefficient algorithms'
            ])
        
        return recommendations
    
    def analyze_memory_performance(self, data: Dict) -> Dict:
        """Analyze memory performance and generate recommendations"""
        memory_usage = data.get('memory_usage', {})
        recommendations = {
            'immediate_actions': [],
            'short_term_optimizations': [],
            'long_term_improvements': []
        }
        
        if memory_usage.get('average', 0) > 85:
            recommendations['immediate_actions'].extend([
                'Increase available memory',
                'Check for memory leaks',
                'Restart application if necessary'
            ])
            recommendations['short_term_optimizations'].extend([
                'Optimize memory usage patterns',
                'Implement object pooling',
                'Review garbage collection settings'
            ])
        elif memory_usage.get('average', 0) > 70:
            recommendations['short_term_optimizations'].extend([
                'Monitor memory usage patterns',
                'Optimize data structures',
                'Implement memory profiling'
            ])
        
        return recommendations
    
    def analyze_response_performance(self, data: Dict) -> Dict:
        """Analyze response time performance and generate recommendations"""
        response_times = data.get('response_times', {})
        recommendations = {
            'immediate_actions': [],
            'short_term_optimizations': [],
            'long_term_improvements': []
        }
        
        if response_times.get('average', 0) > 2000:
            recommendations['immediate_actions'].extend([
                'Identify slow endpoints',
                'Check database performance',
                'Review external service calls'
            ])
            recommendations['short_term_optimizations'].extend([
                'Optimize database queries',
                'Implement response caching',
                'Add connection pooling'
            ])
            recommendations['long_term_improvements'].extend([
                'Implement async processing',
                'Consider microservices architecture',
                'Add CDN for static content'
            ])
        elif response_times.get('average', 0) > 1000:
            recommendations['short_term_optimizations'].extend([
                'Profile application performance',
                'Optimize critical paths',
                'Add performance monitoring'
            ])
        
        return recommendations
    
    def load_tuning_strategies(self) -> Dict:
        """Load performance tuning strategies"""
        return {
            'database_optimization': [
                'Add appropriate indexes',
                'Optimize query execution plans',
                'Implement connection pooling',
                'Use database-specific optimizations',
                'Consider read replicas'
            ],
            'caching_strategies': [
                'Implement Redis caching',
                'Add application-level caching',
                'Use HTTP caching headers',
                'Implement database query caching',
                'Consider CDN integration'
            ],
            'application_optimization': [
                'Profile code performance',
                'Optimize algorithms and data structures',
                'Implement lazy loading',
                'Use async processing for heavy operations',
                'Optimize serialization/deserialization'
            ],
            'infrastructure_scaling': [
                'Horizontal scaling (more instances)',
                'Vertical scaling (more resources)',
                'Load balancing optimization',
                'Auto-scaling configuration',
                'Container orchestration tuning'
            ]
        }
```

---

## External Service Integration Issues

### 1. Firebase Integration Troubleshooting

```python
# troubleshooting/firebase_troubleshooting.py
import firebase_admin
from firebase_admin import auth, messaging
import requests
from typing import Dict, List

class FirebaseTroubleshooting:
    """
    Troubleshoot Firebase integration issues
    """
    
    def __init__(self):
        self.common_errors = self.load_firebase_errors()
    
    def diagnose_auth_issues(self, error_message: str, id_token: str = None) -> Dict:
        """Diagnose Firebase authentication issues"""
        diagnosis = {
            'issue_type': 'unknown',
            'solutions': [],
            'verification_steps': []
        }
        
        error_lower = error_message.lower()
        
        # Token validation issues
        if 'invalid' in error_lower and 'token' in error_lower:
            diagnosis['issue_type'] = 'invalid_token'
            diagnosis['solutions'] = [
                'Verify token format and structure',
                'Check token expiration time',
                'Ensure token is not corrupted',
                'Re-authenticate user to get new token'
            ]
            diagnosis['verification_steps'] = [
                'Decode token without verification',
                'Check token claims',
                'Verify token signature'
            ]
        
        # Expired token issues
        elif 'expired' in error_lower:
            diagnosis['issue_type'] = 'expired_token'
            diagnosis['solutions'] = [
                'Implement automatic token refresh',
                'Check token refresh logic',
                'Verify refresh token validity',
                'Update client-side token handling'
            ]
        
        # Network connectivity issues
        elif 'network' in error_lower or 'connection' in error_lower:
            diagnosis['issue_type'] = 'network_issue'
            diagnosis['solutions'] = [
                'Check internet connectivity',
                'Verify Firebase project configuration',
                'Check firewall settings',
                'Review proxy configuration'
            ]
        
        # Perform token validation if token provided
        if id_token:
            diagnosis['token_validation'] = self.validate_firebase_token(id_token)
        
        return diagnosis
    
    def validate_firebase_token(self, id_token: str) -> Dict:
        """Validate Firebase ID token"""
        try:
            # Verify the token
            decoded_token = auth.verify_id_token(id_token)
            
            return {
                'valid': True,
                'user_id': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'expires_at': decoded_token.get('exp'),
                'issued_at': decoded_token.get('iat'),
                'issuer': decoded_token.get('iss')
            }
        
        except auth.InvalidIdTokenError as e:
            return {
                'valid': False,
                'error': 'Invalid ID token',
                'details': str(e)
            }
        except auth.ExpiredIdTokenError as e:
            return {
                'valid': False,
                'error': 'Expired ID token',
                'details': str(e)
            }
        except Exception as e:
            return {
                'valid': False,
                'error': 'Token validation failed',
                'details': str(e)
            }
    
    def test_firebase_connectivity(self) -> Dict:
        """Test Firebase service connectivity"""
        connectivity_results = {
            'auth_service': False,
            'messaging_service': False,
            'firestore_service': False,
            'overall_status': 'fail'
        }
        
        try:
            # Test Authentication service
            try:
                # Try to get a user (this will fail but tests connectivity)
                auth.get_user('test-user-id')
            except auth.UserNotFoundError:
                # This is expected - service is reachable
                connectivity_results['auth_service'] = True
            except Exception:
                # Service unreachable
                connectivity_results['auth_service'] = False
            
            # Test Cloud Messaging service
            try:
                # Try to send a test message (dry run)
                message = messaging.Message(
                    data={'test': 'connectivity'},
                    token='test-token'
                )
                messaging.send(message, dry_run=True)
            except messaging.InvalidArgumentError:
                # This is expected for invalid token - service is reachable
                connectivity_results['messaging_service'] = True
            except Exception:
                connectivity_results['messaging_service'] = False
            
            # Overall status
            if connectivity_results['auth_service'] and connectivity_results['messaging_service']:
                connectivity_results['overall_status'] = 'pass'
            
        except Exception as e:
            connectivity_results['error'] = str(e)
        
        return connectivity_results
    
    def diagnose_messaging_issues(self, error_details: Dict) -> Dict:
        """Diagnose Firebase Cloud Messaging issues"""
        error_code = error_details.get('error_code')
        error_message = error_details.get('error_message', '').lower()
        
        diagnosis = {
            'issue_category': 'unknown',
            'solutions': [],
            'prevention_tips': []
        }
        
        # Token-related issues
        if error_code == 'INVALID_ARGUMENT' or 'invalid' in error_message:
            diagnosis['issue_category'] = 'invalid_token'
            diagnosis['solutions'] = [
                'Verify FCM token format',
                'Check if token is still valid',
                'Re-register device for new token',
                'Validate token before sending'
            ]
        
        # Registration token issues
        elif error_code == 'UNREGISTERED' or 'not registered' in error_message:
            diagnosis['issue_category'] = 'unregistered_token'
            diagnosis['solutions'] = [
                'Remove token from database',
                'Re-register device',
                'Implement token cleanup process',
                'Handle token refresh on client'
            ]
        
        # Quota exceeded
        elif error_code == 'QUOTA_EXCEEDED' or 'quota' in error_message:
            diagnosis['issue_category'] = 'quota_exceeded'
            diagnosis['solutions'] = [
                'Review message sending frequency',
                'Implement rate limiting',
                'Optimize message content',
                'Consider upgrading Firebase plan'
            ]
        
        # Server errors
        elif error_code in ['INTERNAL', 'UNAVAILABLE'] or 'server' in error_message:
            diagnosis['issue_category'] = 'server_error'
            diagnosis['solutions'] = [
                'Implement retry mechanism',
                'Wait and retry with exponential backoff',
                'Check Firebase status page',
                'Monitor error rates'
            ]
        
        return diagnosis
    
    def load_firebase_errors(self) -> Dict:
        """Load common Firebase error codes and solutions"""
        return {
            'auth_errors': {
                'INVALID_ID_TOKEN': 'ID token is invalid or expired',
                'TOKEN_EXPIRED': 'ID token has expired',
                'USER_NOT_FOUND': 'User record not found',
                'EMAIL_ALREADY_EXISTS': 'Email is already in use',
                'WEAK_PASSWORD': 'Password is too weak'
            },
            'messaging_errors': {
                'INVALID_ARGUMENT': 'Invalid message format or token',
                'UNREGISTERED': 'Device token is not registered',
                'SENDER_ID_MISMATCH': 'Token belongs to different sender',
                'QUOTA_EXCEEDED': 'Message quota exceeded',
                'UNAVAILABLE': 'FCM service temporarily unavailable'
            }
        }

class TwilioTroubleshooting:
    """
    Troubleshoot Twilio integration issues
    """
    
    def __init__(self, account_sid: str, auth_token: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
    
    def diagnose_sms_issues(self, error_code: str, error_message: str) -> Dict:
        """Diagnose Twilio SMS issues"""
        error_solutions = {
            '20003': {
                'description': 'Authentication Error',
                'solutions': [
                    'Verify Account SID and Auth Token',
                    'Check if credentials are expired',
                    'Ensure proper API key permissions'
                ]
            },
            '21211': {
                'description': 'Invalid phone number',
                'solutions': [
                    'Format phone number with country code',
                    'Verify phone number is valid',
                    'Check for special characters in number'
                ]
            },
            '21610': {
                'description': 'Message blocked by carrier',
                'solutions': [
                    'Review message content for spam keywords',
                    'Use verified sender ID',
                    'Check if number is on opt-out list'
                ]
            },
            '30001': {
                'description': 'Queue overflow',
                'solutions': [
                    'Implement rate limiting',
                    'Spread message sending over time',
                    'Monitor queue status'
                ]
            }
        }
        
        diagnosis = error_solutions.get(error_code, {
            'description': 'Unknown error',
            'solutions': ['Check Twilio documentation for error code']
        })
        
        # Add general troubleshooting steps
        diagnosis['general_checks'] = [
            'Verify account balance',
            'Check service status',
            'Review message logs',
            'Validate phone number format'
        ]
        
        return diagnosis
    
    def test_twilio_connectivity(self) -> Dict:
        """Test Twilio service connectivity"""
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            # Test by fetching account info
            account = client.api.accounts(self.account_sid).fetch()
            
            return {
                'status': 'connected',
                'account_sid': account.sid,
                'account_status': account.status,
                'date_created': str(account.date_created)
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'troubleshooting_steps': [
                    'Verify Account SID and Auth Token',
                    'Check internet connectivity',
                    'Verify Twilio service status'
                ]
            }
    
    def validate_phone_number(self, phone_number: str) -> Dict:
        """Validate phone number format for Twilio"""
        validation_result = {
            'valid': False,
            'formatted_number': None,
            'issues': []
        }
        
        # Remove all non-numeric characters except +
        cleaned_number = ''.join(char for char in phone_number if char.isdigit() or char == '+')
        
        # Check if starts with +
        if not cleaned_number.startswith('+'):
            validation_result['issues'].append('Number should start with country code (+)')
            return validation_result
        
        # Check minimum length (country code + number)
        if len(cleaned_number) < 10:
            validation_result['issues'].append('Number too short')
            return validation_result
        
        # Check maximum length
        if len(cleaned_number) > 15:
            validation_result['issues'].append('Number too long')
            return validation_result
        
        validation_result['valid'] = True
        validation_result['formatted_number'] = cleaned_number
        
        return validation_result

class SendGridTroubleshooting:
    """
    Troubleshoot SendGrid integration issues
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def diagnose_email_delivery_issues(self, error_details: Dict) -> Dict:
        """Diagnose SendGrid email delivery issues"""
        status_code = error_details.get('status_code')
        error_message = error_details.get('message', '').lower()
        
        diagnosis = {
            'issue_category': 'unknown',
            'solutions': [],
            'next_steps': []
        }
        
        # Authentication issues
        if status_code == 401:
            diagnosis['issue_category'] = 'authentication'
            diagnosis['solutions'] = [
                'Verify API key is correct',
                'Check API key permissions',
                'Ensure API key is not expired',
                'Regenerate API key if needed'
            ]
        
        # Forbidden/Permission issues
        elif status_code == 403:
            diagnosis['issue_category'] = 'permissions'
            diagnosis['solutions'] = [
                'Check API key scopes',
                'Verify sender identity',
                'Review account permissions',
                'Contact SendGrid support'
            ]
        
        # Rate limiting
        elif status_code == 429:
            diagnosis['issue_category'] = 'rate_limiting'
            diagnosis['solutions'] = [
                'Implement exponential backoff',
                'Reduce sending rate',
                'Upgrade SendGrid plan',
                'Spread email sending over time'
            ]
        
        # Invalid content
        elif status_code == 400:
            diagnosis['issue_category'] = 'invalid_content'
            diagnosis['solutions'] = [
                'Validate email addresses',
                'Check email content format',
                'Verify required fields',
                'Review API request structure'
            ]
        
        # Content filtering
        elif 'spam' in error_message or 'content' in error_message:
            diagnosis['issue_category'] = 'content_filtering'
            diagnosis['solutions'] = [
                'Review email content for spam triggers',
                'Use verified sender domain',
                'Implement proper authentication (SPF, DKIM)',
                'Check sender reputation'
            ]
        
        return diagnosis
    
    def test_sendgrid_connectivity(self) -> Dict:
        """Test SendGrid service connectivity"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            
            # Test with API key validation endpoint
            response = sg.client.scopes.get()
            
            if response.status_code == 200:
                return {
                    'status': 'connected',
                    'api_key_valid': True,
                    'scopes': response.body
                }
            else:
                return {
                    'status': 'failed',
                    'api_key_valid': False,
                    'error': f'HTTP {response.status_code}'
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'troubleshooting_steps': [
                    'Verify API key',
                    'Check internet connectivity',
                    'Review SendGrid service status'
                ]
            }
    
    def validate_email_format(self, email: str) -> Dict:
        """Validate email format for SendGrid"""
        import re
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        validation_result = {
            'valid': bool(re.match(email_pattern, email)),
            'email': email,
            'issues': []
        }
        
        if not validation_result['valid']:
            validation_result['issues'] = [
                'Invalid email format',
                'Ensure proper email structure (user@domain.com)'
            ]
        
        return validation_result
```

---

## Authentication and Authorization Issues

### 1. Authentication Troubleshooting

```python
# troubleshooting/auth_troubleshooting.py
import jwt
import datetime
from typing import Dict, List

class AuthenticationTroubleshooting:
    """
    Troubleshoot authentication and authorization issues
    """
    
    def __init__(self):
        self.auth_error_patterns = self.load_auth_error_patterns()
    
    def diagnose_auth_failure(self, error_type: str, error_details: Dict) -> Dict:
        """Diagnose authentication failures"""
        diagnosis = {
            'failure_type': error_type,
            'root_cause': 'unknown',
            'solutions': [],
            'security_considerations': []
        }
        
        error_message = error_details.get('message', '').lower()
        status_code = error_details.get('status_code')
        
        # Token-related issues
        if 'token' in error_message:
            if 'expired' in error_message:
                diagnosis['root_cause'] = 'expired_token'
                diagnosis['solutions'] = [
                    'Implement automatic token refresh',
                    'Check token expiration handling',
                    'Verify token TTL configuration',
                    'Update client-side token management'
                ]
            elif 'invalid' in error_message:
                diagnosis['root_cause'] = 'invalid_token'
                diagnosis['solutions'] = [
                    'Verify token format and structure',
                    'Check token signing key',
                    'Validate token claims',
                    'Ensure token is not corrupted'
                ]
            elif 'missing' in error_message:
                diagnosis['root_cause'] = 'missing_token'
                diagnosis['solutions'] = [
                    'Check authorization header format',
                    'Verify token is included in request',
                    'Review client authentication flow',
                    'Validate API endpoint requirements'
                ]
        
        # Credential issues
        elif 'credential' in error_message or 'password' in error_message:
            diagnosis['root_cause'] = 'invalid_credentials'
            diagnosis['solutions'] = [
                'Verify username/password combination',
                'Check account status (locked, disabled)',
                'Review password policy compliance',
                'Check for typos in credentials'
            ]
            diagnosis['security_considerations'] = [
                'Monitor failed login attempts',
                'Implement account lockout policies',
                'Review brute force protection',
                'Check for credential stuffing attacks'
            ]
        
        # Permission issues
        elif status_code == 403 or 'permission' in error_message:
            diagnosis['root_cause'] = 'insufficient_permissions'
            diagnosis['solutions'] = [
                'Verify user role assignments',
                'Check resource-level permissions',
                'Review API endpoint access controls',
                'Validate permission inheritance'
            ]
        
        return diagnosis
    
    def analyze_jwt_token(self, token: str, secret_key: str = None) -> Dict:
        """Analyze JWT token for issues"""
        analysis = {
            'valid': False,
            'decoded_payload': None,
            'issues': [],
            'security_warnings': []
        }
        
        try:
            # Decode without verification first to check structure
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            analysis['decoded_payload'] = unverified_payload
            
            # Check token expiration
            if 'exp' in unverified_payload:
                exp_timestamp = unverified_payload['exp']
                current_timestamp = datetime.datetime.utcnow().timestamp()
                
                if exp_timestamp < current_timestamp:
                    analysis['issues'].append('Token has expired')
                else:
                    time_until_expiry = exp_timestamp - current_timestamp
                    if time_until_expiry < 300:  # Less than 5 minutes
                        analysis['security_warnings'].append('Token will expire soon')
            
            # Check required claims
            required_claims = ['sub', 'iat', 'exp']
            missing_claims = [claim for claim in required_claims if claim not in unverified_payload]
            if missing_claims:
                analysis['issues'].extend([f'Missing claim: {claim}' for claim in missing_claims])
            
            # Verify signature if secret provided
            if secret_key:
                try:
                    verified_payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                    analysis['valid'] = True
                except jwt.InvalidSignatureError:
                    analysis['issues'].append('Invalid token signature')
                except jwt.DecodeError:
                    analysis['issues'].append('Token decode error')
            
        except jwt.DecodeError:
            analysis['issues'].append('Invalid token format')
        except Exception as e:
            analysis['issues'].append(f'Token analysis error: {str(e)}')
        
        return analysis
    
    def check_session_management(self, session_data: Dict) -> Dict:
        """Check session management issues"""
        issues = []
        recommendations = []
        
        # Check session timeout
        if 'last_activity' in session_data:
            last_activity = datetime.datetime.fromisoformat(session_data['last_activity'])
            time_since_activity = datetime.datetime.utcnow() - last_activity
            
            if time_since_activity.total_seconds() > 3600:  # 1 hour
                issues.append('Session inactive for extended period')
                recommendations.append('Implement session timeout warnings')
        
        # Check for concurrent sessions
        if session_data.get('concurrent_sessions', 0) > 3:
            issues.append('Multiple concurrent sessions detected')
            recommendations.append('Review concurrent session policies')
        
        # Check session security
        if not session_data.get('secure_flag', False):
            issues.append('Session not marked as secure')
            recommendations.append('Enable secure session flags')
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'session_health': 'healthy' if not issues else 'issues_detected'
        }
    
    def load_auth_error_patterns(self) -> Dict:
        """Load common authentication error patterns"""
        return {
            'token_errors': {
                'expired': ['expired', 'timeout', 'ttl'],
                'invalid': ['invalid', 'malformed', 'corrupt'],
                'missing': ['missing', 'absent', 'not found']
            },
            'credential_errors': {
                'wrong_password': ['password', 'credential', 'authentication failed'],
                'account_locked': ['locked', 'disabled', 'suspended'],
                'user_not_found': ['not found', 'unknown user', 'invalid user']
            },
            'permission_errors': {
                'insufficient_privileges': ['permission', 'privilege', 'access denied'],
                'role_missing': ['role', 'authority', 'scope'],
                'resource_forbidden': ['forbidden', 'not authorized', 'access restricted']
            }
        }

class SecurityAuditTools:
    """
    Security audit and troubleshooting tools
    """
    
    def __init__(self):
        self.security_checks = self.load_security_checks()
    
    def audit_authentication_security(self, auth_config: Dict) -> Dict:
        """Audit authentication security configuration"""
        audit_results = {
            'overall_score': 100,
            'passed_checks': [],
            'failed_checks': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Password policy checks
        password_policy = auth_config.get('password_policy', {})
        
        if password_policy.get('min_length', 0) < 8:
            audit_results['failed_checks'].append('Password minimum length too short')
            audit_results['overall_score'] -= 15
        else:
            audit_results['passed_checks'].append('Password minimum length adequate')
        
        if not password_policy.get('require_special_chars', False):
            audit_results['warnings'].append('Special characters not required in passwords')
            audit_results['overall_score'] -= 5
        
        # Token security checks
        token_config = auth_config.get('token_config', {})
        
        if token_config.get('expiry_time', 0) > 3600:  # More than 1 hour
            audit_results['warnings'].append('Token expiry time is long')
            audit_results['overall_score'] -= 5
        
        if not token_config.get('refresh_enabled', False):
            audit_results['failed_checks'].append('Token refresh not enabled')
            audit_results['overall_score'] -= 10
        
        # Session security checks
        session_config = auth_config.get('session_config', {})
        
        if not session_config.get('secure_cookies', False):
            audit_results['failed_checks'].append('Secure cookie flag not enabled')
            audit_results['overall_score'] -= 20
        
        if not session_config.get('httponly_cookies', False):
            audit_results['failed_checks'].append('HttpOnly cookie flag not enabled')
            audit_results['overall_score'] -= 15
        
        # Generate recommendations
        if audit_results['overall_score'] < 80:
            audit_results['recommendations'].extend([
                'Review and strengthen authentication policies',
                'Implement multi-factor authentication',
                'Enable security headers and flags',
                'Regular security audits and penetration testing'
            ])
        
        return audit_results
    
    def check_common_vulnerabilities(self, request_data: Dict) -> Dict:
        """Check for common security vulnerabilities"""
        vulnerabilities = {
            'sql_injection': self.check_sql_injection(request_data),
            'xss_attacks': self.check_xss_attacks(request_data),
            'csrf_tokens': self.check_csrf_protection(request_data),
            'input_validation': self.check_input_validation(request_data)
        }
        
        risk_level = 'low'
        if any(vuln['risk'] == 'high' for vuln in vulnerabilities.values()):
            risk_level = 'high'
        elif any(vuln['risk'] == 'medium' for vuln in vulnerabilities.values()):
            risk_level = 'medium'
        
        return {
            'overall_risk': risk_level,
            'vulnerabilities': vulnerabilities,
            'remediation_priority': self.prioritize_remediation(vulnerabilities)
        }
    
    def check_sql_injection(self, request_data: Dict) -> Dict:
        """Check for SQL injection patterns"""
        sql_patterns = [
            "'; DROP TABLE", "' OR '1'='1", "UNION SELECT", 
            "'; INSERT INTO", "'; UPDATE", "'; DELETE FROM"
        ]
        
        request_str = str(request_data).upper()
        detected_patterns = [pattern for pattern in sql_patterns if pattern in request_str]
        
        return {
            'detected': len(detected_patterns) > 0,
            'patterns': detected_patterns,
            'risk': 'high' if detected_patterns else 'low',
            'mitigation': 'Use parameterized queries and input validation'
        }
    
    def check_xss_attacks(self, request_data: Dict) -> Dict:
        """Check for XSS attack patterns"""
        xss_patterns = [
            "<script>", "</script>", "javascript:", "onload=", 
            "onerror=", "onclick=", "alert(", "document.cookie"
        ]
        
        request_str = str(request_data).lower()
        detected_patterns = [pattern for pattern in xss_patterns if pattern in request_str]
        
        return {
            'detected': len(detected_patterns) > 0,
            'patterns': detected_patterns,
            'risk': 'high' if detected_patterns else 'low',
            'mitigation': 'Implement input sanitization and output encoding'
        }
    
    def check_csrf_protection(self, request_data: Dict) -> Dict:
        """Check for CSRF protection"""
        has_csrf_token = 'csrf_token' in request_data or 'X-CSRFToken' in request_data.get('headers', {})
        
        return {
            'protected': has_csrf_token,
            'risk': 'low' if has_csrf_token else 'medium',
            'mitigation': 'Implement CSRF tokens for state-changing operations'
        }
    
    def check_input_validation(self, request_data: Dict) -> Dict:
        """Check input validation"""
        issues = []
        
        # Check for oversized inputs
        for key, value in request_data.items():
            if isinstance(value, str) and len(value) > 10000:
                issues.append(f'Oversized input in field: {key}')
        
        # Check for suspicious characters
        suspicious_chars = ['../', '\\', '\x00', '\r\n']
        for key, value in request_data.items():
            if isinstance(value, str):
                for char in suspicious_chars:
                    if char in value:
                        issues.append(f'Suspicious character in field: {key}')
        
        return {
            'issues': issues,
            'risk': 'medium' if issues else 'low',
            'mitigation': 'Implement comprehensive input validation and sanitization'
        }
    
    def prioritize_remediation(self, vulnerabilities: Dict) -> List[str]:
        """Prioritize vulnerability remediation"""
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for vuln_type, vuln_data in vulnerabilities.items():
            if vuln_data['risk'] == 'high':
                high_priority.append(vuln_type)
            elif vuln_data['risk'] == 'medium':
                medium_priority.append(vuln_type)
            else:
                low_priority.append(vuln_type)
        
        return high_priority + medium_priority + low_priority
    
    def load_security_checks(self) -> Dict:
        """Load security check configurations"""
        return {
            'authentication': [
                'Password complexity requirements',
                'Multi-factor authentication',
                'Account lockout policies',
                'Session timeout configuration'
            ],
            'authorization': [
                'Role-based access control',
                'Principle of least privilege',
                'Resource-level permissions',
                'API endpoint protection'
            ],
            'data_protection': [
                'Encryption at rest',
                'Encryption in transit',
                'Data masking/anonymization',
                'Secure key management'
            ],
            'infrastructure': [
                'Network segmentation',
                'Firewall configuration',
                'SSL/TLS configuration',
                'Security monitoring'
            ]
        }
```

---

## Deployment and Infrastructure Issues

### 1. Containerization Troubleshooting

```python
# troubleshooting/container_troubleshooting.py
import docker
import subprocess
import json
from typing import Dict, List

class DockerTroubleshooting:
    """
    Troubleshoot Docker containerization issues
    """
    
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            self.client = None
            print(f"Docker client initialization failed: {e}")
    
    def diagnose_container_startup_failure(self, container_name: str) -> Dict:
        """Diagnose container startup failures"""
        if not self.client:
            return {'error': 'Docker client not available'}
        
        diagnosis = {
            'container_name': container_name,
            'issues_found': [],
            'recommendations': [],
            'logs': None
        }
        
        try:
            # Try to get container information
            container = self.client.containers.get(container_name)
            
            # Check container status
            status = container.status
            diagnosis['status'] = status
            
            if status != 'running':
                diagnosis['issues_found'].append(f'Container status is {status}')
                
                # Get container logs
                logs = container.logs(tail=50).decode('utf-8')
                diagnosis['logs'] = logs
                
                # Analyze logs for common issues
                log_analysis = self.analyze_container_logs(logs)
                diagnosis['issues_found'].extend(log_analysis['issues'])
                diagnosis['recommendations'].extend(log_analysis['recommendations'])
            
            # Check resource usage
            stats = container.stats(stream=False)
            diagnosis['resource_usage'] = self.analyze_resource_usage(stats)
            
        except docker.errors.NotFound:
            diagnosis['issues_found'].append('Container not found')
            diagnosis['recommendations'].extend([
                'Check container name spelling',
                'Verify container was created',
                'List all containers with: docker ps -a'
            ])
        except Exception as e:
            diagnosis['issues_found'].append(f'Error accessing container: {str(e)}')
        
        return diagnosis
    
    def analyze_container_logs(self, logs: str) -> Dict:
        """Analyze container logs for common issues"""
        analysis = {
            'issues': [],
            'recommendations': []
        }
        
        log_lower = logs.lower()
        
        # Port binding issues
        if 'port' in log_lower and ('already in use' in log_lower or 'bind' in log_lower):
            analysis['issues'].append('Port binding conflict')
            analysis['recommendations'].extend([
                'Check if port is already in use',
                'Kill process using the port',
                'Use different port mapping'
            ])
        
        # Memory issues
        if 'out of memory' in log_lower or 'oom' in log_lower:
            analysis['issues'].append('Out of memory error')
            analysis['recommendations'].extend([
                'Increase container memory limit',
                'Optimize application memory usage',
                'Check for memory leaks'
            ])
        
        # Permission issues
        if 'permission denied' in log_lower:
            analysis['issues'].append('Permission denied')
            analysis['recommendations'].extend([
                'Check file/directory permissions',
                'Review user context in Dockerfile',
                'Verify volume mount permissions'
            ])
        
        # Database connection issues
        if 'connection refused' in log_lower or 'connection timeout' in log_lower:
            analysis['issues'].append('Database connection failed')
            analysis['recommendations'].extend([
                'Check database container status',
                'Verify network connectivity',
                'Review connection string configuration'
            ])
        
        # Missing dependencies
        if 'modulenotfounderror' in log_lower or 'importerror' in log_lower:
            analysis['issues'].append('Missing Python dependencies')
            analysis['recommendations'].extend([
                'Rebuild image with all dependencies',
                'Check requirements.txt completeness',
                'Verify pip install process in Dockerfile'
            ])
        
        return analysis
    
    def analyze_resource_usage(self, stats: Dict) -> Dict:
        """Analyze container resource usage"""
        analysis = {
            'memory': {},
            'cpu': {},
            'warnings': []
        }
        
        try:
            # Memory analysis
            memory_stats = stats['memory_stats']
            memory_usage = memory_stats.get('usage', 0)
            memory_limit = memory_stats.get('limit', 0)
            
            if memory_limit > 0:
                memory_percent = (memory_usage / memory_limit) * 100
                analysis['memory'] = {
                    'usage_bytes': memory_usage,
                    'limit_bytes': memory_limit,
                    'usage_percent': memory_percent
                }
                
                if memory_percent > 90:
                    analysis['warnings'].append('High memory usage detected')
                elif memory_percent > 80:
                    analysis['warnings'].append('Elevated memory usage')
            
            # CPU analysis
            cpu_stats = stats['cpu_stats']
            cpu_usage = cpu_stats.get('cpu_usage', {})
            system_usage = cpu_stats.get('system_cpu_usage', 0)
            
            analysis['cpu'] = {
                'total_usage': cpu_usage.get('total_usage', 0),
                'system_usage': system_usage
            }
            
        except Exception as e:
            analysis['error'] = f'Resource analysis failed: {str(e)}'
        
        return analysis
    
    def check_docker_environment(self) -> Dict:
        """Check Docker environment health"""
        environment_check = {
            'docker_daemon': False,
            'docker_version': None,
            'available_space': None,
            'running_containers': 0,
            'image_count': 0,
            'issues': []
        }
        
        try:
            # Check Docker daemon
            version_info = self.client.version()
            environment_check['docker_daemon'] = True
            environment_check['docker_version'] = version_info.get('Version')
            
            # Check running containers
            containers = self.client.containers.list()
            environment_check['running_containers'] = len(containers)
            
            # Check images
            images = self.client.images.list()
            environment_check['image_count'] = len(images)
            
            # Check disk space
            system_info = self.client.info()
            environment_check['available_space'] = system_info.get('SystemStatus')
            
        except Exception as e:
            environment_check['issues'].append(f'Docker environment check failed: {str(e)}')
        
        return environment_check
    
    def troubleshoot_image_build_failure(self, dockerfile_path: str, build_logs: str) -> Dict:
        """Troubleshoot Docker image build failures"""
        troubleshooting = {
            'dockerfile_path': dockerfile_path,
            'issues_identified': [],
            'recommendations': []
        }
        
        log_lower = build_logs.lower()
        
        # Base image issues
        if 'pull access denied' in log_lower or 'not found' in log_lower:
            troubleshooting['issues_identified'].append('Base image not accessible')
            troubleshooting['recommendations'].extend([
                'Check base image name and tag',
                'Verify Docker Hub connectivity',
                'Try pulling base image manually'
            ])
        
        # Copy/ADD instruction failures
        if 'no such file or directory' in log_lower and ('copy' in log_lower or 'add' in log_lower):
            troubleshooting['issues_identified'].append('File copy operation failed')
            troubleshooting['recommendations'].extend([
                'Verify source file paths',
                'Check relative path references',
                'Ensure files exist in build context'
            ])
        
        # Package installation failures
        if 'package not found' in log_lower or 'failed to fetch' in log_lower:
            troubleshooting['issues_identified'].append('Package installation failed')
            troubleshooting['recommendations'].extend([
                'Update package manager cache',
                'Check package name spelling',
                'Verify package repository availability'
            ])
        
        # Permission issues
        if 'permission denied' in log_lower:
            troubleshooting['issues_identified'].append('Permission denied during build')
            troubleshooting['recommendations'].extend([
                'Check Dockerfile USER instructions',
                'Verify file permissions in build context',
                'Review directory ownership'
            ])
        
        return troubleshooting

class KubernetesTroubleshooting:
    """
    Troubleshoot Kubernetes deployment issues
    """
    
    def __init__(self):
        self.kubectl_available = self.check_kubectl_availability()
    
    def check_kubectl_availability(self) -> bool:
        """Check if kubectl is available"""
        try:
            subprocess.run(['kubectl', 'version', '--client'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def diagnose_pod_failures(self, namespace: str = 'default', pod_name: str = None) -> Dict:
        """Diagnose Kubernetes pod failures"""
        if not self.kubectl_available:
            return {'error': 'kubectl not available'}
        
        diagnosis = {
            'namespace': namespace,
            'pod_issues': [],
            'recommendations': []
        }
        
        try:
            # Get pod information
            if pod_name:
                cmd = ['kubectl', 'get', 'pod', pod_name, '-n', namespace, '-o', 'json']
            else:
                cmd = ['kubectl', 'get', 'pods', '-n', namespace, '-o', 'json']
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            pods_data = json.loads(result.stdout)
            
            # Handle single pod vs multiple pods
            if pod_name:
                pods_to_check = [pods_data]
            else:
                pods_to_check = pods_data.get('items', [])
            
            for pod in pods_to_check:
                pod_diagnosis = self.analyze_pod_status(pod)
                if pod_diagnosis['issues']:
                    diagnosis['pod_issues'].append({
                        'pod_name': pod['metadata']['name'],
                        'issues': pod_diagnosis['issues'],
                        'recommendations': pod_diagnosis['recommendations']
                    })
        
        except subprocess.CalledProcessError as e:
            diagnosis['pod_issues'].append({
                'error': f'kubectl command failed: {e.stderr}'
            })
        except json.JSONDecodeError:
            diagnosis['pod_issues'].append({
                'error': 'Failed to parse kubectl output'
            })
        
        return diagnosis
    
    def analyze_pod_status(self, pod_data: Dict) -> Dict:
        """Analyze individual pod status"""
        analysis = {
            'issues': [],
            'recommendations': []
        }
        
        status = pod_data.get('status', {})
        phase = status.get('phase', 'Unknown')
        
        # Check pod phase
        if phase == 'Pending':
            analysis['issues'].append('Pod is stuck in Pending state')
            analysis['recommendations'].extend([
                'Check node resource availability',
                'Verify image pull policies',
                'Review pod scheduling constraints'
            ])
        elif phase == 'Failed':
            analysis['issues'].append('Pod has failed')
            analysis['recommendations'].append('Check pod logs for error details')
        
        # Check container statuses
        container_statuses = status.get('containerStatuses', [])
        for container_status in container_statuses:
            container_analysis = self.analyze_container_status(container_status)
            analysis['issues'].extend(container_analysis['issues'])
            analysis['recommendations'].extend(container_analysis['recommendations'])
        
        # Check conditions
        conditions = status.get('conditions', [])
        for condition in conditions:
            if condition['status'] == 'False':
                analysis['issues'].append(f"Condition {condition['type']} is False: {condition.get('message', '')}")
        
        return analysis
    
    def analyze_container_status(self, container_status: Dict) -> Dict:
        """Analyze container status within pod"""
        analysis = {
            'issues': [],
            'recommendations': []
        }
        
        ready = container_status.get('ready', False)
        if not ready:
            analysis['issues'].append(f"Container {container_status['name']} not ready")
        
        # Check container state
        state = container_status.get('state', {})
        
        if 'waiting' in state:
            waiting_reason = state['waiting'].get('reason', 'Unknown')
            waiting_message = state['waiting'].get('message', '')
            
            analysis['issues'].append(f"Container waiting: {waiting_reason}")
            
            if waiting_reason == 'ImagePullBackOff':
                analysis['recommendations'].extend([
                    'Check image name and tag',
                    'Verify image registry accessibility',
                    'Check image pull secrets'
                ])
            elif waiting_reason == 'CrashLoopBackOff':
                analysis['recommendations'].extend([
                    'Check container logs',
                    'Review application startup process',
                    'Verify resource limits'
                ])
        
        elif 'terminated' in state:
            terminated_reason = state['terminated'].get('reason', 'Unknown')
            exit_code = state['terminated'].get('exitCode', 0)
            
            analysis['issues'].append(f"Container terminated: {terminated_reason} (exit code: {exit_code})")
            
            if exit_code != 0:
                analysis['recommendations'].extend([
                    'Check application logs',
                    'Review exit code meaning',
                    'Verify application configuration'
                ])
        
        return analysis
    
    def check_service_connectivity(self, service_name: str, namespace: str = 'default') -> Dict:
        """Check Kubernetes service connectivity"""
        if not self.kubectl_available:
            return {'error': 'kubectl not available'}
        
        connectivity_check = {
            'service_name': service_name,
            'namespace': namespace,
            'service_exists': False,
            'endpoints_available': False,
            'issues': []
        }
        
        try:
            # Check if service exists
            cmd = ['kubectl', 'get', 'service', service_name, '-n', namespace, '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            service_data = json.loads(result.stdout)
            connectivity_check['service_exists'] = True
            
            # Check service endpoints
            cmd = ['kubectl', 'get', 'endpoints', service_name, '-n', namespace, '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            endpoints_data = json.loads(result.stdout)
            
            subsets = endpoints_data.get('subsets', [])
            if subsets and any(subset.get('addresses') for subset in subsets):
                connectivity_check['endpoints_available'] = True
            else:
                connectivity_check['issues'].append('No endpoints available for service')
        
        except subprocess.CalledProcessError:
            connectivity_check['issues'].append('Service not found or kubectl error')
        except json.JSONDecodeError:
            connectivity_check['issues'].append('Failed to parse service information')
        
        return connectivity_check
    
    def diagnose_deployment_issues(self, deployment_name: str, namespace: str = 'default') -> Dict:
        """Diagnose Kubernetes deployment issues"""
        if not self.kubectl_available:
            return {'error': 'kubectl not available'}
        
        diagnosis = {
            'deployment_name': deployment_name,
            'namespace': namespace,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Get deployment status
            cmd = ['kubectl', 'get', 'deployment', deployment_name, '-n', namespace, '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            deployment_data = json.loads(result.stdout)
            
            status = deployment_data.get('status', {})
            spec = deployment_data.get('spec', {})
            
            # Check replica status
            desired_replicas = spec.get('replicas', 0)
            ready_replicas = status.get('readyReplicas', 0)
            available_replicas = status.get('availableReplicas', 0)
            
            if ready_replicas < desired_replicas:
                diagnosis['issues'].append(f'Only {ready_replicas}/{desired_replicas} replicas ready')
                diagnosis['recommendations'].extend([
                    'Check pod status and logs',
                    'Verify resource availability',
                    'Review deployment configuration'
                ])
            
            # Check deployment conditions
            conditions = status.get('conditions', [])
            for condition in conditions:
                if condition['status'] == 'False':
                    diagnosis['issues'].append(f"Deployment condition {condition['type']}: {condition.get('message', '')}")
        
        except subprocess.CalledProcessError as e:
            diagnosis['issues'].append(f'Deployment not found or kubectl error: {e.stderr}')
        except json.JSONDecodeError:
            diagnosis['issues'].append('Failed to parse deployment information')
        
        return diagnosis

class InfrastructureTroubleshooting:
    """
    General infrastructure troubleshooting
    """
    
    def __init__(self):
        pass
    
    def check_network_connectivity(self, targets: List[str]) -> Dict:
        """Check network connectivity to multiple targets"""
        connectivity_results = {}
        
        for target in targets:
            try:
                # Simple ping test
                result = subprocess.run(['ping', '-c', '3', target], 
                                      capture_output=True, text=True, timeout=10)
                
                connectivity_results[target] = {
                    'reachable': result.returncode == 0,
                    'response_time': self.extract_ping_time(result.stdout) if result.returncode == 0 else None,
                    'output': result.stdout if result.returncode == 0 else result.stderr
                }
            
            except subprocess.TimeoutExpired:
                connectivity_results[target] = {
                    'reachable': False,
                    'error': 'Ping timeout'
                }
            except Exception as e:
                connectivity_results[target] = {
                    'reachable': False,
                    'error': str(e)
                }
        
        return connectivity_results
    
    def extract_ping_time(self, ping_output: str) -> float:
        """Extract average ping time from ping output"""
        try:
            lines = ping_output.split('\n')
            for line in lines:
                if 'avg' in line and 'ms' in line:
                    # Parse format like: "round-trip min/avg/max/stddev = 1.234/2.345/3.456/0.789 ms"
                    parts = line.split('=')[1].strip().split('/')
                    return float(parts[1])  # avg time
            return 0.0
        except:
            return 0.0
    
    def check_ssl_certificate(self, hostname: str, port: int = 443) -> Dict:
        """Check SSL certificate validity"""
        try:
            import ssl
            import socket
            from datetime import datetime
            
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse certificate dates
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    current_time = datetime.utcnow()
                    
                    days_until_expiry = (not_after - current_time).days
                    
                    return {
                        'valid': True,
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'not_before': not_before.isoformat(),
                        'not_after': not_after.isoformat(),
                        'days_until_expiry': days_until_expiry,
                        'expired': current_time > not_after,
                        'warning': days_until_expiry < 30
                    }
        
        except socket.timeout:
            return {'valid': False, 'error': 'Connection timeout'}
        except ssl.SSLError as e:
            return {'valid': False, 'error': f'SSL error: {str(e)}'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def analyze_system_resources(self) -> Dict:
        """Analyze system resource usage"""
        try:
            import psutil
            
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory information
            memory = psutil.virtual_memory()
            
            # Disk information
            disk_usage = psutil.disk_usage('/')
            
            # Network information
            network_io = psutil.net_io_counters()
            
            analysis = {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'core_count': cpu_count,
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'usage_percent': round((disk_usage.used / disk_usage.total) * 100, 2)
                },
                'network': {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_received': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_received': network_io.packets_recv
                }
            }
            
            # Add warnings for high resource usage
            warnings = []
            if cpu_percent > 80:
                warnings.append('High CPU usage detected')
            if memory.percent > 85:
                warnings.append('High memory usage detected')
            if disk_usage.used / disk_usage.total > 0.9:
                warnings.append('Low disk space available')
            
            analysis['warnings'] = warnings
            
            return analysis
        
        except ImportError:
            return {'error': 'psutil module not available'}
        except Exception as e:
            return {'error': f'System resource analysis failed: {str(e)}'}
```

---

## Monitoring and Alerting

### 1. System Monitoring Setup

```python
# troubleshooting/monitoring_setup.py
import logging
import time
import json
from typing import Dict, List, Callable
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class Alert:
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    timestamp: float
    source: str
    metrics: Dict = None
    resolved: bool = False
    resolution_time: float = None

class MonitoringSystem:
    """
    Comprehensive monitoring and alerting system
    """
    
    def __init__(self):
        self.active_alerts = {}
        self.alert_handlers = []
        self.metric_collectors = {}
        self.thresholds = self.load_default_thresholds()
        self.logger = self.setup_logging()
    
    def setup_logging(self) -> logging.Logger:
        """Setup monitoring system logging"""
        logger = logging.getLogger('monitoring_system')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('/var/log/hdfc-card-system/monitoring.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def register_metric_collector(self, name: str, collector_func: Callable) -> None:
        """Register a metric collection function"""
        self.metric_collectors[name] = collector_func
        self.logger.info(f"Registered metric collector: {name}")
    
    def register_alert_handler(self, handler_func: Callable) -> None:
        """Register an alert handling function"""
        self.alert_handlers.append(handler_func)
        self.logger.info("Registered alert handler")
    
    def collect_metrics(self) -> Dict:
        """Collect all registered metrics"""
        metrics = {}
        
        for name, collector in self.metric_collectors.items():
            try:
                metric_value = collector()
                metrics[name] = {
                    'value': metric_value,
                    'timestamp': time.time(),
                    'collector': name
                }
            except Exception as e:
                self.logger.error(f"Error collecting metric {name}: {str(e)}")
                metrics[name] = {
                    'error': str(e),
                    'timestamp': time.time(),
                    'collector': name
                }
        
        return metrics
    
    def evaluate_thresholds(self, metrics: Dict) -> List[Alert]:
        """Evaluate metrics against thresholds and generate alerts"""
        new_alerts = []
        
        for metric_name, metric_data in metrics.items():
            if 'error' in metric_data:
                continue
            
            metric_value = metric_data['value']
            thresholds = self.thresholds.get(metric_name)
            
            if not thresholds:
                continue
            
            # Check each threshold level
            alert_triggered = None
            
            if metric_value >= thresholds.get('critical', float('inf')):
                alert_triggered = AlertSeverity.CRITICAL
            elif metric_value >= thresholds.get('high', float('inf')):
                alert_triggered = AlertSeverity.HIGH
            elif metric_value >= thresholds.get('medium', float('inf')):
                alert_triggered = AlertSeverity.MEDIUM
            elif metric_value >= thresholds.get('low', float('inf')):
                alert_triggered = AlertSeverity.LOW
            
            if alert_triggered:
                alert = Alert(
                    alert_id=f"{metric_name}_{int(time.time())}",
                    title=f"{metric_name.replace('_', ' ').title()} Alert",
                    description=f"{metric_name} value {metric_value} exceeds {alert_triggered.value} threshold",
                    severity=alert_triggered,
                    timestamp=time.time(),
                    source=metric_name,
                    metrics={metric_name: metric_data}
                )
                
                new_alerts.append(alert)
                self.active_alerts[alert.alert_id] = alert
        
        return new_alerts
    
    def process_alerts(self, alerts: List[Alert]) -> None:
        """Process and handle alerts"""
        for alert in alerts:
            self.logger.warning(f"Alert triggered: {alert.title} - {alert.description}")
            
            # Send to all registered handlers
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    self.logger.error(f"Alert handler error: {str(e)}")
    
    def resolve_alert(self, alert_id: str, resolution_notes: str = None) -> bool:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = time.time()
            
            self.logger.info(f"Alert resolved: {alert_id} - {resolution_notes}")
            return True
        
        return False
    
    def get_active_alerts(self, severity_filter: AlertSeverity = None) -> List[Alert]:
        """Get list of active alerts, optionally filtered by severity"""
        alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]
        
        if severity_filter:
            alerts = [alert for alert in alerts if alert.severity == severity_filter]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def load_default_thresholds(self) -> Dict:
        """Load default monitoring thresholds"""
        return {
            'cpu_usage_percent': {
                'medium': 70,
                'high': 85,
                'critical': 95
            },
            'memory_usage_percent': {
                'medium': 75,
                'high': 85,
                'critical': 95
            },
            'disk_usage_percent': {
                'medium': 80,
                'high': 90,
                'critical': 95
            },
            'response_time_ms': {
                'medium': 1000,
                'high': 2000,
                'critical': 5000
            },
            'error_rate_percent': {
                'low': 1,
                'medium': 2,
                'high': 5,
                'critical': 10
            },
            'database_connections': {
                'medium': 80,
                'high': 90,
                'critical': 95
            },
            'queue_size': {
                'medium': 100,
                'high': 500,
                'critical': 1000
            }
        }

class HealthCheckSystem:
    """
    System health check implementation
    """
    
    def __init__(self):
        self.health_checks = {}
        self.last_check_results = {}
    
    def register_health_check(self, name: str, check_func: Callable, timeout: int = 30) -> None:
        """Register a health check function"""
        self.health_checks[name] = {
            'function': check_func,
            'timeout': timeout
        }
    
    def run_health_checks(self) -> Dict:
        """Run all registered health checks"""
        results = {
            'overall_status': 'healthy',
            'timestamp': time.time(),
            'checks': {}
        }
        
        failed_checks = 0
        
        for name, check_config in self.health_checks.items():
            try:
                start_time = time.time()
                
                # Run health check with timeout
                check_result = self.run_with_timeout(
                    check_config['function'], 
                    check_config['timeout']
                )
                
                duration = time.time() - start_time
                
                results['checks'][name] = {
                    'status': 'pass' if check_result.get('healthy', False) else 'fail',
                    'duration_seconds': round(duration, 3),
                    'details': check_result,
                    'timestamp': time.time()
                }
                
                if not check_result.get('healthy', False):
                    failed_checks += 1
                
            except Exception as e:
                results['checks'][name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
                failed_checks += 1
        
        # Determine overall status
        total_checks = len(self.health_checks)
        if failed_checks == 0:
            results['overall_status'] = 'healthy'
        elif failed_checks / total_checks < 0.5:
            results['overall_status'] = 'degraded'
        else:
            results['overall_status'] = 'unhealthy'
        
        self.last_check_results = results
        return results
    
    def run_with_timeout(self, func: Callable, timeout: int) -> Dict:
        """Run function with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Health check timeout")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            result = func()
            signal.alarm(0)
            return result
        finally:
            signal.signal(signal.SIGALRM, old_handler)
    
    def get_health_summary(self) -> Dict:
        """Get health check summary"""
        if not self.last_check_results:
            return {'status': 'no_checks_run'}
        
        checks = self.last_check_results.get('checks', {})
        
        summary = {
            'overall_status': self.last_check_results['overall_status'],
            'total_checks': len(checks),
            'passed_checks': len([c for c in checks.values() if c['status'] == 'pass']),
            'failed_checks': len([c for c in checks.values() if c['status'] == 'fail']),
            'error_checks': len([c for c in checks.values() if c['status'] == 'error']),
            'last_check_time': self.last_check_results['timestamp']
        }
        
        return summary

# Example health check implementations
def database_health_check() -> Dict:
    """Example database health check"""
    try:
        # Replace with actual database connection test
        import cx_Oracle
        
        # Test connection
        connection = cx_Oracle.connect("hdfc_card_system/password@localhost:1521/XE")
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return {
            'healthy': True,
            'details': 'Database connection successful'
        }
    
    except Exception as e:
        return {
            'healthy': False,
            'details': f'Database connection failed: {str(e)}'
        }

def redis_health_check() -> Dict:
    """Example Redis health check"""
    try:
        import redis
        
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        
        return {
            'healthy': True,
            'details': 'Redis connection successful'
        }
    
    except Exception as e:
        return {
            'healthy': False,
            'details': f'Redis connection failed: {str(e)}'
        }

def external_service_health_check() -> Dict:
    """Example external service health check"""
    try:
        import requests
        
        response = requests.get('https://api.example.com/health', timeout=10)
        
        if response.status_code == 200:
            return {
                'healthy': True,
                'details': f'External service responding (status: {response.status_code})'
            }
        else:
            return {
                'healthy': False,
                'details': f'External service returned status: {response.status_code}'
            }
    
    except Exception as e:
        return {
            'healthy': False,
            'details': f'External service check failed: {str(e)}'
        }
```

### 2. Alerting Configuration

```python
# troubleshooting/alerting_config.py
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List

class AlertHandler:
    """
    Base class for alert handlers
    """
    
    def handle_alert(self, alert: Alert) -> bool:
        """Handle an alert - to be implemented by subclasses"""
        raise NotImplementedError

class EmailAlertHandler(AlertHandler):
    """
    Email alert handler
    """
    
    def __init__(self, smtp_config: Dict):
        self.smtp_config = smtp_config
    
    def handle_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(self.smtp_config['to_emails'])
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = self.format_alert_email(alert)
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config.get('use_tls'):
                    server.starttls()
                
                if self.smtp_config.get('username'):
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"Email alert failed: {str(e)}")
            return False
    
    def format_alert_email(self, alert: Alert) -> str:
        """Format alert as HTML email"""
        severity_colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#17a2b8',
            'info': '#6c757d'
        }
        
        color = severity_colors.get(alert.severity.value, '#6c757d')
        
        html_template = f"""
        <html>
        <body>
            <h2 style="color: {color};">{alert.title}</h2>
            
            <table border="1" cellpadding="5" cellspacing="0">
                <tr>
                    <td><strong>Severity:</strong></td>
                    <td style="color: {color}; font-weight: bold;">{alert.severity.value.upper()}</td>
                </tr>
                <tr>
                    <td><strong>Source:</strong></td>
                    <td>{alert.source}</td>
                </tr>
                <tr>
                    <td><strong>Time:</strong></td>
                    <td>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}</td>
                </tr>
                <tr>
                    <td><strong>Description:</strong></td>
                    <td>{alert.description}</td>
                </tr>
            </table>
            
            {self.format_metrics_table(alert.metrics) if alert.metrics else ''}
            
            <p>
                <strong>Action Required:</strong><br>
                Please investigate this alert and take appropriate action based on your incident response procedures.
            </p>
        </body>
        </html>
        """
        
        return html_template
    
    def format_metrics_table(self, metrics: Dict) -> str:
        """Format metrics as HTML table"""
        if not metrics:
            return ""
        
        table_html = "<h3>Related Metrics:</h3><table border='1' cellpadding='5' cellspacing='0'>"
        table_html += "<tr><th>Metric</th><th>Value</th><th>Timestamp</th></tr>"
        
        for metric_name, metric_data in metrics.items():
            timestamp_str = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(metric_data.get('timestamp', time.time()))
            )
            
            table_html += f"""
            <tr>
                <td>{metric_name}</td>
                <td>{metric_data.get('value', 'N/A')}</td>
                <td>{timestamp_str}</td>
            </tr>
            """
        
        table_html += "</table>"
        return table_html

class SlackAlertHandler(AlertHandler):
    """
    Slack alert handler
    """
    
    def __init__(self, webhook_url: str, channel: str = None):
        self.webhook_url = webhook_url
        self.channel = channel
    
    def handle_alert(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        try:
            color_map = {
                'critical': 'danger',
                'high': 'warning',
                'medium': 'warning',
                'low': 'good',
                'info': '#36a64f'
            }
            
            color = color_map.get(alert.severity.value, 'warning')
            
            payload = {
                'channel': self.channel,
                'username': 'HDFC Monitoring',
                'icon_emoji': ':warning:',
                'attachments': [{
                    'color': color,
                    'title': alert.title,
                    'text': alert.description,
                    'fields': [
                        {
                            'title': 'Severity',
                            'value': alert.severity.value.upper(),
                            'short': True
                        },
                        {
                            'title': 'Source',
                            'value': alert.source,
                            'short': True
                        },
                        {
                            'title': 'Time',
                            'value': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp)),
                            'short': False
                        }
                    ],
                    'footer': 'HDFC Card System Monitoring',
                    'ts': int(alert.timestamp)
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        
        except Exception as e:
            print(f"Slack alert failed: {str(e)}")
            return False

class PagerDutyAlertHandler(AlertHandler):
    """
    PagerDuty alert handler for critical alerts
    """
    
    def __init__(self, integration_key: str):
        self.integration_key = integration_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"
    
    def handle_alert(self, alert: Alert) -> bool:
        """Send critical alerts to PagerDuty"""
        # Only send critical and high severity alerts to PagerDuty
        if alert.severity not in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            return True
        
        try:
            payload = {
                'routing_key': self.integration_key,
                'event_action': 'trigger',
                'dedup_key': alert.alert_id,
                'payload': {
                    'summary': alert.title,
                    'source': alert.source,
                    'severity': alert.severity.value,
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(alert.timestamp)),
                    'custom_details': {
                        'description': alert.description,
                        'metrics': alert.metrics
                    }
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 202
        
        except Exception as e:
            print(f"PagerDuty alert failed: {str(e)}")
            return False

class LogAlertHandler(AlertHandler):
    """
    Log file alert handler
    """
    
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
    
    def handle_alert(self, alert: Alert) -> bool:
        """Log alert to file"""
        try:
            alert_entry = {
                'timestamp': alert.timestamp,
                'alert_id': alert.alert_id,
                'title': alert.title,
                'description': alert.description,
                'severity': alert.severity.value,
                'source': alert.source,
                'metrics': alert.metrics
            }
            
            with open(self.log_file_path, 'a') as f:
                f.write(json.dumps(alert_entry) + '\n')
            
            return True
        
        except Exception as e:
            print(f"Log alert failed: {str(e)}")
            return False

# Example monitoring setup
def setup_monitoring_system():
    """Setup monitoring system with all components"""
    monitoring = MonitoringSystem()
    health_checker = HealthCheckSystem()
    
    # Register metric collectors
    monitoring.register_metric_collector('cpu_usage_percent', collect_cpu_usage)
    monitoring.register_metric_collector('memory_usage_percent', collect_memory_usage)
    monitoring.register_metric_collector('disk_usage_percent', collect_disk_usage)
    monitoring.register_metric_collector('response_time_ms', collect_response_time)
    monitoring.register_metric_collector('error_rate_percent', collect_error_rate)
    
    # Register health checks
    health_checker.register_health_check('database', database_health_check)
    health_checker.register_health_check('redis', redis_health_check)
    health_checker.register_health_check('external_api', external_service_health_check)
    
    # Setup alert handlers
    email_config = {
        'host': 'smtp.gmail.com',
        'port': 587,
        'use_tls': True,
        'username': 'alerts@hdfc.com',
        'password': 'app_password',
        'from_email': 'alerts@hdfc.com',
        'to_emails': ['devops@hdfc.com', 'sre@hdfc.com']
    }
    
    email_handler = EmailAlertHandler(email_config)
    slack_handler = SlackAlertHandler('https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK')
    pagerduty_handler = PagerDutyAlertHandler('your-pagerduty-integration-key')
    log_handler = LogAlertHandler('/var/log/hdfc-card-system/alerts.log')
    
    monitoring.register_alert_handler(email_handler.handle_alert)
    monitoring.register_alert_handler(slack_handler.handle_alert)
    monitoring.register_alert_handler(pagerduty_handler.handle_alert)
    monitoring.register_alert_handler(log_handler.handle_alert)
    
    return monitoring, health_checker

# Metric collection functions (examples)
def collect_cpu_usage() -> float:
    """Collect CPU usage percentage"""
    import psutil
    return psutil.cpu_percent(interval=1)

def collect_memory_usage() -> float:
    """Collect memory usage percentage"""
    import psutil
    return psutil.virtual_memory().percent

def collect_disk_usage() -> float:
    """Collect disk usage percentage"""
    import psutil
    return (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100

def collect_response_time() -> float:
    """Collect average response time"""
    # This would integrate with your application metrics
    # For example, from Django or application performance monitoring
    return 250.0  # milliseconds

def collect_error_rate() -> float:
    """Collect error rate percentage"""
    # This would integrate with your application error tracking
    # For example, from logs or error monitoring service
    return 0.5  # percentage
```

---

## Log Analysis and Debugging

### 1. Centralized Logging Configuration

```python
# troubleshooting/logging_config.py
import logging
import logging.handlers
import json
import traceback
from typing import Dict, Any
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for logs
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': record.process,
            'thread_id': record.thread
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        
        return json.dumps(log_entry)

class LoggingConfiguration:
    """
    Centralized logging configuration
    """
    
    @staticmethod
    def setup_application_logging():
        """Setup application logging configuration"""
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Application log handler
        app_handler = logging.handlers.RotatingFileHandler(
            '/var/log/hdfc-card-system/application.log',
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(StructuredFormatter())
        
        # Error log handler
        error_handler = logging.handlers.RotatingFileHandler(
            '/var/log/hdfc-card-system/error.log',
            maxBytes=50*1024*1024,   # 50MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        
        # Security log handler
        security_handler = logging.handlers.RotatingFileHandler(
            '/var/log/hdfc-card-system/security.log',
            maxBytes=50*1024*1024,   # 50MB
            backupCount=10
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(StructuredFormatter())
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to root logger
        root_logger.addHandler(app_handler)
        root_logger.addHandler(error_handler)
        
        # Setup specific loggers
        LoggingConfiguration.setup_security_logger(security_handler)
        LoggingConfiguration.setup_performance_logger()
        LoggingConfiguration.setup_audit_logger()
        
        # Add console handler in development
        import os
        if os.getenv('DJANGO_SETTINGS_MODULE', '').endswith('development'):
            root_logger.addHandler(console_handler)
    
    @staticmethod
    def setup_security_logger(security_handler):
        """Setup security-specific logging"""
        security_logger = logging.getLogger('security')
        security_logger.setLevel(logging.WARNING)
        security_logger.addHandler(security_handler)
        security_logger.propagate = False
    
    @staticmethod
    def setup_performance_logger():
        """Setup performance logging"""
        perf_handler = logging.handlers.RotatingFileHandler(
            '/var/log/hdfc-card-system/performance.log',
            maxBytes=50*1024*1024,   # 50MB
            backupCount=5
        )
        perf_handler.setFormatter(StructuredFormatter())
        
        perf_logger = logging.getLogger('performance')
        perf_logger.setLevel(logging.INFO)
        perf_logger.addHandler(perf_handler)
        perf_logger.propagate = False
    
    @staticmethod
    def setup_audit_logger():
        """Setup audit logging"""
        audit_handler = logging.handlers.RotatingFileHandler(
            '/var/log/hdfc-card-system/audit.log',
            maxBytes=100*1024*1024,  # 100MB
            backupCount=20  # Keep more audit logs
        )
        audit_handler.setFormatter(StructuredFormatter())
        
        audit_logger = logging.getLogger('audit')
        audit_logger.setLevel(logging.INFO)
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False

class LogAnalyzer:
    """
    Log analysis and debugging utilities
    """
    
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
    
    def analyze_error_patterns(self, time_window_hours: int = 24) -> Dict:
        """Analyze error patterns in logs"""
        import re
        from collections import Counter, defaultdict
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        error_patterns = Counter()
        error_timeline = defaultdict(int)
        exception_types = Counter()
        
        try:
            with open(self.log_file_path, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Parse timestamp
                        log_time = datetime.fromisoformat(log_entry['timestamp'])
                        
                        # Skip logs outside time window
                        if log_time < cutoff_time:
                            continue
                        
                        # Analyze error level logs
                        if log_entry.get('level') in ['ERROR', 'CRITICAL']:
                            message = log_entry.get('message', '')
                            
                            # Count error patterns
                            error_patterns[message] += 1
                            
                            # Timeline analysis (hourly buckets)
                            hour_bucket = log_time.replace(minute=0, second=0, microsecond=0)
                            error_timeline[hour_bucket] += 1
                            
                            # Exception type analysis
                            if 'exception' in log_entry:
                                exc_type = log_entry['exception'].get('type', 'Unknown')
                                exception_types[exc_type] += 1
                    
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        
        except FileNotFoundError:
            return {'error': f'Log file not found: {self.log_file_path}'}
        
        return {
            'time_window_hours': time_window_hours,
            'total_errors': sum(error_patterns.values()),
            'unique_error_patterns': len(error_patterns),
            'top_error_patterns': error_patterns.most_common(10),
            'error_timeline': dict(error_timeline),
            'exception_types': dict(exception_types.most_common(10))
        }
    
    def find_request_trace(self, request_id: str) -> List[Dict]:
        """Find all log entries for a specific request"""
        trace_entries = []
        
        try:
            with open(self.log_file_path, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        if log_entry.get('request_id') == request_id:
                            trace_entries.append(log_entry)
                    
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        except FileNotFoundError:
            return []
        
        # Sort by timestamp
        trace_entries.sort(key=lambda x: x.get('timestamp', ''))
        
        return trace_entries
    
    def analyze_performance_logs(self, endpoint: str = None) -> Dict:
        """Analyze performance logs for slow requests"""
        performance_data = {
            'total_requests': 0,
            'slow_requests': [],
            'average_response_time': 0,
            'percentiles': {},
            'endpoint_stats': defaultdict(list)
        }
        
        response_times = []
        
        try:
            with open('/var/log/hdfc-card-system/performance.log', 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        if endpoint and log_entry.get('endpoint') != endpoint:
                            continue
                        
                        response_time = log_entry.get('response_time_ms', 0)
                        request_endpoint = log_entry.get('endpoint', 'unknown')
                        
                        performance_data['total_requests'] += 1
                        response_times.append(response_time)
                        performance_data['endpoint_stats'][request_endpoint].append(response_time)
                        
                        # Flag slow requests (>2 seconds)
                        if response_time > 2000:
                            performance_data['slow_requests'].append({
                                'timestamp': log_entry.get('timestamp'),
                                'endpoint': request_endpoint,
                                'response_time_ms': response_time,
                                'request_id': log_entry.get('request_id')
                            })
                    
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        except FileNotFoundError:
            return {'error': 'Performance log file not found'}
        
        if response_times:
            import statistics
            
            performance_data['average_response_time'] = statistics.mean(response_times)
            performance_data['percentiles'] = {
                'p50': statistics.median(response_times),
                'p90': statistics.quantiles(response_times, n=10)[8] if len(response_times) >= 10 else 0,
                'p95': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0,
                'p99': statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else 0
            }
        
        return performance_data
    
    def search_logs(self, search_term: str, level: str = None, limit: int = 100) -> List[Dict]:
        """Search logs for specific terms"""
        matching_entries = []
        
        try:
            with open(self.log_file_path, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Level filter
                        if level and log_entry.get('level') != level:
                            continue
                        
                        # Search in message and other fields
                        searchable_text = ' '.join([
                            log_entry.get('message', ''),
                            log_entry.get('module', ''),
                            log_entry.get('function', ''),
                            str(log_entry.get('user_id', '')),
                            str(log_entry.get('request_id', ''))
                        ]).lower()
                        
                        if search_term.lower() in searchable_text:
                            matching_entries.append(log_entry)
                            
                            if len(matching_entries) >= limit:
                                break
                    
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        except FileNotFoundError:
            return []
        
        return matching_entries

class DebuggingTools:
    """
    Advanced debugging utilities
    """
    
    @staticmethod
    def create_debug_session(user_id: str = None, session_id: str = None) -> str:
        """Create a debug session with enhanced logging"""
        import uuid
        
        debug_session_id = str(uuid.uuid4())
        
        # Create session-specific logger
        debug_logger = logging.getLogger(f'debug_session_{debug_session_id}')
        debug_handler = logging.FileHandler(
            f'/var/log/hdfc-card-system/debug_session_{debug_session_id}.log'
        )
        debug_handler.setFormatter(StructuredFormatter())
        debug_logger.addHandler(debug_handler)
        debug_logger.setLevel(logging.DEBUG)
        
        # Log session start
        debug_logger.info(
            'Debug session started',
            extra={
                'debug_session_id': debug_session_id,
                'user_id': user_id,
                'session_id': session_id,
                'event_type': 'debug_session_start'
            }
        )
        
        return debug_session_id
    
    @staticmethod
    def log_debug_info(debug_session_id: str, context: str, data: Dict):
        """Log debug information for a session"""
        debug_logger = logging.getLogger(f'debug_session_{debug_session_id}')
        
        debug_logger.debug(
            f'Debug info: {context}',
            extra={
                'debug_session_id': debug_session_id,
                'context': context,
                'debug_data': data,
                'event_type': 'debug_info'
            }
        )
    
    @staticmethod
    def analyze_request_flow(request_id: str) -> Dict:
        """Analyze complete request flow from logs"""
        log_analyzer = LogAnalyzer('/var/log/hdfc-card-system/application.log')
        trace_entries = log_analyzer.find_request_trace(request_id)
        
        if not trace_entries:
            return {'error': f'No log entries found for request_id: {request_id}'}
        
        flow_analysis = {
            'request_id': request_id,
            'start_time': trace_entries[0].get('timestamp'),
            'end_time': trace_entries[-1].get('timestamp'),
            'total_entries': len(trace_entries),
            'error_count': len([e for e in trace_entries if e.get('level') in ['ERROR', 'CRITICAL']]),
            'warning_count': len([e for e in trace_entries if e.get('level') == 'WARNING']),
            'modules_involved': list(set(e.get('module', 'unknown') for e in trace_entries)),
            'functions_called': list(set(e.get('function', 'unknown') for e in trace_entries)),
            'timeline': []
        }
        
        # Create timeline
        for entry in trace_entries:
            flow_analysis['timeline'].append({
                'timestamp': entry.get('timestamp'),
                'level': entry.get('level'),
                'module': entry.get('module'),
                'function': entry.get('function'),
                'message': entry.get('message'),
                'line': entry.get('line')
            })
        
        return flow_analysis
    
    @staticmethod
    def generate_debug_report(issue_description: str) -> Dict:
        """Generate comprehensive debug report"""
        from datetime import datetime, timedelta
        
        report_time = datetime.now()
        
        # Collect various debugging information
        app_log_analyzer = LogAnalyzer('/var/log/hdfc-card-system/application.log')
        error_log_analyzer = LogAnalyzer('/var/log/hdfc-card-system/error.log')
        
        report = {
            'report_generated': report_time.isoformat(),
            'issue_description': issue_description,
            'system_info': DebuggingTools.collect_system_info(),
            'recent_errors': error_log_analyzer.analyze_error_patterns(time_window_hours=1),
            'performance_summary': app_log_analyzer.analyze_performance_logs(),
            'recommendations': []
        }
        
        # Generate recommendations based on findings
        if report['recent_errors'].get('total_errors', 0) > 10:
            report['recommendations'].append('High error rate detected - investigate error patterns')
        
        if report['performance_summary'].get('average_response_time', 0) > 1000:
            report['recommendations'].append('Slow response times detected - review performance bottlenecks')
        
        return report
    
    @staticmethod
    def collect_system_info() -> Dict:
        """Collect current system information"""
        try:
            import psutil
            import platform
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'disk_usage_percent': round(psutil.disk_usage('/').used / psutil.disk_usage('/').total * 100, 2),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                'network_connections': len(psutil.net_connections()),
                'process_count': len(psutil.pids())
            }
        
        except ImportError:
            return {'error': 'psutil module not available for system info collection'}

# Example usage setup
def setup_logging_and_debugging():
    """Setup comprehensive logging and debugging"""
    
    # Configure logging
    LoggingConfiguration.setup_application_logging()
    
    # Create logger instances for different components
    app_logger = logging.getLogger('application')
    security_logger = logging.getLogger('security')
    performance_logger = logging.getLogger('performance')
    audit_logger = logging.getLogger('audit')
    
    # Example usage
    app_logger.info('Application logging configured successfully')
    
    return {
        'app_logger': app_logger,
        'security_logger': security_logger,
        'performance_logger': performance_logger,
        'audit_logger': audit_logger
    }
```

This comprehensive Troubleshooting Guide provides systematic approaches to identifying, analyzing, and resolving issues in the HDFC Card Limit System. The guide covers common problems, database issues, performance analysis, external service integration, authentication/authorization, deployment and infrastructure, monitoring and alerting, and log analysis with automated diagnostic tools and recommendation systems.