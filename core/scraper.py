# core/scraper.py

import time
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def extract_text_and_links(url):
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise Exception(f"Failed to fetch URL: {url}")
    text = trafilatura.extract(downloaded, include_comments=False, include_tables=True, favor_precision=True)
    if not text:
        raise Exception("No extractable text found")
    return {"text": text, "html": downloaded}  # Return raw HTML for link extraction

def extract_deal_links(html, base_url, context_companies=None):
    """
    Extract only links that mention one of the context_companies.
    """
    if context_companies is None:
        context_companies = []

    soup = BeautifulSoup(html, 'html.parser')
    keywords = ['press', 'release', 'announcement', 'filing', 'acquisition', 'merger', 'divestiture', 'sold', 'transaction']
    links = set()
    base_domain = urlparse(base_url).netloc

    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        anchor_text = (a.get_text() or '').strip()
        link_text = (anchor_text + " " + full_url).lower()

        # Only follow if it mentions a context company
        if context_companies:
            if not any(company.lower() in link_text for company in context_companies):
                continue

        if any(kw in anchor_text.lower() or kw in full_url.lower() for kw in keywords):
            if (urlparse(full_url).netloc == base_domain) or any(t in full_url for t in ['sec.gov', 'prnewswire.com', 'businesswire.com']):
                links.add(full_url)

    return list(links)[:2]

def scrape_with_context(trigger_url, context_companies=None):
    """
    Scrape trigger URL + relevant child links (filtered by context_companies).
    """
    visited = set()
    all_content = []

    # Scrape main page
    main = extract_text_and_links(trigger_url)
    all_content.append({"url": trigger_url, "text": main["text"]})
    visited.add(trigger_url)

    # Extract and follow relevant links
    links = extract_deal_links(main["html"], trigger_url, context_companies)
    for link in links:
        if link not in visited:
            try:
                child = extract_text_and_links(link)
                all_content.append({"url": link, "text": child["text"]})
                visited.add(link)
                time.sleep(1)
            except Exception as e:
                print(f"Failed to scrape child link {link}: {e}")
                continue

    return all_content