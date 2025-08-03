import os
import logging
import json
import math
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
# import sympy as sp  # Will be enabled after package installation
# import stripe  # Will be enabled after package installation
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
consumer_app = Flask(__name__, template_folder='consumer_templates', static_folder='consumer_static')
consumer_app.secret_key = os.environ.get("SESSION_SECRET", "consumer-demo-key-change-in-production")

# Add Jinja2 filters
@consumer_app.template_filter('number_format')
def number_format(value):
    """Format numbers with commas"""
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value

# Configure Stripe (demo mode) - will be enabled after package installation
# stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_demo_key")

# Global tracking variables for dashboard
BOOKING_STATS = {
    'total_bookings': 0,
    'total_revenue': 0,
    'total_expenses': 12000,  # Fixed operational costs
    'goal_revenue': 375000,
    'unique_visits': 0,
    'conversion_rate': 0.15,
    'provider_diversity': {
        'rural': 2,
        'traditional': 3,
        'drone': 1,
        'hybrid': 1
    }
}

# Profit sharing tiers
PROFIT_TIERS = {
    '1-10': {'mike': 30, 'steve': 30, 'business': 40},
    '11-30': {'mike': 25, 'steve': 25, 'business': 50}, 
    '31+': {'mike': 20, 'steve': 20, 'business': 60}
}

# Enhanced provider data with diversity focus (50% rural/drone/hybrid)
PROVIDERS = {
    'airmed': {
        'name': 'AirMed Response',
        'type': 'traditional',
        'price': 128500,
        'eta': '3 hours',
        'description': 'ICU Certified Team',
        'details': 'Full ICU capabilities with certified critical care team. Advanced life support equipment onboard.',
        'capabilities': ['ICU Certified', 'Advanced Life Support', '24/7 Available'],
        'green_score': 7.2,
        'emission_offset': True,
        'location_coverage': ['Urban', 'Suburban']
    },
    'reva': {
        'name': 'REVA CriticalCare', 
        'type': 'traditional',
        'price': 112000,
        'eta': '5 hours',
        'description': 'Doctor On Board',
        'details': 'Licensed physician accompanies all flights. Specialized in critical care transport.',
        'capabilities': ['Doctor Onboard', 'Critical Care', 'Rapid Response'],
        'green_score': 6.8,
        'emission_offset': False,
        'location_coverage': ['Urban', 'International']
    },
    'mercywings': {
        'name': 'MercyWings Global',
        'type': 'traditional',
        'price': 102000,
        'eta': '6 hours', 
        'description': 'Compassionate Care',
        'details': 'Experienced medical team focused on patient comfort and family support.',
        'capabilities': ['Family Friendly', 'Basic Life Support', 'Cost Effective'],
        'green_score': 8.1,
        'emission_offset': True,
        'location_coverage': ['Global', 'Family Focus']
    },
    'ruralreach': {
        'name': 'Rural Reach Airways',
        'type': 'rural',
        'price': 89000,
        'eta': '4 hours',
        'description': 'Rural Specialist',
        'details': 'Specialized in serving remote and rural areas with smaller aircraft for accessibility.',
        'capabilities': ['Rural Access', 'Remote Locations', 'Quick Deploy'],
        'green_score': 9.1,
        'emission_offset': True,
        'location_coverage': ['Rural', 'Remote', 'Small Airports']
    },
    'skycare_drone': {
        'name': 'SkyCare Drone Medical',
        'type': 'drone',
        'price': 67000,
        'eta': '2.5 hours',
        'description': 'Ultra Low Emission',
        'details': 'Next-generation electric VTOL aircraft with zero direct emissions for short-range critical transport.',
        'capabilities': ['Zero Emission', 'Rapid Response', 'Urban Access'],
        'green_score': 10.0,
        'emission_offset': True,
        'location_coverage': ['Urban', 'Short Range', 'Emergency']
    },
    'hybrid_med': {
        'name': 'HybridMed Solutions',
        'type': 'hybrid',
        'price': 95000,
        'eta': '4.5 hours',
        'description': 'Hybrid Technology',
        'details': 'Hybrid electric-fuel aircraft combining efficiency with long-range capability.',
        'capabilities': ['Hybrid Power', 'Extended Range', 'Eco Efficient'],
        'green_score': 8.7,
        'emission_offset': True,
        'location_coverage': ['Medium Range', 'Efficient', 'Flexible']
    }
}

