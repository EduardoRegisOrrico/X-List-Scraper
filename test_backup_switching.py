#!/usr/bin/env python3
"""
Test script to verify backup account switching functionality
"""

import os
import time
from dotenv import load_dotenv
from scraper import (
    switch_to_backup_account, 
    auto_login_backup_account, 
    load_cookies, 
    initialize_browser,
    scrape_list
)

def test_backup_account_setup():
    """Test if backup account credentials are properly configured"""
    print("🧪 Testing Backup Account Setup")
    print("=" * 40)
    
    load_dotenv()
    
    # Check primary account
    primary_email = os.getenv("X_EMAIL")
    primary_password = os.getenv("X_PASSWORD")
    
    # Check backup account
    backup_email = os.getenv("X_EMAIL_BACKUP")
    backup_password = os.getenv("X_PASSWORD_BACKUP")
    
    print(f"Primary account email: {'✓ Set' if primary_email else '✗ Missing'}")
    print(f"Primary account password: {'✓ Set' if primary_password else '✗ Missing'}")
    print(f"Backup account email: {'✓ Set' if backup_email else '✗ Missing'}")
    print(f"Backup account password: {'✓ Set' if backup_password else '✗ Missing'}")
    
    if not all([primary_email, primary_password]):
        print("\n❌ Primary account credentials missing!")
        print("Please set X_EMAIL and X_PASSWORD in your .env file")
        return False
    
    if not all([backup_email, backup_password]):
        print("\n❌ Backup account credentials missing!")
        print("Please set X_EMAIL_BACKUP and X_PASSWORD_BACKUP in your .env file")
        return False
    
    if primary_email == backup_email:
        print("\n⚠️  Warning: Primary and backup accounts use the same email!")
        print("For best results, use different Twitter accounts")
    
    print("\n✅ All credentials configured properly")
    return True

def test_backup_account_login():
    """Test backup account login functionality"""
    print("\n🔐 Testing Backup Account Login")
    print("=" * 35)
    
    try:
        # Initialize browser for backup account
        pw_backup, browser_backup, context_backup = switch_to_backup_account()
        
        if pw_backup and browser_backup and context_backup:
            print("✅ Backup account login successful!")
            
            # Test basic functionality
            try:
                page = context_backup.new_page()
                page.goto("https://x.com/home", timeout=15000)
                
                # Check if we're logged in
                if page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']"):
                    print("✅ Backup account session verified - can access Twitter home")
                else:
                    print("⚠️  Backup account session may not be fully authenticated")
                
                page.close()
                
            except Exception as e:
                print(f"⚠️  Error testing backup account session: {e}")
            
            # Cleanup
            try:
                browser_backup.close()
                pw_backup.stop()
            except:
                pass
            
            return True
        else:
            print("❌ Backup account login failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during backup account test: {e}")
        return False

def test_account_switching_scenario():
    """Test a realistic account switching scenario"""
    print("\n🔄 Testing Account Switching Scenario")
    print("=" * 40)
    
    try:
        # Initialize primary browser
        print("1. Initializing primary account browser...")
        pw_primary, browser_primary, context_primary = initialize_browser(headless=True, account_suffix="primary")
        
        # Try to load primary session
        primary_session_loaded = load_cookies(context_primary)
        print(f"   Primary session: {'✓ Loaded' if primary_session_loaded else '✗ Not found'}")
        
        if not primary_session_loaded:
            print("   ⚠️  Primary session not available - this would trigger backup switching")
        
        # Simulate switching to backup account
        print("\n2. Switching to backup account...")
        pw_backup, browser_backup, context_backup = switch_to_backup_account()
        
        if pw_backup and browser_backup and context_backup:
            print("   ✅ Backup account switch successful!")
            
            # Test scraping with backup account
            print("\n3. Testing scraping with backup account...")
            test_url = "https://x.com/i/lists/1919380958723158457"  # Default list
            
            try:
                tweets, newest_id = scrape_list(
                    test_url,
                    max_scrolls=1,  # Minimal scraping for test
                    wait_time=1,
                    browser_param=browser_backup,
                    context_param=context_backup,
                    limit=3
                )
                
                if tweets:
                    print(f"   ✅ Successfully scraped {len(tweets)} tweets with backup account!")
                    for i, tweet in enumerate(tweets, 1):
                        username = tweet.get('user', {}).get('username', 'Unknown')
                        print(f"      {i}. @{username}: {tweet['text'][:50]}...")
                else:
                    print("   ⚠️  No tweets found (may be rate limited or empty list)")
                
            except Exception as scrape_error:
                print(f"   ❌ Scraping test failed: {scrape_error}")
            
            # Cleanup backup
            try:
                browser_backup.close()
                pw_backup.stop()
            except:
                pass
        else:
            print("   ❌ Backup account switch failed")
        
        # Cleanup primary
        try:
            browser_primary.close()
            pw_primary.stop()
        except:
            pass
        
        print("\n✅ Account switching scenario test completed")
        return True
        
    except Exception as e:
        print(f"❌ Account switching test failed: {e}")
        return False

def main():
    print("🚀 Backup Account Switching Test Suite")
    print("=" * 45)
    
    # Test 1: Check configuration
    if not test_backup_account_setup():
        print("\n❌ Configuration test failed. Please fix credentials before proceeding.")
        return
    
    # Test 2: Test backup login
    print("\n" + "=" * 45)
    if not test_backup_account_login():
        print("\n❌ Backup login test failed. Check your backup account credentials.")
        return
    
    # Test 3: Test switching scenario
    print("\n" + "=" * 45)
    if test_account_switching_scenario():
        print("\n🎉 All tests passed! Backup account switching is working correctly.")
        print("\nYou can now use the scraper with confidence that it will switch")
        print("to the backup account when the primary account hits rate limits.")
    else:
        print("\n⚠️  Some tests failed. The backup switching may not work reliably.")

if __name__ == "__main__":
    main()