#!/usr/bin/env python
"""
Simple test script to verify NDtechTrack error tracking system is working.
This script will try to access the error tracking pages and verify functionality.
"""

import os
import django
import requests
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

def test_error_tracking_system():
    """Test the NDtechTrack error tracking system"""
    
    print("🧪 Testing NDtechTrack Error Tracking System")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test URLs to verify they're accessible
    test_urls = [
        "/error-tracking/",
        "/device-tracking/", 
        "/user-activity-tracking/",
        "/automated-issues/",
        "/error-patterns/",
        "/system-performance/"
    ]
    
    print(f"\n🌐 Testing URL Accessibility at {base_url}")
    
    for url_path in test_urls:
        full_url = f"{base_url}{url_path}"
        try:
            print(f"   Testing: {full_url}")
            response = requests.get(full_url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - Status: {response.status_code}")
                if "Error" in response.text:
                    print(f"   ⚠️  Expected error page found")
                else:
                    print(f"   ✅ Page accessible")
            else:
                print(f"   ❌ FAILED - Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ ERROR - Request failed: {str(e)}")
        except Exception as e:
            print(f"   ❌ ERROR - Unexpected error: {str(e)}")
    
    print(f"\n📊 Test Summary:")
    print(f"   Base URL: {base_url}")
    print(f"   Tested URLs: {len(test_urls)}")
    print(f"   Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Open {base_url} in your browser")
    print(f"   2. Login with test credentials:")
    print(f"      Username: test_admin")
    print(f"      Password: test123")
    print(f"   3. Navigate to each tracking page to test functionality")
    print(f"   4. Verify error data is displayed correctly")
    print(f"   5. Test error resolution workflow")
    print(f"   6. Test device and user activity tracking")
    print(f"   7. Test automated issues and alerts")
    print(f"   8. Test system performance monitoring")

if __name__ == '__main__':
    test_error_tracking_system()
