#!/usr/bin/env python3
"""
HDFC Card Limit System - Demo Readiness Checker
This script verifies that all components are ready for the live demo
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        files = len(os.listdir(dirpath))
        print(f"✅ {description}: {dirpath} ({files} files)")
        return True
    else:
        print(f"❌ {description}: {dirpath} - NOT FOUND")
        return False

def main():
    print("🔍 HDFC Card Limit System - Demo Readiness Check")
    print("=" * 55)
    
    base_path = Path(__file__).parent
    all_good = True
    
    print("\n📱 Flutter App Files:")
    flutter_files = [
        (base_path / "Frontend" / "flutter_api_integration.dart", "Flutter API Integration"),
        (base_path / "Frontend" / "hdfc_banking" / "pubspec.yaml", "Flutter Project Config"),
    ]
    
    for filepath, desc in flutter_files:
        if not check_file_exists(filepath, desc):
            all_good = False
    
    print("\n🔧 Backend Server Files:")
    backend_files = [
        (base_path / "Backend" / "card_limit_system" / "simple_server.py", "API Server"),
        (base_path / "Backend" / "oracle_setup.sql", "Database Schema"),
        (base_path / "Backend" / "oracle_live_monitoring.sql", "Live Monitoring Queries"),
        (base_path / "Backend" / "card_limit_system" / ".env", "Environment Config"),
        (base_path / "Backend" / "card_limit_system" / "api_views.py", "Django API Views"),
        (base_path / "Backend" / "card_limit_system" / "api_urls.py", "API URL Configuration"),
    ]
    
    for filepath, desc in backend_files:
        if not check_file_exists(filepath, desc):
            all_good = False
    
    print("\n📚 Documentation Files:")
    doc_files = [
        (base_path / "READY_FOR_DEMO.md", "Demo Instructions"),
        (base_path / "DEMO_GUIDE.md", "Detailed Demo Guide"),
        (base_path / "Backend" / "LIVE_DATA_DEMO_SETUP.md", "Live Data Setup"),
        (base_path / "test_api.ps1", "API Test Script"),
        (base_path / "start_server.bat", "Server Start Script"),
    ]
    
    for filepath, desc in doc_files:
        if not check_file_exists(filepath, desc):
            all_good = False
    
    print("\n🗂️ Directory Structure:")
    directories = [
        (base_path / "Frontend", "Frontend Directory"),
        (base_path / "Backend", "Backend Directory"),
        (base_path / "Backend" / "card_limit_system", "Django Project"),
        (base_path / "Docs", "Documentation"),
    ]
    
    for dirpath, desc in directories:
        if not check_directory_exists(dirpath, desc):
            all_good = False
    
    print("\n🔍 Configuration Validation:")
    
    # Check .env file content
    env_file = base_path / "Backend" / "card_limit_system" / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
            if 'ORACLE_DSN' in env_content and 'hdfc_user' in env_content:
                print("✅ Environment Config: Oracle settings configured")
            else:
                print("❌ Environment Config: Missing Oracle settings")
                all_good = False
    
    # Check server script
    server_file = base_path / "Backend" / "card_limit_system" / "simple_server.py"
    if server_file.exists():
        with open(server_file, 'r') as f:
            server_content = f.read()
            if 'class HDFCAPIHandler' in server_content and 'localhost:8000' in server_content:
                print("✅ Server Script: API endpoints configured")
            else:
                print("❌ Server Script: Missing API configuration")
                all_good = False
    
    # Check Oracle setup script
    oracle_file = base_path / "Backend" / "oracle_setup.sql"
    if oracle_file.exists():
        with open(oracle_file, 'r') as f:
            oracle_content = f.read()
            if 'CREATE TABLE customers' in oracle_content and 'CREATE TABLE limit_requests' in oracle_content:
                print("✅ Oracle Schema: Database tables defined")
            else:
                print("❌ Oracle Schema: Missing table definitions")
                all_good = False
    
    print("\n" + "=" * 55)
    
    if all_good:
        print("🎉 DEMO READY! All components are properly configured.")
        print("\n📋 Next Steps:")
        print("1. Start Oracle Database service")
        print("2. Execute: py Backend\\card_limit_system\\simple_server.py")
        print("3. Open Oracle SQL Developer and run oracle_setup.sql")
        print("4. Configure Flutter app with API endpoint")
        print("5. Begin client demonstration!")
        print("\n🚀 Good luck with your demo!")
    else:
        print("⚠️  ISSUES FOUND! Please resolve the missing files/configurations above.")
        print("\n🔧 Quick fixes:")
        print("- Ensure all files are in the correct directories")
        print("- Check file permissions")
        print("- Verify configuration settings")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())