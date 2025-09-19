"""
Security hardening middleware for production deployment.

This module implements comprehensive security measures including
SSL enforcement, security headers, rate limiting, and threat protection.
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.middleware.security import SecurityMiddleware
from django.middleware.csrf import CsrfViewMiddleware
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from datetime import datetime, timedelta
import ipaddress
import re

logger = logging.getLogger('django.security')

class ProductionSecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware for production environment.
    
    Features:
    - Advanced rate limiting
    - IP whitelist/blacklist
    - Suspicious activity detection
    - Security headers enforcement
    - Request validation and sanitization
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Security configuration
        self.rate_limits = getattr(settings, 'RATE_LIMITING', {})
        self.audit_config = getattr(settings, 'AUDIT_CONFIG', {})
        
        # IP whitelist for internal services
        self.ip_whitelist = [
            '10.0.0.0/8',      # Internal network
            '172.16.0.0/12',   # Internal network
            '192.168.0.0/16',  # Internal network
            '127.0.0.1/32',    # Localhost
        ]
        
        # IP blacklist for known threats
        self.ip_blacklist_cache_key = 'security:ip_blacklist'
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'<script.*?>.*?</script>',  # XSS attempts
            r'union\s+select',           # SQL injection
            r'drop\s+table',             # SQL injection
            r'\.\./',                    # Path traversal
            r'exec\s*\(',               # Code injection
            r'eval\s*\(',               # Code injection
            r'<iframe',                  # Iframe injection
            r'javascript:',              # JavaScript injection
            r'vbscript:',               # VBScript injection
        ]
        
        self.suspicious_regex = re.compile(
            '|'.join(self.suspicious_patterns), 
            re.IGNORECASE
        )
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process incoming request for security validation."""
        
        # Log request for audit trail
        self._log_request(request)
        
        # Check IP blacklist
        if self._is_ip_blacklisted(request):
            logger.warning(
                f"Blocked request from blacklisted IP: {self._get_client_ip(request)}"
            )
            return JsonResponse(
                {'error': 'Access denied'}, 
                status=403
            )
        
        # Rate limiting
        if self._is_rate_limited(request):
            logger.warning(
                f"Rate limit exceeded for IP: {self._get_client_ip(request)}"
            )
            return JsonResponse(
                {'error': 'Rate limit exceeded'}, 
                status=429
            )
        
        # Validate request content
        if self._has_suspicious_content(request):
            logger.error(
                f"Suspicious content detected from IP: {self._get_client_ip(request)}"
            )
            self._blacklist_ip(request, reason='suspicious_content')
            raise SuspiciousOperation("Suspicious content detected")
        
        # Validate request headers
        if self._has_suspicious_headers(request):
            logger.error(
                f"Suspicious headers detected from IP: {self._get_client_ip(request)}"
            )
            self._blacklist_ip(request, reason='suspicious_headers')
            raise SuspiciousOperation("Suspicious headers detected")
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Add security headers to response."""
        
        # Security headers
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': self._get_csp_header(),
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'X-Permitted-Cross-Domain-Policies': 'none',
            'X-Download-Options': 'noopen',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        }
        
        for header, value in security_headers.items():
            response[header] = value
        
        # Remove sensitive headers
        sensitive_headers = ['Server', 'X-Powered-By', 'X-AspNet-Version']
        for header in sensitive_headers:
            if header in response:
                del response[header]
        
        # Log response for audit trail
        self._log_response(request, response)
        
        return response
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address considering proxy headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _is_ip_blacklisted(self, request: HttpRequest) -> bool:
        """Check if IP is in blacklist."""
        client_ip = self._get_client_ip(request)
        blacklist = cache.get(self.ip_blacklist_cache_key, set())
        return client_ip in blacklist
    
    def _is_ip_whitelisted(self, request: HttpRequest) -> bool:
        """Check if IP is in whitelist."""
        client_ip = self._get_client_ip(request)
        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            for whitelist_cidr in self.ip_whitelist:
                if client_ip_obj in ipaddress.ip_network(whitelist_cidr):
                    return True
        except (ipaddress.AddressValueError, ValueError):
            return False
        return False
    
    def _blacklist_ip(self, request: HttpRequest, reason: str = '', duration: int = 3600):
        """Add IP to blacklist."""
        client_ip = self._get_client_ip(request)
        blacklist = cache.get(self.ip_blacklist_cache_key, set())
        blacklist.add(client_ip)
        cache.set(self.ip_blacklist_cache_key, blacklist, duration)
        
        logger.error(
            f"IP {client_ip} blacklisted for {duration}s. Reason: {reason}"
        )
    
    def _is_rate_limited(self, request: HttpRequest) -> bool:
        """Check if request should be rate limited."""
        client_ip = self._get_client_ip(request)
        
        # Skip rate limiting for whitelisted IPs
        if self._is_ip_whitelisted(request):
            return False
        
        # Check different rate limit types
        path = request.path.lower()
        
        # API rate limiting
        if path.startswith('/api/'):
            return self._check_rate_limit(
                f"api:{client_ip}",
                self.rate_limits.get('api_requests', {})
            )
        
        # Login rate limiting
        if 'login' in path or 'auth' in path:
            return self._check_rate_limit(
                f"login:{client_ip}",
                self.rate_limits.get('login_attempts', {})
            )
        
        # OTP rate limiting
        if 'otp' in path:
            return self._check_rate_limit(
                f"otp:{client_ip}",
                self.rate_limits.get('otp_requests', {})
            )
        
        # Limit request rate limiting
        if 'limit-request' in path:
            user_id = getattr(request.user, 'id', client_ip)
            return self._check_rate_limit(
                f"limit_request:{user_id}",
                self.rate_limits.get('limit_requests', {})
            )
        
        return False
    
    def _check_rate_limit(self, key: str, config: Dict[str, int]) -> bool:
        """Check rate limit for specific key and configuration."""
        if not config:
            return False
        
        limit = config.get('limit', 100)
        window = config.get('window', 3600)
        
        cache_key = f"rate_limit:{key}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return True
        
        # Increment counter
        cache.set(cache_key, current_count + 1, window)
        return False
    
    def _has_suspicious_content(self, request: HttpRequest) -> bool:
        """Check for suspicious content in request."""
        # Check query parameters
        query_string = request.META.get('QUERY_STRING', '')
        if self.suspicious_regex.search(query_string):
            return True
        
        # Check POST data
        if hasattr(request, 'body') and request.body:
            try:
                body_str = request.body.decode('utf-8', errors='ignore')
                if self.suspicious_regex.search(body_str):
                    return True
            except UnicodeDecodeError:
                pass
        
        # Check path
        if self.suspicious_regex.search(request.path):
            return True
        
        return False
    
    def _has_suspicious_headers(self, request: HttpRequest) -> bool:
        """Check for suspicious headers."""
        suspicious_headers = [
            'X-Forwarded-Host',
            'X-Original-URL',
            'X-Rewrite-URL',
        ]
        
        for header in suspicious_headers:
            if header in request.META:
                value = request.META[header]
                if self.suspicious_regex.search(value):
                    return True
        
        # Check User-Agent for known bad patterns
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        bad_user_agents = [
            'sqlmap',
            'nikto',
            'nessus',
            'openvas',
            'nmap',
            'masscan',
            'zap',
            'w3af',
        ]
        
        if any(bad_ua in user_agent.lower() for bad_ua in bad_user_agents):
            return True
        
        return False
    
    def _get_csp_header(self) -> str:
        """Generate Content Security Policy header."""
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://apis.google.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://api.twilio.com https://onesignal.com",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "block-all-mixed-content",
            "upgrade-insecure-requests"
        ]
        return '; '.join(csp_directives)
    
    def _log_request(self, request: HttpRequest):
        """Log request for audit trail."""
        if not self.audit_config.get('log_all_requests', False):
            return
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'ip': self._get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        }
        
        logger.info(f"Request: {json.dumps(log_data)}")
    
    def _log_response(self, request: HttpRequest, response: HttpResponse):
        """Log response for audit trail."""
        if not self.audit_config.get('log_all_requests', False):
            return
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'ip': self._get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'response_size': len(response.content) if hasattr(response, 'content') else 0,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        }
        
        logger.info(f"Response: {json.dumps(log_data)}")


class SecurityAuditMiddleware(MiddlewareMixin):
    """
    Security audit middleware for compliance and monitoring.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        self.audit_logger = logging.getLogger('django.security')
        
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Audit security-related events."""
        request._audit_start_time = time.time()
        
        # Log authentication attempts
        if 'login' in request.path.lower() or 'auth' in request.path.lower():
            self._log_auth_attempt(request)
        
        # Log sensitive operations
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            self._log_sensitive_operation(request)
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response audit information."""
        # Calculate response time
        if hasattr(request, '_audit_start_time'):
            response_time = time.time() - request._audit_start_time
            
            # Log slow responses
            threshold = getattr(settings, 'PERFORMANCE_CONFIG', {}).get('response_time_threshold', 2.0)
            if response_time > threshold:
                self.audit_logger.warning(
                    f"Slow response: {request.path} took {response_time:.2f}s"
                )
        
        # Log failed requests
        if response.status_code >= 400:
            self._log_failed_request(request, response)
        
        return response
    
    def _log_auth_attempt(self, request: HttpRequest):
        """Log authentication attempts."""
        audit_data = {
            'event_type': 'auth_attempt',
            'timestamp': datetime.now().isoformat(),
            'ip': self._get_client_ip(request),
            'path': request.path,
            'method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        self.audit_logger.info(f"Auth attempt: {json.dumps(audit_data)}")
    
    def _log_sensitive_operation(self, request: HttpRequest):
        """Log sensitive operations."""
        sensitive_paths = [
            'limit-request',
            'otp',
            'profile',
            'card',
            'account',
        ]
        
        if any(path in request.path.lower() for path in sensitive_paths):
            audit_data = {
                'event_type': 'sensitive_operation',
                'timestamp': datetime.now().isoformat(),
                'ip': self._get_client_ip(request),
                'path': request.path,
                'method': request.method,
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            }
            
            self.audit_logger.info(f"Sensitive operation: {json.dumps(audit_data)}")
    
    def _log_failed_request(self, request: HttpRequest, response: HttpResponse):
        """Log failed requests."""
        audit_data = {
            'event_type': 'failed_request',
            'timestamp': datetime.now().isoformat(),
            'ip': self._get_client_ip(request),
            'path': request.path,
            'method': request.method,
            'status_code': response.status_code,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        }
        
        self.audit_logger.error(f"Failed request: {json.dumps(audit_data)}")
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Performance monitoring middleware for production optimization.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        self.performance_logger = logging.getLogger('card_limit_system')
        
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Start performance monitoring."""
        request._performance_start_time = time.time()
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log performance metrics."""
        if hasattr(request, '_performance_start_time'):
            response_time = time.time() - request._performance_start_time
            
            # Log performance metrics
            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'path': request.path,
                'method': request.method,
                'response_time': round(response_time, 3),
                'status_code': response.status_code,
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
            }
            
            # Log slow requests
            config = getattr(settings, 'PERFORMANCE_CONFIG', {})
            threshold = config.get('response_time_threshold', 2.0)
            
            if response_time > threshold:
                self.performance_logger.warning(
                    f"Slow request: {json.dumps(performance_data)}"
                )
            else:
                self.performance_logger.info(
                    f"Request metrics: {json.dumps(performance_data)}"
                )
        
        return response