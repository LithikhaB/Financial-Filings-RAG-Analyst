"""
embed_store.py
--------------
Stage 2 of the pipeline: turn text chunks into vector embeddings and store
them in a ChromaDB collection.

Used two ways, same reasoning as ingest.py:
  1. Batch mode (CLI) — embeds every chunk from data/processed/chunks.jsonl
     into the persistent, on-disk collection used by the main "Explore
     Filings" page.
  2. Live mode — the "Upload your own PDF" page calls embed_chunks() on a
     freshly extracted, single-document chunk list, storing it in a
     temporary, in-memory collection scoped to that browser session only.

WHY all-MiniLM-L6-v2:
  A small (~80MB), CPU-friendly sentence embedding model. No GPU required;
  a few hundred chunks embed in well under a minute on a laptop CPU.
"""

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent.parent
CHUNKS_PATH = BASE_DIR / "data" / "processed" / "chunks.jsonl"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "filings"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64  # safe batch size for CPU


def load_chunks_from_file():
    records = []
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def embed_chunks(records, collection, embed_model, batch_size=BATCH_SIZE, progress_callback=None):
    """
    Core reusable embedding function.

    records: list of chunk dicts (from ingest.extract_chunks_from_pdf or
             load_chunks_from_file).
    collection: an already-created Chroma collection (persistent or
                in-memory — this function doesn't care which).
    embed_model: a loaded SentenceTransformer instance.
    progress_callback: optional function(chunks_done, chunks_total).
    """
    texts = [r["text"] for r in records]
    ids = [f"chunk-{i}" for i in range(len(records))]
    metadatas = [
        {"company": r["company"], "year": r["year"], "page": r["page"], "source_file": r["source_file"]}
        for r in records
    ]

    total = len(texts)
    for start in range(0, total, batch_size):
        end = start + batch_size
        batch_embeddings = embed_model.encode(texts[start:end], show_progress_bar=False).tolist()

        collection.add(
            ids=ids[start:end],
            embeddings=batch_embeddings,
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        if progress_callback:
            progress_callback(min(end, total), total)

    return collection


def build_persistent_vector_store():
    """Batch mode: rebuilds the on-disk collection from chunks.jsonl."""
    records = load_chunks_from_file()
    if not records:
        print(f"No chunks found at {CHUNKS_PATH}. Run ingest.py first.")
        return

    print(f"Loading embedding model '{EMBED_MODEL_NAME}' (CPU)...")
    embed_model = SentenceTransformer(EMBED_MODEL_NAME, device="cpu")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)  # fresh start, avoids duplicates
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    print(f"Embedding {len(records)} chunks in batches of {BATCH_SIZE}...")
    progress = tqdm(total=len(records), desc="Embedding + storing")

    def cb(done, total):
        progress.n = done
        progress.refresh()

    embed_chunks(records, collection, embed_model, progress_callback=cb)
    progress.close()

    print(f"\nDone. Vector store saved to {CHROMA_DIR} ({len(records)} chunks indexed).")


if __name__ == "__main__":
    build_persistent_vector_store()
