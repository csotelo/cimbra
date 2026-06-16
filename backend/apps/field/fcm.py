"""FCM push notification utility for field device alerts."""

import json
import logging
import os

log = logging.getLogger("field.fcm")

_fcm_app = None
_fcm_init_attempted = False


def _get_app():
    global _fcm_app, _fcm_init_attempted
    if _fcm_init_attempted:
        return _fcm_app
    _fcm_init_attempted = True
    cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
    if not cred_json:
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials
        try:
            # Guard against concurrent workers that already registered the app name
            _fcm_app = firebase_admin.get_app("ximbra-field")
        except ValueError:
            cred = credentials.Certificate(json.loads(cred_json))
            _fcm_app = firebase_admin.initialize_app(cred, name="ximbra-field")
        log.info("Firebase app initialized")
    except Exception as exc:
        log.error("Firebase init error: %s", exc)
    return _fcm_app


def send_fcm_push(fcm_token: str, title: str, body: str, data: dict = None) -> bool:
    """Send a FCM push notification to a field device.

    Returns True on success, False otherwise.
    Silently skips if FIREBASE_CREDENTIALS_JSON is not set.
    """
    if not fcm_token:
        return False
    app = _get_app()
    if app is None:
        log.debug("FCM not configured — skipping push to token %s...", fcm_token[:8])
        return False
    try:
        from firebase_admin import messaging
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={str(k): str(v) for k, v in (data or {}).items()},
            token=fcm_token,
            android=messaging.AndroidConfig(priority="high"),
        )
        messaging.send(msg, app=app)
        log.info("FCM sent to %s... title=%r", fcm_token[:8], title)
        return True
    except Exception as exc:
        log.error("FCM send error: %s", exc)
        return False
