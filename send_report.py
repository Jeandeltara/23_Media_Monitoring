import os
import glob
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuration
FOLDER_ID = '1HLX_PykEsDvuOpp7gGnEoTaTYN49T050'

def cleanup_files():
    """Remove all .txt files in the directory except prompt.txt."""
    print("Starting cleanup of temporary files...")
    files = glob.glob("*.txt")
    for file_path in files:
        if file_path == "prompt.txt":
            continue
        try:
            os.remove(file_path)
            print(f"Removed file: {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

def send_email(date_prefix):
    """Сбор и отправка письма."""
    recipient_str = os.environ.get("EMAIL_RECIPIENT", "")
    smtp_user = os.environ.get("GMAIL_SMTP_USERNAME")
    smtp_pass = os.environ.get("GMAIL_SMTP_PASSWORD")

    content = ""
    # Ищем два конкретных файла
    for f_name in [f"{date_prefix}_report.txt", f"{date_prefix}_analysis_report.txt"]:
        if os.path.exists(f_name):
            with open(f_name, 'r', encoding='utf-8') as f:
                if content: content += "\n\n"
                content += f.read()

    if not content:
        print("No report content found to send.")
        return False

    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = "Звіт про моніторинг регіональної преси"
    msg['From'] = smtp_user
    msg['To'] = recipient_str

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
        print("Email successfully sent.")
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

def main():
    date_prefix = datetime.now().strftime("%y%m%d")
    
    # 1. Отправка почты
    send_email(date_prefix)
    
    # 2. Загрузка на диск
    token_str = os.environ.get("GOOGLE_DRIVE_TOKEN")
    if token_str:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(token_str))
            service = build('drive', 'v3', credentials=creds)
            
            for file_path in glob.glob(f"{date_prefix}_*.txt"):
                file_metadata = {'name': file_path, 'parents': [FOLDER_ID]}
                media = MediaFileUpload(file_path, mimetype='text/plain')
                service.files().create(body=file_metadata, media_body=media).execute()
                print(f"Uploaded: {file_path}")
        except Exception as e:
            print(f"Drive Error: {e}")
            
    # 3. Очистка репозитория
    cleanup_files()

if __name__ == "__main__":
    main()
