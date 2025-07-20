#!/usr/bin/env python3
"""
Multi-account Twitter scraper with automatic account switching for rate limit mitigation.
This is a simplified version that focuses on the core functionality.
"""

import json
import time
import os
import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import sys

# Configuration
DATA_DIR = os.getenv("DATA_DIR", ".")
SESSION_FILE_PRIMARY = os.path.join(DATA_DIR, "x_session_primary.json")
SESSION_FILE_BACKUP = os.path.join(DATA_DIR, "x_session_backup.json")
TWEETS_FILE = os.path.join(DATA_DIR, "tweets_multi.json")

class TwitterAccount:
    def __init__(self, email, password, session_file, name):
        self.email = email
        self.password = password
        self.session_file = session_file
        self.name = name
        self.pw = None
        self.browser = None
        self.context = None
        self.is_active = False
        self.last_used = None
        self.rate_limited_until = None

    def initialize(self, headless=True):
        """Initialize browser and context for this account"""
        try:
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch(headless=headless)
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Try to load existing session
            if self.load_session():
                print(f"✓ Loaded existing session for {self.name}")
                self.is_active = True
                return True
            else:
                print(f"No session found for {self.name}, attempting login...")
                if self.login():
                    self.is_active = True
                    return True
                else:
                    print(f"✗ Failed to login {self.name}")
                    self.cleanup()
                    return False
                    
        except Exception as e:
            print(f"Error initializing {self.name}: {e}")
            self.cleanup()
            return False

    def load_session(self):
        """Load cookies from session file"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    cookies = json.load(f)
                self.context.add_cookies(cookies)
                return True
            except Exception as e:
                print(f"Error loading session for {self.name}: {e}")
        return False

    def save_session(self):
        """Save cookies to session file"""
        try:
            cookies = self.context.cookies()
            with open(self.session_file, "w") as f:
                json.dump(cookies, f)
            print(f"✓ Session saved for {self.name}")
        except Exception as e:
            print(f"Error saving session for {self.name}: {e}")

    def login(self):
        """Perform automatic login"""
        if not self.email or not self.password:
            print(f"Missing credentials for {self.name}")
            return False

        try:
            page = self.context.new_page()
            print(f"Logging in {self.name}...")
            
            page.goto("https://x.com/login", timeout=30000)
            
            # Fill email
            email_selectors = [
                'input[name="text"]',
                'input[autocomplete="username"]',
                'input[data-testid="ocfEnterTextTextInput"]'
            ]
            
            for selector in email_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, self.email)
                    break
                except:
                    continue
            
            # Click Next
            time.sleep(2)
            try:
                page.locator('text="Next"').first.click()
            except:
                page.locator('[data-testid="LoginForm_Login_Button"]').click()
            
            time.sleep(3)
            
            # Fill password
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[autocomplete="current-password"]'
            ]
            
            for selector in password_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, self.password)
                    break
                except:
                    continue
            
            # Click Login
            time.sleep(2)
            try:
                page.locator('text="Log in"').first.click()
            except:
                page.locator('[data-testid="LoginForm_Login_Button"]').click()
            
            # Wait for successful login
            try:
                page.wait_for_url("**/home", timeout=15000)
                if page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']"):
                    print(f"✓ Successfully logged in {self.name}")
                    self.save_session()
                    page.close()
                    return True
            except PlaywrightTimeoutError:
                print(f"✗ Login timeout for {self.name}")
            
            page.close()
            return False
            
        except Exception as e:
            print(f"Login error for {self.name}: {e}")
            return False

    def scrape_tweets(self, list_url, limit=10):
        """Scrape tweets using this account"""
        if not self.is_active:
            return [], None
        
        # Check if account is rate limited
        if self.rate_limited_until and time.time() < self.rate_limited_until:
            remaining = int(self.rate_limited_until - time.time())
            print(f"⏳ {self.name} is rate limited for {remaining} more seconds")
            return [], None

        try:
            page = self.context.new_page()
            tweets = []
            
            # Set up XHR monitoring
            xhr_responses = []
            def handle_response(response):
                if response.request.resource_type == "xhr" and "ListLatestTweetsTimeline" in response.url:
                    xhr_responses.append(response)
            
            page.on("response", handle_response)
            
            print(f"🔍 Scraping with {self.name}: {list_url}")
            page.goto(list_url, timeout=30000)
            page.wait_for_selector("[data-testid='cellInnerDiv']", timeout=15000)
            
            # Scroll a bit to trigger more requests
            for i in range(2):
                page.mouse.wheel(0, 1000)
                time.sleep(1)
            
            # Process XHR responses
            for xhr in xhr_responses:
                try:
                    data = xhr.json()
                    instructions = (
                        data.get("data", {})
                        .get("list", {})
                        .get("tweets_timeline", {})
                        .get("timeline", {})
                        .get("instructions", [])
                    )
                    
                    for instr in instructions:
                        if "entries" in instr:
                            for entry in instr["entries"]:
                                if entry["entryId"].startswith("tweet-"):
                                    try:
                                        tweet_content = entry["content"]["itemContent"]["tweet_results"]["result"]
                                        tweet_id = tweet_content.get("rest_id")
                                        legacy = tweet_content.get("legacy", {})
                                        text = legacy.get("full_text")
                                        
                                        if tweet_id and text:
                                            # Extract basic user info
                                            user_data = tweet_content.get("core", {}).get("user_results", {}).get("result", {})
                                            username = user_data.get("legacy", {}).get("screen_name", "Unknown")
                                            
                                            tweet = {
                                                "id": tweet_id,
                                                "text": text,
                                                "username": username,
                                                "created_at": legacy.get("created_at"),
                                                "scraped_by": self.name,
                                                "scraped_at": datetime.datetime.now().isoformat()
                                            }
                                            tweets.append(tweet)
                                            
                                            if len(tweets) >= limit:
                                                break
                                    except KeyError:
                                        continue
                                        
                        if len(tweets) >= limit:
                            break
                            
                except Exception as e:
                    print(f"Error processing XHR for {self.name}: {e}")
            
            page.close()
            self.last_used = time.time()
            
            if tweets:
                print(f"✓ {self.name} found {len(tweets)} tweets")
            else:
                print(f"⚠️  {self.name} found no tweets (possible rate limit)")
                # Set rate limit cooldown
                self.rate_limited_until = time.time() + 300  # 5 minutes
            
            return tweets, tweets[0]["id"] if tweets else None
            
        except Exception as e:
            print(f"Scraping error with {self.name}: {e}")
            if "rate limit" in str(e).lower() or "429" in str(e):
                self.rate_limited_until = time.time() + 600  # 10 minutes
            return [], None

    def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.browser:
                self.browser.close()
            if self.pw:
                self.pw.stop()
        except:
            pass
        self.is_active = False

class MultiAccountScraper:
    def __init__(self):
        load_dotenv()
        self.accounts = []
        self.setup_accounts()
        
    def setup_accounts(self):
        """Initialize primary and backup accounts"""
        # Primary account
        primary_email = os.getenv("X_EMAIL")
        primary_password = os.getenv("X_PASSWORD")
        if primary_email and primary_password:
            primary = TwitterAccount(primary_email, primary_password, SESSION_FILE_PRIMARY, "Primary")
            self.accounts.append(primary)
        
        # Backup account
        backup_email = os.getenv("X_EMAIL_BACKUP")
        backup_password = os.getenv("X_PASSWORD_BACKUP")
        if backup_email and backup_password:
            backup = TwitterAccount(backup_email, backup_password, SESSION_FILE_BACKUP, "Backup")
            self.accounts.append(backup)
        
        if not self.accounts:
            print("❌ No account credentials found in environment variables")
            sys.exit(1)
        
        print(f"📱 Found {len(self.accounts)} account(s) configured")

    def initialize_accounts(self, headless=True):
        """Initialize all accounts"""
        active_count = 0
        for account in self.accounts:
            if account.initialize(headless):
                active_count += 1
        
        print(f"✅ {active_count}/{len(self.accounts)} accounts ready")
        return active_count > 0

    def get_best_account(self):
        """Get the best available account (not rate limited, least recently used)"""
        available = [acc for acc in self.accounts if acc.is_active and 
                    (not acc.rate_limited_until or time.time() >= acc.rate_limited_until)]
        
        if not available:
            return None
        
        # Return least recently used account
        return min(available, key=lambda x: x.last_used or 0)

    def scrape_with_rotation(self, list_url, limit=10):
        """Scrape tweets with automatic account rotation"""
        account = self.get_best_account()
        if not account:
            print("⚠️  No accounts available (all rate limited)")
            return [], None
        
        return account.scrape_tweets(list_url, limit)

    def monitor(self, list_url, interval=60, limit=10):
        """Monitor with account rotation"""
        print(f"🚀 Starting multi-account monitoring of {list_url}")
        print(f"⏱️  Check interval: {interval} seconds")
        
        all_tweets = []
        
        try:
            while True:
                print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Checking for new tweets...")
                
                tweets, newest_id = self.scrape_with_rotation(list_url, limit)
                
                if tweets:
                    # Remove duplicates
                    existing_ids = {t["id"] for t in all_tweets}
                    new_tweets = [t for t in tweets if t["id"] not in existing_ids]
                    
                    if new_tweets:
                        all_tweets.extend(new_tweets)
                        all_tweets.sort(key=lambda x: int(x["id"]), reverse=True)
                        
                        # Save to file
                        with open(TWEETS_FILE, "w") as f:
                            json.dump({
                                "tweets": all_tweets,
                                "last_updated": datetime.datetime.now().isoformat(),
                                "total_count": len(all_tweets)
                            }, f, indent=2)
                        
                        print(f"💾 Saved {len(new_tweets)} new tweets (total: {len(all_tweets)})")
                        
                        for tweet in new_tweets:
                            print(f"  @{tweet['username']}: {tweet['text'][:60]}...")
                    else:
                        print("📭 No new tweets found")
                else:
                    print("⏳ Waiting for rate limits to reset...")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up all accounts"""
        for account in self.accounts:
            account.cleanup()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-account Twitter scraper")
    parser.add_argument("--url", default="https://x.com/i/lists/1919380958723158457", 
                       help="Twitter list URL to monitor")
    parser.add_argument("--interval", type=int, default=60, 
                       help="Check interval in seconds")
    parser.add_argument("--limit", type=int, default=10, 
                       help="Max tweets per check")
    parser.add_argument("--visible", action="store_true", 
                       help="Show browser windows")
    parser.add_argument("--once", action="store_true", 
                       help="Run once and exit")
    
    args = parser.parse_args()
    
    scraper = MultiAccountScraper()
    
    if not scraper.initialize_accounts(headless=not args.visible):
        print("❌ Failed to initialize accounts")
        sys.exit(1)
    
    if args.once:
        tweets, _ = scraper.scrape_with_rotation(args.url, args.limit)
        print(f"Found {len(tweets)} tweets")
        for tweet in tweets:
            print(f"@{tweet['username']}: {tweet['text'][:80]}...")
    else:
        scraper.monitor(args.url, args.interval, args.limit)

if __name__ == "__main__":
    main()