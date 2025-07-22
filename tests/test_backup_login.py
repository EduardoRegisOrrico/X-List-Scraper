#!/usr/bin/env python3
"""
Simple test script to test backup account login functionality
"""

import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from scraper import auto_login_backup_account, load_cookies, save_cookies

def test_backup_login():
    """Test backup account login functionality"""
    print("🔐 Testing Backup Account Login")
    print("=" * 35)
    
    load_dotenv()
    backup_email = os.getenv("X_EMAIL_BACKUP")
    backup_password = os.getenv("X_PASSWORD_BACKUP")
    
    if not backup_email or not backup_password:
        print("❌ Backup account credentials not found in .env file")
        print("Please set X_EMAIL_BACKUP and X_PASSWORD_BACKUP")
        return False
    
    print(f"Testing login for backup account: {backup_email}")
    
    try:
        with sync_playwright() as pw:
            # Create browser with different settings for backup account
            browser = pw.chromium.launch(
                headless=False,  # Show browser for debugging
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15"
            )
            
            print("🔄 Attempting automatic login for backup account...")
            
            # Test the auto_login_backup_account function
            success = auto_login_backup_account(context)
            
            if success:
                print("✅ Backup account login successful!")
                
                # Test if we can access Twitter home
                page = context.new_page()
                try:
                    page.goto("https://x.com/home", timeout=15000)
                    
                    # Check for login indicators
                    if page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']"):
                        print("✅ Successfully verified backup account session")
                        print("✅ Can access Twitter home page")
                    else:
                        print("⚠️  Login may have succeeded but verification failed")
                    
                    page.close()
                    
                except Exception as e:
                    print(f"⚠️  Error verifying session: {e}")
                
                return True
            else:
                print("❌ Backup account login failed")
                print("This could be due to:")
                print("  - Incorrect credentials")
                print("  - 2FA enabled on the account")
                print("  - Rate limiting")
                print("  - Changed Twitter login page structure")
                return False
                
    except Exception as e:
        print(f"❌ Error during backup login test: {e}")
        return False

def test_manual_backup_login():
    """Test manual backup account login (user completes login in browser)"""
    print("\n🔐 Manual Backup Account Login Test")
    print("=" * 40)
    
    load_dotenv()
    backup_email = os.getenv("X_EMAIL_BACKUP")
    
    print(f"Testing manual login for backup account: {backup_email}")
    print("A browser window will open - please complete the login manually")
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15"
            )
            
            page = context.new_page()
            page.goto("https://x.com/login")
            
            print("Please complete the login in the browser window...")
            input("Press Enter after you have successfully logged in and can see your home feed...")
            
            # Try to navigate to home to verify login
            try:
                page.goto("https://x.com/home", timeout=15000)
                
                if page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']"):
                    print("✅ Manual login successful!")
                    
                    # Save the session for future use
                    save_cookies(context, "x_session_backup.json")
                    print("✅ Backup session saved to x_session_backup.json")
                    return True
                else:
                    print("⚠️  Could not verify successful login")
                    return False
                    
            except Exception as e:
                print(f"❌ Error verifying manual login: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error during manual login test: {e}")
        return False

def main():
    print("🚀 Backup Account Login Test")
    print("=" * 30)
    
    # Test 1: Automatic login
    print("Test 1: Automatic Login")
    auto_success = test_backup_login()
    
    if not auto_success:
        print("\nAutomatic login failed. Let's try manual login...")
        
        # Test 2: Manual login as fallback
        manual_success = test_manual_backup_login()
        
        if manual_success:
            print("\n✅ Manual login successful!")
            print("You can now test the automatic login again, or use the saved session.")
        else:
            print("\n❌ Both automatic and manual login failed.")
            print("Please check your backup account credentials and try again.")
    else:
        print("\n🎉 Automatic backup login is working correctly!")

if __name__ == "__main__":
    main()