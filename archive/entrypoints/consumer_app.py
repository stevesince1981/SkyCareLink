import os
import logging
import json
import math
# import jwt
# import bcrypt
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
# import sympy as sp  # Will be enabled after package installation  
# import stripe  # Will be enabled after package installation
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
consumer_app = Flask(__name__, template_folder='consumer_templates', static_folder='consumer_static')
consumer_app.secret_key = os.environ.get("SESSION_SECRET", "consumer-demo-key-change-in-production")

# # Initialize Flask-Login
# login_manager = LoginManager()
# login_manager.init_app(consumer_app)
# login_manager.login_view = 'login'
# login_manager.login_message = 'Please log in to access this page.'
# login_manager.login_message_category = 'info'

# # Initialize Flask-Limiter for rate limiting
# limiter = Limiter(
#     app=consumer_app,
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"]
# )

# # JWT Configuration
# JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-demo-key-change-in-production")
# JWT_ALGORITHM = "HS256"
# JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
# JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)

# # User class for Flask-Login
# class User(UserMixin):
#     def __init__(self, email, role, name=None):
#         self.id = email
#         self.email = email
#         self.role = role
#         self.name = name or email.split('@')[0].title()
#         self.is_authenticated = True
#         self.is_active = True
#         self.is_anonymous = False

#     def get_id(self):
#         return self.email

# Demo user accounts (simple version without bcrypt)
DEMO_USERS = {
    'family_user': {
        'password': 'demo123',
        'role': 'family',
        'name': 'Sarah Johnson'
    },
    'hospital_staff': {
        'password': 'demo123',
        'role': 'hospital', 
        'name': 'Dr. Michael Chen'
    },
    'provider': {
        'password': 'demo123',
        'role': 'provider',
        'name': 'Captain Lisa Martinez'
    },
    'mvp_user': {
        'password': 'demo123',
        'role': 'mvp',
        'name': 'Alex Thompson'
    },
    'admin': {
        'password': 'demo123',
        'role': 'admin',
        'name': 'Admin User'
    }
}

# Simplified authentication without complex dependencies
def authenticate_user(username, password):
    """Simple authentication function"""
    if username in DEMO_USERS and DEMO_USERS[username]['password'] == password:
        return DEMO_USERS[username]
    return None

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

# Global tracking variables for dashboard with enhanced sample data
BOOKING_STATS = {
    'total_bookings': 7,
    'total_revenue': 189750,  # Sample revenue from completed bookings
    'total_expenses': 42000,  # Operational costs
    'goal_revenue': 375000,
    'unique_visits': 156,
    'conversion_rate': 0.18,
    'provider_diversity': {
        'rural': 3,
        'traditional': 4,
        'drone': 2,
        'hybrid': 2
    },
    'monthly_growth': 0.23,
    'customer_satisfaction': 0.97,
    'average_booking_value': 27107
}

# Profit sharing tiers
PROFIT_TIERS = {
    '1-10': {'mike': 30, 'steve': 30, 'business': 40},
    '11-30': {'mike': 25, 'steve': 25, 'business': 50}, 
    '31+': {'mike': 20, 'steve': 20, 'business': 60}
}

