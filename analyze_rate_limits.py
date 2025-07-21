#!/usr/bin/env python3
"""
Rate Limit Analysis Tool
Analyzes captured rate limit events to understand patterns and suggest solutions.
"""

import sys
import os
from rate_limit_debugger import RateLimitDebugger

def main():
    print("🔍 RATE LIMIT ANALYSIS TOOL")
    print("=" * 50)
    
    debugger = RateLimitDebugger()
    
    if not debugger.events:
        print("❌ No rate limit events found.")
        print("💡 Run the scraper first to capture rate limit events.")
        return
    
    print(f"📊 Found {len(debugger.events)} rate limit events")
    print("\n🔍 ANALYZING PATTERNS...")
    
    # Print detailed analysis
    debugger.print_analysis()
    
    # Show recent events
    print("\n📋 RECENT EVENTS:")
    print("-" * 50)
    
    recent_events = sorted(debugger.events, key=lambda x: x.timestamp, reverse=True)[:5]
    
    for i, event in enumerate(recent_events, 1):
        print(f"\n{i}. {event.datetime_str}")
        print(f"   Account: {event.account_name} ({event.account_type})")
        print(f"   Error: {event.error_type}")
        print(f"   IP: {event.ip_address}")
        print(f"   Requests since success: {event.request_count_since_success}")
        print(f"   Time since success: {event.time_since_last_success:.1f}s")
        print(f"   HTML file: {event.page_html}")
    
    # Show HTML analysis
    print("\n🔍 HTML PATTERN ANALYSIS:")
    print("-" * 50)
    
    html_patterns = {}
    for event in debugger.events:
        html_patterns[event.page_html_hash] = html_patterns.get(event.page_html_hash, 0) + 1
    
    if len(html_patterns) == 1:
        print("✅ All rate limits show identical HTML - consistent rate limiting")
    else:
        print(f"⚠️  Found {len(html_patterns)} different HTML patterns:")
        for hash_val, count in sorted(html_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"   Pattern {hash_val[:8]}: {count} occurrences")
    
    # Show IP analysis
    print("\n🌐 IP ADDRESS ANALYSIS:")
    print("-" * 50)
    
    ip_counts = {}
    for event in debugger.events:
        ip_counts[event.ip_address] = ip_counts.get(event.ip_address, 0) + 1
    
    for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {ip}: {count} rate limit events")
    
    if len(ip_counts) == 1:
        print("🎯 CONCLUSION: All rate limits from same IP - IP-based rate limiting confirmed")
        print("\n💡 RECOMMENDED SOLUTIONS:")
        print("   1. Use residential proxy rotation")
        print("   2. Deploy multiple VPS instances with different IPs")
        print("   3. Use mobile proxy services")
        print("   4. Implement IP rotation with cloud providers")
    else:
        print("🤔 CONCLUSION: Rate limits from multiple IPs - may be account or fingerprint based")
        print("\n💡 RECOMMENDED SOLUTIONS:")
        print("   1. Implement browser fingerprint randomization")
        print("   2. Use different user agents and browser profiles")
        print("   3. Add more account rotation")
        print("   4. Implement timing randomization")
    
    # Show timing analysis
    print("\n⏰ TIMING ANALYSIS:")
    print("-" * 50)
    
    request_counts = [e.request_count_since_success for e in debugger.events]
    if request_counts:
        avg_requests = sum(request_counts) / len(request_counts)
        min_requests = min(request_counts)
        max_requests = max(request_counts)
        
        print(f"   Average requests before rate limit: {avg_requests:.1f}")
        print(f"   Minimum requests before rate limit: {min_requests}")
        print(f"   Maximum requests before rate limit: {max_requests}")
        
        if avg_requests < 5:
            print("🚨 AGGRESSIVE RATE LIMITING: Very few requests allowed")
            print("   → Increase delays between requests")
            print("   → Use more conservative scraping patterns")
        elif avg_requests > 20:
            print("✅ NORMAL RATE LIMITING: Reasonable request allowance")
            print("   → Current approach may be working")
    
    print("\n" + "=" * 50)
    print("📁 Debug files location: debug_logs/")
    print("📄 Full analysis saved to: debug_logs/rate_limit_stats.json")
    print("🌐 HTML captures saved to: debug_logs/html_captures/")

if __name__ == "__main__":
    main()