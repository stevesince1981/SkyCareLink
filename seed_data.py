#!/usr/bin/env python3
"""
Database seeding functionality for MediFly
"""
import os
import sys
from datetime import datetime, timezone, timedelta
import random
from app import create_app, db
from models import (
    User, Niche, Affiliate, Hospital, Booking, Quote, Commission,
    AffiliateNiche, Announcement, SecurityEvent
)

def seed_niches():
    """Seed core medical transport niches (idempotent)"""
    niches_data = [
        {
            'name': 'Neonatal',
            'description': 'Specialized transport for newborns and premature infants',
            'equipment_requirements': ['Isolette', 'Transport Ventilator', 'IV Pumps'],
            'base_upcharge_percent': 0.15
        },
        {
            'name': 'Pediatric Critical Care',
            'description': 'Critical care transport for children under 18',
            'equipment_requirements': ['Pediatric Ventilator', 'ECMO', 'Cardiac Monitor'],
            'base_upcharge_percent': 0.12
        },
        {
            'name': 'Bariatric',
            'description': 'Transport for patients over 350 lbs requiring specialized equipment',
            'equipment_requirements': ['Bariatric Stretcher', 'Heavy Duty Transport'],
            'base_upcharge_percent': 0.20
        },
        {
            'name': 'Organ Transplant',
            'description': 'Time-critical transport for organ transplant patients',
            'equipment_requirements': ['Organ Preservation System', 'Critical Care Monitoring'],
            'base_upcharge_percent': 0.25
        },
        {
            'name': 'High-Risk Obstetric',
            'description': 'Transport for high-risk pregnant patients',
            'equipment_requirements': ['Fetal Monitor', 'High-Risk Obstetric Kit'],
            'base_upcharge_percent': 0.18
        }
    ]
    
    created_count = 0
    for niche_data in niches_data:
        existing = Niche.query.filter_by(name=niche_data['name']).first()
        if not existing:
            niche = Niche(**niche_data)
            db.session.add(niche)
            created_count += 1
    
    db.session.commit()
    print(f"Seeded {created_count} new niches (total: {Niche.query.count()})")
    return created_count

