# Static vs Rotating Residential Proxies for Twitter Scraping

## STATIC RESIDENTIAL PROXIES

### What They Are:
- Fixed IP addresses from real residential connections
- Same IP for extended periods (weeks/months)
- You get dedicated IPs that don't change

### Pros:
- Cheaper than rotating residential (~50-70% less cost)
- Consistent session management
- Better for account-based scraping
- No IP rotation complexity
- Good for maintaining login sessions

### Cons:
- Higher risk of getting that specific IP blocked
- Once blocked, you're stuck until IP changes
- Limited to small pool of IPs
- Single point of failure

### Pricing Examples:
- Bright Data: ~$300/month (vs $500 for rotating)
- Smartproxy: ~$100/month (vs $200 for rotating)
- ProxyRack: ~$80/month (vs $160 for rotating)

### Success Rate for Twitter: ~60-75%
- Better than datacenter, worse than rotating residential
- Risk increases with usage volume

## ROTATING RESIDENTIAL PROXIES

### What They Are:
- IP changes with each request or session
- Large pool of residential IPs
- Automatic rotation to avoid blocks

### Pros:
- Much harder to block (new IP each time)
- Higher success rates
- Better for high-volume scraping
- Built-in redundancy

### Cons:
- More expensive
- Session management complexity
- May break authentication flows

### Success Rate for Twitter: ~85-95%
- Best balance of cost vs performance
- Handles blocks automatically

## RECOMMENDATION FOR YOUR CASE:

Given your Twitter scraping needs, I'd suggest:

## MY RECOMMENDATION FOR YOUR TWITTER SCRAPER:

### START WITH STATIC RESIDENTIAL - HERE'S WHY:

1. **Your Use Case Fits**:
   - You're scraping a specific list, not massive data
   - You have account sessions to maintain
   - Budget considerations are important

2. **Testing Strategy**:
   - Get 2-3 static residential IPs from different regions
   - Rotate them manually in your code
   - Much cheaper than full rotating service

3. **Implementation Approach**:
```python
STATIC_RESIDENTIAL_PROXIES = [
    {
        'server': 'residential-proxy1.provider.com:8000',
        'username': 'user1', 'password': 'pass1',
        'region': 'US-East', 'last_used': None
    },
    {
        'server': 'residential-proxy2.provider.com:8001', 
        'username': 'user2', 'password': 'pass2',
        'region': 'US-West', 'last_used': None
    },
    {
        'server': 'residential-proxy3.provider.com:8002',
        'username': 'user3', 'password': 'pass3', 
        'region': 'Canada', 'last_used': None
    }
]

def get_next_proxy():
    # Simple round-robin with cooldown
    available = [p for p in STATIC_RESIDENTIAL_PROXIES 
                 if not p['last_used'] or 
                 time.time() - p['last_used'] > 300]  # 5min cooldown
    
    if available:
        proxy = available[0]
        proxy['last_used'] = time.time()
        return proxy
    else:
        # All proxies recently used, wait or use oldest
        return min(STATIC_RESIDENTIAL_PROXIES, 
                  key=lambda x: x['last_used'] or 0)
```

4. **Cost-Benefit Analysis**:
   - Static Residential: ~$100-150/month for 3 IPs
   - Rotating Residential: ~$200-300/month
   - Success rate difference: ~10-20%

### PROVIDERS OFFERING STATIC RESIDENTIAL:

1. **Bright Data**: Premium quality, higher cost
2. **Oxylabs**: Good balance of price/performance  
3. **ProxyRack**: Budget-friendly option
4. **NetNut**: Specialized in static residential
5. **IPRoyal**: Affordable with good performance

### FALLBACK PLAN:
If static residential gets blocked after a few weeks:
- Upgrade to rotating residential
- Add more static IPs to your pool
- Mix static + rotating approach
