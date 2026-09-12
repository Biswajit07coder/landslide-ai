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
    # If env var not set, try to auto-discover a credentials JSON under .env/credentials
    if not cred_path:
        # Look in repository root .env/credentials and backend relative path
        candidates = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env", "credentials")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "credentials")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
        ]
        found = None
        for c in candidates:
            if os.path.isdir(c):
                for fname in os.listdir(c):
                    if fname.lower().endswith('.json'):
                        found = os.path.join(c, fname)
                        break
            if found:
                break
        if found:
            cred_path = found
            logging.info("FIREBASE_CREDENTIALS_PATH not set; auto-discovered credentials at %s", cred_path)
        else:
            logging.info("FIREBASE_CREDENTIALS_PATH not set and no credentials found under .env/credentials; FCM disabled")
            return
    if not _fcm_available:
        logging.warning("firebase-admin not installed; FCM disabled")
        return
    try:
        logging.info("Initializing Firebase Admin SDK with credentials: %s", cred_path)
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
        # Include a visible notification block (title/body) so browsers show a proper notification
        # Use a short, consistent title and the provided body (which contains location and level).
        data_payload = {"title": title, "body": body}
        message = messaging.Message(
            token=device_token,
            notification=messaging.Notification(title="Landslide Risk Alert", body=body),
            data=data_payload,
        )
        resp = messaging.send(message)
        logging.info("FCM send OK: %s", resp)
        return True
    except Exception:
        logging.exception("Failed to send FCM message")
        return False
