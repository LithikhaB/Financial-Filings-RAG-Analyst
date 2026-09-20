"""
app.py
------
Home page. Run this with `streamlit run src/app.py` — Streamlit turns
everything in src/pages/ into the other pages automatically.
"""

import streamlit as st

from common import apply_page_style

apply_page_style("Home")

st.title("What's a 10-K, anyway?")
st.caption("A quick primer, for anyone opening one of these for the first time.")

st.markdown("---")

st.header("The short version")
st.markdown(
    """
Every company listed on a US stock exchange has to file one of these with
the SEC every year. It's the annual report, but the real one — not the
glossy version with the CEO letter and nice photos, the one written for
lawyers and regulators. Same company, same year, but far more honest and
far more detailed.

It's also public. Anyone can pull up any company's 10-K for free, no
account needed.
"""
)

st.header("Why bother reading it")
st.markdown(
    """
A few reasons this beats a news article or an earnings call:

- Every company files it the same way, so you can actually compare one
  year to the next, or one company to another.
- The numbers are audited. A press release isn't.
- Companies take these filings seriously because getting them wrong has
  real legal consequences, which tends to keep the language honest — the
  risk section in particular is often more candid than you'd expect.
"""
)

st.header("What's actually in one")
st.markdown("A 10-K is broken into numbered \"Items.\" The ones worth knowing:")

structure = [
    ("Business (Item 1)", "What the company actually does, day to day."),
    ("Risk Factors (Item 1A)", "Everything that could go wrong, in the company's own words. Usually the most interesting section."),
    ("MD&A (Item 7)", "Management explaining the numbers in something closer to plain English."),
    ("Financial Statements (Item 8)", "The audited income statement, balance sheet, and cash flow statement, plus notes."),
    ("Controls and Procedures (Item 9A)", "How the company checks its own numbers are right."),
    ("Exhibits (Item 15)", "Contracts, subsidiary lists, and other supporting paperwork."),
]
for title, desc in structure:
    st.markdown(f"**{title}** — {desc}")

st.header("How people actually read these")
st.markdown(
    """
Nobody reads all 300 pages start to finish. A more realistic approach:

1. Start with Risk Factors. It tells you what could hurt the business,
   straight from the company.
2. Read the MD&A next, before the raw numbers — it gives you the story
   management wants to tell, which you can then check against the actual
   figures.
3. Use the financial statements to check the story, not to discover it.
4. Search instead of scrolling. Most people just Ctrl+F for the section
   or number they need — which is basically what this tool automates.
"""
)

st.header("Where to find them")
st.markdown(
    """
Every US public filing lives on the SEC's EDGAR system, free to search:

- Search across all companies: [sec.gov/edgar/search](https://www.sec.gov/edgar/search/)
- Browse by company or ticker: [sec.gov/edgar/browse](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany)

Filings show up as HTML pages rather than PDFs. To use one here, open it
in your browser, print it, and save as PDF with all pages included.
"""
)

st.markdown("---")
st.markdown("Head to **Explore Filings** on the left to try it on a filing already loaded, or **Upload Your Own** to try it on a PDF of your own.")
