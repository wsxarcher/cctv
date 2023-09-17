import requests
import os

USER_KEY = os.environ.get("PUSHOVER_USER_KEY", None)
APP_TOKEN = os.environ.get("PUSHOVER_APP_TOKEN", None)

def send_notification(camera_id, time, preview_b64):
    if not USER_KEY or not APP_TOKEN:
        print("Notification token not set")
        return
    
    try:
        requests.post("https://api.pushover.net/1/messages.json", json={
            "token": APP_TOKEN,
            "user": USER_KEY,
            "title": "Intrusion detected",
            "message": f"Intrusion detected on camera {camera_id} at {time}",
            "attachment_base64": preview_b64,
            "attachment_type": "image/jpeg",
            "url": "",
            "url_title": ""
        }, timeout=10)
        return True
    except Exception as e:
        print(e)