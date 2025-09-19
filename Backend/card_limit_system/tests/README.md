# Testing Documentation - HDFC Card Limit System

## Overview

This document provides comprehensive information about the testing framework and test suite for the HDFC Card Limit Increase System.

## Test Structure

### Test Organization

```
tests/
├── conftest.py                    # Test configuration and fixtures
├── factories.py                   # Test data factories
├── test_accounts_models.py        # Unit tests for account models
├── test_accounts_api.py           # API tests for account endpoints
├── test_cards_models.py           # Unit tests for card models
├── test_cards_api.py              # API tests for card endpoints
├── test_requests_models.py        # Unit tests for request models
├── test_requests_api.py           # API tests for request endpoints
├── test_notifications_models.py   # Unit tests for notification models
├── test_notifications_api.py      # API tests for notification endpoints
├── test_external_services.py      # Integration tests for external services
├── test_business_logic.py         # Business logic and workflow tests
├── test_security.py               # Security and authentication tests
├── test_performance.py            # Performance and load tests
└── README.md                      # This file
```

### Test Categories

#### 1. Unit Tests (`test_*_models.py`)
- **Purpose**: Test individual model functionality
- **Coverage**: Model validation, business logic, relationships
- **Dependencies**: Minimal external dependencies
- **Example**:
  ```python
  def test_customer_creation(self):
      customer = Customer.objects.create(**self.customer_data)
      self.assertEqual(customer.customer_id, 'CUST123456')
  ```

#### 2. API Tests (`test_*_api.py`)
- **Purpose**: Test REST API endpoints
- **Coverage**: Request/response, authentication, permissions
- **Dependencies**: Database, authentication
- **Example**:
  ```python
  def test_customer_registration(self):
      response = self.client.post(url, data, format='json')
      self.assertEqual(response.status_code, status.HTTP_201_CREATED)
  ```

#### 3. Integration Tests (`test_external_services.py`)
- **Purpose**: Test external service integrations
- **Coverage**: Firebase, Twilio, SendGrid, OneSignal
- **Dependencies**: Mocked external services
- **Example**:
  ```python
  @patch('core.firebase_service.FirebaseService.verify_token')
  def test_firebase_authentication(self, mock_verify):
      mock_verify.return_value = {'success': True}
  ```

#### 4. Business Logic Tests (`test_business_logic.py`)
- **Purpose**: Test complex business workflows
- **Coverage**: Approval workflows, risk assessment, limit updates
- **Dependencies**: Complete database models
- **Example**:
  ```python
  def test_auto_approval_criteria(self):
      result = request.evaluate_auto_approval()
      self.assertTrue(result['eligible'])
  ```

## Test Configuration

### Settings (`test_settings.py`)
- **Database**: SQLite in-memory for speed
- **Cache**: Local memory cache
- **Email**: Local memory backend
- **External Services**: Mocked configurations
- **Security**: Disabled for testing

### Fixtures (`conftest.py`)
- **Database Setup**: Automated test database creation
- **Authentication**: Mock Firebase authentication
- **External Services**: Mock service responses
- **Test Data**: Reusable test data factories

## Test Data Factories

### Factory Classes
- **CustomerFactory**: Creates customer instances
- **CardFactory**: Creates card instances
- **LimitIncreaseRequestFactory**: Creates request instances
- **OTPVerificationFactory**: Creates OTP instances

### Test Data Builder
- **create_complete_customer()**: Full customer with profile and accounts
- **create_limit_request_workflow()**: Complete request workflow
- **create_otp_verification_flow()**: OTP verification process

## Running Tests

### Prerequisites
```bash
pip install pytest pytest-django pytest-cov factory-boy
```

### Test Commands

#### Run All Tests
```bash
python run_tests.py all
```

#### Run Specific Test Categories
```bash
python run_tests.py unit           # Unit tests only
python run_tests.py api            # API tests only
python run_tests.py integration    # Integration tests only
python run_tests.py security       # Security tests only
python run_tests.py performance    # Performance tests only
```

#### Run Specific Test Files
```bash
python run_tests.py tests/test_accounts_models.py
python run_tests.py tests/test_external_services.py
```

#### Run Specific Test Methods
```bash
python run_tests.py tests/test_accounts_api.py::CustomerAPITest::test_customer_registration
```

#### Generate Coverage Report
```bash
python run_tests.py coverage
```

### Coverage Requirements
- **Minimum Coverage**: 85%
- **Target Coverage**: 90%+
- **Critical Paths**: 100% coverage required

## Test Markers

Tests are organized using pytest markers:

### Available Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.external_service` - Tests requiring external services

### Running Marked Tests
```bash
pytest -m "unit"                   # Run only unit tests
pytest -m "api and not slow"       # Run API tests excluding slow ones
pytest -m "security or performance" # Run security or performance tests
```

## Mocking Strategy

### External Services
All external services are mocked in tests:

#### Firebase Authentication
```python
@patch('core.firebase_service.FirebaseService.verify_token')
def test_with_firebase(self, mock_verify):
    mock_verify.return_value = {'success': True, 'uid': 'test_uid'}
```

#### Twilio SMS/Voice
```python
@patch('core.twilio_service.TwilioService.send_sms')
def test_with_twilio(self, mock_sms):
    mock_sms.return_value = {'success': True, 'message_sid': 'test_sid'}
```

