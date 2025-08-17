"""
Email service for SkyCareLink notifications using SMTP
Supports Outlook/Office365 with proper error handling
"""

import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.mail_server = os.environ.get('MAIL_SERVER', 'smtp-mail.outlook.com')
        self.mail_port = int(os.environ.get('MAIL_PORT', '587'))
        self.mail_username = os.environ.get('MAIL_USERNAME')
        self.mail_password = os.environ.get('MAIL_PASSWORD')
        self.mail_from = os.environ.get('MAIL_FROM', self.mail_username)
        self.mail_use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
        
        # Check if email is properly configured
        if not self.mail_username or not self.mail_password:
            logger.warning("Email disabled: MAIL_USERNAME or MAIL_PASSWORD not configured")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Email service configured with server: {self.mail_server}:{self.mail_port}")

    def send_email(self, to_emails: List[str], subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """
        Send HTML email with optional text fallback
        Returns True if successful, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email disabled - would send to {to_emails}: {subject}")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.mail_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            # Add text version if provided
            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))

            # Add HTML version
            msg.attach(MIMEText(html_body, 'html'))

            # Connect and send
            with smtplib.SMTP(self.mail_server, self.mail_port) as server:
                if self.mail_use_tls:
                    server.starttls()
                
                server.login(self.mail_username, self.mail_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_emails}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_emails}: {str(e)}")
            return False

    def send_affiliate_new_quote(self, affiliate_email: str, quote_ref: str, flight_date: str, 
                                from_location: str, to_location: str, quote_url: str) -> bool:
        """Send new quote notification to affiliate"""
        subject = f"New Quote Request #{quote_ref} - SkyCareLink"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1976d2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .quote-button {{ 
                    display: inline-block; 
                    background-color: #1976d2; 
                    color: white; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .details {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ padding: 10px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>SkyCareLink</h1>
                    <h2>New Quote Request</h2>
                </div>
                
                <div class="content">
                    <p>You have received a new medical transport quote request.</p>
                    
                    <div class="details">
                        <h3>Flight Details:</h3>
                        <p><strong>Reference:</strong> {quote_ref}</p>
                        <p><strong>Flight Date:</strong> {flight_date}</p>
                        <p><strong>From:</strong> {from_location}</p>
                        <p><strong>To:</strong> {to_location}</p>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{quote_url}" class="quote-button">PROVIDE QUOTE</a>
                    </div>
                    
                    <p><strong>Direct Link:</strong> <a href="{quote_url}">{quote_url}</a></p>
                    
                    <p>Please respond with your quote within 24 hours to ensure the best service for our client.</p>
                </div>
                
                <div class="footer">
                    <p>SkyCareLink - Professional Medical Transport Services</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        SkyCareLink - New Quote Request

        Reference: {quote_ref}
        Flight Date: {flight_date}
        From: {from_location}
        To: {to_location}

        Please provide your quote at: {quote_url}

        Thank you for your prompt response.
        """

        return self.send_email([affiliate_email], subject, html_body, text_body)

    def send_caller_quote_ready(self, caller_email: str, quote_ref: str, provider_name: str, 
                               price: str, results_url: str) -> bool:
        """Send quote ready notification to caller"""
        subject = f"Quote Ready #{quote_ref} - SkyCareLink"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .quote-button {{ 
                    display: inline-block; 
                    background-color: #28a745; 
                    color: white; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .price-box {{ 
                    background-color: #e8f5e8; 
                    border: 2px solid #28a745; 
                    padding: 20px; 
                    text-align: center; 
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .footer {{ padding: 10px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>SkyCareLink</h1>
                    <h2>Your Quote is Ready!</h2>
                </div>
                
                <div class="content">
                    <p>Great news! We've received a quote for your medical transport request.</p>
                    
                    <div class="price-box">
                        <h3>Quote Details</h3>
                        <p><strong>Provider:</strong> {provider_name}</p>
                        <p><strong>Price:</strong> {price}</p>
                        <p><strong>Reference:</strong> {quote_ref}</p>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{results_url}" class="quote-button">VIEW QUOTE DETAILS</a>
                    </div>
                    
                    <p><strong>Direct Link:</strong> <a href="{results_url}">{results_url}</a></p>
                    
                    <p><strong>Important:</strong> This quote is valid for 7 days. Please review and book promptly to secure your preferred transport.</p>
                </div>
                
                <div class="footer">
                    <p>SkyCareLink - Professional Medical Transport Services</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        SkyCareLink - Quote Ready

        Your quote is ready!

        Provider: {provider_name}
        Price: {price}
        Reference: {quote_ref}

        View details at: {results_url}

        This quote is valid for 7 days.
        """

        return self.send_email([caller_email], subject, html_body, text_body)

    def send_caller_booking_confirmed(self, caller_email: str, booking_ref: str, provider_name: str, 
                                    flight_date: str, booking_url: str) -> bool:
        """Send booking confirmation to caller"""
        subject = f"Booking Confirmed #{booking_ref} - SkyCareLink"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #17a2b8; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .confirmation-box {{ 
                    background-color: #e8f4f8; 
                    border: 2px solid #17a2b8; 
                    padding: 20px; 
                    text-align: center; 
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .booking-button {{ 
                    display: inline-block; 
                    background-color: #17a2b8; 
                    color: white; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{ padding: 10px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>SkyCareLink</h1>
                    <h2>Booking Confirmed!</h2>
                </div>
                
                <div class="content">
                    <p>Congratulations! Your medical transport booking has been confirmed.</p>
                    
                    <div class="confirmation-box">
                        <h3>✅ Booking Confirmed</h3>
                        <p><strong>Booking Reference:</strong> {booking_ref}</p>
                        <p><strong>Provider:</strong> {provider_name}</p>
                        <p><strong>Flight Date:</strong> {flight_date}</p>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{booking_url}" class="booking-button">VIEW BOOKING DETAILS</a>
                    </div>
                    
                    <p><strong>Direct Link:</strong> <a href="{booking_url}">{booking_url}</a></p>
                    
                    <p>Your provider will contact you directly within 24 hours with additional flight details and coordination information.</p>
                    
                    <p><strong>Need help?</strong> Contact our support team at any time.</p>
                </div>
                
                <div class="footer">
                    <p>SkyCareLink - Professional Medical Transport Services</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        SkyCareLink - Booking Confirmed

        Your booking is confirmed!

        Booking Reference: {booking_ref}
        Provider: {provider_name}
        Flight Date: {flight_date}

        View details at: {booking_url}

        Your provider will contact you within 24 hours.
        """

        return self.send_email([caller_email], subject, html_body, text_body)

    def send_password_reset_email(self, email, reset_url, expiry):
        """Send password reset email with secure token link"""
        subject = "SkyCareLink - Password Reset Request"
        
        html_body = f"""
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
            <div style="background-color: #007bff; color: white; padding: 20px; text-align: center;">
                <h2>🚁 SkyCareLink</h2>
                <h3>Password Reset Request</h3>
            </div>
            
            <div style="padding: 30px; background-color: #f8f9fa;">
                <p>Hello,</p>
                
                <p>We received a request to reset your password for your SkyCareLink account.</p>
                
                <div style="background-color: #fff; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <p><strong>Account Email:</strong> {email}</p>
                    <p><strong>Reset Link Expires:</strong> {expiry.strftime('%B %d, %Y at %I:%M %p UTC')}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Your Password</a>
                </div>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 20px 0;">
                    <h4 style="color: #856404; margin-top: 0;">🔒 Security Notice</h4>
                    <ul style="color: #856404; margin-bottom: 0;">
                        <li>This link will expire in 2 hours for your security</li>
                        <li>If you didn't request this reset, please ignore this email</li>
                        <li>Your current password remains unchanged until you complete the reset</li>
                        <li>Never share this link with anyone</li>
                    </ul>
                </div>
                
                <p>If the button above doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background-color: #f1f3f4; padding: 10px; border-radius: 4px;">
                    {reset_url}
                </p>
                
                <hr style="margin: 30px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    This email was sent to {email} because a password reset was requested for your SkyCareLink account.<br>
                    If you did not request this reset, please contact our support team immediately.<br><br>
                    
                    SkyCareLink - Professional Air Medical Transport Network<br>
                    This is an automated security email.
                </p>
            </div>
        </div>
        """
        
        return self.send_email([email], subject, html_body)
    
    def send_password_reset_confirmation(self, email):
        """Send confirmation email after password reset is completed"""
        from datetime import datetime
        
        subject = "SkyCareLink - Password Reset Completed"
        
        html_body = f"""
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
            <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
                <h2>🚁 SkyCareLink</h2>
                <h3>Password Reset Completed</h3>
            </div>
            
            <div style="padding: 30px; background-color: #f8f9fa;">
                <p>Hello,</p>
                
                <p><strong>Your password has been successfully reset.</strong></p>
                
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                    <h4 style="color: #155724; margin-top: 0;">✅ Password Updated</h4>
                    <p style="color: #155724; margin-bottom: 0;">
                        Your password was reset on {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}<br>
                        Account: {email}
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/login" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Sign In Now</a>
                </div>
                
                <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; padding: 15px; margin: 20px 0;">
                    <h4 style="color: #721c24; margin-top: 0;">🚨 Didn't Reset Your Password?</h4>
                    <p style="color: #721c24; margin-bottom: 0;">
                        If you didn't reset your password, your account may have been compromised. 
                        Please contact our support team immediately and change your password again.
                    </p>
                </div>
                
                <hr style="margin: 30px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    This is a security notification for account: {email}<br>
                    This email confirms that your password was successfully changed.<br><br>
                    
                    SkyCareLink - Professional Air Medical Transport Network<br>
                    This is an automated security email.
                </p>
            </div>
        </div>
        """
        
        return self.send_email([email], subject, html_body)

# Global instance
email_service = EmailService()