#!/usr/bin/env python3
"""
Test script for Tor-enabled backup account login
"""

import sys
import os
from scraper import switch_to_backup_account, check_tor_connection, get_new_tor_circuit
from playwright.sync_api import sync_playwright

def test_tor_backup_login():
    """Test the backup account login with Tor"""
    print("=== Testing Tor-enabled Backup Account Login ===")
    
    # Check Tor connection first
    print("\n1. Testing Tor connection...")
    tor_working, tor_ip = check_tor_connection()
    if not tor_working:
        print("❌ Tor is not working. Please check your Tor setup.")
        return False
    
    print(f"✅ Tor is working. Current IP: {tor_ip}")
    
    # Get new circuit
    print("\n2. Getting new Tor circuit...")
    if get_new_tor_circuit():
        print("✅ New Tor circuit obtained")
        # Check new IP
        _, new_ip = check_tor_connection()
        print(f"New IP: {new_ip}")
    else:
        print("❌ Failed to get new Tor circuit")
    
    # Test backup account initialization
    print("\n3. Testing backup account initialization with Tor...")
    try:
        with sync_playwright() as pw:
            browser_backup, context_backup = switch_to_backup_account(pw)
            
            if browser_backup and context_backup:
                print("✅ Backup account browser created successfully")
                
                # Test basic page navigation
                print("\n4. Testing page navigation...")
                page = context_backup.new_page()
                try:
                    page.goto("https://httpbin.org/ip", timeout=30000)
                    content = page.content()
                    if "origin" in content:
                        print("✅ Page navigation successful")
                        print(f"Page content preview: {content[:200]}...")
                    else:
                        print("⚠️  Page loaded but content unexpected")
                except Exception as e:
                    print(f"❌ Page navigation failed: {e}")
                finally:
                    page.close()
                
                browser_backup.close()
                return True
            else:
                print("❌ Failed to create backup account browser")
                return False
                
    except Exception as e:
        print(f"❌ Error during backup account test: {e}")
        return False

if __name__ == "__main__":
    success = test_tor_backup_login()
    sys.exit(0 if success else 1)