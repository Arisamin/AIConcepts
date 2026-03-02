"""
SMS Notification Service for Appointment Confirmations

This module provides SMS notification capabilities when appointments are booked.
Uses Twilio as the SMS provider.

Setup:
1. Install Twilio: pip install twilio
2. Set environment variables:
   - TWILIO_ACCOUNT_SID: Your Twilio account SID
   - TWILIO_AUTH_TOKEN: Your Twilio auth token
   - TWILIO_FROM_NUMBER: The phone number to send from (format: +1234567890)
   - SMS_NOTIFICATION_TO: Your phone number to receive SMS (format: +1234567890)
   - SMS_ENABLED: Set to "true" to enable SMS notifications (default: false)

Get Twilio credentials at: https://www.twilio.com/console
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS notifications about appointments"""
    
    def __init__(self):
        """Initialize SMS service with Twilio credentials"""
        self.enabled = os.getenv("SMS_ENABLED", "false").lower() == "true"
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.to_number = os.getenv("SMS_NOTIFICATION_TO")
        
        self.client = None
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required credentials are configured"""
        if not self.enabled:
            logger.info("SMS notifications are disabled (SMS_ENABLED not set to 'true')")
            return
        
        missing = []
        if not self.account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not self.auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not self.from_number:
            missing.append("TWILIO_FROM_NUMBER")
        if not self.to_number:
            missing.append("SMS_NOTIFICATION_TO")
        
        if missing:
            logger.warning(
                f"SMS notifications enabled but missing credentials: {', '.join(missing)}. "
                f"SMS will be disabled. Set these environment variables to enable SMS."
            )
            self.enabled = False
            return
        
        try:
            from twilio.rest import Client
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("✓ SMS service initialized successfully")
        except ImportError:
            logger.warning(
                "SMS enabled but 'twilio' package not installed. "
                "Install with: pip install twilio"
            )
            self.enabled = False
    
    def send_appointment_confirmed(
        self,
        appointment_date: Optional[str] = None,
        appointment_time: Optional[str] = None,
        doctor_name: Optional[str] = None,
        specialty: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send SMS notification that appointment has been confirmed
        
        Args:
            appointment_date: Date of appointment (e.g., "01.06.2026")
            appointment_time: Time of appointment (e.g., "14:30")
            doctor_name: Name of doctor/specialist
            specialty: Medical specialty
        
        Returns:
            Dict with status and message
        """
        if not self.enabled or not self.client:
            logger.debug("SMS notifications disabled - skipping notification")
            return {"status": "disabled", "message": "SMS notifications disabled"}
        
        try:
            # Build message
            message_parts = ["✓ Appointment Confirmed!"]
            
            if appointment_date:
                message_parts.append(f"Date: {appointment_date}")
            if appointment_time:
                message_parts.append(f"Time: {appointment_time}")
            if specialty:
                message_parts.append(f"Specialty: {specialty}")
            if doctor_name:
                message_parts.append(f"Doctor: {doctor_name}")
            
            message_parts.append("Check your email for full details.")
            
            full_message = "\n".join(message_parts)
            
            # Send SMS
            message = self.client.messages.create(
                body=full_message,
                from_=self.from_number,
                to=self.to_number
            )
            
            logger.info(
                f"✓ SMS sent successfully (SID: {message.sid}) to {self.to_number}"
            )
            return {
                "status": "sent",
                "message_sid": message.sid,
                "to_number": self.to_number
            }
        
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return {
                "status": "error",
                "message": f"SMS sending failed: {str(e)}"
            }
    
    def send_appointment_found(
        self,
        appointment_date: Optional[str] = None,
        appointment_time: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send SMS notification that an available appointment has been found
        
        Args:
            appointment_date: Date of appointment (e.g., "01.06.2026")
            appointment_time: Time of appointment (e.g., "14:30")
        
        Returns:
            Dict with status and message
        """
        if not self.enabled or not self.client:
            logger.debug("SMS notifications disabled - skipping notification")
            return {"status": "disabled", "message": "SMS notifications disabled"}
        
        try:
            message_parts = ["🎉 Appointment Found!"]
            
            if appointment_date:
                message_parts.append(f"Date: {appointment_date}")
            if appointment_time:
                message_parts.append(f"Time: {appointment_time}")
            
            message_parts.append("Confirming booking now...")
            
            full_message = "\n".join(message_parts)
            
            message = self.client.messages.create(
                body=full_message,
                from_=self.from_number,
                to=self.to_number
            )
            
            logger.info(
                f"✓ Appointment found notification sent (SID: {message.sid})"
            )
            return {
                "status": "sent",
                "message_sid": message.sid
            }
        
        except Exception as e:
            logger.error(f"Failed to send appointment found SMS: {str(e)}")
            return {
                "status": "error",
                "message": f"SMS sending failed: {str(e)}"
            }
    
    def send_error_notification(self, error_message: str) -> Dict[str, any]:
        """
        Send SMS notification about an error
        
        Args:
            error_message: Description of the error
        
        Returns:
            Dict with status and message
        """
        if not self.enabled or not self.client:
            return {"status": "disabled"}
        
        try:
            full_message = f"❌ Appointment Booking Error:\n{error_message}"
            
            message = self.client.messages.create(
                body=full_message,
                from_=self.from_number,
                to=self.to_number
            )
            
            logger.info(f"✓ Error notification sent (SID: {message.sid})")
            return {
                "status": "sent",
                "message_sid": message.sid
            }
        
        except Exception as e:
            logger.error(f"Failed to send error SMS: {str(e)}")
            return {"status": "error"}


# Global SMS service instance
sms_service = SMSService()


def get_sms_service() -> SMSService:
    """Get the global SMS service instance"""
    return sms_service
