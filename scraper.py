import json
import time
import os
import datetime
import argparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SESSION_FILE = "x_session.json"
TWEETS_FILE = "tweets.json"
LAST_ID_FILE = "last_tweet_id.txt"

def save_cookies(context):
    cookies = context.cookies()
    with open(SESSION_FILE, "w") as f:
        json.dump(cookies, f)

def load_cookies(context):
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        return True
    return False

def save_last_tweet_id(tweet_id):
    """Save the most recent tweet ID to file"""
    with open(LAST_ID_FILE, "w") as f:
        f.write(tweet_id)

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
    
    # Extract base tweet data
    tweet_data = {
        "id": tweet_content.get("rest_id"),
        "created_at": tweet_content.get("legacy", {}).get("created_at"),
        "text": tweet_content.get("legacy", {}).get("full_text"),
        "lang": tweet_content.get("legacy", {}).get("lang"),
    }
    
    # Extract user data
    user = tweet_content.get("core", {}).get("user_results", {}).get("result", {})
    if user:
        tweet_data["user"] = {
            "id": user.get("rest_id"),
            "name": user.get("legacy", {}).get("name"),
            "username": user.get("legacy", {}).get("screen_name"),
            "verified": user.get("legacy", {}).get("verified", False),
            "is_blue_verified": user.get("is_blue_verified", False),
            "followers_count": user.get("legacy", {}).get("followers_count"),
            "profile_image_url": user.get("legacy", {}).get("profile_image_url_https"),
        }
    
    # Extract engagement stats
    legacy = tweet_content.get("legacy", {})
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
            media_obj = {
                "type": media.get("type"),
                "url": media.get("media_url_https"),
                "expanded_url": media.get("expanded_url"),
            }
            tweet_data["media"].append(media_obj)
    
    # Extract mentions, hashtags, and urls
    tweet_data["entities"] = {}
    entities = legacy.get("entities", {})
    
    if "user_mentions" in entities:
        tweet_data["entities"]["mentions"] = [
            {"screen_name": mention.get("screen_name"), "id": mention.get("id_str")}
            for mention in entities.get("user_mentions", [])
        ]
    
    if "hashtags" in entities:
        tweet_data["entities"]["hashtags"] = [
            hashtag.get("text") for hashtag in entities.get("hashtags", [])
        ]
    
    if "urls" in entities:
        tweet_data["entities"]["urls"] = [
            {"expanded_url": url.get("expanded_url"), "display_url": url.get("display_url")}
            for url in entities.get("urls", [])
        ]
    
    return tweet_data

def _process_xhr_calls(xhr_calls, last_tweet_id, limit, seen_ids, current_tweets):
    """Helper function to process XHR calls and extract tweets."""
    newly_found_tweets = []
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
                                            newly_found_tweets.append(extracted_tweet)
                                            current_tweets.append(extracted_tweet)
                                        
                                        if newest_id_this_batch is None or (tweet_id and int(tweet_id) > int(newest_id_this_batch)):
                                            newest_id_this_batch = tweet_id

                                        if limit and len(current_tweets) >= limit:
                                            return newly_found_tweets, newest_id_this_batch, True # Limit reached
                            except KeyError as e:
                                print(f"Error extracting tweet data: {e}")
                if limit and len(current_tweets) >= limit:
                    return newly_found_tweets, newest_id_this_batch, True # Limit reached
            if limit and len(current_tweets) >= limit:
                return newly_found_tweets, newest_id_this_batch, True # Limit reached
        except Exception as e:
            print(f"Error parsing XHR: {e}")
    return newly_found_tweets, newest_id_this_batch, False # Limit not reached

