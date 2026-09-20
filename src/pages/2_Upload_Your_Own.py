"""
pages/2_Upload_Your_Own.py
----------------------------
Lets a visitor upload their own PDF (any document, not just filings already
indexed by the maintainer) and ask questions of it directly, without
touching the command line.

The document is processed entirely in memory for the duration of the
browser session: nothing is written to disk, and nothing is added to the
main persistent collection used by the "Explore Filings" page.

This page also visibly walks through each pipeline stage as it runs, since
watching "PDF -> chunks -> embeddings -> ready to query" happen live is the
clearest way to understand what the tool is actually doing.
"""

import streamlit as st

from common import apply_page_style, get_embed_model, get_llm, render_sources
from ingest import extract_chunks_from_pdf
from embed_store import embed_chunks
from query import FilingsRAG, new_ephemeral_collection

apply_page_style("Upload Your Own")

st.title("Try it on your own PDF")
st.caption("Nothing gets saved — once you close the tab, it's gone.")

with st.expander("How this is different from Explore Filings", expanded=False):
    st.markdown(
        """
        The **Explore Filings** page queries a pre-built library of filings
        that the project maintainer has already processed and stored
        permanently.

        This page runs the exact same extraction, chunking, and embedding
        pipeline, but **live, on a single document you upload right now** —
        stored only in memory for this browser session. Refresh the page
        and it's gone. This is the right place to try the tool on a filing,
        report, or any other PDF that isn't already indexed.
        """
    )

st.markdown("---")

col_upload, col_meta = st.columns([2, 1])
with col_upload:
    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])
with col_meta:
    company_name = st.text_input("Company / document label", placeholder="e.g. Citigroup")
    doc_year = st.text_input("Year (optional)", placeholder="e.g. 2025")

process_clicked = st.button("Process Document", disabled=uploaded_file is None)

if "upload_rag" not in st.session_state:
    st.session_state.upload_rag = None
    st.session_state.upload_label = None

if process_clicked and uploaded_file is not None:
    label = company_name.strip() or uploaded_file.name
    year = doc_year.strip() or "unknown"

    status_box = st.status("Starting pipeline...", expanded=True)

    # ---- Stage 1: Extraction ----
    status_box.update(label="Stage 1 of 3 — Extracting text from PDF")
    extract_progress = status_box.progress(0, text="Reading pages...")

    def extraction_progress_cb(current_page, total_pages):
        extract_progress.progress(
            current_page / total_pages, text=f"Read page {current_page} of {total_pages}"
        )

    chunks = extract_chunks_from_pdf(
        uploaded_file, company=label, year=year, source_label=uploaded_file.name,
        progress_callback=extraction_progress_cb,
    )
    status_box.write(f"Extracted {len(chunks)} text chunks from {uploaded_file.name}.")

    if not chunks:
        status_box.update(label="No extractable text found", state="error")
        st.error(
            "No text could be extracted from this PDF. It may be a scanned "
            "image without a text layer — try a PDF exported directly from "
            "a browser or word processor instead."
        )
        st.stop()

    # ---- Stage 2: Embedding ----
    status_box.update(label="Stage 2 of 3 — Generating embeddings (CPU)")
    embed_model = get_embed_model()
    embed_progress = status_box.progress(0, text="Embedding chunks...")

    def embed_progress_cb(done, total):
        embed_progress.progress(done / total, text=f"Embedded {done} of {total} chunks")

    collection = new_ephemeral_collection(f"upload-{uploaded_file.name}")
    embed_chunks(chunks, collection, embed_model, progress_callback=embed_progress_cb)

    # ---- Stage 3: Ready ----
    status_box.update(label="Stage 3 of 3 — Finalizing")
    llm = get_llm()
    st.session_state.upload_rag = FilingsRAG(collection, embed_model, llm)
    st.session_state.upload_label = label

    status_box.update(label="Document ready to query", state="complete", expanded=False)

st.markdown("---")

if st.session_state.upload_rag is not None:
    st.success(f"'{st.session_state.upload_label}' is indexed and ready.")

    question = st.text_input(
        "Ask a question about this document",
        placeholder="What does this document say about revenue growth?",
    )

    if st.button("Ask") and question:
        with st.spinner("Retrieving relevant sections and generating an answer..."):
            answer, chunks = st.session_state.upload_rag.ask(question)

        st.subheader("Answer")
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

        st.subheader(f"Sources ({len(chunks)})")
        render_sources(chunks)
else:
    st.markdown("Drop a PDF in above and hit **Process Document** when you're ready.")
