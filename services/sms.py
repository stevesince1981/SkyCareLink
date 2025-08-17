"""
SMS service for SkyCareLink notifications using Twilio
Supports conditional enabling via ENABLE_SMS flag
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.enabled = os.environ.get('ENABLE_SMS', 'false').lower() == 'true'
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        if self.enabled:
            if not all([self.account_sid, self.auth_token, self.phone_number]):
                logger.warning("SMS disabled: Missing Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_PHONE_NUMBER)")
                self.enabled = False
            else:
                try:
                    from twilio.rest import Client
                    self.client = Client(self.account_sid, self.auth_token)
                    logger.info("SMS service enabled with Twilio")
                except ImportError:
                    logger.error("SMS disabled: Twilio library not installed")
                    self.enabled = False
                except Exception as e:
                    logger.error(f"SMS disabled: Twilio initialization failed - {str(e)}")
                    self.enabled = False
        else:
            logger.info("SMS disabled via ENABLE_SMS=false")

    def send_sms(self, to_phone: str, message: str) -> bool:
        """
        Send SMS message
        Returns True if successful, False otherwise
        """
        if not self.enabled:
            logger.info(f"[SMS disabled] Would send to {to_phone}: {message}")
            return False

        try:
            # Ensure phone number is in E.164 format
            if not to_phone.startswith('+'):
                # Assume US number if no country code
                if len(to_phone) == 10:
                    to_phone = f"+1{to_phone}"
                elif len(to_phone) == 11 and to_phone.startswith('1'):
                    to_phone = f"+{to_phone}"
                else:
                    logger.error(f"Invalid phone number format: {to_phone}")
                    return False

            message_obj = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_phone
            )

            logger.info(f"SMS sent successfully to {to_phone}, SID: {message_obj.sid}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {str(e)}")
            return False

    def send_quote_ready_sms(self, to_phone: str, quote_ref: str, price: str, 
                            provider_name: Optional[str], results_url: str) -> bool:
        """Send quote ready SMS notification"""
        provider_text = provider_name if provider_name else "your provider"
        
        message = (
            f"SkyCareLink: Quote ready. {price} from {provider_text}. "
            f"Valid 7 days. {results_url}"
        )
        
        return self.send_sms(to_phone, message)

    def send_booking_confirmed_sms(self, to_phone: str, booking_ref: str, 
                                  provider_name: str, flight_date: str, booking_url: str) -> bool:
        """Send booking confirmation SMS"""
        message = (
            f"SkyCareLink: Booking confirmed! #{booking_ref} with {provider_name} "
            f"on {flight_date}. Details: {booking_url}"
        )
        
        return self.send_sms(to_phone, message)

# Global instance
sms_service = SMSService()