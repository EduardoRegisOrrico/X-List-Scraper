import json
import time
import os
import datetime
import argparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv
import uuid
import requests
import random
import sys
from bs4 import BeautifulSoup
import re

# Use data directory for persistence in Docker
DATA_DIR = os.getenv("DATA_DIR", ".")
SESSION_FILE = os.path.join(DATA_DIR, "x_session.json")
SESSION_FILE_BACKUP = os.path.join(DATA_DIR, "x_session_backup.json")
TWEETS_FILE = os.path.join(DATA_DIR, "tweets.json")
LAST_ID_FILE = os.path.join(DATA_DIR, "last_tweet_id.txt")
MAX_TWEETS_HISTORY = 500  # Maximum number of tweets to keep in tweets.json

# Custom Exception for page load failures
class PageLoadError(Exception):
    pass

def auto_login(existing_context=None):
    """Automatically login using credentials from environment variables"""
    load_dotenv()
    email = os.getenv("X_EMAIL")
    password = os.getenv("X_PASSWORD")
    
    if not email or not password:
        print("X_EMAIL and X_PASSWORD environment variables are required for auto-login")
        return False
    
    print("\n=== Automatic X.com Login ===")
    print("Attempting to login automatically...")
    
    try:
        # Use existing context if provided, otherwise create new one
        if existing_context:
            context = existing_context
            page = context.new_page()
            should_close_page = True
            browser = None
        else:
            pw = sync_playwright().start()
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1024, "height": 768},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            should_close_page = True
        
        # Clear any existing cookies first
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            print("Removed existing session file.")
        
        print("Opening X.com login page...")
        
        try:
            page.goto("https://x.com/login", timeout=30000)
            print("Login page loaded. Filling in credentials...")
            
            # Wait for and fill email/username field - try multiple selectors
            email_filled = False
            email_selectors = [
                'input[name="text"]',
                'input[autocomplete="username"]',
                'input[data-testid="ocfEnterTextTextInput"]',
                'input[placeholder*="email"]',
                'input[placeholder*="username"]',
                'input[type="text"]'
            ]
            
            for selector in email_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, email)
                    print(f"Email filled using selector: {selector}")
                    email_filled = True
                    break
                except:
                    continue
            
            if not email_filled:
                print("Could not find email input field")
                return False
            
            # Click Next button - try multiple approaches
            time.sleep(2)
            next_clicked = False
            next_approaches = [
                lambda: page.locator('text="Next"').first.click(),
                lambda: page.locator('[data-testid="LoginForm_Login_Button"]').click(),
                lambda: page.locator('button:has-text("Next")').click(),
                lambda: page.locator('div[role="button"]:has-text("Next")').click(),
                lambda: page.locator('span:has-text("Next")').click()
            ]
            
            for approach in next_approaches:
                try:
                    approach()
                    print("Next button clicked")
                    next_clicked = True
                    break
                except:
                    continue
            
            if not next_clicked:
                print("Could not click Next button")
                return False
            
            time.sleep(3)
            
            # Wait for and fill password field - try multiple selectors
            password_filled = False
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[autocomplete="current-password"]',
                'input[data-testid="ocfEnterTextTextInput"]'
            ]
            
            for selector in password_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, password)
                    print(f"Password filled using selector: {selector}")
                    password_filled = True
                    break
                except:
                    continue
            
            if not password_filled:
                print("Could not find password input field")
                return False
            
            # Click Login button - try multiple approaches
            time.sleep(2)
            login_clicked = False
            login_approaches = [
                lambda: page.locator('text="Log in"').first.click(),
                lambda: page.locator('[data-testid="LoginForm_Login_Button"]').click(),
                lambda: page.locator('button:has-text("Log in")').click(),
                lambda: page.locator('div[role="button"]:has-text("Log in")').click(),
                lambda: page.locator('span:has-text("Log in")').click()
            ]
            
            for approach in login_approaches:
                try:
                    approach()
                    print("Login button clicked")
                    login_clicked = True
                    break
                except:
                    continue
            
            if not login_clicked:
                print("Could not click Login button")
                return False
            
            print("Login button clicked. Waiting for authentication...")
            
            # Wait for successful login (check for home page elements)
            try:
                # Wait for navigation to complete and check for login success
                page.wait_for_url("**/home", timeout=15000)
                print("Successfully navigated to home page.")
                
                # Additional verification
                if page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']") or page.query_selector("[data-testid='tweet']"):
                    print("Login verification successful!")
                    
                    # Save cookies
                    save_cookies(context)
                    print("Session saved successfully!")
                    return True
                else:
                    print("Warning: Could not verify successful login elements.")
                    save_cookies(context)
                    return True
                    
            except PlaywrightTimeoutError:
                print("Login may have failed or requires additional verification (2FA, etc.)")
                # Try to save session anyway in case login was successful but slow
                save_cookies(context)
                return False
                
        except Exception as page_error:
            print(f"Error during login process: {page_error}")
            return False
        finally:
            if should_close_page:
                try:
                    page.close()
                except:
                    pass
            # Clean up browser and playwright if we created them
            if browser:
                try:
                    browser.close()
                    pw.stop()
                except:
                    pass
                    
    except Exception as e:
        print(f"\nError during auto-login: {e}")
        return False

def handle_login():
    """Handles the explicit login process when --login flag is used"""
    print("\n=== X.com Login Process ===")
    print("1. A browser window will open to the X.com login page")
    print("2. Please log in with your credentials in that window")
    print("3. After successful login, when you see your X home feed, return to this terminal")
    print("4. Press Enter in this terminal to save the session\n")
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)  # Always show browser for login
            context = browser.new_context(
                viewport={"width": 1024, "height": 768},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Clear any existing cookies first
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
                print("Removed existing session file.")
            
            page = context.new_page()
            print("Opening X.com login page...")
            
            try:
                page.goto("https://x.com/login", timeout=30000)
                print("Login page loaded. Please complete the login process in the browser window.")
                
                # Wait for user to login
                input("\nAfter you have logged in and can see your home feed, press Enter here to continue...")
                
                # Verify we're logged in by checking for common elements
                try:
                    # Try to navigate to home to ensure session is valid
                    page.goto("https://x.com/home", timeout=15000)
                    
                    # Check for login indicators
                    if page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']") or page.query_selector("[data-testid='tweet']"):
                        print("Login verification successful!")
                        
                        # Save cookies
                        save_cookies(context)
                        print("\nSession saved successfully! You can now run the script without --login.")
                        return True
                    else:
                        print("Warning: Could not verify successful login. Session may not be valid.")
                        save_cookies(context)
                        print("Session saved anyway. If monitoring fails, please try --login again.")
                        return True
                        
                except Exception as verify_error:
                    print(f"Could not verify login status: {verify_error}")
                    print("Saving session anyway...")
                    save_cookies(context)
                    return True
                    
            except Exception as page_error:
                print(f"Error during page navigation: {page_error}")
                return False
            finally:
                try:
                    page.close()
                except:
                    pass
                    
    except KeyboardInterrupt:
        print("\nLogin process interrupted by user.")
        return False
    except Exception as e:
        print(f"\nError during login process: {e}")
        return False

def get_db_connection():
    """
    Establishes a PostgreSQL database connection using environment variables from .env file.
    Prioritizes DATABASE_URL (newsio-single format) but falls back to individual parameters.
    """
    load_dotenv()
    
    try:
        # First priority: DATABASE_URL (newsio-single format)
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            print("Using DATABASE_URL connection string...")
            # Parse the DATABASE_URL
            parsed_url = urlparse(database_url)
            conn_params = {
                'dbname': parsed_url.path[1:],  # Remove leading slash
                'user': parsed_url.username,
                'password': parsed_url.password,
                'host': parsed_url.hostname,
                'port': parsed_url.port or 5432
            }
            
            # Handle query parameters (like schema)
            options = []
            if parsed_url.query:
                # Handle schema parameter if present
                if 'schema=' in parsed_url.query:
                    schema_name = parsed_url.query.split('schema=')[-1].split('&')[0]
                    options.append(f'search_path={schema_name},public')
            
            # Remove IPv4 address family preference as it's not supported
            # options.append('addr_type=ipv4')
            
            if options:
                conn_params['options'] = f"-c {' -c '.join(options)}"
                
        else:
            # Fallback: Individual parameters (legacy XScraper format)
            print("DATABASE_URL not found, trying individual parameters...")
            user = os.getenv("user")
            password = os.getenv("password")
            host = os.getenv("host")
            port = os.getenv("port")
            dbname = os.getenv("dbname")
            
            if not all([user, password, host, port, dbname]):
                # Final fallback: SUPABASE_DATABASE_URL (old format)
                supabase_url = os.getenv("SUPABASE_DATABASE_URL")
                if supabase_url:
                    print("Using SUPABASE_DATABASE_URL as fallback...")
                    parsed_url = urlparse(supabase_url)
                    conn_params = {
                        'dbname': parsed_url.path[1:],
                        'user': parsed_url.username,
                        'password': parsed_url.password,
                        'host': parsed_url.hostname,
                        'port': parsed_url.port or 5432
                    }
                    
                    # Handle schema if present in query
                    options = []
                    if 'schema' in parsed_url.query:
                        schema_name = parsed_url.query.split('schema=')[-1].split('&')[0]
                        options.append(f'search_path={schema_name},public')
                    
                    # Remove IPv4 address family preference as it's not supported
                    # options.append('addr_type=ipv4')
                    
                    conn_params['options'] = f"-c {' -c '.join(options)}"
                else:
                    print("Error: No database connection parameters found in .env file.")
                    print("Expected: DATABASE_URL or individual parameters (user, password, host, port, dbname)")
                    return None
            else:
                # Use individual parameters
                conn_params = {
                    'user': user,
                    'password': password,
                    'host': host,
                    'port': int(port),
                    'dbname': dbname
                }
        
        # Connect to the database
        print(f"Connecting to database at {conn_params['host']}:{conn_params['port']}...")
        print(f"Database name: {conn_params['dbname']}")
        
        conn = psycopg2.connect(**conn_params)
        
        # Test the connection
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"Successfully connected to database: {version[:50]}...")
            
        return conn
        
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        print("Please check your DATABASE_URL or individual database parameters in .env file")
        return None

