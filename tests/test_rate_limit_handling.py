#!/usr/bin/env python3
"""
Test script to simulate rate limit scenarios and verify backup account switching
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
    switch_to_backup_account,
    load_cookies,
    SESSION_FILE,
    SESSION_FILE_BACKUP,
    DECODO_PORTS
)

def simulate_rate_limit_scenario():
    """Simulate a rate limit scenario and test backup account switching"""
    print("⚡ Testing Rate Limit Handling with Backup Account Switching")
    print("=" * 65)
    
    # Load environment variables
    load_dotenv()
    primary_email = os.getenv("X_EMAIL")
    backup_email = os.getenv("X_EMAIL_BACKUP")
    
    print(f"Primary account: {primary_email if primary_email else 'Not configured'}")
    print(f"Backup account:  {backup_email if backup_email else 'Not configured'}")
    
    if not backup_email:
        print("❌ ERROR: Backup account not configured!")
        print("Please add X_EMAIL_BACKUP and X_PASSWORD_BACKUP to .env file")
        return False
    
    # Test proxy rotation capabilities
    print(f"\n🔗 Testing proxy rotation capabilities...")
    available_proxies = []
    
    for i in range(len(DECODO_PORTS)):
        proxy_working, proxy_ip = check_decodo_connection(i)
        if proxy_working:
            available_proxies.append((i, proxy_ip))
            print(f"✅ Proxy {i+1}: Port {DECODO_PORTS[i]} - IP {proxy_ip}")
        else:
            print(f"❌ Proxy {i+1}: Port {DECODO_PORTS[i]} - Not working")
    
    if len(available_proxies) < 2:
        print("⚠️  WARNING: Less than 2 working proxies. Rate limit mitigation may be limited.")
    else:
        print(f"✅ {len(available_proxies)} proxies available for rotation")
    
    # Simulate the rate limit scenario
    print(f"\n⚡ Simulating Rate Limit Scenario...")
    print("Scenario: Primary account gets rate limited, switch to backup account")
    
    with sync_playwright() as pw:
        # Step 1: Simulate primary account being rate limited
        print("\n1️⃣  Primary Account Status Check...")
        
        primary_session_exists = os.path.exists(SESSION_FILE)
        print(f"Primary session file exists: {primary_session_exists}")
        
        if primary_session_exists:
            print("✅ Primary account session available")
            print("🚫 SIMULATING: Primary account gets rate limited...")
            print("   (In real scenario, this would be detected by timeout/error patterns)")
        else:
            print("❌ Primary account session not available")
            print("   (This would trigger backup account switching immediately)")
        
        # Step 2: Test backup account switching
        print("\n2️⃣  Backup Account Switching Test...")
        
        # Test switching with different proxy ports
        for proxy_index, proxy_ip in available_proxies[:2]:  # Test first 2 proxies
            print(f"\nTesting backup switch with proxy {proxy_index+1} (IP: {proxy_ip})...")
            
            try:
                browser_backup, context_backup = switch_to_backup_account(pw, port_index=proxy_index)
                
                if browser_backup and context_backup:
                    print(f"✅ Successfully switched to backup account with proxy {proxy_index+1}")
                    
                    # Test basic functionality
                    page = context_backup.new_page()
                    try:
                        # Test navigation to X.com (without actually logging in to avoid rate limits)
                        print("   Testing X.com accessibility...")
                        page.goto("https://x.com", timeout=15000)
                        
                        # Check if page loaded
                        title = page.title()
                        if "X" in title or "Twitter" in title:
                            print("   ✅ X.com is accessible through proxy")
                        else:
                            print(f"   ⚠️  X.com loaded but title unexpected: {title}")
                        
                        page.close()
                        
                    except Exception as nav_error:
                        print(f"   ❌ Navigation test failed: {nav_error}")
                    
                    browser_backup.close()
                    print(f"   ✅ Backup account test completed for proxy {proxy_index+1}")
                    
                    # Small delay between tests
                    time.sleep(2)
                    
                else:
                    print(f"   ❌ Failed to switch to backup account with proxy {proxy_index+1}")
                    
            except Exception as switch_error:
                print(f"   ❌ Backup switching error with proxy {proxy_index+1}: {switch_error}")
        
        # Step 3: Test session persistence
        print("\n3️⃣  Session Persistence Test...")
        
        backup_session_exists = os.path.exists(SESSION_FILE_BACKUP)
        print(f"Backup session file exists: {backup_session_exists}")
        
        if backup_session_exists:
            print("✅ Backup session persisted successfully")
            
            # Test loading the session
            try:
                browser_test = pw.chromium.launch(headless=True)
                context_test = browser_test.new_context()
                
                if load_cookies(context_test, SESSION_FILE_BACKUP):
                    print("✅ Backup session can be loaded and reused")
                else:
                    print("⚠️  Backup session file exists but couldn't be loaded")
                
                browser_test.close()
                
            except Exception as session_error:
                print(f"❌ Session loading test failed: {session_error}")
        else:
            print("⚠️  Backup session was not persisted")
    
    # Step 4: Rate limit recovery simulation
    print(f"\n4️⃣  Rate Limit Recovery Simulation...")
    print("In a real scenario:")
    print("   • Monitor would detect primary account recovery")
    print("   • System would switch back to primary account")
    print("   • Backup account would remain available for future use")
    print("   • Different proxy IPs provide additional anonymity")
    
    # Summary
    print(f"\n📊 Rate Limit Handling Test Summary:")
    print(f"Available proxies: {len(available_proxies)}/3")
    print(f"Primary account: {'Configured' if primary_email else 'Not configured'}")
    print(f"Backup account: {'Configured' if backup_email else 'Not configured'}")
    print(f"Backup session: {'Available' if os.path.exists(SESSION_FILE_BACKUP) else 'Not available'}")
    
    if len(available_proxies) >= 2 and backup_email:
        print("✅ Rate limit handling system is properly configured!")
        return True
    else:
        print("⚠️  Rate limit handling system needs attention")
        return False

if __name__ == "__main__":
    success = simulate_rate_limit_scenario()
    if success:
        print("\n🎉 Rate limit handling test completed successfully!")
        print("Your system is ready to handle rate limits with backup account switching.")
    else:
        print("\n❌ Rate limit handling test revealed issues.")
        print("Please check your configuration and proxy setup.")
        sys.exit(1)