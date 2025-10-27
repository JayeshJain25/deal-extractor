import streamlit as st
import pandas as pd
from core.scraper import scrape_with_context, extract_text_and_links
from core.analyzer import extract_deal_info
from core.enricher import enrich_company, generate_company_descriptions
from core.classifier import is_in_scope_merger_acquisition, classify_deal_type, determine_round_status

st.set_page_config(page_title="M&A Deal Tracker", layout="wide")
st.title("🔗 Automated M&A Deal Classifier")
st.write("Paste a deal announcement URL to extract and classify.")

url = st.text_input(
    "Article URL:",
    value="https://globallegalchronicle.com/fujifilm-healthcare-uk-acquires-endoscopy-business-from-aquilant-endoscopy/"
)

if st.button("Analyze Deal"):
    if not url.strip():
        st.error("Please enter a URL.")
    else:
        try:
            # Stage 1: Initial extraction to get company names
            with st.spinner("🔍 Parsing article..."):
                initial_sources = [{"url": url, "text": extract_text_and_links(url)["text"]}]
                deals = extract_deal_info(initial_sources)
            
            if not deals:
                st.warning("No valid deal found in the article.")
            else:
                results = []
                for deal in deals:
                    target = deal["company_name"]
                    acquirer = deal["acquirer_or_counterparty"]

                    # Stage 2: Re-scrape with context
                    with st.spinner(f"🌐 Fetching relevant pages for {target} and {acquirer}..."):
                        context_companies = [target, acquirer]
                        full_sources = scrape_with_context(url, context_companies)

                    # Stage 3: Re-extract with full context
                    with st.spinner("🧠 Analyzing deal details..."):
                        final_deals = extract_deal_info(full_sources)
                        final_deal = final_deals[0] if final_deals else deal

                    # Enrich target and acquirer
                    with st.spinner(f"🏢 Enriching company info for {target}..."):
                        target_info = enrich_company(target)
                    with st.spinner(f"🏢 Enriching company info for {acquirer}..."):
                        acquirer_info = enrich_company(acquirer)

                    # Classify deal
                    in_scope = is_in_scope_merger_acquisition(target_info, acquirer_info)
                    deal_type = classify_deal_type(target_info, acquirer_info, final_deal["summary"])
                    round_status = determine_round_status(final_deal["summary"])

                    # Generate descriptions
                    with st.spinner(f"📝 Generating company descriptions for {target}..."):
                        brief_desc, full_desc = generate_company_descriptions(target)

                    result = {
                        "company_name": target,
                        "acquirer": acquirer,
                        "brief_description": brief_desc,
                        "full_description": full_desc,
                        "deal_type": deal_type,
                        "round_status": round_status,
                        "in_merger_acquisition_scope": in_scope,
                        "target_entity_type": target_info["entity_type"],
                        "acquirer_entity_type": acquirer_info["entity_type"],
                        "summary": final_deal["summary"]
                    }
                    results.append(result)

                df = pd.DataFrame(results)
                st.success(f"✅ Found {len(deals)} deal(s)")
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {str(e)}")
