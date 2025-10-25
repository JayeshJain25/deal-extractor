# core/analyzer.py (Gemini - Optimized)
import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_deal_info(company_context, sources):
    combined = "\n\n---SOURCE BREAK---\n\n".join(
        f"[{i+1}] ({s['url']}): {s['text'][:2500]}" 
        for i, s in enumerate(sources)
    )

    prompt = f"""You are an expert M&A research analyst at a top-tier investment firm. Extract structured deal data from the sources below.

**Rules:**
1. Only report actual transactions — ignore financing, advisory roles, or rumors unless a deal is confirmed.
2. The "company_name" must be the **legal name of the target company** (the entity selling, being acquired, or forming a JV).  
   - Example: If "Acquirer bought the cloud division of XYZ Corp", then company_name = "XYZ Corp".
   - Never use "business unit", "division", or "assets of..." as company_name.
3. "acquirer_or_counterparty" is the buyer, investor, JV partner, or financing recipient (if relevant).
4. Classify deal_type strictly as one of:
   - "M&A"
   - "M&A operating subsidiary"
   - "Joint ventures"
   - "PIPE round"
   - "STP (Secondary Transaction Private)"
   - "Corporate divestiture"
5. For "acquisition financing" announcements (e.g., bank provides loan for an acquisition), **do not report a deal** unless the underlying acquisition is described.
6. "status": Use "Closed" only if the text says "completed", "closed", or "has acquired". Use "Announced" if "to acquire", "plans to", or "announced". Otherwise, omit.
7. "announced_date": Only include if an explicit date (e.g., "on September 30, 2025") is given. Otherwise, use null.
8. Return ONLY a JSON list. If no valid deal, return [].

**Output fields (exact names):**
- "company_name"
- "acquirer_or_counterparty"
- "deal_type"
- "announced_date" (YYYY-MM-DD or null)
- "status"
- "summary" (1–2 factual sentences)
- "source_urls" (list of all source URLs used)

Sources:
{combined}
"""

    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1  # even more deterministic
        )
    )

    try:
        return json.loads(response.text)
    except Exception as e:
        match = re.search(r"\[.*\]", response.text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return []