#!/usr/bin/env python3
"""
Test script for auto-login functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import auto_login
from dotenv import load_dotenv

def test_auto_login():
    """Test the auto-login function"""
    load_dotenv()
    
    email = os.getenv("X_EMAIL")
    password = os.getenv("X_PASSWORD")
    
    if not email or not password:
        print("Error: X_EMAIL and X_PASSWORD must be set in .env file")
        return False
    
    print(f"Testing auto-login with email: {email}")
    print("Starting auto-login test...")
    
    # Test auto-login without existing context (standalone mode)
    result = auto_login(existing_context=None)
    
    if result:
        print("✅ Auto-login test PASSED!")
        return True
    else:
        print("❌ Auto-login test FAILED!")
        return False

if __name__ == "__main__":
    success = test_auto_login()
    sys.exit(0 if success else 1)