#!/usr/bin/env python3
"""
Test script to debug backup account scraping issues
"""
import os
import sys
import time
import requests
import json
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

# Decodo proxy configuration (same as working test)
DECODO_USERNAME = os.getenv("DECODO_USERNAME", "sp5v4mxxv9")
DECODO_PASSWORD = os.getenv("DECODO_PASSWORD", "ff9tilito8IEq9E_1Y")
DECODO_HOST = os.getenv("DECODO_HOST", "isp.decodo.com")
DECODO_PORTS = [10001, 10002, 10003]

# Session file path
SESSION_FILE_BACKUP = "x_session_backup.json"

def check_decodo_connection(port_index=0):
    """Check if Decodo proxy is working and return current IP (same as working test)"""
    try:
        # Test direct connection first
        direct_response = requests.get('https://httpbin.org/ip', timeout=10)
        direct_ip = direct_response.json().get('origin', 'Unknown')
        
        # Test Decodo proxy connection
        port = DECODO_PORTS[port_index]
        proxy_url = f"http://{DECODO_USERNAME}:{DECODO_PASSWORD}@{DECODO_HOST}:{port}"
        decodo_proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        proxy_response = requests.get('https://httpbin.org/ip', proxies=decodo_proxies, timeout=15)
        proxy_ip = proxy_response.json().get('origin', 'Unknown')
        
        print(f"🌐 DIRECT IP: {direct_ip}")
        print(f"🔗 DECODO PROXY IP (Port {port}): {proxy_ip}")
        
        if direct_ip != proxy_ip:
            print(f"✅ DECODO: Proxy is working correctly on port {port}")
            return True, proxy_ip
        else:
            print(f"❌ DECODO: Proxy may not be working on port {port} (same IP)")
            return False, direct_ip
            
    except Exception as e:
        print(f"❌ DECODO: Connection check failed for port {DECODO_PORTS[port_index]}: {e}")
        return False, None

def load_cookies(context, session_file=None):
    """Load cookies from specified file or default session file"""
    file_path = session_file or SESSION_FILE_BACKUP
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        return True
    return False

def create_backup_browser_with_proxy(pw_runtime, port_index=0):
    """Create backup browser with proxy (simplified version)"""
    try:
        port = DECODO_PORTS[port_index]
        proxy_config = {
            "server": f"http://{DECODO_HOST}:{port}",
            "username": DECODO_USERNAME,
            "password": DECODO_PASSWORD
        }
        
        browser = pw_runtime.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        context = browser.new_context(
            proxy=proxy_config,
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            ignore_https_errors=True
        )
        
        return browser, context
        
    except Exception as e:
        print(f"❌ Failed to create proxy browser: {e}")
        return None, None

def create_standard_backup_browser(pw_runtime, port_index=0):
    """Create standard backup browser without proxy"""
    try:
        browser = pw_runtime.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        )
        
        return browser, context
        
    except Exception as e:
        print(f"❌ Failed to create standard browser: {e}")
        return None, None