def close_db_connection_safely(conn):
    """Safely close a database connection."""
    if conn:
        try:
            if not conn.closed:
                conn.close()
                print("Database connection closed successfully.")
            else:
                print("Database connection was already closed.")
        except Exception as e:
            print(f"Error closing database connection: {e}")
    else:
        print("No database connection to close.")

def check_db_connection_status(conn):
    """Check the status of a database connection and attempt basic connectivity test."""
    if not conn:
        print("Database connection is None")
        return False
    
    try:
        if conn.closed:
            print(f"Database connection is closed (status: {conn.closed})")
            return False
        else:
            # Test the connection with a simple query
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()
                if result and result[0] == 1:
                    print("Database connection is healthy")
                    return True
                else:
                    print("Database connection test failed")
                    return False
    except Exception as e:
        print(f"Database connection check failed: {e}")
        return False

def save_tweet_to_db(tweet_data, conn):
    """Saves a single tweet's metadata to the PostgreSQL database."""
    if not conn:
        print("Database connection not available. Skipping DB save.")
        return False, conn

    try:
        # Check if connection is closed
        if conn.closed:
            print("Database connection was closed. Attempting to reconnect...")
            old_conn = conn  # Keep reference to old connection for cleanup
            conn = get_db_connection()
            if not conn:
                print("Failed to reconnect to database. Skipping DB save.")
                # Clean up the old closed connection
                try:
                    if old_conn and not old_conn.closed:
                        old_conn.close()
                except Exception:
                    pass
                return False, None
            # Clean up the old closed connection
            try:
                if old_conn and not old_conn.closed:
                    old_conn.close()
            except Exception:
                pass

        # Validate required tweet data
        if not tweet_data.get('id'):
            print("Tweet missing ID, skipping DB save.")
            return False, conn
        
        if not tweet_data.get('text'):
            print(f"Tweet {tweet_data.get('id')} missing text, skipping DB save.")
            return False, conn

        # Print the raw tweet data for debugging
        print(f"Tweet data for DB save (ID: {tweet_data['id']}):")
        print(f"  - Text: {tweet_data['text'][:50]}...")
        print(f"  - Raw user data: {tweet_data.get('user', {})}")

        # Extract username directly - Twitter API sometimes nests it differently
        username = None
        if 'user' in tweet_data:
            username = tweet_data['user'].get('username')
            if not username or username == "Unknown":
                # Try alternative paths in case API structure changed
                if 'user' in tweet_data and 'screen_name' in tweet_data['user']:
                    username = tweet_data['user']['screen_name']
                elif 'screen_name' in tweet_data:
                    username = tweet_data['screen_name']

        # Debug output for username
        if not username:
            print(f"WARNING: Username not found for tweet {tweet_data['id']}")
            print(f"User data: {tweet_data.get('user', {})}")
        else:
            print(f"Found username for DB: {username}")

        with conn.cursor() as cur:
            # Handle date parsing with fallback
            created_at_dt = None
            created_at_str = tweet_data.get('created_at')
            
            if created_at_str:
                try:
                    # Parse Twitter's date format (e.g., "Wed May 07 00:08:42 +0000 2025")
                    created_at_dt = datetime.datetime.strptime(created_at_str, '%a %b %d %H:%M:%S %z %Y')
                except ValueError as ve:
                    print(f"Error parsing date '{created_at_str}' for tweet {tweet_data['id']}: {ve}")
                    # Use current time as fallback
                    created_at_dt = datetime.datetime.now(datetime.timezone.utc)
            else:
                print(f"Tweet {tweet_data['id']} missing created_at, using current time")
                created_at_dt = datetime.datetime.now(datetime.timezone.utc)
            
            # Generate a unique ID for the tweet - using a UUID which is compatible with CUID format
            tweet_id = str(uuid.uuid4())
            
            sql = """
            INSERT INTO public."Tweet" (id, "tweetId", text, username, "createdAt", analyzed, analysis, "contentFingerprint")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ("tweetId") DO NOTHING;
            """
            
            print(f"Executing SQL with username: {username}")
            
            cur.execute(sql, (
                tweet_id,           # Add the generated UUID as the primary key
                tweet_data['id'],
                tweet_data['text'],
                username,           # Use the directly extracted username
                created_at_dt,      # Use the datetime object
                False,              # analyzed (default)
                None,               # analysis (JSONB, so None for null)
                None                # contentFingerprint (optional)
            ))
            conn.commit()
            print(f"Successfully saved tweet {tweet_data['id']} to database with username: {username}")
            return True, conn
    except Exception as e:
        print(f"Error saving tweet {tweet_data.get('id')} to DB: {e}")
        # Check if the connection was closed by the server
        if "server closed the connection" in str(e) or (conn and conn.closed):
            print("Connection lost. Attempting to reconnect...")
            try:
                old_conn = conn
                # Close the failed connection if it's not already closed
                if old_conn and not old_conn.closed:
                    old_conn.close()
                # Get a new connection
                conn = get_db_connection()
                if conn:
                    print("Successfully reconnected to database.")
                    # Try again with new connection (but limit recursion)
                    return save_tweet_to_db(tweet_data, conn)
                else:
                    print("Failed to reconnect to database.")
                    return False, None
            except Exception as reconnect_error:
                print(f"Error during reconnection: {reconnect_error}")
                return False, None
        else:
            # For other errors, just rollback
            try:
                if conn:
                    conn.rollback()
            except Exception:
                # If rollback fails, the connection is probably dead
                pass
        return False, conn

def save_cookies(context, session_file=None):
    """Save cookies to specified file or default session file"""
    file_path = session_file or SESSION_FILE
    cookies = context.cookies()
    with open(file_path, "w") as f:
        json.dump(cookies, f)