#### SendGrid Email
```python
@patch('core.sendgrid_service.SendGridService.send_email')
def test_with_sendgrid(self, mock_email):
    mock_email.return_value = {'success': True, 'message_id': 'test_id'}
```

#### OneSignal Push Notifications
```python
@patch('core.onesignal_service.OneSignalService.send_notification')
def test_with_onesignal(self, mock_push):
    mock_push.return_value = {'success': True, 'notification_id': 'test_id'}
```

## Test Data Management

### Factory Usage
```python
# Create single instance
customer = CustomerFactory()

# Create with specific attributes
customer = CustomerFactory(email='specific@example.com')

# Create multiple instances
customers = CustomerFactory.create_batch(5)

# Create related objects
profile = CustomerProfileFactory(customer=customer)
```

### Test Data Builder Usage
```python
# Create complete customer setup
customer_data = TestDataBuilder.create_complete_customer()
customer = customer_data['customer']
profile = customer_data['profile']
card = customer_data['credit_card']

# Create workflow setup
workflow_data = TestDataBuilder.create_limit_request_workflow()
request = workflow_data['request']
workflow = workflow_data['workflow']
assessment = workflow_data['assessment']
```

## Performance Testing

### Load Testing
- **API Endpoints**: Test with concurrent requests
- **Database Operations**: Test bulk operations
- **External Services**: Test with rate limiting

### Performance Metrics
- **Response Time**: < 200ms for API endpoints
- **Throughput**: > 100 requests/second
- **Memory Usage**: < 512MB peak usage
- **Database Queries**: < 10 queries per request

## Security Testing

### Authentication Tests
- Token validation
- Permission enforcement
- Rate limiting
- Session management

### Input Validation Tests
- SQL injection prevention
- XSS prevention
- CSRF protection
- Input sanitization

### Data Security Tests
- Field encryption
- PII protection
- Audit logging
- Access control

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py all
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Quality Gates
- **All tests must pass**: 100% test success rate
- **Coverage threshold**: Minimum 85% code coverage
- **Performance tests**: All performance benchmarks must pass
- **Security tests**: All security tests must pass

## Debugging Tests

### Common Issues
1. **Test Isolation**: Ensure tests don't depend on each other
2. **Mock Configuration**: Verify mocks are properly configured
3. **Database State**: Use transactions for test isolation
4. **Async Operations**: Handle async operations properly

### Debugging Tools
```bash
# Run with verbose output
pytest -v -s

# Run with pdb debugger
pytest --pdb

# Run specific failing test
pytest tests/test_file.py::test_method -v -s
```

### Test Environment Variables
```bash
export DJANGO_SETTINGS_MODULE=card_limit_system.test_settings
export TESTING=true
export DEBUG=false
```

## Best Practices

### Test Writing Guidelines
1. **Test Naming**: Use descriptive test method names
2. **Test Structure**: Follow Arrange-Act-Assert pattern
3. **Test Data**: Use factories for test data creation
4. **Assertions**: Use specific assertion methods
5. **Documentation**: Document complex test scenarios

### Example Test Structure
```python
def test_customer_limit_increase_approval(self):
    # Arrange
    customer = CustomerFactory()
    profile = CustomerProfileFactory(customer=customer, credit_score=750)
    request = LimitIncreaseRequestFactory(customer=customer)
    
    # Act
    result = request.evaluate_auto_approval()
    
    # Assert
    self.assertTrue(result['eligible'])
    self.assertEqual(result['reason'], 'AMOUNT_BELOW_THRESHOLD')
```

### Performance Guidelines
1. **Use Transactions**: Wrap tests in database transactions
2. **Minimize Database Hits**: Use select_related and prefetch_related
3. **Mock External Services**: Don't make real external API calls
4. **Use In-Memory Database**: SQLite for speed
5. **Batch Operations**: Use bulk_create for multiple objects

## Test Reports

### Coverage Report
- **HTML Report**: `htmlcov/index.html`
- **Terminal Report**: Displays during test run
- **XML Report**: `coverage.xml` for CI/CD

### Test Results
- **JUnit XML**: For CI/CD integration
- **Console Output**: Real-time test progress
- **Failed Test Details**: Detailed failure information

## Maintenance

### Regular Tasks
1. **Update Test Data**: Keep test data realistic and current
2. **Review Coverage**: Ensure new code has adequate test coverage
3. **Performance Monitoring**: Monitor test execution time
4. **Mock Updates**: Update mocks when external APIs change

### Test Data Cleanup
```bash
# Clean up test artifacts
python run_tests.py cleanup

# Reset test database
python run_tests.py setup
```

## Troubleshooting

### Common Error Solutions

#### Import Errors
```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Database Errors
```bash
# Reset test database
python manage.py migrate --settings=card_limit_system.test_settings
```

#### Mock Errors
```python
# Ensure mocks are properly patched
@patch('full.module.path.to.function')
def test_method(self, mock_function):
    mock_function.return_value = expected_value
```

### Getting Help
- Check test logs for detailed error messages
- Use pytest's `-v` flag for verbose output
- Review factory configurations for test data issues
- Verify mock configurations match actual service interfaces

---

For more information, see the main project documentation or contact the development team.