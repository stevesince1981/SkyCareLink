import os
import logging
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from consumer_main_final import db

# Configure logging
logger = logging.getLogger(__name__)

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Check if database is available
DB_AVAILABLE = True
try:
    from models.affiliate import Affiliate
except ImportError:
    DB_AVAILABLE = False
    logger.warning("Admin models not available - admin features will be limited")

# Email service imports
try:
    from services.mailer import EmailService
    from services.mailer import mail_service
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    logger.warning("Email service not available - email features will be disabled")

@admin_bp.route('/cofounders')
def cofounders():
    """Co-founders management dashboard"""
    try:
        affiliates = []
        stats = {
            'total_affiliates': 0,
            'fully_paid': 0,
            'partial_paid': 0,
            'total_collected': 0
        }
        
        if DB_AVAILABLE:
            affiliates = Affiliate.query.order_by(Affiliate.created_at.desc()).all()
            
            # Calculate statistics
            stats['total_affiliates'] = len(affiliates)
            for affiliate in affiliates:
                if affiliate.buy_in_paid:
                    stats['fully_paid'] += 1
                elif affiliate.buy_in_paid_total > 0:
                    stats['partial_paid'] += 1
                
                stats['total_collected'] += float(affiliate.buy_in_paid_total or 0)
        
        # Demo data if no database
        if not affiliates and not DB_AVAILABLE:
            from datetime import datetime, timedelta
            affiliates = [
                type('Affiliate', (), {
                    'id': 1,
                    'company_name': 'AeroMed Partners',
                    'contact_name': 'Dr. Sarah Johnson',
                    'email': 'sarah.johnson@aeromed.com',
                    'phone': '(555) 123-4567',
                    'is_active': True,
                    'buy_in_required_total': 5000.00,
                    'buy_in_paid_total': 5000.00,
                    'buy_in_paid': True,
                    'buy_in_paid_date': datetime.now() - timedelta(days=30),
                    'verification_email_sent': True,
                    'verification_email_sent_date': datetime.now() - timedelta(days=35),
                    'welcome_email_sent': True,
                    'welcome_email_sent_date': datetime.now() - timedelta(days=30),
                    'terms_understood_timestamp': datetime.now() - timedelta(days=29),
                    'buy_in_percent_complete': 100,
                    'buy_in_remaining': 0,
                    'get_payment_history': lambda: [
                        {'amount': 2500.00, 'date': '2025-01-15', 'method': 'check', 'notes': 'Initial payment'},
                        {'amount': 2500.00, 'date': '2025-02-01', 'method': 'wire', 'notes': 'Final payment'}
                    ],
                    'can_send_welcome_email': lambda: False
                }),
                type('Affiliate', (), {
                    'id': 2,
                    'company_name': 'MedFlight Solutions',
                    'contact_name': 'Michael Chen',
                    'email': 'michael.chen@medflight.com',
                    'phone': '(555) 987-6543',
                    'is_active': False,
                    'buy_in_required_total': 5000.00,
                    'buy_in_paid_total': 2500.00,
                    'buy_in_paid': False,
                    'buy_in_paid_date': None,
                    'verification_email_sent': True,
                    'verification_email_sent_date': datetime.now() - timedelta(days=10),
                    'welcome_email_sent': False,
                    'welcome_email_sent_date': None,
                    'terms_understood_timestamp': None,
                    'buy_in_percent_complete': 50,
                    'buy_in_remaining': 2500.00,
                    'get_payment_history': lambda: [
                        {'amount': 2500.00, 'date': '2025-02-10', 'method': 'ach', 'notes': 'Partial payment'}
                    ],
                    'can_send_welcome_email': lambda: False
                })
            ]
            stats = {
                'total_affiliates': 2,
                'fully_paid': 1,
                'partial_paid': 1,
                'total_collected': 7500.00
            }
        
        return render_template('admin/cofounders.html', affiliates=affiliates, stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading co-founders dashboard: {str(e)}")
        flash('Error loading co-founders data.', 'error')
        return render_template('admin/cofounders.html', affiliates=[], stats={})

@admin_bp.route('/cofounders/add', methods=['POST'])
def add_cofounder():
    """Add a new co-founder"""
    try:
        if not DB_AVAILABLE:
            flash('Database not available. Cannot add co-founder.', 'error')
            return redirect(url_for('admin.cofounders'))
        
        # Extract form data
        company_name = request.form.get('company_name', '').strip()
        contact_name = request.form.get('contact_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        buy_in_required_total = request.form.get('buy_in_required_total', '5000.00')
        
        # Validation
        if not company_name or not contact_name or not email:
            flash('Company name, contact name, and email are required.', 'error')
            return redirect(url_for('admin.cofounders'))
        
        # Check for duplicate email
        existing = Affiliate.query.filter_by(email=email).first()
        if existing:
            flash('An affiliate with this email already exists.', 'error')
            return redirect(url_for('admin.cofounders'))
        
        # Create new affiliate
        affiliate = Affiliate(
            company_name=company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            buy_in_required_total=Decimal(buy_in_required_total)
        )
        
        db.session.add(affiliate)
        db.session.commit()
        
        logger.info(f"New co-founder added: {company_name} ({email})")
        flash(f'Co-founder {company_name} added successfully!', 'success')
        
        return redirect(url_for('admin.cofounders'))
        
    except ValueError as e:
        flash('Invalid buy-in amount. Please enter a valid number.', 'error')
        return redirect(url_for('admin.cofounders'))
    except Exception as e:
        logger.error(f"Error adding co-founder: {str(e)}")
        if DB_AVAILABLE:
            db.session.rollback()
        flash('An error occurred while adding the co-founder.', 'error')
        return redirect(url_for('admin.cofounders'))

@admin_bp.route('/cofounders/add-payment/<int:affiliate_id>', methods=['POST'])
def add_payment(affiliate_id):
    """Add a payment to an affiliate's buy-in"""
    try:
        if not DB_AVAILABLE:
            flash('Database not available. Cannot process payment.', 'error')
            return redirect(url_for('admin.cofounders'))
        
        affiliate = Affiliate.query.get_or_404(affiliate_id)
        
        # Extract form data
        amount = request.form.get('amount', '').strip()
        payment_method = request.form.get('payment_method', 'manual')
        notes = request.form.get('notes', '').strip()
        
        # Validation
        try:
            amount_value = float(amount)
            if amount_value <= 0:
                raise ValueError("Amount must be positive")
            if amount_value > affiliate.buy_in_remaining:
                raise ValueError("Amount exceeds remaining balance")
        except ValueError as e:
            flash(f'Invalid payment amount: {str(e)}', 'error')
            return redirect(url_for('admin.cofounders'))
        
        # Add payment
        affiliate.add_payment(amount_value, payment_method, notes)
        db.session.commit()
        
        # Log the payment
        logger.info(f"Payment added for {affiliate.company_name}: ${amount_value} via {payment_method}")
        
        # Flash message with status
        if affiliate.buy_in_paid:
            flash(f'Payment of ${amount_value:,.2f} added! {affiliate.company_name} is now fully paid.', 'success')
        else:
            remaining = affiliate.buy_in_remaining
            flash(f'Payment of ${amount_value:,.2f} added! ${remaining:,.2f} remaining for full buy-in.', 'success')
        
        return redirect(url_for('admin.cofounders'))
        
    except Exception as e:
        logger.error(f"Error adding payment for affiliate {affiliate_id}: {str(e)}")
        if DB_AVAILABLE:
            db.session.rollback()
        flash('An error occurred while processing the payment.', 'error')
        return redirect(url_for('admin.cofounders'))

@admin_bp.route('/cofounders/toggle-active/<int:affiliate_id>', methods=['POST'])
def toggle_active_status(affiliate_id):
    """Toggle affiliate active status"""
    try:
        if not DB_AVAILABLE:
            flash('Database not available. Cannot update status.', 'error')
            return redirect(url_for('admin.cofounders'))
        
        affiliate = Affiliate.query.get_or_404(affiliate_id)
        
        # Toggle status
        affiliate.is_active = not affiliate.is_active
        affiliate.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        status = "activated" if affiliate.is_active else "deactivated"
        logger.info(f"Affiliate {affiliate.company_name} {status}")
        flash(f'{affiliate.company_name} has been {status}.', 'success')
        
        return redirect(url_for('admin.cofounders'))
        
    except Exception as e:
        logger.error(f"Error toggling status for affiliate {affiliate_id}: {str(e)}")
        if DB_AVAILABLE:
            db.session.rollback()
        flash('An error occurred while updating the status.', 'error')
        return redirect(url_for('admin.cofounders'))

@admin_bp.route('/cofounders/send-verification/<int:affiliate_id>', methods=['POST'])
def send_verification_email(affiliate_id):
    """Send verification email to affiliate"""
    try:
        if not DB_AVAILABLE:
            flash('Database not available.', 'error')
            return redirect(url_for('admin.cofounders'))
        
        affiliate = Affiliate.query.get_or_404(affiliate_id)
        
        # Send verification email
        email_sent = False
        if EMAIL_AVAILABLE:
            try:
                # Prepare verification email content
                remaining_amount = affiliate.buy_in_remaining
                paid_amount = affiliate.buy_in_paid_total
                
                subject = f"SkyCareLink Partnership Verification - {affiliate.company_name}"
                
                # Email body with buy-in details
                body = f"""
Dear {affiliate.contact_name},

Thank you for your interest in joining SkyCareLink as a co-founding partner.

**Buy-in Status:**
- Required Amount: ${affiliate.buy_in_required_total:,.2f}
- Amount Paid: ${paid_amount:,.2f}
- Remaining: ${remaining_amount:,.2f}

{'Your buy-in is complete!' if affiliate.buy_in_paid else 'Please complete your buy-in payment to activate your partnership.'}

**Next Steps:**
1. Review the partnership agreement
2. {'Complete remaining payment' if not affiliate.buy_in_paid else 'Await welcome email and account activation'}
3. Access your affiliate dashboard once activated

If you have any questions about your partnership or payment, please contact our team.

Best regards,
The SkyCareLink Team

---
This is an automated message from SkyCareLink Partnership Management.
"""
                
                # Send email (simplified - in production would use proper email template)
                email_sent = mail_service.send_email(
                    to_email=affiliate.email,
                    subject=subject,
                    body=body
                )
                
                if email_sent:
                    # Update email tracking
                    affiliate.verification_email_sent = True
                    affiliate.verification_email_sent_date = datetime.utcnow()
                    affiliate.updated_at = datetime.utcnow()
                    db.session.commit()
                    
                    logger.info(f"Verification email sent to {affiliate.email}")
                    flash(f'Verification email sent to {affiliate.company_name}!', 'success')
                else:
                    flash('Failed to send verification email. Please check email configuration.', 'error')
                    
            except Exception as e:
                logger.error(f"Error sending verification email: {str(e)}")
                flash('Error sending verification email.', 'error')
        else:
            # Email not available - log the attempt
            logger.info(f"Verification email attempted for {affiliate.company_name} (email service unavailable)")
            flash(f'Verification email logged for {affiliate.company_name} (email service unavailable).', 'warning')
        
        return redirect(url_for('admin.cofounders'))
        
    except Exception as e:
        logger.error(f"Error processing verification email for affiliate {affiliate_id}: {str(e)}")
        flash('An error occurred while sending the verification email.', 'error')
        return redirect(url_for('admin.cofounders'))

@admin_bp.route('/cofounders/send-welcome/<int:affiliate_id>', methods=['POST'])
def send_welcome_email(affiliate_id):
    """Send welcome email to fully paid affiliate"""
    try:
        if not DB_AVAILABLE:
            flash('Database not available.', 'error')
            return redirect(url_for('admin.cofounders'))
        
        affiliate = Affiliate.query.get_or_404(affiliate_id)
        
        # Check if affiliate can receive welcome email
        if not affiliate.can_send_welcome_email():
            flash('Welcome email can only be sent to fully paid affiliates who haven\'t received it yet.', 'error')
            return redirect(url_for('admin.cofounders'))
        
        # Send welcome email
        email_sent = False
        if EMAIL_AVAILABLE:
            try:
                subject = f"Welcome to SkyCareLink Partnership - {affiliate.company_name} Active!"
                
                # Welcome email body
                body = f"""
Dear {affiliate.contact_name},

Congratulations! Your SkyCareLink partnership is now ACTIVE!

**Partnership Details:**
- Company: {affiliate.company_name}
- Status: ACTIVE PARTNER
- Buy-in: ${affiliate.buy_in_required_total:,.2f} (PAID IN FULL)
- Activation Date: {datetime.utcnow().strftime('%B %d, %Y')}

**Your Partnership Benefits:**
✓ Access to SkyCareLink affiliate dashboard
✓ Quote management and booking system
✓ Revenue sharing from successful bookings
✓ Priority booking notifications
✓ Marketing and operational support

**Getting Started:**
1. Log in to your affiliate dashboard at: {request.url_root}affiliate/dashboard
2. Configure your call center settings
3. Set up quote preferences and coverage areas
4. Begin receiving booking requests immediately

**Important:** Please review and accept the partnership terms when you first log in to complete your account setup.

We're excited to have you as part of the SkyCareLink network!

Best regards,
The SkyCareLink Partnership Team

---
Partnership ID: {affiliate.id}
Activation: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
                
                # Send welcome email
                email_sent = mail_service.send_email(
                    to_email=affiliate.email,
                    subject=subject,
                    body=body
                )
                
                if email_sent:
                    # Update email tracking and activate
                    affiliate.welcome_email_sent = True
                    affiliate.welcome_email_sent_date = datetime.utcnow()
                    affiliate.is_active = True  # Activate with welcome email
                    affiliate.status = 'active'
                    affiliate.updated_at = datetime.utcnow()
                    db.session.commit()
                    
                    logger.info(f"Welcome email sent to {affiliate.email} - Partnership activated")
                    flash(f'Welcome email sent and {affiliate.company_name} activated!', 'success')
                else:
                    flash('Failed to send welcome email. Please check email configuration.', 'error')
                    
            except Exception as e:
                logger.error(f"Error sending welcome email: {str(e)}")
                flash('Error sending welcome email.', 'error')
        else:
            # Email not available - still activate if fully paid
            affiliate.is_active = True
            affiliate.status = 'active'
            affiliate.welcome_email_sent = True  # Mark as sent for tracking
            affiliate.welcome_email_sent_date = datetime.utcnow()
            affiliate.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Welcome process completed for {affiliate.company_name} (email service unavailable)")
            flash(f'{affiliate.company_name} activated successfully (email service unavailable).', 'success')
        
        return redirect(url_for('admin.cofounders'))
        
    except Exception as e:
        logger.error(f"Error processing welcome email for affiliate {affiliate_id}: {str(e)}")
        if DB_AVAILABLE:
            db.session.rollback()
        flash('An error occurred while sending the welcome email.', 'error')
        return redirect(url_for('admin.cofounders'))

# Terms acceptance route for affiliates
@admin_bp.route('/affiliate/accept-terms', methods=['POST'])
def accept_terms():
    """Record affiliate terms acceptance (called from affiliate dashboard)"""
    try:
        if not DB_AVAILABLE:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        # Get affiliate from session or form data
        affiliate_id = session.get('affiliate_id') or request.form.get('affiliate_id')
        
        if not affiliate_id:
            return jsonify({'success': False, 'error': 'Affiliate not identified'})
        
        affiliate = Affiliate.query.get(affiliate_id)
        if not affiliate:
            return jsonify({'success': False, 'error': 'Affiliate not found'})
        
        # Record terms acceptance (only once)
        accepted = affiliate.record_terms_acceptance()
        
        if accepted:
            db.session.commit()
            logger.info(f"Terms accepted by {affiliate.company_name}")
            return jsonify({
                'success': True, 
                'message': 'Terms acceptance recorded',
                'timestamp': affiliate.terms_understood_timestamp.isoformat()
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Terms already accepted',
                'timestamp': affiliate.terms_understood_timestamp.isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error recording terms acceptance: {str(e)}")
        if DB_AVAILABLE:
            db.session.rollback()
        return jsonify({'success': False, 'error': 'Internal server error'})