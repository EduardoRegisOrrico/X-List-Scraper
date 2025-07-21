import json
import time
import os
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib
import requests

@dataclass
class RateLimitEvent:
    timestamp: float
    datetime_str: str
    account_name: str
    account_type: str  # primary, backup
    url: str
    error_type: str  # timeout, rate_limit, blocked, etc.
    error_message: str
    page_html: str
    page_html_hash: str
    response_headers: Dict[str, str]
    network_info: Dict[str, Any]
    browser_fingerprint: Dict[str, str]
    session_cookies: List[Dict]
    request_count_since_success: int
    time_since_last_success: float
    ip_address: str
    user_agent: str

class RateLimitDebugger:
    def __init__(self, debug_dir: str = "debug_logs"):
        self.debug_dir = debug_dir
        self.events_file = os.path.join(debug_dir, "rate_limit_events.json")
        self.html_dir = os.path.join(debug_dir, "html_captures")
        self.stats_file = os.path.join(debug_dir, "rate_limit_stats.json")
        
        # Create directories
        os.makedirs(debug_dir, exist_ok=True)
        os.makedirs(self.html_dir, exist_ok=True)
        
        # Load existing events
        self.events: List[RateLimitEvent] = []
        self.load_events()
        
        # Tracking state
        self.request_counts = {}  # account_name -> count
        self.last_success_times = {}  # account_name -> timestamp
        
    def load_events(self):
        """Load existing rate limit events"""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r') as f:
                    events_data = json.load(f)
                    self.events = [RateLimitEvent(**event) for event in events_data]
        except Exception as e:
            print(f"Warning: Could not load existing events: {e}")
            self.events = []
    
    def save_events(self):
        """Save events to file"""
        try:
            events_data = [asdict(event) for event in self.events]
            with open(self.events_file, 'w') as f:
                json.dump(events_data, f, indent=2)
        except Exception as e:
            print(f"Error saving events: {e}")
    
    def get_current_ip(self) -> str:
        """Get current external IP address"""
        try:
            response = requests.get('https://httpbin.org/ip', timeout=5)
            return response.json().get('origin', 'unknown')
        except:
            return 'unknown'
    
    def capture_rate_limit_event(self, 
                                context,
                                account_name: str,
                                account_type: str,
                                url: str,
                                error_type: str,
                                error_message: str,
                                page_content: str = None) -> RateLimitEvent:
        """Capture a comprehensive rate limit event"""
        
        current_time = time.time()
        
        # Get page HTML if not provided
        if page_content is None:
            try:
                page_content = context.page.content() if context and hasattr(context, 'page') else ""
            except:
                page_content = ""
        
        # Create HTML hash for deduplication
        html_hash = hashlib.md5(page_content.encode()).hexdigest()
        
        # Save HTML to file
        html_filename = f"{account_name}_{int(current_time)}_{html_hash[:8]}.html"
        html_path = os.path.join(self.html_dir, html_filename)
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page_content)
        except Exception as e:
            print(f"Warning: Could not save HTML: {e}")
        
        # Get response headers if available
        response_headers = {}
        try:
            if context and hasattr(context, 'page'):
                # Try to get last response headers
                response = context.page.evaluate("""
                    () => {
                        const headers = {};
                        if (window.lastResponse) {
                            for (const [key, value] of window.lastResponse.headers.entries()) {
                                headers[key] = value;
                            }
                        }
                        return headers;
                    }
                """)
                response_headers = response or {}
        except:
            pass
        
        # Get network info
        network_info = {
            "ip_address": self.get_current_ip(),
            "timestamp": current_time,
            "url_accessed": url
        }
        
        # Get browser fingerprint
        browser_fingerprint = {}
        try:
            if context and hasattr(context, 'page'):
                fingerprint = context.page.evaluate("""
                    () => ({
                        userAgent: navigator.userAgent,
                        language: navigator.language,
                        platform: navigator.platform,
                        cookieEnabled: navigator.cookieEnabled,
                        screenWidth: screen.width,
                        screenHeight: screen.height,
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                        webdriver: navigator.webdriver
                    })
                """)
                browser_fingerprint = fingerprint or {}
        except:
            pass
        
        # Get session cookies
        session_cookies = []
        try:
            if context:
                cookies = context.cookies()
                session_cookies = [{"name": c["name"], "domain": c["domain"], "path": c["path"]} for c in cookies]
        except:
            pass
        
        # Calculate request metrics
        self.request_counts[account_name] = self.request_counts.get(account_name, 0) + 1
        last_success = self.last_success_times.get(account_name, current_time)
        time_since_success = current_time - last_success
        
        # Create event
        event = RateLimitEvent(
            timestamp=current_time,
            datetime_str=datetime.datetime.fromtimestamp(current_time).isoformat(),
            account_name=account_name,
            account_type=account_type,
            url=url,
            error_type=error_type,
            error_message=error_message,
            page_html=html_filename,  # Store filename, not content
            page_html_hash=html_hash,
            response_headers=response_headers,
            network_info=network_info,
            browser_fingerprint=browser_fingerprint,
            session_cookies=session_cookies,
            request_count_since_success=self.request_counts[account_name],
            time_since_last_success=time_since_success,
            ip_address=network_info["ip_address"],
            user_agent=browser_fingerprint.get("userAgent", "unknown")
        )
        
        # Add to events list
        self.events.append(event)
        
        # Save immediately
        self.save_events()
        
        # Print summary
        print(f"🔍 RATE LIMIT DEBUG: Captured event for {account_name}")
        print(f"   Error: {error_type} - {error_message}")
        print(f"   IP: {network_info['ip_address']}")
        print(f"   Requests since success: {self.request_counts[account_name]}")
        print(f"   Time since success: {time_since_success:.1f}s")
        print(f"   HTML saved: {html_filename}")
        
        return event
    
    def mark_success(self, account_name: str):
        """Mark successful request for an account"""
        self.last_success_times[account_name] = time.time()
        self.request_counts[account_name] = 0
        print(f"✅ SUCCESS: Reset counters for {account_name}")
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze rate limit patterns from captured events"""
        if not self.events:
            return {"error": "No events to analyze"}
        
        analysis = {
            "total_events": len(self.events),
            "accounts_affected": len(set(e.account_name for e in self.events)),
            "error_types": {},
            "ip_addresses": {},
            "time_patterns": {},
            "request_count_patterns": {},
            "common_html_patterns": {},
            "recommendations": []
        }
        
        # Analyze error types
        for event in self.events:
            analysis["error_types"][event.error_type] = analysis["error_types"].get(event.error_type, 0) + 1
            analysis["ip_addresses"][event.ip_address] = analysis["ip_addresses"].get(event.ip_address, 0) + 1
        
        # Analyze request count patterns
        request_counts = [e.request_count_since_success for e in self.events]
        if request_counts:
            analysis["request_count_patterns"] = {
                "min": min(request_counts),
                "max": max(request_counts),
                "avg": sum(request_counts) / len(request_counts),
                "common_counts": {}
            }
            
            for count in request_counts:
                analysis["request_count_patterns"]["common_counts"][count] = \
                    analysis["request_count_patterns"]["common_counts"].get(count, 0) + 1
        
        # Analyze HTML patterns
        html_hashes = [e.page_html_hash for e in self.events]
        for hash_val in html_hashes:
            analysis["common_html_patterns"][hash_val] = analysis["common_html_patterns"].get(hash_val, 0) + 1
        
        # Generate recommendations
        if len(analysis["ip_addresses"]) == 1:
            analysis["recommendations"].append("🎯 All rate limits from same IP - IP-based limiting detected")
        
        if analysis["error_types"].get("timeout", 0) > analysis["error_types"].get("rate_limit", 0):
            analysis["recommendations"].append("⏰ More timeouts than explicit rate limits - may be soft limiting")
        
        avg_requests = analysis.get("request_count_patterns", {}).get("avg", 0)
        if avg_requests < 10:
            analysis["recommendations"].append("🚨 Rate limits hit very quickly - aggressive limiting")
        elif avg_requests > 50:
            analysis["recommendations"].append("✅ Rate limits hit after many requests - normal behavior")
        
        # Save analysis
        with open(self.stats_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        return analysis
    
    def print_analysis(self):
        """Print human-readable analysis"""
        analysis = self.analyze_patterns()
        
        print("\n" + "="*60)
        print("🔍 RATE LIMIT ANALYSIS")
        print("="*60)
        
        print(f"📊 Total Events: {analysis['total_events']}")
        print(f"👥 Accounts Affected: {analysis['accounts_affected']}")
        
        print(f"\n🚫 Error Types:")
        for error_type, count in analysis["error_types"].items():
            print(f"   {error_type}: {count}")
        
        print(f"\n🌐 IP Addresses:")
        for ip, count in analysis["ip_addresses"].items():
            print(f"   {ip}: {count} events")
        
        if "request_count_patterns" in analysis:
            patterns = analysis["request_count_patterns"]
            print(f"\n📈 Request Patterns:")
            print(f"   Average requests before limit: {patterns['avg']:.1f}")
            print(f"   Min: {patterns['min']}, Max: {patterns['max']}")
        
        print(f"\n💡 Recommendations:")
        for rec in analysis["recommendations"]:
            print(f"   {rec}")
        
        print("="*60)

# Integration helper functions
def setup_rate_limit_debugging(context, debugger: RateLimitDebugger):
    """Setup debugging hooks in browser context"""
    try:
        # Inject response tracking
        context.page.add_init_script("""
            window.lastResponse = null;
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                return originalFetch.apply(this, args).then(response => {
                    window.lastResponse = response.clone();
                    return response;
                });
            };
        """)
    except Exception as e:
        print(f"Warning: Could not setup response tracking: {e}")