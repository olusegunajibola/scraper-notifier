import csv
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import time
from datetime import datetime
from google import genai

# Load Environment Variables
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# Initialize Gemini Client, looks for GEMINI_API_KEY env var
client = genai.Client()

HISTORY_FILE = "sent_notifications.txt"
LOG_FILE = "run_log.txt"

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

def load_history():
    if not os.path.exists(HISTORY_FILE): return set()
    with open(HISTORY_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_to_history(entry_id):
    with open(HISTORY_FILE, "a") as f:
        f.write(entry_id + "\n")

def send_email_logic(subject, body, to_self=False):
    if not all([SENDER_EMAIL, EMAIL_PASSWORD, RECEIVER_EMAIL]):
        log_message("CRITICAL: Email credentials missing.")
        return False

    recipient_list = [SENDER_EMAIL] if to_self else [e.strip() for e in RECEIVER_EMAIL.split(',')]
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

def ask_gemini(page_text, region_name):
    """Uses Gemini to identify official calls for bids based on the MIM article."""
    prompt = f"""Analyze the following text from the USR {region_name} website.

    Context: We are looking for the official implementation of the MIM Decree (March 9, 2026) regarding the 50.3 Million Euro PNRR Investimento 2.1 for ATA Personnel Training.

    Specific Goal: Identify if the page contains an announcement or notice inviting schools or trainers to apply, submitting bids for 'Scuole Polo', or the official 'Piano di riparto' (allocation plan) for this funding.

    Rules:

    If a match is found, respond ONLY in this format: MATCH: [Official Title of the Announcement & a summary in italian]

    If it is just a general news article without an actionable decree or call for bids, respond: NO.

    If no mention of ATA training or PNRR 2.1 is found, respond: NO.

    Text to analyze: {page_text[:12000]}
    """
    try:
        log_message(f"AI: Sending content for {region_name} to Gemini...")
        response = client.models.generate_content(
            # model="gemini-flash-lite-latest",
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            return "RATE_LIMIT_HIT"
        log_message(f"LLM Error for {region_name}: {e}")
        return "ERROR"

def run_bot():
    log_message("--- STARTING RUN (GOOGLE-GENAI SDK) ---")
    
    if not all([SENDER_EMAIL, EMAIL_PASSWORD, RECEIVER_EMAIL, os.getenv("GEMINI_API_KEY")]):
        log_message("CRITICAL: Missing Environment Secrets.")
        return

    history = load_history()
    # csv_filename = 'Elenco USR trial.csv'
    csv_filename = 'mim_deploy_email_list.csv'

    # Counters for the final summary
    processed_count = 0
    skipped_count = 0
    
    try:
        with open(csv_filename, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                region, url = row['Regione'], row['Sito Web Ufficiale']
                check_id = f"{region}_{url}_{datetime.now().strftime('%Y-%m-%d')}"
                
                if check_id in history:
                    # Optional: Log skips if you want to see them in the file
                    log_message(f"SKIP: {region} already handled today. Moving to next.")
                    skipped_count += 1
                    continue

                try:
                    # --- NEW LOGGING LINE ---
                    log_message(f"SCRAPE: Attempting to visit {region} ({url})")
                    processed_count += 1
                    
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    res = requests.get(url, headers=headers, timeout=25)
                    res.raise_for_status()
                    
                    log_message(f"SUCCESS: Page loaded for {region}")
                    
                    soup = BeautifulSoup(res.text, 'html.parser')
                    page_content = " ".join(soup.get_text().split())
                    # print(page_content)  # Optional: Print the content for debugging
                    # log_message(page_content)
                    
                    analysis = ask_gemini(page_content, region)
                    
                    if analysis == "RATE_LIMIT_HIT":
                        log_message("QUOTA EXHAUSTED: Stopping run.")
                        send_email_logic("BOT ALERT: Gemini Quota Hit", "Rate limit hit. Increase sleep time.", to_self=True)
                        break

                    if analysis.startswith("MATCH:"):
                        log_message(f"MATCH FOUND for {region}: {analysis}")
                        # if send_email_logic(f"ACTION: Match - {region}", f"Summary: {analysis}\nURL: {url}"):
                        if send_email_logic(f"È stato trovato un nuovo bando/annuncio di formazione ATA per {region}", f"Riepilogo: {analysis}\nURL: {url}"):
                            save_to_history(check_id)
                    else:
                        log_message(f"RESULT: No match for {region}")
                    
                    time.sleep(20)

                except Exception as e:
                    log_message(f"FAIL: {region} scrape error: {e}")
                    send_email_logic(f"DEBUG: Scraper Fail - {region}", f"Error: {e}", to_self=True)
                    
    except Exception as e:
        log_message(f"FATAL: {e}")

    log_message(f"--- RUN ENDED | Processed: {processed_count} | Skipped: {skipped_count} ---")

if __name__ == "__main__":
    run_bot()