# Tracking stages with emergency handoff capabilities
TRACKING_STAGES = [
    "Flight team dispatched",
    "En route to pickup location", 
    "Arrived and preparing patient",
    "Patient loaded - transport in progress",
    "Ground ambulance notified for destination",
    "Transport complete - patient transferred"
]

# AI Estimation Functions
def calculate_distance_estimate(pickup, destination):
    """Simulate distance calculation for AI pricing (basic estimation)"""
    # Mock geo-distance calculation (would use Google Maps API in production)
    location_coords = {
        'orlando': (28.5383, -81.3792),
        'los angeles': (34.0522, -118.2437),
        'new york': (40.7128, -74.0060),
        'turkey': (39.9334, 32.8597),
        'miami': (25.7617, -80.1918),
        'chicago': (41.8781, -87.6298)
    }
    
    pickup_lower = pickup.lower()
    dest_lower = destination.lower()
    
    # Find closest matches
    pickup_coord = None
    dest_coord = None
    
    for city, coord in location_coords.items():
        if city in pickup_lower:
            pickup_coord = coord
        if city in dest_lower:
            dest_coord = coord
    
    if pickup_coord and dest_coord:
        # Calculate rough distance using Haversine formula
        lat1, lon1 = pickup_coord
        lat2, lon2 = dest_coord
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_miles = 3956 * c  # Earth radius in miles
        return distance_miles
    
    # Default estimate for unknown locations
    return 1500

def calculate_ai_estimate(pickup, destination, severity, equipment_list):
    """AI-powered pricing estimate using basic regression model"""
    base_cost = 50000  # Base transportation cost
    
    # Distance factor
    distance = calculate_distance_estimate(pickup, destination)
    distance_cost = distance * 100  # $100 per mile
    
    # Severity multiplier
    severity_cost = severity * 10000  # $10k per severity level
    
    # Equipment costs
    equipment_costs = {
        'ventilator': 15000,
        'ecmo': 25000,
        'incubator': 18000,
        'oxygen': 5000,
        'escort': 8000,
        'other': 10000
    }
    
    equipment_total = 0
    for equipment in equipment_list:
        equipment_total += equipment_costs.get(equipment.lower(), 5000)
    
    # Repositioning cost (10% of base for aircraft positioning)
    repositioning_cost = base_cost * 0.1
    
    # Green optimization discount (5% for eco-friendly routing)
    green_discount = (base_cost + distance_cost) * 0.05
    
    total_estimate = base_cost + distance_cost + severity_cost + equipment_total + repositioning_cost - green_discount
    
    return {
        'total': int(total_estimate),
        'breakdown': {
            'base': base_cost,
            'distance': int(distance_cost),
            'severity': severity_cost,
            'equipment': equipment_total,
            'repositioning': int(repositioning_cost),
            'green_discount': int(green_discount)
        },
        'distance_miles': int(distance)
    }

def calculate_profit_sharing(total_bookings):
    """Calculate profit sharing based on booking tiers"""
    if total_bookings <= 10:
        return PROFIT_TIERS['1-10']
    elif total_bookings <= 30:
        return PROFIT_TIERS['11-30']
    else:
        return PROFIT_TIERS['31+']

def send_notification(message, notification_type='email'):
    """Simulate notification sending (Twilio/Zapier integration stubs)"""
    logging.info(f"NOTIFICATION ({notification_type}): {message}")
    print(f"📧 {notification_type.upper()}: {message}")
    
    # In production, would integrate with:
    # - Twilio for SMS
    # - Zapier for email automation
    # - Slack webhooks for admin alerts
    return True

@consumer_app.route('/')
def landing():
    """Landing page with family/hospital toggle"""
    # Track unique visits
    BOOKING_STATS['unique_visits'] += 1
    
    # Send notification for milestone visits
    if BOOKING_STATS['unique_visits'] % 100 == 0:
        send_notification(f"Milestone: {BOOKING_STATS['unique_visits']} unique visits today!", 'email')
    
    return render_template('consumer_index.html')

