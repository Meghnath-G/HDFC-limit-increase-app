# API Error Codes Reference
# HDFC Card Limit Increase System

## Overview

This document provides a comprehensive reference for all error codes, their meanings, causes, and resolution steps for the HDFC Card Limit Increase System API.

## Error Response Format

All API error responses follow a standardized format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "description": "Detailed error description",
    "field": "specific_field_name",
    "action": "Recommended action for resolution",
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123def456",
    "documentation_url": "https://docs.hdfc.com/errors/ERROR_CODE"
  },
  "meta": {
    "version": "1.0",
    "environment": "production"
  }
}
```

---

## Authentication Errors (AUTH_XXX)

### AUTH_001 - Invalid Token
**Message:** Invalid authentication token  
**HTTP Status:** 401 Unauthorized  
**Causes:**
- Malformed JWT token
- Token signature verification failed
- Token payload is corrupted

**Resolution:**
- Ensure token is properly formatted
- Check token generation process
- Log in again to get a new token

**Example:**
```json
{
  "success": false,
  "error": {
    "code": "AUTH_001",
    "message": "Invalid authentication token",
    "description": "The provided JWT token is malformed or has an invalid signature",
    "action": "Please log in again to get a new authentication token"
  }
}
```

### AUTH_002 - Expired Token
**Message:** Authentication token has expired  
**HTTP Status:** 401 Unauthorized  
**Causes:**
- Token has exceeded its validity period
- System clock drift
- Token not refreshed in time

**Resolution:**
- Use refresh token to get new access token
- Implement automatic token refresh
- Check system time synchronization

### AUTH_003 - Revoked Token
**Message:** Authentication token has been revoked  
**HTTP Status:** 401 Unauthorized  
**Causes:**
- User logged out
- Security-triggered revocation
- Admin action

**Resolution:**
- Log in again
- Contact support if unexpected
- Check account status

### AUTH_101 - MFA Required
**Message:** Multi-factor authentication required  
**HTTP Status:** 403 Forbidden  
**Causes:**
- High-security operation attempted
- New device login
- Suspicious activity detected

**Resolution:**
- Complete MFA verification
- Use available OTP methods
- Contact support if unable to receive OTP

### AUTH_102 - Invalid OTP
**Message:** Invalid OTP code provided  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Incorrect OTP entered
- Typo in OTP input
- Wrong OTP method used

**Resolution:**
- Double-check OTP code
- Ensure correct OTP method
- Request new OTP if needed

### AUTH_103 - OTP Expired
**Message:** OTP has expired  
**HTTP Status:** 400 Bad Request  
**Causes:**
- OTP validity period exceeded
- Delayed OTP delivery
- Time synchronization issues

**Resolution:**
- Request new OTP
- Check OTP delivery method
- Verify system time

### AUTH_104 - Max OTP Attempts
**Message:** Maximum OTP attempts exceeded  
**HTTP Status:** 429 Too Many Requests  
**Causes:**
- Multiple failed OTP attempts
- Brute force prevention
- Security protection triggered

**Resolution:**
- Wait for cooldown period
- Request new OTP after waiting
- Contact support if persistent

### AUTH_201 - Account Locked
**Message:** Account is temporarily locked  
**HTTP Status:** 403 Forbidden  
**Causes:**
- Multiple failed login attempts
- Suspicious activity detected
- Security policy triggered

**Resolution:**
- Wait for automatic unlock
- Contact customer support
- Verify account security

### AUTH_202 - Account Suspended
**Message:** Account is suspended  
**HTTP Status:** 403 Forbidden  
**Causes:**
- Administrative action
- Policy violation
- Security concern

**Resolution:**
- Contact customer support
- Provide required documentation
- Follow reactivation process

### AUTH_203 - Invalid Credentials
**Message:** Invalid login credentials  
**HTTP Status:** 401 Unauthorized  
**Causes:**
- Wrong email/password combination
- Account not found
- Typo in credentials

**Resolution:**
- Verify credentials
- Use password reset if needed
- Check account registration

### AUTH_301 - Suspicious Activity
**Message:** Suspicious activity detected  
**HTTP Status:** 403 Forbidden  
**Causes:**
- Unusual login pattern
- Multiple device access
- Geographic anomaly

**Resolution:**
- Verify identity through MFA
- Contact support
- Review account activity

### AUTH_302 - IP Blocked
**Message:** Access blocked from this location  
**HTTP Status:** 403 Forbidden  
**Causes:**
- IP address blacklisted
- Geographic restriction
- VPN/proxy detection

**Resolution:**
- Use different network
- Contact support
- Verify location

### AUTH_303 - Rate Limit Exceeded
**Message:** Too many authentication requests  
**HTTP Status:** 429 Too Many Requests  
**Causes:**
- Excessive login attempts
- API rate limit reached
- Automated requests

**Resolution:**
- Wait before retrying
- Implement exponential backoff
- Check request frequency

---

## Customer Management Errors (CUST_XXX)

### CUST_001 - Customer Not Found
**Message:** Customer account not found  
**HTTP Status:** 404 Not Found  
**Causes:**
- Invalid customer ID
- Account deleted
- Database inconsistency

**Resolution:**
- Verify customer ID
- Check account status
- Contact support

### CUST_002 - Duplicate Email
**Message:** Email address already registered  
**HTTP Status:** 409 Conflict  
**Causes:**
- Email already in use
- Previous registration exists
- Account merger needed

**Resolution:**
- Use different email
- Log in to existing account
- Contact support for merger

### CUST_003 - Invalid Phone Number
**Message:** Invalid phone number format  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Incorrect phone format
- Invalid country code
- Non-numeric characters

**Resolution:**
- Use correct phone format
- Include country code
- Remove special characters

### CUST_004 - Phone Already Verified
**Message:** Phone number already verified  
**HTTP Status:** 409 Conflict  
**Causes:**
- Phone already associated
- Previous verification exists
- Duplicate verification attempt

**Resolution:**
- Use different phone number
- Skip verification if already done
- Contact support

### CUST_005 - KYC Incomplete
**Message:** KYC verification incomplete  
**HTTP Status:** 403 Forbidden  
**Causes:**
- Missing KYC documents
- Verification pending
- Documents rejected

**Resolution:**
- Complete KYC process
- Submit required documents
- Check verification status

### CUST_006 - Profile Update Failed
**Message:** Failed to update customer profile  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Invalid field values
- Missing required fields
- Validation errors

**Resolution:**
- Check field requirements
- Provide valid data
- Review validation errors

---

## Limit Request Errors (LIMIT_XXX)

### LIMIT_001 - Insufficient Credit Score
**Message:** Credit score insufficient for limit increase  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Low credit score
- Recent credit issues
- Insufficient credit history

**Resolution:**
- Improve credit score
- Wait for score improvement
- Provide additional documentation

### LIMIT_002 - Recent Request Exists
**Message:** Recent limit increase request already exists  
**HTTP Status:** 409 Conflict  
**Causes:**
- Active request pending
- Recent request completed
- Cooldown period active

**Resolution:**
- Wait for current request completion
- Check request status
- Wait for cooldown period

### LIMIT_003 - Maximum Limit Reached
**Message:** Maximum credit limit already reached  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Card at maximum limit
- Policy restrictions
- Risk assessment

**Resolution:**
- Check current limit
- Review eligibility criteria
- Contact support

### LIMIT_004 - Insufficient Income
**Message:** Declared income insufficient for requested limit  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Low income relative to request
- Income verification failed
- Policy requirements

**Resolution:**
- Provide income proof
- Request lower limit
- Update income information

### LIMIT_005 - Request Not Found
**Message:** Limit increase request not found  
**HTTP Status:** 404 Not Found  
**Causes:**
- Invalid request ID
- Request deleted
- Access permissions

**Resolution:**
- Verify request ID
- Check request history
- Ensure proper access

### LIMIT_006 - Request Cannot Be Cancelled
**Message:** Request cannot be cancelled in current status  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Request already processed
- Final status reached
- System processing

**Resolution:**
- Check request status
- Wait for completion
- Contact support

### LIMIT_007 - Documents Required
**Message:** Additional documents required  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Incomplete documentation
- Verification requirements
- Policy compliance

**Resolution:**
- Submit required documents
- Check document requirements
- Follow submission guidelines

---

## OTP Service Errors (OTP_XXX)

### OTP_001 - Delivery Failed
**Message:** OTP delivery failed  
**HTTP Status:** 502 Bad Gateway  
**Causes:**
- SMS/Email service unavailable
- Invalid recipient
- Network issues

**Resolution:**
- Try different delivery method
- Check contact information
- Retry after delay

### OTP_002 - Generation Failed
**Message:** OTP generation failed  
**HTTP Status:** 500 Internal Server Error  
**Causes:**
- System error
- Service unavailable
- Configuration issue

**Resolution:**
- Retry request
- Try alternative method
- Contact support

### OTP_003 - Invalid Purpose
**Message:** Invalid OTP purpose specified  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Unsupported OTP purpose
- Incorrect parameter
- API misuse

**Resolution:**
- Check supported purposes
- Verify API documentation
- Use correct parameters

### OTP_004 - Rate Limit Exceeded
**Message:** OTP request rate limit exceeded  
**HTTP Status:** 429 Too Many Requests  
**Causes:**
- Too many OTP requests
- Spam prevention
- Security measure

**Resolution:**
- Wait before retry
- Use different method
- Check request frequency

### OTP_005 - Service Unavailable
**Message:** OTP service temporarily unavailable  
**HTTP Status:** 503 Service Unavailable  
**Causes:**
- Service maintenance
- System overload
- Provider issues

**Resolution:**
- Retry later
- Try alternative method
- Check service status

---

## System Errors (SYS_XXX)

### SYS_001 - Internal Server Error
**Message:** Internal server error occurred  
**HTTP Status:** 500 Internal Server Error  
**Causes:**
- Unhandled exception
- System malfunction
- Code error

**Resolution:**
- Retry request
- Contact support
- Check system status

### SYS_002 - Database Connection Failed
**Message:** Database connection failed  
**HTTP Status:** 503 Service Unavailable  
**Causes:**
- Database offline
- Connection timeout
- Network issues

**Resolution:**
- Retry request
- Check system status
- Contact support

### SYS_003 - External Service Unavailable
**Message:** External service unavailable  
**HTTP Status:** 502 Bad Gateway  
**Causes:**
- Third-party service down
- API timeout
- Network connectivity

**Resolution:**
- Retry request
- Check service status
- Try alternative flow

### SYS_004 - Configuration Error
**Message:** System configuration error  
**HTTP Status:** 500 Internal Server Error  
**Causes:**
- Invalid configuration
- Missing settings
- Environment issues

**Resolution:**
- Contact support
- Check configuration
- Verify environment

### SYS_005 - Maintenance Mode
**Message:** System under maintenance  
**HTTP Status:** 503 Service Unavailable  
**Causes:**
- Scheduled maintenance
- System updates
- Emergency maintenance

**Resolution:**
- Wait for completion
- Check maintenance schedule
- Try after maintenance window

---

## Validation Errors (VAL_XXX)

### VAL_001 - Required Field Missing
**Message:** Required field is missing  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Mandatory field not provided
- Empty required value
- Null parameter

**Resolution:**
- Provide required field
- Check API documentation
- Validate request payload

### VAL_002 - Invalid Field Format
**Message:** Invalid field format  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Wrong data type
- Invalid format
- Constraint violation

**Resolution:**
- Use correct format
- Check field requirements
- Validate input data

### VAL_003 - Field Length Exceeded
**Message:** Field length exceeded maximum limit  
**HTTP Status:** 400 Bad Request  
**Causes:**
- String too long
- Exceeded character limit
- Invalid input size

**Resolution:**
- Reduce field length
- Check maximum limits
- Trim unnecessary content

### VAL_004 - Invalid Date Format
**Message:** Invalid date format  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Wrong date format
- Invalid date value
- Timezone issues

**Resolution:**
- Use ISO 8601 format
- Provide valid date
- Check timezone settings

### VAL_005 - Invalid Enum Value
**Message:** Invalid enum value provided  
**HTTP Status:** 400 Bad Request  
**Causes:**
- Unsupported value
- Typo in enum
- Outdated API usage

**Resolution:**
- Use valid enum values
- Check documentation
- Verify API version

---

## Rate Limiting Errors (RATE_XXX)

### RATE_001 - API Rate Limit Exceeded
**Message:** API rate limit exceeded  
**HTTP Status:** 429 Too Many Requests  
**Causes:**
- Too many requests per minute
- Burst limit reached
- Sustained high traffic

**Resolution:**
- Implement exponential backoff
- Reduce request frequency
- Use caching

### RATE_002 - Daily Quota Exceeded
**Message:** Daily API quota exceeded  
**HTTP Status:** 429 Too Many Requests  
**Causes:**
- Daily limit reached
- High usage day
- Inefficient API usage

**Resolution:**
- Wait for quota reset
- Optimize API usage
- Request quota increase

### RATE_003 - Concurrent Request Limit
**Message:** Concurrent request limit exceeded  
**HTTP Status:** 429 Too Many Requests  
**Causes:**
- Too many simultaneous requests
- Parallel processing
- Load balancing issues

**Resolution:**
- Reduce concurrency
- Implement request queuing
- Use connection pooling

---

## Error Handling Best Practices

### Client-Side Error Handling

```javascript
class ApiErrorHandler {
    static handleError(error) {
        const errorCode = error.error?.code;
        
        switch (errorCode) {
            case 'AUTH_002': // Expired token
                return this.handleTokenExpiry();
            
            case 'AUTH_101': // MFA required
                return this.handleMFARequired(error);
            
            case 'RATE_001': // Rate limit
                return this.handleRateLimit(error);
            
            default:
                return this.handleGenericError(error);
        }
    }
    
