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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.block-container { padding: 2rem 3rem; max-width: 1300px; }
#MainMenu, footer { visibility: hidden; }

/* Header */
.app-header {
    background: linear-gradient(120deg, #1e3a5f 0%, #2563eb 100%);
    border-radius: 14px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.app-header h1 { color: #fff; font-size: 1.8rem; font-weight: 700; margin: 0; letter-spacing: -0.3px; }
.app-header p  { color: rgba(255,255,255,0.75); font-size: 0.9rem; margin: 0.3rem 0 0; }
.app-badge {
    background: rgba(255,255,255,0.15);
    color: #fff;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.3);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    white-space: nowrap;
}

/* Metric cards */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 2rem; }
.kpi-card {
    flex: 1;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.kpi-label { font-size: 0.7rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; }
.kpi-value { font-size: 1.75rem; font-weight: 700; color: #0f172a; line-height: 1.1; margin: 0.2rem 0; }
.kpi-sub   { font-size: 0.75rem; color: #2563eb; font-weight: 500; }

/* Result cards */
.result-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #2563eb;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.result-title { font-size: 0.98rem; font-weight: 600; color: #0f172a; margin-bottom: 0.5rem; }
.result-meta  { font-size: 0.8rem; color: #64748b; margin-bottom: 0.8rem; }
.result-hit {
    background: #f8fafc;
    border-left: 3px solid #93c5fd;
    border-radius: 6px;
    padding: 0.7rem 1rem;
    margin-top: 0.6rem;
    font-size: 0.83rem;
    color: #334155;
    line-height: 1.6;
}
.result-hit-label { font-size: 0.72rem; font-weight: 600; color: #2563eb; margin-bottom: 0.3rem; }

/* Answer box */
.answer-card {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #16a34a;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-top: 1.2rem;
    font-size: 0.93rem;
    color: #14532d;
    line-height: 1.75;
}
.answer-label { font-size: 0.7rem; font-weight: 700; color: #16a34a; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.6rem; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #f8fafc; border-right: 1px solid #e2e8f0; }
section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
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
with st.sidebar:
    st.markdown("### 📊 PIMCO ABS Surveillance")
    st.markdown("---")
    st.markdown("**Filters**")
    selected_company = st.selectbox("Company",     ["All"] + companies)
    selected_asset   = st.selectbox("Asset Type",  ["All"] + asset_types)
    selected_year    = st.selectbox("Filing Year", ["All"] + [str(y) for y in years])

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div>
    <h1>ABS Prospectus Intelligence</h1>
    <p>SEC 424H filing search, metadata analysis &amp; AI-powered Q&amp;A across 116 filings from 15 issuers</p>
  </div>
  <span class="app-badge">Milestone 2 &nbsp;·&nbsp; Live</span>
</div>
""", unsafe_allow_html=True)

# ── KPI cards ─────────────────────────────────────────────────────────────────
try:
    total_principal = "${:.1f}B".format(
        index["aggregate_principal_amount"].dropna()
        .str.replace(r"[$,]", "", regex=True).astype(float).sum() / 1e9
    )
except Exception:
    total_principal = "N/A"

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Total Filings</div>
    <div class="kpi-value">{len(index)}</div>
    <div class="kpi-sub">SEC 424H documents</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Issuers</div>
    <div class="kpi-value">{len(companies)}</div>
    <div class="kpi-sub">Unique companies</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Asset Types</div>
    <div class="kpi-value">{len(asset_types)}</div>
    <div class="kpi-sub">Auto, CMBS &amp; more</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Total Principal</div>
    <div class="kpi-value">{total_principal}</div>
    <div class="kpi-sub">Aggregate across corpus</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_search, tab_qa, tab_browse = st.tabs([
    "🔍  Keyword Search",
    "🤖  Semantic Q&A",
    "📋  Browse Index",
])

# ── TAB 1: Keyword Search ─────────────────────────────────────────────────────
with tab_search:
    col_q, col_opt = st.columns([5, 1])
    with col_q:
        query = st.text_input(
            "query",
            placeholder="e.g.  reserve account   |   physical\\s+custody   |   weighted average",
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
                        max_results=20,
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
                    hits_html = ""
                    for i, hit in enumerate(r["hits"], 1):
                        snippet = hit["snippet"].replace("<<", "<b>").replace(">>", "</b>")
                        hits_html += f"""
                        <div class="result-hit">
                          <div class="result-hit-label">Hit {i} &nbsp;·&nbsp; {hit['citation']}</div>
                          {snippet}
                        </div>"""
                    st.markdown(f"""
                    <div class="result-card">
                      <div class="result-title">{deal}</div>
                      <div class="result-meta">
                        🏢 {r['company']} &nbsp;·&nbsp; 🗂 {r['asset_type']} &nbsp;·&nbsp;
                        📅 {r['filing_date']} &nbsp;·&nbsp; ⚡ {r['match_count']} match(es)
                      </div>
                      {hits_html}
                    </div>""", unsafe_allow_html=True)

# ── TAB 2: Semantic Q&A ───────────────────────────────────────────────────────
with tab_qa:
    nl_query = st.text_area(
        "question",
        placeholder="e.g. Which deals use physical custody of receivables?",
        height=120,
        label_visibility="collapsed",
    )
    run_qa = st.button("Generate Answer", type="primary", key="btn_qa")

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
                            top_k=5,
                            model="gpt-6-luna",
                            client=OpenAI(api_key=api_key),
                        )
                        st.markdown(f"""
                        <div class="answer-card">
                          <div class="answer-label">Answer</div>
                          {answer}
                        </div>""", unsafe_allow_html=True)
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
    col_a.metric("Showing",     len(filtered),                    f"of {len(index)} filings")
    col_b.metric("Companies",   filtered["company"].nunique(),    "in current view")
    col_c.metric("Asset Types", filtered["asset_type"].nunique(), "in current view")
    with col_d:
        st.markdown("<div style='margin-top:1.7rem'></div>", unsafe_allow_html=True)
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
            "company":                    st.column_config.TextColumn("Company",            width="medium"),
            "deal_name":                  st.column_config.TextColumn("Deal Name",          width="large"),
            "asset_type":                 st.column_config.TextColumn("Asset Type",         width="medium"),
            "filing_date":                st.column_config.TextColumn("Filed",              width="small"),
            "aggregate_principal_amount": st.column_config.TextColumn("Principal",          width="medium"),
            "wa_apr":                     st.column_config.TextColumn("WA APR",             width="small"),
            "wa_fico":                    st.column_config.TextColumn("WA FICO",            width="small"),
            "credit_enhancement_types":   st.column_config.TextColumn("Credit Enhancement", width="large"),
        },
    )
