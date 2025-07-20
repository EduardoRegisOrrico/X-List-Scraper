# Enhanced Twitter Scraper with Backup Account Support

This enhanced version of the scraper includes automatic backup account switching to avoid rate limits and improve reliability.

## Features

- **Automatic Account Switching**: Switches to backup account when primary is rate limited
- **Session Management**: Saves login sessions for both accounts
- **Rate Limit Detection**: Automatically detects and handles rate limiting
- **Seamless Fallback**: Uses backup account transparently when needed
- **Database Integration**: Full compatibility with existing database and API integration

## Setup

### 1. Configure Backup Account Credentials

Add backup account credentials to your `.env` file:

```bash
# Primary Account (existing)
X_EMAIL=your_primary_email@example.com
X_PASSWORD=your_primary_password

# Backup Account (new - should be a DIFFERENT Twitter account)
X_EMAIL_BACKUP=your_backup_email@example.com
X_PASSWORD_BACKUP=your_backup_password
```

### 2. Run Setup Script

```bash
python setup_backup_credentials.py
```

This interactive script will:
- Help you configure backup account credentials
- Verify the setup is correct
- Save credentials securely to your .env file

### 3. Test the Setup

```bash
python test_backup_switching.py
```

This will test:
- Credential configuration
- Backup account login
- Account switching functionality
- Basic scraping with backup account

## Usage

The backup account functionality is now integrated directly into the main scraper. Use your existing commands:

### Basic Scraping (One-time)
```bash
python scraper.py --url "https://x.com/i/lists/YOUR_LIST_ID" --once
```

### Continuous Monitoring
```bash
python scraper.py --url "https://x.com/i/lists/YOUR_LIST_ID" --interval 60
```

### With Visible Browser (for debugging)
```bash
python scraper.py --url "https://x.com/i/lists/YOUR_LIST_ID" --visible
```

### Enable Backup Account (optional flag)
```bash
python scraper.py --url "https://x.com/i/lists/YOUR_LIST_ID" --use-backup
```

## How It Works

1. **Account Initialization**: Both accounts login and save sessions
2. **Smart Selection**: Always uses the least recently used, non-rate-limited account
3. **Rate Limit Detection**: When an account gets rate limited, it's marked as unavailable
4. **Automatic Switching**: Seamlessly switches to backup account when needed
5. **Cooldown Management**: Tracks rate limit cooldowns and reactivates accounts when ready

## Rate Limit Strategy

- **Primary Account Rate Limited**: Automatically switches to backup account
- **Both Accounts Rate Limited**: Waits for cooldown periods to expire
- **Cooldown Periods**: 5 minutes for no results, 10 minutes for explicit rate limit errors
- **Account Rotation**: Uses least recently used account to distribute load

## Output

Tweets are saved to `tweets.json` with the same structure as before:

```json
{
  "tweets": [
    {
      "id": "1234567890",
      "text": "Tweet content...",
      "username": "twitter_user",
      "created_at": "Wed Jan 01 12:00:00 +0000 2025",
      "user": {
        "username": "twitter_user",
        "name": "Display Name",
        "verified": false
      }
    }
  ],
  "meta": {
    "scraped_at": "2025-01-01T12:00:00",
    "list_url": "https://x.com/i/lists/1234567890",
    "tweet_count": 1
  }
}
```

## Advantages Over Single Account

1. **Higher Throughput**: Can scrape more frequently without hitting limits
2. **Better Reliability**: Backup account ensures continuous operation
3. **Reduced Downtime**: Minimal interruption when rate limits are hit
4. **Load Distribution**: Spreads requests across multiple accounts

## Best Practices

1. **Use Different Email Providers**: Don't use the same email provider for both accounts
2. **Different IP Addresses**: Consider using accounts created from different locations
3. **Account Age**: Older accounts typically have higher rate limits
4. **Realistic Intervals**: Don't set intervals too low (recommended: 60+ seconds)
5. **Monitor Logs**: Watch for rate limit patterns and adjust accordingly

## Troubleshooting

### "No accounts available"
- Both accounts are rate limited
- Wait for cooldown periods to expire
- Check if accounts are still valid

### Login failures
- Verify credentials in `.env` file
- Check if accounts require 2FA (not currently supported)
- Ensure accounts aren't locked or suspended

### No tweets found
- Verify the list URL is correct and public
- Check if accounts have access to the list
- Ensure the list contains recent tweets

## Integration with Existing System

The multi-account scraper can work alongside your existing scraper:

1. **Replace calls** to `scraper.py` with `multi_account_scraper.py`
2. **Same output format** - tweets are saved in compatible JSON format
3. **Same command line options** - most arguments work the same way
4. **Database integration** - can be added similar to the original scraper

## Security Notes

- Session files contain authentication cookies - keep them secure
- Use strong, unique passwords for both accounts
- Consider using app-specific passwords if available
- Regularly rotate credentials for security