"""
pages/3_How_It_Works.py
--------------------------
Shows the pipeline as a single diagram, with a short explanation of the
reasoning underneath it.

Drop a diagram image at src/assets/pipeline_diagram.png (or .jpg) and it
will render automatically. See the project README for a ready-to-use
prompt for generating that image.
"""

from pathlib import Path

import streamlit as st

from common import apply_page_style

apply_page_style("How It Works")

st.title("How it fits together")
st.caption("From a PDF on disk to an answer with a page number attached.")

st.markdown("---")

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
diagram_path = None
for ext in ("png", "jpg", "jpeg", "webp"):
    candidate = ASSETS_DIR / f"pipeline_diagram.{ext}"
    if candidate.exists():
        diagram_path = candidate
        break

if diagram_path:
    st.image(str(diagram_path), use_container_width=True)
else:
    st.info(
        "No diagram yet — save one to `src/assets/pipeline_diagram.png` and it'll "
        "show up here automatically. See the README for a prompt you can paste "
        "into an image model to generate one."
    )

st.markdown("---")

st.header("The two things happening")
st.markdown(
    """
There's the indexing pass, which happens once per document: a PDF gets
read page by page, cut into small overlapping chunks, and each chunk gets
turned into a vector and stored. And there's the query pass, which happens
every time someone asks a question: the question gets turned into a vector
too, the closest-matching chunks get pulled back out, and those chunks
plus the question get handed to a language model to turn into an answer.
"""
)

st.header("A few choices worth explaining")

st.subheader("Why chunk by page instead of embedding the whole document")
st.markdown(
    """
Smaller chunks retrieve better. If someone asks about one specific number,
you want the paragraph with that number, not a whole page of surrounding
noise diluting the match. Keeping a bit of overlap between chunks just
stops a sentence from getting cut in half at the boundary.
"""
)

st.subheader("Why a small local model instead of a hosted embedding API")
st.markdown(
    """
Embedding happens constantly — every chunk gets embedded once when it's
indexed, and every question gets embedded again when it's asked. Doing
that locally means no API costs and no dependency on an outside service
for the part of the pipeline that runs the most. The model is small enough
to run fast on a normal CPU.
"""
)

st.subheader("Why retrieve first, then generate")
st.markdown(
    """
A language model on its own doesn't actually know what's in a specific
company's filing — it can only guess at something plausible. Handing it
the real, retrieved text first and telling it to answer only from that
turns "plausible guess" into "summarize what's actually there," which is a
much easier and more reliable job. More on this on the About page.
"""
)

st.subheader("Why the citations aren't a separate step")
st.markdown(
    """
Every chunk keeps its company, year, and page number attached from the
moment it's extracted, all the way through to the final answer. So a
citation isn't something the model looks up afterward — it's just the tag
that was already sitting on the text it was given, passed along.
"""
)
