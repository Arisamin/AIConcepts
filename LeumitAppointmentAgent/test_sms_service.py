#!/usr/bin/env python3
"""
Quick SMS Service Test Script

Run this to verify SMS notifications are properly configured and working.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sms_service import get_sms_service


def main():
    print("=" * 70)
    print("SMS SERVICE CONFIGURATION TEST")
    print("=" * 70)
    print()
    
    sms = get_sms_service()
    
    print("Status Check:")
    print(f"  SMS Enabled: {sms.enabled}")
    print(f"  From Number: {sms.from_number}")
    print(f"  To Number:   {sms.to_number}")
    print(f"  Client Initialized: {sms.client is not None}")
    print()
    
    if not sms.enabled:
        print("❌ SMS notifications are DISABLED")
        print("   To enable, set SMS_ENABLED=true in your .env file")
        print("   See SMS_SETUP_GUIDE.md for detailed instructions")
        return 1
    
    if not sms.client:
        print("❌ SMS client not initialized")
        print("   Check that all Twilio credentials are set correctly:")
        print("   - TWILIO_ACCOUNT_SID")
        print("   - TWILIO_AUTH_TOKEN")
        print("   - TWILIO_FROM_NUMBER")
        print("   - SMS_NOTIFICATION_TO")
        return 1
    
    print("✓ Configuration looks good!")
    print()
    print("Testing SMS send...")
    print()
    
    # Send test SMS
    result = sms.send_appointment_confirmed(
        appointment_date="01.06.2026",
        appointment_time="14:30",
        doctor_name="Dr. Test",
        specialty="Cardiology"
    )
    
    print(f"Result: {result}")
    print()
    
    if result.get("status") == "sent":
        print("✓ SMS SENT SUCCESSFULLY!")
        print(f"  Message SID: {result.get('message_sid')}")
        print(f"  Sent to: {result.get('to_number')}")
        print()
        print("You should receive the SMS within 5 seconds.")
        return 0
    else:
        print(f"❌ Failed to send SMS: {result.get('message')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
