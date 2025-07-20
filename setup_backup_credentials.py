#!/usr/bin/env python3
"""
Simple script to help set up backup account credentials in .env file
"""

import os
import getpass
from dotenv import load_dotenv, set_key

def setup_backup_credentials():
    """Interactive setup for backup account credentials"""
    print("🔧 Backup Account Credentials Setup")
    print("=" * 40)
    
    # Load existing environment
    load_dotenv()
    
    # Check current status
    primary_email = os.getenv("X_EMAIL")
    backup_email = os.getenv("X_EMAIL_BACKUP")
    
    print("Current configuration:")
    print(f"  Primary account: {primary_email if primary_email else 'Not configured'}")
    print(f"  Backup account:  {backup_email if backup_email else 'Not configured'}")
    print()
    
    if not primary_email:
        print("⚠️  Primary account not configured!")
        print("Please set X_EMAIL and X_PASSWORD in your .env file first.")
        print()
        setup_primary = input("Would you like to set up primary account now? (y/N): ").lower().strip()
        
        if setup_primary == 'y':
            primary_email = input("Primary account email/username: ").strip()
            if primary_email:
                primary_password = getpass.getpass("Primary account password: ").strip()
                if primary_password:
                    set_key(".env", "X_EMAIL", primary_email)
                    set_key(".env", "X_PASSWORD", primary_password)
                    print("✅ Primary account credentials saved")
                else:
                    print("❌ Password cannot be empty")
                    return False
            else:
                print("❌ Email cannot be empty")
                return False
        else:
            return False
    
    # Setup backup account
    if backup_email:
        print(f"✅ Backup account already configured: {backup_email}")
        update = input("Do you want to update backup account credentials? (y/N): ").lower().strip()
        if update != 'y':
            return True
    
    print("\n📝 Setting up backup account...")
    print("This should be a DIFFERENT Twitter account from your primary one.")
    print("Using the same account for both primary and backup won't help with rate limits.")
    print()
    
    # Get backup credentials
    backup_email = input("Backup account email/username: ").strip()
    if not backup_email:
        print("❌ Email cannot be empty")
        return False
    
    # Check if it's the same as primary
    if backup_email == primary_email:
        print("⚠️  Warning: Backup email is the same as primary!")
        confirm = input("This won't help with rate limits. Continue anyway? (y/N): ").lower().strip()
        if confirm != 'y':
            return False
    
    backup_password = getpass.getpass("Backup account password: ").strip()
    if not backup_password:
        print("❌ Password cannot be empty")
        return False
    
    # Save to .env file
    try:
        set_key(".env", "X_EMAIL_BACKUP", backup_email)
        set_key(".env", "X_PASSWORD_BACKUP", backup_password)
        print("✅ Backup credentials saved to .env file")
        
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Test the setup: python test_backup_switching.py")
        print("2. Run the scraper: python scraper.py --url YOUR_LIST_URL")
        print("\nThe scraper will automatically switch to the backup account")
        print("when the primary account hits rate limits.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False

def main():
    if setup_backup_credentials():
        print("\n✅ Backup account setup completed successfully!")
    else:
        print("\n❌ Setup failed. Please try again.")

if __name__ == "__main__":
    main()