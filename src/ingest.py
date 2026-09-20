"""
ingest.py
---------
Stage 1 of the pipeline: turn a PDF into page-tagged, overlapping text chunks.

This module is used two ways in the project:
  1. As a command-line script (batch mode) — processes every PDF in
     data/raw_pdfs/ and writes data/processed/chunks.jsonl.
  2. As an importable module — the "Upload your own PDF" page calls
     extract_chunks_from_pdf() directly on a single uploaded file.

Keeping the extraction logic in one place means the batch pipeline and
the live upload feature can never drift apart or behave differently.
"""

import json
import re
from pathlib import Path

import pdfplumber
from tqdm import tqdm

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_pdfs"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "chunks.jsonl"

CHUNK_SIZE_CHARS = 1800    # roughly 450-500 tokens
CHUNK_OVERLAP_CHARS = 250  # keeps context from being cut mid-sentence at chunk boundaries


def parse_filename(pdf_path: Path):
    """
    'TCS_2024.pdf' -> ('TCS', '2024')
    Falls back gracefully if the filename doesn't match the pattern.
    """
    stem = pdf_path.stem
    match = re.match(r"^(.*)_(\d{4})$", stem)
    if match:
        company, year = match.groups()
        return company.replace("_", " "), year
    return stem, "unknown"


def chunk_text(text: str, chunk_size=CHUNK_SIZE_CHARS, overlap=CHUNK_OVERLAP_CHARS):
    """Sliding-window chunker over characters."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def extract_chunks_from_pdf(pdf_source, company: str, year: str, source_label: str, progress_callback=None):
    """
    Core reusable extraction function.

    pdf_source: a file path (str/Path) OR a file-like object (e.g. from
                Streamlit's file_uploader) — pdfplumber accepts both.
    company, year: explicit metadata tags for every chunk produced.
    source_label: a human-readable name to store alongside each chunk
                  (e.g. the original filename).
    progress_callback: optional function(current_page, total_pages) called
                        after each page is processed — used by the Streamlit
                        upload page to show live progress.

    Returns: list of chunk dicts.
    """
    records = []
    with pdfplumber.open(pdf_source) as pdf:
        total_pages = len(pdf.pages)
        for page_num, page in enumerate(pdf.pages, start=1):
            raw_text = (page.extract_text() or "").strip()
            if raw_text:
                for chunk in chunk_text(raw_text):
                    records.append({
                        "company": company,
                        "year": year,
                        "page": page_num,
                        "text": chunk,
                        "source_file": source_label,
                    })
            if progress_callback:
                progress_callback(page_num, total_pages)
    return records


def process_pdf(pdf_path: Path):
    """Batch-mode wrapper: derives company/year from the filename."""
    company, year = parse_filename(pdf_path)
    return extract_chunks_from_pdf(pdf_path, company, year, pdf_path.name)


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(RAW_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {RAW_DIR}. Drop your 10-K / annual report PDFs there first.")
        return

    all_records = []
    for pdf_path in tqdm(pdf_files, desc="Extracting PDFs"):
        records = process_pdf(pdf_path)
        all_records.extend(records)
        print(f"  {pdf_path.name}: {len(records)} chunks")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nDone. {len(all_records)} total chunks written to {OUT_PATH}")


if __name__ == "__main__":
    main()
