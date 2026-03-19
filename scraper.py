import csv
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import time
from datetime import datetime

# Load Environment Variables
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
HISTORY_FILE = "sent_notifications.txt"
LOG_FILE = "run_log.txt"

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message) # Still prints to GitHub Action console
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_to_history(entry_id):
    with open(HISTORY_FILE, "a") as f:
        f.write(entry_id + "\n")

def send_email_logic(subject, body, to_self=False):
    """Helper function to handle sending. If to_self is True, only sends to SENDER_EMAIL."""
    if not all([SENDER_EMAIL, EMAIL_PASSWORD, RECEIVER_EMAIL]):
        log_message("CRITICAL: Email credentials missing.")
        return False

    # Logic to decide recipients
    if to_self:
        recipient_list = [SENDER_EMAIL]
    else:
        recipient_list = [email.strip() for email in RECEIVER_EMAIL.split(',')]

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipient_list)
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        log_message(f"SMTP ERROR: {e}")
        return False

def run_bot():
    log_message("--- STARTING RUN ---")
    
    # 1. Safety Check
    if not all([SENDER_EMAIL, EMAIL_PASSWORD, RECEIVER_EMAIL]):
        log_message("CRITICAL: Missing .env variables. Check GitHub Secrets.")
        return

    history = load_history()
    # csv_filename = 'mim_deploy_email_list.csv'
    csv_filename = 'Elenco USR trial.csv'
    
    try:
        with open(csv_filename, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                region = row['Regione']
                url = row['Sito Web Ufficiale']
                keywords = [k.strip().lower() for k in row['Keywords'].split(',')]
                
                check_id = f"{region}_{url}"
                if check_id in history:
                    print(f"[-] {region} already notified. Skipping.")
                    continue

                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    response = requests.get(url, headers=headers, timeout=25)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_content = " ".join(soup.get_text().lower().split())
                    
                    matches = [kw for kw in keywords if kw in page_content]
                    
                    if matches:
                        log_message(f"MATCH: Found {matches} on {region}")
                        subject = f"ACTION REQUIRED: Keyword Match - {region}"
                        body = f"Announcement detected for {region}.\nURL: {url}\nKeywords: {', '.join(matches)}"
                        # send_email_logic(..., to_self=False) is default
                        if send_email_logic(subject, body):
                            save_to_history(check_id)
                    else:
                        print(f"[.] No matches for {region}.")
                    
                    time.sleep(5) # Polite delay between requests

                except Exception as e:
                    log_message(f"FAIL: {region} scrape error: {e}")
                    # send errors to me
                    err_subject = f"DEBUG ALERT: Scraper Failure - {region}"
                    err_body = f"The bot could not check {region}.\nURL: {url}\nError: {e}"
                    send_email_logic(err_subject, err_body, to_self=True)
                    
    except FileNotFoundError:
        log_message(f"CRITICAL: CSV file '{csv_filename}' not found.")
        # Send a critical system error to yourself if the CSV is missing
        send_email_logic("CRITICAL: Bot CSV Missing", "The bot failed because the CSV file was not found.", to_self=True)
    
    log_message("--- RUN ENDED ---")

if __name__ == "__main__":
    run_bot()