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

# --- STEP 1: LINK EXTRACTION (The "Baby Urls") ---
def get_notice_links(origin_url, region):
    """
    Fetches links from a URL and applies specific filtering rules 
    based on the 'Regione' provided in the CSV.
    """
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',  # Do Not Track request
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get(origin_url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue
            
            full_url = urljoin(origin_url, href)

            # --- REGION-SPECIFIC SWITCH CASE ---
            
            # Case 1: MIM-hosted regions (Campania, Abruzzo, Basilicata, etc.)
            # These use the standard "/-/" pattern for news.
            if region in ["Abruzzo", "Basilicata", "Campania", "Marche", "Molise", "Sardegna", "Toscana"]:
                if "/-/" in full_url and "?" not in full_url:
                    links.append(full_url)

            # Case 2: Lombardia (Complex Liferay structure)
            elif region == "Lombardia":
                # We want the link even if it has a '?', but we will clean it
                if "/-/" in full_url and "/content/" in full_url:
                    # Split at the '?' and take the first part (the clean URL)
                    clean_url = full_url.split('?')[0]
                    links.append(clean_url)

            # Case 3: Calabria (Independent WordPress Site)
            # These require excluding categories and tags to get pure news.
            elif region == "Calabria":
                noise = ["/category/", "/tag/", "/page/", "?", "sow-", "wp-login", "#"]
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "istruzione.calabria.it" in full_url
                
                # News articles usually have long descriptive slugs (more than 4 slashes)
                if is_internal and has_no_noise and len(full_url.split('/')) > 4:
                    # Avoid adding the homepage
                    if full_url.strip('/') != origin_url.strip('/'):
                        links.append(full_url)

            # Case 4: Umbria (Independent Site with Mixed Content)
            # Similar to case 1 but with a different domain.
            elif region == "Umbria":
                if "/usr-umbria/" in full_url and "?" not in full_url:
                    links.append(full_url)

            elif region == "Emilia-Romagna":
                noise = ["/chi-siamo/", "/siti-tematici/", "/pnrr/", "/materialiedciv30h/", "/contatti-urp/", "mailto:", "#",
                        "/media/", "/dati/", "/note-legali/", "/formazione-pcto-materiali/", "/mappa-del-sito/", "/servizi/", "/feed/", "/privacy/", "/europa/" ]
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "istruzioneer.gov.it" in full_url
                if is_internal and has_no_noise and len(full_url.split('/')) > 4:
                    if full_url.strip('/') != origin_url.strip('/'):
                        links.append(full_url)
                
            elif region == "Lazio":
                noise = ["/616-2/", "/amministrazione/", "/aree-tematiche/", "#main_container", "#menup", "#footer", "tel:", "#", "/note-legali/"]
                
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "ufficioscolasticoregionalelazio.it" in full_url
                if is_internal and has_no_noise and len(full_url.split('/')) > 4:
                    if full_url.strip('/') != origin_url.strip('/'):
                        links.append(full_url)

            elif region == "Puglia":
                # 1. Define noise to ignore
                noise = ["/images/", ".pdf", ".zip",  "#", "mailto:"]
                # "/index.php?start=",
                
                # 2. Check basics
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "pugliausr.gov.it" in full_url
                
                # 3. Identify actual news articles (Joomla style)
                # We look for the year pattern like '-2025' or '-2026'
                if is_internal and has_no_noise and any(yr in full_url for yr in ["-2025", "-2026"]):
                    
                    # --- THE CRITICAL STEP ---
                    # urljoin already turned '/index.php/...' into 'https://www.pugliausr.gov.it/index.php/...'
                    # We just make sure it's clean (no fragments like #)
                    clean_full_url = full_url.split('#')[0].strip()
                    
                    links.append(clean_full_url)

            elif region == "Friuli V.G.":
                # 1. Define noise to ignore
                noise = [".pdf", "#", "mailto:", "index.html", "?facet_instancedate", "sl/?__locale=sl", "/Procedure-concorsuali/", ".html", "/aree/"]
                
                
                # 2. Check basics
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "usrfvg.gov.it" in full_url
                
                if is_internal and has_no_noise:
                    
                    clean_full_url = full_url.split('#')[0].strip()
                    links.append(clean_full_url)

            elif region == "Provincia Autonoma di Trento":
                # 1. Define noise to ignore
                noise = [".pdf", "#", "mailto:", "index.html", "?facet_instancedate", "sl/?__locale=sl", "/Procedure-concorsuali/", ".html", "/aree/"]
                
                
                # 2. Check basics
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "vivoscuola.it" in full_url
                
                if is_internal and has_no_noise:
                    
                    clean_full_url = full_url.split('#')[0].strip()
                    links.append(clean_full_url)

            elif region == "Linguria 1" or region == "Liguria 2":
                # 1. Define noise to ignore
                noise = ["/whistleblowing", "/pagine/monitoraggi", "/note-legali", "/reclutamento-as-2025-2026", "/albo-online", "/accessibilita", "mailto:", "tel:", "/pagine/chi-siamo", "/pagine/elenchi-scuole", "/cookie-policy", "/archivio", "/disclaimer", "/contatti-2"]
               
                
                # 2. Check basics
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "istruzioneliguria.gov.it" in full_url
                
                if is_internal and has_no_noise:
                    
                    clean_full_url = full_url.split('#')[0].strip()
                    links.append(clean_full_url)

            elif region == "Piemonte":
                noise = ["/?page_id=", "/dove-siamo/", "mailto:", "/osservatorio-sicurezza/", "/nonstatali/", "/category/studenti/", "/esame-di-stato-2024/", "/?p=", "/agenda-2030/", "/telegram.me/", "#footer", "/cercalatuascuola/", "/general-data-protection-regulation/", "/fami-256/", "/tag/",  "#main_container", "#", "login.php?", "youtube.com", "#menup", "/invalsi/", "/paritarie/"]
                
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "istruzionepiemonte.it" in full_url
                if is_internal and has_no_noise and len(full_url.split('/')) > 4:
                    if full_url.strip('/') != origin_url.strip('/'):
                        links.append(full_url)

            
            elif region == "Sicilia 1" or region == "Sicilia 2": 
                noise = ["#", "facebook.com/", "twitter.com/", "linkedin.com/", "t.me/", "youtube.com/", "/pnrr/", "tel:", "mailto:","/wp-admin", "/urp", "/area-riservata" ,"/direttore-generale/","/il-personale-dellusr/","/incarichi-dirigenziali-non-generali-usr-sicilia/","/organigramma/","/organizzazione-per-funzioni/","/personale-amministrativo/","/sala-stampa/","/concorsi-e-bandi-di-gara/","/patrocini/","/protocolli-dintesa/","/dirigenti-scolastici/","/personale-scuola/","/pnrr/","/relazioni-sindacali/","/studenti-e-famiglie/","/esami-di-stato/","/organici-e-mobilita-personale-scuola/","/reclutamento/","/rete-scolastica/","/apprendistato/","/educazione-fisica-e-sportiva/","/diritto-allo-studio/","/dispersione-scolastica-e-disagio/","/orientamento/","/orientamento-al-lavoro-its-ifts/","/formazione-scuola-lavoro/","/amministrazione-digitale-e-privacy/","/equipe-formativa-territoriale-per-la-sicilia/","/fami/","/fondi-strutturali/","/innovazione-scuole/","/lingue-straniere-progetti-e-iniziative-internazionali/","/ordinamenti/","/progetti-educativi/","/dirigenti-scolastici/","/concorso-dirigenti-scolastici-2023-2/","/corso-intensivo-d-m-107-2023/","/concorsi-docenti/concorsi-infanzia-e-primaria/","/concorsi-docenti/concorsi-i-e-ii-grado/","/concorsi-docenti/concorsi-irc/","/personale-ata/","/personale-ata/bandi-ata-24-mesi/","/personale-ata/concorso-dsga-2024/","/personale-ata/internalizzazione-servizi-di-pulizia-ex-lsu/","/personale-amministrativo/","/personale-amministrativo/comandi-e-distacchi-presso-la-direzione-generale/","/formazione/","/formazione-dirigenti-scolastici/","/formazione-dirigenti-scolastici/formadsicilia/","/formazione-docenti/","/formazione-docenti/formazione-docenti-neoassunti/","/formazione-personale-ata/","/formazione-personale-amministrativo/","/iniziative-per-le-scuole/",  "/sitemap","/privacy", "/contatti"]
                
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "usr.sicilia.it" in full_url
                if is_internal and has_no_noise and len(full_url.split('/')) > 4:
                    if full_url.strip('/') != origin_url.strip('/'):
                        links.append(full_url)

            # Case 5: Default Fallback
            else:
                if "/-/" in full_url and "?" not in full_url:
                    links.append(full_url)
        
        # Deduplicate results
        return list(set(links))

    except Exception as e:
        print(f"Error fetching {region} at {origin_url}: {e}")
        return []
# --- STEP 2: GEMINI ANALYSIS ---
# def ask_gemini(all_links_text, region_name):
def ask_gemini(full_prompt):
    """Sends the provided prompt to Gemini and returns the response."""

    max_retries = 3
    retry_delay = 15  # seconds

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            if "503" in str(e):
                log_message(f"Service Unavailable (503) error from Gemini. Attempt {attempt + 1} of {max_retries}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                log_message(f"Gemini API Error: {e}")
                return "ERROR"
            
    # If all retries fail, send an email notification
    log_message(f"Max retries ({max_retries}) reached for Gemini API. Sending email notification.")
    subject = f"BOT ALERT: Gemini API Unavailable for {max_retries} attempts"
    body = f"The Gemini API returned a 503 UNAVAILABLE error {max_retries} times. Please check the service status."
    send_email_logic(subject, body, to_self=True)
    return "ERROR"

MISSIONS = [
    # {"id": "GIOCHI", "topic": "Giochi della Gioventù 2025/26", "subject": "Giochi Gioventù"},
    # {"id": "CIRCOLARE", "topic": "Circolare 14/2011 (Diritto allo Studio)", "subject": "Circolare 14/2011"},
    # {"id": "IMPRESA", "topic": "Campionati di Imprenditorialità 2025-2026 (Junior Achievement)", "subject": "Campionati Imprenditorialità"}
    {
        "id": "AI_PNRR", 
        "topic": "Costituzione di Snodi Formativi per l'Intelligenza Artificiale (PNRR Investimento 2.1, Decreto 219/2025 o D.M. n. 219/2025)", 
        "subject": "PNRR: AI Snodi Formativi"
    }
]

def run_bot():
    log_message("--- STARTING REGIONAL SCAN ---")
    history = load_history()
    csv_filename = 'files/data/batch_01.csv'

    with open(csv_filename, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            region, origin_url = row['Regione'], row['Sito Web Ufficiale']
            
            log_message(f"Scanning {region}...")
            # Pass both URL and Region name
            notice_links = get_notice_links(origin_url, region)
            
            if not notice_links: continue
            links_blob = "\n".join(notice_links)
            print(len(links_blob), f"characters in links blob for {region}")

            # --- RUN MORE THAN A MISSION PER REGION ---
            for mission in MISSIONS:
                prompt = f"""
                Analyze these links from USR {region} for the topic: {mission['topic']} on the subject: {mission['subject']}.
                
                Rules:
                - If a relevant link is found, respond ONLY: MATCH: [Title] | [Full URL]
                - If none match, respond: NO.
                
                
                Data: {links_blob}
                """
                
                log_message(f"Sending {region} links to Gemini for analysis...")
                analysis = ask_gemini(prompt)

                if analysis == "RATE_LIMIT_HIT":
                    log_message("Rate limit hit. Sleeping for 60s...")
                    send_email_logic("BOT ALERT: Gemini Quota Hit", "Rate limit hit. Increase sleep time.", to_self=True)
                    time.sleep(60)
                    continue
                
                if "MATCH:" in analysis:
                    # Your splitting and email logic here
                    content = analysis.replace("MATCH:", "").strip()
                    if "|" in content:
                        title, url = content.split("|", 1)
                        match_id = f"{region}_{mission['id']}_{url.strip()}"
                        
                        if match_id not in history:
                            subject = f"{mission['subject']}: Nuovo avviso per {region}"
                            body = f"Trovato avviso per {mission['topic']}\n\nTitolo: {title}\nLink: {url.strip()}"
                            if send_email_logic(subject, body):
                                save_to_history(match_id)
                                log_message(f"Email sent for {region} regarding {url.strip()} under mission {mission['id']}")
                        else:
                            log_message(f"Duplicate found for {region} with URL: {url.strip()} under mission {mission['id']}. Skipping email.")
                
                time.sleep(2) # Short sleep between missions to avoid local rate limits
            
            time.sleep(10) # Longer sleep between regions

if __name__ == "__main__":
    run_bot()