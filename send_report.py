import os
import glob
import json
import time
import shutil
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuration for Google Drive
FOLDER_ID = '1HLX_PykEsDvuOpp7gGnEoTaTYN49T050'

def cleanup_files():
    """Remove all .txt files in the directory except prompt.txt."""
    print("Starting cleanup of temporary files...")
    
    # Получаем список всех .txt файлов
    files = glob.glob("*.txt")
    
    for file_path in files:
        # Пропускаем файл, который нельзя удалять
        if file_path == "prompt.txt":
            continue
            
        try:
            os.remove(file_path)
            print(f"Removed file: {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

def get_report_date_prefix():
    """Get the current date prefix (YYMMDD) to identify today's reports."""
    return datetime.now().strftime("%y%m%d")

def send_email(date_prefix):
    """
    Concatenate YYMMDD_report.txt and YYMMDD_analysis_report.txt 
    and send them via email.
    """
    recipient = os.environ.get("EMAIL_RECIPIENT")
    smtp_user = os.environ.get("GMAIL_SMTP_USERNAME")
    smtp_pass = os.environ.get("GMAIL_SMTP_PASSWORD")

    if not all([recipient, smtp_user, smtp_pass]):
        print("Skipping email: missing environment variables.")
        return

    # Files to look for
    report_file = f"{date_prefix}_report.txt"
    analysis_file = f"{date_prefix}_analysis_report.txt"
    
    content = ""
    
    # Read first file
    if os.path.exists(report_file):
        with open(report_file, 'r', encoding='utf-8') as f:
            content += f.read()
    
    # Append second file with two newlines
    if os.path.exists(analysis_file):
        if content:
            content += "\n\n"
        with open(analysis_file, 'r', encoding='utf-8') as f:
            content += f.read()

    if not content:
        print("No report content found to send.")
        return

    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = "Звіт про моніторинг регіональної преси"
    msg['From'] = smtp_user
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
        print(f"Email successfully sent for date {date_prefix}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    cleanup_old_files()
    
    token_json_str = os.environ.get("GOOGLE_DRIVE_TOKEN")
    if not token_json_str:
        print("Error: GOOGLE_DRIVE_TOKEN not found!")
        return

    # Send email for today's files
    date_prefix = get_report_date_prefix()
    send_email(date_prefix)

    # Upload process
    report_files = glob.glob(f"{date_prefix}_*.txt")
    if not report_files:
        print("No report files found for upload.")
        return

    try:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data)
        service = build('drive', 'v3', credentials=creds)

        for file_path in report_files:
            timestamp = time.strftime("%H%M%S")
            parts = file_path.split('_', 1)
            temp_filename = f"{parts[0]}_{timestamp}_{parts[1]}"
            
            shutil.copy(file_path, temp_filename)
            try:
                file_metadata = {'name': temp_filename, 'parents': [FOLDER_ID]}
                media = MediaFileUpload(temp_filename, mimetype='text/plain', resumable=False)
                service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"SUCCESS! File {temp_filename} uploaded to Drive.")
            finally:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)

    except Exception as e:
        print(f"Critical error: {e}")

if __name__ == "__main__":
    main()
