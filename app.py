import streamlit as st
import pandas as pd
from core.scraper import scrape_with_context
from core.analyzer import extract_deal_info

st.set_page_config(page_title="Deal Extractor", layout="wide")
st.title("🔗 M&A Deal Extractor")
st.write("Paste a news/article link to extract structured deal info.")

url = st.text_input(
    "Enter article URL:",
    value="https://globallegalchronicle.com/fujifilm-healthcare-uk-acquires-endoscopy-business-from-aquilant-endoscopy/"
)

if st.button("Extract Deal Info"):
    if not url:
        st.error("Please enter a URL.")
    else:
        try:
            with st.spinner("Scraping content..."):
                sources = scrape_with_context(url)
            
            with st.spinner("Analyzing with AI..."):
                deals = extract_deal_info("Main company", sources)
            
            if deals:
                df = pd.DataFrame(deals)
                required_cols = ["company_name", "acquirer_or_counterparty", "deal_type", "announced_date", "status", "summary"]
                for col in required_cols:
                    if col not in df.columns:
                        df[col] = None
                df = df[required_cols]
                st.success(f"✅ Found {len(deals)} deal(s)")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No deal found.")
        except Exception as e:
            st.error(f"Error: {str(e)}")