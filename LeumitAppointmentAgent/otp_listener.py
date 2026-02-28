import re
import threading
import queue
import time
from datetime import datetime, timedelta, timezone

try:
    from winrt.windows.ui.notifications.management import UserNotificationListener, UserNotificationListenerAccessStatus
    from winrt.windows.ui.notifications import NotificationKinds
except ImportError:
    # winrt package not installed
    UserNotificationListener = None
    UserNotificationListenerAccessStatus = None
    NotificationKinds = None

OTP_REGEX = re.compile(r"\b\d{4,6}\b")

class OTPListener:
    def __init__(self):
        self.otp_queue = queue.Queue()
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.running = False

    def start(self):
        if UserNotificationListener is None:
            print("winrt-Windows.UI.Notifications not installed.")
            print("Run: pip install winrt-Windows.UI.Notifications winrt-Windows.UI.Notifications.Management winrt-Windows.Foundation")
            return
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False

    def get_latest_otp(self, timeout=90):
        try:
            return self.otp_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    @staticmethod
    def _get_notification_creation_time(notif):
        creation_time = getattr(notif, "creation_time", None)
        if creation_time is None:
            return None
        if creation_time.tzinfo is None:
            return creation_time.replace(tzinfo=timezone.utc)
        return creation_time

    def _listen(self):
        listener = UserNotificationListener.current
        status = listener.request_access_async().get()
        if status != UserNotificationListenerAccessStatus.ALLOWED:
            print("Notification access not allowed.")
            return
        
        # Track processed notification IDs to avoid duplicates
        processed_ids = set()
        
        while self.running:
            notifications = listener.get_notifications_async(NotificationKinds.TOAST).get()
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=1)
            
            # Collect all matching OTPs
            otp_candidates = []
            
            for notif in notifications:
                # Use notification ID to avoid processing the same notification twice
                notif_id = notif.id if hasattr(notif, 'id') else id(notif)
                
                # Skip if we've already processed this notification
                if notif_id in processed_ids:
                    continue

                # Keep only recent notifications (last minute)
                creation_time = self._get_notification_creation_time(notif)
                if creation_time is None:
                    continue
                if creation_time < cutoff_time:
                    processed_ids.add(notif_id)
                    continue
                
                # Extract sender and message body
                sender = None
                message_body = ""
                bindings = notif.notification.visual.bindings
                if len(bindings) > 0:
                    text_elements = bindings[0].get_text_elements()
                    for t in text_elements:
                        if not sender and t.text.startswith("*") and len(t.text) > 1 and t.text[1:].replace('-', '').isdigit():
                            sender = t.text
                        message_body += t.text + " "
                
                # Filter by sender and keyword
                if sender == "*507" and "קוד אימות" in message_body:
                    otp_match = OTP_REGEX.search(message_body)
                    if otp_match:
                        # Mark as processed
                        processed_ids.add(notif_id)
                        otp_candidates.append((creation_time, otp_match.group()))
            
            # If we found any OTPs, put only the most recent one in the queue
            if otp_candidates:
                # Sort by timestamp (newest first) and take the most recent
                otp_candidates.sort(reverse=True, key=lambda x: x[0])
                latest_otp = otp_candidates[0][1]
                
                # Clear the queue and add only the latest OTP
                while not self.otp_queue.empty():
                    try:
                        self.otp_queue.get_nowait()
                    except queue.Empty:
                        break
                
                self.otp_queue.put(latest_otp)
            
            # Clean up old processed IDs to prevent memory bloat (keep last 100)
            if len(processed_ids) > 100:
                processed_ids = set(list(processed_ids)[-100:])
            
            # Sleep a bit to avoid busy loop
            time.sleep(2)

# Usage example:
# listener = OTPListener()
# listener.start()
# otp = listener.get_latest_otp(timeout=90)
# print("OTP code:", otp)
