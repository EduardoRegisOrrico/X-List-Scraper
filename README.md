# X.com List Scraper

A Python script that uses Playwright to scrape tweets from X.com (Twitter) lists by intercepting XHR requests. **Now with real-time monitoring support!**

## Features

- **Real-time monitoring**: Checks for new tweets at regular intervals
- **Only fetches new content**: Tracks tweet IDs to avoid duplicates
- Extracts only relevant tweet metadata (not the full JSON response)
- Handles login/session management
- Scrolls to load more tweets
- Saves tweets to a structured JSON file

## Installation

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install playwright
   playwright install
   ```

## Usage

### First Run / Login

For first-time use or to create a new login session:

```bash
python scraper.py --login
```

This will open a browser window for you to log in to X.com. After logging in, press Enter in the terminal to save your session.

### Real-Time Monitoring

To continuously check for new tweets and output them in real-time:

```bash
python scraper.py 
```

The script will check for new tweets every 60 seconds by default and display them in the terminal.

### Command Line Options

```bash
python scraper.py [options]
```

Options:
- `--url URL`: URL of the X list to scrape (default: https://x.com/i/lists/1919380958723158457)
- `--interval SECONDS`: How often to check for new tweets (default: 60 seconds)
- `--scrolls N`: Number of times to scroll the page (default: 3)
- `--wait SECONDS`: Time to wait between scrolls (default: 1 second)
- `--visible`: Show the browser window instead of running headless
- `--login`: Force a new login session
- `--once`: Run once and exit (don't monitor continuously)
- `--limit N`: Maximum number of tweets to fetch per check (default: 10, use 0 for no limit)

### Examples

```bash
# Monitor a different list every 30 seconds with the browser visible
python scraper.py --url "https://x.com/i/lists/your-list-id" --interval 30 --visible

# Scrape once with 5 scrolls and exit
python scraper.py --once --scrolls 5

# Run headless with quick scrolling to check every 15 seconds
python scraper.py --interval 15 --wait 0.5

# Get a maximum of 5 tweets per check
python scraper.py --limit 5

# Get all available tweets (no limit)
python scraper.py --limit 0
```

## How It Works

1. **Tweet Tracking**: The script saves the ID of the newest tweet found in `last_tweet_id.txt`
2. **Incremental Scraping**: On each run, only tweets newer than the last saved ID are collected
3. **Real-time Output**: New tweets are displayed in the terminal as they are found
4. **Continuous Saving**: All tweets are saved to `tweets.json`, with newest tweets first

## Output Format

Each tweet in `tweets.json` contains:

```json
{
  "id": "tweet_id",
  "created_at": "timestamp",
  "text": "tweet_text",
  "lang": "en",
  "user": {
    "id": "user_id",
    "name": "User Name",
    "username": "username",
    "verified": false,
    "is_blue_verified": true,
    "followers_count": 123456,
    "profile_image_url": "url_to_profile_image"
  },
  "stats": {
    "retweet_count": 123,
    "reply_count": 456,
    "like_count": 789,
    "quote_count": 10,
    "bookmark_count": 5,
    "view_count": "12345"
  },
  "media": [
    {
      "type": "photo",
      "url": "media_url",
      "expanded_url": "tweet_url"
    }
  ],
  "entities": {
    "mentions": [{"screen_name": "username", "id": "user_id"}],
    "hashtags": ["hashtag1", "hashtag2"],
    "urls": [{"expanded_url": "url", "display_url": "displayed_url"}]
  }
}
``` 