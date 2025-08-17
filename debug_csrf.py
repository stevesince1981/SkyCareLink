#!/usr/bin/env python3
"""Debug script to test CSRF token generation directly"""

import sys
import os
sys.path.append('.')

try:
    from consumer_main_final import consumer_app
    
    with consumer_app.app_context():
        with consumer_app.test_request_context():
            from flask_wtf.csrf import generate_csrf
            
            print("Testing CSRF token generation:")
            token = generate_csrf()
            print(f"Generated token: {token}")
            print(f"Token length: {len(token)}")
            
            # Test the context processor
            from consumer_main_final import security_context_processor
            context = security_context_processor()
            print(f"Context processor returns: {context}")
            
            if 'get_csrf_token' in context:
                token2 = context['get_csrf_token']()
                print(f"Context processor token: {token2}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()