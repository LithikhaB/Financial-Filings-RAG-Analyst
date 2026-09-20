"""
pages/4_About_the_Project.py
-------------------------------
Explains what this project is, what Retrieval-Augmented Generation (RAG)
is and why it's used here, and how the citation mechanism works.
"""

import streamlit as st

from common import apply_page_style

apply_page_style("About the Project")

st.title("What's actually going on here")
st.caption("The technique behind the tool, and how it's able to cite its sources.")

st.markdown("---")

st.header("What this project is")
st.markdown(
    """
This is a question-answering tool built on top of company annual reports
(10-K filings). Rather than manually searching through a document that can
run several hundred pages long, a reader can ask a plain-language question
and receive an answer drawn directly from the filing — along with the exact
page it came from.

It is built to run entirely on a standard laptop CPU, using only free
components: no paid API subscriptions, no GPU, and no dedicated server.
"""
)

st.header("The problem with asking a language model directly")
st.markdown(
    """
Large language models are trained on a fixed snapshot of text up to some
past date, and they do not have access to any specific company's latest
filing unless it happens to already exist in their training data — and
even then, they cannot reliably reproduce exact figures or quote specific
pages. Asked directly, a model might describe a company's finances
*plausibly* without them being *accurate* — a well-known failure mode
often called "hallucination."

This project avoids that failure mode by never asking the model to answer
from its own memory at all.
"""
)

st.header("What Retrieval-Augmented Generation (RAG) actually is")
st.markdown(
    """
RAG is a two-step approach that separates **finding information** from
**writing an answer**:

**Step 1 — Retrieval.** Before the language model is asked anything, the
system searches a document that has already been broken into small pieces
and mathematically indexed, and pulls out the specific pieces most relevant
to the question. This step involves no language model at all — it is a
mathematical similarity search over vector representations of text.

**Step 2 — Generation.** Only now is a language model involved. It is
given the question *together with* the retrieved excerpts, and instructed
to answer using only that material. The model's job shrinks from "know
everything about this company" to "summarize and explain what's in front
of you" — a much more reliable task.

This is why the technique is named the way it is: retrieval happens first
and augments what the generation step has to work with.
"""
)

st.header("What an embedding is, in plain terms")
st.markdown(
    """
To make the retrieval step possible, every chunk of text — and every
question a user asks — is converted into an **embedding**: a list of a few
hundred numbers that represents the *meaning* of that text, produced by a
model trained specifically for this purpose (all-MiniLM-L6-v2 in this
project).

Two pieces of text with similar meaning end up with numerically similar
embeddings, even if they don't share the same words. This is what allows a
question like *"how much debt does the company carry?"* to correctly
retrieve a passage that says *"total borrowings increased to..."* — the
words don't match, but the underlying meaning does. These embeddings are
stored in a **vector database** (ChromaDB in this project), which is built
specifically to search efficiently across meanings rather than keywords.
"""
)

st.header("How the citation mechanism works")
st.markdown(
    """
Every citation shown alongside an answer traces back to a single design
decision made at the very first stage of the pipeline: **text is extracted
page by page, never as one combined blob.** That means every chunk of text,
from the moment it is created, is permanently tagged with:

- which document (company / filing) it came from
- which year that filing covers
- which exact page it was extracted from

That tag travels with the chunk through embedding, through storage, and
through retrieval. When the language model is asked to answer a question,
it is explicitly instructed to include this tag with any claim it makes —
so a citation like *(Source: Citigroup, 2025, p.47)* is not the model
"remembering" where something came from; it is the model reading the tag
that was already attached to the text it was given, and passing it along.

This is also why every answer is shown next to the raw source excerpts —
so a reader never has to simply trust the citation, they can read the
underlying text themselves and verify it directly.
"""
)

st.header("Design choices, and why")
choices = [
    ("Small, local embedding model (not a paid embedding API)",
     "Keeps the project free to run and avoids sending document content to a third-party API for this step."),
    ("Chunk-level, page-tagged storage (not whole-document storage)",
     "Enables both precise retrieval and exact, page-level citations — neither is possible if the document is stored as one block of text."),
    ("A free, hosted LLM for generation (rather than a local LLM)",
     "Generation quality benefits from a larger model than a CPU-only laptop could run locally at usable speed; a free-tier hosted model bridges that gap at zero cost."),
    ("Retrieval restricted strictly to the provided context",
     "The prompt explicitly instructs the model not to use outside knowledge, so an answer is either grounded in the filing or the system says it couldn't find the answer — it does not guess."),
]
for title, desc in choices:
    st.markdown(f"**{title}**  \n{desc}")

st.markdown("---")
st.markdown("For the stage-by-stage version of this with a diagram, check out **How It Works**.")
