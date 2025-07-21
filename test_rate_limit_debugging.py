#!/usr/bin/env python3
"""
Test script to verify rate limit debugging system is working
"""

import time
from rate_limit_debugger import RateLimitDebugger

def test_rate_limit_debugging():
    print("🧪 TESTING RATE LIMIT DEBUGGING SYSTEM")
    print("=" * 50)
    
    # Initialize debugger
    debugger = RateLimitDebugger()
    
    # Simulate some rate limit events
    print("📝 Creating test rate limit events...")
    
    # Test event 1 - timeout error
    event1 = debugger.capture_rate_limit_event(
        context=None,
        account_name="test_primary@example.com",
        account_type="primary",
        url="https://x.com/i/lists/1919380958723158457",
        error_type="timeout",
        error_message="Timeout loading page content: Page.wait_for_selector: Timeout 15000ms exceeded",
        page_content="<html><body><div>Rate limited page content</div></body></html>"
    )
    
    time.sleep(1)
    
    # Test event 2 - same account, different error
    event2 = debugger.capture_rate_limit_event(
        context=None,
        account_name="test_primary@example.com", 
        account_type="primary",
        url="https://x.com/i/lists/1919380958723158457",
        error_type="page_load_error",
        error_message="Generic error during page operation",
        page_content="<html><body><div>Different error page</div></body></html>"
    )
    
    time.sleep(1)
    
    # Test event 3 - backup account
    event3 = debugger.capture_rate_limit_event(
        context=None,
        account_name="test_backup@example.com",
        account_type="backup", 
        url="https://x.com/i/lists/1919380958723158457",
        error_type="timeout",
        error_message="Backup account timeout error",
        page_content="<html><body><div>Rate limited page content</div></body></html>"
    )
    
    print(f"✅ Created {len(debugger.events)} test events")
    
    # Test success tracking
    print("\n📈 Testing success tracking...")
    debugger.mark_success("test_primary@example.com")
    print("✅ Marked success for primary account")
    
    # Test analysis
    print("\n🔍 Testing analysis...")
    analysis = debugger.analyze_patterns()
    
    print(f"📊 Analysis results:")
    print(f"   Total events: {analysis['total_events']}")
    print(f"   Accounts affected: {analysis['accounts_affected']}")
    print(f"   Error types: {list(analysis['error_types'].keys())}")
    print(f"   IP addresses: {list(analysis['ip_addresses'].keys())}")
    
    # Test recommendations
    if analysis.get("recommendations"):
        print(f"\n💡 Recommendations generated:")
        for rec in analysis["recommendations"]:
            print(f"   {rec}")
    
    # Print full analysis
    print("\n📋 FULL ANALYSIS:")
    debugger.print_analysis()
    
    print("\n✅ RATE LIMIT DEBUGGING SYSTEM TEST COMPLETED")
    print("🔍 Check debug_logs/ directory for captured files")
    
    return True

if __name__ == "__main__":
    test_rate_limit_debugging()