def test_backup_account_scraping():
    """Test backup account scraping step by step"""
    load_dotenv()
    
    backup_email = os.getenv("X_EMAIL_BACKUP")
    backup_password = os.getenv("X_PASSWORD_BACKUP")
    
    print("🧪 BACKUP ACCOUNT TEST")
    print("=" * 50)
    print(f"Backup email: {backup_email}")
    print(f"Session file: {SESSION_FILE_BACKUP}")
    print(f"Session exists: {os.path.exists(SESSION_FILE_BACKUP)}")
    
    if not backup_email or not backup_password:
        print("❌ Backup account credentials not found in .env")
        return False
    
    pw_runtime = None
    browser_backup = None
    context_backup = None
    
    try:
        pw_runtime = sync_playwright().start()
        
        # Test 1: Check proxy connections
        print("\n🔗 STEP 1: Testing proxy connections")
        working_ports = []
        for i, port in enumerate(DECODO_PORTS):
            print(f"Testing port {port}...")
            try:
                proxy_working, proxy_ip = check_decodo_connection(i)
                if proxy_working:
                    working_ports.append((i, port, proxy_ip))
                    print(f"✅ Port {port}: Working - IP {proxy_ip}")
                else:
                    print(f"❌ Port {port}: Failed")
            except Exception as e:
                print(f"❌ Port {port}: Error - {e}")
        
        if not working_ports:
            print("❌ No working proxy ports found")
            return False
        
        print(f"✅ Found {len(working_ports)} working proxy ports")
        
        # Test 2: Create backup browser with best proxy
        print("\n🔧 STEP 2: Creating backup browser")
        best_port_index = working_ports[0][0]  # Use first working port
        best_port = working_ports[0][1]
        best_ip = working_ports[0][2]
        
        print(f"Using port {best_port} (IP: {best_ip})")
        
        browser_backup, context_backup = create_backup_browser_with_proxy(
            pw_runtime, 
            port_index=best_port_index
        )
        
        if not browser_backup or not context_backup:
            print("❌ Failed to create backup browser with proxy")
            print("🔄 Trying standard browser...")
            browser_backup, context_backup = create_standard_backup_browser(pw_runtime, best_port_index)
            
            if not browser_backup or not context_backup:
                print("❌ Failed to create standard backup browser")
                return False
        
        print("✅ Backup browser created successfully")
        
        # Test 3: Check session
        print("\n🔑 STEP 3: Checking backup account session")
        session_loaded = load_cookies(context_backup, SESSION_FILE_BACKUP)
        
        if session_loaded:
            print("✅ Backup session loaded successfully")
        else:
            print("❌ No backup session found")
            print("⚠️  Skipping login test - session required for this test")
            print("💡 Run the main scraper first to create a backup session")
            return False
        
        # Test 4: Test basic page navigation
        print("\n🌐 STEP 4: Testing basic page navigation")
        page = context_backup.new_page()
        
        try:
            print("Navigating to X.com home...")
            page.goto("https://x.com/home", timeout=30000)
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            
            title = page.title()
            print(f"✅ Page loaded successfully: {title}")
            
            # Check if we're logged in
            if page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']"):
                print("✅ Login verification successful")
            else:
                print("⚠️  Login verification unclear")
            
        except Exception as e:
            print(f"❌ Basic navigation failed: {e}")
            return False
        finally:
            page.close()
        
        # Test 5: Test list access
        print("\n📋 STEP 5: Testing list access")
        list_url = "https://x.com/i/lists/1919380958723158457"
        page = context_backup.new_page()
        
        try:
            print(f"Navigating to list: {list_url}")
            page.goto(list_url, timeout=30000)
            
            # Try different selectors to see what loads
            selectors_to_try = [
                "[data-testid='cellInnerDiv']",
                "[data-testid='tweet']",
                "[role='main']",
                "article",
                "[data-testid='primaryColumn']"
            ]
            
            found_selector = None
            for selector in selectors_to_try:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    found_selector = selector
                    print(f"✅ Found selector: {selector}")
                    break
                except:
                    print(f"❌ Selector not found: {selector}")
            
            if found_selector:
                print("✅ List page loaded with content")
                
                # Get page content for debugging
                content = page.content()
                print(f"Page content length: {len(content)} characters")
                
                # Check for rate limit indicators
                if "rate limit" in content.lower():
                    print("⚠️  Rate limit detected in page content")
                elif "something went wrong" in content.lower():
                    print("⚠️  Error message detected in page content")
                elif "try again" in content.lower():
                    print("⚠️  Retry message detected in page content")
                else:
                    print("✅ No obvious error messages in page content")
                
            else:
                print("❌ No content selectors found - page may not have loaded properly")
                
                # Save page content for debugging
                content = page.content()
                debug_file = f"backup_debug_{int(time.time())}.html"
                with open(debug_file, 'w') as f:
                    f.write(content)
                print(f"📄 Page content saved to {debug_file}")
                
        except Exception as e:
            print(f"❌ List access failed: {e}")
            
            # Save page content for debugging
            try:
                content = page.content()
                debug_file = f"backup_error_{int(time.time())}.html"
                with open(debug_file, 'w') as f:
                    f.write(content)
                print(f"📄 Error page content saved to {debug_file}")
            except:
                pass
                
            return False
        finally:
            page.close()
        
        # Test 6: Check for tweets on the page
        print("\n🔍 STEP 6: Looking for tweets on the page")
        page = context_backup.new_page()
        
        try:
            print(f"Navigating to list: {list_url}")
            page.goto(list_url, timeout=30000)
            
            # Wait for any content to load
            page.wait_for_timeout(3000)
            
            # Look for tweet elements
            tweet_selectors = [
                "[data-testid='tweet']",
                "article[data-testid='tweet']",
                "[data-testid='cellInnerDiv']"
            ]
            
            tweets_found = 0
            for selector in tweet_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        tweets_found = len(elements)
                        print(f"✅ Found {tweets_found} tweets using selector: {selector}")
                        break
                except:
                    continue
            
            if tweets_found > 0:
                print(f"🎉 SUCCESS: Backup account can access list and see {tweets_found} tweets!")
                return True
            else:
                print("⚠️  No tweets found on the page")
                
                # Check page content for clues
                content = page.content()
                if "rate limit" in content.lower():
                    print("❌ Rate limit detected in page content")
                elif "something went wrong" in content.lower():
                    print("❌ Error message detected in page content")
                elif "try again" in content.lower():
                    print("❌ Retry message detected in page content")
                elif len(content) < 1000:
                    print("❌ Page content is very short - may not have loaded properly")
                else:
                    print("⚠️  Page loaded but no tweets visible")
                
                # Save page content for analysis
                debug_file = f"backup_no_tweets_{int(time.time())}.html"
                with open(debug_file, 'w') as f:
                    f.write(content)
                print(f"📄 Page content saved to {debug_file} for analysis")
                
                return False
                
        except Exception as e:
            print(f"❌ Tweet check failed: {e}")
            return False
        finally:
            page.close()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Cleanup
        if browser_backup:
            try:
                browser_backup.close()
            except:
                pass
        if pw_runtime:
            try:
                pw_runtime.stop()
            except:
                pass

if __name__ == "__main__":
    print("🧪 Starting backup account scraping test...")
    success = test_backup_account_scraping()
    
    if success:
        print("\n🎉 Backup account test PASSED!")
    else:
        print("\n❌ Backup account test FAILED!")
    
    print("\nTest completed.")