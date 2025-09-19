"""
Oracle Database connection and utility service.

Provides connection pooling, error handling, and
performance monitoring for Oracle SQL database operations.
"""

import cx_Oracle
import logging
from typing import Optional, Dict, Any, List, Tuple
from django.conf import settings
from django.core.cache import cache
import time
from contextlib import contextmanager
from threading import Lock
import threading

logger = logging.getLogger(__name__)


class OracleConnectionService:
    """
    Service for Oracle database connections with pooling and monitoring.
    
    Handles connection lifecycle, performance monitoring,
    and health checks with proper error handling.
    """
    
    _pool = None
    _pool_lock = Lock()
    _initialized = False
    _connection_stats = {
        'total_connections': 0,
        'active_connections': 0,
        'failed_connections': 0,
        'successful_queries': 0,
        'failed_queries': 0,
        'total_query_time': 0.0,
        'last_health_check': None
    }
    
    @classmethod
    def initialize(cls):
        """Initialize Oracle connection pool."""
        if cls._initialized:
            return
        
        with cls._pool_lock:
            if cls._initialized:
                return
            
            try:
                # Get Oracle configuration from settings
                oracle_config = getattr(settings, 'ORACLE_CONFIG', {})
                
                # Default configuration
                default_config = {
                    'user': 'card_limit_user',
                    'password': 'secure_password',
                    'dsn': 'localhost:1521/XEPDB1',
                    'min_connections': 2,
                    'max_connections': 10,
                    'increment': 1,
                    'encoding': 'UTF-8',
                    'nencoding': 'UTF-8',
                    'threaded': True
                }
                
                # Merge with provided config
                config = {**default_config, **oracle_config}
                
                # Initialize Oracle client if needed
                try:
                    cx_Oracle.init_oracle_client()
                except Exception as init_error:
                    logger.info(f"Oracle client already initialized: {init_error}")
                
                # Create connection pool
                cls._pool = cx_Oracle.SessionPool(
                    user=config['user'],
                    password=config['password'],
                    dsn=config['dsn'],
                    min=config['min_connections'],
                    max=config['max_connections'],
                    increment=config['increment'],
                    encoding=config['encoding'],
                    nencoding=config['nencoding'],
                    threaded=config['threaded']
                )
                
                cls._initialized = True
                logger.info("Oracle connection pool initialized successfully")
                
                # Perform initial health check
                cls.health_check()
                
            except Exception as e:
                logger.error(f"Oracle connection pool initialization failed: {str(e)}")
                raise
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Get database connection from pool with automatic cleanup.
        
        Yields:
            Oracle database connection
        """
        if not cls._initialized:
            cls.initialize()
        
        connection = None
        start_time = time.time()
        
        try:
            if cls._pool is None:
                raise Exception("Oracle connection pool not initialized")
            
            # Acquire connection from pool
            connection = cls._pool.acquire()
            cls._connection_stats['total_connections'] += 1
            cls._connection_stats['active_connections'] += 1
            
            logger.debug("Oracle connection acquired from pool")
            yield connection
            
        except cx_Oracle.DatabaseError as e:
            cls._connection_stats['failed_connections'] += 1
            logger.error(f"Oracle database error: {str(e)}")
            raise
        except Exception as e:
            cls._connection_stats['failed_connections'] += 1
            logger.error(f"Oracle connection error: {str(e)}")
            raise
        finally:
            # Release connection back to pool
            if connection:
                try:
                    cls._pool.release(connection)
                    cls._connection_stats['active_connections'] -= 1
                    logger.debug("Oracle connection released to pool")
                except Exception as e:
                    logger.error(f"Error releasing Oracle connection: {str(e)}")
            
            # Update timing stats
            execution_time = time.time() - start_time
            cls._connection_stats['total_query_time'] += execution_time
    
    @classmethod
    def execute_query(cls, query: str, parameters: Dict[str, Any] = None,
                     fetch_all: bool = True) -> Dict[str, Any]:
        """
        Execute SQL query with parameters.
        
        Args:
            query: SQL query string
            parameters: Query parameters
            fetch_all: Whether to fetch all results or just one
            
        Returns:
            Dictionary with query results and metadata
        """
        start_time = time.time()
        
        try:
            with cls.get_connection() as connection:
                cursor = connection.cursor()
                
                try:
                    # Execute query
                    if parameters:
                        cursor.execute(query, parameters)
                    else:
                        cursor.execute(query)
                    
                    # Fetch results for SELECT queries
                    if query.strip().upper().startswith('SELECT'):
                        if fetch_all:
                            rows = cursor.fetchall()
                        else:
                            rows = cursor.fetchone()
                        
                        # Get column names
                        columns = [desc[0] for desc in cursor.description]
                        
                        # Convert rows to list of dictionaries
                        if fetch_all and rows:
                            results = [dict(zip(columns, row)) for row in rows]
                        elif not fetch_all and rows:
                            results = dict(zip(columns, rows))
                        else:
                            results = [] if fetch_all else None
                        
                        cls._connection_stats['successful_queries'] += 1
                        execution_time = time.time() - start_time
                        
                        return {
                            'success': True,
                            'data': results,
                            'row_count': len(results) if fetch_all and results else (1 if results else 0),
                            'columns': columns,
                            'execution_time': execution_time
                        }
                    else:
                        # For non-SELECT queries (INSERT, UPDATE, DELETE)
                        rows_affected = cursor.rowcount
                        connection.commit()
                        
                        cls._connection_stats['successful_queries'] += 1
                        execution_time = time.time() - start_time
                        
                        return {
                            'success': True,
                            'rows_affected': rows_affected,
                            'execution_time': execution_time
                        }
                        
                finally:
                    cursor.close()
                    
        except cx_Oracle.DatabaseError as e:
            cls._connection_stats['failed_queries'] += 1
            error_obj, = e.args
            logger.error(f"Oracle database error: {error_obj.message}")
            return {
                'success': False,
                'error': error_obj.message,
                'error_code': error_obj.code,
                'error_type': 'DATABASE_ERROR'
            }
        except Exception as e:
            cls._connection_stats['failed_queries'] += 1
            logger.error(f"Oracle query execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'EXECUTION_ERROR'
            }
    
    @classmethod
    def execute_procedure(cls, procedure_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute stored procedure.
        
        Args:
            procedure_name: Name of the stored procedure
            parameters: Procedure parameters
            
        Returns:
            Dictionary with procedure execution results
        """
        start_time = time.time()
        
        try:
            with cls.get_connection() as connection:
                cursor = connection.cursor()
                
                try:
                    # Build parameter list
                    if parameters:
                        param_values = list(parameters.values())
                        cursor.callproc(procedure_name, param_values)
                    else:
                        cursor.callproc(procedure_name)
                    
                    connection.commit()
                    
                    cls._connection_stats['successful_queries'] += 1
                    execution_time = time.time() - start_time
                    
                    return {
                        'success': True,
                        'procedure': procedure_name,
                        'execution_time': execution_time
                    }
                    
                finally:
                    cursor.close()
                    
        except cx_Oracle.DatabaseError as e:
            cls._connection_stats['failed_queries'] += 1
            error_obj, = e.args
            logger.error(f"Oracle procedure error: {error_obj.message}")
            return {
                'success': False,
                'error': error_obj.message,
                'error_code': error_obj.code,
                'error_type': 'PROCEDURE_ERROR'
            }
        except Exception as e:
            cls._connection_stats['failed_queries'] += 1
            logger.error(f"Oracle procedure execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'EXECUTION_ERROR'
            }
    
    @classmethod
    def execute_batch(cls, query: str, parameters_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute batch operations for better performance.
        
        Args:
            query: SQL query string
            parameters_list: List of parameter dictionaries
            
        Returns:
            Dictionary with batch execution results
        """
        start_time = time.time()
        
        try:
            with cls.get_connection() as connection:
                cursor = connection.cursor()
                
                try:
                    # Prepare batch parameters
                    batch_params = []
                    for params in parameters_list:
                        batch_params.append(list(params.values()))
                    
                    # Execute batch
                    cursor.executemany(query, batch_params)
                    rows_affected = cursor.rowcount
                    connection.commit()
                    
                    cls._connection_stats['successful_queries'] += 1
                    execution_time = time.time() - start_time
                    
                    return {
                        'success': True,
                        'batch_size': len(parameters_list),
                        'rows_affected': rows_affected,
                        'execution_time': execution_time
                    }
                    
                finally:
                    cursor.close()
                    
        except cx_Oracle.DatabaseError as e:
            cls._connection_stats['failed_queries'] += 1
            error_obj, = e.args
            logger.error(f"Oracle batch error: {error_obj.message}")
            return {
                'success': False,
                'error': error_obj.message,
                'error_code': error_obj.code,
                'error_type': 'BATCH_ERROR'
            }
        except Exception as e:
            cls._connection_stats['failed_queries'] += 1
            logger.error(f"Oracle batch execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'EXECUTION_ERROR'
            }
    
    @classmethod
    def health_check(cls) -> Dict[str, Any]:
        """
        Perform database health check.
        
        Returns:
            Dictionary with health status and metrics
        """
        try:
            start_time = time.time()
            
            # Simple query to test connection
            result = cls.execute_query("SELECT 1 FROM dual", fetch_all=False)
            
            if result['success']:
                response_time = time.time() - start_time
                cls._connection_stats['last_health_check'] = time.time()
                
                # Cache health status
                health_data = {
                    'status': 'healthy',
                    'response_time': response_time,
                    'pool_busy': cls._pool.busy if cls._pool else 0,
                    'pool_opened': cls._pool.opened if cls._pool else 0,
                    'pool_max': cls._pool.max if cls._pool else 0,
                    'timestamp': cls._connection_stats['last_health_check']
                }
                
                cache.set('oracle_health_status', health_data, timeout=60)
                
                return {
                    'success': True,
                    'health': health_data
                }
            else:
                return {
                    'success': False,
                    'status': 'unhealthy',
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"Oracle health check failed: {str(e)}")
            return {
                'success': False,
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @classmethod
    def get_connection_stats(cls) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Dictionary with connection statistics
        """
        try:
            stats = cls._connection_stats.copy()
            
            if cls._pool:
                stats['pool_busy'] = cls._pool.busy
                stats['pool_opened'] = cls._pool.opened
                stats['pool_max'] = cls._pool.max
                stats['pool_min'] = cls._pool.min
                stats['pool_increment'] = cls._pool.increment
            
            # Calculate averages
            if stats['successful_queries'] > 0:
                stats['avg_query_time'] = stats['total_query_time'] / stats['successful_queries']
            else:
                stats['avg_query_time'] = 0.0
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting Oracle connection stats: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def close_pool(cls):
        """Close the connection pool."""
        try:
            if cls._pool:
                cls._pool.close()
                cls._pool = None
                cls._initialized = False
                logger.info("Oracle connection pool closed")
                
        except Exception as e:
            logger.error(f"Error closing Oracle connection pool: {str(e)}")
    
    @classmethod
    def test_connection(cls) -> Dict[str, Any]:
        """
        Test database connection and return detailed information.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            # Test basic connectivity
            result = cls.execute_query("SELECT SYSDATE, USER, SYS_CONTEXT('USERENV','SERVER_HOST') as server FROM dual", fetch_all=False)
            
            if result['success']:
                data = result['data']
                
                # Get additional database information
                version_result = cls.execute_query("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1", fetch_all=False)
                
                return {
                    'success': True,
                    'connection_test': 'passed',
                    'current_time': data.get('SYSDATE'),
                    'current_user': data.get('USER'),
                    'server_host': data.get('SERVER'),
                    'database_version': version_result['data'].get('BANNER') if version_result['success'] else 'Unknown',
                    'response_time': result['execution_time']
                }
            else:
                return {
                    'success': False,
                    'connection_test': 'failed',
                    'error': result.get('error', 'Connection test failed')
                }
                
        except Exception as e:
            logger.error(f"Oracle connection test failed: {str(e)}")
            return {
                'success': False,
                'connection_test': 'failed',
                'error': str(e)
            }


# Utility functions for common database operations
def get_table_info(table_name: str) -> Dict[str, Any]:
    """
    Get table structure information.
    
    Args:
        table_name: Name of the table
        
    Returns:
        Dictionary with table information
    """
    query = """
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        DATA_LENGTH,
        DATA_PRECISION,
        DATA_SCALE,
        NULLABLE,
        DATA_DEFAULT
    FROM USER_TAB_COLUMNS 
    WHERE TABLE_NAME = UPPER(:table_name)
    ORDER BY COLUMN_ID
    """
    
    return OracleConnectionService.execute_query(
        query, 
        {'table_name': table_name}
    )


def get_sequence_info(sequence_name: str) -> Dict[str, Any]:
    """
    Get sequence information.
    
    Args:
        sequence_name: Name of the sequence
        
    Returns:
        Dictionary with sequence information
    """
    query = """
    SELECT 
        SEQUENCE_NAME,
        MIN_VALUE,
        MAX_VALUE,
        INCREMENT_BY,
        CYCLE_FLAG,
        ORDER_FLAG,
        CACHE_SIZE,
        LAST_NUMBER
    FROM USER_SEQUENCES 
    WHERE SEQUENCE_NAME = UPPER(:sequence_name)
    """
    
    return OracleConnectionService.execute_query(
        query, 
        {'sequence_name': sequence_name},
        fetch_all=False
    )


# Initialize Oracle connection on module load
try:
    OracleConnectionService.initialize()
except Exception as e:
    logger.error(f"Oracle connection initialization failed on import: {str(e)}")
    # Don't raise exception on import to allow application to start