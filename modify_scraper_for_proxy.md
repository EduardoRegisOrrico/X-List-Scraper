# How to Modify Your Scraper for Proxy Support

## 1. Update your Playwright browser launch
```python
# In your scraper.py or multi_account_scraper.py
proxy_settings = {
    'server': 'http://gate.smartproxy.com:7000',
    'username': 'sp-your-username',
    'password': 'your-password'
}

browser = await playwright.chromium.launch(
    headless=True,
    proxy=proxy_settings,
    args=['--no-sandbox', '--disable-dev-shm-usage']
)
```

## 2. Add proxy rotation logic
```python
import random

PROXY_LIST = [
    {'server': 'http://gate.smartproxy.com:7000', 'username': 'sp-user1', 'password': 'pass1'},
    {'server': 'http://gate.smartproxy.com:7001', 'username': 'sp-user2', 'password': 'pass2'},
    # Add more proxy endpoints
]

def get_random_proxy():
    return random.choice(PROXY_LIST)
```

## 3. Test proxy before scraping
```python
async def test_proxy(proxy_config):
    try:
        browser = await playwright.chromium.launch(proxy=proxy_config)
        page = await browser.new_page()
        response = await page.goto('https://httpbin.org/ip')
        ip_info = await page.text_content('pre')
        await browser.close()
        print(f"Proxy working, IP: {ip_info}")
        return True
    except Exception as e:
        print(f"Proxy failed: {e}")
        return False
```
