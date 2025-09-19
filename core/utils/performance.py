"""
Performance optimization utilities for production deployment.

This module provides caching strategies, connection pooling,
query optimization, and performance monitoring tools.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest
import psutil
import gc
from datetime import datetime, timedelta

logger = logging.getLogger('card_limit_system')

class CacheManager:
    """
    Advanced cache management with performance optimization.
    """
    
    # Cache keys
    CUSTOMER_CACHE_KEY = 'customer:{customer_id}'
    CARD_CACHE_KEY = 'card:{customer_id}'
    REQUEST_CACHE_KEY = 'request:{request_id}'
    ANALYTICS_CACHE_KEY = 'analytics:{metric_type}:{date}'
    RATE_LIMIT_CACHE_KEY = 'rate_limit:{identifier}'
    
    # Cache timeouts (in seconds)
    CACHE_TIMEOUTS = {
        'customer': 1800,      # 30 minutes
        'card': 3600,          # 1 hour
        'request': 900,        # 15 minutes
        'analytics': 86400,    # 24 hours
        'rate_limit': 3600,    # 1 hour
        'session': 3600,       # 1 hour
        'otp': 300,           # 5 minutes
        'notification': 1800,  # 30 minutes
    }
    
    @classmethod
    def get_customer(cls, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer data from cache."""
        cache_key = cls.CUSTOMER_CACHE_KEY.format(customer_id=customer_id)
        return cache.get(cache_key)
    
    @classmethod
    def set_customer(cls, customer_id: str, data: Dict[str, Any]) -> bool:
        """Set customer data in cache."""
        cache_key = cls.CUSTOMER_CACHE_KEY.format(customer_id=customer_id)
        timeout = cls.CACHE_TIMEOUTS['customer']
        return cache.set(cache_key, data, timeout)
    
    @classmethod
    def invalidate_customer(cls, customer_id: str) -> bool:
        """Invalidate customer cache."""
        cache_key = cls.CUSTOMER_CACHE_KEY.format(customer_id=customer_id)
        return cache.delete(cache_key)
    
    @classmethod
    def get_card_details(cls, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get card details from cache."""
        cache_key = cls.CARD_CACHE_KEY.format(customer_id=customer_id)
        return cache.get(cache_key)
    
    @classmethod
    def set_card_details(cls, customer_id: str, data: Dict[str, Any]) -> bool:
        """Set card details in cache."""
        cache_key = cls.CARD_CACHE_KEY.format(customer_id=customer_id)
        timeout = cls.CACHE_TIMEOUTS['card']
        return cache.set(cache_key, data, timeout)
    
    @classmethod
    def get_analytics(cls, metric_type: str, date: str) -> Optional[Dict[str, Any]]:
        """Get analytics data from cache."""
        cache_key = cls.ANALYTICS_CACHE_KEY.format(
            metric_type=metric_type, 
            date=date
        )
        return cache.get(cache_key)
    
    @classmethod
    def set_analytics(cls, metric_type: str, date: str, data: Dict[str, Any]) -> bool:
        """Set analytics data in cache."""
        cache_key = cls.ANALYTICS_CACHE_KEY.format(
            metric_type=metric_type, 
            date=date
        )
        timeout = cls.CACHE_TIMEOUTS['analytics']
        return cache.set(cache_key, data, timeout)
    
    @classmethod
    def bulk_invalidate(cls, pattern: str) -> int:
        """Bulk invalidate cache keys matching pattern."""
        # This requires Redis with django-redis
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            keys = redis_conn.keys(pattern)
            if keys:
                return redis_conn.delete(*keys)
            return 0
        except ImportError:
            logger.warning("django-redis not available for bulk cache invalidation")
            return 0


def cache_result(timeout: int = 300, key_prefix: str = 'func'):
    """
    Decorator for caching function results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            cache.set(cache_key, result, timeout)
            logger.debug(
                f"Cache miss for {cache_key}, executed in {execution_time:.3f}s"
            )
            
            return result
        return wrapper
    return decorator


class QueryOptimizer:
    """
    Database query optimization utilities.
    """
    
    @staticmethod
    def optimize_queryset(queryset: QuerySet) -> QuerySet:
        """
        Optimize Django QuerySet with common patterns.
        """
        # Use select_related for ForeignKey relationships
        if hasattr(queryset.model, '_meta'):
            foreign_keys = [
                field.name for field in queryset.model._meta.fields
                if field.get_internal_type() == 'ForeignKey'
            ]
            if foreign_keys:
                queryset = queryset.select_related(*foreign_keys)
        
        return queryset
    
    @staticmethod
    def log_slow_queries():
        """Log slow database queries."""
        if not settings.DEBUG:
            return
        
        threshold = getattr(settings, 'PERFORMANCE_CONFIG', {}).get('slow_query_threshold', 1.0)
        
        for query in connection.queries:
            if float(query['time']) > threshold:
                logger.warning(
                    f"Slow query ({query['time']}s): {query['sql'][:200]}..."
                )


class ConnectionPoolManager:
    """
    Database connection pool management.
    """
    
    @staticmethod
    def get_connection_stats() -> Dict[str, Any]:
        """Get database connection statistics."""
        stats = {
            'queries_count': len(connection.queries),
            'connection_age': getattr(connection, 'connection_age', 0),
            'is_usable': connection.is_usable(),
        }
        
        # Add Oracle-specific stats if available
        try:
            import cx_Oracle
            if hasattr(connection, 'connection') and connection.connection:
                oracle_conn = connection.connection
                stats.update({
                    'oracle_version': oracle_conn.version,
                    'encoding': oracle_conn.encoding,
                    'autocommit': oracle_conn.autocommit,
                })
        except ImportError:
            pass
        
        return stats
    
    @staticmethod
    def health_check() -> bool:
        """Perform database health check."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


class PerformanceMonitor:
    """
    System performance monitoring.
    """
    
    def __init__(self):
        self.metrics = {
            'requests_count': 0,
            'total_response_time': 0.0,
            'error_count': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
        self._lock = threading.Lock()
    
    def record_request(self, response_time: float, status_code: int):
        """Record request metrics."""
        with self._lock:
            self.metrics['requests_count'] += 1
            self.metrics['total_response_time'] += response_time
            
            if status_code >= 400:
                self.metrics['error_count'] += 1
    
    def record_cache_hit(self):
        """Record cache hit."""
        with self._lock:
            self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """Record cache miss."""
        with self._lock:
            self.metrics['cache_misses'] += 1
    
    def get_average_response_time(self) -> float:
        """Get average response time."""
        if self.metrics['requests_count'] == 0:
            return 0.0
        return self.metrics['total_response_time'] / self.metrics['requests_count']
    
    def get_error_rate(self) -> float:
        """Get error rate percentage."""
        if self.metrics['requests_count'] == 0:
            return 0.0
        return (self.metrics['error_count'] / self.metrics['requests_count']) * 100
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        total_cache_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total_cache_requests == 0:
            return 0.0
        return (self.metrics['cache_hits'] / total_cache_requests) * 100
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        with self._lock:
            self.metrics = {
                'requests_count': 0,
                'total_response_time': 0.0,
                'error_count': 0,
                'cache_hits': 0,
                'cache_misses': 0,
            }


class MemoryOptimizer:
    """
    Memory optimization utilities.
    """
    
    @staticmethod
    def cleanup_memory():
        """Perform memory cleanup."""
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Log memory usage
        memory_info = psutil.Process().memory_info()
        logger.info(f"Memory usage: RSS={memory_info.rss / 1024 / 1024:.2f}MB, "
                   f"VMS={memory_info.vms / 1024 / 1024:.2f}MB")
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent(),
        }
    
    @staticmethod
    def check_memory_threshold() -> bool:
        """Check if memory usage exceeds threshold."""
        config = getattr(settings, 'PERFORMANCE_CONFIG', {})
        threshold = config.get('memory_usage_threshold', 80)
        
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > threshold:
            logger.warning(f"Memory usage ({memory_percent}%) exceeds threshold ({threshold}%)")
            return True
        
        return False


class BatchProcessor:
    """
    Batch processing utilities for performance optimization.
    """
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
    
    def process_queryset_in_batches(self, queryset: QuerySet, 
                                  processor: Callable[[List], None]):
        """
        Process QuerySet in batches to avoid memory issues.
        
        Args:
            queryset: Django QuerySet to process
            processor: Function to process each batch
        """
        total_count = queryset.count()
        processed = 0
        
        logger.info(f"Processing {total_count} records in batches of {self.batch_size}")
        
        while processed < total_count:
            batch = list(queryset[processed:processed + self.batch_size])
            if not batch:
                break
            
            start_time = time.time()
            processor(batch)
            processing_time = time.time() - start_time
            
            processed += len(batch)
            logger.info(
                f"Processed batch {processed}/{total_count} "
                f"({len(batch)} records) in {processing_time:.2f}s"
            )
    
    def bulk_create_optimized(self, model_class, objects: List, 
                            batch_size: Optional[int] = None) -> int:
        """
        Optimized bulk create with batching.
        
        Args:
            model_class: Django model class
            objects: List of model instances
            batch_size: Optional batch size override
            
        Returns:
            Number of objects created
        """
        batch_size = batch_size or self.batch_size
        total_created = 0
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            created_objects = model_class.objects.bulk_create(
                batch, 
                ignore_conflicts=True
            )
            total_created += len(created_objects)
            
            logger.info(f"Bulk created {len(created_objects)} {model_class.__name__} objects")
        
        return total_created


# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Performance optimization decorators
def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
        finally:
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
    return wrapper


def optimize_database_queries(func: Callable) -> Callable:
    """Decorator to optimize database queries."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Reset query log
        if settings.DEBUG:
            connection.queries_log.clear()
        
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Log query statistics
        if settings.DEBUG:
            query_count = len(connection.queries)
            logger.info(
                f"{func.__name__}: {query_count} queries in {execution_time:.3f}s"
            )
            
            # Log slow queries
            QueryOptimizer.log_slow_queries()
        
        return result
    return wrapper