def load_cookies(context, session_file=None):
    """Load cookies from specified file or default session file"""
    file_path = session_file or SESSION_FILE
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        return True
    return False

def auto_login_backup_account(existing_context=None):
    """Automatically login using backup account credentials"""
    load_dotenv()
    email = os.getenv("X_EMAIL_BACKUP")
    password = os.getenv("X_PASSWORD_BACKUP")
    
    if not email or not password:
        print("X_EMAIL_BACKUP and X_PASSWORD_BACKUP environment variables are required for backup account")
        return False
    
    print("\n=== Automatic X.com Backup Account Login ===")
    print("Attempting to login with backup account...")
    
    try:
        # Use existing context if provided, otherwise create new one
        if existing_context:
            context = existing_context
            page = context.new_page()
            should_close_page = True
            browser = None
        else:
            pw = sync_playwright().start()
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1024, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            should_close_page = True
        
        # Clear any existing cookies first
        if os.path.exists(SESSION_FILE_BACKUP):
            os.remove(SESSION_FILE_BACKUP)
            print("Removed existing backup session file.")
        
        print("Opening X.com login page for backup account...")
        
        try:
            page.goto("https://x.com/login", timeout=30000)
            print("Login page loaded. Filling in backup account credentials...")
            
            # Wait for and fill email/username field - try multiple selectors
            email_filled = False
            email_selectors = [
                'input[name="text"]',
                'input[autocomplete="username"]',
                'input[data-testid="ocfEnterTextTextInput"]',
                'input[placeholder*="email"]',
                'input[placeholder*="username"]',
                'input[type="text"]'
            ]
            
            for selector in email_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, email)
                    print(f"Backup email filled using selector: {selector}")
                    email_filled = True
                    break
                except:
                    continue
            
            if not email_filled:
                print("Could not find email input field for backup account")
                return False
            
            # Click Next button - try multiple approaches
            time.sleep(2)
            next_clicked = False
            next_approaches = [
                lambda: page.locator('text="Next"').first.click(),
                lambda: page.locator('[data-testid="LoginForm_Login_Button"]').click(),
                lambda: page.locator('button:has-text("Next")').click(),
                lambda: page.locator('div[role="button"]:has-text("Next")').click(),
                lambda: page.locator('span:has-text("Next")').click()
            ]
            
            for approach in next_approaches:
                try:
                    approach()
                    print("Next button clicked for backup account")
                    next_clicked = True
                    break
                except:
                    continue
            
            if not next_clicked:
                print("Could not click Next button for backup account")
                return False
            
            time.sleep(3)
            
            # Wait for and fill password field - try multiple selectors
            password_filled = False
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[autocomplete="current-password"]',
                'input[data-testid="ocfEnterTextTextInput"]'
            ]
            
            for selector in password_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, password)
                    print(f"Backup password filled using selector: {selector}")
                    password_filled = True
                    break
                except:
                    continue
            
            if not password_filled:
                print("Could not find password input field for backup account")
                return False
            
            # Click Login button - try multiple approaches
            time.sleep(2)
            login_clicked = False
            login_approaches = [
                lambda: page.locator('text="Log in"').first.click(),
                lambda: page.locator('[data-testid="LoginForm_Login_Button"]').click(),
                lambda: page.locator('button:has-text("Log in")').click(),
                lambda: page.locator('div[role="button"]:has-text("Log in")').click(),
                lambda: page.locator('span:has-text("Log in")').click()
            ]
            
            for approach in login_approaches:
                try:
                    approach()
                    print("Login button clicked for backup account")
                    login_clicked = True
                    break
                except:
                    continue
            
            if not login_clicked:
                print("Could not click Login button for backup account")
                return False
            
            print("Backup account login button clicked. Waiting for authentication...")
            
            # Wait for successful login (check for home page elements)
            try:
                # Wait for navigation to complete and check for login success
                page.wait_for_url("**/home", timeout=15000)
                print("Successfully navigated to home page with backup account.")
                
                # Additional verification
                if page.query_selector("[data-testid='SideNav_AccountSwitcher_Button']") or page.query_selector("[data-testid='tweet']"):
                    print("Backup account login verification successful!")
                    
                    # Save cookies to backup session file
                    save_cookies(context, SESSION_FILE_BACKUP)
                    print("Backup account session saved successfully!")
                    return True
                else:
                    print("Warning: Could not verify successful backup account login elements.")
                    save_cookies(context, SESSION_FILE_BACKUP)
                    return True
                    
            except PlaywrightTimeoutError:
                print("Backup account login may have failed or requires additional verification (2FA, etc.)")
                # Try to save session anyway in case login was successful but slow
                save_cookies(context, SESSION_FILE_BACKUP)
                return False
                
        except Exception as page_error:
            print(f"Error during backup account login process: {page_error}")
            return False
        finally:
            if should_close_page:
                try:
                    page.close()
                except:
                    pass
            # Clean up browser and playwright if we created them
            if browser:
                try:
                    browser.close()
                    pw.stop()
                except:
                    pass
                    
    except Exception as e:
        print(f"\nError during backup account auto-login: {e}")
        return False

def save_last_tweet_id(tweet_id):
    """Save the most recent tweet ID to file"""
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(tweet_id)) # Ensure it's a string

def load_last_tweet_id():
    """Load the most recent tweet ID from file"""
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r") as f:
            return f.read().strip()
    return None

