#!/usr/bin/env python3
"""
Helper script to set up backup account credentials and test the multi-account setup.
"""

import os
from dotenv import load_dotenv, set_key
import getpass

def setup_backup_credentials():
    """Interactive setup for backup account credentials"""
    load_dotenv()
    
    print("🔧 Multi-Account Twitter Scraper Setup")
    print("=" * 40)
    
    # Check existing credentials
    primary_email = os.getenv("X_EMAIL")
    backup_email = os.getenv("X_EMAIL_BACKUP")
    
    print(f"Primary account: {primary_email if primary_email else 'Not configured'}")
    print(f"Backup account: {backup_email if backup_email else 'Not configured'}")
    print()
    
    if not primary_email:
        print("⚠️  Primary account not configured!")
        print("Please set X_EMAIL and X_PASSWORD in your .env file first.")
        return False
    
    if backup_email:
        print("✅ Backup account already configured")
        update = input("Do you want to update backup account credentials? (y/N): ").lower().strip()
        if update != 'y':
            return True
    
    print("\n📝 Setting up backup account...")
    print("This should be a DIFFERENT Twitter account from your primary one.")
    print()
    
    # Get backup account credentials
    backup_email = input("Backup account email/username: ").strip()
    if not backup_email:
        print("❌ Email cannot be empty")
        return False
    
    backup_password = getpass.getpass("Backup account password: ").strip()
    if not backup_password:
        print("❌ Password cannot be empty")
        return False
    
    # Save to .env file
    env_file = ".env"
    try:
        set_key(env_file, "X_EMAIL_BACKUP", backup_email)
        set_key(env_file, "X_PASSWORD_BACKUP", backup_password)
        print(f"✅ Backup credentials saved to {env_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False

def test_setup():
    """Test the multi-account setup"""
    print("\n🧪 Testing multi-account setup...")
    
    try:
        from multi_account_scraper import MultiAccountScraper
        
        scraper = MultiAccountScraper()
        print(f"✅ Found {len(scraper.accounts)} configured account(s)")
        
        # Test initialization (headless)
        if scraper.initialize_accounts(headless=True):
            print("✅ Account initialization successful")
            
            # Test getting best account
            best_account = scraper.get_best_account()
            if best_account:
                print(f"✅ Best account available: {best_account.name}")
            else:
                print("⚠️  No accounts currently available")
            
            scraper.cleanup()
            return True
        else:
            print("❌ Account initialization failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    print("🚀 Multi-Account Twitter Scraper Setup")
    print()
    
    if setup_backup_credentials():
        print("\n" + "=" * 40)
        if test_setup():
            print("\n🎉 Setup complete! You can now use:")
            print("   python multi_account_scraper.py --url YOUR_LIST_URL")
            print("\nFor continuous monitoring:")
            print("   python multi_account_scraper.py --url YOUR_LIST_URL --interval 60")
        else:
            print("\n⚠️  Setup completed but testing failed.")
            print("You may need to run the scraper manually to complete login.")
    else:
        print("\n❌ Setup failed. Please try again.")

if __name__ == "__main__":
    main()