@consumer_app.route('/hospital')
def hospital_redirect():
    """Redirect to hospital version"""
    # In production, this would redirect to the hospital app URL
    return redirect('http://medtransportlink-prototype.replit.app')

@consumer_app.route('/intake')
def intake():
    """Family-friendly intake form"""
    session.clear()  # Start fresh
    return render_template('consumer_intake.html')

@consumer_app.route('/results', methods=['POST'])
def results():
    """Show provider options with AI estimates and green routing"""
    # Store form data in session
    session['pickup_location'] = request.form.get('pickup_location', '')
    session['destination'] = request.form.get('destination', '')
    session['severity'] = int(request.form.get('severity', 1))
    session['equipment'] = request.form.getlist('equipment')
    session['travel_date'] = request.form.get('travel_date', '')
    
    # Generate AI estimate
    ai_estimate = calculate_ai_estimate(
        session['pickup_location'],
        session['destination'], 
        session['severity'],
        session['equipment']
    )
    session['ai_estimate'] = ai_estimate
    
    # Filter providers based on route optimization and green scoring
    optimized_providers = {}
    for provider_id, provider_data in PROVIDERS.items():
        provider_copy = provider_data.copy()
        
        # Apply green route optimization (prioritize high green scores)
        if provider_data['green_score'] >= 8.0:
            provider_copy['green_optimized'] = True
            provider_copy['price'] = int(provider_data['price'] * 0.95)  # 5% green discount
        else:
            provider_copy['green_optimized'] = False
            
        optimized_providers[provider_id] = provider_copy
    
    # Sort by green score and price
    sorted_providers = dict(sorted(optimized_providers.items(), 
                                 key=lambda x: (-x[1]['green_score'], x[1]['price'])))
    
    # Log for admin notification with enhanced details
    send_notification(
        f"New quote request: {session['pickup_location']} → {session['destination']}, "
        f"Severity {session['severity']}, Equipment: {', '.join(session['equipment'])}, "
        f"AI Estimate: ${ai_estimate['total']:,}", 'email'
    )
    
    return render_template('consumer_results.html', 
                         providers=sorted_providers,
                         ai_estimate=ai_estimate,
                         green_routing=True)

@consumer_app.route('/confirm')
def confirm():
    """Booking confirmation"""
    provider_id = request.args.get('provider_id')
    if not provider_id or provider_id not in PROVIDERS:
        flash('Please select a valid provider.', 'error')
        return redirect(url_for('results'))
    
    session['selected_provider'] = provider_id
    provider = PROVIDERS[provider_id]
    
    return render_template('consumer_confirm.html', 
                         provider=provider, 
                         provider_id=provider_id)

@consumer_app.route('/tracking', methods=['POST'])
def tracking():
    """Flight tracking simulation with enhanced features"""
    # Store add-ons and deposit information
    session['family_seat'] = 'family_seat' in request.form
    session['vip_cabin'] = 'vip_cabin' in request.form
    session['green_offset'] = 'green_offset' in request.form
    session['consent'] = 'consent' in request.form
    session['financial_aid_requested'] = 'financial_aid' in request.form
    
    if not session.get('consent'):
        flash('Please agree to the consent terms to proceed.', 'error')
        return redirect(url_for('confirm'))
    
    # Calculate total cost with add-ons
    provider = PROVIDERS[session['selected_provider']]
    total_cost = provider['price']
    
    add_on_costs = {}
    if session.get('family_seat'):
        add_on_costs['Family Seat'] = 5000
        total_cost += 5000
    if session.get('vip_cabin'):
        add_on_costs['VIP Cabin'] = 10000
        total_cost += 10000
    if session.get('green_offset'):
        add_on_costs['Carbon Offset'] = 500
        total_cost += 500
    
    # Process deposit ($7,500 total: $1,000 non-refundable + $6,500 refundable)
    deposit_total = 7500
    nonrefundable_fee = 1000
    refundable_prepayment = 6500
    
    session['total_cost'] = total_cost
    session['add_on_costs'] = add_on_costs
    session['deposit_total'] = deposit_total
    session['nonrefundable_fee'] = nonrefundable_fee
    session['refundable_prepayment'] = refundable_prepayment
    session['booking_time'] = datetime.now().isoformat()
    
    # Update booking statistics
    BOOKING_STATS['total_bookings'] += 1
    BOOKING_STATS['total_revenue'] += deposit_total
    
    # Calculate profit sharing
    profit_split = calculate_profit_sharing(BOOKING_STATS['total_bookings'])
    session['profit_split'] = profit_split
    
    # Send comprehensive booking notification
    send_notification(
        f"✅ BOOKING CONFIRMED: {provider['name']} | "
        f"${total_cost:,} total | ${deposit_total:,} deposit collected | "
        f"Route: {session['pickup_location']} → {session['destination']} | "
        f"Booking #{BOOKING_STATS['total_bookings']} | "
        f"Conversion rate: {BOOKING_STATS['conversion_rate']:.1%}", 'email'
    )
    
    # Emergency handoff notification (RapidSOS API stub)
    send_notification(
        f"🚨 EMS ALERT: New critical transport dispatch | "
        f"Pickup: {session['pickup_location']} | "
        f"Destination: {session['destination']} | "
        f"Severity: {session['severity']} | "
        f"Provider: {provider['name']}", 'emergency'
    )
    
    # Initialize tracking with emergency handoff capability
    session['current_stage'] = 0
    session['start_time'] = datetime.now().isoformat()
    session['emergency_handoff_enabled'] = True
    
    return render_template('consumer_tracking.html', 
                         provider=provider,
                         stages=TRACKING_STAGES,
                         current_stage=0,
                         progress_percentage=16,  # 6 stages = ~16% per stage
                         emergency_handoff=True)