def seed_dummy_data():
    """Seed dummy data for demo purposes"""
    print("Seeding dummy data...")
    
    # Create demo users
    demo_users = [
        {'username': 'demo_affiliate', 'email': 'affiliate@demo.medifly.com', 'role': 'affiliate'},
        {'username': 'demo_hospital', 'email': 'hospital@demo.medifly.com', 'role': 'hospital'},
        {'username': 'demo_provider', 'email': 'provider@demo.medifly.com', 'role': 'provider'}
    ]
    
    created_users = []
    for user_data in demo_users:
        existing = User.query.filter_by(email=user_data['email']).first()
        if not existing:
            user = User(**user_data)
            db.session.add(user)
            db.session.flush()  # Get ID
            created_users.append(user)
    
    db.session.commit()
    
    # Get or create demo affiliate
    affiliate_user = User.query.filter_by(role='affiliate').first()
    demo_affiliate = Affiliate.query.filter_by(user_id=affiliate_user.id).first()
    if not demo_affiliate:
        demo_affiliate = Affiliate(
            user_id=affiliate_user.id,
            company_name="Demo Medical Partners",
            contact_email=affiliate_user.email,
            recouped_amount_usd=1250.00,
            commission_percent_default=0.05,
            total_bookings=15,
            is_demo_data=True
        )
        db.session.add(demo_affiliate)
        db.session.flush()
    
    # Get or create demo hospital
    hospital_user = User.query.filter_by(role='hospital').first()
    demo_hospital = Hospital.query.filter_by(user_id=hospital_user.id).first()
    if not demo_hospital:
        demo_hospital = Hospital(
            user_id=hospital_user.id,
            affiliate_id=demo_affiliate.id,
            name="Orlando Regional Medical Center",
            address="1414 Kuhl Avenue, Orlando, FL 32806",
            contact_email=hospital_user.email,
            phone="(407) 841-5111",
            license_number="FL-HOSP-12345",
            is_demo_data=True
        )
        db.session.add(demo_hospital)
        db.session.flush()
    
    db.session.commit()
    
    # Get niches for booking assignment
    niches = Niche.query.all()
    if not niches:
        print("Warning: No niches found. Run seed_niches first.")
        return 0
    
    # Create 10 demo bookings with quotes
    demo_locations = [
        ("Orlando Regional Medical Center, Orlando, FL", "Tampa General Hospital, Tampa, FL", 85),
        ("Miami Children's Hospital, Miami, FL", "Shands Hospital, Gainesville, FL", 340),
        ("Jacksonville Memorial, Jacksonville, FL", "Orlando Health, Orlando, FL", 140),
        ("Naples Community Hospital, Naples, FL", "Jackson Memorial, Miami, FL", 120),
        ("Sarasota Memorial, Sarasota, FL", "All Children's Hospital, St. Pete, FL", 45)
    ]
    
    transport_types = ['critical', 'non_critical', 'mvp']
    urgency_levels = ['routine', 'urgent', 'critical']
    statuses = ['completed', 'booked', 'pending']
    
    created_bookings = 0
    for i in range(10):
        # Check if demo booking already exists
        existing_count = Booking.query.filter_by(is_demo_data=True).count()
        if existing_count >= 10:
            break
            
        origin, destination, distance = random.choice(demo_locations)
        niche = random.choice(niches)
        
        booking_data = {
            'hospital_id': demo_hospital.id,
            'niche_id': niche.id,
            'patient_age': random.randint(25, 85),
            'transport_type': random.choice(transport_types),
            'urgency_level': random.choice(urgency_levels),
            'origin_address': origin,
            'destination_address': destination,
            'estimated_distance_miles': distance,
            'equipment_needed': random.sample(['Ventilator', 'IV Pump', 'Cardiac Monitor', 'ECMO'], k=2),
            'status': random.choice(statuses),
            'total_amount_usd': round(random.uniform(8500.0, 25000.0), 2),
            'deposit_amount_usd': 250.0,
            'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
            'is_demo_data': True
        }
        
        if booking_data['status'] == 'completed':
            booking_data['completed_at'] = booking_data['created_at'] + timedelta(hours=random.randint(4, 24))
        
        booking = Booking(**booking_data)
        db.session.add(booking)
        db.session.flush()
        
        # Create 2-5 quotes per booking
        providers = [
            "AirMed Florida", "LifeFlight Central", "CriticalCare Air",
            "MedStar Transport", "Guardian Medical", "Rapid Response Air"
        ]
        
        num_quotes = random.randint(2, 5)
        selected_quote = None
        
        for j in range(num_quotes):
            base_price = booking_data['total_amount_usd'] * random.uniform(0.8, 1.2)
            quote = Quote(
                booking_id=booking.id,
                provider_name=random.choice(providers),
                aircraft_type=random.choice(['King Air 350', 'Citation CJ3', 'Bell 407', 'AW139']),
                eta_minutes=random.randint(15, 120),
                base_price_usd=round(base_price * 0.85, 2),
                equipment_upcharge_usd=round(base_price * 0.10, 2),
                urgency_upcharge_usd=round(base_price * 0.05, 2) if booking_data['urgency_level'] == 'critical' else 0,
                total_price_usd=round(base_price, 2),
                certifications=['CAMTS', 'NAAMTA', 'Part 135'],
                capabilities=['24/7 Availability', 'Critical Care', 'Multi-organ Support'],
                valid_until=datetime.now(timezone.utc) + timedelta(hours=48),
                is_demo_data=True
            )
            db.session.add(quote)
            db.session.flush()
            
            if j == 0:  # First quote is selected
                selected_quote = quote
                quote.is_selected = True
                booking.selected_quote_id = quote.id
        
        # Create commission for completed bookings
        if booking_data['status'] == 'completed' and selected_quote:
            commission = Commission(
                booking_id=booking.id,
                affiliate_id=demo_affiliate.id,
                booking_total_usd=selected_quote.total_price_usd,
                commission_percent=demo_affiliate.commission_percent_default,
                commission_amount_usd=round(selected_quote.total_price_usd * demo_affiliate.commission_percent_default, 2),
                invoice_number=f"INV-{2025001 + i}",
                invoice_generated_at=booking_data['completed_at'] + timedelta(days=1),
                is_demo_data=True
            )
            db.session.add(commission)
        
        created_bookings += 1
    
    db.session.commit()
    print(f"Created {created_bookings} demo bookings with quotes and commissions")
    return created_bookings

def remove_dummy_data():
    """Remove all dummy data"""
    print("Removing dummy data...")
    
    # Remove in order to respect foreign key constraints
    Commission.query.filter_by(is_demo_data=True).delete()
    Quote.query.filter_by(is_demo_data=True).delete()
    Booking.query.filter_by(is_demo_data=True).delete()
    Hospital.query.filter_by(is_demo_data=True).delete()
    Affiliate.query.filter_by(is_demo_data=True).delete()
    
    # Remove demo users
    demo_emails = ['affiliate@demo.medifly.com', 'hospital@demo.medifly.com', 'provider@demo.medifly.com']
    User.query.filter(User.email.in_(demo_emails)).delete()
    
    db.session.commit()
    print("Dummy data removed successfully")

def get_dummy_data_status():
    """Get current dummy data counts"""
    counts = {
        'users': User.query.filter(User.email.like('%@demo.medifly.com')).count(),
        'affiliates': Affiliate.query.filter_by(is_demo_data=True).count(),
        'hospitals': Hospital.query.filter_by(is_demo_data=True).count(),
        'bookings': Booking.query.filter_by(is_demo_data=True).count(),
        'quotes': Quote.query.filter_by(is_demo_data=True).count(),
        'commissions': Commission.query.filter_by(is_demo_data=True).count()
    }
    return counts

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == 'seed_niches':
                seed_niches()
            elif command == 'seed_dummy':
                seed_dummy_data()
            elif command == 'remove_dummy':
                remove_dummy_data()
            elif command == 'status':
                counts = get_dummy_data_status()
                print("Dummy data status:", counts)
            else:
                print("Usage: python seed_data.py [seed_niches|seed_dummy|remove_dummy|status]")
        else:
            print("Seeding niches and dummy data...")
            seed_niches()
            seed_dummy_data()
            counts = get_dummy_data_status()
            print(f"Final dummy data counts: {counts}")