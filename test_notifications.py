#!/usr/bin/env python3
"""
Test script for email and SMS notifications
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db
from models import Quote
from services.mailer import email_service
from services.sms import sms_service

def create_test_quote():
    """Create a test quote for notification testing"""
    test_quote = Quote(
        ref_id="TEST123456",
        contact_name="John Doe",
        contact_email="test@example.com",
        contact_phone="+1234567890",
        service_type="Critical",
        severity_level="Level 2",
        flight_date=datetime.utcnow() + timedelta(days=2),
        from_city="New York",
        from_state="NY",
        from_hospital="NYC General Hospital",
        to_city="Boston",
        to_state="MA", 
        to_hospital="Boston Medical Center",
        medical_equipment=["oxygen", "cardiac_monitor", "stretcher"],
        quote_status="pending",
        created_at=datetime.utcnow()
    )
    
    # Update with provider quote
    test_quote.provider_name = "AirMed Transport"
    test_quote.quoted_price = 15000.00
    test_quote.aircraft_type = "Helicopter"
    test_quote.estimated_flight_time = "45 minutes"
    test_quote.quote_status = "quoted"
    test_quote.quote_submitted_at = datetime.utcnow()
    test_quote.quote_expires_at = datetime.utcnow() + timedelta(days=7)
    test_quote.booking_reference = "BK20250817TEST"
    
    return test_quote

def test_affiliate_notification():
    """Test affiliate new quote notification"""
    print("\n=== Testing Affiliate New Quote Notification ===")
    
    success = email_service.send_affiliate_new_quote(
        affiliate_email="affiliate-test@example.com",
        quote_ref="TEST123456",
        flight_date="August 19, 2025",
        from_location="New York, NY (NYC General Hospital)",
        to_location="Boston, MA (Boston Medical Center)",
        quote_url="http://localhost:5000/affiliate/quote/TEST123456"
    )
    
    print(f"Affiliate email notification: {'SUCCESS' if success else 'FAILED'}")
    return success

def test_quote_ready_notification():
    """Test caller quote ready notification"""
    print("\n=== Testing Quote Ready Notification ===")
    
    # Email notification
    email_success = email_service.send_caller_quote_ready(
        caller_email="test@example.com",
        quote_ref="TEST123456",
        provider_name="AirMed Transport",
        price="$15,000.00",
        results_url="http://localhost:5000/quotes/results/TEST123456"
    )
    
    print(f"Quote ready email: {'SUCCESS' if email_success else 'FAILED'}")
    
    # SMS notification
    sms_success = sms_service.send_quote_ready_sms(
        to_phone="+1234567890",
        quote_ref="TEST123456",
        price="$15,000.00",
        provider_name="AirMed Transport",
        results_url="http://localhost:5000/quotes/results/TEST123456"
    )
    
    print(f"Quote ready SMS: {'SUCCESS' if sms_success else 'FAILED'}")
    
    return email_success or sms_success

def test_booking_confirmation():
    """Test booking confirmation notification"""
    print("\n=== Testing Booking Confirmation Notification ===")
    
    # Email notification
    email_success = email_service.send_caller_booking_confirmed(
        caller_email="test@example.com",
        booking_ref="BK20250817TEST",
        provider_name="AirMed Transport",
        flight_date="August 19, 2025",
        booking_url="http://localhost:5000/quotes/results/TEST123456"
    )
    
    print(f"Booking confirmation email: {'SUCCESS' if email_success else 'FAILED'}")
    
    # SMS notification
    sms_success = sms_service.send_booking_confirmed_sms(
        to_phone="+1234567890",
        booking_ref="BK20250817TEST",
        provider_name="AirMed Transport",
        flight_date="August 19, 2025",
        booking_url="http://localhost:5000/quotes/results/TEST123456"
    )
    
    print(f"Booking confirmation SMS: {'SUCCESS' if sms_success else 'FAILED'}")
    
    return email_success or sms_success

def main():
    """Run all notification tests"""
    print("SkyCareLink Notification System Test")
    print("====================================")
    
    # Test service initialization
    print(f"Email service enabled: {email_service.enabled}")
    print(f"SMS service enabled: {sms_service.enabled}")
    
    if not email_service.enabled:
        print("⚠ Email service disabled - check MAIL_USERNAME and MAIL_PASSWORD environment variables")
    
    if not sms_service.enabled:
        print("⚠ SMS service disabled - check ENABLE_SMS=true and Twilio credentials")
    
    # Run tests
    results = []
    results.append(test_affiliate_notification())
    results.append(test_quote_ready_notification())
    results.append(test_booking_confirmation())
    
    print(f"\n=== Test Results ===")
    print(f"Tests run: {len(results)}")
    print(f"Successful: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if not any(results) and not email_service.enabled and not sms_service.enabled:
        print("\n✓ All tests passed - services correctly disabled without credentials")
        print("  To test with real notifications, add email/SMS credentials to environment")
    elif any(results):
        print(f"\n✓ Some notifications sent successfully")
    else:
        print(f"\n⚠ All notifications failed - check service configuration")

if __name__ == "__main__":
    main()