#!/usr/bin/env python3
"""
HDFC OTP Configuration Validator

This script validates all configuration requirements for the OTP system
including Twilio, Firebase, Django settings, and database connectivity.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

class ConfigValidator:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
        
    def log_success(self, message):
        """Log a successful check."""
        self.success_count += 1
        self.total_checks += 1
        print(f"✅ {message}")
    
    def log_error(self, message):
        """Log an error."""
        self.errors.append(message)
        self.total_checks += 1
        print(f"❌ {message}")
    
    def log_warning(self, message):
        """Log a warning."""
        self.warnings.append(message)
        print(f"⚠️  {message}")
    
    def load_env_file(self):
        """Load and validate .env file."""
        print("🔧 Checking Environment Configuration...")
        print("-" * 50)
        
        env_file = self.project_dir / '.env'
        
        if not env_file.exists():
            self.log_error(".env file not found")
            return {}
        
        self.log_success(".env file exists")
        
        env_vars = {}
        try:
            with open(env_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip('"\'')
                        env_vars[key] = value
                        os.environ[key] = value
            
            self.log_success(f"Loaded {len(env_vars)} environment variables")
            return env_vars
            
        except Exception as e:
            self.log_error(f"Error reading .env file: {e}")
            return {}
    
    def validate_django_config(self, env_vars):
        """Validate Django configuration."""
        print("\n🌐 Checking Django Configuration...")
        print("-" * 50)
        
        # Check SECRET_KEY
        secret_key = env_vars.get('SECRET_KEY')
        if not secret_key:
            self.log_error("SECRET_KEY not found")
        elif len(secret_key) < 50:
            self.log_warning("SECRET_KEY should be longer for production")
            self.log_success("SECRET_KEY is present")
        else:
            self.log_success("SECRET_KEY is properly configured")
        
        # Check DEBUG setting
        debug = env_vars.get('DEBUG', 'True')
        if debug.lower() == 'true':
            self.log_warning("DEBUG is enabled (not recommended for production)")
        else:
            self.log_success("DEBUG is disabled for production")
        
        # Check ALLOWED_HOSTS
        allowed_hosts = env_vars.get('ALLOWED_HOSTS')
        if not allowed_hosts:
            self.log_error("ALLOWED_HOSTS not configured")
        else:
            self.log_success("ALLOWED_HOSTS is configured")
    
    def validate_twilio_config(self, env_vars):
        """Validate Twilio configuration."""
        print("\n📞 Checking Twilio Configuration...")
        print("-" * 50)
        
        required_twilio_vars = [
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'TWILIO_PHONE_NUMBER'
        ]
        
        for var in required_twilio_vars:
            value = env_vars.get(var)
            if not value:
                self.log_error(f"{var} not found")
                continue
            
            # Validate format
            if var == 'TWILIO_ACCOUNT_SID':
                if not value.startswith('AC') or len(value) != 34:
                    self.log_error(f"{var} has invalid format (should start with 'AC' and be 34 characters)")
                else:
                    self.log_success(f"{var} format is valid")
            
            elif var == 'TWILIO_AUTH_TOKEN':
                if len(value) < 30:
                    self.log_error(f"{var} appears to be incomplete")
                else:
                    self.log_success(f"{var} is present and appears valid")
            
            elif var == 'TWILIO_PHONE_NUMBER':
                if not re.match(r'^\+\d{10,15}$', value):
                    self.log_error(f"{var} has invalid format (should be +1234567890)")
                else:
                    self.log_success(f"{var} format is valid")
        
        # Check optional Verify SID
        verify_sid = env_vars.get('TWILIO_VERIFY_SID')
        if verify_sid:
            if verify_sid.startswith('VA') and len(verify_sid) == 34:
                self.log_success("TWILIO_VERIFY_SID format is valid")
            else:
                self.log_warning("TWILIO_VERIFY_SID format appears invalid")
        else:
            self.log_warning("TWILIO_VERIFY_SID not configured (optional)")
    
    def validate_firebase_config(self, env_vars):
        """Validate Firebase configuration."""
        print("\n🔥 Checking Firebase Configuration...")
        print("-" * 50)
        
        required_firebase_vars = [
            'FIREBASE_PROJECT_ID',
            'FIREBASE_PRIVATE_KEY_ID',
            'FIREBASE_PRIVATE_KEY',
            'FIREBASE_CLIENT_EMAIL',
            'FIREBASE_CLIENT_ID'
        ]
        
        for var in required_firebase_vars:
            value = env_vars.get(var)
            if not value:
                self.log_error(f"{var} not found")
                continue
            
            # Basic validation
            if var == 'FIREBASE_PROJECT_ID':
                if not re.match(r'^[a-z0-9-]+$', value):
                    self.log_warning(f"{var} format may be invalid")
                else:
                    self.log_success(f"{var} format is valid")
            
            elif var == 'FIREBASE_CLIENT_EMAIL':
                if '@' not in value or 'iam.gserviceaccount.com' not in value:
                    self.log_warning(f"{var} format may be invalid")
                else:
                    self.log_success(f"{var} format is valid")
            
            elif var == 'FIREBASE_PRIVATE_KEY':
                if 'BEGIN PRIVATE KEY' not in value:
                    self.log_error(f"{var} appears to be incomplete or invalid")
                else:
                    self.log_success(f"{var} format appears valid")
            
            else:
                self.log_success(f"{var} is present")
        
        # Check for service account key file
        service_key_file = self.project_dir / 'firebase-service-account-key.json'
        if service_key_file.exists():
            self.log_success("Firebase service account key file exists")
            try:
                with open(service_key_file, 'r') as f:
                    key_data = json.load(f)
                    if 'project_id' in key_data and 'private_key' in key_data:
                        self.log_success("Service account key file format is valid")
                    else:
                        self.log_error("Service account key file is missing required fields")
            except Exception as e:
                self.log_error(f"Error reading service account key file: {e}")
        else:
            self.log_warning("Firebase service account key file not found (using environment variables)")
    
    def validate_database_config(self):
        """Validate database configuration."""
        print("\n🗄️  Checking Database Configuration...")
        print("-" * 50)
        
        # Check if migrations directory exists
        migrations_dir = self.project_dir / 'migrations'
        if migrations_dir.exists():
            migration_files = list(migrations_dir.glob('*.py'))
            if migration_files:
                self.log_success(f"Found {len(migration_files)} migration files")
            else:
                self.log_warning("No migration files found")
        else:
            self.log_warning("Migrations directory not found")
        
        # Check for customer OTP migration
        otp_migration = self.project_dir / 'migrations' / '0006_customer_otp_fields.py'
        if otp_migration.exists():
            self.log_success("Customer OTP fields migration exists")
        else:
            self.log_error("Customer OTP fields migration not found")
    
    def validate_dependencies(self):
        """Validate Python dependencies."""
        print("\n📦 Checking Python Dependencies...")
        print("-" * 50)
        
        required_packages = [
            'django',
            'djangorestframework',
            'twilio',
            'firebase-admin'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.log_success(f"{package} is installed")
            except ImportError:
                self.log_error(f"{package} is not installed")
    
    def validate_file_structure(self):
        """Validate required file structure."""
        print("\n📁 Checking File Structure...")
        print("-" * 50)
        
        required_files = [
            'core/twilio_otp_service.py',
            'otp/twilio_views.py',
            'apps/otp/urls.py',
            'apps/customers/models.py',
            'apps/otp/serializers.py'
        ]
        
        for file_path in required_files:
            full_path = self.project_dir / file_path
            if full_path.exists():
                self.log_success(f"{file_path} exists")
            else:
                self.log_error(f"{file_path} not found")
        
        # Check if required directories exist
        required_dirs = [
            'apps/customers/management/commands',
            'templates/api_docs',
            'tests'
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_dir / dir_path
            if full_path.exists():
                self.log_success(f"{dir_path}/ directory exists")
            else:
                self.log_warning(f"{dir_path}/ directory not found")
    
    def validate_security_settings(self, env_vars):
        """Validate security settings."""
        print("\n🔐 Checking Security Settings...")
        print("-" * 50)
        
        # Check JWT settings
        jwt_secret = env_vars.get('JWT_SECRET_KEY')
        if jwt_secret:
            if len(jwt_secret) < 32:
                self.log_warning("JWT_SECRET_KEY should be longer for better security")
            else:
                self.log_success("JWT_SECRET_KEY is properly configured")
        else:
            self.log_warning("JWT_SECRET_KEY not found")
        
        # Check if dangerous values are being used
        dangerous_values = [
            'your_actual_twilio_auth_token_here',
            'your-private-key-id-here',
            'YOUR_PRIVATE_KEY_HERE',
            'your-client-id-here'
        ]
        
        for key, value in env_vars.items():
            if any(dangerous in value for dangerous in dangerous_values):
                self.log_error(f"{key} contains placeholder value - needs real credentials")
    
    def generate_report(self):
        """Generate final validation report."""
        print("\n" + "=" * 60)
        print("📋 CONFIGURATION VALIDATION REPORT")
        print("=" * 60)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project Directory: {self.project_dir}")
        print("=" * 60)
        
        print(f"\n📊 Results:")
        print(f"✅ Successful checks: {self.success_count}")
        print(f"❌ Failed checks: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"📝 Total checks: {self.total_checks}")
        
        if self.errors:
            print(f"\n❌ Errors that need to be fixed:")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings to consider:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        # Overall status
        if not self.errors:
            if not self.warnings:
                print(f"\n🎉 Perfect! All configurations are valid!")
            else:
                print(f"\n✅ Good! Configuration is valid with some warnings.")
            print("Your OTP system is ready for testing!")
        else:
            print(f"\n❌ Configuration needs fixes before testing.")
            print("Please address the errors listed above.")
        
        print("=" * 60)
    
    def run_validation(self):
        """Run complete configuration validation."""
        print("🔍 HDFC OTP Configuration Validator")
        print("=" * 50)
        
        # Load environment variables
        env_vars = self.load_env_file()
        
        # Run all validations
        self.validate_django_config(env_vars)
        self.validate_twilio_config(env_vars)
        self.validate_firebase_config(env_vars)
        self.validate_database_config()
        self.validate_dependencies()
        self.validate_file_structure()
        self.validate_security_settings(env_vars)
        
        # Generate final report
        self.generate_report()

def main():
    """Main function to run configuration validation."""
    validator = ConfigValidator()
    validator.run_validation()

if __name__ == "__main__":
    main()