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

def send_alert(region, url, found_keywords):
    msg = EmailMessage()
    msg['Subject'] = f"Keyword Match: {region}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL # Sends to your provided address in .env
    
    body = f"""
New announcement detected for Regione: {region} 

URL: {url}
Matched Keywords: {', '.join(found_keywords)}

Action required regarding this update.
    """
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Alert sent successfully for {region}")
        log_message(f"SUCCESS: Email sent for {region}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        log_message(f"ERROR: Failed to send email for {region} : {e}")

def run_bot():
    log_message("--- STARTING RUN ---")
    history = load_history()
    
    # Using 'utf-8-sig' handles the BOM if the CSV was saved via Excel
    try:
        with open('Elenco USR trial.csv', mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                region = row['Regione']
                url = row['Sito Web Ufficiale']
                # Split keywords and remove extra spaces
                keywords = [k.strip().lower() for k in row['Keywords'].split(',')]
                
                # Check history so we don't alert 4 times a day for the same thing
                check_id = f"{region}_{url}"
                if check_id in history:
                    print(f"[-] {region} already processed. Skipping.")
                    continue

                print(f"[*] Checking {region}...")
                
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    response = requests.get(url, headers=headers, timeout=20)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Normalize text: lowercase and remove excessive newlines/tabs
                    page_content = " ".join(soup.get_text().lower().split())
                    
                    # Verify if any of our target keywords are in the text
                    matches = [kw for kw in keywords if kw in page_content]
                    
                    if matches:
                        print(f"[!] MATCH FOUND: {region} -> {matches}")
                        log_message(f"MATCH: Found {matches} on {region}")
                        send_alert(region, url, matches)
                        save_to_history(check_id)
                    else:
                        print(f"[.] No matches for {region}.")
                        log_message(f"NO MATCH: No keywords found for {region} : {e}")
                    
                    # Gentle delay between requests
                    time.sleep(2)

                except Exception as e:
                    print(f"[ER] Error scraping {region}: {e}")
                    
    except FileNotFoundError:
        print("Error: 'Elenco USR trial.csv' not found. Please ensure the file exists.")
        log_message(f"CRITICAL: CSV Error: Please ensure the file exists")

if __name__ == "__main__":
    run_bot()

# import csv
# import requests
# from bs4 import BeautifulSoup
# import smtplib
# from email.message import EmailMessage
# import os
# from dotenv import load_dotenv

# # --- LOAD SECRETS ---
# load_dotenv() # This looks for the .env file and loads the variables

# SENDER_EMAIL = os.getenv("SENDER_EMAIL")
# EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
# RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
# HISTORY_FILE = "sent_alerts.txt"

# def load_history():
#     if not os.path.exists(HISTORY_FILE):
#         return set()
#     with open(HISTORY_FILE, "r") as file:
#         return set(line.strip() for line in file)

# def save_to_history(url):
#     with open(HISTORY_FILE, "a") as file:
#         file.write(url + "\n")

# def send_email(matched_url, found_keywords):
#     msg = EmailMessage()
#     msg['Subject'] = "Action Required: New Announcement Detected"
#     msg['From'] = SENDER_EMAIL
#     msg['To'] = RECEIVER_EMAIL
    
#     body = f"""
# New announcement matching your criteria:

# URL: {matched_url}
# Keywords detected: {', '.join(found_keywords)}

# Time of check: {os.popen('date').read().strip()}
#     """
#     msg.set_content(body)

#     try:
#         # SMTP settings for Gmail. 
#         # For Outlook, use 'smtp.office365.com' and port 587 (requires .starttls())
#         with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
#             smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)
#             smtp.send_message(msg)
#         print(f"Notification sent for: {matched_url}")
#     except Exception as e:
#         print(f"Failed to send email: {e}")

# def scrape_and_check():
#     sent_history = load_history()
    
#     # Ensure your CSV columns are named exactly 'URL' and 'Keywords'
#     with open('Elenco USR test.csv', mode='r') as file:
#         reader = csv.DictReader(file)
        
#         for row in reader:
#             url = row['Sito Web Ufficiale']
#             # url = row['URL']
#             keywords = [k.strip().lower() for k in row['Keywords'].split(',')]
            
#             if url in sent_history:
#                 continue
                
#             try:
#                 headers = {'User-Agent': 'Mozilla/5.0'}
#                 response = requests.get(url, headers=headers, timeout=15)
#                 response.raise_for_status()
                
#                 soup = BeautifulSoup(response.text, 'html.parser')
#                 page_text = soup.get_text().lower()
                
#                 found_keywords = [kw for kw in keywords if kw in page_text]
                
#                 if found_keywords:
#                     send_email(url, found_keywords)
#                     save_to_history(url)
                    
#             except Exception as e:
#                 print(f"Error checking {url}: {e}")

# if __name__ == "__main__":
#     scrape_and_check()