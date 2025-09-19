#!/usr/bin/env python
"""
Test runner script for the Card Limit System.

This script provides various options for running tests including
unit tests, integration tests, coverage reports, and performance tests.
"""

import os
import sys
import django
import subprocess
from django.conf import settings
from django.test.utils import get_runner

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'card_limit_system.test_settings')

# Setup Django
django.setup()


def run_unit_tests():
    """Run unit tests only."""
    print("🧪 Running Unit Tests...")
    cmd = [
        'python', '-m', 'pytest',
        'tests/test_*_models.py',
        'tests/test_*_serializers.py',
        'tests/test_*_utils.py',
        '-v', '--tb=short'
    ]
    return subprocess.run(cmd).returncode


def run_api_tests():
    """Run API tests only."""
    print("🌐 Running API Tests...")
    cmd = [
        'python', '-m', 'pytest',
        'tests/test_*_api.py',
        'tests/test_*_views.py',
        '-v', '--tb=short'
    ]
    return subprocess.run(cmd).returncode


def run_integration_tests():
    """Run integration tests only."""
    print("🔄 Running Integration Tests...")
    cmd = [
        'python', '-m', 'pytest',
        'tests/test_external_services.py',
        'tests/test_business_logic.py',
        '-v', '--tb=short'
    ]
    return subprocess.run(cmd).returncode


def run_all_tests():
    """Run all tests with coverage."""
    print("🎯 Running All Tests with Coverage...")
    cmd = [
        'python', '-m', 'pytest',
        'tests/',
        '--cov=accounts',
        '--cov=cards',
        '--cov=requests',
        '--cov=notifications',
        '--cov=core',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-fail-under=85',
        '-v'
    ]
    return subprocess.run(cmd).returncode


def run_security_tests():
    """Run security-focused tests."""
    print("🔒 Running Security Tests...")
    cmd = [
        'python', '-m', 'pytest',
        '-m', 'security',
        'tests/',
        '-v', '--tb=short'
    ]
    return subprocess.run(cmd).returncode


def run_performance_tests():
    """Run performance tests."""
    print("⚡ Running Performance Tests...")
    cmd = [
        'python', '-m', 'pytest',
        '-m', 'performance',
        'tests/',
        '-v', '--tb=short'
    ]
    return subprocess.run(cmd).returncode


def run_specific_test(test_path):
    """Run a specific test file or test method."""
    print(f"🎯 Running Specific Test: {test_path}")
    cmd = [
        'python', '-m', 'pytest',
        test_path,
        '-v', '--tb=short'
    ]
    return subprocess.run(cmd).returncode


def generate_coverage_report():
    """Generate detailed coverage report."""
    print("📊 Generating Coverage Report...")
    
    # Run tests with coverage
    cmd = [
        'python', '-m', 'pytest',
        'tests/',
        '--cov=accounts',
        '--cov=cards',
        '--cov=requests',
        '--cov=notifications',
        '--cov=core',
        '--cov-report=html:htmlcov',
        '--cov-report=xml:coverage.xml',
        '--cov-report=term-missing',
        '--quiet'
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ Coverage report generated successfully!")
        print("📁 HTML report: htmlcov/index.html")
        print("📄 XML report: coverage.xml")
    else:
        print("❌ Coverage report generation failed!")
    
    return result.returncode


def run_linting():
    """Run code linting and formatting checks."""
    print("🔍 Running Code Quality Checks...")
    
    # Run flake8
    print("Running flake8...")
    flake8_cmd = ['flake8', '.', '--max-line-length=88', '--extend-ignore=E203,W503']
    flake8_result = subprocess.run(flake8_cmd)
    
    # Run black check
    print("Running black...")
    black_cmd = ['black', '--check', '.']
    black_result = subprocess.run(black_cmd)
    
    # Run isort check
    print("Running isort...")
    isort_cmd = ['isort', '--check-only', '.']
    isort_result = subprocess.run(isort_cmd)
    
    if all(r.returncode == 0 for r in [flake8_result, black_result, isort_result]):
        print("✅ All code quality checks passed!")
        return 0
    else:
        print("❌ Some code quality checks failed!")
        return 1


def setup_test_database():
    """Set up test database with sample data."""
    print("🗄️ Setting up test database...")
    
    # Create test database tables
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
    
    # Create test data
    from tests.factories import TestDataBuilder
    
    # Create sample customers
    for i in range(5):
        TestDataBuilder.create_complete_customer()
    
    # Create sample limit requests
    for i in range(10):
        TestDataBuilder.create_limit_request_workflow()
    
    print("✅ Test database setup complete!")


def cleanup_test_data():
    """Clean up test data and temporary files."""
    print("🧹 Cleaning up test data...")
    
    # Remove coverage files
    import shutil
    files_to_remove = ['htmlcov', 'coverage.xml', '.coverage']
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
    
    print("✅ Cleanup complete!")


def main():
    """Main test runner function."""
    if len(sys.argv) < 2:
        print("🧪 HDFC Card Limit System Test Runner")
        print("=====================================")
        print("Usage: python run_tests.py <command>")
        print("")
        print("Available commands:")
        print("  unit         - Run unit tests only")
        print("  api          - Run API tests only")
        print("  integration  - Run integration tests only")
        print("  all          - Run all tests with coverage")
        print("  security     - Run security tests only")
        print("  performance  - Run performance tests only")
        print("  coverage     - Generate coverage report")
        print("  lint         - Run code quality checks")
        print("  setup        - Set up test database")
        print("  cleanup      - Clean up test data")
        print("  <test_path>  - Run specific test file or method")
        print("")
        print("Examples:")
        print("  python run_tests.py all")
        print("  python run_tests.py unit")
        print("  python run_tests.py tests/test_accounts_models.py")
        print("  python run_tests.py tests/test_accounts_api.py::CustomerAPITest::test_customer_registration")
        return 1
    
    command = sys.argv[1]
    
    # Command mapping
    commands = {
        'unit': run_unit_tests,
        'api': run_api_tests,
        'integration': run_integration_tests,
        'all': run_all_tests,
        'security': run_security_tests,
        'performance': run_performance_tests,
        'coverage': generate_coverage_report,
        'lint': run_linting,
        'setup': setup_test_database,
        'cleanup': cleanup_test_data,
    }
    
    if command in commands:
        return commands[command]()
    else:
        # Treat as specific test path
        return run_specific_test(command)


if __name__ == '__main__':
    sys.exit(main())