    static handleTokenExpiry() {
        // Attempt token refresh
        return authService.refreshToken();
    }
    
    static handleMFARequired(error) {
        // Redirect to MFA flow
        router.push('/mfa-verification');
    }
    
    static handleRateLimit(error) {
        // Implement exponential backoff
        const retryAfter = error.error?.retry_after || 60;
        return new Promise(resolve => {
            setTimeout(resolve, retryAfter * 1000);
        });
    }
    
    static handleGenericError(error) {
        // Show user-friendly message
        notifications.error(error.error?.message || 'An error occurred');
    }
}
```

### Server-Side Error Logging

```python
import logging

class ErrorLogger:
    @staticmethod
    def log_error(error_code, request, additional_context=None):
        logger = logging.getLogger('hdfc.api.errors')
        
        log_data = {
            'error_code': error_code,
            'request_id': request.META.get('HTTP_X_REQUEST_ID'),
            'user_id': getattr(request, 'user_id', None),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'method': request.method,
            'path': request.path,
            'timestamp': datetime.now().isoformat(),
            'additional_context': additional_context
        }
        
        # Log based on severity
        if error_code.startswith(('SYS_', 'AUTH_3')):
            logger.error(f"High severity error: {error_code}", extra=log_data)
        elif error_code.startswith(('AUTH_', 'LIMIT_')):
            logger.warning(f"Business logic error: {error_code}", extra=log_data)
        else:
            logger.info(f"Validation error: {error_code}", extra=log_data)
```

---

## Error Recovery Strategies

### Automatic Recovery
- **Token Refresh**: Automatically refresh expired tokens
- **Retry Logic**: Implement exponential backoff for transient errors
- **Fallback Methods**: Use alternative methods when primary fails
- **Circuit Breaker**: Prevent cascade failures

### User-Assisted Recovery
- **Clear Instructions**: Provide actionable error messages
- **Alternative Flows**: Offer different paths to complete actions
- **Support Contact**: Easy access to customer support
- **Status Pages**: Real-time system status information

### Monitoring and Alerting
- **Error Rate Monitoring**: Track error frequency and patterns
- **Alert Thresholds**: Set up alerts for critical errors
- **Error Categorization**: Group errors by type and severity
- **Recovery Metrics**: Monitor error resolution success rates