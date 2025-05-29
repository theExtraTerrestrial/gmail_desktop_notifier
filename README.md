# Gmail Notifier for Windows

A simple Python application that runs in the background, checks for new Gmail messages, and shows desktop notifications with a tray icon.  
This app is designed for Windows 10 and above.

---

## Features

- **Desktop notifications** for new unread Gmail messages
- **System tray icon** with Quit option
- **Runs in the background/minimized**
- **Automatically start at Windows startup (optional)**

---

## Setup Instructions

### 1. Install Python

- Download and install Python 3.8 or newer from [python.org](https://www.python.org/downloads/).
- During installation, check the box to **Add Python to PATH**.

To verify installation, open Command Prompt and run:
```sh
python --version
```

---

### 2. Download the Script

- Download or clone this repository to your PC.
- Place the `tray_notifier.py` (or `tray_notifier.pyw`) script in a folder of your choice.

---

### 3. Enable Gmail API and Download Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).
3. Go to **APIs & Services > Library**, search for **Gmail API**, and enable it.
4. Go to **APIs & Services > Credentials**.
5. Click **Create Credentials > OAuth client ID**.
    - Set **Application type** to **Desktop app**.
    - Name it (e.g., "Gmail Notifier").
6. Download the `credentials.json` file and place it in the same folder as the script.

---

### 4. Install Required Python Packages

Open Command Prompt in the script's folder and run:
```sh
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib win10toast pystray pillow
```

---

### 5. Run the Script

- **For testing:**  
  Double-click `tray_notifier.py` (you may see a terminal window).

- **For background/tray mode (no terminal window):**  
  Rename the script to `tray_notifier.pyw` and double-click it.  
  You will see the Gmail icon in your system tray.  
  Right-click the tray icon to quit the app.

---

### 6. (Optional) Start Automatically on Windows Login

1. Press `Win + R`, type `shell:startup`, and press Enter.
2. In the opened folder, create a shortcut to your `tray_notifier.pyw` script.

Now, the notifier will start automatically whenever you log in.

---

## Notes

- **First Run:** The script will open a browser window for Google authentication. Sign in and allow access.
- **Notifications:** Only new unread emails trigger a notification. Marking emails as read removes them from future notifications.
- **Multiple Accounts:** For multiple accounts, duplicate the script and credentials, or modify the script to support multi-account.

---

## Troubleshooting

- **No notifications?**  
  - Check internet connection and Gmail access.
  - Ensure you have unread emails in your inbox.
  - Check if your antivirus is blocking notifications.
  - Try running from a terminal to see error messages.

- **Problems with authentication?**  
  - Delete `token.pickle` in the script folder and restart the script to re-authenticate.

---

## License

MIT License

---
