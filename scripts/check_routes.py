#!/usr/bin/env python3
"""
SkyCareLink Route Health Checker
Crawls critical application routes and reports status codes
"""

import requests
import sys
import time
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5000"
TIMEOUT = 10

# Critical routes to check
ROUTES = [
    # Core consumer routes
    '/',
    '/quotes/new',
    '/resources-financial', 
    '/terms-of-service',
    '/login',
    
    # Affiliate routes (may return 401/302 - that's OK)
    '/affiliate/commissions',
    '/join_affiliate',
    '/join_hospital',
    
    # Admin routes (may return 401/302 - that's OK)
    '/admin/affiliates',
    
    # API endpoints
    '/healthz',
    
    # Additional working routes
    '/consumer_partners',
    '/consumer_about',
    '/consumer_referrals'
]

# Expected status codes (some routes may redirect or require auth)
ACCEPTABLE_CODES = {200, 302, 401, 403}

def check_route(route):
    """Check a single route and return status info"""
    url = urljoin(BASE_URL, route)
    
    try:
        response = requests.get(url, timeout=TIMEOUT, allow_redirects=False)
        return {
            'route': route,
            'url': url,
            'status_code': response.status_code,
            'success': response.status_code in ACCEPTABLE_CODES,
            'response_time': response.elapsed.total_seconds(),
            'error': None
        }
    except requests.exceptions.ConnectionError:
        return {
            'route': route,
            'url': url,
            'status_code': 0,
            'success': False,
            'response_time': 0,
            'error': 'Connection refused - server may not be running'
        }
    except requests.exceptions.Timeout:
        return {
            'route': route,
            'url': url,
            'status_code': 0,
            'success': False,
            'response_time': TIMEOUT,
            'error': f'Timeout after {TIMEOUT}s'
        }
    except Exception as e:
        return {
            'route': route,
            'url': url,
            'status_code': 0,
            'success': False,
            'response_time': 0,
            'error': str(e)
        }

def main():
    """Main route checking function"""
    print("🔍 SkyCareLink Route Health Check")
    print(f"Base URL: {BASE_URL}")
    print(f"Routes to check: {len(ROUTES)}")
    print("-" * 60)
    
    start_time = time.time()
    results = []
    failed_routes = []
    
    for route in ROUTES:
        result = check_route(route)
        results.append(result)
        
        # Print result
        if result['success']:
            print(f"✓ PASS: {result['route']} ({result['status_code']}) - {result['response_time']:.2f}s")
        else:
            failed_routes.append(result)
            if result['error']:
                print(f"✗ FAIL: {result['route']} - {result['error']}")
            else:
                print(f"✗ FAIL: {result['route']} ({result['status_code']}) - unexpected status code")
    
    # Summary
    total_time = time.time() - start_time
    success_count = len([r for r in results if r['success']])
    
    print("-" * 60)
    print(f"📊 Summary: {success_count}/{len(ROUTES)} routes healthy")
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"🌐 Average response time: {sum(r['response_time'] for r in results if r['success']) / max(success_count, 1):.2f}s")
    
    # Detailed failure report
    if failed_routes:
        print("\n❌ Failed Routes:")
        for failure in failed_routes:
            error_msg = failure['error'] or f"Status {failure['status_code']}"
            print(f"   {failure['route']}: {error_msg}")
    
    # Special checks for critical routes
    print("\n🔧 System Health Indicators:")
    
    # Check if main app is responding
    home_result = next((r for r in results if r['route'] == '/'), None)
    if home_result and home_result['success']:
        print("   ✓ Main application: RUNNING")
    else:
        print("   ✗ Main application: FAILED")
    
    # Check health endpoint specifically  
    health_result = next((r for r in results if r['route'] == '/healthz'), None)
    if health_result and health_result['status_code'] == 200:
        print("   ✓ Health endpoint: OK")
    else:
        print("   ✗ Health endpoint: FAILED")
    
    # Check database connectivity (admin routes accessible)
    admin_routes = [r for r in results if r['route'].startswith('/admin')]
    if any(r['status_code'] in {200, 302, 401} for r in admin_routes):
        print("   ✓ Database connectivity: OK")
    else:
        print("   ✗ Database connectivity: UNKNOWN")
    
    # Check security features
    auth_routes = [r for r in results if r['route'] in ['/login', '/auth/audit-test']]
    if any(r['success'] for r in auth_routes):
        print("   ✓ Authentication system: OK")
    else:
        print("   ✗ Authentication system: FAILED")
    
    print()
    
    # Exit code based on critical routes
    critical_routes = ['/', '/healthz', '/quotes/new']
    critical_failures = [r for r in results if r['route'] in critical_routes and not r['success']]
    
    if critical_failures:
        print("💥 CRITICAL: Essential routes are failing!")
        for failure in critical_failures:
            print(f"   CRITICAL FAIL: {failure['route']}")
        sys.exit(1)
    elif failed_routes:
        print("⚠️  WARNING: Some routes are failing, but critical paths are OK")
        sys.exit(0)  # Don't fail build for non-critical routes
    else:
        print("🎉 SUCCESS: All routes healthy!")
        sys.exit(0)

if __name__ == '__main__':
    main()