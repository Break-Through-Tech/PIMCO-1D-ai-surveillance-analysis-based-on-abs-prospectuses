"""Streamlit UI — PIMCO ABS Prospectus Surveillance."""

import os
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "notebooks"))

from search_filings import load_index, search_filings, DEFAULT_CLEAN_DIR, DEFAULT_INDEX

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PIMCO | ABS Surveillance",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0d1117;}
section[data-testid="stSidebar"]{background:#0d1117;border-right:1px solid #21262d;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:2rem 2.5rem;max-width:1400px;}

.header-banner{background:linear-gradient(135deg,#0f2027 0%,#1a3a4a 50%,#0f2027 100%);border:1px solid #1e4d6b;border-radius:16px;padding:2rem 2.5rem;margin-bottom:2rem;display:flex;align-items:center;justify-content:space-between;}
.header-title{font-size:1.9rem;font-weight:700;color:#e6edf3;letter-spacing:-0.5px;margin:0;}
.header-subtitle{font-size:0.9rem;color:#8b949e;margin:0.3rem 0 0 0;}
.header-badge{background:#1e4d6b;color:#58a6ff;font-size:0.75rem;font-weight:600;padding:0.3rem 0.8rem;border-radius:20px;border:1px solid #2d6a8f;letter-spacing:0.5px;text-transform:uppercase;}

.metric-row{display:flex;gap:1rem;margin-bottom:2rem;}
.metric-card{flex:1;background:#161b22;border:1px solid #21262d;border-radius:12px;padding:1.2rem 1.5rem;transition:border-color 0.2s;}
.metric-card:hover{border-color:#388bfd;}
.metric-label{font-size:0.72rem;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.4rem;}
.metric-value{font-size:1.8rem;font-weight:700;color:#e6edf3;line-height:1;}
.metric-sub{font-size:0.78rem;color:#58a6ff;margin-top:0.3rem;}

.stTabs [data-baseweb="tab-list"]{background:#161b22;border-radius:10px;padding:4px;gap:2px;border:1px solid #21262d;}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:8px;color:#8b949e;font-weight:500;font-size:0.88rem;padding:0.5rem 1.2rem;border:none;}
.stTabs [aria-selected="true"]{background:#21262d !important;color:#e6edf3 !important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.5rem;}

.stTextInput>div>div>input,.stTextArea textarea{background:#161b22 !important;border:1px solid #30363d !important;border-radius:10px !important;color:#e6edf3 !important;font-size:0.95rem !important;padding:0.65rem 1rem !important;}
.stTextInput>div>div>input:focus,.stTextArea textarea:focus{border-color:#388bfd !important;box-shadow:0 0 0 3px rgba(56,139,253,0.15) !important;}

.stButton>button{background:linear-gradient(135deg,#1f6feb,#388bfd) !important;color:#fff !important;border:none !important;border-radius:10px !important;font-weight:600 !important;font-size:0.9rem !important;padding:0.6rem 2rem !important;transition:opacity 0.2s,transform 0.1s !important;letter-spacing:0.3px;}
.stButton>button:hover{opacity:0.88 !important;transform:translateY(-1px) !important;}
.stButton>button:active{transform:translateY(0) !important;}

.stDownloadButton>button{background:#21262d !important;color:#58a6ff !important;border:1px solid #30363d !important;border-radius:10px !important;font-weight:500 !important;}
.stDownloadButton>button:hover{border-color:#58a6ff !important;}

.stSelectbox>div>div{background:#161b22 !important;border:1px solid #30363d !important;border-radius:10px !important;color:#e6edf3 !important;}
.stSlider>div>div>div{background:#388bfd !important;}
.stCheckbox label{color:#8b949e !important;font-size:0.88rem !important;}
.stSpinner>div{border-top-color:#388bfd !important;}
.stAlert{border-radius:10px !important;}
.stDataFrame{border-radius:12px;overflow:hidden;border:1px solid #21262d;}

.result-card{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:1.4rem 1.6rem;margin-bottom:1rem;transition:border-color 0.2s,box-shadow 0.2s;}
.result-card:hover{border-color:#388bfd;box-shadow:0 4px 24px rgba(56,139,253,0.08);}
.result-deal{font-size:1rem;font-weight:600;color:#e6edf3;margin-bottom:0.4rem;}
.result-meta{display:flex;gap:0.6rem;flex-wrap:wrap;margin-bottom:0.9rem;}
.tag{font-size:0.72rem;font-weight:600;padding:0.2rem 0.65rem;border-radius:20px;letter-spacing:0.4px;text-transform:uppercase;}
.tag-blue{background:#1e3a5f;color:#58a6ff;border:1px solid #2d5a8e;}
.tag-green{background:#1a3a2a;color:#3fb950;border:1px solid #2d6a3f;}
.tag-amber{background:#3a2a0a;color:#d29922;border:1px solid #6a4a0f;}
.tag-gray{background:#21262d;color:#8b949e;border:1px solid #30363d;}

.hit-block{background:#0d1117;border:1px solid #21262d;border-left:3px solid #388bfd;border-radius:8px;padding:0.9rem 1.1rem;margin-top:0.7rem;font-size:0.85rem;color:#8b949e;line-height:1.6;}
.hit-citation{font-size:0.75rem;color:#58a6ff;margin-bottom:0.4rem;font-weight:500;}
.hit-block mark{background:rgba(210,153,34,0.25);color:#d29922;border-radius:3px;padding:0 2px;font-weight:600;}

.answer-box{background:#161b22;border:1px solid #21262d;border-left:4px solid #3fb950;border-radius:12px;padding:1.5rem 1.8rem;color:#c9d1d9;font-size:0.95rem;line-height:1.75;margin-top:1rem;}

.sidebar-section{font-size:0.7rem;font-weight:700;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin:1.2rem 0 0.5rem 0;}
.sidebar-logo{font-size:1.1rem;font-weight:700;color:#e6edf3;padding:0.8rem 0 1.2rem 0;border-bottom:1px solid #21262d;margin-bottom:0.5rem;}

.empty-state{text-align:center;padding:3rem 1rem;color:#8b949e;}
.empty-state-icon{font-size:2.5rem;margin-bottom:0.8rem;}
.empty-state-text{font-size:1rem;font-weight:500;color:#c9d1d9;}
.empty-state-sub{font-size:0.85rem;margin-top:0.3rem;}

.results-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem;}
.results-count{font-size:0.85rem;color:#8b949e;}
.results-count b{color:#e6edf3;}

.qa-setup-card{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:1.4rem 1.6rem;margin-bottom:1.2rem;}
.qa-setup-title{font-size:0.8rem;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:1rem;}
</style>
""", unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────────────────
@st.cache_data
def get_index() -> pd.DataFrame:
    return load_index(DEFAULT_INDEX)

index      = get_index()
companies  = sorted(index["company"].dropna().unique())
asset_types = sorted(index["asset_type"].dropna().unique())
years = sorted(
    {int(d[:4]) for d in index["filing_date"].dropna() if len(d) >= 4},
    reverse=True,
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">📊 PIMCO ABS Surveillance</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Filters</div>', unsafe_allow_html=True)
    selected_company = st.selectbox("Company",     ["All"] + companies)
    selected_asset   = st.selectbox("Asset Type",  ["All"] + asset_types)
    selected_year    = st.selectbox("Filing Year", ["All"] + [str(y) for y in years])
    st.markdown('<div class="sidebar-section">Search Options</div>', unsafe_allow_html=True)
    max_results = st.slider("Max results", 1, 50, 10)
    st.markdown('<div class="sidebar-section">Corpus Stats</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:0.82rem;color:#8b949e;line-height:2;">
        📁 <b style="color:#c9d1d9;">{len(index)}</b> filings indexed<br>
        🏢 <b style="color:#c9d1d9;">{len(companies)}</b> issuers<br>
        🗂 <b style="color:#c9d1d9;">{len(asset_types)}</b> asset types<br>
        📅 <b style="color:#c9d1d9;">{min(years)}–{max(years)}</b> date range
    </div>
    """, unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
  <div>
    <p class="header-title">ABS Prospectus Intelligence</p>
    <p class="header-subtitle">SEC 424H filing search, metadata analysis &amp; AI-powered Q&amp;A across 116 filings from 15 issuers</p>
  </div>
  <span class="header-badge">Milestone 2 · Live</span>
</div>
""", unsafe_allow_html=True)

# ── KPI cards ────────────────────────────────────────────────────────────────
try:
    total_principal = "${:.1f}B".format(
        index["aggregate_principal_amount"].dropna()
        .str.replace(r"[$,]", "", regex=True).astype(float).sum() / 1e9
    )
except Exception:
    total_principal = "N/A"

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">Total Filings</div>
    <div class="metric-value">{len(index)}</div>
    <div class="metric-sub">SEC 424H documents</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Issuers</div>
    <div class="metric-value">{len(companies)}</div>
    <div class="metric-sub">Unique companies</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Asset Types</div>
    <div class="metric-value">{len(asset_types)}</div>
    <div class="metric-sub">Auto, CMBS, device &amp; more</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Total Principal</div>
    <div class="metric-value">{total_principal}</div>
    <div class="metric-sub">Aggregate across corpus</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_search, tab_qa, tab_browse = st.tabs([
    "🔍  Keyword Search",
    "🤖  Semantic Q&A",
    "📋  Browse Index",
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Keyword Search
# ════════════════════════════════════════════════════════════════════════════
with tab_search:
    col_q, col_opt = st.columns([5, 1])
    with col_q:
        query = st.text_input(
            "Search query",
            placeholder='e.g.  reserve account   |   physical\\s+custody   |   weighted average',
            label_visibility="collapsed",
        )
    with col_opt:
        use_regex = st.checkbox("Regex mode", value=False)

    col_btn, col_hint = st.columns([1, 5])
    with col_btn:
        run_search = st.button("Search Filings", type="primary", use_container_width=True)
    with col_hint:
        st.markdown(
            '<p style="color:#8b949e;font-size:0.82rem;padding-top:0.6rem;">'
            'Sidebar filters apply automatically. Leave query blank to filter by metadata only.</p>',
            unsafe_allow_html=True,
        )

    if run_search:
        no_filter = (
            not query
            and selected_company == "All"
            and selected_asset == "All"
            and selected_year == "All"
        )
        if no_filter:
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
                st.markdown("""
                <div class="empty-state">
                  <div class="empty-state-icon">🔎</div>
                  <div class="empty-state-text">No filings matched your query</div>
                  <div class="empty-state-sub">Try broadening your search or adjusting the sidebar filters</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="results-header">
                  <span class="results-count"><b>{len(results)}</b> filing(s) matched</span>
                </div>""", unsafe_allow_html=True)

                asset_tag_class = {
                    "auto_loans": "tag-blue", "auto_leases": "tag-green",
                    "cmbs": "tag-amber", "motorcycle_loans": "tag-gray",
                }

                for r in results:
                    deal   = r["deal_name"] or r["company"]
                    atype  = r["asset_type"]
                    tclass = asset_tag_class.get(atype, "tag-gray")
                    hits_html = ""
                    for i, hit in enumerate(r["hits"], 1):
                        snippet = (
                            hit["snippet"]
                            .replace("<<", "<mark>")
                            .replace(">>", "</mark>")
                        )
                        hits_html += f"""
                        <div class="hit-block">
                          <div class="hit-citation">Hit {i} &nbsp;·&nbsp; {hit['citation']}</div>
                          {snippet}
                        </div>"""

                    st.markdown(f"""
                    <div class="result-card">
                      <div class="result-deal">{deal}</div>
                      <div class="result-meta">
                        <span class="tag tag-gray">{r['company']}</span>
                        <span class="tag {tclass}">{atype}</span>
                        <span class="tag tag-gray">📅 {r['filing_date']}</span>
                        <span class="tag tag-amber">⚡ {r['match_count']} match(es)</span>
                      </div>
                      {hits_html}
                    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Semantic Q&A
# ════════════════════════════════════════════════════════════════════════════
with tab_qa:
    st.markdown("""
    <div style="background:#161b22;border:1px solid #21262d;border-left:4px solid #58a6ff;
                border-radius:10px;padding:1rem 1.3rem;margin-bottom:1.5rem;
                font-size:0.88rem;color:#8b949e;line-height:1.7;">
      <b style="color:#58a6ff;">ℹ️ Setup required</b><br>
      Semantic Q&amp;A needs a pre-built embedding index and an OpenAI API key.<br>
      Run <code style="background:#0d1117;padding:1px 5px;border-radius:4px;color:#c9d1d9;">
      python notebooks/chunk_filings.py</code> then
      <code style="background:#0d1117;padding:1px 5px;border-radius:4px;color:#c9d1d9;">
      python notebooks/embed_chunks.py</code> first.
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="qa-setup-card"><div class="qa-setup-title">Your Question</div>', unsafe_allow_html=True)
        nl_query = st.text_area(
            "Question",
            placeholder="e.g. Which deals use physical custody of receivables?",
            height=110,
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="qa-setup-card"><div class="qa-setup-title">Configuration</div>', unsafe_allow_html=True)
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-…")
        model   = st.text_input("Model", value="gpt-4o")
        top_k   = st.slider("Chunks to retrieve (top-k)", 1, 20, 5)
        st.markdown('</div>', unsafe_allow_html=True)

    run_qa = st.button("Generate Answer", type="primary", key="btn_qa")

    if run_qa:
        if not nl_query.strip():
            st.warning("Enter a question.")
        elif not api_key.strip():
            st.warning("Enter your OpenAI API key.")
        else:
            embeddings_dir = ROOT / "data" / "embeddings"
            if not (embeddings_dir / "vectors.npy").exists():
                st.error(
                    "Embedding index not found at `data/embeddings/vectors.npy`. "
                    "Run `python notebooks/chunk_filings.py` then `python notebooks/embed_chunks.py`."
                )
            else:
                os.environ["OPENAI_API_KEY"] = api_key
                with st.spinner("Retrieving evidence chunks and generating answer…"):
                    try:
                        from openai import OpenAI
                        from answer_questions import answer_question
                        answer = answer_question(
                            nl_query,
                            top_k=top_k,
                            model=model,
                            client=OpenAI(api_key=api_key),
                        )
                        st.markdown(
                            f'<div class="answer-box"><b style="color:#3fb950;font-size:0.8rem;'
                            f'text-transform:uppercase;letter-spacing:0.8px;">Answer</b>'
                            f'<br><br>{answer}</div>',
                            unsafe_allow_html=True,
                        )
                    except Exception as exc:
                        st.error(f"Error: {exc}")

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Browse Index
# ════════════════════════════════════════════════════════════════════════════
with tab_browse:
    filtered = index.copy()
    if selected_company != "All":
        filtered = filtered[filtered["company"] == selected_company]
    if selected_asset != "All":
        filtered = filtered[filtered["asset_type"] == selected_asset]
    if selected_year != "All":
        filtered = filtered[filtered["filing_date"].str.startswith(selected_year)]

    col_stat1, col_stat2, col_stat3, col_dl = st.columns([2, 2, 2, 1])
    with col_stat1:
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:1rem;">
          <div class="metric-label">Showing</div>
          <div class="metric-value" style="font-size:1.4rem;">{len(filtered)}</div>
          <div class="metric-sub">of {len(index)} filings</div>
        </div>""", unsafe_allow_html=True)
    with col_stat2:
        unique_co = filtered["company"].nunique()
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:1rem;">
          <div class="metric-label">Companies</div>
          <div class="metric-value" style="font-size:1.4rem;">{unique_co}</div>
          <div class="metric-sub">in current view</div>
        </div>""", unsafe_allow_html=True)
    with col_stat3:
        unique_at = filtered["asset_type"].nunique()
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:1rem;">
          <div class="metric-label">Asset Types</div>
          <div class="metric-value" style="font-size:1.4rem;">{unique_at}</div>
          <div class="metric-sub">in current view</div>
        </div>""", unsafe_allow_html=True)
    with col_dl:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        csv = filtered.to_csv(index=False).encode()
        st.download_button(
            "⬇ Export CSV",
            csv,
            "filings_filtered.csv",
            "text/csv",
            use_container_width=True,
        )

    display_cols = [
        "company", "deal_name", "asset_type", "filing_date",
        "aggregate_principal_amount", "wa_apr", "wa_fico",
        "credit_enhancement_types",
    ]
    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=520,
        column_config={
            "company":                    st.column_config.TextColumn("Company",        width="medium"),
            "deal_name":                  st.column_config.TextColumn("Deal Name",      width="large"),
            "asset_type":                 st.column_config.TextColumn("Asset Type",     width="medium"),
            "filing_date":                st.column_config.TextColumn("Filed",          width="small"),
            "aggregate_principal_amount": st.column_config.TextColumn("Principal",      width="medium"),
            "wa_apr":                     st.column_config.TextColumn("WA APR",         width="small"),
            "wa_fico":                    st.column_config.TextColumn("WA FICO",        width="small"),
            "credit_enhancement_types":   st.column_config.TextColumn("Credit Enhancement", width="large"),
        },
    )
