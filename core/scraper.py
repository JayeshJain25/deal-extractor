# core/scraper.py
import time
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def extract_text_and_links(url):
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise Exception(f"Failed to fetch URL: {url}")
    
    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        favor_precision=True
    )
    
    if not text:
        raise Exception("No extractable text found")
    
    links = extract_deal_links(downloaded, url)
    return {"text": text, "links": links}

def extract_deal_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    keywords = ['press', 'release', 'announcement', 'filing', 'acquisition', 'merger', 'divestiture', 'sold', 'transaction', 'news']
    links = set()
    base_domain = urlparse(base_url).netloc

    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        anchor = (a.get_text() or '').lower()
        url_lower = full_url.lower()

        if any(kw in anchor or kw in url_lower for kw in keywords):
            if (urlparse(full_url).netloc == base_domain) or any(t in full_url for t in ['sec.gov', 'prnewswire.com', 'businesswire.com', 'reuters.com', 'bloomberg.com']):
                links.add(full_url)
    return list(links)[:2]

def scrape_with_context(trigger_url):
    visited = set()
    all_content = []

    main = extract_text_and_links(trigger_url)
    all_content.append({"url": trigger_url, "text": main["text"]})
    visited.add(trigger_url)

    for link in main["links"]:
        if link not in visited:
            try:
                print(f"Following: {link}")
                child = extract_text_and_links(link)
                all_content.append({"url": link, "text": child["text"]})
                visited.add(link)
                time.sleep(1)
            except Exception as e:
                print(f"Failed to scrape child link: {e}")
    return all_content