@consumer_app.route('/tracking_update')
def tracking_update():
    """AJAX endpoint for tracking updates"""
    current_stage = session.get('current_stage', 0)
    
    # Auto-advance every request (simulating 10-second intervals)
    if current_stage < len(TRACKING_STAGES) - 1:
        current_stage += 1
        session['current_stage'] = current_stage
    
    progress_percentage = min((current_stage + 1) * 25, 100)
    
    return {
        'current_stage': current_stage,
        'progress_percentage': progress_percentage,
        'status': TRACKING_STAGES[current_stage] if current_stage < len(TRACKING_STAGES) else 'Complete'
    }

@consumer_app.route('/summary')
def summary():
    """Booking completion summary"""
    if not session.get('selected_provider'):
        return redirect(url_for('landing'))
    
    provider = PROVIDERS[session['selected_provider']]
    
    # Prepare summary data
    summary_data = {
        'provider': provider,
        'pickup_location': session.get('pickup_location'),
        'destination': session.get('destination'),
        'travel_date': session.get('travel_date'),
        'total_cost': session.get('total_cost'),
        'family_seat': session.get('family_seat', False),
        'vip_cabin': session.get('vip_cabin', False),
        'booking_time': session.get('booking_time')
    }
    
    return render_template('consumer_summary.html', summary=summary_data)

@consumer_app.route('/summary_complete', methods=['POST'])
def summary_complete():
    """Handle feedback submission and clear session"""
    feedback = request.form.get('feedback', '')
    if feedback:
        logging.info(f"Consumer feedback received: {feedback}")
    
    # Clear session data
    session.clear()
    flash('Thank you for choosing MediFly! Your session data has been cleared for privacy.', 'success')
    
    return redirect(url_for('landing'))

@consumer_app.route('/admin')
def admin():
    """Admin panel for debugging"""
    return render_template('consumer_admin.html')

@consumer_app.route('/admin_login', methods=['POST'])
def admin_login():
    """Handle admin login"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin' and password == 'demo123':
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid credentials', 'error')
        return redirect(url_for('admin'))

@consumer_app.route('/admin_dashboard')
def admin_dashboard():
    """Admin dashboard with session data and HIPAA masking"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    # Get current session data (excluding admin flag) with HIPAA masking
    session_data = {}
    for k, v in session.items():
        if k == 'admin_logged_in':
            continue
        
        # HIPAA-compliant data masking for sensitive fields
        if k in ['pickup_location', 'destination'] and isinstance(v, str) and len(v) > 3:
            session_data[k] = v[:3] + '***'
        elif k == 'severity' and isinstance(v, int):
            session_data[k] = f"Level {v} (masked)"
        elif k == 'equipment' and isinstance(v, list):
            session_data[k] = f"{len(v)} items (masked)"
        else:
            session_data[k] = v
    
    return render_template('consumer_admin_dashboard.html', 
                         session_data=session_data,
                         booking_stats=BOOKING_STATS)