# Sample booking data for Admin/Hospital views
SAMPLE_BOOKINGS = [
    {
        'id': 'MF-2025-001',
        'date': '2025-08-01',
        'patient_name': 'M******* J*****',  # HIPAA masked
        'origin': 'Orlando, FL',
        'destination': 'Minneapolis, MN',
        'provider': 'SkyMed Elite',
        'status': 'Completed',
        'cost': 28500,
        'severity': 4,
        'family_contact': 'S**** (Daughter)',
        'satisfaction_score': 5,
        'provider_rating': 4.8
    },
    {
        'id': 'MF-2025-002', 
        'date': '2025-08-02',
        'patient_name': 'R****** G****',
        'origin': 'Denver, CO',
        'destination': 'Seattle, WA',
        'provider': 'AirCare Mountain',
        'status': 'Completed',
        'cost': 31250,
        'severity': 5,
        'family_contact': 'M*** (Son)',
        'satisfaction_score': 5,
        'provider_rating': 4.9
    },
    {
        'id': 'MF-2025-003',
        'date': '2025-08-03',
        'patient_name': 'Baby G****',
        'origin': 'Phoenix, AZ',
        'destination': 'Los Angeles, CA',
        'provider': 'Life Flight Neonatal',
        'status': 'Completed',
        'cost': 42000,
        'severity': 5,
        'family_contact': 'J******* & M*** (Parents)',
        'satisfaction_score': 5,
        'provider_rating': 5.0
    }
]

# Provider reward system data
PROVIDER_REWARDS = {
    'SkyMed Elite': {
        'total_bookings': 15,
        'revenue_generated': 385000,
        'avg_rating': 4.8,
        'completion_rate': 0.98,
        'tier': 'Gold',
        'rewards_earned': 12500,
        'bonuses': ['Family Friendly', 'On-Time Excellence', 'Safety Leader']
    },
    'AirCare Mountain': {
        'total_bookings': 12,
        'revenue_generated': 298000,
        'avg_rating': 4.9,
        'completion_rate': 1.0,
        'tier': 'Platinum',
        'rewards_earned': 15000,
        'bonuses': ['Rural Specialist', 'Critical Care Expert', 'Perfect Record']
    },
    'Life Flight Neonatal': {
        'total_bookings': 8,
        'revenue_generated': 425000,
        'avg_rating': 5.0,
        'completion_rate': 1.0,
        'tier': 'Diamond',
        'rewards_earned': 22500,
        'bonuses': ['Neonatal Specialist', 'Family Champion', 'Innovation Leader']
    }
}

# OWASP Security scan results (simulated)
SECURITY_SCAN_RESULTS = {
    'last_scan': '2025-08-03 12:00:00',
    'status': 'PASSED',
    'vulnerabilities': {
        'high': 0,
        'medium': 2,
        'low': 3,
        'info': 5
    },
    'recommendations': [
        'Implement Content Security Policy headers',
        'Add rate limiting for API endpoints',
        'Enable HTTPS-only cookies',
        'Implement input validation for all forms',
        'Add session timeout mechanisms'
    ],
    'compliance_score': 94
}

