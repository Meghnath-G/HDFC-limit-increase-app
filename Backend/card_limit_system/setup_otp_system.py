#!/usr/bin/env python3
"""
HDFC OTP System Startup Script

This script provides a simple interface to configure, validate, and test
the complete OTP system with guided setup.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step, description):
    """Print a formatted step."""
    print(f"\n📋 Step {step}: {description}")
    print("-" * 40)

def run_command(command, description):
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def check_python_environment():
    """Check if Python environment is properly set up."""
    print_step(1, "Checking Python Environment")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"✅ Python {python_version.major}.{python_version.minor} is supported")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} - Need Python 3.8+")
        return False
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if (current_dir / 'manage.py').exists():
        print("✅ Found Django project directory")
    else:
        print("❌ Not in Django project directory")
        return False
    
    return True

def install_dependencies():
    """Install required Python dependencies."""
    print_step(2, "Installing Dependencies")
    
    # Check if requirements.txt exists
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt not found")
        return False
    
    # Install dependencies
    return run_command("pip install -r requirements.txt", "Installing Python packages")

def validate_configuration():
    """Run configuration validation."""
    print_step(3, "Validating Configuration")
    
    if not Path('validate_config.py').exists():
        print("❌ Configuration validator not found")
        return False
    
    return run_command("python validate_config.py", "Validating configuration")

def test_twilio_connection():
    """Test Twilio connection."""
    print_step(4, "Testing Twilio Connection")
    
    if not Path('test_twilio_connection.py').exists():
        print("❌ Twilio test script not found")
        return False
    
    return run_command("python test_twilio_connection.py", "Testing Twilio connection")

def run_database_migrations():
    """Run database migrations."""
    print_step(5, "Setting Up Database")
    
    # Make migrations
    if not run_command("python manage.py makemigrations", "Creating migrations"):
        return False
    
    # Apply migrations
    return run_command("python manage.py migrate", "Applying migrations")

def start_django_server():
    """Start Django development server."""
    print_step(6, "Starting Django Server")
    
    print("🔄 Starting Django development server...")
    print("📝 Server will run at http://localhost:8000")
    print("📝 Press Ctrl+C to stop the server")
    print("\n" + "=" * 60)
    
    try:
        subprocess.run("python manage.py runserver", shell=True)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

def interactive_setup():
    """Interactive setup wizard."""
    print_header("HDFC OTP System Setup Wizard")
    
    steps = [
        ("Check Python Environment", check_python_environment),
        ("Install Dependencies", install_dependencies),
        ("Validate Configuration", validate_configuration),
        ("Test Twilio Connection", test_twilio_connection),
        ("Setup Database", run_database_migrations),
    ]
    
    print("This wizard will help you set up and test the OTP system.")
    print("Each step must complete successfully before proceeding to the next.")
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        
        # Ask user if they want to run this step
        response = input(f"Run '{step_name}'? (y/n/q): ").strip().lower()
        
        if response == 'q':
            print("Setup cancelled by user")
            return
        elif response == 'n':
            print(f"⏭️  Skipping {step_name}")
            continue
        
        # Run the step
        success = step_func()
        
        if not success:
            print(f"\n❌ {step_name} failed!")
            
            retry = input("Would you like to retry this step? (y/n): ").strip().lower()
            if retry == 'y':
                success = step_func()
            
            if not success:
                print("❌ Setup cannot continue due to failed step.")
                return
    
    # All steps completed
    print_header("Setup Complete!")
    print("🎉 All setup steps completed successfully!")
    
    # Ask if user wants to start the server
    start_server = input("\nWould you like to start the Django server? (y/n): ").strip().lower()
    if start_server == 'y':
        start_django_server()
    else:
        print("\n✅ Setup complete. You can start the server later with:")
        print("   python manage.py runserver")

def quick_test():
    """Run quick validation and testing."""
    print_header("Quick OTP System Test")
    
    print("🔄 Running quick validation and testing...")
    
    # Quick checks
    checks = [
        ("python validate_config.py", "Configuration validation"),
        ("python test_twilio_connection.py", "Twilio connection test"),
    ]
    
    all_passed = True
    
    for command, description in checks:
        if Path(command.split()[1]).exists():
            success = run_command(command, description)
            if not success:
                all_passed = False
        else:
            print(f"⏭️  Skipping {description} (script not found)")
    
    if all_passed:
        print("\n🎉 Quick test passed! System appears to be working.")
        
        # Offer to run full API test
        api_test = input("\nWould you like to run full API testing? (y/n): ").strip().lower()
        if api_test == 'y':
            if Path('test_otp_api.py').exists():
                run_command("python test_otp_api.py", "Full API testing")
            else:
                print("❌ API test script not found")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")

def main():
    """Main function with user menu."""
    print_header("HDFC OTP System Management")
    
    while True:
        print("\nWhat would you like to do?")
        print("1. 🔧 Interactive Setup Wizard")
        print("2. ⚡ Quick Test")
        print("3. 🔍 Validate Configuration Only")
        print("4. 📞 Test Twilio Connection Only")
        print("5. 🗄️  Run Database Migrations Only")
        print("6. 🚀 Start Django Server")
        print("7. 🧪 Run API Tests")
        print("8. ❌ Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            interactive_setup()
        elif choice == '2':
            quick_test()
        elif choice == '3':
            validate_configuration()
        elif choice == '4':
            test_twilio_connection()
        elif choice == '5':
            run_database_migrations()
        elif choice == '6':
            start_django_server()
        elif choice == '7':
            if Path('test_otp_api.py').exists():
                run_command("python test_otp_api.py", "API testing")
            else:
                print("❌ API test script not found")
        elif choice == '8':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-8.")

if __name__ == "__main__":
    main()