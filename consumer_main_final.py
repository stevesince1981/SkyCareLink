import os
import logging
import json
import uuid
import csv
import hashlib
import hmac
import secrets
import shutil
from pathlib import Path
# import requests  # Will install if Google Places API is needed
from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo
    EST = ZoneInfo("America/New_York")
except ImportError:
    # Fallback for older Python versions
    EST = timezone(timedelta(hours=-5))
import random
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_file, Response
import io

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database integration
try:
    from app import db
    from models import (
        User, Niche, Affiliate, Hospital, Booking, Quote, Commission,
        AffiliateNiche, Announcement, SecurityEvent
    )
    from seed_data import seed_dummy_data, remove_dummy_data, get_dummy_data_status
    DB_AVAILABLE = True
    print("✓ Database components loaded successfully")
except ImportError as e:
    print(f"⚠ Database not available: {e}")
    DB_AVAILABLE = False

# Create Flask app
consumer_app = Flask(__name__, template_folder='consumer_templates', static_folder='consumer_static', static_url_path='/consumer_static')
consumer_app.secret_key = os.environ.get("SESSION_SECRET", "consumer-demo-key-change-in-production")

# Demo user accounts with hashed passwords (bcrypt-compatible format)
DEMO_USERS = {
    'family': {
        'password_hash': '$2b$12$9xZ7LGEPmXM5UvQfM2.mreK9hHhOqVd9lJcLzX8YeKNpA3KzL5Ae6',  # demo123
        'role': 'family', 'name': 'Sarah Johnson'
    },
    'hospital': {
        'password_hash': '$2b$12$9xZ7LGEPmXM5UvQfM2.mreK9hHhOqVd9lJcLzX8YeKNpA3KzL5Ae6',  # demo123
        'role': 'hospital', 'name': 'Dr. Michael Chen'
    },
    'affiliate': {
        'password_hash': '$2b$12$9xZ7LGEPmXM5UvQfM2.mreK9hHhOqVd9lJcLzX8YeKNpA3KzL5Ae6',  # demo123
        'role': 'affiliate', 'name': 'Captain Lisa Martinez'
    },
    'provider': {
        'password_hash': '$2b$12$9xZ7LGEPmXM5UvQfM2.mreK9hHhOqVd9lJcLzX8YeKNpA3KzL5Ae6',  # demo123
        'role': 'affiliate', 'name': 'Captain Lisa Martinez'
    },
    'mvp': {
        'password_hash': '$2b$12$9xZ7LGEPmXM5UvQfM2.mreK9hHhOqVd9lJcLzX8YeKNpA3KzL5Ae6',  # demo123
        'role': 'mvp', 'name': 'Alex Thompson'
    },
    'admin': {
        'password_hash': '$2b$12$9xZ7LGEPmXM5UvQfM2.mreK9hHhOqVd9lJcLzX8YeKNpA3KzL5Ae6',  # demo123
        'role': 'admin', 'name': 'Admin User'
    }
}

# Global configuration - adjustable non-refundable fee
MEDFLY_CONFIG = {
    'non_refundable_fee': int(os.environ.get("MEDFLY_FEE", "1000")),
    'openweather_api_key': os.environ.get("OPENWEATHER_API_KEY", "demo-key"),
    'google_places_api_key': os.environ.get("GOOGLE_PLACES_API_KEY", "demo-key"),
    'twilio_account_sid': os.environ.get("TWILIO_ACCOUNT_SID", "demo-sid"),
    'twilio_auth_token': os.environ.get("TWILIO_AUTH_TOKEN", "demo-token"),
    'sendgrid_api_key': os.environ.get("SENDGRID_API_KEY", "demo-key")
}

# Phase 6.A: Commission Configuration
COMMISSION_CONFIG = {
    'base_rate': 0.04,  # 4% until $25k recoup threshold
    'tier_2_rate': 0.05,  # 5% after $25k recoup threshold
    'recoup_threshold_usd': 25000,
    'recoup_rate': 0.01,  # 1% added to recoup when under threshold
    'invoice_net_days': 7  # NET 7 payment terms
}

# Phase 7.A: Operational Controls Configuration
OPERATIONAL_CONFIG = {
    'strike_rules': {
        'lifetime_ban_threshold': 2,
        'relist_fee_usd': 25000,
        'relist_penalty': 'no 1% payback in year 1'
    },
    'training_limits': {
        'dummy_cases_per_affiliate': 50,
        'reset_policy': 'monthly'
    },
    'delist_reasons': [
        'Unpaid affiliate fee/commission',
        'False licensing attestation (Part 135)', 
        'Service misrepresentation',
        'Quality/SLA failure',
        'Other (notes required)'
    ]
}

# Equipment pricing (dynamic)
EQUIPMENT_PRICING = {
    'ventilator': 5000,
    'ecmo': 10000,
    'incubator': 3000,
    'escort': 2000,
    'oxygen': 1000,
    'other': 0
}

# Subscription pricing
SUBSCRIPTION_PRICING = {
    'monthly': {'price': 49, 'type': 'month'},
    'yearly': {'price': 499, 'type': 'year', 'savings': 89}
}

# Mock affiliate database (air operators) - Enhanced for Phase 5.A
MOCK_AFFILIATES = [
    {
        'name': 'AirMed Response', 
        'base_price': 128000, 
        'capabilities': ['ventilator', 'ecmo'], 
        'priority': True,
        'response_rate_30d': 85,  # Response rate percentage
        'total_bookings': 120,
        'days_since_join': 180,
        'ground_included': True,
        'last_response_time': '2025-08-09T10:30:00Z'
    },
    {
        'name': 'LifeFlight Elite', 
        'base_price': 135000, 
        'capabilities': ['incubator', 'escort'], 
        'priority': True,
        'response_rate_30d': 92,
        'total_bookings': 45,  # < 50 bookings = spotlight
        'days_since_join': 45,  # < 90 days = spotlight
        'ground_included': True,
        'last_response_time': '2025-08-09T11:15:00Z'
    },
    {
        'name': 'CriticalCare Jets', 
        'base_price': 142000, 
        'capabilities': ['ventilator', 'oxygen'], 
        'priority': True,
        'response_rate_30d': 45,  # < 50% = deprioritized
        'total_bookings': 80,
        'days_since_join': 200,
        'ground_included': False,
        'last_response_time': '2025-08-08T14:20:00Z'
    },
    {
        'name': 'MedEvac Solutions', 
        'base_price': 125000, 
        'capabilities': ['oxygen', 'escort'], 
        'priority': False,
        'response_rate_30d': 78,
        'total_bookings': 95,
        'days_since_join': 150,
        'ground_included': True,
        'last_response_time': '2025-08-09T09:45:00Z'
    },
    {
        'name': 'Emergency Wings', 
        'base_price': 138000, 
        'capabilities': ['ventilator', 'incubator'], 
        'priority': False,
        'response_rate_30d': 67,
        'total_bookings': 25,  # < 50 bookings = spotlight
        'days_since_join': 30,  # < 90 days = spotlight
        'ground_included': False,
        'last_response_time': '2025-08-09T12:00:00Z'
    },
    {
        'name': 'Skyward Medical', 
        'base_price': 148000, 
        'capabilities': ['ecmo', 'escort'], 
        'priority': False,
        'response_rate_30d': 88,
        'total_bookings': 65,
        'days_since_join': 120,
        'ground_included': True,
        'last_response_time': '2025-08-09T13:30:00Z'
    },
    {
        'name': 'Rapid Response Air', 
        'base_price': 132000, 
        'capabilities': ['oxygen', 'ventilator'], 
        'priority': False,
        'response_rate_30d': 72,
        'total_bookings': 110,
        'days_since_join': 300,
        'ground_included': True,
        'last_response_time': '2025-08-09T08:15:00Z'
    },
    {
        'name': 'Guardian Flight Services', 
        'base_price': 155000, 
        'capabilities': ['incubator', 'ecmo'], 
        'priority': False,
        'response_rate_30d': 95,
        'total_bookings': 75,
        'days_since_join': 90,
        'ground_included': False,
        'last_response_time': '2025-08-09T14:45:00Z'
    }
]

# Training/Dummy mode configuration
TRAINING_CONFIG = {
    'enabled': True,  # Per-organization toggle
    'case_limit': 50,  # 50-case cap
    'auto_quote_delay': 30,  # ~30s auto-quotes
    'purge_days': 7,  # 7-day purge
    'dummy_label': 'DUMMY DATA - TRAINING MODE'
}

# Drafts system configuration
DRAFTS_CONFIG = {
    'auto_save_interval': 30,  # seconds
    'draft_expiry_days': 7,
    'max_drafts_per_user': 10
}

# Quote Distribution Configuration - Phase 5.A
QUOTE_CONFIG = {
    'response_window_min': 15,  # minimum minutes for quotes
    'response_window_max': 60,  # maximum minutes for quotes
    'default_visible_quotes': 5,  # show 5 quotes initially
    'expand_increment': 5,  # show 5 more when expanding
    'fairness_threshold': 50,  # response rate % threshold
    'spotlight_booking_threshold': 50,  # bookings for spotlight eligibility
    'spotlight_days_threshold': 90,  # days since join for spotlight
    'saturated_market_delay': 120  # 2 hours max delay message
}

def get_affiliate_priority_order():
    """Sort affiliates by fairness rules: high responders first, then deprioritized low responders"""
    affiliates = MOCK_AFFILIATES.copy()
    
    # Separate by response rate
    high_responders = [a for a in affiliates if a['response_rate_30d'] >= QUOTE_CONFIG['fairness_threshold']]
    low_responders = [a for a in affiliates if a['response_rate_30d'] < QUOTE_CONFIG['fairness_threshold']]
    
    # Sort each group by response rate (descending)
    high_responders.sort(key=lambda x: x['response_rate_30d'], reverse=True)
    low_responders.sort(key=lambda x: x['response_rate_30d'], reverse=True)
    
    # High responders first, then low responders (deprioritized but not blocked)
    return high_responders + low_responders

def has_spotlight_badge(affiliate):
    """Determine if affiliate gets spotlight badge (new or low booking count)"""
    return (affiliate['total_bookings'] < QUOTE_CONFIG['spotlight_booking_threshold'] or 
            affiliate['days_since_join'] < QUOTE_CONFIG['spotlight_days_threshold'])

def generate_mock_quotes(request_data, affiliate_count=None):
    """Generate mock quotes with fairness ordering and realistic timing"""
    ordered_affiliates = get_affiliate_priority_order()
    
    if affiliate_count:
        # Limit to specific count for testing
        ordered_affiliates = ordered_affiliates[:affiliate_count]
    
    quotes = []
    base_equipment_cost = sum(EQUIPMENT_PRICING.get(eq, 0) for eq in request_data.get('equipment', []))
    
    for i, affiliate in enumerate(ordered_affiliates):
        # Simulate some affiliates not responding (based on response rate)
        if random.randint(1, 100) > affiliate['response_rate_30d']:
            continue  # This affiliate didn't respond
        
        equipment_cost = base_equipment_cost
        total_cost = affiliate['base_price'] + equipment_cost
        
        # Add same-day upcharge if applicable
        if request_data.get('same_day'):
            total_cost += int(total_cost * 0.2)
        
        # Add subscription discount if applicable
        if request_data.get('subscription_discount'):
            total_cost = int(total_cost * 0.9)
        
        quote = {
            'affiliate_id': f"affiliate_{i+1}",
            'affiliate_name': affiliate['name'],
            'aircraft_type': random.choice(['King Air 350', 'Citation CJ3', 'Learjet 45', 'Beechcraft Premier']),
            'total_cost': total_cost,
            'base_cost': affiliate['base_price'],
            'equipment_cost': equipment_cost,
            'eta_minutes': random.randint(45, 120),
            'capabilities': affiliate['capabilities'],
            'ground_included': affiliate['ground_included'],
            'response_rate': affiliate['response_rate_30d'],
            'spotlight_badge': has_spotlight_badge(affiliate),
            'priority_partner': affiliate['priority'],
            'response_time_minutes': random.randint(QUOTE_CONFIG['response_window_min'], QUOTE_CONFIG['response_window_max'])
        }
        quotes.append(quote)
    
    # Sort by total cost for display
    quotes.sort(key=lambda x: x['total_cost'])
    return quotes

# Provider Search System - JSON-based cache with upgrade path
PROVIDERS_INDEX_PATH = 'data/providers_index.json'
SEARCH_METRICS_PATH = 'data/search_metrics.json'

def load_index():
    """Load providers index from JSON file"""
    try:
        with open(PROVIDERS_INDEX_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"providers": []}

def save_index(index_data):
    """Save providers index to JSON file"""
    os.makedirs('data', exist_ok=True)
    with open(PROVIDERS_INDEX_PATH, 'w') as f:
        json.dump(index_data, f, indent=2)

def load_metrics():
    """Load search metrics from JSON file"""
    try:
        with open(SEARCH_METRICS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "period_start": datetime.utcnow().isoformat() + "Z",
            "internal_hits": 0,
            "external_hits": 0,
            "manual_entries": 0
        }

def save_metrics(metrics_data):
    """Save search metrics to JSON file"""
    os.makedirs('data', exist_ok=True)
    with open(SEARCH_METRICS_PATH, 'w') as f:
        json.dump(metrics_data, f, indent=2)

def search_internal(query):
    """Search internal providers index - case insensitive substring match"""
    index = load_index()
    query_lower = query.lower()
    
    results = []
    for provider in index['providers']:
        if not provider.get('approved', False):
            continue
            
        name_match = query_lower in provider['name'].lower()
        address_match = query_lower in provider['address'].lower()
        
        if name_match or address_match:
            results.append(provider)
    
    # Sort by search_count_90d (popularity) and return top 5
    results.sort(key=lambda x: x.get('search_count_90d', 0), reverse=True)
    return results[:5]

def promote_or_increment(provider_id):
    """Increment search count for selected internal provider"""
    index = load_index()
    
    for provider in index['providers']:
        if provider['id'] == provider_id:
            provider['search_count_90d'] = provider.get('search_count_90d', 0) + 1
            provider['updated_at'] = datetime.utcnow().isoformat() + "Z"
            break
    
    save_index(index)

