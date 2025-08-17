"""
SQLAlchemy models for MediFly database
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app import db

class User(db.Model):
    """Base user model for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))
    role = Column(String(20), nullable=False, default='family')  # family, hospital, provider, affiliate, admin, mvp
    sub_role = Column(String(20), default='TeamUser')  # PowerUser, TeamUser
    permissions = Column(JSON, default=lambda: {})  # Detailed permissions
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Niche(db.Model):
    """Medical transport niches/specialties"""
    __tablename__ = 'niches'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    equipment_requirements = Column(JSON)  # Store as JSON
    base_upcharge_percent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    bookings = relationship("Booking", back_populates="niche")
    affiliate_niches = relationship("AffiliateNiche", back_populates="niche")
    
    def __repr__(self):
        return f'<Niche {self.name}>'

class Affiliate(db.Model):
    """Affiliate partners managing hospitals"""
    __tablename__ = 'affiliates'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    company_name = Column(String(200), nullable=False)
    contact_email = Column(String(120), nullable=False)
    phone_number = Column(String(20))
    contact_name = Column(String(100))
    recouped_amount_usd = Column(Float, default=0.0)
    commission_percent_default = Column(Float, default=0.05)  # 3-7% range, adjustable by admin
    total_bookings = Column(Integer, default=0)
    avg_response_time_minutes = Column(Integer, default=0)
    response_rate_30day = Column(Float, default=0.0)  # 0.0-1.0
    is_spotlight = Column(Boolean, default=False)  # <50 bookings or <90 days
    offers_concierge = Column(Boolean, default=False)  # Concierge service provider
    referral_code = Column(String(20), unique=True, nullable=True)  # For referral tracking
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_demo_data = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", backref="affiliate_profile")
    hospitals = relationship("Hospital", back_populates="affiliate")
    affiliate_niches = relationship("AffiliateNiche", back_populates="affiliate")
    commissions = relationship("Commission", back_populates="affiliate")
    
    def __repr__(self):
        return f'<Affiliate {self.company_name}>'

class Hospital(db.Model):
    """Hospitals submitting transport requests"""
    __tablename__ = 'hospitals'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=True)
    name = Column(String(200), nullable=False)
    address = Column(Text)
    contact_email = Column(String(120), nullable=False)
    phone = Column(String(20))
    license_number = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_demo_data = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", backref="hospital_profile")
    affiliate = relationship("Affiliate", back_populates="hospitals")
    bookings = relationship("Booking", back_populates="hospital")
    
    def __repr__(self):
        return f'<Hospital {self.name}>'