def extract_tweet_metadata(tweet_content):
    """Extract only the relevant metadata from a tweet object"""
    if not tweet_content:
        return None
    
    # Validate that we have the minimum required data
    tweet_id = tweet_content.get("rest_id")
    if not tweet_id:
        return None
    
    print(f"\nExtracting metadata for tweet ID: {tweet_id}")
        
    legacy = tweet_content.get("legacy", {})
    tweet_text = legacy.get("full_text")
    
    # Skip tweets without text
    if not tweet_text:
        return None
    
    # Extract base tweet data
    tweet_data = {
        "id": tweet_id,
        "created_at": legacy.get("created_at"),
        "text": tweet_text,
        "lang": legacy.get("lang"),
    }
    
    # Extract user data with multiple fallback paths
    # Twitter API structure can vary based on endpoint and changes over time
    user_data = {
        "id": None,
        "name": "Unknown",
        "username": "Unknown",
        "verified": False,
        "is_blue_verified": False,
        "followers_count": 0,
        "profile_image_url": None,
    }
    
    # Primary path: core > user_results > result > legacy
    user = tweet_content.get("core", {}).get("user_results", {}).get("result", {})
    if user and user.get("legacy"):
        legacy_user = user.get("legacy", {})
        user_data.update({
            "id": user.get("rest_id"),
            "name": legacy_user.get("name"),
            "username": legacy_user.get("screen_name"),
            "verified": legacy_user.get("verified", False),
            "is_blue_verified": user.get("is_blue_verified", False),
            "followers_count": legacy_user.get("followers_count"),
            "profile_image_url": legacy_user.get("profile_image_url_https"),
        })
        
        # Additional extraction attempts for this path when legacy doesn't have the data
        if not user_data["username"] or user_data["username"] == "Unknown":
            # Check if username is in the main user object (outside of legacy)
            if user.get("legacy", {}).get("screen_name"):
                user_data["username"] = user.get("legacy", {}).get("screen_name")
            
        if not user_data["name"] or user_data["name"] == "Unknown":
            # Check for name in the main user object
            if user.get("legacy", {}).get("name"):
                user_data["name"] = user.get("legacy", {}).get("name")
                
    # Fallback 1: user_results > result > legacy
    elif tweet_content.get("user_results", {}).get("result", {}).get("legacy"):
        user_fallback = tweet_content.get("user_results", {}).get("result", {})
        legacy_user = user_fallback.get("legacy", {})
        user_data.update({
            "id": user_fallback.get("rest_id"),
            "name": legacy_user.get("name"),
            "username": legacy_user.get("screen_name"),
            "verified": legacy_user.get("verified", False),
            "is_blue_verified": user_fallback.get("is_blue_verified", False),
            "followers_count": legacy_user.get("followers_count"),
            "profile_image_url": legacy_user.get("profile_image_url_https"),
        })
    # Fallback 2: user_results_data > result > legacy (structure seen in some API responses)
    elif tweet_content.get("user_results_data", {}).get("result", {}).get("legacy"):
        user_fallback = tweet_content.get("user_results_data", {}).get("result", {})
        legacy_user = user_fallback.get("legacy", {})
        user_data.update({
            "id": user_fallback.get("rest_id"),
            "name": legacy_user.get("name"),
            "username": legacy_user.get("screen_name"),
            "verified": legacy_user.get("verified", False),
            "is_blue_verified": user_fallback.get("is_blue_verified", False),
            "followers_count": legacy_user.get("followers_count"),
            "profile_image_url": legacy_user.get("profile_image_url_https"),
        })
    # Fallback 3: direct user property (sometimes exists in the result)
    elif tweet_content.get("user"):
        direct_user = tweet_content.get("user", {})
        user_data.update({
            "id": direct_user.get("id_str") or direct_user.get("id"),
            "name": direct_user.get("name"),
            "username": direct_user.get("screen_name"),
            "verified": direct_user.get("verified", False),
            "followers_count": direct_user.get("followers_count"),
            "profile_image_url": direct_user.get("profile_image_url_https"),
        })
    # Fallback 4: legacy > user_id_str field (try to get at least the user ID)
    elif legacy.get("user_id_str"):
        user_data.update({
            "id": legacy.get("user_id_str"),
        })
    
    # Additional specific checks for username and name when they're missing
    if user_data["username"] == "Unknown" or user_data["username"] is None:
        
        # Check in tweet legacy for user screen name
        if legacy.get("user_screen_name"):
            user_data["username"] = legacy.get("user_screen_name")
    
    # Regex fallback search for username/screen_name if still not found
    if user_data["username"] == "Unknown" or user_data["username"] is None:
        tweet_str = json.dumps(tweet_content)
        if "screen_name" in tweet_str:
            screen_name_matches = re.findall(r'"screen_name":\s*"([^"]*)"', tweet_str)
            if screen_name_matches:
                for match in screen_name_matches:
                    if match and match != "Unknown":
                        user_data["username"] = match
                        print(f"Username found via fallback search: {match}")
                        break
    
    # Look for name field as well via regex if not found
    if user_data["name"] == "Unknown" or user_data["name"] is None:
        tweet_str = json.dumps(tweet_content) if 'tweet_str' not in locals() else tweet_str
        if "\"name\":" in tweet_str:
            name_matches = re.findall(r'"name":\s*"([^"]*)"', tweet_str)
            if name_matches:
                for match in name_matches:
                    if match and match != "Unknown" and match != "":
                        user_data["name"] = match
                        print(f"Name found via fallback search: {match}")
                        break
    
    # If we found a username in the legacy data but not in the user paths
    if user_data["username"] == "Unknown" and legacy.get("user_screen_name"):
        user_data["username"] = legacy.get("user_screen_name")
    
    # If username is still unknown but we have other data like name, try to use what we have
    if user_data["username"] == "Unknown" and user_data["name"] != "Unknown":
        # Try to generate a username from name as a last resort
        generated_username = user_data["name"].lower().replace(" ", "_")
        user_data["username"] = f"{generated_username}_user"
        print(f"Generated username from name: {user_data['username']}")
    
    # Only print warnings if extraction failed
    if user_data["username"] == "Unknown" or user_data["username"] is None:
        print(f"WARNING: Could not extract username for tweet {tweet_id}")
    if user_data["name"] == "Unknown" or user_data["name"] is None:
        print(f"WARNING: Could not extract name for tweet {tweet_id}")
    
    tweet_data["user"] = user_data
    
    # Extract engagement stats
    tweet_data["stats"] = {
        "retweet_count": legacy.get("retweet_count", 0),
        "reply_count": legacy.get("reply_count", 0),
        "like_count": legacy.get("favorite_count", 0),
        "quote_count": legacy.get("quote_count", 0),
        "bookmark_count": legacy.get("bookmark_count", 0),
        "view_count": tweet_content.get("views", {}).get("count", "0"),
    }
    
    # Extract media if present
    media_entities = legacy.get("extended_entities", {}).get("media", [])
    if media_entities:
        tweet_data["media"] = []
        for media in media_entities:
            if media:  # Check if media object is not None
                media_obj = {
                    "type": media.get("type"),
                    "url": media.get("media_url_https"),
                    "expanded_url": media.get("expanded_url"),
                }
                tweet_data["media"].append(media_obj)
    
    # Extract mentions, hashtags, and urls safely
    tweet_data["entities"] = {}
    entities = legacy.get("entities", {})
    
    if entities and "user_mentions" in entities:
        tweet_data["entities"]["mentions"] = [
            {"screen_name": mention.get("screen_name"), "id": mention.get("id_str")}
            for mention in entities.get("user_mentions", []) if mention
        ]
    
    if entities and "hashtags" in entities:
        tweet_data["entities"]["hashtags"] = [
            hashtag.get("text") for hashtag in entities.get("hashtags", []) if hashtag and hashtag.get("text")
        ]
    
    if entities and "urls" in entities:
        tweet_data["entities"]["urls"] = [
            {"expanded_url": url.get("expanded_url"), "display_url": url.get("display_url")}
            for url in entities.get("urls", []) if url
        ]
    
    return tweet_data

def _process_xhr_calls(xhr_calls, last_tweet_id, limit, seen_ids, current_tweets_metadata_list):
    """Helper function to process XHR calls and extract tweets."""
    newly_found_tweets_this_batch = []
    newest_id_this_batch = None

    for xhr in xhr_calls:
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

                                if tweet_id and tweet_id not in seen_ids:
                                    seen_ids.add(tweet_id)
                                    if last_tweet_id is None or int(tweet_id) > int(last_tweet_id):
                                        extracted_tweet = extract_tweet_metadata(tweet_content)
                                        if extracted_tweet:
                                            newly_found_tweets_this_batch.append(extracted_tweet)
                                            current_tweets_metadata_list.append(extracted_tweet)
                                        
                                        if newest_id_this_batch is None or (tweet_id and int(tweet_id) > int(newest_id_this_batch)):
                                            newest_id_this_batch = tweet_id

                                        if limit and len(current_tweets_metadata_list) >= limit:
                                            return newly_found_tweets_this_batch, newest_id_this_batch, True # Limit reached
                            except KeyError as e:
                                # print(f"Error extracting tweet data from entry: {e}")
                                pass
                if limit and len(current_tweets_metadata_list) >= limit:
                    return newly_found_tweets_this_batch, newest_id_this_batch, True # Limit reached
            if limit and len(current_tweets_metadata_list) >= limit:
                return newly_found_tweets_this_batch, newest_id_this_batch, True # Limit reached
        except Exception as e:
            print(f"Error parsing XHR JSON: {e}")
    return newly_found_tweets_this_batch, newest_id_this_batch, False # Limit not reached