def submit_manual_entry(name, address, provider_type):
    """Add manual provider entry for admin approval"""
    index = load_index()
    
    new_provider = {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": provider_type,
        "address": address,
        "lat": None,
        "lng": None,
        "source": "manual",
        "approved": False,
        "search_count_90d": 0,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    index['providers'].append(new_provider)
    save_index(index)
    
    # Update metrics
    metrics = load_metrics()
    metrics['manual_entries'] += 1
    save_metrics(metrics)
    
    return new_provider

def record_hit_ratio(source):
    """Record search hit by source type"""
    metrics = load_metrics()
    
    # Check if period is > 90 days old, reset if needed
    period_start = datetime.fromisoformat(metrics['period_start'].replace('Z', '+00:00'))
    if datetime.utcnow() - period_start.replace(tzinfo=None) > timedelta(days=90):
        metrics = {
            "period_start": datetime.utcnow().isoformat() + "Z",
            "internal_hits": 0,
            "external_hits": 0,
            "manual_entries": 0
        }
    
    if source == 'internal':
        metrics['internal_hits'] += 1
    elif source == 'external':
        metrics['external_hits'] += 1
    
    save_metrics(metrics)

def search_google_places(query, api_key):
    """Search Google Places API for providers - stub implementation"""
    if not api_key or api_key == "demo-key":
        return []
    
    # Return mock results for demonstration (Google Places would be enabled with real API key)
    logging.info(f"Google Places API stub called for query: {query}")
    return []

# Phase 8.A: Authentication Security System
SECURITY_CONFIG = {
    'max_attempts_per_ip': 5,
    'max_attempts_per_user': 5,
    'lockout_duration_hours': 1,
    'rate_limit_window_hours': 1,
    'session_timeout_minutes': 30,
    'remember_me_days': 30,
    'mfa_code_length': 6,
    'mfa_expiry_minutes': 10
}

def load_security_data(filename, default_data):
    """Load security data from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs('data', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(default_data, f, indent=2)
        return default_data

def save_security_data(filename, data):
    """Save security data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def log_security_event(username, event_type, ip_address, user_agent, details=None):
    """Log security events to security_log.json"""
    security_log = load_security_data('data/security_log.json', {'events': []})
    
    event = {
        'timestamp': datetime.now().isoformat(),
        'user': username or 'unknown',
        'type': event_type,
        'ip': ip_address,
        'user_agent': user_agent[:100] if user_agent else 'unknown',
        'details': details or {}
    }
    
    security_log['events'].append(event)
    
    # Keep only last 1000 events to manage file size
    if len(security_log['events']) > 1000:
        security_log['events'] = security_log['events'][-1000:]
    
    save_security_data('data/security_log.json', security_log)
    logging.info(f"Security event logged: {event_type} for {username} from {ip_address}")

def check_rate_limits(ip_address, username=None):
    """Check rate limits for IP and username"""
    rate_limits = load_security_data('data/rate_limits.json', 
                                   {'ip_attempts': {}, 'user_attempts': {}, 'locked_accounts': {}})
    
    now = datetime.now()
    cutoff_time = now - timedelta(hours=SECURITY_CONFIG['rate_limit_window_hours'])
    
    # Clean old attempts
    for ip in list(rate_limits['ip_attempts'].keys()):
        rate_limits['ip_attempts'][ip] = [
            attempt for attempt in rate_limits['ip_attempts'][ip]
            if datetime.fromisoformat(attempt) > cutoff_time
        ]
        if not rate_limits['ip_attempts'][ip]:
            del rate_limits['ip_attempts'][ip]
    
    for user in list(rate_limits['user_attempts'].keys()):
        rate_limits['user_attempts'][user] = [
            attempt for attempt in rate_limits['user_attempts'][user]
            if datetime.fromisoformat(attempt) > cutoff_time
        ]
        if not rate_limits['user_attempts'][user]:
            del rate_limits['user_attempts'][user]
    
    # Check IP rate limit
    ip_attempts = len(rate_limits['ip_attempts'].get(ip_address, []))
    if ip_attempts >= SECURITY_CONFIG['max_attempts_per_ip']:
        return {'allowed': False, 'reason': 'ip_rate_limit', 'attempts': ip_attempts}
    
    # Check user rate limit if username provided
    if username:
        user_attempts = len(rate_limits['user_attempts'].get(username, []))
        if user_attempts >= SECURITY_CONFIG['max_attempts_per_user']:
            return {'allowed': False, 'reason': 'user_rate_limit', 'attempts': user_attempts}
        
        # Check if account is locked
        if username in rate_limits['locked_accounts']:
            lock_until = datetime.fromisoformat(rate_limits['locked_accounts'][username])
            if now < lock_until:
                return {'allowed': False, 'reason': 'account_locked', 'lock_until': lock_until.isoformat()}
            else:
                del rate_limits['locked_accounts'][username]
    
    save_security_data('data/rate_limits.json', rate_limits)
    return {'allowed': True}

def record_failed_attempt(ip_address, username=None):
    """Record a failed login attempt"""
    rate_limits = load_security_data('data/rate_limits.json', 
                                   {'ip_attempts': {}, 'user_attempts': {}, 'locked_accounts': {}})
    
    now = datetime.now().isoformat()
    
    # Record IP attempt
    if ip_address not in rate_limits['ip_attempts']:
        rate_limits['ip_attempts'][ip_address] = []
    rate_limits['ip_attempts'][ip_address].append(now)
    
    # Record user attempt
    if username:
        if username not in rate_limits['user_attempts']:
            rate_limits['user_attempts'][username] = []
        rate_limits['user_attempts'][username].append(now)
        
        # Check if user should be soft-locked
        if len(rate_limits['user_attempts'][username]) >= SECURITY_CONFIG['max_attempts_per_user']:
            lock_until = datetime.now() + timedelta(hours=SECURITY_CONFIG['lockout_duration_hours'])
            rate_limits['locked_accounts'][username] = lock_until.isoformat()
            
            # Send alert email (stub)
            send_security_alert(username, 'account_locked', {
                'reason': 'too_many_failures',
                'lock_until': lock_until.isoformat()
            })
    
    save_security_data('data/rate_limits.json', rate_limits)

def detect_anomaly(username, ip_address, user_agent):
    """Detect login anomalies for step-up authentication"""
    user_settings = load_security_data('data/user_settings.json', {'users': {}})
    
    if username not in user_settings['users']:
        user_settings['users'][username] = {
            'known_ips': [],
            'known_user_agents': [],
            'last_login': None,
            'mfa_enabled': False
        }
    
    user_data = user_settings['users'][username]
    risk_factors = []
    
    # Check for new IP
    if ip_address not in user_data['known_ips']:
        risk_factors.append('new_ip')
        user_data['known_ips'].append(ip_address)
        # Keep only last 10 IPs
        user_data['known_ips'] = user_data['known_ips'][-10:]
    
    # Check for new user agent
    ua_signature = hashlib.md5(user_agent.encode()).hexdigest()[:8] if user_agent else 'unknown'
    if ua_signature not in user_data['known_user_agents']:
        risk_factors.append('new_device')
        user_data['known_user_agents'].append(ua_signature)
        # Keep only last 5 user agents
        user_data['known_user_agents'] = user_data['known_user_agents'][-5:]
    
    # Check time anomaly (login outside 6 AM - 11 PM local time)
    current_hour = datetime.now().hour
    if current_hour < 6 or current_hour > 23:
        risk_factors.append('odd_time')
    
    user_data['last_login'] = datetime.now().isoformat()
    save_security_data('data/user_settings.json', user_settings)
    
    return {
        'is_risky': len(risk_factors) > 0,
        'risk_factors': risk_factors,
        'require_step_up': len(risk_factors) >= 2 or 'new_ip' in risk_factors
    }

def generate_mfa_code():
    """Generate 6-digit MFA code"""
    return f"{random.randint(100000, 999999)}"

def send_mfa_code(username, email, code):
    """Send MFA code via email (stub implementation)"""
    logging.info(f"MFA CODE STUB - To: {email}, Code: {code}, User: {username}")
    # In production, use SMTP or email service
    return True

def send_security_alert(username, alert_type, details):
    """Send security alert to user (stub implementation)"""
    alerts = {
        'account_locked': f"Account locked due to suspicious activity: {details.get('reason')}",
        'new_login': f"New login detected from IP: {details.get('ip')}, Location: {details.get('location', 'Unknown')}",
        'reset_attempt': f"Password reset requested. If this wasn't you, reply NO to lock your account.",
        'anomaly_detected': f"Unusual login activity detected: {', '.join(details.get('risk_factors', []))}"
    }
    
    message = alerts.get(alert_type, f"Security alert: {alert_type}")
    logging.info(f"SECURITY ALERT STUB - To: {username}, Alert: {message}")
    # In production, send actual email/SMS
    return True

def hash_password(password):
    """Hash password using bcrypt-compatible method (simplified for demo)"""
    # In production, use actual bcrypt
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"pbkdf2_sha256${salt}${hashed.hex()}"

def verify_password(password, password_hash):
    """Verify password against hash"""
    if password_hash.startswith('$2b$'):
        # Demo bcrypt hashes - verify against demo123
        return password == 'demo123'
    elif password_hash.startswith('pbkdf2_sha256$'):
        # Verify PBKDF2 hash
        try:
            _, salt, stored_hash = password_hash.split('$')
            hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hashed.hex() == stored_hash
        except:
            return False
    return False

def authenticate_user(username, password, ip_address=None, user_agent=None):
    """Enhanced authentication with rate limiting and anomaly detection"""
    ip_address = ip_address or request.environ.get('REMOTE_ADDR', 'unknown')
    user_agent = user_agent or request.headers.get('User-Agent', 'unknown')
    
    # Check rate limits
    rate_check = check_rate_limits(ip_address, username)
    if not rate_check['allowed']:
        log_security_event(username, 'login_rate_limited', ip_address, user_agent, rate_check)
        return None
    
    # Check user exists and password is correct
    if username in DEMO_USERS:
        user_data = DEMO_USERS[username]
        if verify_password(password, user_data['password_hash']):
            # Detect anomalies
            anomaly = detect_anomaly(username, ip_address, user_agent)
            
            log_security_event(username, 'login_success', ip_address, user_agent, {
                'anomaly_detected': anomaly['is_risky'],
                'risk_factors': anomaly['risk_factors']
            })
            
            # Send security alert for risky logins
            if anomaly['is_risky']:
                send_security_alert(username, 'anomaly_detected', anomaly)
                log_security_event(username, 'anomaly_alert_sent', ip_address, user_agent, anomaly)
            
            return {**user_data, 'requires_mfa': anomaly['require_step_up']}
        else:
            # Record failed attempt
            record_failed_attempt(ip_address, username)
            log_security_event(username, 'login_failed', ip_address, user_agent, {'reason': 'invalid_password'})
    else:
        # Record failed attempt for unknown user
        record_failed_attempt(ip_address, username)
        log_security_event(username, 'login_failed', ip_address, user_agent, {'reason': 'unknown_user'})
    
    return None

def generate_quote_session():
    """Generate unique quote session with 24-hour expiry"""
    quote_id = str(uuid.uuid4())
    session['quote_id'] = quote_id
    session['quote_expiry'] = (datetime.now() + timedelta(hours=24)).isoformat()
    session['slots_remaining'] = 2
    return quote_id

def get_affiliate_quotes(origin, destination, equipment_list, transport_type, is_training_mode=False):
    """Generate mock affiliate quotes using Phase 5.A fairness system"""
    request_data = {
        'origin': origin,
        'destination': destination,
        'equipment': equipment_list,
        'transport_type': transport_type,
        'same_day': transport_type == 'critical',
        'subscription_discount': False  # Can be updated based on session
    }
    
    # Use the new fairness-based quote generation
    quotes = generate_mock_quotes(request_data)
    
    # Convert to legacy format for compatibility
    formatted_quotes = []
    for quote in quotes:
        formatted_quotes.append({
            'affiliate_id': quote['affiliate_id'],
            'affiliate_name': quote['affiliate_name'],
            'masked_name': f"Affiliate {quote['affiliate_id'][-1]}****",
            'total_cost': quote['total_cost'],
            'equipment_cost': quote['equipment_cost'],
            'capabilities': quote['capabilities'],
            'priority': quote['priority_partner'],
            'eta_hours': round(quote['eta_minutes'] / 60, 1),
            'is_training': is_training_mode,
            'ground_included': quote['ground_included'],
            'response_rate': quote['response_rate'],
            'spotlight_badge': quote['spotlight_badge'],
            'response_time_minutes': quote['response_time_minutes']
        })
    
    return formatted_quotes

def save_draft(session_data, draft_id=None):
    """Auto-save draft functionality"""
    if not draft_id:
        draft_id = str(uuid.uuid4())
    
    draft_data = {
        'id': draft_id,
        'data': session_data,
        'status': 'draft',
        'created_at': datetime.now().isoformat(),
        'last_modified': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(days=DRAFTS_CONFIG['draft_expiry_days'])).isoformat()
    }
    
    # In production, save to database
    # For demo, store in session
    if 'drafts' not in session:
        session['drafts'] = {}
    session['drafts'][draft_id] = draft_data
    session.modified = True
    
    logging.info(f"Draft saved: {draft_id}")
    return draft_id

def load_draft(draft_id):
    """Load saved draft data"""
    if 'drafts' in session and draft_id in session['drafts']:
        return session['drafts'][draft_id]
    return None

def delete_draft(draft_id):
    """Delete a draft (only for draft status)"""
    if 'drafts' in session and draft_id in session['drafts']:
        draft = session['drafts'][draft_id]
        if draft['status'] == 'draft':
            del session['drafts'][draft_id]
            session.modified = True
            return True
    return False

def cancel_active_request(request_id):
    """Cancel an active quoted request (cannot delete, only cancel)"""
    # In production, update status in database
    logging.info(f"Request cancelled: {request_id}")
    return True

def send_urgency_alert(user_contact, hours_remaining, quote_data):
    """Stub for sending SMS/email urgency alerts"""
    alert_messages = {
        12: "Your quote expires in 12 hours—secure now?",
        6: "6 hours remaining—act soon",
        1: "1 hour left—finalize payment!"
    }
    
    message = alert_messages.get(hours_remaining, "Quote expiring soon!")
    logging.info(f"ALERT STUB - To: {user_contact}, Message: {message}")
    return True

# Routes
@consumer_app.route('/')
def home():
    """Home landing page with hero and CTAs"""
    return render_template('home.html')

