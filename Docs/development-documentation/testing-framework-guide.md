# Testing Framework Documentation

## Overview

The Card Limit Increase System employs a comprehensive testing framework designed to ensure the reliability, security, and performance of the banking application. This document provides a complete guide to understanding and using the testing infrastructure.

## Table of Contents

1. [Testing Architecture](#testing-architecture)
2. [Test Suite Components](#test-suite-components)
3. [Running Tests](#running-tests)
4. [Test Data Management](#test-data-management)
5. [Coverage and Reporting](#coverage-and-reporting)
6. [CI/CD Integration](#cicd-integration)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Testing Architecture

### Framework Stack
- **pytest**: Primary testing framework for Python
- **pytest-django**: Django-specific pytest integration
- **factory-boy**: Test data generation
- **coverage**: Code coverage measurement
- **requests-mock**: HTTP request mocking
- **freezegun**: Time-based testing utilities

### Test Categories

#### 1. Unit Tests
- **Purpose**: Test individual components in isolation
- **Location**: `tests/unit/`
- **Scope**: Models, utilities, business logic functions
- **Coverage Target**: 95%+

#### 2. Integration Tests
- **Purpose**: Test component interactions
- **Location**: `tests/integration/`
- **Scope**: External services, database operations
- **Coverage Target**: 85%+

#### 3. API Tests
- **Purpose**: Test REST API endpoints
- **Location**: `tests/api/`
- **Scope**: Authentication, permissions, data validation
- **Coverage Target**: 90%+

#### 4. Security Tests
- **Purpose**: Test security controls and vulnerabilities
- **Location**: `tests/security/`
- **Scope**: Authentication, authorization, data protection
- **Coverage Target**: 100%

#### 5. Performance Tests
- **Purpose**: Test system performance under load
- **Location**: `tests/performance/`
- **Scope**: Response times, throughput, resource usage
- **Coverage Target**: Critical paths

## Test Suite Components

### Configuration Files

#### conftest.py
```python
# Central test configuration
# - Database fixtures
# - Authentication mocking
# - External service mocking
# - Common test utilities
```

#### test_settings.py
```python
# Optimized test settings
# - In-memory database
# - Disabled external services
# - Debug configurations
# - Performance optimizations
```

#### pyproject.toml
```python
# pytest configuration
# - Test discovery
# - Coverage settings
# - Markers and plugins
# - Output formatting
```

### Factory Classes

#### TestDataBuilder
```python
# Comprehensive test data creation
builder = TestDataBuilder()
customer = builder.create_complete_customer()
workflow = builder.create_limit_request_workflow()
```

#### Model Factories
- `CustomerFactory`: Creates customer test data
- `CustomerProfileFactory`: Creates profile test data
- `CardFactory`: Creates card test data
- `LimitRequestFactory`: Creates request test data
- `NotificationFactory`: Creates notification test data

### Test Modules

#### Model Tests (test_accounts_models.py)
```python
# Tests for:
# - Model validation
# - Business logic methods
# - Relationships
# - Custom properties
```

#### API Tests (test_accounts_api.py)
```python
# Tests for:
# - Endpoint functionality
# - Authentication/authorization
# - Input validation
# - Response formatting
```

#### External Service Tests (test_external_services.py)
```python
# Tests for:
# - Firebase integration
# - Twilio SMS/voice
# - SendGrid email
# - OneSignal push notifications
```

#### Business Logic Tests (test_business_logic.py)
```python
# Tests for:
# - Approval workflows
# - Risk assessment
# - Business rules
# - Process automation
```

## Running Tests

### Basic Test Execution

#### Run All Tests
```bash
python run_tests.py
```

#### Run Specific Test Categories
```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# API tests only
python run_tests.py --api

# Security tests only
python run_tests.py --security

# Performance tests only
python run_tests.py --performance
```

#### Run Tests with Coverage
```bash
python run_tests.py --with-coverage
```

#### Run Tests in Parallel
```bash
python run_tests.py --parallel
```

### Advanced Test Options

#### Run Specific Test Files
```bash
pytest tests/unit/test_accounts_models.py -v
```

#### Run Specific Test Functions
```bash
pytest tests/unit/test_accounts_models.py::TestCustomerModel::test_customer_creation -v
```

#### Run Tests with Markers
```bash
# Run only slow tests
pytest -m slow

# Run only fast tests
pytest -m "not slow"

# Run only security tests
pytest -m security
```

#### Run Tests with Live Database
```bash
python run_tests.py --use-db
```

### Test Runner Features

#### Performance Timing
```bash
python run_tests.py --with-timing
```

#### Detailed Output
```bash
python run_tests.py --verbose
```

#### HTML Coverage Report
```bash
python run_tests.py --html-report
```

## Test Data Management

### Factory Usage

#### Creating Test Data
```python
from tests.factories import TestDataBuilder

# Create a complete customer with profile
builder = TestDataBuilder()
customer = builder.create_complete_customer(
    kyc_status='verified',
    credit_score=750
)

# Create a limit request workflow
workflow = builder.create_limit_request_workflow(
    customer=customer,
    current_limit=50000,
    requested_limit=100000
)
```

#### Custom Test Data
```python
from tests.factories import CustomerFactory

# Create customer with specific attributes
customer = CustomerFactory(
    customer_id='CUST123456',
    first_name='John',
    last_name='Doe',
    email='john.doe@example.com'
)
```

### Data Cleanup

#### Automatic Cleanup
- Database transactions are automatically rolled back after each test
- Temporary files are cleaned up automatically
- Mock objects are reset between tests

#### Manual Cleanup
```python
@pytest.fixture(autouse=True)
def cleanup_test_data():
    yield
    # Custom cleanup code
    clear_cache()
    reset_counters()
```

## Coverage and Reporting

### Coverage Configuration

#### Coverage Settings
```ini
[coverage:run]
source = .
omit = 
    */venv/*
    */migrations/*
    */tests/*
    manage.py
    */settings/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

#### Coverage Targets
- **Overall Coverage**: 85%+
- **Unit Tests**: 95%+
- **API Tests**: 90%+
- **Integration Tests**: 85%+
- **Security Tests**: 100%

### Report Generation

#### Console Report
```bash
python run_tests.py --with-coverage
```

#### HTML Report
```bash
python run_tests.py --html-report
# Report available at htmlcov/index.html
```

#### XML Report (for CI/CD)
```bash
python run_tests.py --xml-report
```

#### JSON Report
```bash
python run_tests.py --json-report
```

## CI/CD Integration

### GitHub Actions Configuration

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r test-requirements.txt
      - name: Run tests
        run: python run_tests.py --with-coverage --xml-report
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh 'python run_tests.py --with-coverage --xml-report'
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'test-results.xml'
                    publishCoverage adapters: [
                        coberturaAdapter('coverage.xml')
                    ]
                }
            }
        }
    }
}
```

### Docker Test Environment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt test-requirements.txt ./
RUN pip install -r requirements.txt -r test-requirements.txt

COPY . .
CMD ["python", "run_tests.py", "--with-coverage"]
```

## Best Practices

### Test Structure

#### Arrange-Act-Assert Pattern
```python
def test_customer_creation():
    # Arrange
    customer_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com'
    }
    
    # Act
    customer = Customer.objects.create(**customer_data)
    
    # Assert
    assert customer.first_name == 'John'
    assert customer.email == 'john@example.com'
```

#### Test Naming Convention
```python
# Pattern: test_[unit_being_tested]_[scenario]_[expected_result]
def test_customer_validation_invalid_email_raises_error():
    pass

def test_limit_request_auto_approval_below_threshold_approves():
    pass

def test_notification_sending_external_service_down_retries():
    pass
```

### Mocking Guidelines

#### External Service Mocking
```python
@pytest.fixture
def mock_firebase_service():
    with patch('services.firebase_service.FirebaseService') as mock:
        mock.verify_token.return_value = {'uid': 'test_user'}
        yield mock
```

#### Database Mocking
```python
@pytest.mark.django_db
def test_customer_creation():
    # Database operations are automatically mocked
    customer = CustomerFactory()
    assert Customer.objects.count() == 1
```

### Performance Testing

#### Response Time Testing
```python
@pytest.mark.performance
def test_api_response_time():
    start_time = time.time()
    response = client.get('/api/customers/')
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 0.5  # 500ms threshold
```

#### Load Testing
```python
@pytest.mark.load
def test_concurrent_requests():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(client.get, '/api/customers/')
            for _ in range(100)
        ]
        
        for future in as_completed(futures):
            response = future.result()
            assert response.status_code == 200
```

### Security Testing

#### Authentication Testing
```python
@pytest.mark.security
def test_unauthenticated_access_denied():
    client = APIClient()  # No authentication
    response = client.get('/api/customers/')
    assert response.status_code == 401
```

#### Authorization Testing
```python
@pytest.mark.security
def test_user_cannot_access_other_customer_data():
    other_customer = CustomerFactory()
    response = authenticated_client.get(f'/api/customers/{other_customer.id}/')
    assert response.status_code == 403
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Issue: Module not found
# Solution: Ensure PYTHONPATH is set correctly
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
```

#### Database Connection Errors
```bash
# Issue: Database connection failed
# Solution: Use test database settings
python run_tests.py --use-test-db
```

#### External Service Timeouts
```bash
# Issue: External service calls timing out
# Solution: Ensure mocking is enabled
python run_tests.py --mock-services
```

### Debug Mode

#### Verbose Output
```bash
python run_tests.py --verbose --debug
```

#### Drop into Debugger on Failure
```bash
pytest --pdb tests/unit/test_accounts_models.py
```

#### Live Logging
```bash
pytest --log-cli-level=DEBUG tests/
```

### Performance Issues

#### Slow Test Identification
```bash
python run_tests.py --with-timing --slow-threshold=1.0
```

#### Parallel Execution
```bash
python run_tests.py --parallel --workers=4
```

#### Database Optimization
```bash
python run_tests.py --use-memory-db
```

## Maintenance and Updates

### Regular Maintenance Tasks

1. **Update Test Dependencies**
   ```bash
   pip-compile test-requirements.in
   ```

2. **Review Coverage Reports**
   ```bash
   python run_tests.py --html-report
   # Check htmlcov/index.html for uncovered areas
   ```

3. **Performance Baseline Updates**
   ```bash
   python run_tests.py --performance --update-baselines
   ```

4. **Security Test Updates**
   ```bash
   python run_tests.py --security --update-patterns
   ```

### Test Data Maintenance

1. **Factory Updates**: Keep factories in sync with model changes
2. **Mock Updates**: Update mocks when external APIs change
3. **Test Case Reviews**: Regularly review and update test cases

### Documentation Updates

1. **API Changes**: Update test documentation when APIs change
2. **Process Changes**: Update workflow tests when business processes change
3. **Security Updates**: Update security tests when security requirements change

## Conclusion

This comprehensive testing framework ensures the Card Limit Increase System maintains high quality, security, and performance standards. Regular use of the testing suite during development helps catch issues early and maintains system reliability.

For additional support or questions about the testing framework, refer to the team documentation or contact the development team.