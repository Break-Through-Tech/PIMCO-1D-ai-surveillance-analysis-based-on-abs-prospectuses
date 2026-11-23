"""Design system CSS for PIMCO ABS Intelligence Platform."""

DESIGN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
#MainMenu, footer { visibility: hidden; }
/* Keep Streamlit's built-in sidebar toggle available in both expanded states. */
header[data-testid="stHeader"] {
  visibility:visible !important; background:transparent !important;
}
header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarExpandButton"],
[data-testid="collapsedControl"] {
  visibility:visible !important; opacity:1 !important; color:#64748B !important;
}
header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarExpandButton"] {
  width:34px !important; height:34px !important; border-radius:8px !important;
}
header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"]:hover,
button[data-testid="stSidebarExpandButton"]:hover { background:#EDF2F8 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.stApp { background: #F8FAFC; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: #101E30 !important;
  border-right: 1px solid #1C2E45 !important;
  min-width: 240px !important; max-width: 240px !important;
}
section[data-testid="stSidebar"] .block-container { padding: 0 !important; }
section[data-testid="stSidebar"] * { color: #C8D8E8 !important; }
section[data-testid="stSidebar"] label {
  font-size: 0.63rem !important; font-weight: 700 !important;
  text-transform: uppercase !important; letter-spacing: 1.1px !important;
  color: #7A9AB8 !important;
}
section[data-testid="stSidebar"] .stRadio > div { gap: 0 !important; }
section[data-testid="stSidebar"] .stRadio label {
  color: #A8C0D4 !important; font-size: 0.82rem !important;
  font-weight: 400 !important; text-transform: none !important;
  letter-spacing: 0 !important; padding: 0.62rem 1.1rem !important;
  border-radius: 0 !important; cursor: pointer !important;
  transition: background 0.15s !important; display: block !important;
  width: 100% !important; border-left: 2px solid transparent !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
  background: #1C2E45 !important; color: #E0EDF8 !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: #162438 !important; border: 1px solid #2A4060 !important;
  border-radius: 7px !important; color: #E8F2FA !important;
  font-size: 0.81rem !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] div,
section[data-testid="stSidebar"] [data-baseweb="select"] p {
  color: #E8F2FA !important;
}
section[data-testid="stSidebar"] .stButton > button {
  background: transparent !important; color: #7A9AB8 !important;
  border: 1px solid #2A4060 !important; border-radius: 6px !important;
  font-size: 0.72rem !important; width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: #1C2E45 !important; color: #C8D8E8 !important;
}

/* ── Topbar ── */
.topbar {
  display: flex; align-items: center; padding: 0 2rem;
  height: 52px; background: #101E30;
  border-bottom: 1px solid #1C2E45;
  position: sticky; top: 0; z-index: 999;
}
.tb-logo {
  width: 26px; height: 26px;
  background: linear-gradient(135deg, #234B7C, #3B82F6);
  border-radius: 6px; display: flex; align-items: center;
  justify-content: center; font-size: 0.72rem; font-weight: 800;
  color: #fff; margin-right: 0.7rem; flex-shrink: 0;
}
.tb-wordmark { font-size: 0.85rem; font-weight: 700; color: #E0EDF8; }
.tb-divider-v { width: 1px; height: 14px; background: #1C2E45; margin: 0 0.7rem; }
.tb-subtitle { font-size: 0.68rem; color: #4A6A8A; }

/* ── Page wrapper ── */
.page { padding: 0 2rem 3rem; max-width: 1480px; margin: 0 auto; }
.page-hdr { margin-bottom: 1.6rem; padding: 1.6rem 0 1.2rem; border-bottom: 1px solid #E2E8F0; }
.page-hdr-title { font-size: 1.15rem; font-weight: 700; color: #172B45; letter-spacing: -0.3px; }
.page-hdr-sub { font-size: 0.76rem; color: #64748B; margin-top: 0.25rem; }

/* ── KPI cards ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; margin-bottom: 1.5rem; }
.kpi-card {
  background: #fff; border: 1px solid #E2E8F0; border-radius: 10px;
  padding: 1.1rem 1.3rem 1rem; box-shadow: 0 1px 3px rgba(23,43,69,.05);
  transition: box-shadow .2s, transform .2s; position: relative; overflow: hidden;
}
.kpi-card::before {
  content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:10px 10px 0 0;
}
.kpi-card.kc-blue::before  { background: linear-gradient(90deg,#234B7C,#3B82F6); }
.kpi-card.kc-teal::before  { background: linear-gradient(90deg,#0D9488,#14B8A6); }
.kpi-card.kc-amber::before { background: linear-gradient(90deg,#D97706,#F59E0B); }
.kpi-card.kc-violet::before{ background: linear-gradient(90deg,#7C3AED,#A78BFA); }
.kpi-card:hover { box-shadow: 0 5px 18px rgba(23,43,69,.09); transform: translateY(-1px); }
.kpi-card-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:.7rem; }
.kpi-card-label { font-size:.63rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:1px; }
.kpi-card-icon { width:28px; height:28px; border-radius:7px; display:flex; align-items:center; justify-content:center; font-size:.85rem; font-weight:700; }
.icon-blue   { background:#DBEAFE; color:#234B7C; }
.icon-teal   { background:#CCFBF1; color:#0D9488; }
.icon-amber  { background:#FEF3C7; color:#D97706; }
.icon-violet { background:#EDE9FE; color:#7C3AED; }
.kpi-card-value { font-size:1.65rem; font-weight:800; color:#172B45; letter-spacing:-.7px; line-height:1; }
.kpi-card-sub { font-size:.72rem; color:#64748B; margin-top:.35rem; }

/* ── Chart card ── */
.chart-card {
  background:#fff; border:1px solid #E2E8F0; border-radius:10px;
  padding:1.2rem 1.35rem .5rem; box-shadow:0 1px 3px rgba(23,43,69,.05);
}
.chart-card-title { font-size:.7rem; font-weight:700; color:#172B45; text-transform:uppercase; letter-spacing:.9px; }
.chart-card-sub { font-size:.68rem; color:#94A3B8; margin-top:.12rem; margin-bottom:.5rem; }

/* ── Inputs ── */
.stTextInput > div > div > input {
  background:#fff !important; border:1.5px solid #D1DAE8 !important;
  border-radius:8px !important; color:#172B45 !important;
  font-size:.86rem !important; padding:.56rem .9rem !important;
  font-family:'Inter',sans-serif !important;
  transition:border-color .15s,box-shadow .15s !important;
}
.stTextInput > div > div > input:focus {
  border-color:#234B7C !important; box-shadow:0 0 0 3px rgba(35,75,124,.1) !important; outline:none !important;
}
.stTextInput > div > div > input::placeholder { color:#94A3B8 !important; }
.stTextArea textarea {
  background:#fff !important; border:1.5px solid #D1DAE8 !important;
  border-radius:8px !important; color:#172B45 !important;
  font-size:.86rem !important; line-height:1.65 !important;
  font-family:'Inter',sans-serif !important;
  transition:border-color .15s,box-shadow .15s !important;
}
.stTextArea textarea:focus {
  border-color:#234B7C !important; box-shadow:0 0 0 3px rgba(35,75,124,.1) !important; outline:none !important;
}
.stTextArea textarea::placeholder { color:#94A3B8 !important; }

/* ── Buttons ── */
.stButton > button {
  background:#234B7C !important; color:#fff !important; border:none !important;
  border-radius:8px !important; font-weight:600 !important; font-size:.82rem !important;
  padding:.52rem 1.2rem !important; letter-spacing:.1px !important;
  box-shadow:0 1px 3px rgba(35,75,124,.25) !important;
  transition:background .15s,box-shadow .15s,transform .1s !important;
  font-family:'Inter',sans-serif !important;
}
.stButton > button:hover {
  background:#1A3A62 !important; box-shadow:0 4px 12px rgba(35,75,124,.3) !important;
  transform:translateY(-1px) !important;
}
.stButton > button:active { transform:translateY(0) !important; }
.stDownloadButton > button {
  background:#fff !important; color:#234B7C !important;
  border:1.5px solid #BFDBFE !important; border-radius:8px !important;
  font-weight:600 !important; font-size:.79rem !important;
  padding:.46rem .9rem !important; box-shadow:none !important;
}
.stDownloadButton > button:hover { background:#EDF2F8 !important; border-color:#234B7C !important; }

/* ── Search result cards ── */
.rc {
  background:#fff; border:1px solid #E2E8F0; border-left:3px solid #234B7C;
  border-radius:8px; padding:.95rem 1.25rem; margin-bottom:.65rem; transition:box-shadow .15s;
}
.rc:hover { box-shadow:0 3px 12px rgba(23,43,69,.08); }
.rc-title { font-size:.86rem; font-weight:600; color:#172B45; line-height:1.35; }
.rc-meta { font-size:.7rem; color:#64748B; display:flex; flex-wrap:wrap; gap:.65rem; margin:.28rem 0 .6rem; }
.rc-badge { font-size:.58rem; font-weight:700; padding:.13rem .48rem; border-radius:4px; text-transform:uppercase; letter-spacing:.5px; white-space:nowrap; }
.b-auto  { background:#DBEAFE; color:#1E40AF; }
.b-sub   { background:#FCE7F3; color:#9D174D; }
.b-cmbs  { background:#FEF3C7; color:#92400E; }
.b-dev   { background:#D1FAE5; color:#065F46; }
.b-cc    { background:#EDE9FE; color:#4C1D95; }
.b-lease { background:#E0F2FE; color:#0C4A6E; }
.b-moto  { background:#FEF9C3; color:#713F12; }
.b-def   { background:#F1F5F9; color:#475569; }
.hit {
  background:#F8FAFC; border-left:2px solid #93C5FD;
  border-radius:0 5px 5px 0; padding:.52rem .85rem; margin-top:.38rem;
  font-size:.75rem; color:#334155; line-height:1.7;
}
.hit-lbl { font-size:.61rem; font-weight:700; color:#234B7C; text-transform:uppercase; letter-spacing:.5px; margin-bottom:.18rem; }
.hit b { background:#FEF08A; color:#172B45; padding:0 2px; border-radius:2px; font-weight:600; }

/* ── Browse toolbar ── */
.browse-toolbar {
  display:flex; align-items:center; justify-content:space-between;
  padding:.7rem 1rem; background:#fff; border:1px solid #E2E8F0;
  border-radius:8px; margin-bottom:.85rem;
}
.browse-ct { font-size:.75rem; color:#64748B; }
.browse-ct b { color:#172B45; font-weight:600; }

/* ── Sidebar brand ── */
.sb-brand { padding:1.1rem 1.1rem .9rem; border-bottom:1px solid #1C2E45; }
.sb-brand-name { font-size:.82rem; font-weight:700; color:#E0EDF8; }
.sb-brand-sub { font-size:.6rem; color:#4A6A8A; margin-top:2px; }
.sb-section-label { font-size:.56rem; font-weight:700; color:#4A6A8A; text-transform:uppercase; letter-spacing:1.3px; padding:.9rem 1.1rem .3rem; }
.sb-divider { height:1px; background:#1C2E45; margin:.45rem 1.1rem; }
.sb-filter-tag { display:inline-block; background:#1C2E45; color:#6AAAD8; font-size:.61rem; font-weight:600; padding:.13rem .42rem; border-radius:4px; margin:.1rem; border:1px solid #2A4060; }

/* ── Empty states ── */
.empty-state { text-align:center; padding:3.5rem 2rem; }
.empty-icon { font-size:1.8rem; margin-bottom:.7rem; opacity:.35; }
.empty-title { font-size:.9rem; font-weight:600; color:#475569; }
.empty-sub { font-size:.76rem; color:#94A3B8; margin-top:.3rem; line-height:1.55; }

/* ── Misc ── */
.stAlert { border-radius:8px !important; font-size:.82rem !important; }
.stCheckbox label { color:#475569 !important; font-size:.82rem !important; }
.stSpinner > div { border-top-color:#234B7C !important; }
.stDataFrame { border-radius:8px !important; border:1px solid #E2E8F0 !important; }

/* ════════════════════════════════════════════════
   AI RESEARCH ASSISTANT
   ════════════════════════════════════════════════ */

/* Hero */
.ai-hero {
  display:flex; flex-direction:column; align-items:center;
  text-align:center; padding:3rem 2rem 1.5rem;
  max-width:1000px; margin:0 auto;
}
.ai-hero-icon-wrap {
  width:60px; height:60px; border-radius:16px;
  background:linear-gradient(135deg,#EDF2F8 0%,#DBEAFE 100%);
  border:1px solid #BFDBFE;
  display:flex; align-items:center; justify-content:center;
  margin-bottom:1.4rem;
  box-shadow:0 2px 12px rgba(35,75,124,.1);
}
.ai-hero-icon-wrap svg { display:block; width:28px !important; height:28px !important; max-width:28px !important; max-height:28px !important; flex:0 0 28px; }
.ai-hero-title {
  font-size:2.1rem; font-weight:700; color:#172B45;
  letter-spacing:-.6px; line-height:1.15; margin-bottom:.6rem;
}
.ai-hero-sub {
  font-size:.95rem; color:#64748B; font-weight:400;
  line-height:1.65; max-width:480px; margin-bottom:1.8rem;
}

/* Input box */
.ai-input-box {
  width:100%; max-width:680px;
  background:#fff;
  border:1.5px solid #E2E8F0;
  border-radius:16px;
  box-shadow:0 4px 24px rgba(23,43,69,.07);
  overflow:hidden;
  transition:border-color .2s, box-shadow .2s;
  margin-bottom:2.5rem;
}
.ai-input-box:focus-within {
  border-color:#234B7C;
  box-shadow:0 4px 28px rgba(35,75,124,.13);
}
.ai-input-textarea {
  width:100%; border:none; outline:none; resize:none;
  padding:1rem 1.2rem .5rem;
  font-size:.92rem; color:#172B45; line-height:1.6;
  font-family:'Inter',sans-serif; background:transparent;
  min-height:80px;
}
.ai-input-textarea::placeholder { color:#94A3B8; }
.ai-input-footer {
  display:flex; align-items:center; justify-content:space-between;
  padding:.6rem 1rem .7rem 1.2rem;
  border-top:1px solid #F1F5F9;
}
.ai-scope-pill {
  display:inline-flex; align-items:center; gap:.4rem;
  font-size:.7rem; color:#64748B;
}
.ai-scope-dot { width:6px; height:6px; border-radius:50%; background:#22C55E; flex-shrink:0; }
.ai-ask-btn {
  display:inline-flex; align-items:center; gap:.4rem;
  background:#172B45; color:#fff; border:none; border-radius:8px;
  padding:.42rem .9rem; font-size:.78rem; font-weight:600;
  cursor:pointer; transition:background .15s, transform .1s;
  font-family:'Inter',sans-serif; letter-spacing:.1px;
}
.ai-ask-btn:hover { background:#234B7C; transform:translateY(-1px); }
.ai-ask-btn svg { width:14px; height:14px; }

/* Category grid */
.ai-cat-grid {
  display:grid; grid-template-columns:1fr 1fr;
  gap:.85rem; width:100%; max-width:780px;
}
.ai-cat-card {
  background:#fff; border:1px solid #E2E8F0; border-radius:12px;
  padding:1.1rem 1.2rem; cursor:pointer;
  transition:border-color .15s, box-shadow .15s, transform .15s;
  display:flex; align-items:center; justify-content:space-between;
  gap:.8rem;
}
.ai-cat-card:hover {
  border-color:#93C5FD; box-shadow:0 4px 16px rgba(35,75,124,.09);
  transform:translateY(-1px);
}
.ai-cat-card.open { border-color:#234B7C; background:#F8FBFF; }
.ai-cat-left { display:flex; align-items:center; gap:.85rem; }
.ai-cat-icon {
  width:38px; height:38px; border-radius:10px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center;
}
.ai-cat-icon.ic-legal  { background:#EDF2F8; }
.ai-cat-icon.ic-coll   { background:#ECFDF5; }
.ai-cat-icon.ic-credit { background:#FFFBEB; }
.ai-cat-icon.ic-serv   { background:#F5F3FF; }
.ai-cat-icon svg { width:18px; height:18px; }
.ai-cat-title { font-size:.84rem; font-weight:600; color:#172B45; line-height:1.2; }
.ai-cat-sub { font-size:.71rem; color:#64748B; margin-top:.15rem; line-height:1.35; }
.ai-cat-chevron { color:#CBD5E1; flex-shrink:0; transition:transform .2s; }
.ai-cat-card.open .ai-cat-chevron { transform:rotate(90deg); color:#234B7C; }

/* Expanded question rows */
.ai-q-rows { margin-top:.5rem; display:flex; flex-direction:column; gap:.3rem; }
.ai-q-row {
  padding:.6rem .85rem; border-radius:8px;
  font-size:.79rem; color:#334155; line-height:1.5;
  cursor:pointer; transition:background .12s, color .12s;
  border:1px solid transparent;
  text-align:left; background:transparent;
}
.ai-q-row:hover { background:#EDF2F8; color:#172B45; border-color:#BFDBFE; }

/* Workspace */
.ai-workspace-wrap { max-width:1000px; margin:0 auto; padding:0 2rem; }

/* Question bubble */
.ai-q-bubble {
  background:#EDF2F8; border:1px solid #BFDBFE;
  border-radius:12px 12px 4px 12px;
  padding:.85rem 1.1rem; margin-bottom:1.2rem;
  font-size:.88rem; color:#172B45; line-height:1.6; font-weight:500;
  max-width:85%;
}

/* Answer card */
.ai-answer-card {
  background:#fff; border:1px solid #E2E8F0; border-radius:12px;
  box-shadow:0 2px 12px rgba(23,43,69,.06); overflow:hidden;
  margin-bottom:1rem;
}
.ai-answer-card-hdr {
  display:flex; align-items:center; gap:.6rem;
  padding:.8rem 1.2rem; border-bottom:1px solid #F1F5F9;
  background:#FAFBFD;
}
.ai-answer-badge {
  width:22px; height:22px; border-radius:6px;
  background:linear-gradient(135deg,#234B7C,#3B82F6);
  display:flex; align-items:center; justify-content:center;
  font-size:.58rem; font-weight:800; color:#fff; flex-shrink:0;
}
.ai-answer-card-title { font-size:.7rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:.9px; flex:1; }
.ai-answer-body {
  padding:1.2rem 1.3rem; font-size:.875rem; color:#1E293B;
  line-height:1.9; white-space:pre-wrap; max-width:72ch;
}
.ai-answer-footer {
  display:flex; align-items:center; gap:.5rem;
  padding:.7rem 1.2rem; border-top:1px solid #F1F5F9;
  background:#FAFBFD;
}
.ai-footer-chip {
  font-size:.69rem; color:#64748B; background:#F1F5F9;
  border:1px solid #E2E8F0; border-radius:6px;
  padding:.22rem .6rem; cursor:default;
}

/* Source cards */
.ai-src-card {
  background:#fff; border:1px solid #E2E8F0; border-radius:10px;
  padding:.85rem 1rem; margin-bottom:.6rem;
  box-shadow:0 1px 4px rgba(23,43,69,.04);
  transition:box-shadow .15s;
}
.ai-src-card:hover { box-shadow:0 3px 12px rgba(23,43,69,.08); }
.ai-src-header { display:flex; align-items:center; gap:.5rem; margin-bottom:.35rem; }
.ai-src-num {
  width:20px; height:20px; border-radius:5px;
  background:#234B7C; color:#fff;
  font-size:.62rem; font-weight:700;
  display:flex; align-items:center; justify-content:center; flex-shrink:0;
}
.ai-src-issuer { font-size:.75rem; font-weight:600; color:#172B45; line-height:1.2; }
.ai-src-filing { font-size:.68rem; color:#64748B; margin-bottom:.3rem; }
.ai-src-chips { display:flex; flex-wrap:wrap; gap:.28rem; margin-bottom:.38rem; }
.ai-src-chip { font-size:.61rem; color:#64748B; background:#F1F5F9; border-radius:4px; padding:.1rem .38rem; }
.ai-src-excerpt {
  font-size:.71rem; color:#475569; line-height:1.55;
  border-left:2px solid #BFDBFE; padding-left:.55rem;
  display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;
}
.ai-src-sim { display:inline-block; background:#F0FDF4; color:#15803D; font-size:.6rem; font-weight:700; padding:.1rem .38rem; border-radius:3px; margin-top:.3rem; }

/* History rail */
.ai-hist-card {
  background:#fff; border:1px solid #E2E8F0; border-radius:8px;
  padding:.65rem .85rem; margin-bottom:.45rem; cursor:pointer;
  transition:border-color .12s, background .12s;
}
.ai-hist-card:hover { border-color:#93C5FD; background:#F8FBFF; }
.ai-hist-card.active { border-color:#234B7C; background:#EDF2F8; }
.ai-hist-q { font-size:.74rem; color:#334155; line-height:1.4; font-weight:500; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.ai-hist-time { font-size:.61rem; color:#94A3B8; margin-top:.18rem; }

/* Progress */
.ai-progress-wrap { max-width:680px; margin:0 auto; padding:1.5rem 2rem; }
.ai-prog-step { display:flex; align-items:center; gap:.7rem; padding:.45rem 0; font-size:.8rem; color:#94A3B8; }
.ai-prog-step.done   { color:#15803D; }
.ai-prog-step.active { color:#234B7C; font-weight:500; }
.ai-prog-icon { width:20px; height:20px; border-radius:50%; border:2px solid #E2E8F0; display:flex; align-items:center; justify-content:center; font-size:.58rem; flex-shrink:0; }
.ai-prog-step.done   .ai-prog-icon { border-color:#22C55E; background:#F0FDF4; color:#15803D; }
.ai-prog-step.active .ai-prog-icon { border-color:#234B7C; background:#EDF2F8; color:#234B7C; }

/* Follow-up bar */
.ai-followup-bar {
  background:#fff; border:1px solid #E2E8F0; border-radius:12px;
  box-shadow:0 2px 12px rgba(23,43,69,.06);
  overflow:hidden; margin-top:.5rem;
}

/* ── Refined Streamlit layout and keyed component wrappers ── */
:root { color-scheme:light; }
html, body, [class*="css"] { font-family:'Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif !important; }
.stApp, [data-testid="stAppViewContainer"] { background:#F8FAFC !important; }
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div { background:#0F1D2F !important; }
main[data-testid="stMain"] > div[data-testid="stMainBlockContainer"],
section.main > div.block-container {
  width:100% !important; max-width:1300px !important;
  padding:24px 32px 64px !important; margin:0 auto !important;
}
section[data-testid="stSidebar"] { width:264px !important; min-width:264px !important; }
section[data-testid="stSidebar"] > div { padding:0 14px 24px !important; }
section[data-testid="stSidebar"] .block-container { padding:14px 8px 24px !important; }
.sb-brand { padding:13px 10px 20px; margin-bottom:10px; border-bottom:1px solid #26384D; }
.sb-brand { display:flex; align-items:center; gap:10px; }
.brand-mark { width:30px; height:30px; display:grid; place-items:center; flex:0 0 30px; border-radius:8px; background:#244B78; color:#fff !important; font-size:15px; font-weight:700; }
.sb-brand-name { color:#F2F6FA !important; font-size:14px; font-weight:650; letter-spacing:-.1px; }
.sb-brand-sub { color:#91A4B8 !important; font-size:11px; margin-top:5px; }
.sb-section-label { padding:13px 10px 7px; color:#91A4B8 !important; font-size:10px; letter-spacing:1.1px; }
.sb-divider { margin:18px 10px 2px; background:#26384D; }
section[data-testid="stSidebar"] .stSelectbox { padding:0 5px; margin:0 0 8px; }
section[data-testid="stSidebar"] .stSelectbox label { color:#B5C2D0 !important; font-size:11px !important; letter-spacing:.15px !important; text-transform:none !important; margin-bottom:5px !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] > div { min-height:40px; background:#17283D !important; border-color:#34485F !important; border-radius:8px !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] div,
section[data-testid="stSidebar"] [data-baseweb="select"] p { color:#F1F5F9 !important; }
ul[data-baseweb="menu"] { background:#fff !important; }
ul[data-baseweb="menu"] *, [role="listbox"] * { color:#172B45 !important; }

/* Navigation icons are rendered inside the native Streamlit button. */
section[data-testid="stSidebar"] .st-key-nav_overview,
section[data-testid="stSidebar"] .st-key-nav_research,
section[data-testid="stSidebar"] .st-key-nav_search,
section[data-testid="stSidebar"] .st-key-nav_documents { position:relative; margin:2px 0; }
section[data-testid="stSidebar"] .st-key-nav_overview button,
section[data-testid="stSidebar"] .st-key-nav_research button,
section[data-testid="stSidebar"] .st-key-nav_search button,
section[data-testid="stSidebar"] .st-key-nav_documents button {
  width:100%; min-height:40px; justify-content:flex-start; gap:10px; padding:0 10px !important;
  color:#C5D0DC !important; background:transparent !important; border:1px solid transparent !important;
  border-radius:8px !important; box-shadow:none !important; font-size:12px !important; font-weight:500 !important;
}
section[data-testid="stSidebar"] .st-key-nav_overview button[kind="primary"],
section[data-testid="stSidebar"] .st-key-nav_research button[kind="primary"],
section[data-testid="stSidebar"] .st-key-nav_search button[kind="primary"],
section[data-testid="stSidebar"] .st-key-nav_documents button[kind="primary"] { background:#20344D !important; color:#fff !important; border-color:#2B4360 !important; }
section[data-testid="stSidebar"] .st-key-nav_overview button:hover,
section[data-testid="stSidebar"] .st-key-nav_research button:hover,
section[data-testid="stSidebar"] .st-key-nav_search button:hover,
section[data-testid="stSidebar"] .st-key-nav_documents button:hover { background:#1B2D43 !important; color:#fff !important; transform:none !important; }
section[data-testid="stSidebar"] .st-key-nav_overview button svg,
section[data-testid="stSidebar"] .st-key-nav_research button svg,
section[data-testid="stSidebar"] .st-key-nav_search button svg,
section[data-testid="stSidebar"] .st-key-nav_documents button svg { width:16px !important; height:16px !important; }
/* Streamlit Material icons are font glyphs, not SVGs. Size the actual DOM node. */
section[data-testid="stSidebar"] [data-testid="stIconMaterial"] {
  display:inline-flex !important; align-items:center; justify-content:center;
  width:14px !important; min-width:14px !important; height:14px !important;
  overflow:hidden; font-size:14px !important; line-height:14px !important;
}
section[data-testid="stSidebar"] .st-key-nav_overview button > div,
section[data-testid="stSidebar"] .st-key-nav_research button > div,
section[data-testid="stSidebar"] .st-key-nav_search button > div,
section[data-testid="stSidebar"] .st-key-nav_documents button > div { width:100%; }

/* Assistant hero and input are centered in the same ~1000px content rail. */
.ai-hero { padding:26px 24px 13px; max-width:1000px; }
.ai-hero-icon-wrap { width:54px; height:54px; border-radius:15px; background:#EDF2F8; border:1px solid #DCE5EF; box-shadow:0 2px 8px rgba(23,43,69,.06); margin-bottom:17px; }
.ai-hero-title { font-size:36px; font-weight:650; letter-spacing:-1.1px; color:#172B45; margin-bottom:8px; }
.ai-hero-sub { font-size:14px; color:#64748B; max-width:none; margin-bottom:20px; }
.st-key-ai_prompt_card {
  width:100%; max-width:1000px; margin:0 auto 34px; padding:14px 18px 15px;
  border:1px solid #E2E8F0; border-radius:16px; background:#fff;
  box-shadow:0 5px 22px rgba(23,43,69,.055);
}
.st-key-ai_prompt_card > div[data-testid="stVerticalBlock"] { gap:7px; }
.st-key-ai_prompt_card .prompt-label { padding:0 1px 2px; color:#64748B; font-size:12px; font-weight:550; }
.st-key-ai_prompt_card textarea {
  min-height:88px; background:#fff !important; border:0 !important; border-radius:8px !important;
  box-shadow:none !important; color:#172B45 !important; padding:8px 2px !important;
  font-size:14px !important; line-height:1.65 !important; resize:vertical;
}
.st-key-ai_prompt_card [data-testid="stTextAreaRootElement"] { border:0 !important; border-radius:8px !important; background:transparent !important; box-shadow:none !important; }
.st-key-ai_prompt_card [data-testid="stTextArea"] { border:0 !important; background:transparent !important; }
.st-key-ai_prompt_card [data-testid="stTextAreaRootElement"]:focus-within { border:0 !important; box-shadow:none !important; }
.st-key-ai_prompt_card textarea::placeholder { color:#94A3B8 !important; }
.st-key-ai_prompt_card [data-testid="stForm"] { border:0 !important; padding:0 !important; background:transparent !important; }
.st-key-ai_prompt_card [data-testid="stForm"] > div { gap:6px !important; }
.st-key-ai_prompt_card [data-testid="stForm"] [data-testid="stHorizontalBlock"] { border-top:1px solid #F1F5F9; margin-top:5px; padding-top:10px; }
.st-key-ai_prompt_card [data-testid="stForm"] [data-testid="column"] { display:flex; align-items:center; }
.st-key-ai_prompt_card [data-testid="stForm"] [data-testid="column"]:last-child { justify-content:flex-end; }
.st-key-ai_prompt_card [data-testid="stForm"] [data-testid="column"]:last-child [data-testid="stFormSubmitButton"] { width:auto !important; margin-left:auto; }
.ai-scope-pill { display:flex; align-items:center; gap:7px; min-height:36px; color:#64748B; font-size:11px; }
.ai-scope-pill b { color:#475569; font-weight:550; }
.ai-scope-dot { background:#527A69; width:7px; height:7px; }
.st-key-ai_prompt_card button[kind="primaryFormSubmit"] {
  min-height:37px; padding:0 13px !important; white-space:nowrap;
  color:#fff !important; background:#234B7C !important; border:0 !important;
  border-radius:8px !important; box-shadow:none !important; font-size:12px !important; font-weight:600 !important;
}
.st-key-ai_prompt_card button[kind="primaryFormSubmit"]:hover { background:#1B3D66 !important; transform:translateY(-1px) !important; }
.suggestions-heading { display:flex; flex-direction:column; align-items:center; gap:4px; margin:0 auto 15px; text-align:center; }
.suggestions-heading span:first-child { color:#172B45; font-size:15px; font-weight:650; }
.suggestions-heading span:last-child { color:#64748B; font-size:12px; }
.st-key-cat_card_0, .st-key-cat_card_1, .st-key-cat_card_2, .st-key-cat_card_3 {
  position:relative; min-height:100%; padding:18px 19px 14px; border:1px solid #E2E8F0; border-radius:12px;
  background:#fff; box-shadow:0 1px 2px rgba(23,43,69,.025); transition:border-color .16s,box-shadow .16s,transform .16s;
}
.st-key-cat_card_0:hover, .st-key-cat_card_1:hover, .st-key-cat_card_2:hover, .st-key-cat_card_3:hover { border-color:#C8D5E3; box-shadow:0 5px 16px rgba(23,43,69,.055); transform:translateY(-1px); }
.st-key-cat_card_0 > div[data-testid="stVerticalBlock"], .st-key-cat_card_1 > div[data-testid="stVerticalBlock"],
.st-key-cat_card_2 > div[data-testid="stVerticalBlock"], .st-key-cat_card_3 > div[data-testid="stVerticalBlock"] { gap:7px; }
.category-heading { display:flex; align-items:center; gap:12px; min-height:49px; }
.category-icon { width:38px; height:38px; flex:0 0 38px; display:grid; place-items:center; border-radius:10px; background:#EDF2F8; }
.category-icon svg { display:block; width:19px !important; height:19px !important; max-width:19px !important; max-height:19px !important; flex:0 0 19px; fill:none; stroke:#234B7C; stroke-width:1.7; stroke-linecap:round; stroke-linejoin:round; }
.category-icon.ic-coll { background:#EDF3F1; }.category-icon.ic-coll svg { stroke:#426A5A; }
.category-icon.ic-credit { background:#F4F1EA; }.category-icon.ic-credit svg { stroke:#8B7045; }
.category-icon.ic-serv { background:#F0EFF5; }.category-icon.ic-serv svg { stroke:#6B6482; }
.category-copy { display:flex; flex-direction:column; gap:4px; flex:1; }
.category-copy b { color:#172B45; font-size:13px; font-weight:650; }
.category-copy small { color:#64748B; font-size:11px; }
.category-chevron { color:#8190A2; font-size:20px; line-height:1; }
.category-subtitle { margin:0 0 5px 27px; color:#64748B; font-size:11px; line-height:1.45; }
.st-key-cat_card_0 .stButton button, .st-key-cat_card_1 .stButton button,
.st-key-cat_card_2 .stButton button, .st-key-cat_card_3 .stButton button {
  width:100%; min-height:34px; display:flex; justify-content:flex-start; text-align:left;
  padding:5px 7px !important; background:transparent !important; color:#64748B !important;
  border:0 !important; border-radius:6px !important; box-shadow:none !important;
  font-size:11px !important; font-weight:500 !important; line-height:1.4 !important; white-space:normal !important;
}
.st-key-cat_card_0 .st-key-tog_0 button, .st-key-cat_card_1 .st-key-tog_1 button,
.st-key-cat_card_2 .st-key-tog_2 button, .st-key-cat_card_3 .st-key-tog_3 button {
  min-height:36px; height:36px; width:100%; justify-content:flex-start !important; gap:9px !important;
  padding:0 !important; opacity:1; cursor:pointer; color:#172B45 !important;
  background:transparent !important; border:0 !important; box-shadow:none !important;
  font-size:13px !important; font-weight:650 !important; text-align:left !important;
}
.st-key-cat_card_0 .st-key-tog_0 button > div, .st-key-cat_card_1 .st-key-tog_1 button > div,
.st-key-cat_card_2 .st-key-tog_2 button > div, .st-key-cat_card_3 .st-key-tog_3 button > div { width:100%; justify-content:flex-start !important; }
.st-key-cat_card_0 .st-key-tog_0 button span[data-has-shortcut], .st-key-cat_card_1 .st-key-tog_1 button span[data-has-shortcut],
.st-key-cat_card_2 .st-key-tog_2 button span[data-has-shortcut], .st-key-cat_card_3 .st-key-tog_3 button span[data-has-shortcut] {
  display:flex !important; flex:1 1 auto; align-items:center; justify-content:flex-start !important; text-align:left !important;
}
.st-key-cat_card_0 .st-key-tog_0 button span[data-has-shortcut], .st-key-cat_card_1 .st-key-tog_1 button span[data-has-shortcut],
.st-key-cat_card_2 .st-key-tog_2 button span[data-has-shortcut], .st-key-cat_card_3 .st-key-tog_3 button span[data-has-shortcut] { width:100%; justify-content:flex-start !important; }
.st-key-cat_card_0 .st-key-tog_0 button [data-testid="stIconMaterial"],
.st-key-cat_card_1 .st-key-tog_1 button [data-testid="stIconMaterial"],
.st-key-cat_card_2 .st-key-tog_2 button [data-testid="stIconMaterial"],
.st-key-cat_card_3 .st-key-tog_3 button [data-testid="stIconMaterial"] {
  display:inline-flex !important; align-items:center; justify-content:center;
  width:15px !important; min-width:15px !important; height:15px !important;
  overflow:hidden; font-size:15px !important; line-height:15px !important;
}
.st-key-cat_card_0 .st-key-tog_0 button > div, .st-key-cat_card_1 .st-key-tog_1 button > div,
.st-key-cat_card_2 .st-key-tog_2 button > div, .st-key-cat_card_3 .st-key-tog_3 button > div {
  display:flex !important; width:100% !important; justify-content:flex-start !important; text-align:left !important;
}
.st-key-cat_card_0 .st-key-tog_0 button [data-testid="stMarkdownContainer"],
.st-key-cat_card_1 .st-key-tog_1 button [data-testid="stMarkdownContainer"],
.st-key-cat_card_2 .st-key-tog_2 button [data-testid="stMarkdownContainer"],
.st-key-cat_card_3 .st-key-tog_3 button [data-testid="stMarkdownContainer"] { width:100%; text-align:left !important; }
.st-key-cat_card_0 .st-key-tog_0 button p, .st-key-cat_card_1 .st-key-tog_1 button p,
.st-key-cat_card_2 .st-key-tog_2 button p, .st-key-cat_card_3 .st-key-tog_3 button p { text-align:left !important; }
.st-key-cat_card_0 .st-key-tog_0 button span[style*="display: contents"], .st-key-cat_card_1 .st-key-tog_1 button span[style*="display: contents"],
.st-key-cat_card_2 .st-key-tog_2 button span[style*="display: contents"], .st-key-cat_card_3 .st-key-tog_3 button span[style*="display: contents"] { flex:1 1 auto; min-width:0; text-align:left !important; }
.st-key-cat_card_0 .st-key-tog_0 button svg, .st-key-cat_card_1 .st-key-tog_1 button svg,
.st-key-cat_card_2 .st-key-tog_2 button svg, .st-key-cat_card_3 .st-key-tog_3 button svg {
  width:17px !important; height:17px !important; color:#496887 !important;
}
.st-key-cat_card_0 .st-key-tog_0 button::after, .st-key-cat_card_1 .st-key-tog_1 button::after,
.st-key-cat_card_2 .st-key-tog_2 button::after, .st-key-cat_card_3 .st-key-tog_3 button::after {
  content:"›"; margin-left:auto; color:#8190A2; font-size:20px; font-weight:400;
}
.st-key-cat_card_0 .st-key-tog_0 button:hover, .st-key-cat_card_1 .st-key-tog_1 button:hover,
.st-key-cat_card_2 .st-key-tog_2 button:hover, .st-key-cat_card_3 .st-key-tog_3 button:hover { background:transparent !important; color:#244B78 !important; transform:none !important; }
.st-key-cat_card_0 .stButton button:hover, .st-key-cat_card_1 .stButton button:hover,
.st-key-cat_card_2 .stButton button:hover, .st-key-cat_card_3 .stButton button:hover { background:#EDF2F8 !important; color:#172B45 !important; transform:none !important; }
.st-key-cat_card_0 [class*="st-key-q_"], .st-key-cat_card_1 [class*="st-key-q_"],
.st-key-cat_card_2 [class*="st-key-q_"], .st-key-cat_card_3 [class*="st-key-q_"] { border-top:1px solid #F1F5F9; padding-top:3px; }
/* Apply the same card treatment to every topic in the expanded six-topic set. */
[class*="st-key-cat_card_"] { min-height:100%; padding:18px 19px 14px; border:1px solid #E2E8F0; border-radius:12px; background:#fff; box-shadow:0 1px 2px rgba(23,43,69,.025); transition:border-color .16s,box-shadow .16s,transform .16s; }
[class*="st-key-cat_card_"]:hover { border-color:#C8D5E3; box-shadow:0 5px 16px rgba(23,43,69,.055); transform:translateY(-1px); }
[class*="st-key-cat_card_"] > div[data-testid="stVerticalBlock"] { gap:7px; }
[class*="st-key-cat_card_"] .stButton button { width:100%; min-height:34px; display:flex; justify-content:flex-start; text-align:left; padding:5px 7px !important; background:transparent !important; color:#64748B !important; border:0 !important; border-radius:6px !important; box-shadow:none !important; font-size:11px !important; font-weight:500 !important; line-height:1.4 !important; white-space:normal !important; }
[class*="st-key-cat_card_"] [class*="st-key-tog_"] button { min-height:36px; height:36px; width:100%; justify-content:flex-start !important; gap:9px !important; padding:0 !important; opacity:1; cursor:pointer; color:#172B45 !important; background:transparent !important; border:0 !important; box-shadow:none !important; font-size:13px !important; font-weight:650 !important; text-align:left !important; }
[class*="st-key-cat_card_"] [class*="st-key-tog_"] button > div { display:flex !important; width:100% !important; justify-content:flex-start !important; text-align:left !important; }
[class*="st-key-cat_card_"] [class*="st-key-tog_"] button span[data-has-shortcut] { display:flex !important; flex:1 1 auto; align-items:center; justify-content:flex-start !important; text-align:left !important; }
[class*="st-key-cat_card_"] [class*="st-key-tog_"] button [data-testid="stIconMaterial"] { display:inline-flex !important; align-items:center; justify-content:center; width:15px !important; min-width:15px !important; height:15px !important; overflow:hidden; font-size:15px !important; line-height:15px !important; }
[class*="st-key-cat_card_"] [class*="st-key-tog_"] button [data-testid="stMarkdownContainer"] { width:100%; text-align:left !important; }
[class*="st-key-cat_card_"] [class*="st-key-tog_"] button p { text-align:left !important; }
[class*="st-key-cat_card_"] [class*="st-key-tog_"] button::after { content:"›"; margin-left:auto; color:#8190A2; font-size:20px; font-weight:400; }
[class*="st-key-cat_card_"] [class*="st-key-tog_"] button:hover { background:transparent !important; color:#244B78 !important; transform:none !important; }
[class*="st-key-cat_card_"] .stButton button:hover { background:#EDF2F8 !important; color:#172B45 !important; transform:none !important; }
[class*="st-key-cat_card_"] [class*="st-key-q_"] { border-top:1px solid #F1F5F9; padding-top:3px; }
.grounding-note { max-width:790px; margin:18px auto 0; display:flex; align-items:flex-start; gap:9px; color:#64748B; font-size:11px; line-height:1.55; }
.grounding-mark { width:16px; height:16px; flex:0 0 16px; display:grid; place-items:center; border:1px solid #CBD5E1; border-radius:50%; color:#64748B; font-size:10px; font-weight:700; }

/* Real keyed wrappers style the widgets that Streamlit places in separate DOM blocks. */
.st-key-chart_asset_mix, .st-key-chart_principal_asset, .st-key-chart_principal_year,
.st-key-chart_apr_asset, .st-key-chart_issuer_activity, .st-key-chart_credit_scatter {
  height:100%; padding:16px 17px 8px; background:#fff; border:1px solid #E2E8F0;
  border-radius:11px; box-shadow:0 1px 3px rgba(23,43,69,.035);
}
.st-key-chart_asset_mix > div[data-testid="stVerticalBlock"], .st-key-chart_principal_asset > div[data-testid="stVerticalBlock"],
.st-key-chart_principal_year > div[data-testid="stVerticalBlock"], .st-key-chart_apr_asset > div[data-testid="stVerticalBlock"],
.st-key-chart_issuer_activity > div[data-testid="stVerticalBlock"], .st-key-chart_credit_scatter > div[data-testid="stVerticalBlock"] { gap:0; }
.st-key-answer_panel { margin:0 0 16px; padding:0; overflow:hidden; background:#fff; border:1px solid #E2E8F0; border-radius:12px; box-shadow:0 2px 10px rgba(23,43,69,.045); }
.st-key-answer_panel .ai-answer-card-hdr { min-height:48px; padding:12px 16px; }
.st-key-answer_panel [data-testid="stMarkdownContainer"] { padding:5px 18px; color:#24364B; font-size:14px; line-height:1.8; }
.st-key-answer_panel [data-testid="stMarkdownContainer"] p { margin:0 0 12px; }
.st-key-answer_panel [data-testid="stMarkdownContainer"] ul,
.st-key-answer_panel [data-testid="stMarkdownContainer"] ol { margin:5px 0 12px 20px; }
.st-key-answer_panel [data-testid="stMarkdownContainer"] a { color:#244B78; font-weight:650; text-decoration:underline; text-decoration-color:#A9BCD2; text-underline-offset:2px; }
.st-key-answer_panel .ai-answer-footer { padding:10px 16px; }
.evidence-header { display:flex; flex-direction:column; gap:3px; padding:4px 1px 12px; }
.evidence-header b { color:#172B45; font-size:13px; font-weight:650; }
.evidence-header small { color:#64748B; font-size:11px; }
.ai-src-card { scroll-margin-top:24px; padding:12px; border-radius:9px; }
.ai-src-issuer { font-size:11px; color:#64748B; }
.ai-src-deal { color:#172B45; font-size:12px; font-weight:650; line-height:1.45; margin:3px 0; }
.ai-src-filing { color:#94A3B8; font-size:9px; word-break:break-word; }
.ai-src-chip { font-size:9px; }
.ai-src-excerpt { display:block; max-height:88px; -webkit-line-clamp:4; margin-top:6px; }
.source-link { display:inline-block; margin-top:9px; color:#244B78; font-size:10px; font-weight:600; text-decoration:none; }
.source-link:hover { color:#172B45; text-decoration:underline; }
.source-unavailable { display:inline-block; margin-top:8px; color:#94A3B8; font-size:10px; }
.st-key-followup_composer { margin-top:10px; padding:14px; background:#fff; border:1px solid #E2E8F0; border-radius:12px; }
.page-hdr { padding:18px 0 20px; margin-bottom:18px; }
.page-hdr-title { color:#172B45; font-size:24px; font-weight:650; letter-spacing:-.45px; }
.page-hdr-sub { color:#64748B; font-size:13px; }
.kpi-card { border-radius:10px; box-shadow:0 1px 3px rgba(23,43,69,.035); }
.kpi-card.kc-blue::before { background:#244B78; }
.kpi-card.kc-teal::before { background:#66897C; }
.kpi-card.kc-amber::before { background:#B18B55; }
.kpi-card.kc-violet::before { background:#77768D; }
.icon-blue { background:#EDF2F8; color:#244B78; }
.icon-teal { background:#EDF3F1; color:#557668; }
.icon-amber { background:#F5F1E9; color:#927144; }
.icon-violet { background:#F0EFF5; color:#6B6982; }
.chart-card { border-radius:11px; box-shadow:0 1px 3px rgba(23,43,69,.035); }
.chart-card-title { color:#172B45; font-size:13px; font-weight:650; letter-spacing:.1px; text-transform:none; }
.chart-card-sub { color:#52637A; font-size:12px; }
.browse-toolbar { border-radius:9px; }
.rc { border-left-color:#244B78; border-radius:10px; box-shadow:0 1px 3px rgba(23,43,69,.035); }
.rc:hover { border-color:#CAD5E1; }
.stDataFrame { border-radius:10px !important; }
.market-page-hdr { padding:20px 0 5px; margin:0; border:0; }
.market-page-hdr .page-hdr-title { font-size:30px; font-weight:650; letter-spacing:-.75px; line-height:1.18; }
.market-page-hdr .page-hdr-sub { margin-top:7px; color:#52637A; font-size:14px; line-height:1.55; }
.market-context { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:8px 20px; margin:7px 0 22px; padding-bottom:15px; border-bottom:1px solid #E2E8F0; }
.market-context-stats { display:flex; align-items:center; flex-wrap:wrap; gap:11px; color:#52637A; font-size:13px; }
.market-context-stats b { color:#172B45; font-weight:650; }
.market-context-stats i { width:3px; height:3px; border-radius:50%; background:#94A3B8; }
.market-coverage { color:#64748B; font-size:11px; line-height:1.45; }
.kpi-grid { gap:16px; margin-bottom:18px; }
.kpi-card-label { color:#52637A; font-size:11px; letter-spacing:.55px; }
.kpi-card-value { font-size:28px; letter-spacing:-.6px; }
.market-observations { margin:20px 0 18px; padding:20px; border:1px solid #E2E8F0; border-radius:12px; background:#fff; box-shadow:0 1px 3px rgba(23,43,69,.03); }
.market-section-heading { display:flex; align-items:center; gap:10px; margin:0 0 15px; }
.market-section-icon { width:30px; height:30px; display:grid; place-items:center; border-radius:8px; background:#EDF2F8; color:#234B7C; font-size:16px; font-weight:600; }
.market-section-heading h2 { margin:0; color:#172B45; font-size:16px; font-weight:650; letter-spacing:-.15px; }
.market-section-heading p { margin:3px 0 0; color:#64748B; font-size:12px; }
.observation-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }
.observation-card { display:flex; flex-direction:column; gap:6px; min-width:0; padding:16px; border:1px solid #E8EDF3; border-radius:10px; background:#F8FAFC; }
.observation-label { color:#52637A; font-size:11px; font-weight:600; letter-spacing:.1px; }
.observation-card strong { color:#234B78; font-size:25px; font-weight:650; letter-spacing:-.5px; line-height:1.2; }
.observation-card b { color:#172B45; font-size:13px; font-weight:600; line-height:1.35; }
.observation-card p { margin:0; color:#52637A; font-size:12px; line-height:1.5; }
.st-key-market_ai_cta { display:block; margin:0 0 24px; padding:17px 20px; border:1px solid #DCE5EF; border-radius:11px; background:#fff; }
.st-key-market_ai_cta > div[data-testid="stVerticalBlock"] { gap:0; }
.market-cta-title { color:#172B45; font-size:15px; font-weight:650; }
.market-cta-copy { max-width:760px; margin-top:4px; color:#52637A; font-size:12px; line-height:1.55; }
.st-key-market_ai_cta button { width:auto !important; min-height:38px; padding:0 15px !important; border-radius:8px !important; font-size:12px !important; }
.stExpander { border:1px solid #E2E8F0 !important; border-radius:10px !important; background:#fff !important; }
/* Small finishing refinements for the approved interface. */
section[data-testid="stSidebar"] .st-key-nav_overview button > div,
section[data-testid="stSidebar"] .st-key-nav_research button > div,
section[data-testid="stSidebar"] .st-key-nav_search button > div,
section[data-testid="stSidebar"] .st-key-nav_documents button > div { display:flex !important; justify-content:flex-start !important; }
section[data-testid="stSidebar"] .st-key-nav_overview button span[data-has-shortcut],
section[data-testid="stSidebar"] .st-key-nav_research button span[data-has-shortcut],
section[data-testid="stSidebar"] .st-key-nav_search button span[data-has-shortcut],
section[data-testid="stSidebar"] .st-key-nav_documents button span[data-has-shortcut] { display:flex !important; width:100%; align-items:center; justify-content:flex-start !important; gap:9px; }
.category-subtitle { margin:-3px 0 5px 39px; }
[class*="st-key-cat_card_"] [class*="st-key-tog_"] button { font-weight:600 !important; }
[class*="st-key-cat_card_"] > div[data-testid="stVerticalBlock"] { gap:3px; }
.st-key-cat_card_0 .st-key-tog_0 button [data-testid="stIconMaterial"], .st-key-cat_card_4 .st-key-tog_4 button [data-testid="stIconMaterial"] { width:30px !important; min-width:30px !important; height:30px !important; border-radius:8px; background:#EDF2F8; color:#234B7C !important; font-size:15px !important; line-height:30px !important; }
.st-key-cat_card_1 .st-key-tog_1 button [data-testid="stIconMaterial"], .st-key-cat_card_5 .st-key-tog_5 button [data-testid="stIconMaterial"] { width:30px !important; min-width:30px !important; height:30px !important; border-radius:8px; background:#EDF3F1; color:#557668 !important; font-size:15px !important; line-height:30px !important; }
.st-key-cat_card_2 .st-key-tog_2 button [data-testid="stIconMaterial"] { width:30px !important; min-width:30px !important; height:30px !important; border-radius:8px; background:#F4F1EA; color:#927144 !important; font-size:15px !important; line-height:30px !important; }
.st-key-cat_card_3 .st-key-tog_3 button [data-testid="stIconMaterial"] { width:30px !important; min-width:30px !important; height:30px !important; border-radius:8px; background:#F0EFF5; color:#6B6982 !important; font-size:15px !important; line-height:30px !important; }
.st-key-ai_prompt_card [data-testid="stForm"] [data-testid="column"]:last-child [data-testid="stElementContainer"] { width:100% !important; display:flex; justify-content:flex-end !important; }
.st-key-ai_prompt_card [data-testid="stForm"] [data-testid="column"]:last-child [data-testid="stFormSubmitButton"] { width:auto !important; margin-left:auto !important; }
.st-key-ai_prompt_card [data-testid="stForm"] [data-testid="column"]:last-child button[kind="primaryFormSubmit"] { margin-left:auto !important; }
.st-key-ai_prompt_card textarea { resize:none !important; }
.st-key-ai_prompt_card [data-testid="stForm"] button[kind="primaryFormSubmit"] svg { width:14px !important; height:14px !important; }
.st-key-ai_prompt_card [data-testid="stForm"] button[kind="primaryFormSubmit"] { width:auto !important; min-width:0 !important; }
@media (max-width:760px) {
  .kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .observation-grid { grid-template-columns:1fr; }
  .market-context { align-items:flex-start; flex-direction:column; }
  .st-key-chart_asset_mix, .st-key-chart_principal_asset, .st-key-chart_principal_year,
  .st-key-chart_apr_asset, .st-key-chart_issuer_activity, .st-key-chart_credit_scatter { padding:12px; }
}
@media (max-width:700px) {
  main[data-testid="stMain"] > div[data-testid="stMainBlockContainer"],
  section.main > div.block-container { padding:16px 18px 48px !important; }
  .ai-hero { padding:22px 8px 12px; }
  .ai-hero-title { font-size:30px; }
  .market-page-hdr .page-hdr-title { font-size:26px; }
  .market-observations { padding:15px; }
  .observation-grid { grid-template-columns:1fr; }
  .st-key-market_ai_cta { padding:15px; }
  .st-key-ai_prompt_card { padding:12px; }
}
</style>
"""
