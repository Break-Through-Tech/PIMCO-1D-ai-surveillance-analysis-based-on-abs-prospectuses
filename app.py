"""PIMCO ABS Prospectus Intelligence Platform."""
import os, sys
import re
from html import escape
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import streamlit as st
import pandas as pd

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "notebooks"))

from search_filings import load_index, search_filings, DEFAULT_CLEAN_DIR, DEFAULT_INDEX
from styles import DESIGN_CSS
from charts import (
    asset_donut, principal_by_asset, principal_by_year,
    apr_by_asset, issuer_activity, fico_distribution, ASSET_LABELS,
)

st.set_page_config(
    page_title="PIMCO | ABS Intelligence",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(DESIGN_CSS, unsafe_allow_html=True)

BADGE = {
    "auto_loans": "b-auto", "auto_loans_subprime": "b-sub", "cmbs": "b-cmbs",
    "device_payment_revolving": "b-dev", "credit_card_revolving": "b-cc",
    "auto_leases": "b-lease", "motorcycle_loans": "b-moto",
}

@st.cache_data
def get_index():
    return load_index(DEFAULT_INDEX)

index       = get_index()
companies   = sorted(index["company"].dropna().unique())
asset_types = sorted(index["asset_type"].dropna().unique())
years       = sorted({int(d[:4]) for d in index["filing_date"].dropna() if len(d) >= 4}, reverse=True)

@st.cache_data
def get_filing_urls():
    manifest_path = ROOT / "data" / "_manifest.csv"
    if not manifest_path.exists():
        return {}
    manifest = pd.read_csv(manifest_path, dtype=str).fillna("")
    links = {}
    for _, item in manifest.iterrows():
        local_name = Path(item.get("local_path", "").replace("\\", "/")).stem
        if local_name and item.get("doc_url"):
            links[local_name] = item["doc_url"]
    return links

filing_urls = get_filing_urls()

def render_source_cards(chunks):
    if not chunks:
        st.caption("No source passages were retrieved.")
        return
    for number, item in enumerate(chunks, 1):
        filing = str(item.get("filing_stem", ""))
        page = escape(str(item.get("page_num", "?")))
        printed = escape(str(item.get("printed_label", "")))
        section = escape(str(item.get("toc_section", "")))
        issuer = escape(str(item.get("company") or "Issuer"))
        deal = escape(str(item.get("deal_name") or filing.replace("_", " ")))
        excerpt = escape(str(item.get("embed_text", ""))[:360])
        page_label = f"Printed page {printed} · physical page {page}" if printed else f"Physical page {page}"
        original_url = filing_urls.get(filing, "")
        source_link = (
            f'<a class="source-link" href="{escape(original_url, quote=True)}" target="_blank" rel="noopener">Open original SEC filing ↗</a>'
            if original_url else '<span class="source-unavailable">Original filing link unavailable</span>'
        )
        section_chip = f'<span class="ai-src-chip">{section}</span>' if section else ""
        excerpt_html = f'<div class="ai-src-excerpt">{excerpt}</div>' if excerpt else ""
        filing_label = escape(filing.replace("_", " "))
        st.markdown(f"""
        <div class="ai-src-card" id="source-{number}">
          <div class="ai-src-header"><span class="ai-src-num">{number}</span><span class="ai-src-issuer">{issuer}</span></div>
          <div class="ai-src-deal">{deal}</div>
          <div class="ai-src-filing">{filing_label}</div>
          <div class="ai-src-chips"><span class="ai-src-chip">{page_label}</span>{section_chip}</div>
          {excerpt_html}{source_link}
        </div>
        """, unsafe_allow_html=True)

def _num(s):
    return pd.to_numeric(s.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")

def _format_financial(value):
    if pd.isna(value):
        return "N/A"
    value = float(value)
    if abs(value) >= 1_000_000_000:
        number, suffix, precision = value / 1_000_000_000, "B", 2
    elif abs(value) >= 1_000_000:
        number, suffix, precision = value / 1_000_000, "M", 1
    elif abs(value) >= 1_000:
        number, suffix, precision = value / 1_000, "K", 1
    else:
        return f"${value:,.0f}"
    text = f"{number:,.{precision}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return f"${text}{suffix}"

def reset_filters():
    st.session_state["filter_issuer"] = "All Issuers"
    st.session_state["filter_asset"] = "All Asset Classes"
    st.session_state["filter_year"] = "All Years"

def reset_research():
    st.session_state["last_answer"] = None
    st.session_state["last_chunks"] = []
    st.session_state["last_q"] = ""
    st.session_state["followup_q"] = ""

try:    principal_str = f"${_num(index['aggregate_principal_amount']).sum()/1e9:.1f}B"
except: principal_str = "N/A"
try:    apr_str  = f"{pd.to_numeric(index['wa_apr'], errors='coerce').mean():.2f}%"
except: apr_str  = "N/A"
try:    fico_str = f"{pd.to_numeric(index['wa_fico'], errors='coerce').mean():.0f}"
except: fico_str = "N/A"
try:    deal_str = f"${_num(index['aggregate_principal_amount']).mean()/1e6:.0f}M"
except: deal_str = "N/A"

# Sidebar
NAV_ITEMS = [
    ("Market Overview", "nav_overview", ":material/space_dashboard:"),
    ("AI Assistant", "nav_research", ":material/auto_awesome:"),
    ("Keyword Search", "nav_search", ":material/search:"),
    ("Document Explorer", "nav_documents", ":material/description:"),
]
PAGE_ROUTES = {"overview": "Market Overview", "research": "AI Assistant", "search": "Keyword Search", "documents": "Document Explorer"}
PAGE_TO_ROUTE = {label: route for route, label in PAGE_ROUTES.items()}
if "page" not in st.session_state:
    st.session_state.page = PAGE_ROUTES.get(st.query_params.get("page", "overview"), "Market Overview")
elif st.session_state.page == "AI Research Assistant":
    # Migrate the label stored in existing Streamlit browser sessions.
    st.session_state.page = "AI Assistant"

with st.sidebar:
    st.markdown('<div class="sb-brand"><span class="brand-mark">P</span><div><div class="sb-brand-name">ABS Intelligence</div><div class="sb-brand-sub">Prospectus Analysis</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section-label">Workspace</div>', unsafe_allow_html=True)
    for label, key, svg in NAV_ITEMS:
        with st.container(key=key):
            if st.button(label, key=f"go_{key}", icon=svg, width="stretch", type="primary" if st.session_state.page == label else "secondary"):
                st.session_state.page = label
                st.query_params["page"] = PAGE_TO_ROUTE[label]
                st.rerun()
    page = st.session_state.page

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section-label">Filters</div>', unsafe_allow_html=True)

    selected_company = st.selectbox("Issuer", ["All Issuers"] + list(companies), key="filter_issuer")
    selected_asset   = st.selectbox(
        "Asset Class", ["All Asset Classes"] + list(asset_types),
        format_func=lambda x: ASSET_LABELS.get(x, x) if x != "All Asset Classes" else x,
        key="filter_asset",
    )
    selected_year = st.selectbox("Filing Year", ["All Years"] + [str(y) for y in years], key="filter_year")

    active = [v for v in [selected_company, selected_asset, selected_year]
              if v not in ("All Issuers", "All Asset Classes", "All Years")]
    if active:
        tags = "".join(f'<span class="sb-filter-tag">{escape(str(v))}</span>' for v in active)
        st.markdown(f'<div style="padding:.35rem 1.1rem .55rem;">{tags}</div>', unsafe_allow_html=True)
        st.button("Reset filters", key="reset_filters", width="stretch", on_click=reset_filters)

filtered_index = index.copy()
if selected_company != "All Issuers":
    filtered_index = filtered_index[filtered_index["company"] == selected_company]
if selected_asset != "All Asset Classes":
    filtered_index = filtered_index[filtered_index["asset_type"] == selected_asset]
if selected_year != "All Years":
    filtered_index = filtered_index[filtered_index["filing_date"].str.startswith(selected_year)]
if filtered_index.empty:
    principal_str = deal_str = apr_str = fico_str = "N/A"
else:
    filing_principal = _num(filtered_index["aggregate_principal_amount"])
    principal_str = _format_financial(filing_principal.sum(min_count=1))
    deal_str = _format_financial(filing_principal.mean())
    apr_numbers = pd.to_numeric(filtered_index["wa_apr"], errors="coerce")
    fico_numbers = pd.to_numeric(filtered_index["wa_fico"], errors="coerce")
    apr_str = f"{apr_numbers.mean():.2f}%" if apr_numbers.notna().any() else "N/A"
    fico_str = f"{fico_numbers.mean():.0f}" if fico_numbers.notna().any() else "N/A"

# ── Topbar ────────────────────────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Market Overview
# ════════════════════════════════════════════════════════════════════════════
if page == "Market Overview":
    filing_count = len(filtered_index)
    issuer_count = filtered_index["company"].nunique()
    asset_class_count = filtered_index["asset_type"].nunique()
    st.markdown("""
    <div class="page-hdr market-page-hdr">
      <div class="page-hdr-title">ABS Market Overview</div>
      <div class="page-hdr-sub">Explore deal characteristics and financial trends across indexed ABS prospectuses.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="market-context">
      <div class="market-context-stats"><span><b>{filing_count:,}</b> filings</span><i></i><span><b>{issuer_count:,}</b> issuers</span><i></i><span><b>{asset_class_count:,}</b> asset classes</span></div>
      <div class="market-coverage">Coverage reflects the indexed document library and may not represent the full ABS market.</div>
    </div>
    """, unsafe_allow_html=True)

    apr_values = pd.to_numeric(filtered_index["wa_apr"], errors="coerce")
    fico_values = pd.to_numeric(filtered_index["wa_fico"], errors="coerce")

    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card kc-blue" title="Sum of reported aggregate principal amounts for the currently filtered filings. This is indexed deal principal, not an estimate of the full ABS market.">
        <div class="kpi-card-top"><span class="kpi-card-label">Aggregate Principal</span><span class="kpi-card-icon icon-blue">$</span></div>
        <div class="kpi-card-value">{principal_str}</div>
        <div class="kpi-card-sub">Across {filing_count:,} filtered filings</div>
      </div>
      <div class="kpi-card kc-teal" title="Arithmetic mean of non-missing reported aggregate principal amounts across the currently filtered filings; each filing is equally weighted.">
        <div class="kpi-card-top"><span class="kpi-card-label">Avg Deal Size</span><span class="kpi-card-icon icon-teal">&#8776;</span></div>
        <div class="kpi-card-value">{deal_str}</div>
        <div class="kpi-card-sub">Mean reported principal per filing</div>
      </div>
      <div class="kpi-card kc-amber" title="Arithmetic mean of non-missing reported WA APR values in the filtered dataset. This is not weighted by deal principal.">
        <div class="kpi-card-top"><span class="kpi-card-label">Avg WA APR</span><span class="kpi-card-icon icon-amber">%</span></div>
        <div class="kpi-card-value">{apr_str}</div>
        <div class="kpi-card-sub">Mean of reported deal WA APRs</div>
      </div>
      <div class="kpi-card kc-violet" title="Arithmetic mean of non-missing reported WA FICO values across the filtered filings; the deal-level values are equally weighted.">
        <div class="kpi-card-top"><span class="kpi-card-label">Avg WA FICO</span><span class="kpi-card-icon icon-violet">&#9733;</span></div>
        <div class="kpi-card-value">{fico_str}</div>
        <div class="kpi-card-sub">Mean of reported deal WA FICO</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(key="chart_asset_mix"):
            st.markdown('<div class="chart-card-title" title="Number of indexed filings grouped by asset class.">Asset Class Distribution</div><div class="chart-card-sub">Filing count by asset type</div>', unsafe_allow_html=True)
            st.plotly_chart(asset_donut(filtered_index), width="stretch", config={"displayModeBar": False})
    with col_b:
        with st.container(key="chart_principal_asset"):
            st.markdown('<div class="chart-card-title" title="Sum of reported aggregate principal amounts within each asset class.">Principal by Asset Class</div><div class="chart-card-sub">Aggregate notional in USD billions</div>', unsafe_allow_html=True)
            st.plotly_chart(principal_by_asset(filtered_index), width="stretch", config={"displayModeBar": False})

    col_c, col_d = st.columns(2)
    with col_c:
        with st.container(key="chart_principal_year"):
            st.markdown('<div class="chart-card-title" title="Sum of reported aggregate principal by prospectus filing year.">Principal Volume by Year</div><div class="chart-card-sub">Aggregate deal size trend (USD billions)</div>', unsafe_allow_html=True)
            st.plotly_chart(principal_by_year(filtered_index), width="stretch", config={"displayModeBar": False})
    with col_d:
        with st.container(key="chart_apr_asset"):
            st.markdown('<div class="chart-card-title" title="Arithmetic mean of reported WA APR values by asset class; each filing is equally weighted.">Avg WA APR by Asset Class</div><div class="chart-card-sub">Mean reported WA APR across filings</div>', unsafe_allow_html=True)
            st.plotly_chart(apr_by_asset(filtered_index), width="stretch", config={"displayModeBar": False})

    col_e, col_f = st.columns(2)
    with col_e:
        with st.container(key="chart_issuer_activity"):
            st.markdown('<div class="chart-card-title" title="Count of indexed filings for each issuer within the current filters.">Filing Activity by Issuer</div><div class="chart-card-sub">Indexed filing count per issuer</div>', unsafe_allow_html=True)
            st.plotly_chart(issuer_activity(filtered_index), width="stretch", config={"displayModeBar": False})
    with col_f:
        with st.container(key="chart_credit_scatter"):
            st.markdown('<div class="chart-card-title" title="Each point is one filing with reported WA FICO and WA APR; points are not principal-weighted.">WA FICO vs WA APR</div><div class="chart-card-sub">Reported deal-level credit and rate metrics</div>', unsafe_allow_html=True)
            st.plotly_chart(fico_distribution(filtered_index), width="stretch", config={"displayModeBar": False})

    # Observations are derived from the filtered indexed filings on every rerun.
    asset_counts = filtered_index["asset_type"].dropna().value_counts()
    count_total = int(asset_counts.sum())
    if count_total:
        count_leaders = asset_counts.head(2)
        concentration = count_leaders.sum() / count_total * 100
        concentration_names = " + ".join(ASSET_LABELS.get(name, name) for name in count_leaders.index)
        concentration_detail = f"{concentration_names} account for {int(count_leaders.sum()):,} of {count_total:,} filings with an asset-class label."
        concentration_value = f"{concentration:.1f}%"
    else:
        concentration_value, concentration_names, concentration_detail = "N/A", "No asset-class data", "No filtered filings contain an asset-class label."

    principal_by_class = pd.DataFrame({
        "asset_type": filtered_index["asset_type"],
        "principal": _num(filtered_index["aggregate_principal_amount"]),
    }).dropna(subset=["asset_type", "principal"]).groupby("asset_type")["principal"].sum().sort_values(ascending=False)
    if not principal_by_class.empty:
        leader_type = principal_by_class.index[0]
        leader_principal = _format_financial(principal_by_class.iloc[0])
        leader_label = ASSET_LABELS.get(leader_type, leader_type)
        principal_detail = f"{leader_label} has the highest summed reported principal in this filtered dataset."
    else:
        leader_principal, leader_label, principal_detail = "N/A", "No principal data", "No reported principal amounts are available for the current filters."

    apr_by_class_values = pd.DataFrame({
        "asset_type": filtered_index["asset_type"], "apr": apr_values,
    }).dropna(subset=["asset_type", "apr"]).groupby("asset_type")["apr"].mean().sort_values(ascending=False)
    if not apr_by_class_values.empty:
        highest_apr_type = apr_by_class_values.index[0]
        highest_apr = f"{apr_by_class_values.iloc[0]:.2f}%"
        highest_apr_label = ASSET_LABELS.get(highest_apr_type, highest_apr_type)
        highest_apr_detail = f"{highest_apr_label} has the highest simple mean of reported WA APR values."
    else:
        highest_apr, highest_apr_label, highest_apr_detail = "N/A", "No APR data", "No reported WA APR values are available for the current filters."

    st.markdown(f"""
    <section class="market-observations">
      <div class="market-section-heading"><span class="market-section-icon">↗</span><div><h2>Key Market Observations</h2><p>Calculated from the currently filtered indexed filings</p></div></div>
      <div class="observation-grid">
        <article class="observation-card"><span class="observation-label">Top two classes by filing count</span><strong>{concentration_value}</strong><b>{escape(concentration_names)}</b><p>{escape(concentration_detail)}</p></article>
        <article class="observation-card"><span class="observation-label">Largest asset class by principal</span><strong>{escape(leader_principal)}</strong><b>{escape(leader_label)}</b><p>{escape(principal_detail)}</p></article>
        <article class="observation-card"><span class="observation-label">Highest average reported WA APR</span><strong>{escape(highest_apr)}</strong><b>{escape(highest_apr_label)}</b><p>{escape(highest_apr_detail)}</p></article>
      </div>
    </section>
    """, unsafe_allow_html=True)

    with st.container(key="market_ai_cta"):
        cta_copy, cta_action = st.columns([5, 1.5], vertical_alignment="center")
        with cta_copy:
            st.markdown('<div class="market-cta-title">Go beyond the numbers</div><div class="market-cta-copy">Ask questions about the filings behind these metrics and trace answers back to original prospectus evidence.</div>', unsafe_allow_html=True)
        with cta_action:
            if st.button("Open AI Assistant", key="market_ai_cta_button", icon=":material/auto_awesome:", type="primary", width="content"):
                st.session_state.page = "AI Assistant"
                st.query_params["page"] = "research"
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — AI Assistant
# ════════════════════════════════════════════════════════════════════════════
elif page == "AI Assistant":

    # session state
    for k, v in [("qa_history",[]),("qa_prefill",""),("last_answer",None),
                 ("last_chunks",[]),("last_q",""),("open_cat","")]:
        if k not in st.session_state:
            st.session_state[k] = v
    has_answer = bool(st.session_state["last_answer"])

    CATS = {
        "Collateral Ownership & True Sale": {
            "icon": ":material/account_balance:",
            "sub": "Title transfer, perfection actions & substitutions",
            "questions": [
                "Has legal title to the receivables been transferred via a true sale at each step?",
                "Are any receivable transfers conditional, delayed, or subject to post-closing perfection actions (e.g., pending title issuance up to 180 days)?",
                "Are post-closing substitutions or repurchases permitted, and are they capped and objectively defined?",
                "Are vehicle titles perfected in the trust's name?",
            ],
        },
        "Custody, Control & Perfection": {
            "icon": ":material/folder_managed:",
            "sub": "Collateral holders, custodians & file controls",
            "questions": [
                "Who holds the collateral and in what capacity?",
                "Is the collateral serviced by a third party?",
                "Is the collateral custodied by a third party?",
                "If so, what tier is the collateral custodian?",
                "How are documents custodied?",
                "If a third party is used, what tier is the third-party custodian?",
                "Are the documents custodied using third-party software (eVault)?",
                "Are the files custodied in paper form?",
                "Is there a mix of paper and electronic collateral files?",
            ],
        },
        "Double-Pledging & Warehouse Risk": {
            "icon": ":material/lock:",
            "sub": "Lien status, warehouse release & pledge controls",
            "questions": [
                "Is the collateral free and clear of liens?",
                "Proceeds are used to repay warehouse facilities. Were any receivables pledged to warehouse lenders, and how is release verified?",
                "Are there operational controls preventing the same receivable from being pledged to multiple trusts or facilities?",
            ],
        },
        "Commingling & Cash Control": {
            "icon": ":material/account_balance_wallet:",
            "sub": "Collection accounts, segregation & insolvency",
            "questions": [
                "Where are collections initially deposited?",
                "What happens to collections in a servicer bankruptcy?",
                "What happens to collections in an issuer bankruptcy?",
                "Are collections segregated in a specific account?",
                "How long can collections stay in a servicer account?",
            ],
        },
        "Amendments, Waivers & Control Rights": {
            "icon": ":material/tune:",
            "sub": "Controlling class, consent & amendment powers",
            "questions": [
                "Which class is the Controlling Class, and can it waive defaults or amend economics without minority consent?",
                "Can rating-agency confirmation substitute for noteholder consent?",
            ],
        },
        "Enforcement & Post-Default Realities": {
            "icon": ":material/gavel:",
            "sub": "Default control, liquidation & proceeds",
            "questions": [
                "Who controls liquidation timing and method after default?",
                "Are liquidation proceeds distributed differently than ongoing collections?",
            ],
        },
    }

    requested_category = st.query_params.get("category", "")
    if requested_category in CATS and not st.session_state["open_cat"]:
        st.session_state["open_cat"] = requested_category

    # ── LANDING ──────────────────────────────────────────────────────────────
    if not has_answer:
        scoped_index = index.copy()
        scope_parts = []
        if selected_company != "All Issuers":
            scoped_index = scoped_index[scoped_index["company"] == selected_company]
            scope_parts.append(selected_company.replace("_", " ").title())
        if selected_asset != "All Asset Classes":
            scoped_index = scoped_index[scoped_index["asset_type"] == selected_asset]
            scope_parts.append(ASSET_LABELS.get(selected_asset, selected_asset))
        if selected_year != "All Years":
            scoped_index = scoped_index[scoped_index["filing_date"].str.startswith(selected_year)]
            scope_parts.append(selected_year)
        scope_label = " | ".join(scope_parts + [f"{len(scoped_index)} filings"])

        # Hero
        st.markdown(f"""
        <div class="ai-hero">
          <div class="ai-hero-icon-wrap">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#234B7C" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/>
              <path d="m19 15 .9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z"/>
              <path d="m5 3 .6 1.4L7 5l-1.4.6L5 7l-.6-1.4L3 5l1.4-.6L5 3Z"/>
            </svg>
          </div>
          <div class="ai-hero-title">What do you want to know?</div>
          <div class="ai-hero-sub">Ask a question and get an answer grounded in the original prospectus.</div>
        </div>
        """, unsafe_allow_html=True)

        # A keyed Streamlit container owns the real form widgets; CSS styles this wrapper.
        with st.container(key="ai_prompt_card"):
            st.markdown('<div class="prompt-label">Ask a question about the prospectus</div>', unsafe_allow_html=True)
            if st.session_state.get("qa_prefill"):
                st.session_state["landing_q"] = st.session_state.pop("qa_prefill")
            with st.form("research_question_form", clear_on_submit=False):
                nl_query = st.text_area(
                    "Question", height=88, label_visibility="collapsed",
                    placeholder="e.g. Has legal title been transferred via a true sale at each step?",
                    key="landing_q",
                )
                scope_col, action_col = st.columns([5, 1.35], vertical_alignment="center")
                with scope_col:
                    st.markdown(f'<div class="ai-scope-pill"><span class="ai-scope-dot"></span><span>Selected documents</span><b>{escape(scope_label)}</b></div>', unsafe_allow_html=True)
                with action_col:
                    run_qa = st.form_submit_button("Ask assistant  →", type="primary", width="content")

        st.markdown('<div class="suggestions-heading"><span>Browse question topics</span><span>Choose a topic to see suggested questions</span></div>', unsafe_allow_html=True)
        cat_names = list(CATS.keys())
        for row in range(3):
            c1, c2 = st.columns(2, gap="medium")
            for ci, col in ((row * 2, c1), (row * 2 + 1, c2)):
                cat_name = cat_names[ci]
                cat = CATS[cat_name]
                with col:
                    with st.container(key=f"cat_card_{ci}"):
                        is_open = st.session_state["open_cat"] == cat_name
                        if st.button(cat_name, key=f"tog_{ci}", icon=cat["icon"], type="secondary", width="stretch"):
                            st.session_state["open_cat"] = "" if is_open else cat_name
                            if is_open:
                                st.query_params.pop("category", None)
                            else:
                                st.query_params["category"] = cat_name
                            st.rerun()
                        st.markdown(f'<div class="category-subtitle">{escape(cat["sub"])}</div>', unsafe_allow_html=True)
                        if is_open:
                            for qi, q in enumerate(cat["questions"]):
                                if st.button(q, key=f"q_{ci}_{qi}", width="stretch"):
                                    st.session_state["qa_prefill"] = q
                                    st.session_state["open_cat"] = ""
                                    st.query_params.pop("category", None)
                                    st.rerun()

        st.markdown('<div class="grounding-note"><span class="grounding-mark">i</span><span>Answers are grounded in retrieved prospectus passages. Open the cited filing to review the original context.</span></div>', unsafe_allow_html=True)

        # Handle submit
        if run_qa:
            q = nl_query.strip()
            if not q:
                st.warning("Enter a question first.")
            else:
                api_key = os.getenv("OPENAI_API_KEY", "")
                if not api_key:
                    st.error("No API key found. Add OPENAI_API_KEY to your .env file.")
                elif not (ROOT / "data" / "embeddings" / "vectors.npy").exists():
                    st.error("Embedding index not found. Run `python notebooks/embed_chunks.py`.")
                else:
                    prog = st.empty()
                    prog.markdown("""
                    <div class="ai-progress-wrap">
                      <div class="ai-prog-step done"><div class="ai-prog-icon">✓</div>Embedding your question</div>
                      <div class="ai-prog-step active"><div class="ai-prog-icon">↻</div>Searching prospectuses…</div>
                      <div class="ai-prog-step"><div class="ai-prog-icon"></div>Retrieving relevant evidence</div>
                      <div class="ai-prog-step"><div class="ai-prog-icon"></div>Generating cited answer</div>
                    </div>
                    """, unsafe_allow_html=True)
                    try:
                        from openai import OpenAI
                        from answer_questions import answer_question
                        from search_embeddings import retrieve
                        client = OpenAI(api_key=api_key)
                        query_filters = {}
                        if selected_company != "All Issuers": query_filters["company"] = selected_company
                        if selected_asset != "All Asset Classes": query_filters["asset_type"] = selected_asset
                        if selected_year != "All Years": query_filters["year"] = selected_year
                        chunks = retrieve(q, top_k=5, client=client, filters=query_filters)
                        prog.markdown("""
                        <div class="ai-progress-wrap">
                          <div class="ai-prog-step done"><div class="ai-prog-icon">✓</div>Embedding your question</div>
                          <div class="ai-prog-step done"><div class="ai-prog-icon">✓</div>Prospectus chunks retrieved</div>
                          <div class="ai-prog-step active"><div class="ai-prog-icon">↻</div>Generating cited answer…</div>
                        </div>
                        """, unsafe_allow_html=True)
                        answer = answer_question(q, top_k=5, model="gpt-6-luna", client=client, retrieved=chunks)
                        prog.empty()
                        st.session_state["last_answer"] = answer
                        st.session_state["last_chunks"] = chunks
                        st.session_state["last_q"] = q
                        st.session_state["qa_history"].append({"q": q, "a": answer, "ts": datetime.now().strftime("%H:%M")})
                        st.rerun()
                    except Exception as exc:
                        prog.empty()
                        st.error(f"Error: {exc}")

    # ── WORKSPACE ────────────────────────────────────────────────────────────
    else:
        col_main, col_src = st.columns([2, 1])

        with col_main:
            # Question history + start over
            if st.session_state["qa_history"]:
                with st.expander("Question history", expanded=False):
                    for item in reversed(st.session_state["qa_history"][-6:]):
                        is_active = item["q"] == st.session_state["last_q"]
                        cls = "ai-hist-card active" if is_active else "ai-hist-card"
                        st.markdown(
                            f'<div class="{cls}"><div class="ai-hist-q">{item["q"]}</div>'
                            f'<div class="ai-hist-time">{item["ts"]}</div></div>',
                            unsafe_allow_html=True,
                        )

            # Question bubble
            st.markdown(f'<div class="ai-q-bubble">{escape(st.session_state["last_q"])}</div>', unsafe_allow_html=True)

            # Answer card
            n_src = len(st.session_state["last_chunks"])
            with st.container(key="answer_panel"):
                st.markdown(f'<div class="ai-answer-card-hdr"><span class="ai-answer-badge">AI</span><span class="ai-answer-card-title">Answer</span><span class="ai-footer-chip">{n_src} cited passages</span></div>', unsafe_allow_html=True)
                linked_answer = re.sub(r"\[Source\s+(\d+)\]", r"[Source \1](#source-\1)", st.session_state["last_answer"])
                st.markdown(linked_answer, help="Citations jump to the matching retrieved passage.")
                st.markdown(f'<div class="ai-answer-footer"><span class="ai-footer-chip">Evidence-grounded response</span><span class="ai-footer-chip">{n_src} source passages</span></div>', unsafe_allow_html=True)

            # Follow-up input
            st.markdown('<div style="padding:.6rem 1rem .2rem;font-size:.72rem;color:#94A3B8;font-weight:500;">Ask a follow-up</div>', unsafe_allow_html=True)
            followup = st.text_input("followup", label_visibility="collapsed",
                                     placeholder="Ask a follow-up question…", key="followup_q")
            col_fu, col_new = st.columns([3, 1])
            with col_fu:
                run_fu = st.button("Ask follow-up  →", key="btn_fu", width="stretch")
            with col_new:
                st.button("New question", key="btn_new", on_click=reset_research)

            if run_fu and followup.strip():
                api_key = os.getenv("OPENAI_API_KEY", "")
                if api_key and (ROOT / "data" / "embeddings" / "vectors.npy").exists():
                    with st.spinner("Retrieving evidence…"):
                        try:
                            from openai import OpenAI
                            from answer_questions import answer_question
                            from search_embeddings import retrieve
                            client = OpenAI(api_key=api_key)
                            query_filters = {}
                            if selected_company != "All Issuers": query_filters["company"] = selected_company
                            if selected_asset != "All Asset Classes": query_filters["asset_type"] = selected_asset
                            if selected_year != "All Years": query_filters["year"] = selected_year
                            chunks = retrieve(followup, top_k=5, client=client, filters=query_filters)
                            answer = answer_question(followup, top_k=5, model="gpt-6-luna", client=client, retrieved=chunks)
                            st.session_state["last_answer"] = answer
                            st.session_state["last_chunks"] = chunks
                            st.session_state["last_q"] = followup
                            st.session_state["qa_history"].append({"q": followup, "a": answer, "ts": datetime.now().strftime("%H:%M")})
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Error: {exc}")

        with col_src:
            chunks = st.session_state["last_chunks"]
            with st.expander(f"Source evidence ? {len(chunks)} passages", expanded=True):
                render_source_cards(chunks)

# PAGE 3 — Keyword Search
# ════════════════════════════════════════════════════════════════════════════
elif page == "Keyword Search":
    st.markdown("""
    <div class="page-hdr">
      <div class="page-hdr-title">Keyword Search</div>
      <div class="page-hdr-sub">Full-text search across all indexed filings with optional regex and metadata filters</div>
    </div>
    """, unsafe_allow_html=True)

    col_q, col_rx = st.columns([7, 1])
    with col_q:
        query = st.text_input("query", label_visibility="collapsed",
                              placeholder="e.g.  reserve account   |   physical custody   |   weighted average life")
    with col_rx:
        use_regex = st.checkbox("Regex", value=False)

    col_btn, col_hint = st.columns([1, 5])
    with col_btn:
        run_search = st.button("Search", type="primary", width="stretch")
    with col_hint:
        st.caption("Sidebar filters apply automatically. Leave query blank to filter by metadata only.")

    if run_search:
        no_filter = (not query and selected_company == "All Issuers"
                     and selected_asset == "All Asset Classes" and selected_year == "All Years")
        if no_filter:
            st.warning("Enter a search query or select at least one filter.")
        else:
            with st.spinner("Searching across filings…"):
                try:
                    results = search_filings(
                        query or None, index=index, clean_dir=DEFAULT_CLEAN_DIR,
                        use_regex=use_regex,
                        company=None if selected_company == "All Issuers" else selected_company,
                        asset_type=None if selected_asset == "All Asset Classes" else selected_asset,
                        year=None if selected_year == "All Years" else int(selected_year),
                        max_results=20,
                    )
                except Exception as exc:
                    st.error(f"Search error: {exc}"); results = []

            if not results:
                st.markdown("""
                <div class="empty-state">
                  <div class="empty-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="1.7" stroke-linecap="round"><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/></svg></div>
                  <div class="empty-title">No filings matched</div>
                  <div class="empty-sub">Try broadening your query or adjusting the sidebar filters.</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:.75rem;color:#64748B;margin-bottom:.85rem;"><b style="color:#172B45;">{len(results)}</b> filing(s) matched</div>', unsafe_allow_html=True)
                for r in results:
                    deal  = escape(str(r["deal_name"] or r["company"]))
                    atype = r["asset_type"]
                    bcls  = BADGE.get(atype, "b-def")
                    albl  = escape(ASSET_LABELS.get(atype, atype))
                    filing_key = Path(str(r.get("filename", ""))).stem.removesuffix("_clean")
                    original_url = filing_urls.get(filing_key, "")
                    original_link = f'<a class="source-link" href="{escape(original_url, quote=True)}" target="_blank" rel="noopener">Open original SEC filing</a>' if original_url else ""
                    hits_html = ""
                    for i, hit in enumerate(r["hits"], 1):
                        snippet = escape(hit["snippet"]).replace("&lt;&lt;", "<b>").replace("&gt;&gt;", "</b>")
                        citation = escape(str(hit["citation"]))
                        hits_html += f'<div class="hit"><div class="hit-lbl">Match {i} · {citation}</div>{snippet}</div>'
                    st.markdown(f"""
                    <div class="rc">
                      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:.2rem;">
                        <div class="rc-title">{deal}</div>
                        <span class="rc-badge {bcls}">{albl}</span>
                      </div>
                      <div class="rc-meta">
                        <span>{escape(str(r['company']))}</span><span>{escape(str(r['filing_date']))}</span><span>{r['match_count']} match(es)</span>
                      </div>
                      {hits_html}
                      {original_link}
                    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Document Explorer
# ════════════════════════════════════════════════════════════════════════════
elif page == "Document Explorer":
    st.markdown("""
    <div class="page-hdr">
      <div class="page-hdr-title">Document Explorer</div>
      <div class="page-hdr-sub">Browse, filter, sort, and export the full ABS filing index</div>
    </div>
    """, unsafe_allow_html=True)

    filtered = index.copy()
    if selected_company != "All Issuers":       filtered = filtered[filtered["company"] == selected_company]
    if selected_asset   != "All Asset Classes": filtered = filtered[filtered["asset_type"] == selected_asset]
    if selected_year    != "All Years":         filtered = filtered[filtered["filing_date"].str.startswith(selected_year)]

    col_info, col_dl = st.columns([5, 1])
    with col_info:
        st.markdown(f"""
        <div class="browse-toolbar">
          <span class="browse-ct">
            Showing <b>{len(filtered)}</b> of <b>{len(index)}</b> filings
            &nbsp;&middot;&nbsp; <b>{filtered['company'].nunique()}</b> issuers
            &nbsp;&middot;&nbsp; <b>{filtered['asset_type'].nunique()}</b> asset classes
          </span>
        </div>""", unsafe_allow_html=True)
    with col_dl:
        csv = filtered.to_csv(index=False).encode()
        st.download_button("Export CSV", csv, "filings.csv", "text/csv", width="stretch")

    display_cols = ["company","deal_name","asset_type","filing_date",
                    "aggregate_principal_amount","wa_apr","wa_fico","credit_enhancement_types"]
    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        width="stretch", height=560,
        column_config={
            "company":                    st.column_config.TextColumn("Issuer",             width="medium"),
            "deal_name":                  st.column_config.TextColumn("Deal Name",          width="large"),
            "asset_type":                 st.column_config.TextColumn("Asset Class",        width="medium"),
            "filing_date":                st.column_config.TextColumn("Filed",              width="small"),
            "aggregate_principal_amount": st.column_config.TextColumn("Principal",          width="medium"),
            "wa_apr":                     st.column_config.TextColumn("WA APR",             width="small"),
            "wa_fico":                    st.column_config.TextColumn("WA FICO",            width="small"),
            "credit_enhancement_types":   st.column_config.TextColumn("Credit Enhancement", width="large"),
        },
    )

    if len(filtered) > 0:
        st.markdown("<div style='height:.9rem'></div>", unsafe_allow_html=True)
        with st.expander("Document Preview", expanded=False):
            preview_options = filtered["filename"].tolist()
            preview_labels = {
                filename: (deal_name.strip() or company)
                for filename, deal_name, company in zip(filtered["filename"], filtered["deal_name"], filtered["company"])
            }
            selected_doc = st.selectbox("Select filing to preview", preview_options, format_func=lambda filename: preview_labels.get(filename, filename), key="doc_preview_sel")
            row = filtered[filtered["filename"] == selected_doc].iloc[0]
            clean_filename = Path(str(row["filename"])).name
            if not clean_filename.endswith("_clean.txt"):
                clean_filename = f"{Path(clean_filename).stem}_clean.txt"
            clean_path = DEFAULT_CLEAN_DIR / clean_filename
            filing_key = Path(clean_filename).stem.removesuffix("_clean")
            if filing_urls.get(filing_key):
                st.markdown(f"[Open original SEC filing]({filing_urls[filing_key]})")
            if clean_path.exists():
                text = clean_path.read_text(encoding="utf-8", errors="replace")
                st.text_area("Filing text (first 3000 chars)", text[:3000], height=320, label_visibility="visible")
            else:
                st.info("Clean text not available for this filing.")
