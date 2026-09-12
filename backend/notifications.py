import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

_initialized = False
_fcm_available = True

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception:
    firebase_admin = None
    credentials = None
    messaging = None
    _fcm_available = False


def init_firebase():
    global _initialized
    if _initialized:
        return
    cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    if not cred_path:
        logging.info("FIREBASE_CREDENTIALS_PATH not set; FCM disabled")
        return
    if not _fcm_available:
        logging.warning("firebase-admin not installed; FCM disabled")
        return
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _initialized = True
    except Exception as e:
        logging.exception("Failed to initialize Firebase Admin SDK: %s", e)


def send_push(device_token: str, title: str, body: str) -> bool:
    """Send push via FCM. Returns True if send succeeded, False otherwise."""
    init_firebase()
    if not _fcm_available or messaging is None:
        logging.info("FCM not available; skipping send")
        return False
    if not _initialized:
        logging.info("FCM not initialized; skipping send")
        return False
    try:
        message = messaging.Message(
            token=device_token,
            notification=messaging.Notification(title=title, body=body),
        )
        resp = messaging.send(message)
        logging.info("FCM send OK: %s", resp)
        return True
    except Exception:
        logging.exception("Failed to send FCM message")
        return False
