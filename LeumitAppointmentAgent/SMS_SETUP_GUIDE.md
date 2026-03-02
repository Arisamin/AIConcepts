# SMS Notification Setup Guide

This guide will help you set up SMS notifications so you receive a text message when an appointment is found and confirmed.

## Overview

The system uses **Twilio** to send SMS notifications. When an appointment is successfully booked, your phone will receive an SMS with the confirmation details.

## Step-by-Step Setup

### 1. Install Twilio Package

```bash
pip install twilio python-dotenv
```

### 2. Create a Twilio Account

1. Go to https://www.twilio.com/console
2. Sign up for a free Twilio account (you get $15 credit)
3. Verify your phone number
4. You'll see your **Account SID** and **Auth Token** on the dashboard

### 3. Get a Twilio Phone Number

1. In Twilio Console, go to **Phone Numbers** → **Manage Numbers**
2. Buy a phone number (choose any country/area code)
3. Copy the phone number (it will look like: `+1234567890`)

### 4. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your details:
   ```env
   SMS_ENABLED=true
   TWILIO_ACCOUNT_SID=your_account_sid_from_dashboard
   TWILIO_AUTH_TOKEN=your_auth_token_from_dashboard
   TWILIO_FROM_NUMBER=+1234567890  # Your Twilio phone number
   SMS_NOTIFICATION_TO=+1234567890 # Your personal phone number
   ```

### 5. Verify Your Phone Number (Important!)

⚠️ **For free Twilio accounts**, you must verify any phone number that will receive SMS.

1. In Twilio Console, go to **Verified Caller IDs**
2. Add your personal phone number
3. Twilio will send you a verification code via SMS
4. Confirm the code in the Twilio console

### 6. Test the Setup

Run this Python script to test if SMS is working:

```python
from sms_service import get_sms_service

sms = get_sms_service()
result = sms.send_appointment_confirmed(
    appointment_date="01.06.2026",
    appointment_time="14:30",
    doctor_name="Dr. Smith",
    specialty="Cardiology"
)
print(result)
```

You should receive an SMS within 5 seconds!

## SMS Message Examples

### Appointment Confirmed
```
✓ Appointment Confirmed!
Date: 01.06.2026
Time: 14:30
Specialty: Cardiology
Doctor: Dr. Smith
Check your email for full details.
```

### Appointment Found
```
🎉 Appointment Found!
Date: 01.06.2026
Time: 14:30
Confirming booking now...
```

## Troubleshooting

### Problem: "SMS notifications disabled"
**Solution**: Make sure `SMS_ENABLED=true` in your `.env` file

### Problem: Missing credentials error
**Solution**: Check all four environment variables are set correctly:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `SMS_NOTIFICATION_TO`

### Problem: "Phone number not verified"
**Solution**: For free Twilio accounts, you must verify the destination number first. Go to Twilio Console → Verified Caller IDs and add your phone number.

### Problem: SMS not received
**Solution**: 
1. Check Twilio Console → Message Logs to see delivery status
2. Verify your phone number can receive SMS (some carriers block Twilio)
3. Check your spam/junk folder
4. Try a different phone number

## Phone Number Format

Always use international format with country code:
- **USA/Canada**: `+1` (e.g., `+12025551234`)
- **Israel**: `+972` (e.g., `+972501234567`)
- **UK**: `+44` (e.g., `+442071838750`)
- Other countries: Look up the country code

## Cost

- **Twilio**: ~$0.50-1.00 per SMS sent (varies by country)
- **Free trial**: You get $15 credit to test
- **Twilio phone number**: ~$1/month

## Disable SMS

To disable SMS notifications without uninstalling:
1. Set `SMS_ENABLED=false` in `.env`
2. OR leave `SMS_ENABLED` unset (defaults to false)

The system will continue working normally, just without SMS alerts.

## Advanced: Customize SMS Messages

Edit `sms_service.py` to customize the message format:

```python
# In the send_appointment_confirmed() method:
message_parts = ["🎉 Your appointment is confirmed!"]  # Change this
# ... rest of the code
```

## Security Notes

✓ **Credentials are NOT stored in code** - they're in `.env` (which is in `.gitignore`)
✓ **Never commit `.env` to Git** - it contains sensitive credentials
✓ **Use `.env.example`** as a template for your `.env` file

## Support

If you have issues:
1. Check Twilio dashboard → Message Logs for delivery details
2. Run `python -c "from sms_service import sms_service; print(sms_service.enabled)"` to verify setup
3. Check logs at `logs/persistent_agent_*.log` for error messages
