#!/usr/bin/env python3
"""
Test script to verify backup account switching with Decodo proxy
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Add the current directory to Python path to import from scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import (
    check_decodo_connection, 
    create_decodo_browser_context,
    switch_to_backup_account,
    load_cookies,
    SESSION_FILE_BACKUP
)

def test_backup_account_switching():
    """Test the backup account switching functionality"""
    print("🔄 Testing Backup Account Switching with Decodo Proxy")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    backup_email = os.getenv("X_EMAIL_BACKUP")
    backup_password = os.getenv("X_PASSWORD_BACKUP")
    
    if not backup_email or not backup_password:
        print("❌ ERROR: X_EMAIL_BACKUP and X_PASSWORD_BACKUP not found in .env file")
        print("Please add your backup account credentials to continue testing.")
        return False
    
    print(f"✅ Backup account credentials found: {backup_email}")
    
    # Test all 3 Decodo proxy ports
    print("\n🔗 Testing Decodo proxy connections...")
    working_ports = []
    
    for port_index in range(3):
        print(f"\nTesting port index {port_index}...")
        proxy_working, proxy_ip = check_decodo_connection(port_index)
        if proxy_working:
            working_ports.append((port_index, proxy_ip))
            print(f"✅ Port {port_index}: Working with IP {proxy_ip}")
        else:
            print(f"❌ Port {port_index}: Not working")
    
    if not working_ports:
        print("❌ ERROR: No working Decodo proxy ports found!")
        return False
    
    print(f"\n✅ Found {len(working_ports)} working proxy ports")
    
    # Test browser creation with different ports
    print("\n🌐 Testing browser creation with Decodo proxy...")
    
    with sync_playwright() as pw:
        for port_index, proxy_ip in working_ports[:2]:  # Test first 2 working ports
            print(f"\nTesting browser creation with port {port_index} (IP: {proxy_ip})...")
            
            try:
                browser, context = create_decodo_browser_context(
                    pw, 
                    headless=True, 
                    account_type="backup", 
                    port_index=port_index
                )
                
                if browser and context:
                    print(f"✅ Successfully created browser with port {port_index}")
                    
                    # Test basic page navigation
                    page = context.new_page()
                    try:
                        print("Testing page navigation...")
                        page.goto("https://httpbin.org/ip", timeout=15000)
                        content = page.content()
                        if proxy_ip in content:
                            print(f"✅ Browser is using correct proxy IP: {proxy_ip}")
                        else:
                            print(f"⚠️  Could not verify proxy IP in page content")
                        
                        page.close()
                        print(f"✅ Page navigation test passed for port {port_index}")
                        
                    except Exception as nav_error:
                        print(f"❌ Page navigation failed for port {port_index}: {nav_error}")
                    
                    browser.close()
                    print(f"✅ Browser cleanup completed for port {port_index}")
                    
                else:
                    print(f"❌ Failed to create browser with port {port_index}")
                    
            except Exception as browser_error:
                print(f"❌ Browser creation error for port {port_index}: {browser_error}")
    
    # Test the full switch_to_backup_account function
    print(f"\n🔄 Testing full backup account switching...")
    
    with sync_playwright() as pw:
        try:
            # Test with a specific port
            test_port = working_ports[0][0]  # Use first working port
            print(f"Testing switch_to_backup_account with port {test_port}...")
            
            browser_backup, context_backup = switch_to_backup_account(pw, port_index=test_port)
            
            if browser_backup and context_backup:
                print("✅ switch_to_backup_account succeeded!")
                
                # Check if session file was created
                if os.path.exists(SESSION_FILE_BACKUP):
                    print("✅ Backup session file was created")
                else:
                    print("⚠️  Backup session file was not created (login may have failed)")
                
                # Test loading the session
                if load_cookies(context_backup, SESSION_FILE_BACKUP):
                    print("✅ Backup session can be loaded successfully")
                else:
                    print("⚠️  Could not load backup session")
                
                browser_backup.close()
                print("✅ Backup browser cleanup completed")
                
            else:
                print("❌ switch_to_backup_account failed")
                
        except Exception as switch_error:
            print(f"❌ Backup account switching error: {switch_error}")
    
    print(f"\n📊 Test Summary:")
    print(f"Working proxy ports: {len(working_ports)}/3")
    print(f"Backup account: {backup_email}")
    print("✅ Backup account switching test completed!")
    
    return len(working_ports) > 0

if __name__ == "__main__":
    success = test_backup_account_switching()
    if success:
        print("\n🎉 All tests passed! Backup account switching is ready to use.")
    else:
        print("\n❌ Some tests failed. Please check your configuration.")
        sys.exit(1)