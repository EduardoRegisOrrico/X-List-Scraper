#!/usr/bin/env python3

def calculate_twitter_scraping_traffic():
    print("=== TWITTER SCRAPING TRAFFIC CALCULATION ===\n")
    
    # Typical data sizes for Twitter scraping
    twitter_page_size = 2.5  # MB (average Twitter list page with tweets)
    tweet_api_response = 0.1  # MB (typical API response with 20 tweets)
    images_media = 0.5  # MB (if downloading tweet images/media)
    
    print("📊 TYPICAL DATA SIZES:")
    print(f"   Twitter list page: ~{twitter_page_size} MB")
    print(f"   API response (20 tweets): ~{tweet_api_response} MB") 
    print(f"   Media/images per page: ~{images_media} MB")
    
    # Your current scraping pattern
    checks_per_hour = 30  # Every 2 seconds = 1800 checks/hour, but limited by rate limits
    realistic_successful_checks = 10  # After rate limiting
    hours_per_day = 24
    
    print(f"\n🔄 YOUR SCRAPING PATTERN:")
    print(f"   Realistic successful checks/hour: {realistic_successful_checks}")
    print(f"   Hours per day: {hours_per_day}")
    
    # Daily traffic calculation
    daily_page_loads = realistic_successful_checks * hours_per_day
    daily_traffic_mb = daily_page_loads * twitter_page_size
    daily_traffic_gb = daily_traffic_mb / 1024
    
    print(f"\n📈 DAILY USAGE:")
    print(f"   Page loads per day: {daily_page_loads}")
    print(f"   Daily traffic: {daily_traffic_gb:.2f} GB")
    
    # Monthly calculation
    monthly_traffic_gb = daily_traffic_gb * 30
    print(f"\n📅 MONTHLY USAGE:")
    print(f"   Monthly traffic: {monthly_traffic_gb:.1f} GB")
    
    # 50GB analysis
    print(f"\n🎯 50GB PACKAGE ANALYSIS:")
    days_covered = 50 / daily_traffic_gb
    print(f"   50GB would last: {days_covered:.1f} days")
    
    if monthly_traffic_gb <= 50:
        print(f"   ✅ 50GB is MORE than enough!")
        print(f"   📊 You'd use ~{(monthly_traffic_gb/50)*100:.1f}% of the package")
    else:
        print(f"   ❌ 50GB is NOT enough")
        print(f"   📊 You'd need ~{monthly_traffic_gb:.1f}GB/month")
    
    # Scenarios
    print(f"\n📋 DIFFERENT SCENARIOS:")
    
    scenarios = [
        ("Light usage (5 checks/hour)", 5),
        ("Current usage (10 checks/hour)", 10), 
        ("Heavy usage (20 checks/hour)", 20),
        ("Aggressive (50 checks/hour)", 50)
    ]
    
    for name, checks in scenarios:
        daily_gb = (checks * 24 * twitter_page_size) / 1024
        monthly_gb = daily_gb * 30
        print(f"   {name}: {monthly_gb:.1f} GB/month")

if __name__ == "__main__":
    calculate_twitter_scraping_traffic()
