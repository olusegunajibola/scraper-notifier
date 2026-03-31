import csv
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import time
from datetime import datetime
from urllib.parse import urljoin
from google import genai

# --- CONFIGURATION & ENV ---
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

client = genai.Client()

HISTORY_FILE = "sent_notifications.txt"
LOG_FILE = "run_log.txt"

# --- HELPER FUNCTIONS ---
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

# --- STEP 1: LINK EXTRACTION (The "Baby Urls") ---
def get_notice_links(origin_url):
    """Extracts specific news links containing '/-/' and excludes queries."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
    try:
        res = requests.get(origin_url, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and "/-/" in href and "?" not in href:
                links.append(urljoin(origin_url, href))
        return list(set(links)) # Deduplicate
    except Exception as e:
        log_message(f"Scrape Error for {origin_url}: {e}")
        return []

# --- STEP 2: GEMINI ANALYSIS ---
def ask_gemini(all_links_text, region_name):
    """Sends the 31k character block of links to Gemini for analysis."""
    prompt = f"""
    Analyze this list of links from the USR {region_name} website.
    
    Context: We are looking for the official implementation of the MIM Decree (March 9, 2026) 
    regarding the PNRR Investimento 2.1 for ATA Personnel Training.
    
    Goal: Identify if any URL 'slug' suggests an announcement for 'Scuole Polo', 'Piano di riparto', 
    or a call for bids/training specifically for ATA personnel.
    
    Data: {all_links_text}
    
    Rules:
    - If a relevant link is found, respond ONLY: MATCH: [Title Based on URL] | [The Full URL]
    - If none match, respond: NO.
    """
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        if "429" in str(e): return "RATE_LIMIT_HIT"
        return "ERROR"

# --- MAIN BOT LOGIC ---
def run_bot():
    log_message("--- STARTING REGIONAL SCAN ---")
    history = load_history()
    csv_filename = '../../files/data/batch_01_test.csv'

    try:
        with open(csv_filename, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                region, origin_url = row['Regione'], row['Sito Web Ufficiale']
                
                # 1. Get all "Baby URLs"
                log_message(f"Scanning {region}...")
                notice_links = get_notice_links(origin_url)
                
                # Convert list to a single string (max 31k chars as requested)
                links_blob = "\n".join(notice_links)[:31000]
                
                # 2. Analyze with Gemini
                analysis = ask_gemini(links_blob, region)
                
                if analysis == "RATE_LIMIT_HIT":
                    log_message("Rate limit hit. Sleeping for 60s...")
                    time.sleep(60)
                    continue

                if "MATCH:" in analysis:
                    # Check if we already alerted for this specific match today
                    match_id = f"{region}_{analysis[:50]}"
                    if match_id not in history:
                        log_message(f"FOUND: {analysis}")
                        # Send Email Logic here (omitted for brevity)
                        save_to_history(match_id)
                
                # Safety sleep to avoid 429 errors between the 8 regions
                time.sleep(15)

    except Exception as e:
        log_message(f"FATAL ERROR: {e}")

if __name__ == "__main__":
    run_bot()