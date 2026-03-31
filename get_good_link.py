import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_all_hrefs(url):
    # Mimics a standard Chrome browser on Windows
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
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
        print(f"Successfully fetched {url}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue

            # --- FILTER LOGIC ---
            # 1. Target notice sub-links (indicated by '/-/')
            # 2. Skip search queries and pagination links (indicated by '?')
            # if "/-/" in href and "?" not in href:
            #     # Resolve relative paths (e.g., '/web/basilicata/-/slug') into full URLs
            #     full_url = urljoin(url, href)
            #     links.append(full_url)

            full_url = urljoin(url, href)
            
            #  elif region == "Puglia":
                # 1. Define noise to ignore
            # noise = ["/whistleblowing", "/pagine/monitoraggi", "/note-legali", "/reclutamento-as-2025-2026", "/albo-online", "/accessibilita", "mailto:", "tel:", "/pagine/chi-siamo", "/pagine/elenchi-scuole", "/cookie-policy", "/archivio", "/disclaimer", "/contatti-2"]
            # # "/index.php?start=",
            
            # # 2. Check basics
            # has_no_noise = not any(p in full_url.lower() for p in noise)
            # is_internal = "istruzioneliguria.gov.it" in full_url
            
            # # 3. Identify actual news articles 
            
            # if is_internal and has_no_noise:
                
            #     # --- THE CRITICAL STEP ---
            #     # urljoin already turned '/index.php/...' into 'https://www.pugliausr.gov.it/index.php/...'
            #     # We just make sure it's clean (no fragments like #)
            #     clean_full_url = full_url.split('#')[0].strip()
                
            #     links.append(clean_full_url)

            noise = ["#", "facebook.com/", "twitter.com/", "linkedin.com/", "t.me/", "youtube.com/", "/pnrr/", "tel:", "mailto:","/wp-admin", "/urp", "/area-riservata" ,"/direttore-generale/","/il-personale-dellusr/","/incarichi-dirigenziali-non-generali-usr-sicilia/",
"/organigramma/","/organizzazione-per-funzioni/","/personale-amministrativo/","/sala-stampa/","/concorsi-e-bandi-di-gara/","/patrocini/","/protocolli-dintesa/","/dirigenti-scolastici/","/personale-scuola/","/pnrr/","/relazioni-sindacali/","/studenti-e-famiglie/","/esami-di-stato/","/organici-e-mobilita-personale-scuola/","/reclutamento/","/rete-scolastica/","/apprendistato/","/educazione-fisica-e-sportiva/","/diritto-allo-studio/","/dispersione-scolastica-e-disagio/","/orientamento/","/orientamento-al-lavoro-its-ifts/","/formazione-scuola-lavoro/","/amministrazione-digitale-e-privacy/","/equipe-formativa-territoriale-per-la-sicilia/",
"/fami/","/fondi-strutturali/","/innovazione-scuole/","/lingue-straniere-progetti-e-iniziative-internazionali/","/ordinamenti/","/progetti-educativi/","/dirigenti-scolastici/","/concorso-dirigenti-scolastici-2023-2/","/corso-intensivo-d-m-107-2023/","/concorsi-docenti/concorsi-infanzia-e-primaria/","/concorsi-docenti/concorsi-i-e-ii-grado/",
"/concorsi-docenti/concorsi-irc/","/personale-ata/","/personale-ata/bandi-ata-24-mesi/","/personale-ata/concorso-dsga-2024/","/personale-ata/internalizzazione-servizi-di-pulizia-ex-lsu/","/personale-amministrativo/","/personale-amministrativo/comandi-e-distacchi-presso-la-direzione-generale/","/formazione/","/formazione-dirigenti-scolastici/","/formazione-dirigenti-scolastici/formadsicilia/","/formazione-docenti/","/formazione-docenti/formazione-docenti-neoassunti/","/formazione-personale-ata/","/formazione-personale-amministrativo/","/iniziative-per-le-scuole/"]
                
            has_no_noise = not any(p in full_url.lower() for p in noise)
            is_internal = "usr.sicilia.it" in full_url
            if is_internal and has_no_noise and len(full_url.split('/')) > 4:
                if full_url.strip('/') != url.strip('/'):
                    links.append(full_url)
        
        # Deduplicate the list to ensure unique outputs
        return list(set(links))

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

# Example usage:
target_url = "https://www.usr.sicilia.it"
all_links = get_all_hrefs(target_url)


# Save the filtered links to a text file
with open("files/clean_txt/links_output_sicilia2.txt", "w",encoding="utf-8") as f:
    if all_links:
        for link in all_links:
            f.write(link + "\n")
        print(f"Saved {len(all_links)} filtered notice links to links_output_sicilia2.txt")
    else:
        f.write("No notice links found or an error occurred.")
        print("No notice links found to save.")