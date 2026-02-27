import re
import threading
import queue
import time

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

    def _listen(self):
        listener = UserNotificationListener.current
        status = listener.request_access_async().get()
        if status != UserNotificationListenerAccessStatus.ALLOWED:
            print("Notification access not allowed.")
            return
        while self.running:
            notifications = listener.get_notifications_async(NotificationKinds.TOAST).get()
            for notif in notifications:
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
                        self.otp_queue.put(otp_match.group())
            # Sleep a bit to avoid busy loop
            time.sleep(2)

# Usage example:
# listener = OTPListener()
# listener.start()
# otp = listener.get_latest_otp(timeout=90)
# print("OTP code:", otp)
