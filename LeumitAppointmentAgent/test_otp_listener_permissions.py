"""Test OTP listener permissions and functionality."""
import sys

try:
    from winsdk.windows.ui.notifications.management import UserNotificationListener, UserNotificationListenerAccessStatus
    print("✓ winsdk imported successfully")
except ImportError as e:
    print(f"✗ Failed to import winsdk: {e}")
    print("Run: pip install winsdk")
    sys.exit(1)

print("\nChecking notification access permissions...")
listener = UserNotificationListener.get_current()
print("✓ Created UserNotificationListener")

print("\nRequesting notification access...")
status_async = listener.request_access_async()
print("✓ Requested access (async)")

print("Waiting for permission result...")
status = status_async.get()
print(f"✓ Permission status: {status}")

if status == UserNotificationListenerAccessStatus.ALLOWED:
    print("\n✓✓✓ SUCCESS: Notification access ALLOWED")
    print("\nFetching current notifications...")
    try:
        notifications = listener.get_notifications_async().get()
        print(f"✓ Found {len(notifications)} notifications")
        
        if len(notifications) > 0:
            print("\nFirst 3 notifications:")
            for i, notif in enumerate(notifications[:3]):
                print(f"\n--- Notification {i+1} ---")
                try:
                    text_elements = notif.notification.visual.binding_generic.get_text_elements()
                    for t in text_elements:
                        print(f"  Text: {t.text}")
                except Exception as e:
                    print(f"  Error reading notification: {e}")
    except Exception as e:
        print(f"✗ Error fetching notifications: {e}")
        import traceback
        traceback.print_exc()
elif status == UserNotificationListenerAccessStatus.DENIED:
    print("\n✗✗✗ DENIED: User denied notification access")
    print("\nTo fix:")
    print("1. Open Windows Settings")
    print("2. Go to System > Notifications")
    print("3. Enable notification access for Python")
elif status == UserNotificationListenerAccessStatus.UNSPECIFIED:
    print("\n⚠ UNSPECIFIED: Permission status unclear")
    print("Try running the script again")
else:
    print(f"\n⚠ Unknown status: {status}")
