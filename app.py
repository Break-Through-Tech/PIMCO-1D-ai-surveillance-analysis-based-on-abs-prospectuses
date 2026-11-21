"""Streamlit app: the connection layer to the Q/A backend in src/qa/.

Run from the repository root:
    streamlit run app.py

This file only shows how the frontend calls the backend. The layout, the
sources display and styling are still to be built (see TODO (frontend)).
"""

import os

import streamlit as st

from src.qa import QAError, filter_options, stream_answer


# The backend reads OPENAI_API_KEY from the environment. Set it in the terminal
# or in .streamlit/secrets.toml (never committed).
# TODO: decide whether to also load the key from .env.
def _key_from_secrets() -> str | None:
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except FileNotFoundError:  # no secrets file
        return None


if not os.getenv("OPENAI_API_KEY") and (key := _key_from_secrets()):
    os.environ["OPENAI_API_KEY"] = key


@st.cache_data
def load_filter_options() -> dict:
    """Company, asset type and year values in the index, for the filters."""
    return filter_options()


def ask(question: str, filters: dict) -> dict:
    """{"sources": [...], "answer": text pieces}. Raises QAError.

    [Source N] in the answer is sources[N - 1].
    """
    return stream_answer(question, filters=filters)


# --- Bare-bones UI, just enough to prove the connection works ---------------
# TODO (frontend): replace everything below with the real layout.
st.title("ABS Prospectus Q&A")

try:
    options = load_filter_options()
except QAError as error:
    st.error(str(error))
    st.stop()

filters = {
    "company": st.sidebar.multiselect("Company", options["company"]),
    "asset_type": st.sidebar.multiselect("Asset type", options["asset_type"]),
    "year": st.sidebar.multiselect("Year", options["year"]),
}

question = st.text_input("Ask a question about the filings")
if question:
    try:
        result = ask(question, filters)
        st.write_stream(result["answer"])
        # TODO (frontend): a proper sources display (expandable text, links).
        for source in result["sources"]:
            st.caption(
                f"[Source {source['number']}] {source['deal_name'] or source['company']} · "
                f"page {source['page_label'] or source['page']} · {source['section'] or 'n/a'}"
            )
    except QAError as error:
        st.error(str(error))