def scrape_list(list_url, max_scrolls=3, wait_time=1, browser_param=None, context_param=None, last_tweet_id=None, limit=None, is_backup_account=False):
    _xhr_calls_buffer = [] 
    all_new_tweets_metadata = []
    overall_newest_id = last_tweet_id
    seen_ids = set()
    
    playwright_instance_local = None
    browser_to_use = browser_param
    context_to_use = context_param
    page = None # Initialize page to None

    try:
        if browser_to_use is None:
            playwright_instance_local = sync_playwright().start()
            browser_to_use = playwright_instance_local.chromium.launch(headless=True)
            context_to_use = browser_to_use.new_context(viewport={"width": 1920, "height": 1080})
            if not load_cookies(context_to_use):
                print("No session found for scraping. Returning empty result.")
                return [], None

        page = context_to_use.new_page()
        page.on("response", lambda response: _xhr_calls_buffer.append(response) if response.request.resource_type == "xhr" and ("ListLatestTweetsTimeline" in response.url or "Timeline" in response.url) else None)
        
        print(f"Navigating to {list_url}...")
        page.goto(list_url, timeout=30000)
        page.wait_for_selector("[data-testid='cellInnerDiv']", timeout=15000) # Using 15000 as per user traceback
        print("Page content loaded.")

        for i in range(max_scrolls + 1):
            if i > 0:
                print(f"Scrolling... ({i}/{max_scrolls})")
                page.mouse.wheel(0, 2000)
                time.sleep(wait_time)
            else:
                print("Initial content check after page load...")
                time.sleep(max(wait_time, 1.5))
                
            # Debug XHR calls before processing
            if _xhr_calls_buffer:
                print(f"Found {len(_xhr_calls_buffer)} XHR calls to process")
                for idx, xhr in enumerate(_xhr_calls_buffer[:3]):  # Log first 3 for debugging
                    try:
                        print(f"XHR {idx+1} URL: {xhr.url}")
                        if "ListLatestTweetsTimeline" in xhr.url:
                            xhr_data = xhr.json()
                            # Check data structure for debugging
                            data_keys = list(xhr_data.keys()) if isinstance(xhr_data, dict) else "Not a dict"
                            print(f"XHR {idx+1} data keys: {data_keys}")
                            
                            # Try to find instructions
                            if isinstance(xhr_data, dict) and 'data' in xhr_data:
                                if 'list' in xhr_data['data']:
                                    tweets_path = xhr_data.get('data', {}).get('list', {}).get('tweets_timeline', {})
                                    if tweets_path:
                                        print(f"Found tweets_timeline in response {idx+1}")
                    except Exception as e:
                        print(f"Error examining XHR {idx+1}: {e}")
            
            newly_processed_this_scroll, id_this_batch, limit_hit = _process_xhr_calls(
                _xhr_calls_buffer, last_tweet_id, limit, seen_ids, all_new_tweets_metadata
            )
            _xhr_calls_buffer.clear()

            if id_this_batch and (overall_newest_id is None or int(id_this_batch) > int(overall_newest_id)):
                overall_newest_id = id_this_batch

            if limit_hit:
                print("Tweet limit reached for this cycle.")
                break
            
            if i == 0 and not newly_processed_this_scroll and last_tweet_id is not None:
                print("No new tweets found on initial check; skipping further scrolls this cycle.")
                break

    except PlaywrightTimeoutError as e:
        error_msg = f"Timeout loading page content for {list_url}: {e}"
        print(error_msg)
        raise PageLoadError(error_msg)
    except Exception as e:
        error_msg = f"Generic error during page operation for {list_url}: {e}"
        print(error_msg)
        raise PageLoadError(error_msg)
    finally:
        if page:
            try:
                page.close()
            except Exception as e_close:
                print(f"Error closing page: {e_close}")
        if playwright_instance_local: # This means browser_to_use was also local
            if browser_to_use:
                try:
                    browser_to_use.close()
                except Exception as e_close_browser:
                    print(f"Error closing local browser: {e_close_browser}")
            try:
                playwright_instance_local.stop()
            except Exception as e_stop_pw:
                print(f"Error stopping local Playwright: {e_stop_pw}")
    
    # Debug found tweets
    if all_new_tweets_metadata:
        print(f"\nFound {len(all_new_tweets_metadata)} tweets in total:")
        for idx, tweet in enumerate(all_new_tweets_metadata[:5]):  # Show first 5
            username = tweet.get('user', {}).get('username', 'Unknown')
            print(f"Tweet {idx+1}: ID={tweet['id']}, Username={username}, Text={tweet['text'][:50]}...")
        if len(all_new_tweets_metadata) > 5:
            print(f"... and {len(all_new_tweets_metadata) - 5} more tweets")
    
    all_new_tweets_metadata.sort(key=lambda x: int(x.get("id", "0")), reverse=True)
    if limit and len(all_new_tweets_metadata) > limit:
        all_new_tweets_metadata = all_new_tweets_metadata[:limit]
        
    return all_new_tweets_metadata, overall_newest_id

