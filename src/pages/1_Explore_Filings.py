"""
pages/1_Explore_Filings.py
---------------------------
Ask questions of, or compare trends across, the filings that have already
been indexed into the persistent vector store (via ingest.py + embed_store.py
run from the command line).
"""

import streamlit as st

from common import apply_page_style, get_rag, render_sources

apply_page_style("Explore Filings")

st.title("Ask the filings")
st.caption("Question the reports that are already loaded in.")

rag = get_rag()

if rag is None:
    st.warning(
        "No filings are indexed yet. Run `python src/ingest.py` and then "
        "`python src/embed_store.py` from the project root after adding PDFs "
        "to `data/raw_pdfs/`."
    )
    st.stop()

companies = rag.get_companies()

if not companies:
    st.warning(
        "No filings are indexed yet. Run `python src/ingest.py` and then "
        "`python src/embed_store.py` from the project root after adding PDFs "
        "to `data/raw_pdfs/`."
    )
    st.stop()

tab_ask, tab_compare = st.tabs(["Ask a question", "Compare across years"])

with tab_ask:
    st.markdown("Ask about one filing, or all of them at once.")

    col1, col2 = st.columns([1, 2])
    with col1:
        company_filter = st.selectbox("Restrict to a company (optional)", ["All companies"] + companies)
    with col2:
        question = st.text_input(
            "Your question",
            placeholder="What were the main risk factors mentioned?",
        )

    if st.button("Ask", key="ask_button") and question:
        with st.spinner("Retrieving relevant filing sections and generating an answer..."):
            filter_value = None if company_filter == "All companies" else company_filter
            answer, chunks = rag.ask(question, company_filter=filter_value)

        st.subheader("Answer")
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

        st.subheader(f"Sources ({len(chunks)})")
        render_sources(chunks)

with tab_compare:
    st.markdown("See how something changed for one company, year over year.")

    company = st.selectbox("Company", companies, key="compare_company")
    available_years = rag.get_years(company)
    years = st.multiselect("Years to compare", available_years, default=available_years, key="compare_years")
    metric = st.text_input("What to compare", placeholder="debt to equity ratio", key="compare_metric")

    if st.button("Compare", key="compare_button") and metric and years:
        with st.spinner(f"Pulling data across {', '.join(years)} and summarizing the trend..."):
            answer, chunks = rag.compare_trend(company, metric, years)

        st.subheader("Trend Summary")
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

        st.subheader(f"Sources ({len(chunks)})")
        render_sources(chunks)
