"""
Unit tests for OTP timestamp extraction logic.

Run with: python test_otp_listener_timestamp.py
"""

from datetime import datetime, timezone

from otp_listener import OTPListener


GREEN = ''
RED = ''


def test_passed(msg):
    print(f"[PASS] {msg}")


def test_failed(msg):
    print(f"[FAIL] {msg}")


class DummyNotif:
    def __init__(self, creation_time=None, notification=None):
        self.creation_time = creation_time
        self.notification = notification


class DummyPayload:
    def __init__(self, created_time=None):
        self.created_time = created_time


def test_uses_user_notification_creation_time():
    aware_time = datetime(2026, 2, 28, 11, 6, 23, tzinfo=timezone.utc)
    payload_time = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    notif = DummyNotif(
        creation_time=aware_time,
        notification=DummyPayload(created_time=payload_time),
    )

    extracted = OTPListener._get_notification_creation_time(notif)
    if extracted == aware_time:
        test_passed("Uses notif.creation_time (UserNotification) for timestamp")
    else:
        test_failed(f"Expected {aware_time}, got {extracted}")


def test_naive_creation_time_is_normalized_to_utc():
    naive_time = datetime(2026, 2, 28, 11, 6, 23)
    notif = DummyNotif(creation_time=naive_time)

    extracted = OTPListener._get_notification_creation_time(notif)
    if extracted is not None and extracted.tzinfo == timezone.utc:
        test_passed("Naive creation_time normalized to UTC")
    else:
        test_failed(f"Expected UTC-aware datetime, got {extracted}")


def test_missing_creation_time_returns_none():
    notif = DummyNotif(creation_time=None)
    extracted = OTPListener._get_notification_creation_time(notif)

    if extracted is None:
        test_passed("Missing creation_time returns None")
    else:
        test_failed(f"Expected None, got {extracted}")


def main():
    print("\n" + "=" * 70)
    print("OTP LISTENER TIMESTAMP EXTRACTION TESTS")
    print("=" * 70)

    test_uses_user_notification_creation_time()
    test_naive_creation_time_is_normalized_to_utc()
    test_missing_creation_time_returns_none()

    print("\nAll timestamp extraction checks completed.")


if __name__ == "__main__":
    main()
