import time 
from datetime import datetime, timezone


def send_notification(email: str, message: str) -> None:
    try:
        time.sleep(2)
        timestamp = datetime.now(timezone.utc).isoformat()
        with open("notification_log.txt", "a") as f:
            f.write(f"[{timestamp}] to={email} | Message: {message}\\n")
    except Exception as e:
        print(f"Failed to send notification: {e}")