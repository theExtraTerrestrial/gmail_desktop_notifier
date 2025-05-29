import os
import pickle
import time
import threading
from PIL import Image, ImageDraw
import pystray
from win10toast_click import ToastNotifier
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import sys
import traceback

# Log all exceptions to a file for debugging (especially useful for .pyw)
def log_exceptions(exctype, value, tb):
    with open("error_log.txt", "a") as f:
        f.write(''.join(traceback.format_exception(exctype, value, tb)))
        f.write("\n\n")
sys.excepthook = log_exceptions

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_script_dir():
    print("Entered get_script_dir()")
    try:
        path = os.path.dirname(os.path.abspath(__file__))
        print(f"get_script_dir: path is {path}")
        return path
    except NameError:
        cwd = os.getcwd()
        print(f"get_script_dir: __file__ not defined, cwd is {cwd}")
        return cwd

def get_last_checked_time(path="last_checked_time.txt"):
    print(f"Entered get_last_checked_time({path})")
    try:
        with open(path, "r") as f:
            t = int(f.read().strip())
            print(f"Loaded last_checked_time: {t}")
            return t
    except Exception as e:
        now = int(time.time() * 1000)
        print(f"No last_checked_time file found or error '{e}'; using now: {now}")
        return now

def set_last_checked_time(t, path="last_checked_time.txt"):
    with open(path, "w") as f:
        f.write(str(t))
    print(f"Persisted last_checked_time: {t}")

def authenticate_gmail():
    print("Entered authenticate_gmail()")
    script_dir = get_script_dir()
    CREDENTIALS_PATH = os.path.join(script_dir, 'credentials.json')
    TOKEN_PATH = os.path.join(script_dir, 'token.pickle')

    creds = None
    if os.path.exists(TOKEN_PATH):
        print("authenticate_gmail: Loading creds from token.pickle")
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        print("authenticate_gmail: Credentials missing or invalid")
        if creds and creds.expired and creds.refresh_token:
            print("authenticate_gmail: Refreshing expired credentials")
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            print("authenticate_gmail: Running local server for OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    print("authenticate_gmail: Building Gmail service")
    return build('gmail', 'v1', credentials=creds)

def get_recent_messages(service, max_results=10):
    print("Entered get_recent_messages()")
    results = service.users().messages().list(userId='me', maxResults=max_results, q=None).execute()
    messages = results.get('messages', [])
    print(f"get_recent_messages: {len(messages)} messages")
    return messages

def get_message_details_and_date(service, msg_id):
    print(f"Entered get_message_details_and_date() for msg_id {msg_id}")
    msg = service.users().messages().get(
        userId='me',
        id=msg_id,
        format='metadata',
        metadataHeaders=['Subject', 'From']
    ).execute()
    headers = msg['payload']['headers']
    subject = sender = "Unknown"
    for h in headers:
        if h['name'] == 'Subject':
            subject = h['value']
        if h['name'] == 'From':
            sender = h['value']
    internal_date = int(msg.get('internalDate', "0"))
    thread_id = msg.get('threadId')
    label_ids = msg.get('labelIds', [])
    print(f"get_message_details_and_date: subject={subject}, sender={sender}, internal_date={internal_date}, thread_id={thread_id}, labels={label_ids}")
    return subject, sender, internal_date, thread_id, label_ids

MAX_TITLE_LEN = 64

toaster = ToastNotifier()
service = authenticate_gmail()

def show_notification(subject, sender, thread_id):
    print(f"Entered show_notification() subject={subject} sender={sender} thread_id={thread_id}")
    title = f"New Email from {sender}"
    if len(title) > MAX_TITLE_LEN:
        title = title[:MAX_TITLE_LEN - 3] + "..."
    url = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}"

    def open_gmail():
        print(f"Notification clicked - opening Gmail thread: {url}")
        webbrowser.open(url)
        return 0  # This is crucial!

    print(f"show_notification: Sending toast with title='{title}' and subject='{subject}'")
    toaster.show_toast(
        title=title,
        msg=f"Subject: {subject}",
        duration=10,
        threaded=True,
        callback_on_click=open_gmail
    )

def notifier_thread(stop_event):
    print("Entered notifier_thread()")
    try:
        last_checked_date = get_last_checked_time()
        print("Notifier started. Only new UNREAD emails among the last 10 received will trigger notifications.")
        while not stop_event.is_set():
            try:
                print("notifier_thread: Checking for last 10 messages")
                messages = get_recent_messages(service, max_results=10)
                max_msg_date = last_checked_date
                for msg in messages:
                    subject, sender, msg_date, thread_id, label_ids = get_message_details_and_date(service, msg['id'])
                    print(f"notifier_thread: msg_date={msg_date}, last_checked_date={last_checked_date}, labels={label_ids}")
                    if msg_date > last_checked_date and 'UNREAD' in label_ids:
                        print("notifier_thread: New UNREAD message detected, showing notification")
                        show_notification(subject, sender, thread_id)
                    if msg_date > max_msg_date:
                        max_msg_date = msg_date
                if max_msg_date > last_checked_date:
                    set_last_checked_time(max_msg_date)
                print("notifier_thread: Sleeping for 60 seconds")
                time.sleep(60)
            except Exception as e:
                print(f"notifier_thread: Error: {e}")
                with open("error_log.txt", "a") as f:
                    f.write(f"Notifier loop error: {e}\n")
                time.sleep(60)
    except Exception as e:
        print(f"notifier_thread: Critical error: {e}")
        with open("error_log.txt", "a") as f:
            f.write(f"Notifier thread error: {e}\n")

def show_unread_messages(icon, item):
    messages = get_recent_messages(service, max_results=10)
    if messages:
        print(f"show_unread_messages: Found {len(messages)} recent messages")
        for msg in messages:
            subject, sender, msg_date, thread_id, label_ids = get_message_details_and_date(service, msg['id'])
            print(f"notifier_thread: msg_date={msg_date}, labels={label_ids}")
            print("notifier_thread: New UNREAD message detected, showing notification")
            show_notification(subject, sender, thread_id)

def main():
    print("Entered main()")
    stop_event = threading.Event()
    thread = threading.Thread(target=notifier_thread, args=(stop_event,), daemon=True)
    thread.start()

    def on_quit(icon, item):
        print("on_quit() called from tray menu")
        stop_event.set()
        icon.stop()
        return 0  # Must return int

    print("Creating tray icon")
    icon = pystray.Icon(
        "GmailNotifier",
        Image.open("gmail_tray_icon.png"),
        "Gmail Notifier",
        menu=pystray.Menu(
            pystray.MenuItem("Show 10 unread messages", show_unread_messages),
            pystray.MenuItem("Quit", on_quit)
        )
    )
    print("Running tray icon")
    icon.run()
    print("Exited tray icon loop")

if __name__ == '__main__':
    print("Script started as __main__")
    main()
