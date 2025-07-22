#!/usr/bin/env python3
"""
Test script for multi-account functionality
"""

import time
from multi_account_scraper import MultiAccountScraper

def test_basic_functionality():
    """Test basic multi-account scraping"""
    print("🧪 Testing Multi-Account Scraper")
    print("=" * 40)
    
    # Initialize scraper
    scraper = MultiAccountScraper()
    
    if not scraper.accounts:
        print("❌ No accounts configured")
        return False
    
    print(f"📱 Testing with {len(scraper.accounts)} account(s)")
    
    # Initialize accounts
    if not scraper.initialize_accounts(headless=True):
        print("❌ Failed to initialize accounts")
        return False
    
    # Test scraping
    test_url = "https://x.com/i/lists/1919380958723158457"  # Default list
    print(f"\n🔍 Testing scrape of: {test_url}")
    
    tweets, newest_id = scraper.scrape_with_rotation(test_url, limit=5)
    
    if tweets:
        print(f"✅ Successfully scraped {len(tweets)} tweets")
        for i, tweet in enumerate(tweets[:3], 1):
            print(f"  {i}. @{tweet['username']}: {tweet['text'][:50]}...")
        if len(tweets) > 3:
            print(f"  ... and {len(tweets) - 3} more")
    else:
        print("⚠️  No tweets found (might be rate limited or empty list)")
    
    # Test account rotation
    print(f"\n🔄 Testing account rotation...")
    for i in range(3):
        best_account = scraper.get_best_account()
        if best_account:
            print(f"  Round {i+1}: Using {best_account.name}")
            # Simulate rate limiting the account
            best_account.rate_limited_until = time.time() + 60
        else:
            print(f"  Round {i+1}: No accounts available")
        time.sleep(1)
    
    # Cleanup
    scraper.cleanup()
    print("\n✅ Test completed")
    return True

def test_rate_limit_handling():
    """Test rate limit handling"""
    print("\n🚦 Testing Rate Limit Handling")
    print("=" * 30)
    
    scraper = MultiAccountScraper()
    
    if not scraper.initialize_accounts(headless=True):
        print("❌ Failed to initialize accounts")
        return False
    
    # Simulate rate limiting all accounts
    for account in scraper.accounts:
        account.rate_limited_until = time.time() + 30  # 30 seconds
        print(f"⏳ Simulated rate limit for {account.name}")
    
    # Try to get best account
    best = scraper.get_best_account()
    if best:
        print("❌ Should not have found available account")
    else:
        print("✅ Correctly identified no available accounts")
    
    # Remove rate limits
    for account in scraper.accounts:
        account.rate_limited_until = None
        print(f"✅ Removed rate limit for {account.name}")
    
    # Try again
    best = scraper.get_best_account()
    if best:
        print(f"✅ Found available account: {best.name}")
    else:
        print("❌ Should have found available account")
    
    scraper.cleanup()
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        test_rate_limit_handling()
    else:
        print("\n❌ Basic functionality test failed")
        print("Make sure you have:")
        print("1. X_EMAIL and X_PASSWORD in .env (primary account)")
        print("2. X_EMAIL_BACKUP and X_PASSWORD_BACKUP in .env (backup account)")
        print("3. Valid Twitter accounts that can access the test list")