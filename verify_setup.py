#!/usr/bin/env python3
"""
Quick verification script to check if XScraper is properly configured with Decodo proxy
"""
import os
import sys
from dotenv import load_dotenv

def verify_setup():
    """Verify that XScraper is properly configured"""
    print("🔍 XScraper Setup Verification")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Check database configuration
    print("\n📊 Database Configuration:")
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("✅ DATABASE_URL configured")
    else:
        print("❌ DATABASE_URL not found")
    
    # Check API configuration
    print("\n🌐 API Configuration:")
    api_base_url = os.getenv("API_BASE_URL")
    if api_base_url:
        print(f"✅ API_BASE_URL: {api_base_url}")
    else:
        print("❌ API_BASE_URL not found")
    
    # Check primary account
    print("\n👤 Primary Account:")
    primary_email = os.getenv("X_EMAIL")
    primary_password = os.getenv("X_PASSWORD")
    if primary_email and primary_password:
        print(f"✅ Primary account configured: {primary_email}")
    else:
        print("❌ Primary account credentials missing")
    
    # Check backup account
    print("\n👥 Backup Account:")
    backup_email = os.getenv("X_EMAIL_BACKUP")
    backup_password = os.getenv("X_PASSWORD_BACKUP")
    if backup_email and backup_password:
        print(f"✅ Backup account configured: {backup_email}")
    else:
        print("❌ Backup account credentials missing")
    
    # Check Decodo proxy configuration
    print("\n🔗 Decodo Proxy Configuration:")
    decodo_username = os.getenv("DECODO_USERNAME")
    decodo_password = os.getenv("DECODO_PASSWORD")
    decodo_host = os.getenv("DECODO_HOST")
    decodo_ports = os.getenv("DECODO_PORTS")
    
    if all([decodo_username, decodo_password, decodo_host, decodo_ports]):
        print(f"✅ Decodo proxy configured")
        print(f"   Username: {decodo_username}")
        print(f"   Host: {decodo_host}")
        print(f"   Ports: {decodo_ports}")
    else:
        print("❌ Decodo proxy configuration incomplete")
    
    # Check for old Tor configuration
    print("\n🧅 Legacy Configuration Check:")
    tor_configs = [
        "USE_TOR_FOR_BACKUP",
        "USE_TOR_FOR_PRIMARY", 
        "TOR_PROXY_HOST",
        "TOR_PROXY_PORT",
        "TOR_CONTROL_PORT",
        "PROXY_SERVER"
    ]
    
    tor_found = False
    for config in tor_configs:
        if os.getenv(config):
            print(f"⚠️  Found legacy Tor config: {config}")
            tor_found = True
    
    if not tor_found:
        print("✅ No legacy Tor configuration found")
    
    # Check required files
    print("\n📁 Required Files:")
    required_files = [
        "scraper.py",
        "rate_limit_debugger.py",
        ".env",
        "requirements.txt"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
    
    # Check test files
    print("\n🧪 Test Files:")
    test_files = [
        "test_decodo_proxy.py",
        "test_backup_switching.py", 
        "test_rate_limit_handling.py"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
    
    # Summary
    print(f"\n📋 Setup Summary:")
    
    issues = []
    if not database_url:
        issues.append("Database configuration")
    if not (primary_email and primary_password):
        issues.append("Primary account credentials")
    if not (backup_email and backup_password):
        issues.append("Backup account credentials")
    if not all([decodo_username, decodo_password, decodo_host, decodo_ports]):
        issues.append("Decodo proxy configuration")
    
    if not issues:
        print("✅ All configurations are properly set up!")
        print("\n🚀 Ready to run:")
        print("   python3 scraper.py --url 'https://x.com/i/lists/YOUR_LIST_ID'")
        return True
    else:
        print(f"❌ Issues found: {len(issues)}")
        for issue in issues:
            print(f"   • {issue}")
        print("\n🔧 Please fix the issues above before running the scraper.")
        return False

if __name__ == "__main__":
    success = verify_setup()
    if not success:
        sys.exit(1)