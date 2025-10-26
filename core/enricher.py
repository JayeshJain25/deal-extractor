
import trafilatura
from urllib.parse import urljoin, urlparse
from duckduckgo_search import DDGS

def google_first_result(query):
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=1)
            for r in results:
                return r['href']
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
    return None

def get_website(company_name):
    try:
        url = google_first_result(f'"{company_name}" official website')
        if url:
            return url
        url = google_first_result(company_name)
        if url:
            domain = urlparse(url).netloc
            if domain and not any(x in domain for x in ['google.', 'wikipedia.', 'linkedin.', 'crunchbase.']):
                return f"https://{domain}"
    except Exception as e:
        print(f"Failed to get website for '{company_name}': {e}")
    return None

def classify_company_type(company_name, website):
    try:
        # Default
        entity_type = "Operating Company"
        is_pe_vc_firm = False

        # Heuristic: firm names
        firm_keywords = ['capital', 'partners', 'ventures', 'holdings', 'advisors', 'group', 'fund']
        if any(kw in company_name.lower() for kw in firm_keywords):
            entity_type = "PE/VC Firm"
            is_pe_vc_firm = True

        # Scrape website
        if website:
            for path in ["/", "/about", "/about-us"]:
                try:
                    url = urljoin(website, path)
                    downloaded = trafilatura.fetch_url(url)
                    if not downloaded:
                        continue
                    text = trafilatura.extract(downloaded, include_comments=False)
                    if not text:
                        continue
                    text_lower = text.lower()
                    if any(term in text_lower for term in ['private equity', 'venture capital', 'investment firm']):
                        if 'portfolio company' not in text_lower:
                            entity_type = "PE/VC Firm"
                            is_pe_vc_firm = True
                    break
                except Exception as e:
                    continue
        return {
            "entity_type": entity_type,
            "is_pe_vc_firm": is_pe_vc_firm,
            "website": website
        }
    except Exception as e:
        print(f"Error classifying '{company_name}': {e}")
        # Always return safe defaults
        return {
            "entity_type": "Operating Company",
            "is_pe_vc_firm": False,
            "website": website
        }

def enrich_company(company_name):
    if not company_name or not isinstance(company_name, str):
        return {
            "entity_type": "Operating Company",
            "is_pe_vc_firm": False,
            "website": None
        }
    try:
        website = get_website(company_name)
        return classify_company_type(company_name, website)
    except Exception as e:
        print(f"Enrichment failed for '{company_name}': {e}")
        return {
            "entity_type": "Operating Company",
            "is_pe_vc_firm": False,
            "website": None
        }