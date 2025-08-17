#!/usr/bin/env python3
"""Quick script to test login with proper CSRF token handling"""

import requests
import re

BASE_URL = "http://localhost:5000"

def test_login():
    """Test the login flow with proper CSRF token"""
    session = requests.Session()
    
    # Get the login page and extract CSRF token
    login_page = session.get(f"{BASE_URL}/login")
    print(f"Login page status: {login_page.status_code}")
    
    # Try multiple patterns to find CSRF token
    csrf_patterns = [
        r'name="csrf_token"[^>]*value="([^"]+)"',
        r'csrf_token"[^>]*value="([^"]+)"', 
        r'value="([^"]+)"[^>]*name="csrf_token"'
    ]
    
    csrf_token = None
    for pattern in csrf_patterns:
        match = re.search(pattern, login_page.text)
        if match:
            csrf_token = match.group(1)
            print(f"Found CSRF token: {csrf_token[:20]}...")
            break
    
    if not csrf_token:
        print("No CSRF token found in page")
        print("Page content sample:")
        # Show form section
        form_section = re.search(r'<form.*?</form>', login_page.text, re.DOTALL)
        if form_section:
            print(form_section.group(0)[:500])
        else:
            print(login_page.text[:1000])
        return
    
    # Attempt login with CSRF token
    login_data = {
        'username': 'admin',
        'password': 'demo123',
        'csrf_token': csrf_token
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login response status: {response.status_code}")
    
    if response.status_code in [302, 301]:
        print(f"Redirected to: {response.headers.get('Location', 'Unknown')}")
        print("Login likely successful!")
    else:
        print("Login response content:")
        print(response.text[:500])

if __name__ == "__main__":
    test_login()