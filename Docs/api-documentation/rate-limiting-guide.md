# API Rate Limiting Guide
# HDFC Card Limit Increase System

## Overview

This guide provides comprehensive documentation for API rate limiting policies, implementation strategies, and best practices for the HDFC Card Limit Increase System API to ensure fair usage and system stability.

## Table of Contents

1. [Rate Limiting Overview](#rate-limiting-overview)
2. [Rate Limiting Policies](#rate-limiting-policies)
3. [Rate Limiting Headers](#rate-limiting-headers)
4. [Implementation Details](#implementation-details)
5. [Client-Side Best Practices](#client-side-best-practices)
6. [Rate Limiting Strategies](#rate-limiting-strategies)
7. [Monitoring and Analytics](#monitoring-and-analytics)
8. [Error Handling](#error-handling)

---

## Rate Limiting Overview

### Purpose of Rate Limiting

Rate limiting is implemented to:
- **Prevent API Abuse**: Protect against malicious or excessive usage
- **Ensure Fair Usage**: Provide equitable access to all users
- **Maintain Performance**: Preserve system responsiveness under load
- **Protect Resources**: Prevent resource exhaustion and service degradation
- **Security Enhancement**: Mitigate brute force and DoS attacks

### Rate Limiting Scope

Rate limits are applied at multiple levels:
- **Global Limits**: System-wide rate limits
- **User Limits**: Per-customer rate limits
- **Endpoint Limits**: Specific limits for different API endpoints
- **IP Limits**: Network-based rate limiting
- **Application Limits**: Client application-specific limits

---

## Rate Limiting Policies

### General API Limits

| Limit Type | Requests | Time Window | Reset Policy |
|------------|----------|-------------|--------------|
| Burst Limit | 100 | 1 minute | Rolling window |
| Sustained Rate | 1,000 | 1 hour | Fixed window |
| Daily Quota | 10,000 | 24 hours | Daily at midnight UTC |
| Monthly Quota | 250,000 | 30 days | Monthly on 1st |

### Authentication Endpoints

| Endpoint | Requests | Time Window | Reset Policy |
|----------|----------|-------------|--------------|
| `/api/v1/auth/login/` | 5 | 5 minutes | Fixed window |
| `/api/v1/auth/register/` | 3 | 10 minutes | Fixed window |
| `/api/v1/auth/mfa/verify/` | 10 | 10 minutes | Fixed window |
| `/api/v1/auth/refresh/` | 20 | 1 hour | Rolling window |
| `/api/v1/auth/logout/` | 10 | 1 minute | Rolling window |

### Customer Management Endpoints

| Endpoint | Requests | Time Window | Reset Policy |
|----------|----------|-------------|--------------|
| `/api/v1/customers/profile/` | 50 | 1 hour | Rolling window |
| `/api/v1/customers/update/` | 10 | 1 hour | Fixed window |
| `/api/v1/customers/verify/` | 5 | 10 minutes | Fixed window |

### Limit Request Endpoints

| Endpoint | Requests | Time Window | Reset Policy |
|----------|----------|-------------|--------------|
| `/api/v1/limit-requests/create/` | 2 | 24 hours | Fixed window |
| `/api/v1/limit-requests/` | 100 | 1 hour | Rolling window |
| `/api/v1/limit-requests/{id}/` | 20 | 1 hour | Rolling window |
| `/api/v1/limit-requests/{id}/cancel/` | 5 | 1 hour | Fixed window |

### OTP Endpoints

| Endpoint | Requests | Time Window | Reset Policy |
|----------|----------|-------------|--------------|
| `/api/v1/otp/generate/` | 3 | 10 minutes | Fixed window |
| `/api/v1/otp/verify/` | 5 | 10 minutes | Fixed window |
| `/api/v1/otp/resend/` | 2 | 5 minutes | Fixed window |

### Special Endpoints

| Endpoint | Requests | Time Window | Reset Policy |
|----------|----------|-------------|--------------|
| `/api/v1/health/` | No limit | - | No restriction |
| `/api/docs/` | 100 | 1 hour | Rolling window |
| `/api/redoc/` | 100 | 1 hour | Rolling window |

---

## Rate Limiting Headers

### Standard Headers

Every API response includes rate limiting information in the headers:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642678800
X-RateLimit-Window: 3600
X-RateLimit-Retry-After: 0
```

### Header Descriptions

| Header | Description | Example |
|--------|-------------|---------|
| `X-RateLimit-Limit` | Maximum requests allowed in current window | `1000` |
| `X-RateLimit-Remaining` | Requests remaining in current window | `999` |
| `X-RateLimit-Reset` | Unix timestamp when limit resets | `1642678800` |
| `X-RateLimit-Window` | Window duration in seconds | `3600` |
| `X-RateLimit-Retry-After` | Seconds to wait before next request | `60` |

### Rate Limit Exceeded Response

When rate limit is exceeded, the API returns:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642678800
X-RateLimit-Retry-After: 300

{
  "success": false,
  "error": {
    "code": "RATE_001",
    "message": "API rate limit exceeded",
    "description": "You have exceeded the maximum number of requests allowed",
    "action": "Please wait before making additional requests",
    "retry_after": 300,
    "limit_info": {
      "limit": 1000,
      "window": 3600,
      "reset_time": "2024-01-15T11:00:00Z"
    }
  }
}
```

---

## Implementation Details

### Server-Side Rate Limiting

```python
import time
import redis
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

class RateLimiter:
    """
    Comprehensive rate limiting implementation for HDFC API
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.rate_limits = self._load_rate_limits()
    
    def check_rate_limit(
        self, 
        identifier: str, 
        endpoint: str, 
        limit_type: str = 'default'
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is within rate limits
        
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        # Get rate limit configuration
        limit_config = self._get_limit_config(endpoint, limit_type)
        
        # Create rate limit key
        key = self._create_rate_limit_key(identifier, endpoint, limit_config['window'])
        
        # Check different rate limiting strategies
        if limit_config['strategy'] == 'token_bucket':
            return self._token_bucket_check(key, limit_config)
        elif limit_config['strategy'] == 'sliding_window':
            return self._sliding_window_check(key, limit_config)
        elif limit_config['strategy'] == 'fixed_window':
            return self._fixed_window_check(key, limit_config)
        else:
            return self._simple_counter_check(key, limit_config)
    
    def _token_bucket_check(self, key: str, config: Dict) -> Tuple[bool, Dict[str, int]]:
        """
        Token bucket rate limiting algorithm
        """
        bucket_key = f"bucket:{key}"
        last_refill_key = f"refill:{key}"
        
        # Get current bucket state
        current_tokens = self.redis.get(bucket_key)
        last_refill = self.redis.get(last_refill_key)
        
        now = time.time()
        bucket_size = config['limit']
        refill_rate = config['refill_rate']  # tokens per second
        
        if current_tokens is None:
            # Initialize bucket
            current_tokens = bucket_size
            last_refill = now
        else:
            current_tokens = int(current_tokens)
            last_refill = float(last_refill)
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = now - last_refill
            tokens_to_add = int(time_elapsed * refill_rate)
            current_tokens = min(bucket_size, current_tokens + tokens_to_add)
        
        # Check if request can be served
        if current_tokens >= 1:
            # Consume token
            current_tokens -= 1
            
            # Update bucket state
            pipe = self.redis.pipeline()
            pipe.set(bucket_key, current_tokens, ex=config['window'])
            pipe.set(last_refill_key, now, ex=config['window'])
            pipe.execute()
            
            return True, {
                'limit': bucket_size,
                'remaining': current_tokens,
                'reset': int(now + (bucket_size - current_tokens) / refill_rate),
                'window': config['window'],
                'retry_after': 0
            }
        else:
            # Rate limit exceeded
            retry_after = int((1 - current_tokens) / refill_rate)
            return False, {
                'limit': bucket_size,
                'remaining': 0,
                'reset': int(now + retry_after),
                'window': config['window'],
                'retry_after': retry_after
            }
    
    def _sliding_window_check(self, key: str, config: Dict) -> Tuple[bool, Dict[str, int]]:
        """
        Sliding window rate limiting algorithm
        """
        window_key = f"sliding:{key}"
        now = time.time()
        window_size = config['window']
        limit = config['limit']
        
        # Remove old entries outside the window
        self.redis.zremrangebyscore(window_key, 0, now - window_size)
        
        # Count current requests in window
        current_count = self.redis.zcard(window_key)
        
        if current_count < limit:
            # Add current request
            self.redis.zadd(window_key, {f"req:{now}": now})
            self.redis.expire(window_key, window_size)
            
            return True, {
                'limit': limit,
                'remaining': limit - current_count - 1,
                'reset': int(now + window_size),
                'window': window_size,
                'retry_after': 0
            }
        else:
            # Get oldest request in window to calculate retry time
            oldest_requests = self.redis.zrange(window_key, 0, 0, withscores=True)
            if oldest_requests:
                oldest_time = oldest_requests[0][1]
                retry_after = int(oldest_time + window_size - now)
            else:
                retry_after = window_size
            
            return False, {
                'limit': limit,
                'remaining': 0,
                'reset': int(now + retry_after),
                'window': window_size,
                'retry_after': retry_after
            }
    
    def _fixed_window_check(self, key: str, config: Dict) -> Tuple[bool, Dict[str, int]]:
        """
        Fixed window rate limiting algorithm
        """
        window_key = f"fixed:{key}"
        now = time.time()
        window_size = config['window']
        limit = config['limit']
        
        # Calculate window start time
        window_start = int(now // window_size) * window_size
        window_key_with_time = f"{window_key}:{window_start}"
        
        # Get current count for this window
        current_count = self.redis.get(window_key_with_time)
        current_count = int(current_count) if current_count else 0
        
        if current_count < limit:
            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(window_key_with_time)
            pipe.expire(window_key_with_time, window_size)
            pipe.execute()
            
            return True, {
                'limit': limit,
                'remaining': limit - current_count - 1,
                'reset': int(window_start + window_size),
                'window': window_size,
                'retry_after': 0
            }
        else:
            retry_after = int(window_start + window_size - now)
            return False, {
                'limit': limit,
                'remaining': 0,
                'reset': int(window_start + window_size),
                'window': window_size,
                'retry_after': retry_after
            }
    
    def _get_limit_config(self, endpoint: str, limit_type: str) -> Dict:
        """
        Get rate limit configuration for endpoint
        """
        # Default configuration
        default_config = {
            'limit': 1000,
            'window': 3600,
            'strategy': 'sliding_window',
            'refill_rate': 1.0
        }
        
        # Endpoint-specific configurations
        endpoint_configs = {
            '/api/v1/auth/login/': {
                'limit': 5,
                'window': 300,
                'strategy': 'fixed_window'
            },
            '/api/v1/limit-requests/create/': {
                'limit': 2,
                'window': 86400,
                'strategy': 'fixed_window'
            },
            '/api/v1/otp/generate/': {
                'limit': 3,
                'window': 600,
                'strategy': 'token_bucket',
                'refill_rate': 0.1
            }
        }
        
        config = endpoint_configs.get(endpoint, default_config).copy()
        return config
    
    def _create_rate_limit_key(self, identifier: str, endpoint: str, window: int) -> str:
        """
        Create Redis key for rate limiting
        """
        return f"ratelimit:{identifier}:{endpoint}:{window}"
    
    def _load_rate_limits(self) -> Dict:
        """
        Load rate limit configurations
        """
        # Load from configuration file or database
        return {}


class RateLimitMiddleware:
    """
    Django middleware for rate limiting
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limiter = RateLimiter(redis.Redis(host='localhost', port=6379, db=0))
    
    def __call__(self, request):
        # Apply rate limiting
        rate_limit_result = self.apply_rate_limiting(request)
        
        if not rate_limit_result['allowed']:
            return self.rate_limit_exceeded_response(rate_limit_result)
        
        # Process request
        response = self.get_response(request)
        
        # Add rate limit headers
        self.add_rate_limit_headers(response, rate_limit_result['info'])
        
        return response
    
    def apply_rate_limiting(self, request) -> Dict:
        """
        Apply rate limiting to request
        """
        # Get identifier (user ID, IP address, API key)
        identifier = self.get_rate_limit_identifier(request)
        
        # Get endpoint
        endpoint = request.path
        
        # Check rate limits
        allowed, rate_info = self.rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint,
            limit_type='default'
        )
        
        return {
            'allowed': allowed,
            'info': rate_info,
            'identifier': identifier
        }
    
    def get_rate_limit_identifier(self, request) -> str:
        """
        Get rate limiting identifier for request
        """
        # Try user ID first (for authenticated requests)
        if hasattr(request, 'user_info') and request.user_info.get('customer_id'):
            return f"user:{request.user_info['customer_id']}"
        
        # Fall back to IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f"ip:{ip}"
    
    def add_rate_limit_headers(self, response, rate_info: Dict):
        """
        Add rate limiting headers to response
        """
        response['X-RateLimit-Limit'] = str(rate_info['limit'])
        response['X-RateLimit-Remaining'] = str(rate_info['remaining'])
        response['X-RateLimit-Reset'] = str(rate_info['reset'])
        response['X-RateLimit-Window'] = str(rate_info['window'])
        response['X-RateLimit-Retry-After'] = str(rate_info['retry_after'])
    
    def rate_limit_exceeded_response(self, rate_limit_result):
        """
        Return rate limit exceeded response
        """
        from django.http import JsonResponse
        
        response_data = {
            "success": False,
            "error": {
                "code": "RATE_001",
                "message": "API rate limit exceeded",
                "description": "You have exceeded the maximum number of requests allowed",
                "action": "Please wait before making additional requests",
                "retry_after": rate_limit_result['info']['retry_after'],
                "limit_info": {
                    "limit": rate_limit_result['info']['limit'],
                    "window": rate_limit_result['info']['window'],
                    "reset_time": datetime.fromtimestamp(rate_limit_result['info']['reset']).isoformat()
                }
            }
        }
        
        response = JsonResponse(response_data, status=429)
        self.add_rate_limit_headers(response, rate_limit_result['info'])
        
        return response
```

---

## Client-Side Best Practices

### Rate Limit Aware HTTP Client

```javascript
class RateLimitAwareHttpClient {
    constructor(baseURL, options = {}) {
        this.baseURL = baseURL;
        this.options = options;
        this.requestQueue = [];
        this.isProcessingQueue = false;
        this.rateLimitInfo = new Map();
    }
    
    async request(method, endpoint, data = null, options = {}) {
        const requestConfig = {
            method,
            endpoint,
            data,
            options: { ...this.options, ...options },
            retryCount: 0,
            maxRetries: options.maxRetries || 3
        };
        
        return this.processRequest(requestConfig);
    }
    
    async processRequest(requestConfig) {
        try {
            // Check if we need to wait due to rate limiting
            await this.checkRateLimit(requestConfig.endpoint);
            
            // Make the request
            const response = await this.makeHttpRequest(requestConfig);
            
            // Update rate limit info from response headers
            this.updateRateLimitInfo(requestConfig.endpoint, response.headers);
            
            return response.data;
            
        } catch (error) {
            if (error.status === 429) {
                // Rate limit exceeded
                return this.handleRateLimit(requestConfig, error);
            } else {
                throw error;
            }
        }
    }
    
    async handleRateLimit(requestConfig, error) {
        const retryAfter = this.getRetryAfter(error);
        
        console.log(`Rate limit exceeded. Retrying after ${retryAfter} seconds`);
        
        // Wait for retry period
        await this.sleep(retryAfter * 1000);
        
        // Retry request if within retry limit
        if (requestConfig.retryCount < requestConfig.maxRetries) {
            requestConfig.retryCount++;
            return this.processRequest(requestConfig);
        } else {
            throw new Error('Rate limit exceeded. Maximum retries reached.');
        }
    }
    
    checkRateLimit(endpoint) {
        const rateLimitData = this.rateLimitInfo.get(endpoint);
        
        if (rateLimitData && rateLimitData.remaining <= 0) {
            const now = Date.now() / 1000;
            const waitTime = rateLimitData.reset - now;
            
            if (waitTime > 0) {
                console.log(`Proactively waiting ${waitTime} seconds for rate limit reset`);
                return this.sleep(waitTime * 1000);
            }
        }
        
        return Promise.resolve();
    }
    
    updateRateLimitInfo(endpoint, headers) {
        const rateLimitData = {
            limit: parseInt(headers.get('X-RateLimit-Limit') || '0'),
            remaining: parseInt(headers.get('X-RateLimit-Remaining') || '0'),
            reset: parseInt(headers.get('X-RateLimit-Reset') || '0'),
            window: parseInt(headers.get('X-RateLimit-Window') || '0'),
            retryAfter: parseInt(headers.get('X-RateLimit-Retry-After') || '0')
        };
        
        this.rateLimitInfo.set(endpoint, rateLimitData);
    }
    
    getRetryAfter(error) {
        // Try to get retry-after from error response
        const retryAfter = error.response?.headers?.get('X-RateLimit-Retry-After') ||
                          error.response?.headers?.get('Retry-After');
        
        if (retryAfter) {
            return parseInt(retryAfter);
        }
        
        // Default exponential backoff
        return Math.pow(2, error.retryCount || 1);
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    async makeHttpRequest(requestConfig) {
        const url = `${this.baseURL}${requestConfig.endpoint}`;
        const options = {
            method: requestConfig.method,
            headers: {
                'Content-Type': 'application/json',
                ...requestConfig.options.headers
            }
        };
        
        if (requestConfig.data) {
            options.body = JSON.stringify(requestConfig.data);
        }
        
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
            error.status = response.status;
            error.response = response;
            throw error;
        }
        
        return {
            data: await response.json(),
            headers: response.headers
        };
    }
}

// Usage example
const apiClient = new RateLimitAwareHttpClient('https://api.hdfc.com');

// The client will automatically handle rate limiting
apiClient.request('POST', '/api/v1/limit-requests/create/', {
    requested_limit: 50000,
    reason: 'Salary increase'
}).then(response => {
    console.log('Request created:', response);
}).catch(error => {
    console.error('Request failed:', error);
});
```

### Exponential Backoff Implementation

```javascript
class ExponentialBackoff {
    constructor(options = {}) {
        this.baseDelay = options.baseDelay || 1000; // 1 second
        this.maxDelay = options.maxDelay || 30000;   // 30 seconds
        this.maxRetries = options.maxRetries || 5;
        this.backoffFactor = options.backoffFactor || 2;
        this.jitterFactor = options.jitterFactor || 0.1;
    }
    
    async executeWithBackoff(fn, context = null) {
        let lastError;
        
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                return await fn.call(context);
            } catch (error) {
                lastError = error;
                
                // Don't retry if it's not a retryable error
                if (!this.isRetryableError(error)) {
                    throw error;
                }
                
                // Don't wait after the last attempt
                if (attempt === this.maxRetries) {
                    break;
                }
                
                const delay = this.calculateDelay(attempt);
                console.log(`Attempt ${attempt + 1} failed. Retrying in ${delay}ms`);
                await this.sleep(delay);
            }
        }
        
        throw lastError;
    }
    
    calculateDelay(attempt) {
        // Calculate exponential delay
        let delay = this.baseDelay * Math.pow(this.backoffFactor, attempt);
        
        // Cap at maximum delay
        delay = Math.min(delay, this.maxDelay);
        
        // Add jitter to prevent thundering herd
        const jitter = delay * this.jitterFactor * Math.random();
        delay += jitter;
        
        return Math.floor(delay);
    }
    
    isRetryableError(error) {
        // Only retry on rate limiting and server errors
        return error.status === 429 || 
               error.status === 500 || 
               error.status === 502 || 
               error.status === 503 || 
               error.status === 504;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Usage
const backoff = new ExponentialBackoff({
    baseDelay: 1000,
    maxDelay: 30000,
    maxRetries: 5
});

backoff.executeWithBackoff(async () => {
    return await apiClient.request('GET', '/api/v1/limit-requests/');
}).then(response => {
    console.log('Success:', response);
}).catch(error => {
    console.error('Final failure:', error);
});
```

---

## Rate Limiting Strategies

### Strategy Comparison

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| **Fixed Window** | Simple rate limiting | Easy to implement | Burst at window boundaries |
| **Sliding Window** | Smooth rate limiting | Even distribution | Higher memory usage |
| **Token Bucket** | Burst handling | Allows burst traffic | Complex implementation |
| **Leaky Bucket** | Consistent output | Smooth output rate | May drop requests |

### Fixed Window Counter

```python
def fixed_window_rate_limit(key, limit, window_size):
    """
    Fixed window rate limiting
    """
    current_window = int(time.time()) // window_size
    window_key = f"{key}:{current_window}"
    
    current_count = redis_client.get(window_key) or 0
    current_count = int(current_count)
    
    if current_count >= limit:
        return False, {
            'reset_time': (current_window + 1) * window_size,
            'retry_after': (current_window + 1) * window_size - time.time()
        }
    
    # Increment counter
    pipe = redis_client.pipeline()
    pipe.incr(window_key)
    pipe.expire(window_key, window_size)
    pipe.execute()
    
    return True, {
        'remaining': limit - current_count - 1,
        'reset_time': (current_window + 1) * window_size
    }
```

### Sliding Window Log

```python
def sliding_window_log_rate_limit(key, limit, window_size):
    """
    Sliding window log rate limiting
    """
    now = time.time()
    window_start = now - window_size
    
    # Remove old entries
    redis_client.zremrangebyscore(key, 0, window_start)
    
    # Count current requests
    current_count = redis_client.zcard(key)
    
    if current_count >= limit:
        # Get oldest request to calculate retry time
        oldest = redis_client.zrange(key, 0, 0, withscores=True)
        if oldest:
            retry_after = oldest[0][1] + window_size - now
        else:
            retry_after = window_size
        
        return False, {'retry_after': retry_after}
    
    # Add current request
    redis_client.zadd(key, {str(uuid.uuid4()): now})
    redis_client.expire(key, window_size)
    
    return True, {'remaining': limit - current_count - 1}
```

---

## Monitoring and Analytics

### Rate Limiting Metrics

```python
class RateLimitMetrics:
    """
    Collect and analyze rate limiting metrics
    """
    
    def __init__(self, metrics_client):
        self.metrics = metrics_client
    
    def record_rate_limit_check(self, identifier, endpoint, allowed, rate_info):
        """
        Record rate limit check metrics
        """
        # Basic metrics
        self.metrics.increment('rate_limit.checks.total', tags={
            'endpoint': endpoint,
            'allowed': str(allowed).lower()
        })
        
        if not allowed:
            self.metrics.increment('rate_limit.exceeded.total', tags={
                'endpoint': endpoint
            })
        
        # Usage metrics
        usage_percentage = (rate_info['limit'] - rate_info['remaining']) / rate_info['limit'] * 100
        self.metrics.gauge('rate_limit.usage.percentage', usage_percentage, tags={
            'endpoint': endpoint
        })
        
        # Remaining capacity
        self.metrics.gauge('rate_limit.remaining', rate_info['remaining'], tags={
            'endpoint': endpoint
        })
    
    def record_rate_limit_violation(self, identifier, endpoint, violation_type):
        """
        Record rate limit violations for security monitoring
        """
        self.metrics.increment('rate_limit.violations.total', tags={
            'endpoint': endpoint,
            'violation_type': violation_type,
            'identifier_type': 'user' if identifier.startswith('user:') else 'ip'
        })
    
    def get_top_rate_limited_endpoints(self, time_range='1h'):
        """
        Get endpoints with most rate limit violations
        """
        query = f"""
        SELECT endpoint, COUNT(*) as violations
        FROM rate_limit_violations
        WHERE timestamp >= NOW() - INTERVAL '{time_range}'
        GROUP BY endpoint
        ORDER BY violations DESC
        LIMIT 10
        """
        return self.metrics.query(query)
    
    def get_rate_limit_trends(self, endpoint, time_range='24h'):
        """
        Get rate limiting trends for an endpoint
        """
        query = f"""
        SELECT 
            DATE_TRUNC('hour', timestamp) as hour,
            COUNT(*) as total_requests,
            SUM(CASE WHEN allowed = false THEN 1 ELSE 0 END) as blocked_requests
        FROM rate_limit_checks
        WHERE endpoint = '{endpoint}' 
        AND timestamp >= NOW() - INTERVAL '{time_range}'
        GROUP BY hour
        ORDER BY hour
        """
        return self.metrics.query(query)
```

### Rate Limiting Dashboard

```python
def generate_rate_limiting_dashboard():
    """
    Generate rate limiting dashboard data
    """
    dashboard_data = {
        'overview': {
            'total_requests': get_total_requests_today(),
            'blocked_requests': get_blocked_requests_today(),
            'block_rate': get_block_rate_today(),
            'top_blocked_ips': get_top_blocked_ips(),
        },
        'endpoint_metrics': get_endpoint_rate_limit_metrics(),
        'trends': {
            'hourly_blocks': get_hourly_block_trends(),
            'daily_usage': get_daily_usage_trends()
        },
        'alerts': get_rate_limit_alerts()
    }
    
    return dashboard_data
```

---

## Error Handling

### Rate Limit Error Responses

```python
class RateLimitErrorHandler:
    """
    Handle rate limit errors with appropriate responses
    """
    
    @staticmethod
    def create_rate_limit_response(rate_info, request_info=None):
        """
        Create standardized rate limit error response
        """
        retry_after = rate_info.get('retry_after', 60)
        reset_time = datetime.fromtimestamp(rate_info.get('reset', time.time() + retry_after))
        
        response_data = {
            "success": False,
            "error": {
                "code": "RATE_001",
                "message": "API rate limit exceeded",
                "description": "You have exceeded the maximum number of requests allowed for this endpoint",
                "action": f"Please wait {retry_after} seconds before making additional requests",
                "retry_after": retry_after,
                "limit_info": {
                    "limit": rate_info.get('limit'),
                    "remaining": rate_info.get('remaining', 0),
                    "window": rate_info.get('window'),
                    "reset_time": reset_time.isoformat(),
                    "endpoint": request_info.get('endpoint') if request_info else None
                },
                "helpful_tips": [
                    "Implement exponential backoff in your client",
                    "Cache responses when possible to reduce API calls",
                    "Use webhooks for real-time updates instead of polling",
                    "Batch multiple operations into single requests when available"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return response_data
    
    @staticmethod
    def get_user_friendly_message(endpoint, retry_after):
        """
        Get user-friendly rate limit message
        """
        endpoint_messages = {
            '/api/v1/auth/login/': f"Too many login attempts. Please wait {retry_after} seconds before trying again.",
            '/api/v1/limit-requests/create/': f"You can only request a limit increase once per day. Please try again in {retry_after} seconds.",
            '/api/v1/otp/generate/': f"Too many OTP requests. Please wait {retry_after} seconds before requesting another code.",
        }
        
        return endpoint_messages.get(
            endpoint, 
            f"Too many requests. Please wait {retry_after} seconds before trying again."
        )
```

### Client-Side Error Handling

```javascript
class RateLimitErrorHandler {
    static handleRateLimitError(error, context = {}) {
        const errorData = error.response?.data?.error;
        const retryAfter = errorData?.retry_after || 60;
        const endpoint = context.endpoint || 'Unknown endpoint';
        
        // Show user-friendly message
        const userMessage = this.getUserFriendlyMessage(endpoint, retryAfter);
        this.showUserNotification(userMessage, 'warning');
        
        // Log for debugging
        console.warn('Rate limit exceeded:', {
            endpoint,
            retryAfter,
            limitInfo: errorData?.limit_info,
            timestamp: new Date().toISOString()
        });
        
        // Return retry information
        return {
            canRetry: true,
            retryAfter: retryAfter * 1000, // Convert to milliseconds
            retryAt: new Date(Date.now() + retryAfter * 1000),
            userMessage
        };
    }
    
    static getUserFriendlyMessage(endpoint, retryAfter) {
        const minutes = Math.ceil(retryAfter / 60);
        
        const endpointMessages = {
            '/api/v1/auth/login/': `Too many login attempts. Please wait ${retryAfter} seconds before trying again.`,
            '/api/v1/limit-requests/create/': `You can only submit one limit increase request per day. Please try again tomorrow.`,
            '/api/v1/otp/generate/': `Please wait ${retryAfter} seconds before requesting another verification code.`
        };
        
        return endpointMessages[endpoint] || 
               `Please wait ${minutes > 1 ? `${minutes} minutes` : `${retryAfter} seconds`} before making another request.`;
    }
    
    static showUserNotification(message, type = 'info') {
        // Implementation depends on your UI framework
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}
```

This comprehensive rate limiting guide provides all the necessary information for implementing, monitoring, and managing API rate limits effectively in the HDFC Card Limit Increase System.