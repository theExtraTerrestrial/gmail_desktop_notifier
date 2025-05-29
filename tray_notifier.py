import os
import pickle
import time
import threading
from PIL import Image, ImageDraw
import win10toast
import pystray
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = 'credentials.json'

def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def get_unread_messages(service):
    results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD']).execute()
    return results.get('messages', [])

def show_notification(subject, sender):
    toaster = win10toast.ToastNotifier()
    toaster.show_toast(
        f"New Email from {sender}",
        f"Subject: {subject}",
        duration=10,
        threaded=True
    )

def get_message_details(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['Subject', 'From']).execute()
    headers = msg['payload']['headers']
    subject = sender = "Unknown"
    for h in headers:
        if h['name'] == 'Subject':
            subject = h['value']
        if h['name'] == 'From':
            sender = h['value']
    return subject, sender

def notifier_thread(stop_event):
    service = authenticate_gmail()
    seen_ids = set()
    while not stop_event.is_set():
        try:
            messages = get_unread_messages(service)
            for msg in messages:
                if msg['id'] not in seen_ids:
                    subject, sender = get_message_details(service, msg['id'])
                    show_notification(subject, sender)
                    seen_ids.add(msg['id'])
            time.sleep(60)
        except Exception as e:
            print("Error:", e)
            time.sleep(60)

def create_image():
    # Generates a simple icon
    image = Image.new('RGB', (64, 64), color1 := (76, 175, 80))
    d = ImageDraw.Draw(image)
    d.rectangle((16, 24, 48, 40), fill=(255, 255, 255))
    d.polygon([(16, 24), (32, 36), (48, 24)], fill=(255, 0, 0))
    return image

def main():
    stop_event = threading.Event()
    thread = threading.Thread(target=notifier_thread, args=(stop_event,), daemon=True)
    thread.start()

    def on_quit(icon, item):
        stop_event.set()
        icon.stop()

    icon = pystray.Icon(
        "GmailNotifier",
        create_image(),
        "Gmail Notifier",
        menu=pystray.Menu(
            pystray.MenuItem("Quit", on_quit)
        )
    )
    icon.run()

if __name__ == '__main__':
    main()
