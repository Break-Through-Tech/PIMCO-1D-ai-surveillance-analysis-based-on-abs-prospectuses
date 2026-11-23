"""PIMCO ABS Prospectus Intelligence Platform."""
import os, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "notebooks"))
from search_filings import load_index, search_filings, DEFAULT_CLEAN_DIR, DEFAULT_INDEX

st.set_page_config(page_title="PIMCO | ABS Intelligence", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;}
html,body,[class*="css"]{font-family:'Inter',-apple-system,sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0!important;max-width:100%!important;}
.stApp{background:#eef1f6;}

/* Sidebar */
section[data-testid="stSidebar"]{background:#0b1929;border-right:1px solid #162840;}
section[data-testid="stSidebar"] .block-container{padding:0!important;}
section[data-testid="stSidebar"] label{color:#7a9ab8!important;font-size:0.7rem!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:0.8px!important;}
section[data-testid="stSidebar"] .stSelectbox>div>div{background:#0f2035!important;border:1px solid #1e3450!important;border-radius:6px!important;color:#c0d4e8!important;font-size:0.83rem!important;}

/* Topbar */
.topbar{display:flex;align-items:center;justify-content:space-between;padding:0.85rem 2rem;background:#0b1929;border-bottom:1px solid #162840;}
.tb-brand{display:flex;align-items:center;gap:0.7rem;}
.tb-logo{width:30px;height:30px;background:#1a56db;border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:0.9rem;font-weight:800;color:#fff;flex-shrink:0;}
.tb-title{font-size:0.92rem;font-weight:700;color:#e0ecf8;letter-spacing:0.1px;}
.tb-sub{font-size:0.65rem;color:#4a6a8a;margin-top:1px;}
.tb-stats{display:flex;align-items:center;gap:1.2rem;}
.tb-stat{text-align:right;}
.tb-stat-v{font-size:0.85rem;font-weight:600;color:#c0d4e8;}
.tb-stat-l{font-size:0.62rem;color:#4a6a8a;text-transform:uppercase;letter-spacing:0.5px;}
.tb-sep{width:1px;height:24px;background:#1e3450;}

/* Main */
.main{padding:1.4rem 2rem;max-width:1380px;margin:0 auto;}

/* KPI strip */
.kpi-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#d0d8e4;border:1px solid #d0d8e4;border-radius:10px;overflow:hidden;margin-bottom:1.4rem;box-shadow:0 1px 4px rgba(0,0,0,0.07);}
.kpi-cell{background:#fff;padding:1rem 1.3rem;transition:background 0.15s;}
.kpi-cell:hover{background:#f7f9fc;}
.kpi-v{font-size:1.55rem;font-weight:700;color:#0b1929;letter-spacing:-0.5px;line-height:1;}
.kpi-l{font-size:0.67rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.8px;margin-top:0.25rem;}
.kpi-d{font-size:0.7rem;color:#1a56db;font-weight:500;margin-top:0.15rem;}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{background:transparent!important;border-bottom:2px solid #d8e0ec!important;gap:0!important;padding:0!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;border:none!important;border-bottom:2px solid transparent!important;border-radius:0!important;color:#64748b!important;font-weight:500!important;font-size:0.83rem!important;padding:0.6rem 1.1rem!important;margin-bottom:-2px!important;}
.stTabs [data-baseweb="tab"]:hover{color:#0b1929!important;}
.stTabs [aria-selected="true"]{color:#1a56db!important;border-bottom:2px solid #1a56db!important;font-weight:600!important;}
.stTabs [data-baseweb="tab-highlight"]{display:none!important;}
.stTabs [data-baseweb="tab-border"]{display:none!important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.3rem!important;}

/* Inputs */
.stTextInput>div>div>input{background:#fff!important;border:1.5px solid #cdd5e0!important;border-radius:7px!important;color:#0b1929!important;font-size:0.88rem!important;padding:0.6rem 0.9rem!important;}
.stTextInput>div>div>input:focus{border-color:#1a56db!important;box-shadow:0 0 0 3px rgba(26,86,219,0.1)!important;}
.stTextArea textarea{background:#fff!important;border:1.5px solid #cdd5e0!important;border-radius:7px!important;color:#0b1929!important;font-size:0.88rem!important;line-height:1.6!important;}
.stTextArea textarea:focus{border-color:#1a56db!important;box-shadow:0 0 0 3px rgba(26,86,219,0.1)!important;}

/* Buttons */
.stButton>button{background:#1a56db!important;color:#fff!important;border:none!important;border-radius:7px!important;font-weight:600!important;font-size:0.83rem!important;padding:0.52rem 1.3rem!important;box-shadow:0 1px 3px rgba(26,86,219,0.3)!important;transition:background 0.15s,box-shadow 0.15s!important;}
.stButton>button:hover{background:#1648c0!important;box-shadow:0 3px 10px rgba(26,86,219,0.35)!important;}
.stDownloadButton>button{background:#fff!important;color:#1a56db!important;border:1.5px solid #1a56db!important;border-radius:7px!important;font-weight:600!important;font-size:0.8rem!important;}
.stDownloadButton>button:hover{background:#eff4ff!important;}

/* Result cards */
.rc{background:#fff;border:1px solid #dde4ef;border-left:3px solid #1a56db;border-radius:8px;padding:1rem 1.3rem;margin-bottom:0.7rem;transition:box-shadow 0.15s,border-color 0.15s;}
.rc:hover{box-shadow:0 2px 12px rgba(26,86,219,0.09);border-color:#1a56db;}
.rc-title{font-size:0.9rem;font-weight:600;color:#0b1929;margin-bottom:0.35rem;}
.rc-meta{font-size:0.73rem;color:#64748b;margin-bottom:0.6rem;display:flex;flex-wrap:wrap;gap:0.8rem;}
.rc-badge{font-size:0.62rem;font-weight:700;padding:0.18rem 0.5rem;border-radius:4px;text-transform:uppercase;letter-spacing:0.4px;}
.b-auto{background:#dbeafe;color:#1e40af;}
.b-sub{background:#fce7f3;color:#9d174d;}
.b-cmbs{background:#fef3c7;color:#92400e;}
.b-dev{background:#d1fae5;color:#065f46;}
.b-cc{background:#ede9fe;color:#4c1d95;}
.b-lease{background:#e0f2fe;color:#0c4a6e;}
.b-moto{background:#fef9c3;color:#713f12;}
.b-def{background:#f1f5f9;color:#475569;}
.hit{background:#f8fafc;border-left:3px solid #93c5fd;border-radius:0 5px 5px 0;padding:0.6rem 0.85rem;margin-top:0.45rem;font-size:0.78rem;color:#334155;line-height:1.65;}
.hit-lbl{font-size:0.65rem;font-weight:700;color:#1a56db;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.25rem;}
.hit b{background:#fef08a;color:#0b1929;padding:0 2px;border-radius:2px;}

/* Q&A */
.qa-outer{max-width:820px;margin:0 auto;}
.qa-lbl{font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.45rem;}
.sq-wrap{display:flex;flex-wrap:wrap;gap:0.45rem;margin-bottom:1.1rem;}
.sq{background:#fff;border:1px solid #cdd5e0;border-radius:20px;padding:0.3rem 0.8rem;font-size:0.75rem;color:#334155;cursor:pointer;transition:all 0.15s;}
.sq:hover{border-color:#1a56db;background:#eff4ff;color:#1a56db;}
.ans-wrap{background:#fff;border:1px solid #dde4ef;border-radius:9px;overflow:hidden;margin-top:1.1rem;box-shadow:0 2px 8px rgba(0,0,0,0.06);}
.ans-hdr{background:#0b1929;padding:0.65rem 1.1rem;display:flex;align-items:center;gap:0.5rem;}
.ans-hdr-t{font-size:0.7rem;font-weight:700;color:#c0d4e8;text-transform:uppercase;letter-spacing:0.8px;}
.ans-body{padding:1.2rem 1.4rem;font-size:0.88rem;color:#1e293b;line-height:1.8;}

/* Browse */
.browse-bar{display:flex;align-items:center;justify-content:space-between;padding:0.65rem 1rem;background:#fff;border:1px solid #dde4ef;border-radius:8px;margin-bottom:0.9rem;}
.browse-ct{font-size:0.78rem;color:#64748b;}
.browse-ct b{color:#0b1929;}

/* Sidebar nav */
.sb-logo{padding:1.1rem 1.1rem 0.75rem;border-bottom:1px solid #162840;margin-bottom:0.4rem;}
.sb-logo-t{font-size:0.75rem;font-weight:700;color:#e0ecf8;}
.sb-logo-s{font-size:0.62rem;color:#3a5a7a;margin-top:2px;}
.sb-sec{font-size:0.6rem;font-weight:700;color:#2a4a6a;text-transform:uppercase;letter-spacing:1.2px;padding:0.8rem 1.1rem 0.35rem;}
.sb-tag{display:inline-block;background:#1a3a5c;color:#7ab3e0;font-size:0.65rem;font-weight:600;padding:0.18rem 0.5rem;border-radius:4px;margin:0.12rem;border:1px solid #2a4a6c;}

/* Empty state */
.empty{text-align:center;padding:3rem 1rem;color:#94a3b8;}
.empty-t{font-size:0.9rem;font-weight:600;color:#475569;margin-top:0.5rem;}
.empty-s{font-size:0.78rem;margin-top:0.25rem;}

.stAlert{border-radius:7px!important;font-size:0.83rem!important;}
.stCheckbox label{color:#475569!important;font-size:0.82rem!important;}
.stSpinner>div{border-top-color:#1a56db!important;}
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def get_index():
    return load_index(DEFAULT_INDEX)

index       = get_index()
companies   = sorted(index["company"].dropna().unique())
asset_types = sorted(index["asset_type"].dropna().unique())
years       = sorted({int(d[:4]) for d in index["filing_date"].dropna() if len(d) >= 4}, reverse=True)

try:
    principal_val = index["aggregate_principal_amount"].dropna().str.replace(r"[$,]","",regex=True).astype(float).sum()/1e9
    principal_str = f"${principal_val:.1f}B"
except:
    principal_str = "N/A"

try:
    apr_str  = f"{index['wa_apr'].dropna().astype(float).mean():.2f}%"
except:
    apr_str  = "N/A"

try:
    fico_str = f"{index['wa_fico'].dropna().astype(float).mean():.0f}"
except:
    fico_str = "N/A"

ASSET_LABELS = {
    "auto_loans":"Auto Loans","auto_loans_subprime":"Subprime Auto",
    "cmbs":"CMBS","device_payment_revolving":"Device Payment",
    "credit_card_revolving":"Credit Card","auto_leases":"Auto Leases","motorcycle_loans":"Motorcycle",
}
BADGE = {
    "auto_loans":"b-auto","auto_loans_subprime":"b-sub","cmbs":"b-cmbs",
    "device_payment_revolving":"b-dev","credit_card_revolving":"b-cc",
    "auto_leases":"b-lease","motorcycle_loans":"b-moto",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
      <div style="display:flex;align-items:center;gap:0.55rem;">
        <div style="width:26px;height:26px;background:#1a56db;border-radius:5px;
                    display:flex;align-items:center;justify-content:center;
                    font-size:0.8rem;font-weight:800;color:#fff;flex-shrink:0;">P</div>
        <div>
          <div class="sb-logo-t">PIMCO ABS Intelligence</div>
          <div class="sb-logo-s">Prospectus Surveillance</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">Filters</div>', unsafe_allow_html=True)
    selected_company = st.selectbox("Issuer",       ["All Issuers"]       + list(companies))
    selected_asset   = st.selectbox("Asset Class",  ["All Asset Classes"] + list(asset_types),
                                    format_func=lambda x: ASSET_LABELS.get(x, x) if x != "All Asset Classes" else x)
    selected_year    = st.selectbox("Filing Year",  ["All Years"]         + [str(y) for y in years])

    active = [v for v in [selected_company, selected_asset, selected_year]
              if v not in ("All Issuers","All Asset Classes","All Years")]
    if active:
        tags = "".join(f'<span class="sb-tag">{v}</span>' for v in active)
        st.markdown(f'<div style="padding:0.4rem 1.1rem;">{tags}</div>', unsafe_allow_html=True)
        if st.button("Clear Filters", use_container_width=True):
            st.rerun()

    st.markdown('<div class="sb-sec" style="margin-top:0.8rem;">Corpus</div>', unsafe_allow_html=True)
    rows = [("Filings", len(index)), ("Issuers", len(companies)),
            ("Asset Classes", len(asset_types)), ("Principal", principal_str)]
    rows_html = "".join(f"""
      <div style="display:flex;justify-content:space-between;padding:0.4rem 0;
                  border-bottom:1px solid #162840;">
        <span style="font-size:0.73rem;color:#4a6a8a;">{l}</span>
        <span style="font-size:0.73rem;font-weight:600;color:#c0d4e8;">{v}</span>
      </div>""" for l, v in rows)
    st.markdown(f'<div style="padding:0 1.1rem;">{rows_html}</div>', unsafe_allow_html=True)

# ── Topbar ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="topbar">
  <div class="tb-brand">
    <div class="tb-logo">P</div>
    <div>
      <div class="tb-title">ABS Prospectus Intelligence</div>
      <div class="tb-sub">SEC 424H Surveillance &mdash; {len(index)} filings indexed across {len(companies)} issuers</div>
    </div>
  </div>
  <div class="tb-stats">
    <div class="tb-stat"><div class="tb-stat-v">{principal_str}</div><div class="tb-stat-l">Total Principal</div></div>
    <div class="tb-sep"></div>
    <div class="tb-stat"><div class="tb-stat-v">{len(companies)}</div><div class="tb-stat-l">Issuers</div></div>
    <div class="tb-sep"></div>
    <div class="tb-stat"><div class="tb-stat-v">{min(years)}&ndash;{max(years)}</div><div class="tb-stat-l">Coverage</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="main">', unsafe_allow_html=True)

# ── KPI strip ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi-cell">
    <div class="kpi-v">{len(index)}</div>
    <div class="kpi-l">Total Filings</div>
    <div class="kpi-d">SEC 424H documents</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-v">{principal_str}</div>
    <div class="kpi-l">Aggregate Principal</div>
    <div class="kpi-d">Across all indexed deals</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-v">{apr_str}</div>
    <div class="kpi-l">Avg WA APR</div>
    <div class="kpi-d">Weighted average rate</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-v">{fico_str}</div>
    <div class="kpi-l">Avg WA FICO</div>
    <div class="kpi-d">Borrower credit quality</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Charts row ────────────────────────────────────────────────────────────────
ch1, ch2, ch3 = st.columns([1, 1, 1])

CHART_COLORS = ["#1a56db","#2563eb","#3b82f6","#60a5fa","#93c5fd","#bfdbfe","#dbeafe"]

with ch1:
    asset_df = index["asset_type"].value_counts().reset_index()
    asset_df.columns = ["asset","count"]
    asset_df["label"] = asset_df["asset"].map(ASSET_LABELS).fillna(asset_df["asset"])
    fig = px.pie(asset_df, values="count", names="label", hole=0.55,
                 color_discrete_sequence=CHART_COLORS)
    fig.update_traces(textposition="outside", textfont_size=10)
    fig.update_layout(
        title=dict(text="Asset Class Distribution", font=dict(size=12, color="#0b1929"), x=0),
        margin=dict(t=40, b=10, l=10, r=10), height=240,
        paper_bgcolor="#fff", plot_bgcolor="#fff",
        legend=dict(font=dict(size=9), orientation="v", x=1, y=0.5),
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with ch2:
    yr_df = index["filing_date"].str[:4].value_counts().sort_index().reset_index()
    yr_df.columns = ["year","count"]
    fig2 = px.bar(yr_df, x="year", y="count", color_discrete_sequence=["#1a56db"])
    fig2.update_traces(marker_line_width=0)
    fig2.update_layout(
        title=dict(text="Filings by Year", font=dict(size=12, color="#0b1929"), x=0),
        margin=dict(t=40, b=10, l=10, r=10), height=240,
        paper_bgcolor="#fff", plot_bgcolor="#fff",
        xaxis=dict(showgrid=False, tickfont=dict(size=10), title=""),
        yaxis=dict(gridcolor="#f0f2f5", tickfont=dict(size=10), title=""),
        bargap=0.35,
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

with ch3:
    iss_df = index["company"].value_counts().reset_index()
    iss_df.columns = ["issuer","count"]
    fig3 = px.bar(iss_df.head(8), x="count", y="issuer", orientation="h",
                  color_discrete_sequence=["#1a56db"])
    fig3.update_traces(marker_line_width=0)
    fig3.update_layout(
        title=dict(text="Top Issuers", font=dict(size=12, color="#0b1929"), x=0),
        margin=dict(t=40, b=10, l=10, r=10), height=240,
        paper_bgcolor="#fff", plot_bgcolor="#fff",
        xaxis=dict(gridcolor="#f0f2f5", tickfont=dict(size=9), title=""),
        yaxis=dict(showgrid=False, tickfont=dict(size=9), title="", autorange="reversed"),
    )
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_qa, tab_search, tab_browse = st.tabs([
    "  AI Research Assistant  ",
    "  Keyword Search  ",
    "  Document Explorer  ",
])

# ── TAB 1: AI Research Assistant ────────────────────────────────────────────
with tab_qa:
    st.markdown('<div class="qa-outer">', unsafe_allow_html=True)
    st.markdown('<div class="qa-lbl">Suggested Questions</div>', unsafe_allow_html=True)
    SUGGESTED = [
        "Which deals use physical custody of receivables?",
        "What credit enhancement structures are most common?",
        "How do reserve account requirements vary across issuers?",
        "Which CMBS deals have the highest WA LTV?",
        "What are the servicer replacement provisions?",
    ]
    st.markdown(
        '<div class="sq-wrap">' +
        "".join(f'<span class="sq">{q}</span>' for q in SUGGESTED) +
        '</div>', unsafe_allow_html=True
    )
    st.markdown('<div class="qa-lbl">Ask a Question</div>', unsafe_allow_html=True)
    nl_query = st.text_area("question", placeholder="e.g. Which deals use physical custody of receivables?",
                            height=100, label_visibility="collapsed")
    run_qa = st.button("Generate Answer", type="primary", key="btn_qa")
    st.markdown('</div>', unsafe_allow_html=True)

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
                with st.spinner("Retrieving evidence and generating answer…"):
                    try:
                        from openai import OpenAI
                        from answer_questions import answer_question
                        answer = answer_question(nl_query, top_k=5, model="gpt-6-luna", client=OpenAI(api_key=api_key))
                        st.markdown(f"""
                        <div class="ans-wrap">
                          <div class="ans-hdr"><div class="ans-hdr-t">AI Research Assistant &mdash; Answer</div></div>
                          <div class="ans-body">{answer}</div>
                        </div>""", unsafe_allow_html=True)
                    except Exception as exc:
                        st.error(f"Error: {exc}")

# ── TAB 2: Keyword Search ─────────────────────────────────────────────────────
with tab_search:
    col_q, col_rx = st.columns([6, 1])
    with col_q:
        query = st.text_input("query", placeholder="e.g.  reserve account   |   physical\\s+custody   |   weighted average",
                              label_visibility="collapsed")
    with col_rx:
        use_regex = st.checkbox("Regex")
    col_btn, col_hint = st.columns([1, 5])
    with col_btn:
        run_search = st.button("Search", type="primary", use_container_width=True)
    with col_hint:
        st.caption("Sidebar filters apply automatically. Leave query blank to filter by metadata only.")

    if run_search:
        if not query and all(v in ("All Issuers","All Asset Classes","All Years")
                             for v in [selected_company, selected_asset, selected_year]):
            st.warning("Enter a search query or select at least one filter.")
        else:
            with st.spinner("Searching across filings…"):
                try:
                    results = search_filings(
                        query or None, index=index, clean_dir=DEFAULT_CLEAN_DIR,
                        use_regex=use_regex,
                        company=None if selected_company=="All Issuers" else selected_company,
                        asset_type=None if selected_asset=="All Asset Classes" else selected_asset,
                        year=None if selected_year=="All Years" else int(selected_year),
                        max_results=20,
                    )
                except Exception as exc:
                    st.error(f"Search error: {exc}"); results = []

            if not results:
                st.markdown('<div class="empty"><div class="empty-t">No filings matched</div><div class="empty-s">Try broadening your query or adjusting the sidebar filters</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:0.78rem;color:#64748b;margin-bottom:0.9rem;"><b style="color:#0b1929;">{len(results)}</b> filing(s) matched</div>', unsafe_allow_html=True)
                for r in results:
                    deal  = r["deal_name"] or r["company"]
                    atype = r["asset_type"]
                    bcls  = BADGE.get(atype, "b-def")
                    albl  = ASSET_LABELS.get(atype, atype)
                    hits_html = ""
                    for i, hit in enumerate(r["hits"], 1):
                        snippet = hit["snippet"].replace("<<","<b>").replace(">>","</b>")
                        hits_html += f'<div class="hit"><div class="hit-lbl">Match {i} &nbsp;&middot;&nbsp; {hit["citation"]}</div>{snippet}</div>'
                    st.markdown(f"""
                    <div class="rc">
                      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:0.3rem;">
                        <div class="rc-title">{deal}</div>
                        <span class="rc-badge {bcls}">{albl}</span>
                      </div>
                      <div class="rc-meta">
                        <span>{r['company']}</span>
                        <span>{r['filing_date']}</span>
                        <span>{r['match_count']} match(es)</span>
                      </div>
                      {hits_html}
                    </div>""", unsafe_allow_html=True)

# ── TAB 3: Document Explorer ────────────────────────────────────────────────────
with tab_browse:
    filtered = index.copy()
    if selected_company != "All Issuers":      filtered = filtered[filtered["company"]==selected_company]
    if selected_asset   != "All Asset Classes": filtered = filtered[filtered["asset_type"]==selected_asset]
    if selected_year    != "All Years":         filtered = filtered[filtered["filing_date"].str.startswith(selected_year)]

    csv = filtered.to_csv(index=False).encode()
    col_info, col_dl = st.columns([5, 1])
    with col_info:
        st.markdown(f'<div class="browse-bar"><span class="browse-ct">Showing <b>{len(filtered)}</b> of <b>{len(index)}</b> filings &nbsp;&middot;&nbsp; <b>{filtered["company"].nunique()}</b> issuers &nbsp;&middot;&nbsp; <b>{filtered["asset_type"].nunique()}</b> asset classes</span></div>', unsafe_allow_html=True)
    with col_dl:
        st.download_button("Export CSV", csv, "filings.csv", "text/csv", use_container_width=True)

    display_cols = ["company","deal_name","asset_type","filing_date",
                    "aggregate_principal_amount","wa_apr","wa_fico","credit_enhancement_types"]
    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        use_container_width=True, height=520,
        column_config={
            "company":                    st.column_config.TextColumn("Issuer",              width="medium"),
            "deal_name":                  st.column_config.TextColumn("Deal Name",           width="large"),
            "asset_type":                 st.column_config.TextColumn("Asset Class",         width="medium"),
            "filing_date":                st.column_config.TextColumn("Filed",               width="small"),
            "aggregate_principal_amount": st.column_config.TextColumn("Principal",           width="medium"),
            "wa_apr":                     st.column_config.TextColumn("WA APR",              width="small"),
            "wa_fico":                    st.column_config.TextColumn("WA FICO",             width="small"),
            "credit_enhancement_types":   st.column_config.TextColumn("Credit Enhancement",  width="large"),
        },
    )

st.markdown('</div>', unsafe_allow_html=True)
