"""
common.py
---------
Shared setup used by every page: page config, styling, and cached
loaders for the embedding model / LLM / persistent vector store.

Import this at the top of every page file:
    from common import apply_page_style, get_rag
"""

from pathlib import Path

import streamlit as st

from query import FilingsRAG, get_persistent_collection, load_embed_model, load_llm

STYLE_PATH = Path(__file__).parent / "style.css"

# Loaded as a <link> tag rather than a CSS @import: @import statements
# inside a <style> block that gets injected into the page after load
# (which is what st.markdown does) are unreliable across browsers and
# often silently fail to fetch. A <link> tag doesn't have that problem.
FONT_LINK = (
    '<link rel="stylesheet" '
    'href="https://fonts.googleapis.com/css2?'
    'family=Lora:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap">'
)


def load_css() -> str:
    return STYLE_PATH.read_text(encoding="utf-8")


def apply_page_style(page_title: str):
    st.set_page_config(page_title=f"{page_title} · Filings RAG Analyst", layout="wide")
    st.markdown(FONT_LINK, unsafe_allow_html=True)
    st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### Filings Analyst")
        st.caption("Ask a filing a question, get a sourced answer.")
        st.divider()


@st.cache_resource(show_spinner="Loading the local embedding model...")
def get_embed_model():
    """Cached so the ~80MB model is loaded into memory only once per session."""
    return load_embed_model()


@st.cache_resource(show_spinner="Connecting to the language model...")
def get_llm():
    return load_llm()


@st.cache_resource(show_spinner="Getting everything ready...")
def get_rag():
    """
    Cached loader for the main, persistent-store RAG instance.
    Returns None if the persistent collection hasn't been built yet
    (i.e. ingest.py + embed_store.py haven't been run), so pages can
    show a plain message instead of crashing.
    """
    try:
        collection = get_persistent_collection()
    except Exception:
        return None
    return FilingsRAG(collection, get_embed_model(), get_llm())


def render_sources(chunks):
    """Renders retrieved source chunks as citation cards."""
    for c in chunks:
        st.markdown(
            f"""<div class="source-card">
                    <div class="source-tag">{c['company']} &middot; {c['year']} &middot; page {c['page']}</div>
                    <div class="source-text">{c['text'][:450]}{'...' if len(c['text']) > 450 else ''}</div>
                </div>""",
            unsafe_allow_html=True,
        )
