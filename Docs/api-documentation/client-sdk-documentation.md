# Client SDK Documentation
# HDFC Card Limit Increase System

## Overview

This document provides comprehensive SDK documentation and code samples for integrating with the HDFC Card Limit Increase System API across multiple platforms including Python, JavaScript, and Flutter.

## Table of Contents

1. [Python SDK](#python-sdk)
2. [JavaScript/Node.js SDK](#javascript-sdk)
3. [Flutter/Dart SDK](#flutter-sdk)
4. [Authentication Examples](#authentication-examples)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)

---

## Python SDK

### Installation

```bash
pip install requests firebase-admin
```

### Basic Setup

```python
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

class HDFCCardLimitAPI:
    """
    Python SDK for HDFC Card Limit Increase System API
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.auth_token = None
        self.token_expiry = None
        
        # Setup default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'HDFC-Python-SDK/1.0.0'
        })
        
        if api_key:
            self.session.headers['X-API-Key'] = api_key
            
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Add request ID for tracking
        headers = kwargs.get('headers', {})
        headers['X-Request-ID'] = f"req_{int(datetime.now().timestamp())}"
        kwargs['headers'] = headers
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                error_data = response.json()
            except:
                error_data = {'error': {'message': str(e)}}
            
            self.logger.error(f"API Error: {error_data}")
            raise APIError(error_data.get('error', {}), response.status_code)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request Error: {str(e)}")
            raise ConnectionError(f"Failed to connect to API: {str(e)}")
    
    def set_auth_token(self, token: str):
        """Set Firebase JWT token for authentication"""
        self.auth_token = token
        self.session.headers['Authorization'] = f'Bearer {token}'
        
        # Estimate token expiry (Firebase tokens typically expire in 1 hour)
        self.token_expiry = datetime.now() + timedelta(hours=1)
    
    def is_token_expired(self) -> bool:
        """Check if auth token is expired"""
        if not self.token_expiry:
            return True
        return datetime.now() >= self.token_expiry
    
    # Customer Management
    def register_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new customer"""
        return self._request('POST', '/api/v1/customers/register/', json=customer_data)
    
    def login_customer(self, email: str, password: str, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate customer and get tokens"""
        login_data = {
            'email': email,
            'password': password,
            'device_info': device_info
        }
        response = self._request('POST', '/api/v1/auth/login/', json=login_data)
        
        # Automatically set the received token
        if response.get('success') and response.get('data', {}).get('access_token'):
            self.set_auth_token(response['data']['access_token'])
        
        return response
    
    def get_customer_profile(self) -> Dict[str, Any]:
        """Get authenticated customer's profile"""
        return self._request('GET', '/api/v1/customers/profile/')
    
    def update_customer_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer profile"""
        return self._request('PUT', '/api/v1/customers/profile/', json=profile_data)
    
    # Limit Requests
    def create_limit_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a limit increase request"""
        return self._request('POST', '/api/v1/requests/', json=request_data)
    
    def get_limit_request(self, request_id: str) -> Dict[str, Any]:
        """Get specific limit request details"""
        return self._request('GET', f'/api/v1/requests/{request_id}/')
    
    def list_limit_requests(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List customer's limit requests"""
        params = filters or {}
        return self._request('GET', '/api/v1/requests/', params=params)
    
    def cancel_limit_request(self, request_id: str, reason: str, comments: str = "") -> Dict[str, Any]:
        """Cancel a limit request"""
        cancel_data = {
            'cancellation_reason': reason,
            'comments': comments
        }
        return self._request('POST', f'/api/v1/requests/{request_id}/cancel/', json=cancel_data)
    
    # OTP Management
    def generate_otp(self, purpose: str, delivery_method: str, contact_info: str, **kwargs) -> Dict[str, Any]:
        """Generate and send OTP"""
        otp_data = {
            'purpose': purpose,
            'delivery_method': delivery_method,
            'contact_info': contact_info,
            **kwargs
        }
        return self._request('POST', '/api/v1/otp/generate/', json=otp_data)
    
    def verify_otp(self, otp_id: str, otp_code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify OTP code"""
        verify_data = {
            'otp_id': otp_id,
            'otp_code': otp_code,
            'context': context
        }
        return self._request('POST', '/api/v1/otp/verify/', json=verify_data)
    
    def resend_otp(self, otp_id: str, delivery_method: str = None, reason: str = "not_received") -> Dict[str, Any]:
        """Resend OTP"""
        resend_data = {
            'otp_id': otp_id,
            'reason': reason
        }
        if delivery_method:
            resend_data['delivery_method'] = delivery_method
            
        return self._request('POST', '/api/v1/otp/resend/', json=resend_data)
    
    # Utility Methods
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return self._request('GET', '/api/v1/health/')
    
    def test_auth_token(self) -> Dict[str, Any]:
        """Test current authentication token"""
        return self._request('POST', '/api/v1/auth/test-token/')


class APIError(Exception):
    """Custom exception for API errors"""
    
    def __init__(self, error_data: Dict[str, Any], status_code: int):
        self.error_data = error_data
        self.status_code = status_code
        self.code = error_data.get('code', 'UNKNOWN_ERROR')
        self.message = error_data.get('message', 'An unknown error occurred')
        self.details = error_data.get('details', {})
        
        super().__init__(self.message)


# Usage Examples
def example_usage():
    """Example usage of the Python SDK"""
    
    # Initialize the API client
    api = HDFCCardLimitAPI('https://card-limit-api.hdfc.com')
    
    try:
        # Check API health
        health = api.health_check()
        print(f"API Status: {health['status']}")
        
        # Customer registration
        customer_data = {
            'email': 'customer@example.com',
            'phone_number': '+919876543210',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-15',
            'pan_number': 'ABCDE1234F',
            'address': {
                'street': '123 Main Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400001',
                'country': 'India'
            }
        }
        
        registration = api.register_customer(customer_data)
        print(f"Registration: {registration['message']}")
        
        # Customer login
        device_info = {
            'device_id': 'device_12345',
            'device_type': 'mobile',
            'os': 'android',
            'app_version': '1.0.0'
        }
        
        login = api.login_customer('customer@example.com', 'password123', device_info)
        print(f"Login: {login['message']}")
        
        # Create limit request
        limit_request_data = {
            'request_type': 'credit_card',
            'card_number': '1234567890123456',
            'current_limit': 100000.00,
            'requested_limit': 150000.00,
            'reason': 'Higher monthly expenses due to business growth',
            'income_details': {
                'monthly_income': 75000.00,
                'income_source': 'salary',
                'employer_name': 'Tech Corp Pvt Ltd'
            }
        }
        
        request = api.create_limit_request(limit_request_data)
        print(f"Limit Request: {request['data']['request_id']}")
        
        # Generate OTP
        otp = api.generate_otp(
            purpose='transaction_verification',
            delivery_method='sms',
            contact_info='+919876543210'
        )
        print(f"OTP ID: {otp['data']['otp_id']}")
        
        # Verify OTP (example)
        verify = api.verify_otp(
            otp['data']['otp_id'],
            '123456',  # User-entered OTP
            {'device_id': 'device_12345'}
        )
        print(f"OTP Verification: {verify['data']['verification_status']}")
        
    except APIError as e:
        print(f"API Error: {e.code} - {e.message}")
        if e.details:
            print(f"Details: {e.details}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")


if __name__ == "__main__":
    example_usage()
```

### Async Python SDK

```python
import aiohttp
import asyncio
from typing import Dict, Any, Optional

class AsyncHDFCCardLimitAPI:
    """
    Async Python SDK for HDFC Card Limit Increase System API
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.auth_token = None
        
        # Default headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'HDFC-Async-Python-SDK/1.0.0'
        }
        
        if api_key:
            self.headers['X-API-Key'] = api_key
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make async HTTP request"""
        url = f"{self.base_url}{endpoint}"
        
        # Merge headers
        headers = {**self.headers}
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise APIError(error_data.get('error', {}), response.status)
                
                return await response.json()
    
    async def login_customer(self, email: str, password: str, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Async customer login"""
        login_data = {
            'email': email,
            'password': password,
            'device_info': device_info
        }
        response = await self._request('POST', '/api/v1/auth/login/', json=login_data)
        
        if response.get('success') and response.get('data', {}).get('access_token'):
            self.auth_token = response['data']['access_token']
            self.headers['Authorization'] = f"Bearer {self.auth_token}"
        
        return response
    
    async def create_limit_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Async limit request creation"""
        return await self._request('POST', '/api/v1/requests/', json=request_data)


# Async usage example
async def async_example():
    api = AsyncHDFCCardLimitAPI('https://card-limit-api.hdfc.com')
    
    # Login
    login_result = await api.login_customer(
        'customer@example.com',
        'password123',
        {'device_id': 'async_device', 'device_type': 'web'}
    )
    
    # Create request
    request_result = await api.create_limit_request({
        'request_type': 'credit_card',
        'card_number': '1234567890123456',
        'current_limit': 100000.00,
        'requested_limit': 150000.00,
        'reason': 'Business expansion'
    })
    
    print(f"Request ID: {request_result['data']['request_id']}")

# Run async example
# asyncio.run(async_example())
```

---

## JavaScript SDK

### Installation

```bash
npm install axios firebase
```

### Basic Setup

```javascript
const axios = require('axios');

class HDFCCardLimitAPI {
    constructor(baseUrl, apiKey = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
        this.authToken = null;
        
        // Create axios instance
        this.client = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'HDFC-JS-SDK/1.0.0'
            }
        });
        
        if (apiKey) {
            this.client.defaults.headers['X-API-Key'] = apiKey;
        }
        
        // Request interceptor
        this.client.interceptors.request.use(
            (config) => {
                // Add request ID
                config.headers['X-Request-ID'] = `req_${Date.now()}`;
                
                // Add correlation ID
                config.headers['X-Correlation-ID'] = `corr_${Math.random().toString(36).substr(2, 9)}`;
                
                return config;
            },
            (error) => Promise.reject(error)
        );
        
        // Response interceptor
        this.client.interceptors.response.use(
            (response) => response.data,
            (error) => {
                const errorData = error.response?.data || {
                    error: {
                        code: 'NETWORK_ERROR',
                        message: error.message
                    }
                };
                
                throw new APIError(errorData.error, error.response?.status);
            }
        );
    }
    
    setAuthToken(token) {
        this.authToken = token;
        this.client.defaults.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Customer Management
    async registerCustomer(customerData) {
        return await this.client.post('/api/v1/customers/register/', customerData);
    }
    
    async loginCustomer(email, password, deviceInfo) {
        const loginData = {
            email,
            password,
            device_info: deviceInfo
        };
        
        const response = await this.client.post('/api/v1/auth/login/', loginData);
        
        // Auto-set token
        if (response.success && response.data.access_token) {
            this.setAuthToken(response.data.access_token);
        }
        
        return response;
    }
    
    async getCustomerProfile() {
        return await this.client.get('/api/v1/customers/profile/');
    }
    
    async updateCustomerProfile(profileData) {
        return await this.client.put('/api/v1/customers/profile/', profileData);
    }
    
    // Limit Requests
    async createLimitRequest(requestData) {
        return await this.client.post('/api/v1/requests/', requestData);
    }
    
    async getLimitRequest(requestId) {
        return await this.client.get(`/api/v1/requests/${requestId}/`);
    }
    
    async listLimitRequests(filters = {}) {
        return await this.client.get('/api/v1/requests/', { params: filters });
    }
    
    async cancelLimitRequest(requestId, reason, comments = '') {
        const cancelData = {
            cancellation_reason: reason,
            comments
        };
        return await this.client.post(`/api/v1/requests/${requestId}/cancel/`, cancelData);
    }
    
    // OTP Management
    async generateOTP(purpose, deliveryMethod, contactInfo, options = {}) {
        const otpData = {
            purpose,
            delivery_method: deliveryMethod,
            contact_info: contactInfo,
            ...options
        };
        return await this.client.post('/api/v1/otp/generate/', otpData);
    }
    
    async verifyOTP(otpId, otpCode, context) {
        const verifyData = {
            otp_id: otpId,
            otp_code: otpCode,
            context
        };
        return await this.client.post('/api/v1/otp/verify/', verifyData);
    }
    
    async resendOTP(otpId, deliveryMethod = null, reason = 'not_received') {
        const resendData = {
            otp_id: otpId,
            reason
        };
        
        if (deliveryMethod) {
            resendData.delivery_method = deliveryMethod;
        }
        
        return await this.client.post('/api/v1/otp/resend/', resendData);
    }
    
    // Utility Methods
    async healthCheck() {
        return await this.client.get('/api/v1/health/');
    }
    
    async testAuthToken() {
        return await this.client.post('/api/v1/auth/test-token/');
    }
}

class APIError extends Error {
    constructor(errorData, statusCode) {
        super(errorData.message || 'An unknown error occurred');
        
        this.errorData = errorData;
        this.statusCode = statusCode;
        this.code = errorData.code || 'UNKNOWN_ERROR';
        this.details = errorData.details || {};
        
        this.name = 'APIError';
    }
}

// Usage Example
async function exampleUsage() {
    const api = new HDFCCardLimitAPI('https://card-limit-api.hdfc.com');
    
    try {
        // Health check
        const health = await api.healthCheck();
        console.log('API Status:', health.status);
        
        // Customer registration
        const customerData = {
            email: 'customer@example.com',
            phone_number: '+919876543210',
            first_name: 'John',
            last_name: 'Doe',
            date_of_birth: '1990-01-15',
            pan_number: 'ABCDE1234F',
            address: {
                street: '123 Main Street',
                city: 'Mumbai',
                state: 'Maharashtra',
                pincode: '400001',
                country: 'India'
            }
        };
        
        const registration = await api.registerCustomer(customerData);
        console.log('Registration:', registration.message);
        
        // Customer login
        const deviceInfo = {
            device_id: 'web_device_123',
            device_type: 'web',
            os: 'chrome',
            app_version: '1.0.0'
        };
        
        const login = await api.loginCustomer('customer@example.com', 'password123', deviceInfo);
        console.log('Login:', login.message);
        
        // Create limit request
        const limitRequestData = {
            request_type: 'credit_card',
            card_number: '1234567890123456',
            current_limit: 100000.00,
            requested_limit: 150000.00,
            reason: 'Higher monthly expenses due to business growth',
            income_details: {
                monthly_income: 75000.00,
                income_source: 'salary',
                employer_name: 'Tech Corp Pvt Ltd'
            }
        };
        
        const request = await api.createLimitRequest(limitRequestData);
        console.log('Request ID:', request.data.request_id);
        
        // Generate OTP
        const otp = await api.generateOTP(
            'transaction_verification',
            'sms',
            '+919876543210'
        );
        console.log('OTP ID:', otp.data.otp_id);
        
    } catch (error) {
        if (error instanceof APIError) {
            console.error('API Error:', error.code, '-', error.message);
            if (Object.keys(error.details).length > 0) {
                console.error('Details:', error.details);
            }
        } else {
            console.error('Unexpected Error:', error.message);
        }
    }
}

// Export for use
module.exports = { HDFCCardLimitAPI, APIError };

// Run example (uncomment to test)
// exampleUsage();
```

### Browser/Frontend JavaScript

```html
<!DOCTYPE html>
<html>
<head>
    <title>HDFC Card Limit API - Frontend Example</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
</head>
<body>
    <div id="app">
        <h1>HDFC Card Limit API</h1>
        <button onclick="testAPI()">Test API</button>
        <div id="result"></div>
    </div>

    <script>
        class HDFCCardLimitAPIBrowser {
            constructor(baseUrl) {
                this.baseUrl = baseUrl.replace(/\/$/, '');
                this.authToken = null;
                
                // Configure axios defaults
                axios.defaults.headers.common['Content-Type'] = 'application/json';
                axios.defaults.headers.common['Accept'] = 'application/json';
                axios.defaults.headers.common['X-API-Client'] = 'HDFC-Browser-SDK/1.0.0';
            }
            
            setAuthToken(token) {
                this.authToken = token;
                axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            }
            
            async request(method, endpoint, data = null) {
                const config = {
                    method,
                    url: `${this.baseUrl}${endpoint}`,
                    headers: {
                        'X-Request-ID': `req_${Date.now()}`,
                        'X-Correlation-ID': `corr_${Math.random().toString(36).substr(2, 9)}`
                    }
                };
                
                if (data) {
                    config.data = data;
                }
                
                try {
                    const response = await axios(config);
                    return response.data;
                } catch (error) {
                    const errorData = error.response?.data || {
                        error: {
                            code: 'NETWORK_ERROR',
                            message: error.message
                        }
                    };
                    
                    throw new Error(`API Error: ${errorData.error.code} - ${errorData.error.message}`);
                }
            }
            
            async healthCheck() {
                return await this.request('GET', '/api/v1/health/');
            }
            
            async loginCustomer(email, password, deviceInfo) {
                const loginData = {
                    email,
                    password,
                    device_info: deviceInfo
                };
                
                const response = await this.request('POST', '/api/v1/auth/login/', loginData);
                
                if (response.success && response.data.access_token) {
                    this.setAuthToken(response.data.access_token);
                }
                
                return response;
            }
            
            async createLimitRequest(requestData) {
                return await this.request('POST', '/api/v1/requests/', requestData);
            }
        }
        
        // Example usage
        const api = new HDFCCardLimitAPIBrowser('https://card-limit-api.hdfc.com');
        
        async function testAPI() {
            const resultDiv = document.getElementById('result');
            
            try {
                // Test health check
                const health = await api.healthCheck();
                resultDiv.innerHTML = `<p>API Health: ${health.status}</p>`;
                
                // You can add more API calls here
                
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
```

---

## Flutter SDK

### pubspec.yaml

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^0.13.5
  firebase_auth: ^4.15.3
  shared_preferences: ^2.2.2
  logger: ^2.0.2
```

### Dart SDK Implementation

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:logger/logger.dart';
import 'package:shared_preferences/shared_preferences.dart';

class HDFCCardLimitAPI {
  final String baseUrl;
  final String? apiKey;
  String? authToken;
  DateTime? tokenExpiry;
  final Logger logger = Logger();
  
  HDFCCardLimitAPI({
    required this.baseUrl,
    this.apiKey,
  });
  
  /// Get default headers for API requests
  Map<String, String> get _defaultHeaders => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'HDFC-Flutter-SDK/1.0.0',
    if (apiKey != null) 'X-API-Key': apiKey!,
    if (authToken != null) 'Authorization': 'Bearer $authToken',
  };
  
  /// Make HTTP request with error handling
  Future<Map<String, dynamic>> _request(
    String method,
    String endpoint, {
    Map<String, dynamic>? body,
    Map<String, String>? queryParams,
    Map<String, String>? additionalHeaders,
  }) async {
    final uri = Uri.parse('${baseUrl.replaceAll(RegExp(r'/$'), '')}$endpoint');
    final headers = {
      ..._defaultHeaders,
      'X-Request-ID': 'req_${DateTime.now().millisecondsSinceEpoch}',
      'X-Correlation-ID': 'corr_${_generateCorrelationId()}',
      if (additionalHeaders != null) ...additionalHeaders,
    };
    
    http.Response response;
    
    try {
      switch (method.toUpperCase()) {
        case 'GET':
          final getUri = queryParams != null 
              ? uri.replace(queryParameters: queryParams)
              : uri;
          response = await http.get(getUri, headers: headers);
          break;
        case 'POST':
          response = await http.post(
            uri,
            headers: headers,
            body: body != null ? jsonEncode(body) : null,
          );
          break;
        case 'PUT':
          response = await http.put(
            uri,
            headers: headers,
            body: body != null ? jsonEncode(body) : null,
          );
          break;
        case 'DELETE':
          response = await http.delete(uri, headers: headers);
          break;
        default:
          throw ArgumentError('Unsupported HTTP method: $method');
      }
      
      final responseData = jsonDecode(response.body) as Map<String, dynamic>;
      
      if (response.statusCode >= 400) {
        final error = responseData['error'] as Map<String, dynamic>? ?? {};
        throw APIException(
          code: error['code'] as String? ?? 'UNKNOWN_ERROR',
          message: error['message'] as String? ?? 'An unknown error occurred',
          details: error['details'] as Map<String, dynamic>? ?? {},
          statusCode: response.statusCode,
        );
      }
      
      return responseData;
      
    } on SocketException catch (e) {
      logger.e('Network error: ${e.message}');
      throw NetworkException('Failed to connect to API: ${e.message}');
    } on FormatException catch (e) {
      logger.e('JSON parsing error: ${e.message}');
      throw ParseException('Failed to parse API response: ${e.message}');
    } catch (e) {
      logger.e('Unexpected error: $e');
      rethrow;
    }
  }
  
  String _generateCorrelationId() {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    return List.generate(9, (index) => 
      chars[DateTime.now().millisecondsSinceEpoch % chars.length]
    ).join();
  }
  
  /// Set authentication token
  void setAuthToken(String token) {
    authToken = token;
    tokenExpiry = DateTime.now().add(const Duration(hours: 1));
    _saveTokenToStorage(token);
  }
  
  /// Check if token is expired
  bool get isTokenExpired {
    if (tokenExpiry == null) return true;
    return DateTime.now().isAfter(tokenExpiry!);
  }
  
  /// Save token to local storage
  Future<void> _saveTokenToStorage(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('hdfc_auth_token', token);
    await prefs.setString('hdfc_token_expiry', tokenExpiry!.toIso8601String());
  }
  
  /// Load token from local storage
  Future<void> loadTokenFromStorage() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('hdfc_auth_token');
    final expiryString = prefs.getString('hdfc_token_expiry');
    
    if (token != null && expiryString != null) {
      authToken = token;
      tokenExpiry = DateTime.parse(expiryString);
      
      if (isTokenExpired) {
        await clearToken();
      }
    }
  }
  
  /// Clear stored token
  Future<void> clearToken() async {
    authToken = null;
    tokenExpiry = null;
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('hdfc_auth_token');
    await prefs.remove('hdfc_token_expiry');
  }
  
  // Customer Management
  Future<Map<String, dynamic>> registerCustomer(Map<String, dynamic> customerData) async {
    return await _request('POST', '/api/v1/customers/register/', body: customerData);
  }
  
  Future<Map<String, dynamic>> loginCustomer(
    String email,
    String password,
    Map<String, dynamic> deviceInfo,
  ) async {
    final loginData = {
      'email': email,
      'password': password,
      'device_info': deviceInfo,
    };
    
    final response = await _request('POST', '/api/v1/auth/login/', body: loginData);
    
    // Auto-set token
    if (response['success'] == true) {
      final data = response['data'] as Map<String, dynamic>;
      final accessToken = data['access_token'] as String?;
      if (accessToken != null) {
        setAuthToken(accessToken);
      }
    }
    
    return response;
  }
  
  Future<Map<String, dynamic>> getCustomerProfile() async {
    return await _request('GET', '/api/v1/customers/profile/');
  }
  
  Future<Map<String, dynamic>> updateCustomerProfile(Map<String, dynamic> profileData) async {
    return await _request('PUT', '/api/v1/customers/profile/', body: profileData);
  }
  
  // Limit Requests
  Future<Map<String, dynamic>> createLimitRequest(Map<String, dynamic> requestData) async {
    return await _request('POST', '/api/v1/requests/', body: requestData);
  }
  
  Future<Map<String, dynamic>> getLimitRequest(String requestId) async {
    return await _request('GET', '/api/v1/requests/$requestId/');
  }
  
  Future<Map<String, dynamic>> listLimitRequests([Map<String, String>? filters]) async {
    return await _request('GET', '/api/v1/requests/', queryParams: filters);
  }
  
  Future<Map<String, dynamic>> cancelLimitRequest(
    String requestId,
    String reason,
    String comments,
  ) async {
    final cancelData = {
      'cancellation_reason': reason,
      'comments': comments,
    };
    return await _request('POST', '/api/v1/requests/$requestId/cancel/', body: cancelData);
  }
  
  // OTP Management
  Future<Map<String, dynamic>> generateOTP(
    String purpose,
    String deliveryMethod,
    String contactInfo, {
    Map<String, dynamic>? context,
    Map<String, dynamic>? preferences,
  }) async {
    final otpData = {
      'purpose': purpose,
      'delivery_method': deliveryMethod,
      'contact_info': contactInfo,
      if (context != null) 'context': context,
      if (preferences != null) 'preferences': preferences,
    };
    return await _request('POST', '/api/v1/otp/generate/', body: otpData);
  }
  
  Future<Map<String, dynamic>> verifyOTP(
    String otpId,
    String otpCode,
    Map<String, dynamic> context,
  ) async {
    final verifyData = {
      'otp_id': otpId,
      'otp_code': otpCode,
      'context': context,
    };
    return await _request('POST', '/api/v1/otp/verify/', body: verifyData);
  }
  
  Future<Map<String, dynamic>> resendOTP(
    String otpId, {
    String? deliveryMethod,
    String reason = 'not_received',
  }) async {
    final resendData = {
      'otp_id': otpId,
      'reason': reason,
      if (deliveryMethod != null) 'delivery_method': deliveryMethod,
    };
    return await _request('POST', '/api/v1/otp/resend/', body: resendData);
  }
  
  // Utility Methods
  Future<Map<String, dynamic>> healthCheck() async {
    return await _request('GET', '/api/v1/health/');
  }
  
  Future<Map<String, dynamic>> testAuthToken() async {
    return await _request('POST', '/api/v1/auth/test-token/');
  }
}

// Custom Exception Classes
class APIException implements Exception {
  final String code;
  final String message;
  final Map<String, dynamic> details;
  final int statusCode;
  
  const APIException({
    required this.code,
    required this.message,
    required this.details,
    required this.statusCode,
  });
  
  @override
  String toString() => 'APIException: $code - $message';
}

class NetworkException implements Exception {
  final String message;
  
  const NetworkException(this.message);
  
  @override
  String toString() => 'NetworkException: $message';
}

class ParseException implements Exception {
  final String message;
  
  const ParseException(this.message);
  
  @override
  String toString() => 'ParseException: $message';
}

// Usage Example
class ExampleUsage {
  final HDFCCardLimitAPI api;
  
  ExampleUsage() : api = HDFCCardLimitAPI(
    baseUrl: 'https://card-limit-api.hdfc.com',
  );
  
  Future<void> demonstrateAPI() async {
    try {
      // Load any saved token
      await api.loadTokenFromStorage();
      
      // Health check
      final health = await api.healthCheck();
      print('API Status: ${health['status']}');
      
      // Customer registration
      final customerData = {
        'email': 'customer@example.com',
        'phone_number': '+919876543210',
        'first_name': 'John',
        'last_name': 'Doe',
        'date_of_birth': '1990-01-15',
        'pan_number': 'ABCDE1234F',
        'address': {
          'street': '123 Main Street',
          'city': 'Mumbai',
          'state': 'Maharashtra',
          'pincode': '400001',
          'country': 'India',
        },
      };
      
      final registration = await api.registerCustomer(customerData);
      print('Registration: ${registration['message']}');
      
      // Customer login
      final deviceInfo = {
        'device_id': 'flutter_device_123',
        'device_type': 'mobile',
        'os': 'android',
        'app_version': '1.0.0',
      };
      
      final login = await api.loginCustomer(
        'customer@example.com',
        'password123',
        deviceInfo,
      );
      print('Login: ${login['message']}');
      
      // Create limit request
      final limitRequestData = {
        'request_type': 'credit_card',
        'card_number': '1234567890123456',
        'current_limit': 100000.00,
        'requested_limit': 150000.00,
        'reason': 'Higher monthly expenses due to business growth',
        'income_details': {
          'monthly_income': 75000.00,
          'income_source': 'salary',
          'employer_name': 'Tech Corp Pvt Ltd',
        },
      };
      
      final request = await api.createLimitRequest(limitRequestData);
      final requestData = request['data'] as Map<String, dynamic>;
      print('Request ID: ${requestData['request_id']}');
      
      // Generate OTP
      final otp = await api.generateOTP(
        'transaction_verification',
        'sms',
        '+919876543210',
      );
      final otpData = otp['data'] as Map<String, dynamic>;
      print('OTP ID: ${otpData['otp_id']}');
      
    } on APIException catch (e) {
      print('API Error: ${e.code} - ${e.message}');
      if (e.details.isNotEmpty) {
        print('Details: ${e.details}');
      }
    } on NetworkException catch (e) {
      print('Network Error: ${e.message}');
    } catch (e) {
      print('Unexpected Error: $e');
    }
  }
}
```

This comprehensive SDK documentation provides developers with ready-to-use code for integrating with the HDFC Card Limit Increase System API across multiple platforms. Each SDK includes proper error handling, authentication management, and complete examples for all major API operations.