def scrape_list(list_url, max_scrolls=3, wait_time=1, browser=None, context=None, last_tweet_id=None, limit=None):
    _xhr_calls_buffer = [] 
    all_new_tweets_metadata = []
    overall_newest_id = last_tweet_id
    seen_ids = set()
    should_close_browser = False

    def intercept_response(response):
        if response.request.resource_type == "xhr":
            if "ListLatestTweetsTimeline" in response.url or "Timeline" in response.url:
                _xhr_calls_buffer.append(response)

    if browser is None:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        should_close_browser = True
        if not load_cookies(context):
            print("No session found. Please run with --login first.")
            if should_close_browser:
                browser.close()
                playwright.stop()
            return [], last_tweet_id # Return empty and original newest_id

    page = context.new_page()
    page.on("response", intercept_response)

    page.goto(list_url)
    try:
        page.wait_for_selector("[data-testid='cellInnerDiv']", timeout=15000)
    except PlaywrightTimeoutError:
        print("Timeout waiting for initial tweets to load.")
        page.close()
        if should_close_browser:
            browser.close()
            playwright.stop()
        return [], last_tweet_id

    for i in range(max_scrolls):
        if i > 0: # Only scroll after the first load/check
            print(f"Scrolling... ({i}/{max_scrolls -1 })")
            page.mouse.wheel(0, 2000)
            time.sleep(wait_time)
        else:
            # Initial load, give a bit of time for XHRs
            time.sleep(max(wait_time, 1)) # Ensure at least 1 sec for initial XHRs
            print("Initial page load check...")

        # Process buffered XHR calls for this scroll iteration
        processed_xhr_this_scroll, newest_id_this_batch, limit_reached = _process_xhr_calls(
            _xhr_calls_buffer,
            last_tweet_id,
            limit,
            seen_ids,
            all_new_tweets_metadata 
        )
        _xhr_calls_buffer.clear() # Clear buffer after processing

        if newest_id_this_batch and (overall_newest_id is None or int(newest_id_this_batch) > int(overall_newest_id)):
            overall_newest_id = newest_id_this_batch

        if limit_reached:
            print("Limit reached, stopping scroll for this cycle.")
            break 
        
        if i == 0 and not processed_xhr_this_scroll and last_tweet_id is not None:
            # If it's the first check (i=0), no new tweets were found beyond last_tweet_id,
            # and this isn't the very first run ever (last_tweet_id exists),
            # then further scrolls in this cycle are unlikely to yield new tweets.
            print("No new tweets found on initial check, skipping further scrolls for this cycle.")
            break

    page.close()

    if should_close_browser:
        browser.close()
        playwright.stop()
    
    all_new_tweets_metadata.sort(key=lambda x: int(x.get("id", 0)), reverse=True)
    # Limit is already applied within _process_xhr_calls for efficiency, 
    # but a final check ensures it if tweets came from multiple scrolls.
    if limit and len(all_new_tweets_metadata) > limit:
        all_new_tweets_metadata = all_new_tweets_metadata[:limit]
        
    return all_new_tweets_metadata, overall_newest_id


