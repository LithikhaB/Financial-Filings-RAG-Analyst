"""
query.py
--------
Stage 3 of the pipeline: retrieval + generation (the "RAG" part).

FilingsRAG can wrap EITHER:
  - the persistent, on-disk collection built from data/raw_pdfs/ (used by
    the "Explore Filings" page), or
  - a temporary, in-memory collection built on the fly from a single
    uploaded PDF (used by the "Upload Your Own" page).

Both cases share identical retrieval and prompting logic — the only
difference is which Chroma collection object gets passed in.

SETUP NEEDED FIRST:
  1. Get a free Groq API key: https://console.groq.com  (no credit card)
  2. Copy .env.example to .env and paste your key in
"""

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "filings"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"

load_dotenv(BASE_DIR / ".env")

SYSTEM_PROMPT = """You are a financial filings analyst assistant.
You will be given excerpts from company annual reports / 10-K filings, each
tagged with [Company, Year, Page].

Rules:
- Answer ONLY using the provided excerpts. If the excerpts don't contain
  the answer, say so clearly — do not guess or use outside knowledge.
- Always cite the company, year, and page number(s) you used, like this:
  (Source: TCS, 2024, page: 47)
- Be concise and precise, especially with numbers.
"""


def load_embed_model() -> SentenceTransformer:
    """Loads the local, CPU-only sentence embedding model."""
    return SentenceTransformer(EMBED_MODEL_NAME, device="cpu")


def load_llm() -> ChatGroq:
    """Loads the Groq-hosted LLM client used for answer generation."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not found. Did you create a .env file from .env.example?")
    model_name = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    return ChatGroq(model=model_name, api_key=api_key, temperature=0)


def get_persistent_collection():
    """Opens the on-disk collection built by embed_store.py's batch mode."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(COLLECTION_NAME)


def new_ephemeral_collection(name: str):
    """
    Creates a fresh, in-memory (non-persistent) Chroma collection.
    Used for one-off uploaded PDFs — nothing is written to disk, and the
    collection disappears when the Streamlit session ends.
    """
    client = chromadb.EphemeralClient()
    return client.create_collection(name)


class FilingsRAG:
    def __init__(self, collection, embed_model: SentenceTransformer, llm: ChatGroq):
        self.collection = collection
        self.embed_model = embed_model
        self.llm = llm

    @classmethod
    def from_persistent_store(cls):
        return cls(get_persistent_collection(), load_embed_model(), load_llm())

    def get_companies(self) -> list:
        results = self.collection.get(include=["metadatas"])
        return sorted({meta["company"] for meta in results["metadatas"]})

    def get_years(self, company: str = None) -> list:
        where = {"company": company} if company else None
        results = self.collection.get(where=where, include=["metadatas"])
        return sorted({meta["year"] for meta in results["metadatas"]})

    def retrieve(self, question: str, k: int = 5, where: dict = None):
        query_embedding = self.embed_model.encode([question]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            where=where,
        )
        chunks = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            chunks.append({"text": doc, **meta})
        return chunks

    def _format_context(self, chunks):
        blocks = []
        for c in chunks:
            tag = f"[{c['company']}, {c['year']}, Page {c['page']}]"
            blocks.append(f"{tag}\n{c['text']}")
        return "\n\n---\n\n".join(blocks)

    def ask(self, question: str, k: int = 5, company_filter: str = None):
        where = {"company": company_filter} if company_filter else None
        chunks = self.retrieve(question, k=k, where=where)

        if not chunks:
            return "No relevant chunks found in the indexed document(s).", []

        context = self._format_context(chunks)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"CONTEXT:\n{context}\n\nQUESTION: {question}"),
        ]
        response = self.llm.invoke(messages)
        return response.content, chunks

    def compare_trend(self, company: str, metric_question: str, years: list, k_per_year: int = 3):
        """
        Retrieves chunks from EACH year for one company, then asks the LLM
        to summarize the trend across years rather than answer a single
        single-document lookup.
        """
        all_chunks = []
        for year in years:
            year_chunks = self.retrieve(
                metric_question, k=k_per_year, where={"$and": [{"company": company}, {"year": year}]}
            )
            all_chunks.extend(year_chunks)

        if not all_chunks:
            return "No relevant chunks found for that company/years.", []

        context = self._format_context(all_chunks)
        trend_prompt = (
            f"Using ONLY the context below, describe the trend in '{metric_question}' "
            f"for {company} across the years {', '.join(years)}. "
            f"Structure your answer year-by-year, then give a one-line overall trend summary. "
            f"Cite sources for every figure."
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"CONTEXT:\n{context}\n\nTASK: {trend_prompt}"),
        ]
        response = self.llm.invoke(messages)
        return response.content, all_chunks


if __name__ == "__main__":
    rag = FilingsRAG.from_persistent_store()

    print("\n--- Single question test ---")
    answer, sources = rag.ask("What were the main risk factors mentioned?")
    print(answer)
