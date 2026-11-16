"""Streamlit UI — PIMCO ABS Prospectus Surveillance."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import streamlit as st
import pandas as pd

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "notebooks"))

from search_filings import load_index, search_filings, DEFAULT_CLEAN_DIR, DEFAULT_INDEX

st.set_page_config(
    page_title="PIMCO | ABS Surveillance",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data ─────────────────────────────────────────────────────────────────────
@st.cache_data
def get_index() -> pd.DataFrame:
    return load_index(DEFAULT_INDEX)

index       = get_index()
companies   = sorted(index["company"].dropna().unique())
asset_types = sorted(index["asset_type"].dropna().unique())
years = sorted(
    {int(d[:4]) for d in index["filing_date"].dropna() if len(d) >= 4},
    reverse=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("📊 PIMCO ABS Surveillance")
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
selected_company = st.sidebar.selectbox("Company",     ["All"] + companies)
selected_asset   = st.sidebar.selectbox("Asset Type",  ["All"] + asset_types)
selected_year    = st.sidebar.selectbox("Filing Year", ["All"] + [str(y) for y in years])
st.sidebar.markdown("---")
st.sidebar.subheader("Search Options")
max_results = st.sidebar.slider("Max results", 1, 50, 10)
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
**Corpus**
- 📁 {len(index)} filings
- 🏢 {len(companies)} issuers
- 🗂 {len(asset_types)} asset types
- 📅 {min(years)}–{max(years)}
""")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("ABS Prospectus Intelligence")
st.caption("SEC 424H filing search, metadata analysis & AI-powered Q&A across 116 filings from 15 issuers.")
st.markdown("---")

# ── KPI metrics ───────────────────────────────────────────────────────────────
try:
    total_principal = "${:.1f}B".format(
        index["aggregate_principal_amount"].dropna()
        .str.replace(r"[$,]", "", regex=True).astype(float).sum() / 1e9
    )
except Exception:
    total_principal = "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Filings",   len(index),        "SEC 424H documents")
col2.metric("Issuers",         len(companies),    "Unique companies")
col3.metric("Asset Types",     len(asset_types),  "Auto, CMBS & more")
col4.metric("Total Principal", total_principal,   "Aggregate corpus")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_search, tab_qa, tab_browse = st.tabs([
    "🔍 Keyword Search",
    "🤖 Semantic Q&A",
    "📋 Browse Index",
])

# ── TAB 1: Keyword Search ─────────────────────────────────────────────────────
with tab_search:
    col_q, col_opt = st.columns([5, 1])
    with col_q:
        query = st.text_input(
            "Search query",
            placeholder='e.g. reserve account  |  physical\\s+custody  |  weighted average',
            label_visibility="collapsed",
        )
    with col_opt:
        use_regex = st.checkbox("Regex mode")

    col_btn, col_hint = st.columns([1, 5])
    with col_btn:
        run_search = st.button("Search Filings", type="primary", use_container_width=True)
    with col_hint:
        st.caption("Sidebar filters apply automatically. Leave query blank to filter by metadata only.")

    if run_search:
        if not query and selected_company == "All" and selected_asset == "All" and selected_year == "All":
            st.warning("Enter a search query or select at least one sidebar filter.")
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

            if not results:
                st.info("No filings matched your query. Try broadening your search or adjusting the filters.")
            else:
                st.success(f"**{len(results)} filing(s) matched**")
                for r in results:
                    deal = r["deal_name"] or r["company"]
                    with st.expander(f"**{deal}** — {r['filing_date']} | {r['asset_type']} | {r['match_count']} match(es)"):
                        st.markdown(f"**Company:** {r['company']}  \n**Asset type:** {r['asset_type']}  \n**Filed:** {r['filing_date']}  \n**Source:** `{r['source_path']}`")
                        for i, hit in enumerate(r["hits"], 1):
                            st.markdown(f"**Hit {i}** — {hit['citation']}")
                            snippet = hit["snippet"].replace("<<", "**").replace(">>", "**")
                            st.markdown(f"> {snippet}")
                            if i < len(r["hits"]):
                                st.markdown("---")

# ── TAB 2: Semantic Q&A ───────────────────────────────────────────────────────
with tab_qa:
    nl_query = st.text_area(
        "Ask a question about the filings",
        placeholder="e.g. Which deals use physical custody of receivables?",
        height=110,
        label_visibility="collapsed",
    )

    col_btn, col_topk = st.columns([1, 2])
    with col_btn:
        run_qa = st.button("Generate Answer", type="primary", key="btn_qa", use_container_width=True)
    with col_topk:
        top_k = st.slider("Sources to retrieve", 1, 20, 5)

    if run_qa:
        if not nl_query.strip():
            st.warning("Enter a question.")
        else:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                st.error("No API key found. Add OPENAI_API_KEY to your .env file.")
            elif not (ROOT / "data" / "embeddings" / "vectors.npy").exists():
                st.error("Embedding index not found. Run `python notebooks/embed_chunks.py --model text-embedding-3-small` first.")
            else:
                with st.spinner("Searching filings and generating answer…"):
                    try:
                        from openai import OpenAI
                        from answer_questions import answer_question
                        answer = answer_question(
                            nl_query,
                            top_k=top_k,
                            model="gpt-6-luna",
                            client=OpenAI(api_key=api_key),
                        )
                        st.markdown("### Answer")
                        st.markdown(answer)
                    except Exception as exc:
                        st.error(f"Error: {exc}")

# ── TAB 3: Browse Index ───────────────────────────────────────────────────────
with tab_browse:
    filtered = index.copy()
    if selected_company != "All":
        filtered = filtered[filtered["company"] == selected_company]
    if selected_asset != "All":
        filtered = filtered[filtered["asset_type"] == selected_asset]
    if selected_year != "All":
        filtered = filtered[filtered["filing_date"].str.startswith(selected_year)]

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Showing",      len(filtered),                f"of {len(index)} filings")
    col_b.metric("Companies",    filtered["company"].nunique(), "in current view")
    col_c.metric("Asset Types",  filtered["asset_type"].nunique(), "in current view")
    with col_d:
        st.markdown("<div style='margin-top:1.6rem'></div>", unsafe_allow_html=True)
        csv = filtered.to_csv(index=False).encode()
        st.download_button("⬇ Export CSV", csv, "filings_filtered.csv", "text/csv", use_container_width=True)

    display_cols = [
        "company", "deal_name", "asset_type", "filing_date",
        "aggregate_principal_amount", "wa_apr", "wa_fico", "credit_enhancement_types",
    ]
    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=520,
        column_config={
            "company":                    st.column_config.TextColumn("Company",             width="medium"),
            "deal_name":                  st.column_config.TextColumn("Deal Name",           width="large"),
            "asset_type":                 st.column_config.TextColumn("Asset Type",          width="medium"),
            "filing_date":                st.column_config.TextColumn("Filed",               width="small"),
            "aggregate_principal_amount": st.column_config.TextColumn("Principal",           width="medium"),
            "wa_apr":                     st.column_config.TextColumn("WA APR",              width="small"),
            "wa_fico":                    st.column_config.TextColumn("WA FICO",             width="small"),
            "credit_enhancement_types":   st.column_config.TextColumn("Credit Enhancement",  width="large"),
        },
    )
