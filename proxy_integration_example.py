# Example: Integrating rotating proxies with your scraper

import requests
import random

# Example configuration for Bright Data/Oxylabs
PROXY_CONFIG = {
    'bright_data': {
        'endpoint': 'brd-customer-hl_xxxxx-zone-residential:your_password@brd.superproxy.io:22225',
        'session_id': None  # Auto-rotating
    },
    'oxylabs': {
        'endpoint': 'pr.oxylabs.io:7777',
        'username': 'customer-username-cc-US',
        'password': 'your_password'
    }
}

def get_proxy_config(service='bright_data'):
    if service == 'bright_data':
        return {
            'http': f"http://{PROXY_CONFIG['bright_data']['endpoint']}",
            'https': f"http://{PROXY_CONFIG['bright_data']['endpoint']}"
        }
    elif service == 'oxylabs':
        auth = (PROXY_CONFIG['oxylabs']['username'], PROXY_CONFIG['oxylabs']['password'])
        return {
            'http': f"http://{PROXY_CONFIG['oxylabs']['endpoint']}",
            'https': f"http://{PROXY_CONFIG['oxylabs']['endpoint']}",
            'auth': auth
        }

# Integration with your existing scraper
def scrape_with_proxy():
    proxies = get_proxy_config('bright_data')
    
    try:
        response = requests.get(
            'https://x.com/i/lists/1919380958723158457',
            proxies=proxies,
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        print(f"Status: {response.status_code}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

# For Playwright integration (your current setup)
def setup_playwright_with_proxy():
    proxy_config = {
        'server': 'http://brd.superproxy.io:22225',
        'username': 'brd-customer-hl_xxxxx-zone-residential',
        'password': 'your_password'
    }
    return proxy_config
