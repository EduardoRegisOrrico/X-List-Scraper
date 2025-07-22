#!/usr/bin/env python3
"""
Test script to verify Decodo proxy functionality
"""
import requests
import time

# Decodo proxy configuration
DECODO_USERNAME = "sp5v4mxxv9"
DECODO_PASSWORD = "ff9tilito8IEq9E_1Y"
DECODO_HOST = "isp.decodo.com"
DECODO_PORTS = [10001, 10002, 10003]

def test_decodo_proxy():
    """Test all Decodo proxy ports"""
    print("🔗 Testing Decodo Proxy Service")
    print("=" * 50)
    
    # Test direct connection first
    try:
        print("🌐 Testing direct connection...")
        direct_response = requests.get('https://httpbin.org/ip', timeout=10)
        direct_ip = direct_response.json().get('origin', 'Unknown')
        print(f"✅ Direct IP: {direct_ip}")
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return False
    
    print("\n🔗 Testing proxy connections...")
    working_proxies = []
    
    for i, port in enumerate(DECODO_PORTS):
        try:
            proxy_url = f"http://{DECODO_USERNAME}:{DECODO_PASSWORD}@{DECODO_HOST}:{port}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            print(f"Testing port {port}...")
            response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=15)
            proxy_ip = response.json().get('origin', 'Unknown')
            
            if proxy_ip != direct_ip:
                print(f"✅ Port {port}: Working - IP: {proxy_ip}")
                working_proxies.append((port, proxy_ip))
            else:
                print(f"⚠️  Port {port}: Same IP as direct connection - {proxy_ip}")
                
        except Exception as e:
            print(f"❌ Port {port}: Failed - {e}")
    
    print(f"\n📊 Summary:")
    print(f"Direct IP: {direct_ip}")
    print(f"Working proxies: {len(working_proxies)}/{len(DECODO_PORTS)}")
    
    if working_proxies:
        print("✅ Decodo proxy service is working!")
        for port, ip in working_proxies:
            print(f"   Port {port}: {ip}")
        return True
    else:
        print("❌ No working proxies found!")
        return False

if __name__ == "__main__":
    test_decodo_proxy()