def monitor_list_real_time(list_url, interval=60, max_scrolls=3, wait_time=1, headless=True, limit=None):
    last_tweet_id = load_last_tweet_id()
    all_tweets_ever_saved = [] # This will store all tweets from tweets.json plus new ones

    if os.path.exists(TWEETS_FILE):
        try:
            with open(TWEETS_FILE, "r") as f:
                # The file now stores a dict: {"tweets": [...], "meta": {...}}
                # We only care about the list of tweets for merging.
                saved_data = json.load(f)
                if isinstance(saved_data, dict) and "tweets" in saved_data:
                    all_tweets_ever_saved = saved_data["tweets"]
                elif isinstance(saved_data, list): # Handle old format if present
                    all_tweets_ever_saved = saved_data
        except Exception as e:
            print(f"Error loading existing tweets file ({TWEETS_FILE}): {e}. Starting fresh.")
            all_tweets_ever_saved = []
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        
        if not load_cookies(context):
            print("Please log in to X.com in the opened browser window.")
            temp_page = context.new_page()
            temp_page.goto("https://x.com/login")
            input("Press Enter after you have logged in and the home page is visible...")
            save_cookies(context)
            temp_page.close()
            print("Session saved.")
        
        try:
            print(f"Starting real-time monitoring of {list_url}")
            print(f"Checking for new tweets every {interval} seconds")
            if limit:
                print(f"Limited to {limit} new tweets per check")
            if last_tweet_id:
                print(f"Last seen tweet ID: {last_tweet_id}")
            
            while True:
                start_time = time.time()
                print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new tweets...")
                
                newly_scraped_tweets, newest_id_from_scrape = scrape_list(
                    list_url, 
                    max_scrolls=max_scrolls, 
                    wait_time=wait_time,
                    browser=browser,
                    context=context,
                    last_tweet_id=last_tweet_id,
                    limit=limit
                )
                
                if newest_id_from_scrape and (last_tweet_id is None or int(newest_id_from_scrape) > int(last_tweet_id)):
                    last_tweet_id = newest_id_from_scrape
                    save_last_tweet_id(last_tweet_id)
                
                if newly_scraped_tweets:
                    print(f"Found {len(newly_scraped_tweets)} new tweets!")
                    
                    # Merge new tweets with previously saved ones, avoiding duplicates
                    existing_ids = {tweet["id"] for tweet in all_tweets_ever_saved}
                    unique_new_tweets_to_add = [
                        tweet for tweet in newly_scraped_tweets if tweet["id"] not in existing_ids
                    ]
                    all_tweets_ever_saved = unique_new_tweets_to_add + all_tweets_ever_saved
                    # Sort all tweets by ID again to ensure overall order
                    all_tweets_ever_saved.sort(key=lambda x: int(x.get("id", 0)), reverse=True)

                    # Prepare data for saving (including meta)
                    output_data = {
                        "tweets": all_tweets_ever_saved,
                        "meta": {
                            "scraped_at": datetime.datetime.now().isoformat(),
                            "list_url": list_url,
                            "tweet_count": len(all_tweets_ever_saved)
                        }
                    }
                    with open(TWEETS_FILE, "w") as f:
                        json.dump(output_data, f, indent=2)
                    
                    for tweet in newly_scraped_tweets: # Only print the ones just found
                        username = tweet.get("user", {}).get("username", "Unknown")
                        text = tweet.get("text", "").replace("\n", " ")
                        print(f"@{username}: {text[:100]}{'...' if len(text) > 100 else ''}")
                else:
                    print("No new tweets found this cycle.")
                
                elapsed = time.time() - start_time
                wait_seconds = max(1, interval - elapsed)
                print(f"Waiting {int(wait_seconds)} seconds before next check...")
                time.sleep(wait_seconds)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
        finally:
            browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X.com List Scraper")
    parser.add_argument("--url", default="https://x.com/i/lists/1919380958723158457", 
                       help="URL of the X list to scrape")
    parser.add_argument("--interval", type=int, default=60,
                       help="How often to check for new tweets (in seconds)")
    parser.add_argument("--scrolls", type=int, default=3, # Default is 3 (0, 1, 2 scrolls after initial load)
                       help="Number of additional scrolls after initial load (0 for no scrolls beyond initial load)")
    parser.add_argument("--wait", type=float, default=1,
                       help="Time to wait between scrolls")
    parser.add_argument("--visible", action="store_true",
                       help="Show the browser window (not headless)")
    parser.add_argument("--login", action="store_true",
                       help="Force a new login session")
    parser.add_argument("--once", action="store_true",
                       help="Run once and exit (don't monitor continuously)")
    parser.add_argument("--limit", type=int, default=10,
                       help="Maximum number of tweets to return in each check (default: 10, 0 for no limit)")
    
    args = parser.parse_args()
    
    limit_arg = args.limit if args.limit > 0 else None
    
    if args.login and os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
        print("Removed existing session. You will be prompted to log in.")
    
    if args.once:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=not args.visible)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            if not load_cookies(context):
                print("Please log in to X.com in the opened browser window.")
                temp_page = context.new_page()
                temp_page.goto("https://x.com/login")
                input("Press Enter after you have logged in and the home page is visible...")
                save_cookies(context)
                temp_page.close()
                print("Session saved.")
            
            print(f"Scraping {args.url} once...")
            # For --once mode, we typically want all available new tweets since the last run, 
            # or all tweets if it's the first run.
            # We can use the existing last_tweet_id logic. The limit will apply to this single run.
            last_id_for_once_run = load_last_tweet_id() 
            
            tweets, newest_id_for_once = scrape_list(
                args.url, 
                max_scrolls=args.scrolls, 
                wait_time=args.wait,
                browser=browser,
                context=context,
                last_tweet_id=last_id_for_once_run,
                limit=limit_arg
            )
            
            # In --once mode, we should update the last_tweet_id if new tweets were found
            if newest_id_for_once and (last_id_for_once_run is None or int(newest_id_for_once) > int(last_id_for_once_run)):
                save_last_tweet_id(newest_id_for_once)

            # Save tweets.json with meta structure.
            output_data_once = {
                "tweets": tweets,
                "meta": {
                    "scraped_at": datetime.datetime.now().isoformat(),
                    "list_url": args.url,
                    "tweet_count": len(tweets)
                }
            }
            with open(TWEETS_FILE, "w") as f:
                json.dump(output_data_once, f, indent=2)
            
            print(f"Saved {len(tweets)} tweets to {TWEETS_FILE}")
            browser.close()
    else:
        monitor_list_real_time(
            args.url,
            interval=args.interval,
            max_scrolls=args.scrolls,
            wait_time=args.wait,
            headless=not args.visible,
            limit=limit_arg
        )