def trigger_tweet_analysis():
    """Trigger the tweet analysis API endpoint."""
    try:
        # Get the API base URL from environment or use default
        load_dotenv()
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:3000")
        api_url = f"{api_base_url}/api/twitter/analyze"
        
        # Make a POST request to the analysis endpoint
        response = requests.post(api_url, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Successfully triggered tweet analysis API")
            return True
        else:
            print(f"Failed to trigger tweet analysis API. Status code: {response.status_code}")
            print(f"API URL: {api_url}")
            return False
    except Exception as e:
        print(f"Error triggering tweet analysis API: {e}")
        return False

def switch_to_backup_account(pw_runtime):
    """Initialize backup account browser and context using existing playwright runtime with different fingerprint"""
    load_dotenv()
    backup_email = os.getenv("X_EMAIL_BACKUP")
    backup_password = os.getenv("X_PASSWORD_BACKUP")
    
    print(f"\n🔄 ACCOUNT SWITCH: Initializing backup account ({backup_email})")
    
    if not backup_email or not backup_password:
        print("❌ BACKUP ACCOUNT: Credentials not found in environment variables")
        return None, None
    
    try:
        print("🔄 BACKUP ACCOUNT: Creating new browser with different fingerprint...")
        
        # Different browser args for backup account (removed --user-data-dir)
        browser_backup = pw_runtime.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Faster loading, different fingerprint
                '--disable-javascript-harmony-shipping',
                '--memory-pressure-off',
                '--max_old_space_size=4096'
            ]
        )
        
        # Completely different browser fingerprint
        backup_user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        
        # Select different user agent from backup pool
        backup_user_agent = backup_user_agents[int(time.time()) % len(backup_user_agents)]
        
        context_backup = browser_backup.new_context(
            viewport={"width": 1366, "height": 768},  # Different viewport size
            user_agent=backup_user_agent,
            locale='en-GB',  # Different locale
            timezone_id='Europe/London',  # Different timezone
            color_scheme='dark',  # Different color scheme
            reduced_motion='reduce',  # Different motion preference
            forced_colors='none',
            extra_http_headers={
                'Accept-Language': 'en-GB,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
        )
        
        # Add different browser fingerprint script
        context_backup.add_init_script("""
            // Different fingerprint for backup account
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5, 6, 7],  // Different plugin count
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-GB', 'en'],  // Different language preference
            });
            Object.defineProperty(navigator, 'platform', {
                get: () => 'MacIntel',  // Different platform
            });
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,  // Different CPU core count
            });
            Object.defineProperty(screen, 'width', {
                get: () => 1366,
            });
            Object.defineProperty(screen, 'height', {
                get: () => 768,
            });
            Object.defineProperty(screen, 'availWidth', {
                get: () => 1366,
            });
            Object.defineProperty(screen, 'availHeight', {
                get: () => 728,
            });
        """)
        
        print(f"🔧 BACKUP FINGERPRINT: Using {backup_user_agent[:50]}...")
        print(f"🔧 BACKUP FINGERPRINT: Viewport 1366x768, Locale en-GB, Timezone Europe/London")
        
        # Add random delay to make requests less predictable
        initial_delay = random.uniform(3, 8)
        print(f"🔧 BACKUP TIMING: Adding {initial_delay:.1f}s initial delay for natural behavior")
        time.sleep(initial_delay)
        
        # Try to load existing backup session first
        print(f"🔍 BACKUP ACCOUNT: Checking for existing session ({backup_email})")
        if load_cookies(context_backup, SESSION_FILE_BACKUP):
            print(f"✅ BACKUP ACCOUNT: Loaded existing session for {backup_email}")
            return browser_backup, context_backup
        else:
            print(f"❌ BACKUP ACCOUNT: No existing session found for {backup_email}")
            print(f"🔄 BACKUP ACCOUNT: Attempting automatic login for {backup_email}...")
            if auto_login_backup_account(context_backup):
                print(f"✅ BACKUP ACCOUNT: Login successful for {backup_email}")
                return browser_backup, context_backup
            else:
                print(f"❌ BACKUP ACCOUNT: Login failed for {backup_email}")
                browser_backup.close()
                return None, None
                
    except Exception as e:
        print(f"❌ BACKUP ACCOUNT: Error during switch - {e}")
        return None, None



def monitor_list_real_time(db_conn, list_url, interval=60, max_scrolls=3, wait_time=1, headless=True, limit=None, max_consecutive_errors=5, max_history=MAX_TWEETS_HISTORY):
    """Monitor Twitter list for new tweets with rate limiting protection."""
    last_tweet_id = load_last_tweet_id()
    all_tweets_ever_saved_json = [] # For tweets.json cache/backup
    consecutive_error_count = 0
    base_wait_time = interval # Store the original interval for normal operation
    current_wait_time = base_wait_time # This will change during backoff

    if os.path.exists(TWEETS_FILE):
        try:
            with open(TWEETS_FILE, "r") as f:
                saved_data = json.load(f)
                if isinstance(saved_data, dict) and "tweets" in saved_data:
                    all_tweets_ever_saved_json = saved_data["tweets"]
                elif isinstance(saved_data, list): # Handle old format if present
                    all_tweets_ever_saved_json = saved_data
                    
                # Trim history if it exceeds the maximum limit
                if len(all_tweets_ever_saved_json) > max_history:
                    print(f"Tweets history exceeds limit ({len(all_tweets_ever_saved_json)} > {max_history}). Trimming to most recent {max_history} tweets.")
                    all_tweets_ever_saved_json = all_tweets_ever_saved_json[:max_history]
        except Exception as e:
            print(f"Error loading existing tweets file ({TWEETS_FILE}): {e}. Starting fresh.")
            all_tweets_ever_saved_json = []
    
    pw_runtime = None 
    browser_monitor = None
    context_monitor = None
    
    # Initialize browser before main loop
    pw_runtime, browser_monitor, context_monitor = initialize_browser(headless, "primary")
    
    # Initialize backup browser components (will be created when needed)
    browser_monitor_backup = None
    context_monitor_backup = None
    
    session_available = False
    backup_session_available = False
    using_backup_account = False
    
    try:
        # Load environment variables to check account info
        load_dotenv()
        primary_email = os.getenv("X_EMAIL")
        backup_email = os.getenv("X_EMAIL_BACKUP")
        
        print(f"\n=== Account Configuration ===")
        print(f"Primary account: {primary_email if primary_email else 'Not configured'}")
        print(f"Backup account:  {backup_email if backup_email else 'Not configured'}")
        print("=" * 30)
        
        if load_cookies(context_monitor):
            session_available = True
            print(f"✅ PRIMARY ACCOUNT SESSION: Valid session found for {primary_email}")
            print("🔄 Using PRIMARY account for monitoring")
        else:
            print(f"❌ PRIMARY ACCOUNT SESSION: No valid session found for {primary_email}")
            print("🔄 Attempting automatic login for PRIMARY account...")
            # Try automatic login using existing context
            if auto_login(context_monitor):
                print("✅ PRIMARY ACCOUNT LOGIN: Automatic login successful!")
                # Reload cookies after successful auto-login
                if load_cookies(context_monitor):
                    session_available = True
                    print("✅ PRIMARY ACCOUNT SESSION: Session loaded successfully")
                    print("🔄 Using PRIMARY account for monitoring")
                else:
                    print("⚠️  PRIMARY ACCOUNT WARNING: Auto-login succeeded but session reload failed")
                    session_available = False
            else:
                print("❌ PRIMARY ACCOUNT LOGIN: Automatic login failed")
                session_available = False
        
        # Check if backup account credentials are available
        if backup_email:
            print(f"✅ BACKUP ACCOUNT: Credentials detected for {backup_email}")
            print("🔄 Backup account will be used for rate limit mitigation")
        else:
            print("❌ BACKUP ACCOUNT: No credentials found")
            print("💡 Add X_EMAIL_BACKUP and X_PASSWORD_BACKUP to .env for better rate limit handling")
        
        print("=" * 50)
        
        print(f"Starting real-time monitoring of {list_url}")
        print(f"Checking for new tweets every {interval} seconds")
        if limit:
            print(f"Limited to {limit} new tweets per check")
        if last_tweet_id:
            print(f"Last seen tweet ID: {last_tweet_id}")
        
        while True:
            start_time_cycle = time.time()
            try:
                print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new tweets...")
                
                newly_scraped_tweets = []
                newest_id_from_scrape = None
                
                if session_available and not using_backup_account:
                    # Try browser-based scraping with primary account
                    print(f"🔄 SCRAPING: Using PRIMARY account ({primary_email})")
                    newly_scraped_tweets, newest_id_from_scrape = scrape_list(
                        list_url, 
                        max_scrolls=max_scrolls, 
                        wait_time=wait_time,
                        browser_param=browser_monitor,
                        context_param=context_monitor,
                        last_tweet_id=last_tweet_id,
                        limit=limit
                    )
                    consecutive_error_count = 0
                    current_wait_time = base_wait_time
                    print(f"✅ PRIMARY ACCOUNT: Successful request. Resuming normal interval of {current_wait_time} seconds.")
                elif using_backup_account and browser_monitor_backup and context_monitor_backup:
                    # Continue using backup account with different timing
                    print(f"🔄 SCRAPING: Using BACKUP account ({backup_email})")
                    
                    # Use different timing patterns for backup account
                    backup_max_scrolls = max(1, max_scrolls - 1)  # Fewer scrolls
                    backup_wait_time = wait_time * random.uniform(1.5, 2.5)  # Longer waits
                    
                    newly_scraped_tweets, newest_id_from_scrape = scrape_list(
                        list_url, 
                        max_scrolls=backup_max_scrolls, 
                        wait_time=backup_wait_time,
                        browser_param=browser_monitor_backup,
                        context_param=context_monitor_backup,
                        last_tweet_id=last_tweet_id,
                        limit=limit,
                        is_backup_account=True
                    )
                    
                    if newly_scraped_tweets:
                        consecutive_error_count = 0
                        current_wait_time = base_wait_time
                        print(f"✅ BACKUP ACCOUNT: Successful request. Found {len(newly_scraped_tweets)} tweets.")
                    else:
                        print("⚠️  BACKUP ACCOUNT: No tweets found.")
                else:
                    # No session available, try to switch to backup account
                    print(f"❌ PRIMARY ACCOUNT: No session available for {primary_email}")
                    print(f"🔄 SWITCHING: Attempting to switch to backup account ({backup_email})...")
                    browser_monitor_backup, context_monitor_backup = switch_to_backup_account(pw_runtime)
                    
                    if browser_monitor_backup and context_monitor_backup:
                        print(f"✅ BACKUP ACCOUNT: Successfully switched to {backup_email}")
                        using_backup_account = True
                        
                        # Try scraping with backup account using different timing
                        print(f"🔄 SCRAPING: Using BACKUP account ({backup_email})")
                        
                        # Use different timing patterns for backup account
                        backup_max_scrolls = max(1, max_scrolls - 1)  # Fewer scrolls
                        backup_wait_time = wait_time * random.uniform(1.5, 2.5)  # Longer waits
                        
                        newly_scraped_tweets, newest_id_from_scrape = scrape_list(
                            list_url, 
                            max_scrolls=backup_max_scrolls, 
                            wait_time=backup_wait_time,
                            browser_param=browser_monitor_backup,
                            context_param=context_monitor_backup,
                            last_tweet_id=last_tweet_id,
                            limit=limit,
                            is_backup_account=True
                        )
                        
                        if newly_scraped_tweets:
                            consecutive_error_count = 0
                            current_wait_time = base_wait_time
                            print(f"✅ BACKUP ACCOUNT: Successful request. Found {len(newly_scraped_tweets)} tweets.")
                        else:
                            print("⚠️  BACKUP ACCOUNT: No tweets found.")
                    else:
                        print(f"❌ BACKUP ACCOUNT: Failed to switch to {backup_email}")
                        print("🚫 NO ACCOUNTS AVAILABLE: No tweets will be scraped this cycle.")
                        newly_scraped_tweets = []
                        newest_id_from_scrape = None
            
                if newest_id_from_scrape and (last_tweet_id is None or int(newest_id_from_scrape) > int(last_tweet_id)):
                    last_tweet_id = newest_id_from_scrape
                    save_last_tweet_id(last_tweet_id)
                
                if newly_scraped_tweets:
                    print(f"Found {len(newly_scraped_tweets)} new tweets this cycle!")
                    
                    existing_ids_json = {tweet["id"] for tweet in all_tweets_ever_saved_json}
                    unique_new_tweets_to_add_json = [
                        tweet for tweet in newly_scraped_tweets if tweet["id"] not in existing_ids_json
                    ]
                    all_tweets_ever_saved_json = unique_new_tweets_to_add_json + all_tweets_ever_saved_json
                    all_tweets_ever_saved_json.sort(key=lambda x: int(x.get("id", 0)), reverse=True)

                    # Now trim to max_history if needed
                    if len(all_tweets_ever_saved_json) > max_history:
                        all_tweets_ever_saved_json = all_tweets_ever_saved_json[:max_history]
                        print(f"Trimmed tweets history to {max_history} most recent tweets.")

                    output_data_json = {
                        "tweets": all_tweets_ever_saved_json,
                        "meta": {
                            "scraped_at": datetime.datetime.now().isoformat(),
                            "list_url": list_url,
                            "tweet_count": len(all_tweets_ever_saved_json)
                        }
                    }
                    with open(TWEETS_FILE, "w") as f_json:
                        json.dump(output_data_json, f_json, indent=2)
                    
                    saved_to_db_count = 0
                    if db_conn:
                        print(f"Saving {len(newly_scraped_tweets)} tweets to DB...")
                        for tweet_data in newly_scraped_tweets:
                            success, db_conn = save_tweet_to_db(tweet_data, db_conn)
                            if success:
                                saved_to_db_count += 1
                        print(f"Successfully saved {saved_to_db_count} new tweets to the database.")
                    
                        if saved_to_db_count > 0:
                            print("Triggering tweet analysis API...")
                            trigger_tweet_analysis()
                    else:
                        print(f"Found {len(newly_scraped_tweets)} tweets (DB connection not available).")
                    
                    for tweet in newly_scraped_tweets: 
                        username = tweet.get("user", {}).get("username", "Unknown")
                        text = tweet.get("text", "").replace("\n", " ")
                        print(f"@{username}: {text[:70]}{'...' if len(text) > 70 else ''}")
                else:
                    print("No new tweets found this cycle.")

            except PageLoadError as ple:
                current_account = "PRIMARY" if not using_backup_account else "BACKUP"
                current_email = primary_email if not using_backup_account else backup_email
                
                print(f"🚫 {current_account} ACCOUNT ERROR: Page load/scrape error for {current_email}")
                print(f"   Error details: {ple}")
                consecutive_error_count += 1
                current_wait_time = min(1800, base_wait_time * (2 ** consecutive_error_count))
                
                if "timeout" in str(ple).lower() or "wait_for_selector" in str(ple).lower():
                    print(f"⏰ RATE LIMIT DETECTED: {current_account} account ({current_email}) appears to be rate limited")
                    print(f"🔄 BACKOFF STRATEGY: Implementing exponential backoff: {current_wait_time} seconds")
                else:
                    print(f"🚫 {current_account} ACCOUNT: Generic page load error")
                    print(f"🔄 BACKOFF STRATEGY: Implementing backoff: {current_wait_time} seconds")
                
                if consecutive_error_count >= 3:
                    if not using_backup_account:
                        print(f"🔄 SWITCHING STRATEGY: Multiple errors with PRIMARY account ({primary_email})")
                        print("🔄 Attempting to switch to backup account...")
                        
                        # Try to switch to backup account
                        if backup_email:
                            browser_monitor_backup, context_monitor_backup = switch_to_backup_account(pw_runtime)
                            if browser_monitor_backup and context_monitor_backup:
                                using_backup_account = True
                                consecutive_error_count = 0  # Reset error count for backup account
                                current_wait_time = base_wait_time
                                print(f"✅ ACCOUNT SWITCH: Successfully switched to backup account ({backup_email})")
                            else:
                                print(f"❌ ACCOUNT SWITCH: Failed to switch to backup account ({backup_email})")
                        else:
                            print("❌ NO BACKUP: No backup account available for switching")
                    else:
                        print(f"🔄 BROWSER RESET: Multiple errors with BACKUP account ({backup_email})")
                        print("🔄 Reinitializing backup browser...")
                        try:
                            if browser_monitor_backup: browser_monitor_backup.close()
                        except Exception as e_cleanup: 
                            print(f"Error during backup browser cleanup: {e_cleanup}")
                        
                        time.sleep(5)
                        browser_monitor_backup, context_monitor_backup = switch_to_backup_account(pw_runtime)
                        if browser_monitor_backup and context_monitor_backup:
                            print(f"✅ BACKUP RESET: Successfully reinitialized backup account ({backup_email})")
                        else:
                            print(f"❌ BACKUP RESET: Failed to reinitialize backup account ({backup_email})")
                            using_backup_account = False
                
                if consecutive_error_count >= max_consecutive_errors:
                    print(f"🚫 MAX ERRORS REACHED: {consecutive_error_count}/{max_consecutive_errors} consecutive errors")
                    print(f"⏰ EXTENDED BACKOFF: Backing off for {current_wait_time} seconds before trying again")
                    print("💡 This is NOT fatal - monitoring will continue after backoff period")
                else:
                    print(f"⚠️  ERROR COUNT: {consecutive_error_count}/{max_consecutive_errors} consecutive errors")
                    print(f"⏰ BACKOFF: Waiting {current_wait_time} seconds before retry")
            
            except Exception as e_cycle:
                print(f"Unexpected error during scraping cycle: {e_cycle}")
                consecutive_error_count += 1
                current_wait_time = min(1800, base_wait_time * (2 ** consecutive_error_count))
                if consecutive_error_count >= max_consecutive_errors:
                    print(f"Reached maximum consecutive errors ({max_consecutive_errors}) due to unexpected error.")
                    print(f"This is NOT fatal - will continue after a {current_wait_time} second backoff period.")
                else:
                    print(f"Consecutive errors: {consecutive_error_count}/{max_consecutive_errors}. Will wait {current_wait_time} seconds.")
            
            # Calculate wait time and sleep
            elapsed_cycle = time.time() - start_time_cycle
            actual_wait_time = max(1, current_wait_time - elapsed_cycle)
            
            print(f"Waiting {int(actual_wait_time)} seconds before next check...")
            time.sleep(actual_wait_time)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user. Cleaning up resources...")
    except Exception as e_monitor: # Catches errors from setup
        print(f"Fatal error in monitor setup: {e_monitor}. Exiting.")
    finally:
        if db_conn:
            try:
                close_db_connection_safely(db_conn)
            except Exception as e_db_close:
                print(f"Error closing database connection: {e_db_close}")
        
        if browser_monitor:
            try:
                print("Shutting down browser...")
                for page in browser_monitor.contexts[0].pages:
                    try:
                        page.close(timeout=1000) 
                    except Exception:
                        pass 
                browser_monitor.close()
                print("Browser closed.")
            except Exception as e_close_browser_mon:
                print(f"Non-fatal error closing browser: {e_close_browser_mon}")
        
        if pw_runtime:
            try:
                print("Stopping Playwright...")
                pw_runtime.stop()
                print("Playwright stopped.")
            except Exception as e_stop_pw_mon:
                print(f"Non-fatal error stopping Playwright: {e_stop_pw_mon}")
        
        # Clean up backup browser resources if they exist
        if browser_monitor_backup:
            try:
                print("Shutting down backup browser...")
                browser_monitor_backup.close()
                print("Backup browser closed.")
            except Exception as e_close_backup:
                print(f"Non-fatal error closing backup browser: {e_close_backup}")
        
        print("Monitoring ended.")

def initialize_browser(headless=True, account_suffix=""):
    """Initialize a browser with a random user agent and return the components."""
    print(f"Initializing Playwright and browser{' for ' + account_suffix if account_suffix else ''}...")
    pw_runtime = sync_playwright().start()
    
    # Create browser with custom user agent to reduce detection
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    # Select a random user agent
    selected_user_agent = user_agents[int(time.time()) % len(user_agents)]
    
    browser = pw_runtime.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',  # Hide automation
            '--disable-features=IsolateOrigins,site-per-process',  # Improve stability
        ]
    )
    
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=selected_user_agent
    )
    
    # Make the browser more human-like
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
    """)
    
    print(f"Browser initialized{' for ' + account_suffix if account_suffix else ''} with user agent: {selected_user_agent}")
    return pw_runtime, browser, context

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X.com List Scraper with DB Integration")
    parser.add_argument("--url", default="https://x.com/i/lists/1919380958723158457", 
                       help="URL of the X list to scrape")
    parser.add_argument("--interval", type=int, default=60,
                       help="How often to check for new tweets (in seconds)")
    parser.add_argument("--scrolls", type=int, default=2, # Default is 3 (0, 1, 2 scrolls after initial load)
                       help="Number of additional scrolls after initial load (0 for no scrolls beyond initial load)")
    parser.add_argument("--wait", type=float, default=1.0,
                       help="Time to wait between scrolls")
    parser.add_argument("--visible", action="store_true",
                       help="Show the browser window (not headless)")
    parser.add_argument("--login", action="store_true",
                       help="Force a new login session")
    parser.add_argument("--once", action="store_true",
                       help="Run once and exit (don't monitor continuously)")
    parser.add_argument("--limit", type=int, default=10,
                       help="Maximum number of tweets to return in each check (default: 10, 0 for no limit)")
    parser.add_argument("--max-errors", type=int, default=5, help="Max consecutive errors before stopping monitor")
    parser.add_argument("--max-history", type=int, default=MAX_TWEETS_HISTORY,
                       help=f"Maximum number of tweets to keep in history (default: {MAX_TWEETS_HISTORY})")
    parser.add_argument("--use-backup", action="store_true",
                       help="Enable backup account for rate limit mitigation (requires X_EMAIL_BACKUP and X_PASSWORD_BACKUP in .env)")
    
    args = parser.parse_args()
    
    run_limit = args.limit if args.limit > 0 else None
    max_history = args.max_history if args.max_history > 0 else MAX_TWEETS_HISTORY
    
    # Handle explicit login if requested
    if args.login:
        if handle_login():
            # Check if only login was requested (no other monitoring arguments)
            if (not args.once and 
                args.url == "https://x.com/i/lists/1919380958723158457" and  # Default URL
                args.interval == 60 and  # Default interval
                args.scrolls == 2 and    # Default scrolls
                args.limit == 10):       # Default limit - essentially just --login
                print("Login completed. Run the script again without --login to start monitoring.")
                sys.exit(0)
        else:
            print("Login process didn't complete successfully. Exiting.")
            sys.exit(1)
    
    db_connection = get_db_connection()
    if not db_connection and not args.once: # If DB fails and it's not --once, maybe warn or exit if DB is critical
        print("Warning: Could not connect to database. Monitoring will proceed without DB saving.")
        # If DB is absolutely critical for monitoring, you might choose to exit here:
        # print("Critical: Database connection failed. Exiting monitor.")
        # exit(1)
    elif not db_connection and args.once:
        print("Warning: Could not connect to database. --once mode will run without DB saving.")

    if args.once:
        # For --once, we manage playwright and browser instance within this block
        with sync_playwright() as pw_once:
            browser_once = pw_once.chromium.launch(headless=not args.visible)
            context_once = browser_once.new_context(viewport={"width": 1920, "height": 1080})
            if not load_cookies(context_once):
                print("Login required for --once mode. Please run with --login first or allow login now.")
                temp_page_once = context_once.new_page()
                temp_page_once.goto("https://x.com/login")
                input("Press Enter after you have logged in and the home page is visible...")
                save_cookies(context_once)
                temp_page_once.close()
                print("Session saved for --once mode.")
            
            try:
                print(f"Scraping {args.url} once...")
                # For --once mode, we typically want all available new tweets since the last run, 
                # or all tweets if it's the first run.
                # We can use the existing last_tweet_id logic. The limit will apply to this single run.
                last_id_for_once_run = load_last_tweet_id() 
                
                tweets_scraped_once, newest_id_for_once = scrape_list(
                    args.url, 
                    max_scrolls=args.scrolls, 
                    wait_time=args.wait,
                    browser_param=browser_once,
                    context_param=context_once,
                    last_tweet_id=last_id_for_once_run,
                    limit=run_limit
                )
                
                # In --once mode, we should update the last_tweet_id if new tweets were found
                if newest_id_for_once and (last_id_for_once_run is None or int(newest_id_for_once) > int(last_id_for_once_run)):
                    save_last_tweet_id(newest_id_for_once)

                # Load any existing tweets for proper merging
                all_tweets_history = []
                if os.path.exists(TWEETS_FILE):
                    try:
                        with open(TWEETS_FILE, "r") as f:
                            saved_data = json.load(f)
                            if isinstance(saved_data, dict) and "tweets" in saved_data:
                                all_tweets_history = saved_data["tweets"]
                            elif isinstance(saved_data, list):
                                all_tweets_history = saved_data
                    except Exception as e:
                        print(f"Error loading existing tweets: {e}")
                
                # Merge tweets while avoiding duplicates
                existing_ids = {tweet["id"] for tweet in all_tweets_history}
                unique_new_tweets = [tweet for tweet in tweets_scraped_once if tweet["id"] not in existing_ids]
                all_tweets_history = unique_new_tweets + all_tweets_history
                
                # Sort and trim
                all_tweets_history.sort(key=lambda x: int(x.get("id", 0)), reverse=True)
                if len(all_tweets_history) > max_history:
                    all_tweets_history = all_tweets_history[:max_history]
                    print(f"Trimmed tweets history to {max_history} most recent tweets.")

                # Save tweets.json with meta structure.
                output_data_once_json = {
                    "tweets": all_tweets_history,
                    "meta": {
                        "scraped_at": datetime.datetime.now().isoformat(),
                        "list_url": args.url,
                        "tweet_count": len(all_tweets_history)
                    }
                }
                with open(TWEETS_FILE, "w") as f_json_once:
                    json.dump(output_data_once_json, f_json_once, indent=2)
                
                print(f"Saved {len(tweets_scraped_once)} new tweets (total: {len(all_tweets_history)}) to {TWEETS_FILE}")
                
                # Add saving to database in --once mode
                saved_to_db_count = 0
                if db_connection and tweets_scraped_once:
                    print(f"Saving {len(tweets_scraped_once)} tweets to database...")
                    for tweet_data in tweets_scraped_once:
                        success, db_connection = save_tweet_to_db(tweet_data, db_connection)
                        if success:
                            saved_to_db_count += 1
                    print(f"Successfully saved {saved_to_db_count} tweets to database.")
                    
                    # If any tweets were saved to the database, trigger the analysis API
                    if saved_to_db_count > 0:
                        print("Triggering tweet analysis API...")
                        trigger_tweet_analysis()
                
            finally:
                # Always clean up database connection in --once mode
                close_db_connection_safely(db_connection)
            
            browser_once.close()
            pw_once.stop()
    else:
        monitor_list_real_time(
            db_connection, args.url, args.interval, args.scrolls, 
            args.wait, not args.visible, run_limit, args.max_errors, max_history
        )