# Bubble migration checklist for after 10 bookings
BUBBLE_MIGRATION_CHECKLIST = {
    'current_bookings': 7,
    'migration_threshold': 10,
    'status': 'Preparing',
    'tasks': [
        {
            'category': 'Data Migration',
            'items': [
                {'task': 'Export user session data to structured format', 'status': 'pending', 'priority': 'high'},
                {'task': 'Create HIPAA-compliant data anonymization scripts', 'status': 'pending', 'priority': 'high'},
                {'task': 'Map current provider database to Bubble schema', 'status': 'pending', 'priority': 'medium'},
                {'task': 'Design booking workflow in Bubble', 'status': 'pending', 'priority': 'high'}
            ]
        },
        {
            'category': 'HIPAA Compliance',
            'items': [
                {'task': 'Set up Business Associate Agreement with Bubble', 'status': 'pending', 'priority': 'critical'},
                {'task': 'Configure encrypted data storage', 'status': 'pending', 'priority': 'critical'},
                {'task': 'Implement audit logging for all patient data access', 'status': 'pending', 'priority': 'high'},
                {'task': 'Create data retention and deletion policies', 'status': 'pending', 'priority': 'high'}
            ]
        },
        {
            'category': 'Technical Setup',
            'items': [
                {'task': 'Configure Bubble workspace and plan upgrade', 'status': 'pending', 'priority': 'medium'},
                {'task': 'Migrate payment processing to production Stripe', 'status': 'pending', 'priority': 'high'},
                {'task': 'Set up real-time notifications and SMS integration', 'status': 'pending', 'priority': 'medium'},
                {'task': 'Create provider dashboard and admin panels', 'status': 'pending', 'priority': 'medium'}
            ]
        }
    ]
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

# Authentication Routes
@consumer_app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Role-based login with security features"""
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        
        # Validate input
        if not email or not password or not role:
            flash('Please fill in all required fields.', 'error')
            return render_template('login.html')
        
        # Check if user exists
        if email not in DEMO_USERS:
            flash('Invalid credentials. Please try again.', 'error')
            return render_template('login.html')
        
        # Verify password
        user_data = DEMO_USERS[email]
        if not bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash']):
            flash('Invalid credentials. Please try again.', 'error')
            return render_template('login.html')
        
        # Verify role matches
        if user_data['role'] != role:
            flash('Role mismatch. Please select the correct role.', 'error')
            return render_template('login.html')
        
        # Create user and login
        user = User(email, user_data['role'], user_data['name'])
        login_user(user)
        
        # Generate JWT token
        jwt_token = generate_jwt_token(user)
        session['jwt_token'] = jwt_token
        
        # Log successful login
        logging.info(f"Successful login: {email} as {role}")
        
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('role_dashboard'))
    
    return render_template('login.html')

@consumer_app.route('/logout')
@login_required
def secure_logout():
    """Secure logout with session cleanup"""
    logging.info(f"User logout: {current_user.email}")
    session.clear()
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@consumer_app.route('/role_dashboard')
@login_required
def role_dashboard():
    """Role-specific dashboard with comprehensive features and admin storyboards"""
    user_role = current_user.role
    
    # Role-specific dashboard data
    dashboard_data = {
        'user': current_user,
        'role': user_role,
        'booking_stats': BOOKING_STATS,
        'sample_bookings': SAMPLE_BOOKINGS[:3],
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'storyboard_data': {
            'revenue_milestone': '$847,500 achieved',
            'security_score': '94% HIPAA compliance',
            'migration_progress': '70% toward Bubble threshold',
            'provider_tiers': '3 active reward levels'
        }
    }
    
    if user_role == 'family':
        dashboard_data.update({
            'family_bookings': [b for b in SAMPLE_BOOKINGS if 'family' in str(b).lower()][:2],
            'upcoming_appointments': [],
            'support_contacts': {
                'emergency': '1-800-MEDIFLY',
                'family_advocate': 'advocate@medifly.com',
                'insurance_help': 'insurance@medifly.com'
            }
        })
        return render_template('family_dashboard.html', **dashboard_data)
    elif user_role == 'hospital':
        dashboard_data.update({
            'bulk_requests': SAMPLE_BOOKINGS,
            'compliance_score': 94,
            'monthly_volume': 7,
            'average_response_time': '4.2 minutes'
        })
        return render_template('hospital_dashboard.html', **dashboard_data)
    elif user_role == 'provider':
        dashboard_data.update({
            'available_requests': [b for b in SAMPLE_BOOKINGS if b['status'] == 'Pending'][:3],
            'active_bookings': [b for b in SAMPLE_BOOKINGS if b['status'] in ['In Progress', 'Completed']][:2],
            'earnings_summary': {
                'this_month': 45000,
                'pending_payments': 12000,
                'total_flights': 5
            }
        })
        return render_template('provider_dashboard.html', **dashboard_data)
    elif user_role == 'mvp':
        dashboard_data.update({
            'early_features': ['AI Cost Estimator', 'Route Optimizer', 'Family Communication Hub'],
            'feedback_requests': 3,
            'beta_access': True
        })
        return render_template('mvp_dashboard.html', **dashboard_data)
    elif user_role == 'admin':
        # Admin gets access to comprehensive admin panel with storyboards
        return redirect(url_for('admin_panel'))
    else:
        return render_template('generic_dashboard.html', **dashboard_data)

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

@consumer_app.route('/admin_panel')
def admin_panel():
    """Admin panel for co-founders with comprehensive data"""
    # Compile comprehensive statistics with business goal tracking
    stats = {
        'total_bookings': 7,  # Updated to match storyboard
        'total_revenue': 847500,  # $847,500 milestone achieved
        'unique_visits': 245,
        'conversion_rate': 0.029,  # 2.9% conversion rate (7/245)
        'customer_satisfaction': 0.98  # 98% satisfaction
    }
    
    # Update global stats to match
    BOOKING_STATS.update(stats)
    
    return render_template('admin_panel.html', 
                         bookings=SAMPLE_BOOKINGS,
                         provider_rewards=PROVIDER_REWARDS,
                         security_scan=SECURITY_SCAN_RESULTS,
                         migration_checklist=BUBBLE_MIGRATION_CHECKLIST,
                         stats=stats)

@consumer_app.route('/admin_storyboard')
def admin_storyboard():
    """Admin feature storyboard demonstration"""
    return render_template('admin_storyboard.html',
                         booking_stats=BOOKING_STATS,
                         sample_bookings=SAMPLE_BOOKINGS)

@consumer_app.route('/provider_search')
def provider_search():
    """Hospital/Provider search interface for previous bookings"""
    search_query = request.args.get('search', '')
    
    # Filter sample bookings based on search
    filtered_bookings = SAMPLE_BOOKINGS
    if search_query:
        filtered_bookings = [
            booking for booking in SAMPLE_BOOKINGS 
            if search_query.lower() in booking['id'].lower() or 
               search_query.lower() in booking['provider'].lower() or
               search_query.lower() in booking['origin'].lower() or
               search_query.lower() in booking['destination'].lower()
        ]
    
    return render_template('provider_search.html', 
                         bookings=filtered_bookings,
                         search_query=search_query,
                         provider_rewards=PROVIDER_REWARDS)

@consumer_app.route('/security_scan')
def security_scan():
    """OWASP security scan results"""
    return render_template('security_scan.html', scan_results=SECURITY_SCAN_RESULTS)

@consumer_app.route('/run_security_scan', methods=['POST'])
def run_security_scan():
    """Simulate running an OWASP security scan"""
    # Update scan timestamp
    SECURITY_SCAN_RESULTS['last_scan'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Simulate random scan results
    import random
    SECURITY_SCAN_RESULTS['vulnerabilities']['medium'] = random.randint(0, 3)
    SECURITY_SCAN_RESULTS['vulnerabilities']['low'] = random.randint(1, 5)
    SECURITY_SCAN_RESULTS['compliance_score'] = random.randint(92, 98)
    
    flash('Security scan completed successfully!', 'success')
    return redirect(url_for('security_scan'))

@consumer_app.route('/migration_status')
def migration_status():
    """Bubble migration status and checklist"""
    # Update current booking count
    BUBBLE_MIGRATION_CHECKLIST['current_bookings'] = BOOKING_STATS['total_bookings']
    
    # Update status based on booking count
    if BOOKING_STATS['total_bookings'] >= 10:
        BUBBLE_MIGRATION_CHECKLIST['status'] = 'Ready for Migration'
    elif BOOKING_STATS['total_bookings'] >= 8:
        BUBBLE_MIGRATION_CHECKLIST['status'] = 'Almost Ready'
    else:
        BUBBLE_MIGRATION_CHECKLIST['status'] = 'Preparing'
    
    return render_template('migration_status.html', migration=BUBBLE_MIGRATION_CHECKLIST)

@consumer_app.route('/provider_rewards')
def provider_rewards():
    """Provider reward system dashboard"""
    return render_template('provider_rewards.html', provider_rewards=PROVIDER_REWARDS)

if __name__ == '__main__':
    consumer_app.run(host='0.0.0.0', port=5001, debug=True)