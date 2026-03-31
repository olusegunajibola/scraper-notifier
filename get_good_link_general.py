import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

def get_all_hrefs(url, region):
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
        response = session.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue
            
            full_url = urljoin(url, href)

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
                    if full_url.strip('/') != url.strip('/'):
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
                    if full_url.strip('/') != url.strip('/'):
                        links.append(full_url)
                
            elif region == "Lazio":
                noise = ["/616-2/", "/amministrazione/", "/aree-tematiche/", "#main_container", "#menup", "#footer", "tel:", "#", "/note-legali/"]
                
                has_no_noise = not any(p in full_url.lower() for p in noise)
                is_internal = "ufficioscolasticoregionalelazio.it" in full_url
                if is_internal and has_no_noise and len(full_url.split('/')) > 4:
                    if full_url.strip('/') != url.strip('/'):
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

            # Case 5: Default Fallback
            else:
                if "/-/" in full_url and "?" not in full_url:
                    links.append(full_url)
        
        # Deduplicate results
        return list(set(links))

    except Exception as e:
        print(f"Error fetching {region} at {url}: {e}")
        return []

def run_bot():
    # Path to your CSV file
    csv_filename = 'files/data/batch_01.csv'

    # Create an output directory for the test files if it doesn't exist
    output_dir = "files/test_outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with open(csv_filename, mode='r', encoding='utf-8-sig') as file:
            # Use DictReader to reference columns by their names in the CSV header
            reader = csv.DictReader(file)
            
            for row in reader:
                # Reference the specific columns: 'Regione' and 'Sito Web Ufficiale'
                region = row['Regione']
                origin_url = row['Sito Web Ufficiale']
                
                print(f"--- Processing {region} ---")
                
                # Call the scraper with the region-specific switch logic
                notice_links = get_all_hrefs(origin_url, region)

                # Create a filename like "test_outputs/Abruzzo_links.txt"
                file_path = os.path.join(output_dir, f"{region}_links.txt")

                with open(file_path, "w", encoding="utf-8") as f:
                    if notice_links:
                        for link in sorted(notice_links):
                            f.write(link + "\n")
                        print(f"   -> Saved {len(notice_links)} links to {file_path}")
                    else:
                        f.write("No links found for this region with current filters.")
                        print(f"   -> No links found for {region}.")
                
                # if notice_links:
                #     print(f"Found {len(notice_links)} valid news links for {region}.")
                #     # (Insert your Gemini analysis and email logic here)
                # else:
                #     print(f"No new notices found for {region}.")

    except FileNotFoundError:
        print(f"Error: The file '{csv_filename}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_bot()