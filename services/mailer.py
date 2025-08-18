"""
Email service for SkyCareLink using Outlook SMTP
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from models import EmailLog, QuoteRequest
from app import db

logger = logging.getLogger(__name__)

class MailService:
    def __init__(self):
        self.smtp_server = "smtp.office365.com"
        self.smtp_port = 587
        self.username = os.environ.get("MAIL_USERNAME")
        self.password = os.environ.get("MAIL_PASSWORD")
        self.default_sender = os.environ.get("MAIL_DEFAULT_SENDER", f"SkyCareLink <{self.username}>")
        self.portal_base = os.environ.get("PORTAL_BASE", "https://your-app.replit.app")
        
        self.enabled = bool(self.username and self.password)
        if not self.enabled:
            logger.warning("[MAIL disabled] - MAIL_USERNAME or MAIL_PASSWORD not configured")
    
    def send_email(self, recipient, subject, body_html, email_type):
        """Send email and log the result"""
        if not self.enabled:
            logger.warning(f"Email disabled, cannot send to {recipient}: {subject}")
            self._log_email(recipient, subject, email_type, "FAILED", "Mail service disabled")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.default_sender
            msg['To'] = recipient
            
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {recipient}: {subject}")
            self._log_email(recipient, subject, email_type, "SENT", "Successfully sent")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email to {recipient}: {error_msg}")
            self._log_email(recipient, subject, email_type, "FAILED", error_msg)
            return False
    
    def _log_email(self, recipient, subject, email_type, status, response):
        """Log email attempt to database"""
        try:
            email_log = EmailLog(
                recipient=recipient,
                subject=subject,
                email_type=email_type,
                status=status,
                smtp_response=response,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(email_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log email: {e}")
    
    def send_verification_email(self, user, token):
        """Send email verification"""
        verify_url = f"{self.portal_base}/verify?token={token}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1976D2;">Welcome to SkyCareLink!</h2>
                <p>Hi {user.username},</p>
                <p>Thank you for registering with SkyCareLink. Please verify your email address to complete your registration.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" 
                       style="background: #1976D2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 3px;">
                    {verify_url}
                </p>
                
                <p>If you didn't create an account with SkyCareLink, please ignore this email.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    SkyCareLink - Medical Transport Services<br>
                    This is an automated message, please do not reply.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            user.email,
            "Verify your SkyCareLink account",
            html_body,
            "verification"
        )

    def send_welcome_email(self, user, user_type="individual"):
        """Send welcome email after successful registration"""
        user_type_titles = {
            'family': 'Individual/Family',
            'affiliate': 'Transport Affiliate', 
            'hospital': 'Healthcare Provider'
        }
        
        user_type_title = user_type_titles.get(user_type, 'Individual/Family')
        name = getattr(user, 'contact_name', user.username)
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1976D2;">🚁 Welcome to SkyCareLink!</h2>
                <p>Hi {name},</p>
                <p>Your <strong>{user_type_title}</strong> account has been successfully created!</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1976D2; margin-top: 0;">Your Account Details:</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Username:</strong> {user.email}</li>
                        <li><strong>Email:</strong> {user.email}</li>
                        <li><strong>Account Type:</strong> {user_type_title}</li>
                    </ul>
                </div>
                
                <h3 style="color: #1976D2;">What's Next?</h3>
                <p>You're now ready to access all SkyCareLink features:</p>
                <ul>
                    <li>✈️ Request medical transport services</li>
                    <li>📋 Compare qualified providers instantly</li>
                    <li>💬 Get AI-assisted transport planning</li>
                    <li>📱 Track your requests in real-time</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.portal_base}" 
                       style="background: #1976D2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Access Your Dashboard
                    </a>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    SkyCareLink - Medical Transport Services<br>
                    Need help? Contact us at support@skycarelink.com<br>
                    This is an automated message, please do not reply.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            user.email,
            "Welcome to SkyCareLink - Account Created Successfully!",
            html_body,
            "welcome"
        )
    
    def send_quote_request_confirmation(self, user, quote):
        """Send confirmation to individual that quote request was received"""
        results_url = f"{self.portal_base}/quote_results/{quote.booking_id}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1976D2;">Quote Request Received</h2>
                <p>Hi {user.username},</p>
                <p>Your quote request has been received and sent to our transport affiliates.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Reference Number:</strong> {quote.booking_id}<br>
                    <strong>Route:</strong> {quote.pickup_location} → {quote.destination}<br>
                    <strong>Transport Date:</strong> {quote.transport_date.strftime('%B %d, %Y')}
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{results_url}" 
                       style="background: #1976D2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Quote Status
                    </a>
                </div>
                
                <p>You can also check your quote status here:</p>
                <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 3px;">
                    {results_url}
                </p>
                
                <p>We'll notify you as soon as quotes become available.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    SkyCareLink - Medical Transport Services<br>
                    Reference: {quote.booking_id}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            user.email,
            f"Quote request received – Ref #{quote.booking_id}",
            html_body,
            "quote_request_confirmation"
        )
    
    def send_new_quote_notification(self, affiliate_user, quote):
        """Send notification to affiliate about new quote request"""
        quote_url = f"{self.portal_base}/affiliate/quote/{quote.booking_id}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1976D2;">New Quote Request</h2>
                <p>Hello,</p>
                <p>A new quote request has been submitted that matches your service area.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Reference:</strong> {quote.booking_id}<br>
                    <strong>Route:</strong> {quote.pickup_location} → {quote.destination}<br>
                    <strong>Transport Date:</strong> {quote.transport_date.strftime('%B %d, %Y')}<br>
                    {f'<strong>Patient Condition:</strong> {quote.patient_condition}<br>' if quote.patient_condition else ''}
                    {f'<strong>Special Requirements:</strong> {quote.special_requirements}<br>' if quote.special_requirements else ''}
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{quote_url}" 
                       style="background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Provide Quote
                    </a>
                </div>
                
                <p>Click the link above or visit:</p>
                <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 3px;">
                    {quote_url}
                </p>
                
                <p>Please respond promptly to maintain your response rate and priority in our system.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    SkyCareLink - Medical Transport Services<br>
                    Reference: {quote.booking_id}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            affiliate_user.email,
            f"New quote request – Provide Quote – Ref #{quote.booking_id}",
            html_body,
            "new_quote_notification"
        )
    
    def send_quote_ready_notification(self, user, quote):
        """Send notification to individual that quote is ready"""
        results_url = f"{self.portal_base}/quote_results/{quote.booking_id}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1976D2;">Your Quote is Ready!</h2>
                <p>Hi {user.username},</p>
                <p>Great news! We have a quote ready for your transport request.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Reference:</strong> {quote.booking_id}<br>
                    <strong>Route:</strong> {quote.pickup_location} → {quote.destination}<br>
                    <strong>Transport Date:</strong> {quote.transport_date.strftime('%B %d, %Y')}<br>
                    <strong>Quoted Price:</strong> ${quote.quoted_price:,.2f}
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{results_url}" 
                       style="background: #1976D2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Quote Details
                    </a>
                </div>
                
                <p>Click above or visit this link to review and confirm your booking:</p>
                <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 3px;">
                    {results_url}
                </p>
                
                <p>This quote is available for a limited time. Please review and confirm at your earliest convenience.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    SkyCareLink - Medical Transport Services<br>
                    Reference: {quote.booking_id}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            user.email,
            f"Your quote is ready – Ref #{quote.booking_id}",
            html_body,
            "quote_ready"
        )
    
    def send_booking_confirmation(self, user, quote):
        """Send booking confirmation to individual"""
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745;">Booking Confirmed!</h2>
                <p>Hi {user.username},</p>
                <p>Your medical transport booking has been confirmed. We're coordinating with your transport provider to ensure everything is ready for your scheduled date.</p>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Confirmation Number:</strong> {quote.booking_id}<br>
                    <strong>Route:</strong> {quote.pickup_location} → {quote.destination}<br>
                    <strong>Transport Date:</strong> {quote.transport_date.strftime('%B %d, %Y')}<br>
                    <strong>Final Price:</strong> ${quote.quoted_price:,.2f}<br>
                    <strong>Status:</strong> CONFIRMED
                </div>
                
                <p><strong>What's Next:</strong></p>
                <ul>
                    <li>Your transport provider will contact you 24-48 hours before your scheduled transport</li>
                    <li>Please have all necessary medical records and identification ready</li>
                    <li>If you need to make changes, contact us immediately</li>
                </ul>
                
                <p>Thank you for choosing SkyCareLink for your medical transport needs.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    SkyCareLink - Medical Transport Services<br>
                    Confirmation: {quote.booking_id}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            user.email,
            f"Booking confirmed – Ref #{quote.booking_id}",
            html_body,
            "booking_confirmation"
        )
    
    def send_quote_accepted_notification(self, affiliate_user, quote):
        """Send notification to affiliate that quote was accepted"""
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745;">Quote Accepted!</h2>
                <p>Hello,</p>
                <p>Congratulations! Your quote has been accepted and the booking is now confirmed.</p>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Booking Reference:</strong> {quote.booking_id}<br>
                    <strong>Route:</strong> {quote.pickup_location} → {quote.destination}<br>
                    <strong>Transport Date:</strong> {quote.transport_date.strftime('%B %d, %Y')}<br>
                    <strong>Confirmed Price:</strong> ${quote.quoted_price:,.2f}<br>
                    <strong>Status:</strong> CONFIRMED
                </div>
                
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Please contact the patient 24-48 hours before transport</li>
                    <li>Confirm pickup location and any special requirements</li>
                    <li>Ensure your team is prepared for the scheduled transport</li>
                </ul>
                
                <p>Thank you for being part of the SkyCareLink network!</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    SkyCareLink - Medical Transport Services<br>
                    Reference: {quote.booking_id}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            affiliate_user.email,
            f"Quote accepted – Ref #{quote.booking_id}",
            html_body,
            "quote_accepted"
        )

# Global mail service instance
mail_service = MailService()