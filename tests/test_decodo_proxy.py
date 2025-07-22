#!/usr/bin/env python3
"""
Test script to verify Decodo proxy functionality with comprehensive logging
"""
import requests
import time
import os
import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Decodo proxy configuration from environment variables
DECODO_USERNAME = os.getenv("DECODO_USERNAME", "sp5v4mxxv9")
DECODO_PASSWORD = os.getenv("DECODO_PASSWORD", "ff9tilito8IEq9E_1Y")
DECODO_HOST = os.getenv("DECODO_HOST", "isp.decodo.com")
DECODO_PORTS_STR = os.getenv("DECODO_PORTS", "10001,10002,10003")
DECODO_PORTS = [int(port.strip()) for port in DECODO_PORTS_STR.split(",")]

# Logging configuration
def setup_logging():
    """Setup comprehensive logging for the test with fallback options"""
    handlers = []
    log_file_path = None
    
    # Try to create log file in multiple locations
    possible_log_dirs = [
        os.path.join(os.path.dirname(__file__), '..', 'logs'),  # XScraper/logs
        os.path.join(os.path.dirname(__file__), 'logs'),        # tests/logs
        os.path.join(os.getcwd(), 'logs'),                      # current directory/logs
        '/tmp'                                                   # fallback to /tmp
    ]
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for log_dir in possible_log_dirs:
        try:
            # Create directory if it doesn't exist
            os.makedirs(log_dir, exist_ok=True)
            
            # Test if we can write to this directory
            log_file_path = os.path.join(log_dir, f'decodo_proxy_test_{timestamp}.log')
            
            # Try to create and write to the file
            with open(log_file_path, 'w') as test_file:
                test_file.write("# Decodo Proxy Test Log\n")
            
            # If successful, add file handler
            handlers.append(logging.FileHandler(log_file_path))
            print(f"📝 Log file created: {log_file_path}")
            break
            
        except (PermissionError, OSError) as e:
            print(f"⚠️  Cannot create log in {log_dir}: {e}")
            continue
    
    # Always add console handler
    handlers.append(logging.StreamHandler())
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"=== DECODO PROXY TEST STARTED ===")
    
    if log_file_path:
        logger.info(f"Log file: {log_file_path}")
    else:
        logger.warning("Could not create log file - logging to console only")
    
    logger.info(f"Test configuration:")
    logger.info(f"  - Host: {DECODO_HOST}")
    logger.info(f"  - Username: {DECODO_USERNAME}")
    logger.info(f"  - Ports: {DECODO_PORTS}")
    
    return logger

# Initialize logger with error handling
try:
    logger = setup_logging()
except Exception as e:
    # Fallback to console-only logging if setup fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)
    logger.warning(f"Logging setup failed, using console only: {e}")

def test_decodo_proxy():
    """Test all Decodo proxy ports"""
    logger.info("=== STARTING BASIC PROXY TEST ===")
    print("🔗 Testing Decodo Proxy Service")
    print("=" * 50)
    
    # Test direct connection first
    try:
        logger.info("Testing direct connection to httpbin.org/ip")
        print("🌐 Testing direct connection...")
        start_time = time.time()
        direct_response = requests.get('https://httpbin.org/ip', timeout=10)
        response_time = time.time() - start_time
        direct_ip = direct_response.json().get('origin', 'Unknown')
        
        logger.info(f"Direct connection successful - IP: {direct_ip}, Response time: {response_time:.2f}s")
        print(f"✅ Direct IP: {direct_ip}")
    except Exception as e:
        logger.error(f"Direct connection failed: {e}")
        print(f"❌ Direct connection failed: {e}")
        return False
    
    logger.info("Starting proxy connection tests")
    print("\n🔗 Testing proxy connections...")
    working_proxies = []
    
    for i, port in enumerate(DECODO_PORTS):
        logger.info(f"Testing proxy port {port} ({i+1}/{len(DECODO_PORTS)})")
        try:
            proxy_url = f"http://{DECODO_USERNAME}:{DECODO_PASSWORD}@{DECODO_HOST}:{port}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            print(f"Testing port {port}...")
            start_time = time.time()
            response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=15)
            response_time = time.time() - start_time
            proxy_ip = response.json().get('origin', 'Unknown')
            
            if proxy_ip != direct_ip:
                logger.info(f"Port {port} SUCCESS - IP: {proxy_ip}, Response time: {response_time:.2f}s")
                print(f"✅ Port {port}: Working - IP: {proxy_ip}")
                working_proxies.append((port, proxy_ip))
            else:
                logger.warning(f"Port {port} WARNING - Same IP as direct connection: {proxy_ip}")
                print(f"⚠️  Port {port}: Same IP as direct connection - {proxy_ip}")
                
        except requests.exceptions.Timeout:
            logger.error(f"Port {port} TIMEOUT - Request timed out after 15 seconds")
            print(f"❌ Port {port}: Timeout")
        except requests.exceptions.ConnectionError as ce:
            logger.error(f"Port {port} CONNECTION ERROR - {ce}")
            print(f"❌ Port {port}: Connection error")
        except Exception as e:
            logger.error(f"Port {port} FAILED - {e}")
            print(f"❌ Port {port}: Failed - {e}")
    
    # Log summary
    logger.info(f"BASIC PROXY TEST SUMMARY:")
    logger.info(f"  - Direct IP: {direct_ip}")
    logger.info(f"  - Working proxies: {len(working_proxies)}/{len(DECODO_PORTS)}")
    for port, ip in working_proxies:
        logger.info(f"    Port {port}: {ip}")
    
    print(f"\n📊 Summary:")
    print(f"Direct IP: {direct_ip}")
    print(f"Working proxies: {len(working_proxies)}/{len(DECODO_PORTS)}")
    
    if working_proxies:
        logger.info("Basic proxy test PASSED")
        print("✅ Decodo proxy service is working!")
        for port, ip in working_proxies:
            print(f"   Port {port}: {ip}")
        return True
    else:
        logger.error("Basic proxy test FAILED - No working proxies found")
        print("❌ No working proxies found!")
        return False

