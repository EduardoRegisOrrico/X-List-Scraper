#!/usr/bin/env python3
"""
Account health checker to diagnose rate limiting issues
"""
import os
import time
import json
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

def check_account_health(account_type="primary"):
    """Check if an account is healthy or rate limited"""
    
    if account_type == "primary":
        email = os.getenv("X_EMAIL")
        session_file = "x_session.json"
    else:
        email = os.getenv("X_EMAIL_BACKUP")
        session_file = "x_session_backup.json"
    
    print(f"\n🏥 ACCOUNT HEALTH CHECK: {account_type.upper()} ({email})")
    print("=" * 60)
    
    if not os.path.exists(session_file):
        print(f"❌ No session file found: {session_file}")
        return False
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            
            # Load session
            with open(session_file, 'r') as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
            
            page = context.new_page()
            
            # Test 1: Basic login check
            print("🔍 Test 1: Basic login verification")
            try:
                page.goto("https://x.com/home", timeout=15000)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                
                if page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']"):
                    print("✅ Login verified - account is logged in")
                else:
                    print("❌ Login failed - session may be expired")
                    return False
            except Exception as e:
                print(f"❌ Login test failed: {e}")
                return False
            
            # Test 2: Timeline access
            print("\n🔍 Test 2: Timeline access")
            try:
                page.goto("https://x.com/home", timeout=15000)
                page.wait_for_selector("[data-testid='tweet']", timeout=10000)
                tweets = page.query_selector_all("[data-testid='tweet']")
                print(f"✅ Timeline accessible - found {len(tweets)} tweets")
            except Exception as e:
                print(f"⚠️  Timeline access limited: {e}")
            
            # Test 3: List access (the critical test)
            print("\n🔍 Test 3: List access (critical)")
            list_url = "https://x.com/i/lists/1919380958723158457"
            try:
                page.goto(list_url, timeout=15000)
                
                # Wait for content with shorter timeout
                try:
                    page.wait_for_selector("[data-testid='cellInnerDiv']", timeout=8000)
                    list_tweets = page.query_selector_all("[data-testid='tweet']")
                    
                    if len(list_tweets) > 0:
                        print(f"✅ List access HEALTHY - found {len(list_tweets)} tweets")
                        return True
                    else:
                        print("⚠️  List loaded but no tweets visible")
                        
                        # Check for rate limit indicators
                        content = page.content()
                        if "rate limit" in content.lower():
                            print("❌ RATE LIMITED - explicit rate limit message")
                            return False
                        elif len(content) < 5000:
                            print("❌ RATE LIMITED - minimal content loaded")
                            return False
                        else:
                            print("⚠️  Unknown issue - content loaded but no tweets")
                            return False
                            
                except Exception as selector_error:
                    print(f"❌ RATE LIMITED - selector timeout: {selector_error}")
                    
                    # Save page for analysis
                    content = page.content()
                    debug_file = f"{account_type}_health_check_{int(time.time())}.html"
                    with open(debug_file, 'w') as f:
                        f.write(content)
                    print(f"📄 Page saved for analysis: {debug_file}")
                    
                    return False
                    
            except Exception as e:
                print(f"❌ RATE LIMITED - page load failed: {e}")
                return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    finally:
        try:
            browser.close()
        except:
            pass

def get_account_status_summary():
    """Get status of both accounts"""
    print("\n" + "=" * 80)
    print("🏥 COMPREHENSIVE ACCOUNT HEALTH REPORT")
    print("=" * 80)
    
    primary_healthy = check_account_health("primary")
    backup_healthy = check_account_health("backup")
    
    print("\n📊 SUMMARY:")
    print(f"Primary Account: {'✅ HEALTHY' if primary_healthy else '❌ RATE LIMITED'}")
    print(f"Backup Account:  {'✅ HEALTHY' if backup_healthy else '❌ RATE LIMITED'}")
    
    if not primary_healthy and not backup_healthy:
        print("\n🚨 CRITICAL: Both accounts are rate limited!")
        print("💡 Recommendations:")
        print("   1. Wait 24-48 hours before resuming")
        print("   2. Consider using different accounts")
        print("   3. Reduce scraping frequency")
        print("   4. Check if accounts are shadowbanned")
    elif not primary_healthy:
        print("\n⚠️  Primary account rate limited - backup account available")
    elif not backup_healthy:
        print("\n⚠️  Backup account rate limited - primary account available")
    else:
        print("\n✅ Both accounts are healthy!")
    
    return primary_healthy, backup_healthy

if __name__ == "__main__":
    get_account_status_summary()