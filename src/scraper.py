import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MyScraperBot/1.0)"}
SITEMAP_URL = "https://www.able.co/sitemap.xml"

def get_urls_from_sitemap(sitemap_url):
    """Extracts all URLs from the given sitemap."""
    response = requests.get(sitemap_url, headers=HEADERS)
    urls = []
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [elem.text for elem in root.findall(".//ns:loc", namespaces)]
    
    return urls

def extract_text_from_page(url):
    """Extracts all headers and paragraphs from a webpage."""
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    
    extracted_data = []
    
    for tag in soup.find_all(["h1", "h2", "h3", "p"]):
        tag_name = tag.name.upper()  #"H1", "H2", "H3", "P"
        text = tag.get_text(strip=True)
        
        if text:
            extracted_data.append(f"{tag_name}: {text}")

    return extracted_data

def extract_from_site():
    """Extracts raw text from all pages and saves it."""
    urls = get_urls_from_sitemap(SITEMAP_URL)
    all_text = []

    for url in urls:
        print(f"Extracting from: {url}")
        text_data = extract_text_from_page(url)
        if text_data:
            all_text.extend(text_data)
    
    #save as a txt file
    with open("data/raw_text.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_text))

    print(f"Extracted raw text saved to data/raw_text.txt!")

if __name__ == "__main__":
    extract_from_site()
