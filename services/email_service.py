import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from flask import current_app
# Will import models from quote_app context

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.enabled = self._check_config()
        if not self.enabled:
            logger.warning("[MAIL] Email service disabled: Missing configuration")
    
    def _check_config(self):
        """Check if all required email configuration is present"""
        required_vars = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD']
        return all(os.environ.get(var) for var in required_vars)
    
    def is_enabled(self):
        return self.enabled
    
    def send_email(self, recipient, subject, html_body, template_name, quote_id=None):
        """Send email and log the result"""
        if not self.enabled:
            self._log_email(recipient, subject, template_name, 'FAILED', 
                          error_message='Email service not configured', quote_id=quote_id)
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr(('SkyCareLink', os.environ.get('MAIL_USERNAME')))
            msg['To'] = recipient
            
            # Add HTML content
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(os.environ.get('MAIL_SERVER'), int(os.environ.get('MAIL_PORT', 587)))
            server.starttls()
            server.login(os.environ.get('MAIL_USERNAME'), os.environ.get('MAIL_PASSWORD'))
            
            response = server.send_message(msg)
            server.quit()
            
            self._log_email(recipient, subject, template_name, 'SENT', 
                          smtp_response=str(response), quote_id=quote_id)
            
            # Log audit event
            self._log_audit_event(f'email_sent_{template_name}', 
                                f'Email sent to {recipient}: {subject}', quote_id=quote_id)
            
            logger.info(f"[MAIL] Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            self._log_email(recipient, subject, template_name, 'FAILED', 
                          error_message=error_msg, quote_id=quote_id)
            
            self._log_audit_event('email_send_failed', 
                                f'Failed to send email to {recipient}: {error_msg}', quote_id=quote_id)
            
            logger.error(f"[MAIL] Failed to send email to {recipient}: {error_msg}")
            return False
    
    def _log_email(self, recipient, subject, template, status, smtp_response=None, error_message=None, quote_id=None):
        """Log email attempt to database"""
        try:
            from quote_app import db, EmailLog
            email_log = EmailLog(
                recipient=recipient,
                subject=subject,
                template=template,
                status=status,
                smtp_response=smtp_response,
                error_message=error_message,
                quote_id=quote_id
            )
            db.session.add(email_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log email: {e}")
            try:
                from quote_app import db
                db.session.rollback()
            except:
                pass
    
    def _log_audit_event(self, action, details, quote_id=None, user_id=None):
        """Log audit event"""
        try:
            from quote_app import db, AuditLog
            audit_log = AuditLog(
                action=action,
                details=details,
                quote_id=quote_id,
                user_id=user_id
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            try:
                from quote_app import db
                db.session.rollback()
            except:
                pass

# Email templates
class EmailTemplates:
    @staticmethod
    def verification_email(verification_token, portal_base):
        verify_url = f"{portal_base}/verify?token={verification_token}"
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">Welcome to SkyCareLink</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">Verify your account to get started</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    Thank you for joining SkyCareLink! To complete your registration and start accessing our medical transport services, please verify your email address.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Verify Your Account
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    If the button doesn't work, copy and paste this link into your browser:
                    <br><br>
                    <code style="background: #f5f5f5; padding: 10px; display: block; word-break: break-all;">{verify_url}</code>
                </p>
                
                <p style="font-size: 12px; color: #999; margin-top: 30px; border-top: 1px solid #e0e0e0; padding-top: 20px;">
                    This verification link will expire in 24 hours. If you didn't create an account with SkyCareLink, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def quote_request_confirmation(quote_ref, quote_id, portal_base):
        results_url = f"{portal_base}/quote/{quote_id}/results"
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">Quote Request Received</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">Reference: {quote_ref}</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    Thank you for your quote request! We've received your medical transport request and our affiliate partners are reviewing it now.
                </p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #667eea;">Quote Reference</h3>
                    <p style="margin: 0; font-size: 18px; font-weight: bold; color: #333;">{quote_ref}</p>
                </div>
                
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    You'll receive email notifications as quotes become available. You can also check your results anytime using the link below.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{results_url}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        View Quote Results
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Direct link: <code style="background: #f5f5f5; padding: 5px; word-break: break-all;">{results_url}</code>
                </p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def affiliate_quote_request(quote_ref, quote_id, pickup, destination, transport_date, portal_base):
        quote_url = f"{portal_base}/affiliate/quote/{quote_id}"
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">New SkyCareLink Quote</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">Reference: {quote_ref}</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    A new medical transport quote request is available for your review and pricing.
                </p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin: 0 0 15px 0; color: #667eea;">Transport Details</h3>
                    <p style="margin: 5px 0;"><strong>From:</strong> {pickup}</p>
                    <p style="margin: 5px 0;"><strong>To:</strong> {destination}</p>
                    <p style="margin: 5px 0;"><strong>Date:</strong> {transport_date}</p>
                    <p style="margin: 5px 0;"><strong>Reference:</strong> {quote_ref}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{quote_url}" style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Provide Quote
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Direct link: <code style="background: #f5f5f5; padding: 5px; word-break: break-all;">{quote_url}</code>
                </p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def quote_ready_notification(quote_ref, quote_id, price, portal_base):
        results_url = f"{portal_base}/quote/{quote_id}/results"
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">Your Quote is Ready</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">Reference: {quote_ref}</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    Great news! We've received a quote for your medical transport request.
                </p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                    <h3 style="margin: 0 0 10px 0; color: #667eea;">Quoted Price</h3>
                    <p style="margin: 0; font-size: 28px; font-weight: bold; color: #28a745;">${price:,.2f}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{results_url}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        View Full Quote & Book
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Direct link: <code style="background: #f5f5f5; padding: 5px; word-break: break-all;">{results_url}</code>
                </p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def booking_confirmed_individual(quote_ref):
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">Booking Confirmed!</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">Reference: {quote_ref}</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    Congratulations! Your medical transport booking has been confirmed. Our affiliate partner will contact you shortly with next steps.
                </p>
                
                <div style="background: #d4edda; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #28a745;">
                    <h3 style="margin: 0 0 10px 0; color: #155724;">What's Next?</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #155724;">
                        <li>Our partner will contact you within 24 hours</li>
                        <li>They'll coordinate pickup details and timing</li>
                        <li>All medical requirements will be confirmed</li>
                        <li>You'll receive a final itinerary before transport</li>
                    </ul>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Keep this confirmation email for your records. Reference number: <strong>{quote_ref}</strong>
                </p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def booking_confirmed_affiliate(quote_ref):
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">Quote Accepted!</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">Reference: {quote_ref}</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    Excellent! Your quote has been accepted by the customer. Please proceed with coordinating the medical transport.
                </p>
                
                <div style="background: #d4edda; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #28a745;">
                    <h3 style="margin: 0 0 10px 0; color: #155724;">Next Steps</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #155724;">
                        <li>Contact the customer within 24 hours</li>
                        <li>Coordinate pickup logistics and timing</li>
                        <li>Confirm all medical requirements</li>
                        <li>Provide final transport itinerary</li>
                    </ul>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Transport reference: <strong>{quote_ref}</strong>
                </p>
            </div>
        </body>
        </html>
        """

# Global email service instance
email_service = EmailService()