class Booking(db.Model):
    """Transport booking requests"""
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=False)
    niche_id = Column(Integer, ForeignKey('niches.id'), nullable=True)
    
    # Patient info (anonymized)
    patient_age = Column(Integer)
    transport_type = Column(String(50))  # critical, non_critical, mvp
    urgency_level = Column(String(20))  # routine, urgent, critical
    
    # Location details
    origin_address = Column(Text)
    destination_address = Column(Text)
    estimated_distance_miles = Column(Integer)
    
    # Equipment and requirements
    equipment_needed = Column(JSON)  # Store as JSON array
    special_requirements = Column(Text)
    
    # Booking details
    status = Column(String(30), default='pending')  # pending, quoted, booked, completed, cancelled
    selected_quote_id = Column(Integer, nullable=True)  # Remove FK for now
    total_amount_usd = Column(Float)
    deposit_amount_usd = Column(Float, default=250.0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    requested_pickup_time = Column(DateTime)
    actual_pickup_time = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Concierge add-on option
    concierge_selected = Column(Boolean, default=False)
    
    # Demo/testing flags
    is_demo_data = Column(Boolean, default=False)
    
    # Relationships
    hospital = relationship("Hospital", back_populates="bookings")
    niche = relationship("Niche", back_populates="bookings")
    # quotes = relationship("Quote", back_populates="booking")  # Disabled until proper FK setup
    commissions = relationship("Commission", back_populates="booking")
    
    def __repr__(self):
        return f'<Booking {self.id} - {self.status}>'

class Quote(db.Model):
    """Provider quotes for transport requests"""
    __tablename__ = 'quotes'
    
    id = Column(Integer, primary_key=True)
    ref_id = Column(String(50), unique=True, nullable=False)  # QR240817XXXX format
    
    # Contact information
    contact_name = Column(String(200), nullable=False)
    contact_email = Column(String(120), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    
    # Service details
    service_type = Column(String(50), nullable=False)  # critical, scheduled
    severity_level = Column(Integer, nullable=False)  # 1, 2, 3
    
    # Flight information
    flight_date = Column(DateTime, nullable=False)
    return_flight = Column(Boolean, default=False)
    return_date = Column(DateTime, nullable=True)
    
    # Location details
    from_city = Column(String(100), nullable=False)
    from_state = Column(String(100), nullable=False) 
    from_country = Column(String(100), default='United States')
    to_city = Column(String(100), nullable=False)
    to_state = Column(String(100), nullable=False)
    to_country = Column(String(100), default='United States')
    
    # COVID information
    covid_tested = Column(String(10), nullable=True)  # yes, no
    covid_result = Column(String(10), nullable=True)  # n/a, negative, positive
    
    # Medical information
    specialized_care = Column(Text, nullable=True)
    additional_medical_info = Column(Text, nullable=True)
    
    # Equipment flags based on severity level
    equipment_monitor = Column(Boolean, default=False)
    equipment_stretcher = Column(Boolean, default=False) 
    equipment_oxygen = Column(Boolean, default=False)
    
    # Provider quote fields (added for notification system)
    provider_name = Column(String(200), nullable=True)
    quoted_price = Column(Float, nullable=True)
    aircraft_type = Column(String(100), nullable=True)
    estimated_flight_time = Column(String(50), nullable=True)
    provider_notes = Column(Text, nullable=True)
    
    # Notification timestamps
    affiliate_notified_at = Column(DateTime, nullable=True)
    caller_notified_at = Column(DateTime, nullable=True)
    quote_submitted_at = Column(DateTime, nullable=True)
    quote_expires_at = Column(DateTime, nullable=True)
    booking_confirmed_at = Column(DateTime, nullable=True)
    booking_reference = Column(String(50), nullable=True)
    
    # Additional contact fields for intake form
    relation_to_patient = Column(String(100), nullable=True)
    from_hospital = Column(String(200), nullable=True)
    from_address = Column(String(500), nullable=True)
    to_hospital = Column(String(200), nullable=True)
    to_address = Column(String(500), nullable=True)
    preferred_time = Column(String(50), nullable=True)
    family_seats = Column(Integer, default=0)
    patient_gender = Column(String(20), nullable=True)
    patient_age_range = Column(String(50), nullable=True)
    patient_weight = Column(String(50), nullable=True)
    additional_info = Column(Text, nullable=True)
    
    # Medical equipment flags (for compatibility with intake form)
    oxygen_required = Column(Boolean, default=False)
    cardiac_monitor_required = Column(Boolean, default=False)
    stretcher_required = Column(Boolean, default=False)
    iv_pump_required = Column(Boolean, default=False)
    defibrillator_required = Column(Boolean, default=False)
    ventilator_required = Column(Boolean, default=False)
    balloon_pump_required = Column(Boolean, default=False)
    ecmo_required = Column(Boolean, default=False)
    suction_required = Column(Boolean, default=False)
    incubator_required = Column(Boolean, default=False)
    
    # Medical equipment list (JSON field for flexibility)
    medical_equipment = Column(JSON, default=list)
    
    # Status field mapping for notification system
    quote_status = Column(String(30), default='pending')  # pending, quoted, booked, expired
    return_flight_needed = Column(Boolean, default=False)
    
    # Quote metadata
    status = Column(String(30), default='submitted')  # submitted, quotes_received, selected, expired
    quote_expiry = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_demo_data = Column(Boolean, default=False)
    
    def __repr__(self):
        return f'<Quote {self.ref_id} - {self.contact_name}>'

class Commission(db.Model):
    """Commission tracking for completed bookings"""
    __tablename__ = 'commissions'
    
    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)
    
    # Commission calculation
    booking_total_usd = Column(Float, nullable=False)
    commission_percent = Column(Float, nullable=False)  # 0.04 or 0.05
    commission_amount_usd = Column(Float, nullable=False)
    
    # Payment tracking
    invoice_number = Column(String(50))
    invoice_generated_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    payment_method = Column(String(50))  # ach, check, wire
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_demo_data = Column(Boolean, default=False)
    
    # Relationships
    booking = relationship("Booking", back_populates="commissions")
    affiliate = relationship("Affiliate", back_populates="commissions")
    
    def __repr__(self):
        return f'<Commission {self.id} - ${self.commission_amount_usd}>'

class AffiliateNiche(db.Model):
    """Many-to-many relationship between affiliates and niches"""
    __tablename__ = 'affiliate_niches'
    
    id = Column(Integer, primary_key=True)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)
    niche_id = Column(Integer, ForeignKey('niches.id'), nullable=False)
    specialization_level = Column(String(20), default='standard')  # standard, expert, exclusive
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    affiliate = relationship("Affiliate", back_populates="affiliate_niches")
    niche = relationship("Niche", back_populates="affiliate_niches")
    
    def __repr__(self):
        return f'<AffiliateNiche {self.affiliate_id}-{self.niche_id}>'

class Announcement(db.Model):
    """System announcements and banners"""
    __tablename__ = 'announcements'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    style = Column(String(20), default='info')  # info, warning, success, danger
    is_active = Column(Boolean, default=True)
    
    # Countdown functionality
    countdown_target = Column(DateTime, nullable=True)
    countdown_display = Column(String(100), nullable=True)
    countdown_expired = Column(Boolean, default=False)
    
    # Targeting
    target_roles = Column(JSON)  # Array of roles to show to
    priority = Column(Integer, default=1)  # Higher = more important
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Announcement {self.title}>'

class SecurityEvent(db.Model):
    """Security events and audit log"""
    __tablename__ = 'security_events'
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False)  # login_success, login_fail, logout, admin_action
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    username = Column(String(64))  # Store username for deleted users
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    additional_data = Column(JSON)  # Extra context
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", backref="security_events")
    
    def __repr__(self):
        return f'<SecurityEvent {self.event_type} - {self.username}>'