@consumer_app.route('/dashboard')
def dashboard():
    """Comprehensive profit/revenue/notifications dashboard"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    # Calculate profit split based on current bookings
    current_profit_split = calculate_profit_sharing(BOOKING_STATS['total_bookings'])
    
    # Calculate actual profits (revenue - expenses)
    gross_profit = BOOKING_STATS['total_revenue'] - BOOKING_STATS['total_expenses']
    
    # Calculate individual profit shares
    mike_share = gross_profit * (current_profit_split['mike'] / 100)
    steve_share = gross_profit * (current_profit_split['steve'] / 100)
    business_share = gross_profit * (current_profit_split['business'] / 100)
    
    # Prepare dashboard data
    dashboard_data = {
        'bookings': BOOKING_STATS['total_bookings'],
        'revenue': BOOKING_STATS['total_revenue'],
        'expenses': BOOKING_STATS['total_expenses'],
        'goal_revenue': BOOKING_STATS['goal_revenue'],
        'gross_profit': gross_profit,
        'profit_split': current_profit_split,
        'individual_shares': {
            'mike': mike_share,
            'steve': steve_share,
            'business': business_share
        },
        'unique_visits': BOOKING_STATS['unique_visits'],
        'conversion_rate': BOOKING_STATS['conversion_rate'],
        'provider_diversity': BOOKING_STATS['provider_diversity'],
        'revenue_progress': (BOOKING_STATS['total_revenue'] / BOOKING_STATS['goal_revenue']) * 100
    }
    
    return render_template('consumer_dashboard.html', dashboard=dashboard_data)

@consumer_app.route('/dashboard_export_csv')
def dashboard_export_csv():
    """Export dashboard data as CSV"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    # Simulate CSV export (in production, would generate actual CSV)
    csv_data = f"""Date,Bookings,Revenue,Expenses,Profit,Visits,Conversion
{datetime.now().strftime('%Y-%m-%d')},{BOOKING_STATS['total_bookings']},{BOOKING_STATS['total_revenue']},{BOOKING_STATS['total_expenses']},{BOOKING_STATS['total_revenue'] - BOOKING_STATS['total_expenses']},{BOOKING_STATS['unique_visits']},{BOOKING_STATS['conversion_rate']}"""
    
    send_notification(f"Dashboard CSV exported: {len(csv_data)} bytes", 'email')
    flash('CSV export completed! Check notifications for download link.', 'success')
    return redirect(url_for('dashboard'))

@consumer_app.route('/cancellation_request', methods=['POST'])
def cancellation_request():
    """Handle medical cancellation requests"""
    if not session.get('selected_provider'):
        return redirect(url_for('landing'))
    
    cancellation_reason = request.form.get('cancellation_reason', '')
    medical_documentation = request.form.get('medical_docs', '')
    
    # Simulate medical review process
    if 'medical' in cancellation_reason.lower() or 'emergency' in cancellation_reason.lower():
        refund_eligible = True
        refund_amount = session.get('refundable_prepayment', 6500)
    else:
        refund_eligible = False
        refund_amount = 0
    
    # Log cancellation request
    send_notification(
        f"🔄 CANCELLATION REQUEST: Booking #{BOOKING_STATS['total_bookings']} | "
        f"Reason: {cancellation_reason} | "
        f"Medical docs: {'Yes' if medical_documentation else 'No'} | "
        f"Refund eligible: ${refund_amount:,}", 'email'
    )
    
    session['cancellation_status'] = {
        'requested': True,
        'reason': cancellation_reason,
        'refund_eligible': refund_eligible,
        'refund_amount': refund_amount,
        'request_time': datetime.now().isoformat()
    }
    
    flash(f'Cancellation request submitted. Refund status: ${refund_amount:,} eligible for refund.' if refund_eligible 
          else 'Cancellation request submitted. Non-medical cancellations forfeit prepayment.', 
          'info')
    
    return redirect(url_for('summary'))

if __name__ == '__main__':
    consumer_app.run(host='0.0.0.0', port=5001, debug=True)