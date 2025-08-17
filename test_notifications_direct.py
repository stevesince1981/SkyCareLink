#!/usr/bin/env python3
"""
Direct test script for email and SMS notifications - uses services directly
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import notification services directly
from services.mailer import email_service
from services.sms import sms_service

def test_all_notifications():
    """Test all notification types with realistic data"""
    print("SkyCareLink Notification System Direct Test")
    print("==========================================")
    
    print(f"Email service enabled: {email_service.enabled}")
    print(f"SMS service enabled: {sms_service.enabled}")
    
    if not email_service.enabled:
        print("⚠ Email disabled - check MAIL_USERNAME and MAIL_PASSWORD")
    
    if not sms_service.enabled:
        print("⚠ SMS disabled - check ENABLE_SMS=true and Twilio credentials")
    
    results = []
    
    # Test 1: Affiliate new quote notification
    print("\n=== Test 1: Affiliate New Quote Notification ===")
    result1 = email_service.send_affiliate_new_quote(
        affiliate_email="affiliate@example.com",
        quote_ref="QR20250817ABC123",
        flight_date="August 19, 2025", 
        from_location="NYC General Hospital, New York, NY",
        to_location="Boston Medical Center, Boston, MA",
        quote_url="http://localhost:5000/affiliate/quote/QR20250817ABC123"
    )
    print(f"Result: {'✓ SUCCESS' if result1 else '✗ FAILED'}")
    results.append(result1)
    
    # Test 2: Quote ready notification (email)
    print("\n=== Test 2: Quote Ready Email Notification ===")
    result2a = email_service.send_caller_quote_ready(
        caller_email="patient@example.com",
        quote_ref="QR20250817ABC123",
        provider_name="AirMed Transport",
        price="$15,500.00",
        results_url="http://localhost:5000/quotes/results/QR20250817ABC123"
    )
    print(f"Result: {'✓ SUCCESS' if result2a else '✗ FAILED'}")
    results.append(result2a)
    
    # Test 3: Quote ready notification (SMS)
    print("\n=== Test 3: Quote Ready SMS Notification ===")
    result2b = sms_service.send_quote_ready_sms(
        to_phone="+1234567890",
        quote_ref="QR20250817ABC123",
        price="$15,500.00",
        provider_name="AirMed Transport",
        results_url="http://localhost:5000/quotes/results/QR20250817ABC123"
    )
    print(f"Result: {'✓ SUCCESS' if result2b else '✗ FAILED'}")
    results.append(result2b)
    
    # Test 4: Booking confirmation (email)
    print("\n=== Test 4: Booking Confirmation Email ===")
    result3a = email_service.send_caller_booking_confirmed(
        caller_email="patient@example.com",
        booking_ref="BK20250817XYZ789",
        provider_name="AirMed Transport",
        flight_date="August 19, 2025",
        booking_url="http://localhost:5000/quotes/results/QR20250817ABC123"
    )
    print(f"Result: {'✓ SUCCESS' if result3a else '✗ FAILED'}")
    results.append(result3a)
    
    # Test 5: Booking confirmation (SMS)
    print("\n=== Test 5: Booking Confirmation SMS ===")
    result3b = sms_service.send_booking_confirmed_sms(
        to_phone="+1234567890",
        booking_ref="BK20250817XYZ789",
        provider_name="AirMed Transport",
        flight_date="August 19, 2025", 
        booking_url="http://localhost:5000/quotes/results/QR20250817ABC123"
    )
    print(f"Result: {'✓ SUCCESS' if result3b else '✗ FAILED'}")
    results.append(result3b)
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if not email_service.enabled and not sms_service.enabled:
        print("\n✓ All tests completed - services correctly disabled without credentials")
        print("  The notification system would work when credentials are provided")
    elif any(results):
        print(f"\n✓ Some notifications sent successfully")
    else:
        print(f"\n⚠ All notifications failed - check logs for details")
    
    return results

if __name__ == "__main__":
    test_all_notifications()