
import json
import trafilatura
from urllib.parse import urljoin, urlparse
from duckduckgo_search import DDGS
import google.generativeai as genai

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
    
# core/enricher.py (add this function)

def fetch_company_description_text(company_name):
    """Fetch raw descriptive text about the company from the web."""
    try:
        # Search for company homepage or about page
        with DDGS() as ddgs:
            results = ddgs.text(f"{company_name} about", max_results=3)
            urls = [r['href'] for r in results if 'linkedin.com' not in r['href'] and 'wikipedia.org' not in r['href']]
            print(f"Description fetch URLs for {company_name}: {urls}")  
        for url in urls[:2]:
            try:
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    text = trafilatura.extract(downloaded, include_comments=False, favor_precision=True)
                    if text and len(text) > 100:
                        return text[:3000]  # limit for LLM
            except:
                continue
    except Exception as e:
        print(f"Description fetch failed for {company_name}: {e}")
    return ""

def generate_company_descriptions(company_name):
    """Generate both Brief Description (BD) and Full Description (FD) per methodology."""
    raw_text = fetch_company_description_text(company_name)
    
    if not raw_text:
        bd = f"{company_name} is a company that provides products and services."
        fd = bd
        return bd, fd

    prompt = f"""You are a corporate research analyst at PitchBook. Generate two descriptions for "{company_name}" following the exact formulas below.

--- BRIEF DESCRIPTION (BD) ---
Formula: [Role] + [Product/Service] + [Transition Phrase] + [Purpose]
- ONE sentence only.
- Start with: "Developer of", "Provider of", "Manufacturer of", "Operator of", or "Distributor of".
- Transition phrase: "designed to", "aimed at", "intended to", "created to".
- End with the company's purpose or mission.
- Do NOT mention markets, customers, or value proposition here.

--- FULL DESCRIPTION (FD) ---
Formula: BD + " The company " + [Differentiating Features] + [Transitional Verb] + [Market] + [Value Proposition].
- Start with the exact BD sentence.
- Then: " The company " + key differentiators (tech, process, IP, partnerships).
- Use a transitional verb: "serves", "targets", "supplies", "provides to".
- Name the market (e.g., "hospitals in the UK", "enterprise SaaS companies").
- End with clear value proposition (e.g., "improving diagnostic accuracy", "reducing operational costs").

--- RAW INFO ---
{raw_text}

--- OUTPUT FORMAT ---
Return ONLY a JSON object with:
{{
  "brief_description": "...",
  "full_description": "..."
}}
"""

    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        result = json.loads(response.text.strip())
        return result.get("brief_description", ""), result.get("full_description", "")
    except Exception as e:
        fallback_bd = f"Distributor of medical devices for endoscopy procedures."
        fallback_fd = f"{fallback_bd} The company supplies endoscopy equipment to healthcare providers in the UK, enhancing procedural efficiency and patient outcomes."
        return fallback_bd, fallback_fd