def test_x_access_through_proxy():
    """Test X.com access through Decodo proxy"""
    logger.info("=== STARTING X.COM ACCESS TEST ===")
    print("\n🐦 Testing X.com Access Through Proxy")
    print("=" * 50)
    
    # Test direct X.com access first
    try:
        logger.info("Testing direct X.com access")
        print("🌐 Testing direct X.com access...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        start_time = time.time()
        direct_response = requests.get('https://x.com', headers=headers, timeout=15)
        response_time = time.time() - start_time
        
        logger.info(f"Direct X.com access - Status: {direct_response.status_code}, Response time: {response_time:.2f}s")
        print(f"✅ Direct X.com access: Status {direct_response.status_code}")
        direct_accessible = direct_response.status_code == 200
    except requests.exceptions.Timeout:
        logger.error("Direct X.com access TIMEOUT - Request timed out after 15 seconds")
        print(f"❌ Direct X.com access failed: Timeout")
        direct_accessible = False
    except requests.exceptions.ConnectionError as ce:
        logger.error(f"Direct X.com access CONNECTION ERROR - {ce}")
        print(f"❌ Direct X.com access failed: Connection error")
        direct_accessible = False
    except Exception as e:
        logger.error(f"Direct X.com access FAILED - {e}")
        print(f"❌ Direct X.com access failed: {e}")
        direct_accessible = False
    
    logger.info("Starting X.com proxy access tests")
    print("\n🔗 Testing X.com access through proxy...")
    x_working_proxies = []
    
    for i, port in enumerate(DECODO_PORTS):
        logger.info(f"Testing X.com access through port {port} ({i+1}/{len(DECODO_PORTS)})")
        try:
            proxy_url = f"http://{DECODO_USERNAME}:{DECODO_PASSWORD}@{DECODO_HOST}:{port}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            print(f"Testing X.com through port {port}...")
            start_time = time.time()
            response = requests.get('https://x.com', proxies=proxies, headers=headers, timeout=20)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"Port {port} X.com SUCCESS - Status: {response.status_code}, Response time: {response_time:.2f}s")
                print(f"✅ Port {port}: X.com accessible - Status {response.status_code}")
                
                # Check if we can also access the login page
                logger.info(f"Port {port} - Testing login page access")
                login_start_time = time.time()
                login_response = requests.get('https://x.com/login', proxies=proxies, headers=headers, timeout=20)
                login_response_time = time.time() - login_start_time
                
                if login_response.status_code == 200:
                    logger.info(f"Port {port} LOGIN PAGE SUCCESS - Status: {login_response.status_code}, Response time: {login_response_time:.2f}s")
                    print(f"   ✅ Login page also accessible")
                    x_working_proxies.append(port)
                else:
                    logger.warning(f"Port {port} LOGIN PAGE WARNING - Status: {login_response.status_code}, Response time: {login_response_time:.2f}s")
                    print(f"   ⚠️  Login page returned status {login_response.status_code}")
            else:
                logger.warning(f"Port {port} X.com WARNING - Status: {response.status_code}, Response time: {response_time:.2f}s")
                print(f"⚠️  Port {port}: X.com returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error(f"Port {port} X.com TIMEOUT - Request timed out after 20 seconds")
            print(f"❌ Port {port}: Timeout accessing X.com")
        except requests.exceptions.ConnectionError as ce:
            logger.error(f"Port {port} X.com CONNECTION ERROR - {ce}")
            print(f"❌ Port {port}: Connection error accessing X.com")
        except Exception as e:
            logger.error(f"Port {port} X.com FAILED - {e}")
            print(f"❌ Port {port}: Failed to access X.com - {e}")
        
        # Small delay between requests to avoid overwhelming
        time.sleep(1)
    
    # Log X.com test summary
    logger.info(f"X.COM ACCESS TEST SUMMARY:")
    logger.info(f"  - Direct X.com access: {'SUCCESS' if direct_accessible else 'FAILED'}")
    logger.info(f"  - Working proxy ports for X.com: {len(x_working_proxies)}/{len(DECODO_PORTS)}")
    for port in x_working_proxies:
        logger.info(f"    Port {port}: Ready for X.com scraping")
    
    print(f"\n📊 X.com Access Summary:")
    print(f"Direct X.com access: {'✅ Working' if direct_accessible else '❌ Failed'}")
    print(f"Proxy ports working for X.com: {len(x_working_proxies)}/{len(DECODO_PORTS)}")
    
    if x_working_proxies:
        logger.info("X.com access test PASSED")
        print("✅ X.com is accessible through proxy!")
        for port in x_working_proxies:
            print(f"   Port {port}: Ready for scraping")
        return True
    else:
        logger.error("X.com access test FAILED - No working proxy ports for X.com")
        print("❌ X.com not accessible through any proxy port!")
        return False

def test_playwright_integration():
    """Test Decodo proxy integration with Playwright (similar to main scraper)"""
    logger.info("=== STARTING PLAYWRIGHT INTEGRATION TEST ===")
    print("\n🎭 Testing Playwright Integration with Decodo Proxy")
    print("=" * 50)
    
    try:
        from playwright.sync_api import sync_playwright
        logger.info("Playwright import successful")
    except ImportError as e:
        logger.error(f"Playwright import failed: {e}")
        print("❌ Playwright not available - skipping integration test")
        return False
    
    working_ports = []
    
    for i, port in enumerate(DECODO_PORTS):
        logger.info(f"Testing Playwright integration with port {port} ({i+1}/{len(DECODO_PORTS)})")
        browser = None
        try:
            proxy_config = {
                "server": f"http://{DECODO_HOST}:{port}",
                "username": DECODO_USERNAME,
                "password": DECODO_PASSWORD
            }
            
            with sync_playwright() as pw:
                print(f"Testing Playwright with port {port}...")
                start_time = time.time()
                
                # Launch browser with proxy configuration
                browser = pw.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                
                # Create context with proxy
                context = browser.new_context(
                    proxy=proxy_config,
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    ignore_https_errors=True
                )
                
                page = context.new_page()
                
                # Set longer timeout and try to load page
                page.set_default_timeout(30000)  # 30 seconds
                
                # Test basic page load
                logger.info(f"Port {port} - Attempting to load httpbin.org/ip")
                page.goto("https://httpbin.org/ip", wait_until="domcontentloaded", timeout=30000)
                
                # Wait a bit for content to load
                page.wait_for_timeout(2000)
                content = page.content()
                
                # Extract IP from the page content
                if '"origin"' in content:
                    import json
                    import re
                    ip_match = re.search(r'"origin":\s*"([^"]+)"', content)
                    if ip_match:
                        proxy_ip = ip_match.group(1)
                        setup_time = time.time() - start_time
                        
                        logger.info(f"Port {port} PLAYWRIGHT SUCCESS - IP: {proxy_ip}, Setup time: {setup_time:.2f}s")
                        print(f"✅ Port {port}: Playwright working - IP: {proxy_ip}")
                        working_ports.append(port)
                        
                        # Test X.com access with this working port
                        logger.info(f"Port {port} - Testing X.com access with Playwright")
                        try:
                            page.goto("https://x.com", wait_until="domcontentloaded", timeout=30000)
                            page.wait_for_timeout(3000)  # Wait for page to load
                            x_title = page.title()
                            logger.info(f"Port {port} - X.com loaded successfully, title: {x_title}")
                            print(f"   ✅ X.com also accessible via Playwright")
                        except Exception as x_error:
                            logger.warning(f"Port {port} - X.com test failed: {x_error}")
                            print(f"   ⚠️  X.com test failed: {str(x_error)[:50]}...")
                    else:
                        logger.warning(f"Port {port} PLAYWRIGHT WARNING - Could not extract IP from response")
                        print(f"⚠️  Port {port}: Could not extract IP from response")
                else:
                    logger.warning(f"Port {port} PLAYWRIGHT WARNING - Unexpected response format")
                    print(f"⚠️  Port {port}: Unexpected response format")
                    logger.debug(f"Port {port} - Page content preview: {content[:200]}...")
                
                # Clean up
                context.close()
                browser.close()
                browser = None
                
        except Exception as e:
            logger.error(f"Port {port} PLAYWRIGHT FAILED - {e}")
            print(f"❌ Port {port}: Playwright test failed - {e}")
            
            # Clean up on error
            if browser:
                try:
                    browser.close()
                except:
                    pass
        
        # Small delay between tests
        time.sleep(2)
    
    # Log Playwright test summary
    logger.info(f"PLAYWRIGHT INTEGRATION TEST SUMMARY:")
    logger.info(f"  - Working Playwright ports: {len(working_ports)}/{len(DECODO_PORTS)}")
    for port in working_ports:
        logger.info(f"    Port {port}: Ready for Playwright scraping")
    
    print(f"\n📊 Playwright Integration Summary:")
    print(f"Working Playwright ports: {len(working_ports)}/{len(DECODO_PORTS)}")
    
    if working_ports:
        logger.info("Playwright integration test PASSED")
        print("✅ Playwright integration working!")
        for port in working_ports:
            print(f"   Port {port}: Ready for browser scraping")
        return True
    else:
        logger.error("Playwright integration test FAILED - No working ports")
        print("❌ Playwright integration failed!")
        return False

def run_full_test():
    """Run comprehensive test suite for Decodo proxy"""
    logger.info("=== STARTING FULL TEST SUITE ===")
    test_start_time = time.time()
    
    print("🚀 Starting Full Decodo Proxy Test Suite")
    print("=" * 60)
    
    # Test basic proxy functionality
    logger.info("Running basic proxy test")
    basic_test_passed = test_decodo_proxy()
    
    # Test X.com specific access
    logger.info("Running X.com access test")
    x_test_passed = test_x_access_through_proxy()
    
    # Test Playwright integration
    logger.info("Running Playwright integration test")
    playwright_test_passed = test_playwright_integration()
    
    # Calculate total test time
    total_test_time = time.time() - test_start_time
    
    # Log final summary
    logger.info("=== FINAL TEST RESULTS ===")
    logger.info(f"Total test time: {total_test_time:.2f} seconds")
    logger.info(f"Basic proxy test: {'PASSED' if basic_test_passed else 'FAILED'}")
    logger.info(f"X.com access test: {'PASSED' if x_test_passed else 'FAILED'}")
    logger.info(f"Playwright integration test: {'PASSED' if playwright_test_passed else 'FAILED'}")
    
    print(f"\n🏁 Final Results:")
    print(f"Basic proxy test: {'✅ PASSED' if basic_test_passed else '❌ FAILED'}")
    print(f"X.com access test: {'✅ PASSED' if x_test_passed else '❌ FAILED'}")
    print(f"Playwright integration: {'✅ PASSED' if playwright_test_passed else '❌ FAILED'}")
    print(f"Total test time: {total_test_time:.1f} seconds")
    
    all_tests_passed = basic_test_passed and x_test_passed and playwright_test_passed
    
    if all_tests_passed:
        logger.info("=== ALL TESTS PASSED ===")
        print("🎉 All tests passed! Decodo proxy is fully ready for X scraping.")
        return True
    else:
        logger.warning("=== SOME TESTS FAILED ===")
        print("⚠️  Some tests failed. Check proxy configuration and logs.")
        
        # Provide specific recommendations based on test results
        if not basic_test_passed:
            print("💡 Basic proxy test failed - check network connectivity and proxy credentials")
        if not x_test_passed:
            print("💡 X.com access failed - X.com may be blocking proxy IPs or rate limiting")
        if not playwright_test_passed:
            print("💡 Playwright integration failed - check Playwright installation")
        
        return False

def run_quick_test():
    """Run a quick test of just the basic proxy functionality"""
    logger.info("=== STARTING QUICK TEST ===")
    print("⚡ Running Quick Proxy Test")
    print("=" * 30)
    
    result = test_decodo_proxy()
    
    if result:
        logger.info("Quick test PASSED")
        print("✅ Quick test passed!")
    else:
        logger.error("Quick test FAILED")
        print("❌ Quick test failed!")
    
    return result

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_quick_test()
    else:
        run_full_test()