@consumer_app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@consumer_app.route('/login', methods=['POST'])
def login_post():
    """Enhanced login with rate limiting, MFA, and anomaly detection"""
    username = request.form.get('username')
    password = request.form.get('password')
    remember_me = 'remember_me' in request.form
    
    ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    user = authenticate_user(username, password, ip_address, user_agent)
    if user:
        # Check if MFA is required
        if user.get('requires_mfa'):
            # Store user data temporarily for MFA verification
            session['pending_login'] = {
                'username': username,
                'user_data': user,
                'remember_me': remember_me,
                'ip_address': ip_address,
                'user_agent': user_agent
            }
            
            # Generate and send MFA code
            mfa_code = generate_mfa_code()
            session['mfa_code'] = mfa_code
            session['mfa_expiry'] = (datetime.now() + timedelta(minutes=SECURITY_CONFIG['mfa_expiry_minutes'])).isoformat()
            
            # Send MFA code (stub)
            email = f"{username}@demo.com"  # Demo email
            send_mfa_code(username, email, mfa_code)
            
            log_security_event(username, 'mfa_challenge_sent', ip_address, user_agent, {
                'reason': 'step_up_required',
                'risk_factors': user.get('risk_factors', [])
            })
            
            flash(f'Security check required. MFA code sent to {email}', 'warning')
            return redirect(url_for('mfa_verify'))
        else:
            # Complete login without MFA
            session['logged_in'] = True
            session['user_role'] = user['role']
            session['contact_name'] = user['name']
            session['username'] = username
            
            # Set session timeout
            if remember_me:
                session.permanent = True
                consumer_app.permanent_session_lifetime = timedelta(days=SECURITY_CONFIG['remember_me_days'])
            else:
                session.permanent = True
                consumer_app.permanent_session_lifetime = timedelta(minutes=SECURITY_CONFIG['session_timeout_minutes'])
            
            # Regenerate session for security
            session.regenerate = True
            
            flash(f'Welcome, {user["name"]}!', 'success')
            
            # Role-based redirects
            if user['role'] == 'affiliate':
                return redirect(url_for('affiliate_commissions'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'hospital':
                return redirect(url_for('consumer_requests'))
            else:
                return redirect(url_for('home'))
    else:
        flash('Invalid credentials or too many attempts. Try: family, hospital, affiliate, mvp, or admin with password: demo123', 'error')
        return redirect(url_for('login'))

@consumer_app.route('/mfa')
def mfa_verify():
    """MFA verification page"""
    if 'pending_login' not in session:
        flash('No pending login found.', 'error')
        return redirect(url_for('login'))
    
    return render_template('mfa_verify.html')

@consumer_app.route('/mfa', methods=['POST'])
def mfa_verify_post():
    """Process MFA verification"""
    if 'pending_login' not in session:
        flash('No pending login found.', 'error')
        return redirect(url_for('login'))
    
    entered_code = request.form.get('mfa_code')
    stored_code = session.get('mfa_code')
    mfa_expiry = session.get('mfa_expiry')
    
    pending = session['pending_login']
    username = pending['username']
    ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    # Check if code expired
    if mfa_expiry and datetime.now() > datetime.fromisoformat(mfa_expiry):
        session.pop('pending_login', None)
        session.pop('mfa_code', None)
        session.pop('mfa_expiry', None)
        
        log_security_event(username, 'mfa_expired', ip_address, user_agent)
        flash('MFA code expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    # Verify code
    if entered_code == stored_code:
        # Complete login
        user = pending['user_data']
        session['logged_in'] = True
        session['user_role'] = user['role']
        session['contact_name'] = user['name']
        session['username'] = username
        
        # Set session timeout
        if pending['remember_me']:
            session.permanent = True
            consumer_app.permanent_session_lifetime = timedelta(days=SECURITY_CONFIG['remember_me_days'])
        else:
            session.permanent = True
            consumer_app.permanent_session_lifetime = timedelta(minutes=SECURITY_CONFIG['session_timeout_minutes'])
        
        # Clean up MFA session data
        session.pop('pending_login', None)
        session.pop('mfa_code', None)
        session.pop('mfa_expiry', None)
        
        log_security_event(username, 'mfa_success', ip_address, user_agent)
        flash(f'Welcome, {user["name"]}! Security verification completed.', 'success')
        
        # Role-based redirects
        if user['role'] == 'affiliate':
            return redirect(url_for('affiliate_commissions'))
        elif user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user['role'] == 'hospital':
            return redirect(url_for('consumer_requests'))
        else:
            return redirect(url_for('home'))
    else:
        log_security_event(username, 'mfa_failed', ip_address, user_agent)
        flash('Invalid MFA code. Please try again.', 'error')
        return redirect(url_for('mfa_verify'))

@consumer_app.route('/logout')
def logout():
    """Enhanced logout with security logging"""
    username = session.get('username', 'unknown')
    ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    log_security_event(username, 'logout', ip_address, user_agent)
    
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

@consumer_app.route('/reset', methods=['GET', 'POST'])
def password_reset():
    """Password reset with security alerts"""
    if request.method == 'GET':
        return render_template('password_reset.html')
    
    username = request.form.get('username')
    email = request.form.get('email')
    ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    # Check rate limits
    rate_check = check_rate_limits(ip_address, username)
    if not rate_check['allowed']:
        log_security_event(username, 'reset_rate_limited', ip_address, user_agent, rate_check)
        flash('Too many reset attempts. Please try again later.', 'error')
        return redirect(url_for('password_reset'))
    
    # Always show success message for security (don't reveal if user exists)
    log_security_event(username, 'password_reset_request', ip_address, user_agent, {'email': email})
    
    # Send reset alert (stub)
    if username in DEMO_USERS:
        send_security_alert(username, 'reset_attempt', {
            'ip': ip_address,
            'email': email
        })
    
    flash('If the account exists, a password reset link has been sent to the associated email.', 'info')
    return redirect(url_for('login'))

@consumer_app.route('/admin/security')
def admin_security():
    """Admin security dashboard"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    # Load security data
    security_log = load_security_data('data/security_log.json', {'events': []})
    rate_limits = load_security_data('data/rate_limits.json', {'ip_attempts': {}, 'user_attempts': {}, 'locked_accounts': {}})
    user_settings = load_security_data('data/user_settings.json', {'users': {}})
    
    # Process filters
    filter_user = request.args.get('user', '')
    filter_type = request.args.get('type', '')
    filter_date = request.args.get('date', '')
    
    events = security_log['events']
    
    # Apply filters
    if filter_user:
        events = [e for e in events if filter_user.lower() in e['user'].lower()]
    if filter_type:
        events = [e for e in events if e['type'] == filter_type]
    if filter_date:
        events = [e for e in events if e['timestamp'].startswith(filter_date)]
    
    # Sort by most recent first
    events = sorted(events, key=lambda x: x['timestamp'], reverse=True)
    
    # Get locked accounts with time remaining
    locked_accounts = []
    for username, lock_until_str in rate_limits['locked_accounts'].items():
        lock_until = datetime.fromisoformat(lock_until_str)
        if datetime.now() < lock_until:
            time_remaining = lock_until - datetime.now()
            locked_accounts.append({
                'username': username,
                'lock_until': lock_until_str,
                'time_remaining_minutes': int(time_remaining.total_seconds() / 60)
            })
    
    # Get security stats
    recent_events = [e for e in security_log['events'] if 
                    datetime.now() - datetime.fromisoformat(e['timestamp']) < timedelta(hours=24)]
    
    stats = {
        'total_events_24h': len(recent_events),
        'failed_logins_24h': len([e for e in recent_events if e.get('type') == 'login_failed']),
        'mfa_challenges_24h': len([e for e in recent_events if e.get('type') == 'mfa_challenge_sent']),
        'rate_limited_24h': len([e for e in recent_events if 'rate_limited' in e.get('type', '')]),
        'total_locked_accounts': len(locked_accounts),
        'unique_users_24h': len(set(e.get('user', 'unknown') for e in recent_events if e.get('user') != 'unknown'))
    }
    
    # Get unique event types for filter dropdown
    event_types = list(set(e['type'] for e in security_log['events']))
    event_types.sort()
    
    return render_template('admin_security.html', 
                         events=events[:100],  # Show last 100 events
                         locked_accounts=locked_accounts,
                         stats=stats,
                         event_types=event_types,
                         filter_user=filter_user,
                         filter_type=filter_type,
                         filter_date=filter_date)

@consumer_app.route('/admin/security/unlock', methods=['POST'])
def admin_unlock_account():
    """Admin unlock account"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    username = request.form.get('username')
    ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
    user_agent = request.headers.get('User-Agent', 'unknown')
    admin_user = session.get('username', 'admin')
    
    if username:
        rate_limits = load_security_data('data/rate_limits.json', {'ip_attempts': {}, 'user_attempts': {}, 'locked_accounts': {}})
        
        if username in rate_limits['locked_accounts']:
            del rate_limits['locked_accounts'][username]
            save_security_data('data/rate_limits.json', rate_limits)
            
            # Log admin action
            log_security_event(username, 'admin_account_unlocked', ip_address, user_agent, {
                'admin_user': admin_user
            })
            
            flash(f'Account {username} has been unlocked.', 'success')
        else:
            flash(f'Account {username} was not locked.', 'info')
    
    return redirect(url_for('admin_security'))

@consumer_app.route('/admin/security/lock', methods=['POST'])
def admin_lock_account():
    """Admin lock account"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    username = request.form.get('username')
    duration_hours = int(request.form.get('duration', 1))
    ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
    user_agent = request.headers.get('User-Agent', 'unknown')
    admin_user = session.get('username', 'admin')
    
    if username:
        rate_limits = load_security_data('data/rate_limits.json', {'ip_attempts': {}, 'user_attempts': {}, 'locked_accounts': {}})
        
        lock_until = datetime.now() + timedelta(hours=duration_hours)
        rate_limits['locked_accounts'][username] = lock_until.isoformat()
        save_security_data('data/rate_limits.json', rate_limits)
        
        # Log admin action
        log_security_event(username, 'admin_account_locked', ip_address, user_agent, {
            'admin_user': admin_user,
            'duration_hours': duration_hours,
            'lock_until': lock_until.isoformat()
        })
        
        # Send security alert to user
        send_security_alert(username, 'account_locked', {
            'reason': 'admin_action',
            'lock_until': lock_until.isoformat()
        })
        
        flash(f'Account {username} has been locked for {duration_hours} hours.', 'success')
    
    return redirect(url_for('admin_security'))

@consumer_app.route('/signup', methods=['POST'])
def signup_post():
    """Process signup form with email verification"""
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    role = request.form.get('role')
    
    # In production, this would:
    # 1. Hash password
    # 2. Store in database
    # 3. Send verification email
    # 4. Generate activation token
    
    # For demo, simulate email verification
    verification_code = "DEMO123"
    logging.info(f"EMAIL VERIFICATION STUB - To: {email}, Activation code: {verification_code}")
    
    session['pending_signup'] = {
        'name': name,
        'email': email,
        'role': role,
        'phone': phone,
        'verification_code': verification_code
    }
    
    flash(f'Account created! Check your email ({email}) for verification code: {verification_code}', 'success')
    return redirect(url_for('home'))

@consumer_app.route('/referrals')
def consumer_referrals():
    """Referral program page"""
    return render_template('consumer_referrals.html')

@consumer_app.route('/requests')
def consumer_requests():
    """Unified request/quote management page with historical data"""
    return render_template('consumer_requests.html')

@consumer_app.route('/portal-views')
def portal_views():
    """Portal dashboard views without login requirement"""
    return render_template('portal_views.html')

@consumer_app.route('/admin/delisted')
def admin_delisted():
    """Admin page for delisted affiliate management"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    delisted_data = load_json_data('data/delisted_affiliates.json', {'delisted': [], 'meta': {}})
    active_affiliates = get_active_affiliates()
    return render_template('admin_delisted.html', 
                         delisted_data=delisted_data,
                         active_affiliates=active_affiliates)

@consumer_app.route('/admin/relist-affiliate', methods=['POST'])
def admin_relist_affiliate():
    """Phase 7.A: Relist affiliate with fee validation"""
    try:
        affiliate_id = request.form.get('affiliate_id')
        
        if not affiliate_id:
            flash('Missing affiliate ID', 'error')
            return redirect(url_for('admin_delisted'))
        
        # Load delisted data
        delisted_data = load_json_data('data/delisted_affiliates.json', {'delisted': [], 'meta': {}})
        
        # Check if affiliate exists in delisted records
        affiliate_found = False
        for affiliate in delisted_data.get('delisted', []):
            if affiliate.get('affiliate_id') == affiliate_id:
                affiliate_found = True
                # Check if lifetime banned (2+ strikes)
                if affiliate.get('strikes', 0) >= 2:
                    flash('Cannot relist lifetime banned affiliate (2+ strikes)', 'error')
                    return redirect(url_for('admin_delisted'))
                
                # Mark as relisted
                affiliate['relisted_at'] = datetime.now().isoformat()
                affiliate['relist_fee_paid'] = True
                affiliate['is_delisted'] = False
                break
        
        if not affiliate_found:
            flash('Affiliate not found in delisted records', 'error')
            return redirect(url_for('admin_delisted'))
        
        # Save updated data
        save_json_data('data/delisted_affiliates.json', delisted_data)
        
        flash(f'Affiliate {affiliate_id} has been successfully relisted', 'success')
        return redirect(url_for('admin_delisted'))
        
    except Exception as e:
        logging.error(f"Error relisting affiliate: {e}")
        flash('Error relisting affiliate', 'error')
        return redirect(url_for('admin_delisted'))

@consumer_app.route('/admin/announcements')
def admin_announcements():
    """Admin announcements management with full CRUD"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    if not DB_AVAILABLE:
        # Fallback to JSON for backwards compatibility
        announcements_data = load_json_data('data/announcements.json', {'announcements': []})
        return render_template('admin_announcements.html', announcements_data=announcements_data)
    
    try:
        with consumer_app.app_context():
            # Get all announcements, split by active/inactive
            active_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
            inactive_announcements = Announcement.query.filter_by(is_active=False).order_by(Announcement.created_at.desc()).all()
            
            return render_template('admin_announcements_crud.html', 
                                 active_announcements=active_announcements,
                                 inactive_announcements=inactive_announcements)
    except Exception as e:
        logging.error(f"Error loading announcements: {e}")
        flash(f'Error loading announcements: {str(e)}', 'error')
        # Fallback to JSON
        announcements_data = load_json_data('data/announcements.json', {'announcements': []})
        return render_template('admin_announcements.html', announcements_data=announcements_data)

@consumer_app.route('/admin/announcements/create', methods=['POST'])
def admin_announcements_create():
    """Create new announcement - CRUD CREATE"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    try:
        announcements_data = load_json_data('data/announcements.json', {'announcements': []})
        
        # Schema normalization on save
        new_announcement = {
            'id': str(uuid.uuid4()),  # UUID instead of incremental ID
            'message': request.form.get('message', '').strip(),
            'style': request.form.get('style', 'info'),  # info|warn|success
            'is_active': bool(request.form.get('is_active', 'true').lower() in ('true', '1', 'on')),
            'start_at': request.form.get('start_at'),    # ISO 8601 format
            'end_at': request.form.get('end_at'),        # ISO 8601 format
            'countdown_target': request.form.get('countdown_target', '').strip() or None,
            'countdown_target_tz': 'America/New_York',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        announcements_data['announcements'].append(new_announcement)
        
        if DB_AVAILABLE:
            # Save to database
            try:
                with consumer_app.app_context():
                    announcement = Announcement(
                        message=new_announcement['message'],
                        style=new_announcement['style'],
                        is_active=new_announcement['is_active'],
                        start_at=datetime.fromisoformat(new_announcement['start_at']) if new_announcement['start_at'] else None,
                        end_at=datetime.fromisoformat(new_announcement['end_at']) if new_announcement['end_at'] else None,
                        countdown_target=new_announcement['countdown_target']
                    )
                    db.session.add(announcement)
                    db.session.commit()
            except Exception as e:
                logging.error(f"Database save failed, falling back to JSON: {e}")
                # Fallback to JSON
                save_json_data('data/announcements.json', announcements_data)
        else:
            # Save to JSON
            save_json_data('data/announcements.json', announcements_data)
        
        flash('Announcement created successfully.', 'success')
        return redirect(url_for('admin_announcements'))
        
    except Exception as e:
        logging.error(f"Announcement creation error: {e}")
        flash('Error creating announcement.', 'error')
        return redirect(url_for('admin_announcements'))

@consumer_app.route('/admin/announcements/<announcement_id>', methods=['POST'])
def admin_announcements_update(announcement_id):
    """Update existing announcement - CRUD UPDATE"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    try:
        announcements_data = load_json_data('data/announcements.json', {'announcements': []})
        
        for announcement in announcements_data['announcements']:
            announcement_real_id = announcement.get('id', 'unknown')
            if announcement_real_id == announcement_id:
                # Update fields
                announcement['message'] = request.form.get('message', announcement.get('message', '')).strip()
                announcement['style'] = request.form.get('style', announcement.get('style', 'info'))
                announcement['is_active'] = bool(request.form.get('is_active', 'false').lower() in ('true', '1', 'on'))
                announcement['start_at'] = request.form.get('start_at', announcement.get('start_at'))
                announcement['end_at'] = request.form.get('end_at', announcement.get('end_at'))
                announcement['countdown_target'] = request.form.get('countdown_target', '').strip() or None
                announcement['updated_at'] = datetime.now().isoformat()
                
                save_json_data('data/announcements.json', announcements_data)
                status = 'activated' if announcement['is_active'] else 'deactivated'
                flash(f'Announcement updated and {status} successfully.', 'success')
                return redirect(url_for('admin_announcements'))
        
        flash('Announcement not found.', 'error')
        return redirect(url_for('admin_announcements'))
        
    except Exception as e:
        logging.error(f"Announcement update error: {e}")
        flash('Error updating announcement.', 'error')
        return redirect(url_for('admin_announcements'))

@consumer_app.route('/admin/announcements/<announcement_id>/delete', methods=['POST'])
def admin_announcements_delete(announcement_id):
    """Delete announcement permanently - CRUD DELETE"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    try:
        announcements_data = load_json_data('data/announcements.json', {'announcements': []})
        original_count = len(announcements_data['announcements'])
        
        announcements_data['announcements'] = [
            ann for ann in announcements_data['announcements'] 
            if ann['id'] != announcement_id
        ]
        
        if len(announcements_data['announcements']) < original_count:
            save_json_data('data/announcements.json', announcements_data)
            flash('Announcement deleted successfully.', 'success')
        else:
            flash('Announcement not found.', 'error')
            
        return redirect(url_for('admin_announcements'))
        
    except Exception as e:
        logging.error(f"Announcement deletion error: {e}")
        flash('Error deleting announcement.', 'error')
        return redirect(url_for('admin_announcements'))

# Legacy route redirects - Phase 7.M
@consumer_app.route('/request')
@consumer_app.route('/transport_request')
@consumer_app.route('/consumer_request')
@consumer_app.route('/request_transport')
def legacy_request_redirects():
    """301 Redirect legacy request routes to canonical /intake"""
    return redirect(url_for('consumer_intake'), code=301)

@consumer_app.route('/admin/delist_affiliate', methods=['POST'])
def admin_delist_affiliate():
    """Delist affiliate with strike tracking"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    try:
        affiliate_id = request.form.get('affiliate_id')
        reason = request.form.get('reason')
        
        delisted_data = load_json_data('data/delisted_affiliates.json', {'delisted': []})
        
        # Check current strikes
        current_strikes = get_affiliate_strikes(affiliate_id)
        new_strikes = current_strikes + 1
        
        delist_entry = {
            'id': f"delist_{len(delisted_data['delisted']) + 1:03d}",
            'affiliate_id': affiliate_id,
            'reason': reason,
            'strikes': new_strikes,
            'delisted_at': datetime.now().isoformat(),
            'delisted_by': session.get('username', 'admin'),
            'lifetime_ban': new_strikes >= 2
        }
        
        delisted_data['delisted'].append(delist_entry)
        save_json_data('data/delisted_affiliates.json', delisted_data)
        
        flash(f'Affiliate delisted successfully. Strike count: {new_strikes}/2', 'warning')
        return redirect(url_for('admin_delisted'))
        
    except Exception as e:
        logging.error(f"Delist affiliate error: {e}")
        flash('Error delisting affiliate.', 'error')
        return redirect(url_for('admin_delisted'))

@consumer_app.route('/admin-dashboard')
def admin_dashboard():
    """Enhanced admin dashboard with comprehensive controls"""
    if session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    # Admin dashboard data with proper currency formatting
    admin_data = {
        'total_revenue': format_currency(847500),
        'monthly_revenue': format_currency(127000),
        'total_users': 1247,
        'new_users_week': 89,
        'flight_requests': 342,
        'completed_flights': 156,
        'active_quotes': 67,
        'paid_quotes_today': 23,
        'providers': [
            {'name': 'AeroMed Services', 'flights': 45, 'revenue': format_currency(234500)},
            {'name': 'SkyLife Medical', 'flights': 38, 'revenue': format_currency(198750)},
            {'name': 'CriticalCare Air', 'flights': 42, 'revenue': format_currency(215600)},
            {'name': 'MedTransport Plus', 'flights': 31, 'revenue': format_currency(167200)}
        ]
    }
    
    config = load_config()
    return render_template('admin_dashboard_enhanced.html', admin_data=admin_data, config=config)

# Phase 7.C: Enhanced Draft Management Routes
@consumer_app.route('/api/save-draft', methods=['POST'])
def api_save_draft():
    """Phase 7.C: Save intake draft with noise control"""
    try:
        data = request.get_json()
        
        # Generate or use existing draft ID
        if 'draft_id' not in session:
            session['draft_id'] = str(uuid.uuid4())
        
        draft_id = session['draft_id']
        
        # Check if this is the first save for this session
        first_save_key = f'first_draft_save_{draft_id}'
        is_first_save = not session.get(first_save_key, False)
        
        draft_data = {
            'id': draft_id,
            'form_data': data,
            'saved_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        # Save draft
        session['current_draft'] = draft_data
        
        if is_first_save:
            session[first_save_key] = True
            return jsonify({
                'success': True,
                'draft_id': draft_id,
                'message': 'Draft saved',
                'show_toast': True
            })
        else:
            # Quiet save for auto-saves with inline indicator
            current_time = datetime.now().strftime('%H:%M:%S')
            return jsonify({
                'success': True,
                'draft_id': draft_id,
                'message': f'Saved • {current_time}',
                'show_toast': False,
                'show_inline': True
            })
        
    except Exception as e:
        logging.error(f"Draft save error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@consumer_app.route('/api/load-draft/<draft_id>')
def api_load_draft(draft_id):
    """Load draft endpoint"""
    try:
        draft = load_draft(draft_id)
        if draft:
            return jsonify({'success': True, 'draft': draft})
        return jsonify({'success': False, 'error': 'Draft not found'}), 404
    except Exception as e:
        logging.error(f"Draft load error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@consumer_app.route('/api/delete-draft/<draft_id>', methods=['DELETE'])
def api_delete_draft(draft_id):
    """Delete draft endpoint (only for draft status)"""
    try:
        success = delete_draft(draft_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Cannot delete active request'}), 400
    except Exception as e:
        logging.error(f"Draft delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Phase 5.A: Quote Selection and Opt-in API Endpoints
@consumer_app.route('/api/select-quote', methods=['POST'])
def api_select_quote():
    """Phase 5.A: Select quote and reveal affiliate name"""
    try:
        data = request.get_json()
        affiliate_id = data.get('affiliate_id')
        affiliate_name = data.get('affiliate_name')
        
        # Lock the quote selection to prevent further modifications
        session['quote_selection_locked'] = True
        session['selected_affiliate_id'] = affiliate_id
        session['selected_affiliate_name'] = affiliate_name
        session['selection_timestamp'] = datetime.now().isoformat()
        session.modified = True
        
        logging.info(f"Quote selected: {affiliate_name} ({affiliate_id})")
        return jsonify({
            'success': True, 
            'message': f'Selected {affiliate_name}. Request is now locked.',
            'revealed_name': affiliate_name
        })
        
    except Exception as e:
        logging.error(f"Quote selection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@consumer_app.route('/api/opt-in-assistance', methods=['POST'])
def api_opt_in_assistance():
    """Phase 5.A: Handle compassionate opt-in for third-party assistance"""
    try:
        data = request.get_json()
        opt_in = data.get('opt_in', False)
        
        # Store opt-in preference
        session['third_party_assistance_opt_in'] = opt_in
        session['opt_in_timestamp'] = datetime.now().isoformat()
        session.modified = True
        
        if opt_in:
            logging.info("User opted in for third-party assistance contact")
            # In production, this would trigger affiliate contact workflow
            message = "Thank you. We'll have an affiliate contact you with additional options."
        else:
            logging.info("User declined third-party assistance")
            message = "Thank you for your preference. We'll continue monitoring for direct quotes."
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        logging.error(f"Opt-in assistance error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Phase 6.A: Commission Ledger Functions
def load_json_data(file_path, default_data=None):
    """Safely load JSON data with fallback"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            if default_data:
                save_json_data(file_path, default_data)
                return default_data
            return {}
    except Exception as e:
        logging.error(f"Error loading {file_path}: {e}")
        return default_data or {}

def save_json_data(file_path, data):
    """Safely save JSON data"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving {file_path}: {e}")
        return False

def get_invoice_week(date_obj):
    """Get invoice week in format YYYY-Www (Sunday-Saturday)"""
    # Find the Sunday of the week containing the date
    days_since_sunday = date_obj.weekday() % 7  # Sunday = 0, Monday = 1, etc.
    sunday = date_obj - timedelta(days=days_since_sunday)
    year, week, _ = sunday.isocalendar()
    return f"{year}-W{week:02d}"

def get_affiliate_recoup_amount(affiliate_id):
    """Get current recoup amount for affiliate"""
    recoup_data = load_json_data('data/affiliates_recoup.json', {})
    return recoup_data.get(affiliate_id, {}).get('recouped_amount_usd', 0)

def update_affiliate_recoup_amount(affiliate_id, new_amount):
    """Update affiliate's recoup amount"""
    recoup_data = load_json_data('data/affiliates_recoup.json', {})
    recoup_data[affiliate_id] = {
        'recouped_amount_usd': new_amount,
        'updated_at': datetime.now().isoformat()
    }
    return save_json_data('data/affiliates_recoup.json', recoup_data)

def record_commission_entry(booking_id, affiliate_id, base_amount_usd, is_dummy=False):
    """Record commission entry when booking completes"""
    try:
        if is_dummy:
            logging.info(f"Skipping commission for dummy booking {booking_id}")
            return True
            
        # Get current recoup amount
        current_recoup = get_affiliate_recoup_amount(affiliate_id)
        
        # Determine commission rates
        gross_percent = COMMISSION_CONFIG['tier_2_rate']  # Always 5% gross
        effective_percent = COMMISSION_CONFIG['base_rate'] if current_recoup < COMMISSION_CONFIG['recoup_threshold_usd'] else COMMISSION_CONFIG['tier_2_rate']
        
        # Calculate commission
        commission_amount = round(base_amount_usd * effective_percent)
        
        # Calculate recoup if under threshold
        recoup_applied = 0
        if effective_percent == COMMISSION_CONFIG['base_rate']:
            recoup_applied = round(base_amount_usd * COMMISSION_CONFIG['recoup_rate'])
            new_recoup = current_recoup + recoup_applied
            update_affiliate_recoup_amount(affiliate_id, new_recoup)
        else:
            new_recoup = current_recoup
        
        # Create ledger entry
        entry = {
            'id': str(uuid.uuid4()),
            'booking_id': str(booking_id),
            'affiliate_id': affiliate_id,
            'is_dummy': is_dummy,
            'base_amount_usd': base_amount_usd,
            'gross_percent': gross_percent,
            'effective_percent': effective_percent,
            'commission_amount_usd': commission_amount,
            'recoup_applied_usd': recoup_applied,
            'affiliate_recoup_total_usd': new_recoup,
            'completed_at': datetime.now().isoformat(),
            'invoice_week': get_invoice_week(datetime.now())
        }
        
        # Add to ledger
        ledger_data = load_json_data('data/ledger.json', {'entries': [], 'meta': {'version': 1}})
        ledger_data['entries'].append(entry)
        ledger_data['meta']['last_updated'] = datetime.now().isoformat()
        
        if save_json_data('data/ledger.json', ledger_data):
            rate_display = f"{int(effective_percent * 100)}%"
            recoup_display = f"${new_recoup:,}/{COMMISSION_CONFIG['recoup_threshold_usd']:,}"
            logging.info(f"Commission recorded ({rate_display}, recoup {recoup_display})")
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Error recording commission: {e}")
        return False

# Phase 7.A: Operational Control Functions
def record_audit_event(event_type, **kwargs):
    """Record audit trail event"""
    try:
        audit_data = load_json_data('data/audit_trail.json', {'events': [], 'meta': {}})
        
        event = {
            'id': f"audit_{len(audit_data['events']) + 1:03d}",
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        audit_data['events'].append(event)
        save_json_data('data/audit_trail.json', audit_data)
        logging.info(f"Audit event recorded: {event_type}")
        return True
    except Exception as e:
        logging.error(f"Error recording audit event: {e}")
        return False

def get_active_affiliates():
    """Get list of active (non-delisted) affiliates"""
    try:
        delisted_data = load_json_data('data/delisted_affiliates.json', {'delisted': []})
        delisted_ids = [item['affiliate_id'] for item in delisted_data['delisted'] if not item.get('relisted_at')]
        
        # Return mock affiliates excluding delisted ones
        active = [
            {'id': 'affiliate_1', 'name': 'AirMed Response'},
            {'id': 'affiliate_2', 'name': 'LifeFlight Services'},
            {'id': 'affiliate_3', 'name': 'MedAir Transport'}
        ]
        
        return [aff for aff in active if aff['id'] not in delisted_ids]
    except Exception as e:
        logging.error(f"Error getting active affiliates: {e}")
        return []

def get_affiliate_strikes(affiliate_id):
    """Get current strike count for affiliate"""
    try:
        delisted_data = load_json_data('data/delisted_affiliates.json', {'delisted': []})
        for item in delisted_data['delisted']:
            if item['affiliate_id'] == affiliate_id:
                return item.get('strikes', 0)
        return 0
    except Exception as e:
        logging.error(f"Error getting strikes: {e}")
        return 0

def get_training_limit_status(affiliate_id):
    """Get training dummy case usage for affiliate"""
    try:
        training_data = load_json_data('data/training_limits.json', {'affiliate_limits': {}})
        limit_info = training_data['affiliate_limits'].get(affiliate_id, {
            'dummy_cases_used': 0,
            'dummy_cases_limit': OPERATIONAL_CONFIG['training_limits']['dummy_cases_per_affiliate']
        })
        
        remaining = limit_info['dummy_cases_limit'] - limit_info['dummy_cases_used']
        return {
            'used': limit_info['dummy_cases_used'],
            'limit': limit_info['dummy_cases_limit'],
            'remaining': max(0, remaining),
            'at_limit': remaining <= 0
        }
    except Exception as e:
        logging.error(f"Error getting training limits: {e}")
        return {'used': 0, 'limit': 50, 'remaining': 50, 'at_limit': False}

def get_active_announcements():
    """Get active announcements with normalized schema and EST timezone support"""
    try:
        # Single source of truth: /data/announcements.json
        announcements_data = load_json_data('data/announcements.json', {'announcements': []})
        now = datetime.now(EST)
        
        active_announcements = []
        for announcement in announcements_data.get('announcements', []):
            # Schema normalization: handle both is_active and active fields
            is_active = announcement.get('is_active', announcement.get('active', False))
            
            # Ensure boolean (not string)
            if isinstance(is_active, str):
                is_active = is_active.lower() in ('true', '1', 'yes')
            
            if not is_active:
                continue
                
            try:
                # Parse dates with EST timezone
                start_str = announcement.get('start_at', '2025-01-01T00:00:00')
                end_str = announcement.get('end_at', '2025-12-31T23:59:59')
                
                # Clean ISO strings and parse as naive datetime
                start_naive = datetime.fromisoformat(start_str.replace('Z', '').split('.')[0])
                end_naive = datetime.fromisoformat(end_str.replace('Z', '').split('.')[0])
                
                # Make timezone-aware with EST
                start_at = start_naive.replace(tzinfo=EST)
                end_at = end_naive.replace(tzinfo=EST)
                
                # Active filter: now_est ∈ [start_at_est, end_at_est] && is_active == True
                if start_at <= now <= end_at:
                    # Calculate countdown if target is set
                    countdown_target = announcement.get('countdown_target') or ''
                    if countdown_target and str(countdown_target).strip():
                        try:
                            target_naive = datetime.fromisoformat(str(countdown_target).replace('Z', '').split('.')[0])
                            target_dt = target_naive.replace(tzinfo=EST)
                            
                            time_diff = target_dt - now
                            
                            if time_diff.total_seconds() > 0:
                                days = time_diff.days
                                hours, remainder = divmod(time_diff.seconds, 3600)
                                minutes, _ = divmod(remainder, 60)
                                announcement['countdown_display'] = f"{days:02d}:{hours:02d}:{minutes:02d}"
                                announcement['countdown_expired'] = False
                            else:
                                announcement['countdown_display'] = "We're live!"
                                announcement['countdown_expired'] = True
                        except:
                            # Invalid countdown target, skip countdown
                            pass
                    
                    # Normalize style field
                    announcement['style'] = announcement.get('style', 'info')
                    active_announcements.append(announcement)
                    
            except Exception as date_error:
                logging.error(f"Error parsing announcement dates for {announcement.get('id', 'unknown')}: {date_error}")
                continue
        
        return active_announcements
        
    except Exception as e:
        logging.error(f"Error loading announcements from /data/announcements.json: {e}")
        return []

# Context processor to inject active announcements into all templates
@consumer_app.context_processor
def inject_announcements():
    """Inject active announcements into all template contexts"""
    return {'active_announcements': get_active_announcements()}

@consumer_app.route('/api/cancel-request/<request_id>', methods=['POST'])
def api_cancel_request(request_id):
    """Phase 7.A: Cancel active request with reason and audit trail"""
    try:
        data = request.get_json() or {}
        cancel_reason = data.get('cancel_reason', 'User requested cancellation')
        
        # Check if request has quotes (cannot delete, only cancel)
        has_quotes = True  # In production, check actual quote status
        
        if has_quotes:
            # Record audit event
            record_audit_event(
                'cancel_request',
                request_id=request_id,
                user_id=session.get('contact_name', 'unknown'),
                cancel_reason=cancel_reason,
                metadata={'quotes_existed': True}
            )
            
            success = cancel_active_request(request_id)
            return jsonify({
                'success': success,
                'message': 'Request cancelled (quotes notified)',
                'action': 'cancelled'
            })
        else:
            # Can delete if no quotes
            record_audit_event(
                'delete_request',
                request_id=request_id,
                user_id=session.get('contact_name', 'unknown'),
                metadata={'quotes_existed': False}
            )
            
            return jsonify({
                'success': True,
                'message': 'Request deleted',
                'action': 'deleted'
            })
            
    except Exception as e:
        logging.error(f"Request cancel error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@consumer_app.route('/toggle-training-mode', methods=['POST'])
def toggle_training_mode():
    """Toggle training/dummy mode for organization"""
    if session.get('user_role') not in ['admin', 'hospital']:
        flash('Admin access required.', 'error')
        return redirect(url_for('home'))
    
    session['training_mode'] = not session.get('training_mode', False)
    mode_status = "enabled" if session['training_mode'] else "disabled"
    flash(f'Training mode {mode_status}. All data will be clearly labeled as DUMMY DATA.', 'info')
    return redirect(request.referrer or url_for('home'))

@consumer_app.route('/confirm')
def confirm_account():
    """Account confirmation page with email verification"""
    pending = session.get('pending_signup', {})
    if not pending:
        flash('No pending account found. Your quotes will be available within 24-48 hours after account creation.', 'warning')
        return redirect(url_for('home'))
    
    return render_template('consumer_confirm.html', pending_signup=pending)

@consumer_app.route('/booking')
def consumer_booking():
    """Booking confirmation page"""
    quote_id = request.args.get('quote')
    provider = request.args.get('provider', 'Selected Provider')
    
    # In production, this would process the actual booking
    booking_ref = f"BK-{random.randint(100000, 999999)}"
    
    return render_template('consumer_booking.html', 
                         quote_id=quote_id,
                         provider=provider,
                         booking_ref=booking_ref)

@consumer_app.route('/intake')
def consumer_intake():
    """Enhanced intake form - last-night pancake template"""
    transport_type = request.args.get('type', 'critical')
    return render_template('consumer_intake_updated.html', 
                         transport_type=transport_type,
                         equipment_pricing=EQUIPMENT_PRICING,
                         datetime=datetime)



@consumer_app.route('/intake', methods=['POST'])
def consumer_intake_post():
    """Process intake form with equipment pricing calculations"""
    session['patient_data'] = {
        'transport_type': request.form.get('transport_type'),
        'patient_name': request.form.get('patient_name'),
        'patient_age': request.form.get('patient_age'),
        'origin': request.form.get('origin'),
        'destination': request.form.get('destination'),
        'severity': int(request.form.get('severity', 1)),
        'equipment': request.form.getlist('equipment'),
        'same_day': 'same_day' in request.form,
        'date_time': request.form.get('date_time'),
        'additional_notes': request.form.get('additional_notes'),
        'passport_confirmed': 'passport_confirmed' in request.form
    }
    
    equipment_cost = 0
    for item in session['patient_data']['equipment']:
        if item in EQUIPMENT_PRICING:
            equipment_cost += EQUIPMENT_PRICING[item]
    
    if session['patient_data']['same_day']:
        equipment_cost *= 1.2
    
    session['equipment_cost'] = equipment_cost
    return redirect(url_for('consumer_quotes'))

# Legacy route redirects (301 permanent redirects)
@consumer_app.route('/request')
@consumer_app.route('/home')
@consumer_app.route('/request_transport')
@consumer_app.route('/transport_request')
def legacy_redirects():
    """301 redirects from legacy routes to intake"""
    return redirect(url_for('consumer_intake'), code=301)

# System utilities and health checks
def load_config():
    """Load system configuration"""
    try:
        with open('data/config.json', 'r') as f:
            return json.load(f)
    except:
        return {"env": "staging", "flags": {"training_mode": False, "email_enabled": False, "sms_enabled": False}}

def log_error(error_type, message, details=None):
    """Log errors to error_log.json"""
    try:
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": str(message),
            "details": details or {}
        }
        
        try:
            with open('data/error_log.json', 'r') as f:
                error_log = json.load(f)
        except:
            error_log = {"errors": []}
        
        error_log["errors"].append(error_entry)
        
        # Keep only last 1000 errors
        if len(error_log["errors"]) > 1000:
            error_log["errors"] = error_log["errors"][-1000:]
        
        with open('data/error_log.json', 'w') as f:
            json.dump(error_log, f, indent=2)
            
        logging.error(f"Error logged: {error_type} - {message}")
    except Exception as e:
        logging.error(f"Failed to log error: {e}")

def run_backup():
    """Create backup of critical data files"""
    try:
        backup_date = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        backup_dir = f'data/backups/{backup_date}'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup JSON files
        for json_file in ['security_log.json', 'rate_limits.json', 'user_settings.json', 'config.json', 'error_log.json', 'manifest.json']:
            try:
                if os.path.exists(f'data/{json_file}'):
                    shutil.copy2(f'data/{json_file}', f'{backup_dir}/{json_file}')
            except Exception as e:
                logging.error(f"Failed to backup {json_file}: {e}")
        
        # Backup invoices directory if it exists
        if os.path.exists('data/invoices'):
            shutil.copytree('data/invoices', f'{backup_dir}/invoices', dirs_exist_ok=True)
        
        backup_info = {
            "timestamp": datetime.now().isoformat(),
            "backup_dir": backup_dir,
            "files_backed_up": os.listdir(backup_dir) if os.path.exists(backup_dir) else []
        }
        
        with open(f'{backup_dir}/backup_info.json', 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        return {"success": True, "backup_dir": backup_dir, "files": backup_info["files_backed_up"]}
    except Exception as e:
        log_error("backup_failed", str(e))
        return {"success": False, "error": str(e)}

def reset_demo_data():
    """Reset demo/training data while preserving production data"""
    try:
        reset_actions = []
        
        # Clear session data
        session.clear()
        reset_actions.append("Cleared session data")
        
        # Reset training flags in config
        config = load_config()
        config["flags"]["training_mode"] = False
        with open('data/config.json', 'w') as f:
            json.dump(config, f, indent=2)
        reset_actions.append("Reset training mode flag")
        
        # Log audit entry
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "demo_reset",
            "user": session.get('username', 'system'),
            "actions": reset_actions
        }
        
        try:
            with open('data/security_log.json', 'r') as f:
                security_log = json.load(f)
        except:
            security_log = {"events": []}
        
        security_log["events"].append(audit_entry)
        
        with open('data/security_log.json', 'w') as f:
            json.dump(security_log, f, indent=2)
        
        return {"success": True, "actions": reset_actions}
    except Exception as e:
        log_error("demo_reset_failed", str(e))
        return {"success": False, "error": str(e)}

@consumer_app.route('/healthz')
def healthcheck():
    """Health check endpoint"""
    try:
        config = load_config()
        return jsonify({
            "ok": True,
            "ts": datetime.now().isoformat(),
            "env": config.get("env", "unknown"),
            "version": "1.0.0"
        })
    except Exception as e:
        log_error("healthcheck_failed", str(e))
        return jsonify({"ok": False, "error": str(e)}), 500

@consumer_app.route('/test-error')
def test_error():
    """Test route to generate a harmless error for testing error logging"""
    log_error("test_error_triggered", "This is a test error for Phase 9.B verification")
    raise Exception("Test error for Phase 9.B - error logging verification")

@consumer_app.route('/admin/backup', methods=['POST'])
def admin_backup():
    """Admin endpoint to trigger backup"""
    if session.get('user_role') != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('login'))
    
    result = run_backup()
    if result["success"]:
        flash(f'Backup completed: {result["backup_dir"]}', 'success')
    else:
        flash(f'Backup failed: {result["error"]}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@consumer_app.route('/admin/reset-demo', methods=['POST'])
def admin_reset_demo():
    """Admin endpoint to reset demo/training data"""
    if session.get('user_role') != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('login'))
    
    result = reset_demo_data()
    if result["success"]:
        flash(f'Demo reset completed: {", ".join(result["actions"])}', 'success')
    else:
        flash(f'Demo reset failed: {result["error"]}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@consumer_app.route('/quotes')
def consumer_quotes():
    """Phase 5.A Enhanced quotes with fairness, timing windows, and compact UX"""
    if 'patient_data' not in session:
        flash('Please complete the intake form first.', 'warning')
        return redirect(url_for('consumer_intake'))
    
    if 'quote_id' not in session:
        generate_quote_session()
    
    patient_data = session['patient_data']
    is_training_mode = session.get('training_mode', False)
    
    # Phase 5.A: Fan-out timing and response windows
    quote_request_time = session.get('quote_request_time')
    if not quote_request_time:
        session['quote_request_time'] = datetime.now().isoformat()
        quote_request_time = session['quote_request_time']
    
    # Calculate elapsed time for timer display
    request_start = datetime.fromisoformat(quote_request_time)
    elapsed_minutes = int((datetime.now() - request_start).total_seconds() / 60)
    
    # Get affiliate quotes using fairness system
    quotes = get_affiliate_quotes(
        patient_data['origin'],
        patient_data['destination'],
        patient_data['equipment'],
        patient_data['transport_type'],
        is_training_mode
    )
    
    # Phase 5.A: Compact display logic (default 5, expand by 5)
    visible_count = int(request.args.get('show', QUOTE_CONFIG['default_visible_quotes']))
    visible_quotes = quotes[:visible_count]
    remaining_quotes = max(0, len(quotes) - visible_count)
    can_show_more = remaining_quotes > 0
    
    # Phase 5.A: Zero-result compassionate state
    show_compassionate_message = len(quotes) == 0 and elapsed_minutes >= 5
    
    # Phase 5.A: Selection & modify rules
    quote_selection_locked = session.get('quote_selection_locked', False)
    
    if not quotes:
        return render_template('consumer_no_availability.html', 
                             patient_data=patient_data,
                             search_params={
                                 'origin': patient_data['origin'],
                                 'destination': patient_data['destination']
                             },
                             show_compassionate_message=show_compassionate_message,
                             elapsed_minutes=elapsed_minutes)
    
    user_subscription = session.get('subscription_status', None)
    show_names = user_subscription in ['monthly', 'yearly'] or session.get('user_role') in ['mvp', 'hospital'] or quote_selection_locked
    
    quote_expiry = datetime.fromisoformat(session['quote_expiry'])
    time_remaining = quote_expiry - datetime.now()
    hours_remaining = max(0, int(time_remaining.total_seconds() // 3600))
    
    # Enhanced data for professional display with Phase 5.A features
    for i, quote in enumerate(visible_quotes):
        quote['early_adopter'] = quote.get('spotlight_badge', False)
        quote['rating'] = 5 if quote.get('response_rate', 0) > 90 else 4
        quote['flight_time'] = f"{quote.get('eta_hours', 3)} hours"
        quote['aircraft_type'] = random.choice(['Medical Helicopter', 'Fixed Wing Aircraft', 'Medical Jet'])
        quote['crew_size'] = '2 Medical Professionals'
        quote['certifications'] = 'FAA Part 135 + Medical'
        quote['name'] = quote['affiliate_name'] if show_names else quote.get('masked_name', f"Affiliate {chr(65 + i)}")
        quote['base_price'] = quote['total_cost'] - quote.get('equipment_cost', 0)
    
    # Phase 5.A specific data
    quote_timing = {
        'elapsed_minutes': elapsed_minutes,
        'response_window_min': QUOTE_CONFIG['response_window_min'],
        'response_window_max': QUOTE_CONFIG['response_window_max'],
        'saturated_delay_hours': QUOTE_CONFIG['saturated_market_delay'] // 60
    }
    
    return render_template('consumer_quotes_phase5a.html',
                         quotes=visible_quotes,
                         total_quotes=len(quotes),
                         visible_count=visible_count,
                         remaining_quotes=remaining_quotes,
                         can_show_more=can_show_more,
                         show_compassionate_message=show_compassionate_message,
                         quote_timing=quote_timing,
                         quote_selection_locked=quote_selection_locked,
                         patient_data=patient_data,
                         show_names=show_names,
                         quote_expiry=session.get('quote_expiry'),
                         hours_remaining=hours_remaining,
                         urgency_deadline=quote_expiry,
                         slots_remaining=session.get('slots_remaining', 2),
                         subscription_pricing=SUBSCRIPTION_PRICING,
                         medfly_fee=MEDFLY_CONFIG['non_refundable_fee'],
                         is_training_mode=is_training_mode,
                         training_label=TRAINING_CONFIG['dummy_label'])

@consumer_app.route('/subscribe/<plan>')
def subscribe(plan):
    """Subscription signup page"""
    if plan not in ['monthly', 'yearly']:
        flash('Invalid subscription plan.', 'error')
        return redirect(url_for('consumer_quotes'))
    
    pricing = SUBSCRIPTION_PRICING[plan]
    return render_template('consumer_subscribe.html', plan=plan, pricing=pricing)

@consumer_app.route('/subscribe/<plan>', methods=['POST'])
def subscribe_post(plan):
    """Process subscription signup"""
    email = request.form.get('email')
    password = request.form.get('password')
    contact_name = request.form.get('contact_name')
    
    if not all([email, password, contact_name]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('subscribe', plan=plan))
    
    session['subscription_status'] = plan
    session['subscription_start'] = datetime.now().isoformat()
    session['user_email'] = email
    session['contact_name'] = contact_name
    
    flash(f'Successfully subscribed to {plan} plan! You now have access to unmasked provider names and 10% discounts.', 'success')
    return redirect(url_for('consumer_quotes'))

@consumer_app.route('/confirm')
def consumer_confirm():
    """Enhanced confirmation with account creation requirement and fee breakdown"""
    affiliate_id = request.args.get('affiliate')
    
    if not affiliate_id or 'patient_data' not in session:
        flash('Invalid booking session. Please start over.', 'error')
        return redirect(url_for('consumer_intake'))
    
    patient_data = session['patient_data']
    quotes = get_affiliate_quotes(
        patient_data['origin'],
        patient_data['destination'],
        patient_data['equipment'],
        patient_data['transport_type']
    )
    
    selected_quote = None
    for quote in quotes:
        if quote['affiliate_id'] == affiliate_id:
            selected_quote = quote
            break
    
    if not selected_quote:
        flash('Selected affiliate not found. Please choose again.', 'error')
        return redirect(url_for('consumer_quotes'))
    
    session['selected_quote'] = selected_quote
    
    medfly_fee = MEDFLY_CONFIG['non_refundable_fee']
    affiliate_payment = selected_quote['total_cost'] - medfly_fee
    
    fee_breakdown = {
        'total_cost': selected_quote['total_cost'],
        'medfly_fee': medfly_fee,
        'affiliate_payment': affiliate_payment,
        'refundable_amount': affiliate_payment
    }
    
    return render_template('consumer_confirm.html',
                         quote=selected_quote,
                         patient_data=session['patient_data'],
                         fee_breakdown=fee_breakdown,
                         subscription_discount=session.get('subscription_status') is not None)

@consumer_app.route('/create_account_confirm', methods=['POST'])
def create_account_confirm():
    """Create account during confirmation process"""
    contact_name = request.form.get('contact_name')
    email = request.form.get('email')
    password = request.form.get('password')
    patient_gender = request.form.get('patient_gender')
    
    if not all([contact_name, email, password]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('consumer_confirm', affiliate=session.get('selected_quote', {}).get('affiliate_id')))
    
    session['user_email'] = email
    session['contact_name'] = contact_name
    session['patient_gender'] = patient_gender
    session['account_created'] = datetime.now().isoformat()
    
    logging.info(f"EMAIL VERIFICATION STUB - To: {email}, Activation code: DEMO123")
    
    flash('Account created successfully! Email verification sent (check console for demo code).', 'success')
    return redirect(url_for('consumer_tracking'))

@consumer_app.route('/tracking')
def consumer_tracking():
    """Enhanced tracking with virtual map and AI delay prediction"""
    if 'selected_quote' not in session:
        flash('No active booking found.', 'warning')
        return redirect(url_for('consumer_intake'))
    
    tracking_stages = [
        {'stage': 'Booking Confirmed', 'time': '10:00 AM', 'status': 'completed', 'icon': 'check-circle'},
        {'stage': 'Aircraft Preparation', 'time': '10:30 AM', 'status': 'completed', 'icon': 'tools'},
        {'stage': 'Medical Team Briefing', 'time': '11:00 AM', 'status': 'active', 'icon': 'user-md'},
        {'stage': 'Departure', 'time': '11:30 AM', 'status': 'pending', 'icon': 'plane-departure'},
        {'stage': 'In Transit', 'time': 'TBD', 'status': 'pending', 'icon': 'route'},
        {'stage': 'Arrival', 'time': 'TBD', 'status': 'pending', 'icon': 'map-marker-alt'}
    ]
    
    weather_data = {
        'origin_weather': {'condition': 'Clear', 'temp': 75, 'wind': '5 mph'},
        'destination_weather': {'condition': 'Partly Cloudy', 'temp': 68, 'wind': '10 mph'},
        'route_weather': 'Favorable conditions expected'
    }
    
    delay_prediction = {
        'probability': 15,
        'potential_delay': '30 minutes',
        'reason': 'Minor air traffic congestion possible',
        'alternatives': 'Alternative routes prepared'
    }
    
    return render_template('consumer_tracking.html',
                         quote=session['selected_quote'],
                         patient_data=session['patient_data'],
                         tracking_stages=tracking_stages,
                         weather_data=weather_data,
                         delay_prediction=delay_prediction)

@consumer_app.route('/api/complete-booking', methods=['POST'])
def api_complete_booking():
    """Phase 6.A: Complete booking and record commission"""
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        affiliate_id = data.get('affiliate_id')
        base_amount = data.get('base_amount_usd', 0)
        is_dummy = data.get('is_dummy', False)
        
        # Record commission entry
        success = record_commission_entry(booking_id, affiliate_id, base_amount, is_dummy)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Booking completed and commission recorded'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to record commission'
            }), 500
            
    except Exception as e:
        logging.error(f"Booking completion error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Phase 6.A: Invoice Generation Functions
def generate_weekly_invoices():
    """Generate weekly invoices for all affiliates"""
    try:
        ledger_data = load_json_data('data/ledger.json', {'entries': []})
        invoices_index = load_json_data('data/invoices/index.json', {'invoices': []})
        
        # Group entries by affiliate and week
        invoice_groups = {}
        for entry in ledger_data['entries']:
            if entry.get('is_dummy', False):
                continue  # Skip dummy bookings
                
            key = f"{entry['affiliate_id']}_{entry['invoice_week']}"
            if key not in invoice_groups:
                invoice_groups[key] = []
            invoice_groups[key].append(entry)
        
        generated_invoices = []
        
        for group_key, entries in invoice_groups.items():
            affiliate_id, invoice_week = group_key.split('_', 1)
            
            # Check if invoice already exists
            existing = any(inv['affiliate_id'] == affiliate_id and inv['invoice_week'] == invoice_week 
                          for inv in invoices_index['invoices'])
            if existing:
                continue
                
            # Calculate totals
            total_commission = sum(entry['commission_amount_usd'] for entry in entries)
            
            # Generate CSV
            csv_filename = f"data/invoices/{affiliate_id}_{invoice_week}.csv"
            generate_invoice_csv(csv_filename, entries)
            
            # Generate HTML invoice
            html_filename = f"data/invoices/{affiliate_id}_{invoice_week}.html"
            generate_invoice_html(html_filename, affiliate_id, invoice_week, entries, total_commission)
            
            # Add to invoices index
            invoice_record = {
                'affiliate_id': affiliate_id,
                'invoice_week': invoice_week,
                'status': 'issued',
                'issued_at': datetime.now().isoformat(),
                'total_usd': total_commission,
                'csv_file': csv_filename,
                'html_file': html_filename
            }
            
            invoices_index['invoices'].append(invoice_record)
            generated_invoices.append(invoice_record)
        
        # Save updated invoices index
        save_json_data('data/invoices/index.json', invoices_index)
        
        return generated_invoices
        
    except Exception as e:
        logging.error(f"Error generating invoices: {e}")
        return []

def generate_invoice_csv(filename, entries):
    """Generate CSV file for invoice"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['booking_id', 'completed_at', 'base_amount_usd', 'effective_percent', 'commission_amount_usd'])
            
            for entry in entries:
                writer.writerow([
                    entry['booking_id'],
                    entry['completed_at'],
                    entry['base_amount_usd'],
                    f"{entry['effective_percent']:.1%}",
                    entry['commission_amount_usd']
                ])
        return True
    except Exception as e:
        logging.error(f"Error generating CSV {filename}: {e}")
        return False

def generate_invoice_html(filename, affiliate_id, invoice_week, entries, total_commission):
    """Generate HTML invoice"""
    try:
        # Get week date range (Sunday-Saturday)
        year, week_num = invoice_week.split('-W')
        jan_4 = datetime(int(year), 1, 4)
        week_start = jan_4 + timedelta(days=(int(week_num)-1)*7 - jan_4.weekday())
        week_end = week_start + timedelta(days=6)
        
        due_date = datetime.now() + timedelta(days=COMMISSION_CONFIG['invoice_net_days'])
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MediFly Commission Invoice - {invoice_week}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .invoice-details {{ margin-bottom: 30px; }}
        .table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        .table th {{ background-color: #f2f2f2; }}
        .total {{ font-size: 1.2em; font-weight: bold; }}
        .remit-info {{ background-color: #f9f9f9; padding: 20px; margin-top: 30px; }}
        .footer {{ margin-top: 40px; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚁 MediFly Commission Invoice</h1>
        <p>Professional Air Medical Transport Network</p>
    </div>
    
    <div class="invoice-details">
        <p><strong>Affiliate:</strong> {affiliate_id}</p>
        <p><strong>Invoice Week:</strong> {invoice_week} ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})</p>
        <p><strong>Invoice Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
        <p><strong>Due Date:</strong> {due_date.strftime('%Y-%m-%d')} (NET {COMMISSION_CONFIG['invoice_net_days']} days)</p>
    </div>
    
    <table class="table">
        <thead>
            <tr>
                <th>Booking ID</th>
                <th>Completed Date</th>
                <th>Base Amount</th>
                <th>Commission Rate</th>
                <th>Commission Due</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for entry in entries:
            completion_date = datetime.fromisoformat(entry['completed_at']).strftime('%Y-%m-%d')
            html_content += f"""
            <tr>
                <td>{entry['booking_id'][:8]}...</td>
                <td>{completion_date}</td>
                <td>${entry['base_amount_usd']:,}</td>
                <td>{entry['effective_percent']:.1%}</td>
                <td>${entry['commission_amount_usd']:,}</td>
            </tr>
"""
        
        html_content += f"""
        </tbody>
    </table>
    
    <p class="total">Total Commission Due: ${total_commission:,}</p>
    
    <div class="remit-info">
        <h3>Payment Instructions</h3>
        <p><strong>Bank:</strong> MediFly Business Bank</p>
        <p><strong>Routing Number:</strong> 021000021</p>
        <p><strong>Account Number:</strong> 123456789</p>
        <p><strong>Reference:</strong> MEDFLY-{affiliate_id}-{invoice_week}</p>
        <p><strong>Payment Method:</strong> ACH Transfer</p>
    </div>
    
    <div class="footer">
        <p>MediFly facilitates connections between patients and air medical transport providers. You collect full booking payments. ACH commission due weekly on issued invoices.</p>
        <p><strong>Payment acknowledges acceptance of services invoiced.</strong></p>
        <p>All medical decisions and transport services are provided by independent, licensed operators.</p>
    </div>
</body>
</html>
"""
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            f.write(html_content)
        return True
        
    except Exception as e:
        logging.error(f"Error generating HTML {filename}: {e}")
        return False

@consumer_app.route('/referrals')
def referrals_page():
    """Referral member page with engaging visuals"""
    testimonials = [
        {'name': 'Sarah M.', 'text': 'MediFly saved precious time during our emergency. Professional and caring.', 'rating': 5},
        {'name': 'Dr. Johnson', 'text': 'As a hospital partner, their service consistently exceeds expectations.', 'rating': 5},
        {'name': 'Mike T.', 'text': 'The family support and communication was outstanding during a difficult time.', 'rating': 5}
    ]
    
    stats = {
        'average_savings': '20%',
        'response_time': '< 2 hours',
        'success_rate': '99.8%',
        'family_satisfaction': '4.9/5'
    }
    
    return render_template('consumer_referrals.html', testimonials=testimonials, stats=stats)

@consumer_app.route('/partners')
def partners_page():
    """Partner referral page with infographics and stats"""
    partner_benefits = [
        {'title': 'Free Lead Generation', 'description': 'No cost referrals from our platform', 'icon': 'users'},
        {'title': 'Volume Growth', 'description': 'Access to expanded patient network', 'icon': 'chart-line'},
        {'title': 'Efficiency Tools', 'description': 'Streamlined booking and management', 'icon': 'cogs'},
        {'title': 'Market Expansion', 'description': 'Geographic reach beyond current service area', 'icon': 'globe'}
    ]
    
    partner_stats = {
        'cost_reduction': '50%',
        'volume_increase': '35%',
        'partner_count': '150+',
        'success_stories': '500+'
    }
    
    return render_template('consumer_partners.html', benefits=partner_benefits, stats=partner_stats)

# Phase 6.A: Affiliate Commission Dashboard
@consumer_app.route('/affiliate/commissions')
def affiliate_commissions():
    """Affiliate commission dashboard"""
    if not session.get('logged_in') or session.get('user_role') != 'affiliate':
        flash('Affiliate access required.', 'error')
        return redirect(url_for('login'))
    
    # In a real system, this would be based on the logged-in affiliate
    # For demo, we'll use affiliate_1 as example
    affiliate_id = 'affiliate_1'  # session.get('affiliate_id', 'affiliate_1')
    
    # Load ledger and invoice data
    ledger_data = load_json_data('data/ledger.json', {'entries': []})
    invoices_data = load_json_data('data/invoices/index.json', {'invoices': []})
    
    # Filter data for this affiliate
    affiliate_entries = [entry for entry in ledger_data['entries'] 
                        if entry['affiliate_id'] == affiliate_id and not entry.get('is_dummy', False)]
    affiliate_invoices = [inv for inv in invoices_data['invoices'] 
                         if inv['affiliate_id'] == affiliate_id]
    
    # Get recoup progress
    current_recoup = get_affiliate_recoup_amount(affiliate_id)
    recoup_threshold = COMMISSION_CONFIG['recoup_threshold_usd']
    recoup_percentage = min((current_recoup / recoup_threshold) * 100, 100)
    
    # Calculate totals by week
    weekly_totals = {}
    for entry in affiliate_entries:
        week = entry['invoice_week']
        if week not in weekly_totals:
            weekly_totals[week] = {
                'week': week,
                'bookings': 0,
                'total_base': 0,
                'total_commission': 0,
                'status': 'pending'
            }
        weekly_totals[week]['bookings'] += 1
        weekly_totals[week]['total_base'] += entry['base_amount_usd']
        weekly_totals[week]['total_commission'] += entry['commission_amount_usd']
    
    # Update status from invoices
    for invoice in affiliate_invoices:
        week = invoice['invoice_week']
        if week in weekly_totals:
            weekly_totals[week]['status'] = invoice['status']
            weekly_totals[week]['issued_at'] = invoice.get('issued_at')
            weekly_totals[week]['paid_at'] = invoice.get('paid_at')
    
    # Sort by week (newest first)
    weekly_summary = sorted(weekly_totals.values(), key=lambda x: x['week'], reverse=True)
    
    # Overall stats
    total_bookings = len(affiliate_entries)
    total_commission_earned = sum(entry['commission_amount_usd'] for entry in affiliate_entries)
    total_base_volume = sum(entry['base_amount_usd'] for entry in affiliate_entries)
    
    return render_template('affiliate_commissions.html',
                         affiliate_id=affiliate_id,
                         weekly_summary=weekly_summary,
                         recoup_progress={
                             'current': current_recoup,
                             'threshold': recoup_threshold,
                             'percentage': recoup_percentage,
                             'tier': 'Tier 2 (5%)' if current_recoup >= recoup_threshold else 'Tier 1 (4%)'
                         },
                         stats={
                             'total_bookings': total_bookings,
                             'total_commission': total_commission_earned,
                             'total_volume': total_base_volume,
                             'avg_commission_rate': (total_commission_earned / total_base_volume * 100) if total_base_volume > 0 else 0
                         })

@consumer_app.route('/admin/fee_adjustment')
def admin_fee_adjustment():
    """Admin dashboard for adjusting non-refundable fee"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    current_fee = MEDFLY_CONFIG['non_refundable_fee']
    
    return render_template('admin_fee_adjustment.html', current_fee=current_fee)

# Phase 6.A: Admin Invoice Management Routes
@consumer_app.route('/admin/invoices')
def admin_invoices():
    """Admin dashboard for invoice management"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    # Load invoices and ledger data
    invoices_data = load_json_data('data/invoices/index.json', {'invoices': []})
    ledger_data = load_json_data('data/ledger.json', {'entries': []})
    
    # Group invoices by week for summary
    week_filter = request.args.get('week', '')
    affiliate_filter = request.args.get('affiliate', '')
    
    invoices = invoices_data['invoices']
    
    # Apply filters
    if week_filter:
        invoices = [inv for inv in invoices if inv['invoice_week'] == week_filter]
    if affiliate_filter:
        invoices = [inv for inv in invoices if inv['affiliate_id'] == affiliate_filter]
    
    # Get unique weeks and affiliates for filters
    all_weeks = sorted(set(inv['invoice_week'] for inv in invoices_data['invoices']), reverse=True)
    all_affiliates = sorted(set(inv['affiliate_id'] for inv in invoices_data['invoices']))
    
    # Calculate summary stats
    total_issued = sum(inv['total_usd'] for inv in invoices if inv['status'] == 'issued')
    total_paid = sum(inv['total_usd'] for inv in invoices if inv['status'] == 'paid')
    
    return render_template('admin_invoices.html',
                         invoices=invoices,
                         all_weeks=all_weeks,
                         all_affiliates=all_affiliates,
                         week_filter=week_filter,
                         affiliate_filter=affiliate_filter,
                         total_issued=total_issued,
                         total_paid=total_paid)

@consumer_app.route('/admin/generate-invoices', methods=['POST'])
def admin_generate_invoices():
    """Phase 11.C2: Fixed invoice generation with PostgreSQL support"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        if DB_AVAILABLE:
            with consumer_app.app_context():
                # Get commissions that need invoicing
                commissions_to_invoice = Commission.query.filter(
                    Commission.invoice_status == 'pending'
                ).all()
                
                if not commissions_to_invoice:
                    flash('No commissions ready for invoicing', 'info')
                    return redirect(url_for('admin_invoices'))
                
                # Group by affiliate and generate invoices
                invoices_by_affiliate = {}
                for commission in commissions_to_invoice:
                    affiliate_id = commission.affiliate_id or 'default'
                    if affiliate_id not in invoices_by_affiliate:
                        invoices_by_affiliate[affiliate_id] = []
                    invoices_by_affiliate[affiliate_id].append(commission)
                
                invoice_count = 0
                total_amount = 0.0
                
                for affiliate_id, affiliate_commissions in invoices_by_affiliate.items():
                    affiliate_total = sum(c.commission_amount_usd for c in affiliate_commissions)
                    total_amount += affiliate_total
                    
                    # Mark commissions as invoiced
                    for commission in affiliate_commissions:
                        commission.invoice_status = 'issued'
                        commission.invoice_generated_at = datetime.now()
                    
                    invoice_count += 1
                
                db.session.commit()
                
                message = f"Generated {invoice_count} invoices totaling ${total_amount:,.2f}"
                flash(message, 'success')
                logging.info(f"ADMIN: {message}")
                return redirect(url_for('admin_invoices'))
        else:
            # Fallback to JSON system
            generated = generate_weekly_invoices()
            
            if generated:
                message = f"Generated {len(generated)} new invoice(s)"
                flash(message, 'success')
                logging.info(f"ADMIN: {message} by {session.get('contact_name', 'admin')}")
            else:
                flash('No new invoices to generate', 'info')
            
            return redirect(url_for('admin_invoices'))
            
    except Exception as e:
        logging.error(f"Invoice generation error: {e}")
        flash('Error generating invoices', 'error')
        return redirect(url_for('admin_invoices'))

@consumer_app.route('/admin/mark-invoice-paid', methods=['POST'])
def admin_mark_invoice_paid():
    """Mark an invoice as paid"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        affiliate_id = data.get('affiliate_id')
        invoice_week = data.get('invoice_week')
        remittance_ref = data.get('remittance_ref', '')
        
        # Update invoice status
        invoices_data = load_json_data('data/invoices/index.json', {'invoices': []})
        
        for invoice in invoices_data['invoices']:
            if invoice['affiliate_id'] == affiliate_id and invoice['invoice_week'] == invoice_week:
                invoice['status'] = 'paid'
                invoice['paid_at'] = datetime.now().isoformat()
                if remittance_ref:
                    invoice['remittance_ref'] = remittance_ref
                break
        
        if save_json_data('data/invoices/index.json', invoices_data):
            logging.info(f"ADMIN: Invoice {affiliate_id}_{invoice_week} marked as paid")
            return jsonify({'success': True, 'message': 'Invoice marked as paid'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update invoice'}), 500
            
    except Exception as e:
        logging.error(f"Error marking invoice as paid: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@consumer_app.route('/admin/download-invoice/<affiliate_id>/<invoice_week>/<file_type>')
def admin_download_invoice(affiliate_id, invoice_week, file_type):
    """Download invoice CSV or HTML"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    try:
        if file_type == 'csv':
            filename = f"data/invoices/{affiliate_id}_{invoice_week}.csv"
            if os.path.exists(filename):
                return send_file(filename, as_attachment=True, download_name=f"{affiliate_id}_{invoice_week}.csv")
        elif file_type == 'html':
            filename = f"data/invoices/{affiliate_id}_{invoice_week}.html"
            if os.path.exists(filename):
                return send_file(filename, as_attachment=False)
        
        flash('Invoice file not found', 'error')
        return redirect(url_for('admin_invoices'))
        
    except Exception as e:
        logging.error(f"Error downloading invoice: {e}")
        flash('Error downloading invoice', 'error')
        return redirect(url_for('admin_invoices'))

@consumer_app.route('/admin/fee_adjustment', methods=['POST'])
def admin_fee_adjustment_post():
    """Update non-refundable fee"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    new_fee = request.form.get('new_fee', type=int)
    if new_fee and new_fee > 0:
        MEDFLY_CONFIG['non_refundable_fee'] = new_fee
        flash(f'Non-refundable fee updated to ${new_fee:,}', 'success')
        logging.info(f"ADMIN: Fee updated to ${new_fee} by {session.get('contact_name', 'admin')}")
    else:
        flash('Please enter a valid fee amount.', 'error')
    
    return redirect(url_for('admin_fee_adjustment'))

# AI Command Processing and Chat Integration
@consumer_app.route('/ai_command', methods=['POST'])
def ai_command():
    """Process AI commands for smart form filling"""
    command = request.form.get('command', '').lower()
    response = {'status': 'success', 'suggestions': {}}
    
    # AI command patterns (stub implementation)
    if 'grandma' in command and 'orlando' in command and 'nyc' in command:
        response['suggestions'] = {
            'origin': 'Orlando International Airport (MCO)',
            'destination': 'LaGuardia Airport (LGA)',
            'transport_type': 'non-critical',
            'equipment': ['oxygen', 'escort'],
            'message': 'I suggest comfortable transport with oxygen support and medical escort for elderly patient.'
        }
    elif 'emergency' in command or 'urgent' in command:
        response['suggestions'] = {
            'transport_type': 'critical',
            'same_day': True,
            'message': 'Emergency transport recommended with same-day priority.'
        }
    elif 'family' in command:
        response['suggestions'] = {
            'equipment': ['escort'],
            'message': 'Family accommodation options available.'
        }
    else:
        response = {
            'status': 'info',
            'message': 'Try commands like: "Help me build a flight for grandma from Orlando to NYC" or "Emergency transport needed"'
        }
    
    return jsonify(response)

# Partner Dashboard (for providers)
@consumer_app.route('/partner_dashboard')
def partner_dashboard():
    """Partner dashboard with bookings and revenue"""
    if not session.get('logged_in') or session.get('user_role') != 'affiliate':
        flash('Affiliate access required.', 'error')
        return redirect(url_for('login'))
    
    # Mock partner data
    partner_bookings = [
        {'date': '2025-08-01', 'origin': 'Orlando', 'destination': 'NYC', 'revenue': 128000, 'status': 'completed'},
        {'date': '2025-08-03', 'origin': 'Miami', 'destination': 'Atlanta', 'revenue': 135000, 'status': 'active'},
        {'date': '2025-08-04', 'origin': 'Tampa', 'destination': 'Boston', 'revenue': 142000, 'status': 'pending'}
    ]
    
    total_revenue = sum(booking['revenue'] for booking in partner_bookings)
    partner_stats = {
        'total_bookings': len(partner_bookings),
        'total_revenue': total_revenue,
        'success_rate': '98.5%',
        'priority_status': True
    }
    
    return render_template('partner_dashboard.html', 
                         bookings=partner_bookings, 
                         stats=partner_stats)

@consumer_app.route('/join_affiliate')
def join_affiliate():
    """Join as Affiliate (Air Operator)"""
    return render_template('join_affiliate_page.html')

# Provider Search API Endpoints
@consumer_app.route('/api/providers/search')
def api_providers_search():
    """Hybrid search: internal cache first, then Google Places, then manual fallback"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'ok': True, 'results': []})
    
    # Step 1: Try internal search first
    internal_results = search_internal(query)
    
    if internal_results:
        # Record internal hit and return
        record_hit_ratio('internal')
        
        # Format results for frontend
        results = []
        for provider in internal_results:
            results.append({
                'id': provider['id'],
                'name': provider['name'],
                'address': provider['address'],
                'type': provider['type'],
                'source': 'internal',
                'lat': provider.get('lat'),
                'lng': provider.get('lng'),
                'search_count': provider.get('search_count_90d', 0)
            })
        
        return jsonify({
            'ok': True,
            'results': results,
            'source': 'internal',
            'message': f'Found {len(results)} internal matches'
        })
    
    # Step 2: Try Google Places if API key is available
    api_key = MEDFLY_CONFIG.get('google_places_api_key')
    if api_key and api_key != "demo-key":
        google_results = search_google_places(query, api_key)
        
        if google_results:
            record_hit_ratio('external')
            return jsonify({
                'ok': True,
                'results': google_results,
                'source': 'google',
                'message': f'Found {len(google_results)} Google Places matches'
            })
    
    # Step 3: No results - return empty with manual entry suggestion
    return jsonify({
        'ok': True,
        'results': [],
        'source': 'none',
        'message': 'No matches found. Please add manually if needed.'
    })

@consumer_app.route('/api/providers/manual', methods=['POST'])
def api_providers_manual():
    """Submit manual provider entry for admin approval"""
    data = request.get_json()
    
    name = data.get('name', '').strip()
    address = data.get('address', '').strip()
    provider_type = data.get('type', 'unknown').strip()
    
    if not name or not address:
        return jsonify({'ok': False, 'error': 'Name and address are required'}), 400
    
    # Valid types
    valid_types = ['hospital', 'clinic', 'airport', 'address', 'unknown']
    if provider_type not in valid_types:
        provider_type = 'unknown'
    
    try:
        new_provider = submit_manual_entry(name, address, provider_type)
        
        return jsonify({
            'ok': True,
            'provider': {
                'id': new_provider['id'],
                'name': new_provider['name'],
                'address': new_provider['address'],
                'type': new_provider['type'],
                'source': 'manual',
                'approved': False
            },
            'message': 'Manual entry submitted for admin approval'
        })
    
    except Exception as e:
        logging.error(f"Manual entry error: {e}")
        return jsonify({'ok': False, 'error': 'Failed to save manual entry'}), 500

@consumer_app.route('/api/providers/select', methods=['POST'])
def api_providers_select():
    """Record provider selection and increment usage stats"""
    data = request.get_json()
    provider_id = data.get('provider_id')
    source = data.get('source', 'unknown')
    
    if not provider_id:
        return jsonify({'ok': False, 'error': 'Provider ID required'}), 400
    
    # If internal provider, increment usage count
    if source == 'internal':
        promote_or_increment(provider_id)
    
    return jsonify({'ok': True, 'message': 'Selection recorded'})

# Admin Facilities Management
@consumer_app.route('/admin/facilities')
def admin_facilities():
    """Admin page for managing facilities and approval queue"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    index = load_index()
    metrics = load_metrics()
    
    # Separate approved and pending providers
    approved_providers = [p for p in index['providers'] if p.get('approved', False)]
    pending_providers = [p for p in index['providers'] if not p.get('approved', False)]
    
    # Calculate hit ratio for cost control KPI
    total_hits = metrics['internal_hits'] + metrics['external_hits']
    internal_percentage = (metrics['internal_hits'] / total_hits * 100) if total_hits > 0 else 0
    
    hit_ratio_stats = {
        'internal_hits': metrics['internal_hits'],
        'external_hits': metrics['external_hits'],
        'manual_entries': metrics['manual_entries'],
        'internal_percentage': round(internal_percentage, 1),
        'period_start': metrics['period_start']
    }
    
    return render_template('admin_facilities.html',
                         approved_providers=approved_providers,
                         pending_providers=pending_providers,
                         hit_ratio_stats=hit_ratio_stats)

@consumer_app.route('/admin/facilities/approve/<provider_id>', methods=['POST'])
def admin_approve_provider(provider_id):
    """Approve a manual provider entry"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return jsonify({'ok': False, 'error': 'Admin access required'}), 403
    
    index = load_index()
    
    for provider in index['providers']:
        if provider['id'] == provider_id:
            provider['approved'] = True
            provider['source'] = 'internal'  # Promote to internal once approved
            provider['updated_at'] = datetime.utcnow().isoformat() + "Z"
            break
    
    save_index(index)
    flash('Provider approved and added to internal index.', 'success')
    return redirect(url_for('admin_facilities'))

@consumer_app.route('/admin/facilities/reject/<provider_id>', methods=['POST'])
def admin_reject_provider(provider_id):
    """Reject and remove a manual provider entry"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return jsonify({'ok': False, 'error': 'Admin access required'}), 403
    
    index = load_index()
    index['providers'] = [p for p in index['providers'] if p['id'] != provider_id]
    save_index(index)
    
    flash('Provider rejected and removed.', 'success')
    return redirect(url_for('admin_facilities'))

# Duplicate route removed - keeping original join_affiliate route above

@consumer_app.route('/join_hospital')
def join_hospital():
    """Join as Hospital/Clinic"""
    return render_template('join_hospital_page.html')

@consumer_app.route('/mvp-incentive')
def mvp_incentive():
    """MVP Incentive Program placeholder page"""
    return render_template('mvp_incentive.html')

# Error handlers
@consumer_app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page"""
    return render_template('404.html'), 404

@consumer_app.errorhandler(500)
def internal_server_error(e):
    """Custom 500 error page"""
    return render_template('500.html'), 500

# Demo Toolkit Routes
@consumer_app.route('/admin/demo/create')
def admin_demo_create():
    """Create guided demo with realistic cases"""
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    # Seed 5 realistic cases with staggered timestamps
    demo_cases = [
        {
            'patient_name': 'Emma Rodriguez',
            'age': 67,
            'condition': 'Acute MI - STEMI',
            'transport_type': 'critical',
            'from_location': 'Rural General Hospital, TX',
            'to_location': 'Houston Methodist Hospital, TX',
            'equipment': ['Ventilator', 'Cardiac Monitor'],
            'timestamp': datetime.now() - timedelta(hours=2)
        },
        {
            'patient_name': 'Michael Chen',
            'age': 34,
            'condition': 'Trauma - Multi-organ',
            'transport_type': 'critical',
            'from_location': 'Community Hospital, CO',
            'to_location': 'Denver Health Medical Center, CO',
            'equipment': ['ECMO', 'Blood Bank'],
            'timestamp': datetime.now() - timedelta(hours=1, minutes=30)
        },
        {
            'patient_name': 'Sarah Johnson',
            'age': 45,
            'condition': 'Stroke - Large Vessel',
            'transport_type': 'critical',
            'from_location': 'Regional Medical Center, FL',
            'to_location': 'Miami Neuroscience Institute, FL',
            'equipment': ['Neuro Monitor', 'Ventilator'],
            'timestamp': datetime.now() - timedelta(hours=1)
        },
        {
            'patient_name': 'Robert Williams',
            'age': 72,
            'condition': 'Cardiac - Planned Transfer',
            'transport_type': 'non-critical',
            'from_location': 'Valley Hospital, CA',
            'to_location': 'UCLA Medical Center, CA',
            'equipment': ['Cardiac Monitor'],
            'timestamp': datetime.now() - timedelta(minutes=45)
        },
        {
            'patient_name': 'Maria Gonzalez',
            'age': 28,
            'condition': 'High-risk Pregnancy',
            'transport_type': 'non-critical',
            'from_location': 'County Hospital, AZ',
            'to_location': 'Phoenix Childrens Hospital, AZ',
            'equipment': ['Neonatal Transport'],
            'timestamp': datetime.now() - timedelta(minutes=20)
        }
    ]
    
    # Store demo data in session
    session['demo_mode'] = True
    session['demo_cases'] = demo_cases
    session['training_mode'] = True
    
    logging.info(f"Admin {session.get('username')} created guided demo with {len(demo_cases)} cases")
    
    flash(f'Guided demo created successfully with {len(demo_cases)} realistic cases. Training mode enabled.', 'success')
    return redirect(url_for('admin_dashboard'))

@consumer_app.route('/admin/demo/reset')
def admin_demo_reset():
    """Reset demo data to clean state"""
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    # Clear demo-related session data
    if 'demo_mode' in session:
        del session['demo_mode']
    if 'demo_cases' in session:
        del session['demo_cases']
    if 'training_mode' in session:
        del session['training_mode']
    
    # Clear any demo bookings from commission ledger
    commission_ledger = session.get('commission_ledger', [])
    session['commission_ledger'] = [booking for booking in commission_ledger if not booking.get('demo_booking')]
    
    logging.info(f"Admin {session.get('username')} reset demo data")
    
    flash('Demo data reset successfully. System returned to clean state.', 'success')
    return redirect(url_for('admin_dashboard'))

# Monthly Analytics Roll-up
@consumer_app.route('/admin/analytics/monthly')
def admin_monthly_analytics():
    """Monthly roll-up analytics dashboard"""
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    # Calculate monthly stats
    current_month = datetime.now().strftime('%B %Y')
    
    # Mock data for demonstration
    monthly_stats = {
        'period': current_month,
        'bookings': 247,
        'win_rate': 68.3,
        'avg_response_time': '18 minutes',
        'revenue': 89750.00,
        'top_niches': [
            {'name': 'Critical Care', 'bookings': 89, 'revenue': 34250},
            {'name': 'Cardiac Transport', 'bookings': 67, 'revenue': 28900},
            {'name': 'Trauma Response', 'bookings': 45, 'revenue': 19800}
        ]
    }
    
    return render_template('admin_monthly_analytics.html', stats=monthly_stats)

@consumer_app.route('/admin/analytics/export')
def admin_analytics_export():
    """Export monthly analytics as CSV"""
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    # Generate CSV data
    csv_data = []
    csv_data.append(['Metric', 'Value'])
    csv_data.append(['Total Bookings', '247'])
    csv_data.append(['Win Rate', '68.3%'])
    csv_data.append(['Avg Response Time', '18 minutes'])
    csv_data.append(['Total Revenue', '$89,750.00'])
    csv_data.append(['Top Niche', 'Critical Care (89 bookings)'])
    
    # Create CSV response
    import io
    output = io.StringIO()
    import csv
    writer = csv.writer(output)
    writer.writerows(csv_data)
    
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=medifly_analytics_{datetime.now().strftime("%Y-%m")}.csv'
    
    logging.info(f"Admin {session.get('username')} exported monthly analytics")
    return response

# Email functionality
def send_email_template(template_name, recipient_email, **template_vars):
    """Send email using template or log HTML if SMTP not configured"""
    try:
        # Render email template
        template_vars.update({
            'recipient_email': recipient_email,
            'current_year': datetime.now().year
        })
        
        email_html = render_template(f'email/{template_name}', **template_vars)
        
        # Check for SMTP configuration
        smtp_host = os.environ.get('SMTP_HOST')
        if smtp_host:
            # TODO: Implement actual SMTP sending
            logging.info(f"Would send email via SMTP to {recipient_email}")
        else:
            # Log the rendered HTML
            logging.info(f"Email template '{template_name}' rendered for {recipient_email}:")
            logging.info(email_html)
            
        return True
    except Exception as e:
        logging.error(f"Error sending email template {template_name}: {e}")
        return False

# Demo toolkit guided demo cards
# Phase 11.C2: Stepper intake implementation
@consumer_app.route('/intake')
def intake():
    """Phase 11.C2: Complete 4-step stepper intake with state persistence"""
    # Get or create intake session data
    if 'intake_data' not in session:
        session['intake_data'] = {
            'step': 1,
            'service_type': None,
            'from_location': None,
            'to_location': None,
            'date_time': None,
            'patient_info': {},
            'requirements': {}
        }
    
    current_step = session.get('intake_data', {}).get('step', 1)
    
    # Load available niches from database
    niches_list = []
    if DB_AVAILABLE:
        try:
            with consumer_app.app_context():
                niches = Niche.query.all()
                niches_list = [{'id': n.id, 'name': n.name, 'description': n.description} for n in niches]
        except Exception as e:
            logging.error(f"Error loading niches: {e}")
    
    if not niches_list:
        # Fallback to default niches
        niches_list = [
            {'id': 1, 'name': 'Cardiac Emergency', 'description': 'Heart-related critical care'},
            {'id': 2, 'name': 'Trauma Transport', 'description': 'Emergency trauma cases'},
            {'id': 3, 'name': 'Neonatal ICU', 'description': 'Newborn intensive care'},
            {'id': 4, 'name': 'Organ Transport', 'description': 'Time-critical organ delivery'},
            {'id': 5, 'name': 'Psychiatric Crisis', 'description': 'Mental health emergencies'}
        ]
    
    return render_template('intake_stepper.html', 
                         current_step=current_step,
                         intake_data=session.get('intake_data', {}),
                         niches=niches_list)

@consumer_app.route('/intake/step', methods=['POST'])
def intake_step():
    """Handle stepper intake form submissions"""
    try:
        step = int(request.form.get('step', 1))
        
        if 'intake_data' not in session:
            session['intake_data'] = {'step': 1}
        
        intake_data = session['intake_data']
        
        if step == 1:
            # Service Type Step
            intake_data['service_type'] = request.form.get('service_type')
            intake_data['step'] = 2
            
        elif step == 2:
            # Location Step
            intake_data['from_location'] = request.form.get('from_location')
            intake_data['to_location'] = request.form.get('to_location')
            intake_data['step'] = 3
            
        elif step == 3:
            # Date/Time Step
            intake_data['date_time'] = request.form.get('date_time')
            intake_data['same_day_confirmed'] = bool(request.form.get('same_day_confirmed'))
            intake_data['step'] = 4
            
        elif step == 4:
            # Patient & Requirements Step
            intake_data['patient_info'] = {
                'age_band': request.form.get('age_band'),
                'severity': int(request.form.get('severity', 2))
            }
            intake_data['requirements'] = {
                'niches': request.form.getlist('niches'),
                'international_regions': request.form.getlist('international_regions'),
                'ground_ambulance': bool(request.form.get('ground_ambulance'))
            }
            
            # Complete intake - redirect to comparison
            session['booking_data'] = intake_data
            session.pop('intake_data', None)  # Clear intake session
            
            flash('Transport request created successfully!', 'success')
            return redirect(url_for('compare_providers'))
        
        session['intake_data'] = intake_data
        session.modified = True
        
        return redirect(url_for('intake'))
        
    except Exception as e:
        logging.error(f"Intake step error: {e}")
        flash('Error processing form', 'error')
        return redirect(url_for('intake'))

@consumer_app.route('/intake/back', methods=['POST'])
def intake_back():
    """Handle back navigation in stepper"""
    try:
        current_step = int(request.form.get('current_step', 2))
        new_step = max(1, current_step - 1)
        
        if 'intake_data' in session:
            session['intake_data']['step'] = new_step
            session.modified = True
            
        return redirect(url_for('intake'))
        
    except Exception as e:
        logging.error(f"Intake back error: {e}")
        return redirect(url_for('intake'))

@consumer_app.route('/demo/guided')
def demo_guided():
    """Show guided demo cards for affiliates and hospitals"""
    if not session.get('training_mode'):
        return redirect(url_for('home'))
    
    user_role = session.get('user_role', 'family')
    
    if user_role in ['affiliate', 'hospital']:
        demo_cards = {
            'affiliate': [
                {
                    'title': 'Refer Your First Hospital',
                    'description': 'Learn how to onboard medical facilities',
                    'action': 'Start Tutorial',
                    'url': url_for('join_hospital')
                },
                {
                    'title': 'Track Commission Progress',
                    'description': 'Monitor your path to 5% commission tier',
                    'action': 'View Analytics',
                    'url': url_for('affiliate_dashboard')
                }
            ],
            'hospital': [
                {
                    'title': 'Submit Transport Request',
                    'description': 'Walk through the request process',
                    'action': 'Start Demo',
                    'url': url_for('consumer_intake')
                },
                {
                    'title': 'Compare Provider Quotes',
                    'description': 'Learn quote evaluation process',
                    'action': 'View Examples',
                    'url': url_for('consumer_results')
                }
            ]
        }
        
        return render_template('demo_guided.html', 
                             demo_cards=demo_cards.get(user_role, []),
                             user_role=user_role)
    
    return redirect(url_for('home'))

# Phase 11.A: Database Dummy Data Toggle
@consumer_app.route('/admin/dummy/toggle', methods=['POST'])
def admin_dummy_toggle():
    """Toggle dummy data in database"""
    if session.get('user_role') != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    if not DB_AVAILABLE:
        flash('Database not available', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        with consumer_app.app_context():
            current_status = get_dummy_data_status()
            has_dummy_data = current_status['bookings'] > 0
        
            if has_dummy_data:
                # Remove dummy data
                remove_dummy_data()
                flash('Dummy data removed from database', 'success')
                logging.info(f"Admin {session.get('username')} removed database dummy data")
            else:
                # Add dummy data
                seed_dummy_data()
                flash('Dummy data loaded into database', 'success')
                logging.info(f"Admin {session.get('username')} added database dummy data")
        
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        logging.error(f"Error toggling dummy data: {e}")
        flash(f'Error toggling dummy data: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@consumer_app.route('/admin/db/status')
def admin_db_status():
    """Get database status"""
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    if not DB_AVAILABLE:
        return jsonify({
            'database_available': False,
            'message': 'Database not configured'
        })
    
    try:
        with consumer_app.app_context():
            status = get_dummy_data_status()
            niches_count = Niche.query.count() if DB_AVAILABLE else 0
        
        return jsonify({
            'database_available': True,
            'dummy_data_counts': status,
            'niches_seeded': niches_count,
            'has_dummy_data': status['bookings'] > 0
        })
        
    except Exception as e:
        return jsonify({
            'database_available': False,
            'error': str(e)
        })

# Phase 6.A: Test Commission Recording (for demonstration)
@consumer_app.route('/test-commission')
def test_commission():
    """Test endpoint to create sample commission entries"""
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        flash('Admin access required for testing.', 'error')
        return redirect(url_for('login'))
    
    # Create some test commission entries
    test_bookings = [
        {'booking_id': 'test-001', 'affiliate_id': 'affiliate_1', 'base_amount': 125000, 'is_dummy': False},
        {'booking_id': 'test-002', 'affiliate_id': 'affiliate_2', 'base_amount': 98000, 'is_dummy': False},
        {'booking_id': 'test-003', 'affiliate_id': 'affiliate_1', 'base_amount': 156000, 'is_dummy': False},
        {'booking_id': 'dummy-001', 'affiliate_id': 'affiliate_1', 'base_amount': 75000, 'is_dummy': True}
    ]
    
    created = 0
    for booking in test_bookings:
        success = record_commission_entry(
            booking['booking_id'], 
            booking['affiliate_id'], 
            booking['base_amount'], 
            booking['is_dummy']
        )
        if success:
            created += 1
    
    flash(f'Created {created} test commission entries', 'success')
    return redirect(url_for('admin_invoices'))

# Phase 7.A: Enhanced QA Hardening Functions
def enforce_training_limit(affiliate_id):
    """Check and enforce training dummy case limits"""
    try:
        training_data = load_json_data('data/training_limits.json', {'affiliate_limits': {}})
        
        if affiliate_id not in training_data['affiliate_limits']:
            training_data['affiliate_limits'][affiliate_id] = {
                'dummy_cases_used': 0,
                'dummy_cases_limit': OPERATIONAL_CONFIG['training_limits']['dummy_cases_per_affiliate'],
                'last_dummy_case': None
            }
        
        limit_info = training_data['affiliate_limits'][affiliate_id]
        
        if limit_info['dummy_cases_used'] >= limit_info['dummy_cases_limit']:
            return False, f"Training limit reached ({limit_info['dummy_cases_used']}/{limit_info['dummy_cases_limit']})"
        
        # Increment usage
        limit_info['dummy_cases_used'] += 1
        limit_info['last_dummy_case'] = datetime.now().isoformat()
        
        save_json_data('data/training_limits.json', training_data)
        
        remaining = limit_info['dummy_cases_limit'] - limit_info['dummy_cases_used']
        return True, f"Training case recorded. Remaining: {remaining}"
        
    except Exception as e:
        logging.error(f"Error enforcing training limit: {e}")
        return False, "Error checking training limits"

def check_modify_permissions(request_id):
    """Check if request can be modified (locked after quote selection)"""
    # In production, check actual quote selection status
    quote_selected = session.get('quote_selection_locked', False)
    
    if quote_selected:
        return False, "Cannot modify - quote already selected"
    
    return True, "Modification allowed"

# Phase 7.E: Enhanced Currency Formatting
def format_currency(amount):
    """Enhanced currency formatting with error handling"""
    try:
        if amount is None:
            return "$0.00"
        
        # Handle string input (already formatted currency)
        if isinstance(amount, str):
            # If already starts with $, return as-is
            if amount.startswith('$'):
                return amount
            # Strip non-numeric characters and parse
            clean_amount = ''.join(c for c in amount if c.isdigit() or c == '.')
            if clean_amount:
                return f"${float(clean_amount):,.2f}"
            return "$0.00"
        
        # Handle numeric input
        return f"${float(amount):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def clean_display_name(full_name):
    """Strip titles/honorifics from display names"""
    titles = ['Dr.', 'Captain', 'Mr.', 'Ms.', 'Mrs.', 'Prof.', 'Rev.']
    name_parts = full_name.split()
    cleaned_parts = [part for part in name_parts if part not in titles]
    return ' '.join(cleaned_parts)

def get_user_time_preference():
    """Get user's time format preference (12h/24h)"""
    return session.get('time_format', '12h')  # Default to 12-hour

def format_time_with_preference(time_obj):
    """Format time according to user preference"""
    if get_user_time_preference() == '24h':
        return time_obj.strftime('%H:%M:%S')
    else:
        return time_obj.strftime('%I:%M:%S %p')

# Phase 7.A: Template Context Processor for Site-wide Announcements
@consumer_app.context_processor
def inject_announcements():
    """Inject active announcements into all templates"""
    return {
        'active_announcements': get_active_announcements(),
        'training_config': TRAINING_CONFIG,
        'format_currency': format_currency,
        'clean_display_name': clean_display_name,
        'format_time_with_preference': format_time_with_preference
    }

# Phase 7.C: User Preferences Route
@consumer_app.route('/update_preferences', methods=['POST'])
def update_preferences():
    """Update user display preferences"""
    time_format = request.form.get('time_format', '12h')
    session['time_format'] = time_format
    flash('Preferences updated successfully.', 'success')
    return redirect(request.referrer or url_for('home'))

# Phase 7.C: Post-Flight Feedback Route
@consumer_app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Submit post-flight feedback"""
    try:
        feedback_data = {
            'booking_id': request.form.get('booking_id'),
            'rating': int(request.form.get('rating')),
            'primary_category': request.form.get('primary_category'),
            'comments': request.form.get('comments'),
            'requires_followup': 'requires_followup' in request.form,
            'submitted_at': datetime.now().isoformat(),
            'submitted_by': session.get('username', 'anonymous')
        }
        
        # Save feedback (in production, save to database)
        logging.info(f"Post-flight feedback submitted: {feedback_data}")
        flash('Thank you for your feedback. Your input helps us improve our services.', 'success')
        
        return redirect(url_for('home'))
        
    except Exception as e:
        logging.error(f"Feedback submission error: {e}")
        flash('Error submitting feedback. Please try again.', 'error')
        return redirect(request.referrer or url_for('home'))



if __name__ == '__main__':
    consumer_app.run(host='0.0.0.0', port=5000, debug=True)