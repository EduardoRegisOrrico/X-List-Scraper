#!/usr/bin/env python3
import requests
import subprocess
import json

def test_twitter_access():
    print("=== TWITTER ACCESSIBILITY TEST ===\n")
    
    # Get current IP
    try:
        ip_result = subprocess.run(['curl', '-s', 'https://ipinfo.io/ip'], 
                                 capture_output=True, text=True)
        current_ip = ip_result.stdout.strip()
        print(f"🌐 Current IP: {current_ip}")
    except:
        current_ip = "unknown"
    
    # Test Twitter main page
    print("\n📋 Testing Twitter access...")
    try:
        response = requests.get('https://x.com/', timeout=10)
        print(f"✅ x.com - Status: {response.status_code}")
        if response.status_code == 403:
            print("   🚨 IP appears to be blocked!")
        elif response.status_code == 200:
            print("   ✅ IP can access Twitter")
    except Exception as e:
        print(f"❌ x.com - Error: {e}")
    
    # Test specific list
    print("\n📋 Testing specific list...")
    list_url = "https://x.com/i/lists/1919380958723158457"
    try:
        response = requests.get(list_url, timeout=10)
        print(f"✅ List URL - Status: {response.status_code}")
        if response.status_code == 403:
            print("   🚨 List access blocked!")
        elif response.status_code == 200:
            print("   ✅ List accessible")
            print(f"   📄 Content length: {len(response.content)} bytes")
    except Exception as e:
        print(f"❌ List URL - Error: {e}")

if __name__ == "__main__":
    test_twitter_access()
