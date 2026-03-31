import requests
from bs4 import BeautifulSoup

def get_all_hrefs(url):

    # This tells the website you are a standard Chrome browser on Windows
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
        # 1. Fetch the page content
        response = session.get(url, timeout=20)
        response.raise_for_status() # Check for HTTP errors
        print(f"Successfully fetched {url}")
        
        # 2. Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. Find all <a> tags and extract the 'href' attribute
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                links.append(href)
        
        return list(set(links))

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

# Example usage:
target_url = "https://www.usr.sicilia.it/tutte-le-news/"
# target_url = "https://www.usr.sicilia.it"
# target_url = "https://www.mim.gov.it/web/basilicata/notizie"
# target_url = "https://nairametrics.com/"
# target_url = "https://www.nairaland.com"
all_links = get_all_hrefs(target_url)

# for l in all_links:
#     print(l)

            # Save the links to a text file
with open("files/txt/see_all_links_output_Sicilia1_new.txt", "w", encoding="utf-8") as f:
    if all_links:
        for link in all_links:
            f.write(link + "\n")
        print(f"Saved {len(all_links)} links to see_all_links_output_Sicilia1_new.txt")
    else:
        f.write("No links found or error occurred.")
        print("No links found to save.")