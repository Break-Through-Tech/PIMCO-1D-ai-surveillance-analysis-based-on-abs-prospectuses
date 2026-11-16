"""Streamlit UI for ABS Prospectus Surveillance Analysis."""

import os
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "notebooks"))

from search_filings import load_index, search_filings, DEFAULT_CLEAN_DIR, DEFAULT_INDEX

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ABS Prospectus Search",
    page_icon="📄",
    layout="wide",
)

st.title("📄 ABS Prospectus Surveillance")
st.caption("Search 116 SEC 424H filings from 15 issuers — keyword, regex, and semantic Q&A.")

# ---------------------------------------------------------------------------
# Load index once
# ---------------------------------------------------------------------------
@st.cache_data
def get_index() -> pd.DataFrame:
    return load_index(DEFAULT_INDEX)

index = get_index()

companies = sorted(index["company"].dropna().unique())
asset_types = sorted(index["asset_type"].dropna().unique())
years = sorted(
    {int(d[:4]) for d in index["filing_date"].dropna() if len(d) >= 4},
    reverse=True,
)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

selected_company = st.sidebar.selectbox("Company", ["All"] + companies)
selected_asset = st.sidebar.selectbox("Asset Type", ["All"] + asset_types)
selected_year = st.sidebar.selectbox("Filing Year", ["All"] + [str(y) for y in years])
max_results = st.sidebar.slider("Max results", 1, 50, 10)

# ---------------------------------------------------------------------------
# Tabs: Keyword Search | Semantic Q&A | Browse Index
# ---------------------------------------------------------------------------
tab_search, tab_qa, tab_browse = st.tabs(["🔍 Keyword Search", "🤖 Semantic Q&A", "📋 Browse Index"])

# ── Keyword Search ──────────────────────────────────────────────────────────
with tab_search:
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("Search query", placeholder='e.g. "reserve account" or physical\\s+custody')
    with col2:
        use_regex = st.checkbox("Regex", value=False)

    run_search = st.button("Search", type="primary", key="btn_search")

    if run_search:
        if not query and selected_company == "All" and selected_asset == "All" and selected_year == "All":
            st.warning("Enter a query or select at least one filter.")
        else:
            with st.spinner("Searching filings…"):
                try:
                    results = search_filings(
                        query or None,
                        index=index,
                        clean_dir=DEFAULT_CLEAN_DIR,
                        use_regex=use_regex,
                        company=None if selected_company == "All" else selected_company,
                        asset_type=None if selected_asset == "All" else selected_asset,
                        year=None if selected_year == "All" else int(selected_year),
                        max_results=max_results,
                    )
                except Exception as exc:
                    st.error(f"Search error: {exc}")
                    results = []

            st.write(f"**{len(results)} filing(s) matched**")

            for result in results:
                with st.expander(
                    f"**{result['deal_name'] or result['company']}** — "
                    f"{result['filing_date']} | {result['asset_type']} | "
                    f"{result['match_count']} match(es)"
                ):
                    st.write(f"**Company:** {result['company']}")
                    st.write(f"**Asset type:** {result['asset_type']}")
                    st.write(f"**Filed:** {result['filing_date']}")
                    st.write(f"**Source:** `{result['source_path']}`")

                    for i, hit in enumerate(result["hits"], 1):
                        st.markdown(f"**Hit {i}** — {hit['citation']}")
                        snippet_html = hit["snippet"].replace(
                            "<<", "<mark>"
                        ).replace(">>", "</mark>")
                        st.markdown(snippet_html, unsafe_allow_html=True)
                        st.divider()

# ── Semantic Q&A ────────────────────────────────────────────────────────────
with tab_qa:
    st.info(
        "Semantic Q&A requires an OpenAI API key and a pre-built embedding index "
        "(`data/embeddings/`). Run `python notebooks/embed_chunks.py` first."
    )

    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-…")
    nl_query = st.text_area("Question", placeholder="Which deals use physical custody?", height=80)
    top_k = st.slider("Chunks to retrieve (top-k)", 1, 20, 5)
    model = st.text_input("Model", value="gpt-4o")

    run_qa = st.button("Ask", type="primary", key="btn_qa")

    if run_qa:
        if not nl_query.strip():
            st.warning("Enter a question.")
        elif not api_key.strip():
            st.warning("Enter your OpenAI API key.")
        else:
            embeddings_dir = ROOT / "data" / "embeddings"
            if not (embeddings_dir / "vectors.npy").exists():
                st.error(
                    "Embedding index not found. "
                    "Run `python notebooks/chunk_filings.py` then `python notebooks/embed_chunks.py`."
                )
            else:
                os.environ["OPENAI_API_KEY"] = api_key
                with st.spinner("Retrieving chunks and generating answer…"):
                    try:
                        from openai import OpenAI
                        from answer_questions import answer_question

                        answer = answer_question(
                            nl_query,
                            top_k=top_k,
                            model=model,
                            client=OpenAI(api_key=api_key),
                        )
                        st.markdown("### Answer")
                        st.write(answer)
                    except Exception as exc:
                        st.error(f"Error: {exc}")

# ── Browse Index ─────────────────────────────────────────────────────────────
with tab_browse:
    filtered = index.copy()
    if selected_company != "All":
        filtered = filtered[filtered["company"] == selected_company]
    if selected_asset != "All":
        filtered = filtered[filtered["asset_type"] == selected_asset]
    if selected_year != "All":
        filtered = filtered[filtered["filing_date"].str.startswith(selected_year)]

    st.write(f"**{len(filtered)} filing(s)**")

    display_cols = ["company", "deal_name", "asset_type", "filing_date",
                    "aggregate_principal_amount", "wa_apr", "wa_fico", "credit_enhancement_types"]
    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=500,
    )

    csv = filtered.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "filings_filtered.csv", "text/csv")
