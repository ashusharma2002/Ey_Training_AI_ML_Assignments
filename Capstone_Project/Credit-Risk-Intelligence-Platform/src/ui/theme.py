# src/ui/theme.py  — Enterprise Redesign v2.0
# ============================================================
# Full enterprise banking theme.
# One file controls everything — sidebar, cards, typography,
# charts, badges, chat, upload — all design tokens here.
# ============================================================
from __future__ import annotations
import streamlit as st

# ── Design tokens ─────────────────────────────────────────────────────────────
C = {
    # Surfaces
    "shell":         "#0A0F1E",   # sidebar / app shell
    "shell_hover":   "#141B2D",
    "shell_border":  "#1E2A40",
    "bg":            "#F4F6FA",   # page background
    "surface":       "#FFFFFF",   # cards
    "surface2":      "#F8FAFC",   # secondary surface

    # Brand
    "blue":          "#0052CC",   # primary action
    "blue_light":    "#0066FF",
    "blue_dim":      "rgba(0,82,204,0.10)",
    "teal":          "#00B4A6",   # accent / positive
    "teal_dim":      "rgba(0,180,166,0.10)",
    "gold":          "#F5A623",   # highlight / warning accent
    "gold_dim":      "rgba(245,166,35,0.12)",

    # Semantic
    "success":       "#00875A",
    "success_bg":    "#E3FCEF",
    "warning":       "#FF8B00",
    "warning_bg":    "#FFFAE6",
    "danger":        "#DE350B",
    "danger_bg":     "#FFEBE6",
    "info":          "#0052CC",
    "info_bg":       "#DEEBFF",

    # Text
    "text":          "#091E42",
    "text2":         "#42526E",
    "text3":         "#6B778C",
    "text_inv":      "#FFFFFF",
    "text_inv2":     "rgba(255,255,255,0.65)",

    # Border / divider
    "border":        "#DFE1E6",
    "border2":       "#EBECF0",
    "divider":       "rgba(255,255,255,0.07)",
}

RISK_COLORS = {
    "Low":      C["success"],
    "Moderate": C["warning"],
    "High":     "#E07B00",
    "Critical": C["danger"],
}

RISK_BG = {
    "Low":      C["success_bg"],
    "Moderate": C["warning_bg"],
    "High":     "#FFF3E0",
    "Critical": C["danger_bg"],
}

# Keep backward-compat alias used by existing page files
COLORS = {
    "navy":           C["shell"],
    "navy_light":     C["shell_hover"],
    "teal":           C["teal"],
    "teal_light":     "#00D4C8",
    "gold":           C["gold"],
    "gold_light":     "#F7B84B",
    "bg":             C["bg"],
    "card_bg":        C["surface"],
    "text_primary":   C["text"],
    "text_secondary": C["text2"],
    "border":         C["border"],
    "success":        C["success"],
    "warning":        C["warning"],
    "danger":         C["danger"],
    "info":           C["info"],
    "sidebar_bg":     C["shell"],
    "sidebar_text":   C["text_inv"],
}


# ── Global CSS ────────────────────────────────────────────────────────────────
def inject_global_css() -> None:
    st.markdown(f"""
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── CSS Tokens ── */
    :root {{
        --shell:        {C['shell']};
        --shell-hover:  {C['shell_hover']};
        --shell-border: {C['shell_border']};
        --bg:           {C['bg']};
        --surface:      {C['surface']};
        --surface2:     {C['surface2']};
        --blue:         {C['blue']};
        --blue-light:   {C['blue_light']};
        --blue-dim:     {C['blue_dim']};
        --teal:         {C['teal']};
        --teal-dim:     {C['teal_dim']};
        --gold:         {C['gold']};
        --success:      {C['success']};
        --success-bg:   {C['success_bg']};
        --warning:      {C['warning']};
        --warning-bg:   {C['warning_bg']};
        --danger:       {C['danger']};
        --danger-bg:    {C['danger_bg']};
        --info:         {C['info']};
        --info-bg:      {C['info_bg']};
        --text:         {C['text']};
        --text2:        {C['text2']};
        --text3:        {C['text3']};
        --text-inv:     {C['text_inv']};
        --text-inv2:    {C['text_inv2']};
        --border:       {C['border']};
        --border2:      {C['border2']};
        /* Type scale */
        --t-display: 2rem;
        --t-h1:      1.375rem;
        --t-h2:      1rem;
        --t-body:    0.875rem;
        --t-caption: 0.75rem;
        --t-micro:   0.6875rem;
        /* Spacing (8px grid) */
        --sp-1: 4px; --sp-2: 8px; --sp-3: 12px; --sp-4: 16px;
        --sp-5: 24px; --sp-6: 32px; --sp-7: 48px; --sp-8: 64px;
        /* Radius */
        --r-sm: 6px; --r-md: 10px; --r-lg: 14px; --r-xl: 20px;
        /* Shadow */
        --shadow-sm: 0 1px 3px rgba(9,30,66,0.08), 0 0 0 1px rgba(9,30,66,0.04);
        --shadow-md: 0 4px 12px rgba(9,30,66,0.12), 0 0 0 1px rgba(9,30,66,0.04);
        --shadow-lg: 0 8px 24px rgba(9,30,66,0.14), 0 0 0 1px rgba(9,30,66,0.05);
    }}

    /* ── Reset & base ── */
    *, *::before, *::after {{ box-sizing: border-box; }}
    html, body, .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        background-color: var(--bg) !important;
        color: var(--text);
    }}

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header {{ visibility: hidden !important; height: 0 !important; }}
    .stDeployButton {{ display: none !important; }}

    /* ── Main content area ── */
    .block-container {{
        padding: 32px 40px 64px 40px !important;
        max-width: 1440px !important;
    }}

    /* ════════════════════════════════════════════
       SIDEBAR — Enterprise dark rail v2.1
    ════════════════════════════════════════════ */
    [data-testid="stSidebar"] {{
        background: var(--shell) !important;
        border-right: 1px solid var(--shell-border) !important;
        min-width: 252px !important;
        max-width: 252px !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding: 0 !important;
        background: var(--shell) !important;
    }}
    /* General sidebar text */
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown div,
    [data-testid="stSidebar"] .stMarkdown span {{
        color: rgba(255,255,255,0.55) !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: var(--shell-border) !important;
        margin: 4px 16px !important;
    }}

    /* ── Radio nav — hide the circle inputs ── */
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {{
        display: none !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] > div {{
        gap: 1px !important;
        background: transparent !important;
        padding: 0 8px !important;
    }}
    /* Each option row */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label {{
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        padding: 9px 12px !important;
        margin: 0 !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        background: transparent !important;
        border: none !important;
        transition: background 0.14s ease !important;
    }}
    /* Hide the radio circle dot */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:first-child {{
        display: none !important;
    }}
    /* Option text */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:last-child p,
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:last-child {{
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        color: rgba(255,255,255,0.6) !important;
        letter-spacing: 0.01em !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.3 !important;
    }}
    /* Hover state */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {{
        background: rgba(255,255,255,0.07) !important;
    }}
    /* Selected / active state — three selectors for full cross-version compat */
    /* :has(input:checked) = Streamlit 1.35+  |  data-selected / aria-checked = older versions */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked),
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-selected="true"],
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[aria-checked="true"] {{
        background: rgba(0,82,204,0.22) !important;
        border-left: 3px solid #3b82f6 !important;
        padding-left: 9px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) > div:last-child p,
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) > div:last-child,
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-selected="true"] > div:last-child p,
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-selected="true"] > div:last-child,
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[aria-checked="true"] > div:last-child p,
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[aria-checked="true"] > div:last-child {{
        color: #ffffff !important;
        font-weight: 700 !important;
    }}

    /* ── Group labels (MAIN / ANALYSIS / SESSION) ── */
    .nav-group-label {{
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: rgba(255,255,255,0.28);
        padding: 12px 20px 2px 20px;
        margin: 0;
    }}

    /* ════════════════════════════════════════════
       PAGE HEADER
    ════════════════════════════════════════════ */
    .page-hero {{
        margin-bottom: var(--sp-5);
    }}
    .page-title {{
        font-size: var(--t-h1);
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.02em;
        line-height: 1.2;
        margin: 0 0 4px 0;
    }}
    .page-subtitle {{
        font-size: var(--t-body);
        color: var(--text2);
        margin: 0;
        font-weight: 400;
    }}
    .page-divider {{
        height: 1px;
        background: var(--border);
        margin: var(--sp-4) 0 var(--sp-5) 0;
    }}

    /* ════════════════════════════════════════════
       KPI CARDS v2 — with accent bar + icon
    ════════════════════════════════════════════ */
    .kpi-card {{
        background: var(--surface);
        border-radius: var(--r-md);
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
        padding: var(--sp-4) var(--sp-4) var(--sp-4) 0;
        display: flex;
        align-items: stretch;
        overflow: hidden;
        transition: box-shadow 0.18s ease, transform 0.18s ease;
        height: 100%;
    }}
    .kpi-card:hover {{
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }}
    .kpi-accent {{
        width: 4px;
        border-radius: 4px 0 0 4px;
        flex-shrink: 0;
        margin-right: var(--sp-3);
    }}
    .kpi-body {{
        flex: 1;
        min-width: 0;
    }}
    .kpi-label {{
        font-size: var(--t-micro);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: var(--text3);
        margin-bottom: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .kpi-value {{
        font-size: var(--t-display);
        font-weight: 800;
        color: var(--text);
        line-height: 1.05;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.03em;
        margin-bottom: 4px;
    }}
    .kpi-sub {{
        font-size: var(--t-caption);
        color: var(--text3);
        font-weight: 400;
    }}
    .kpi-icon {{
        width: 36px;
        height: 36px;
        border-radius: var(--r-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        flex-shrink: 0;
        align-self: flex-start;
        margin-right: var(--sp-3);
    }}

    /* ════════════════════════════════════════════
       SECTION HEADERS — cleaner, less overused
    ════════════════════════════════════════════ */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 24px 0 14px 0;
    }}
    .section-dot {{
        width: 3px;
        height: 18px;
        background: var(--blue);
        border-radius: 2px;
        flex-shrink: 0;
    }}
    .section-title {{
        font-size: var(--t-h2);
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.01em;
    }}

    /* ════════════════════════════════════════════
       STATUS BADGES
    ════════════════════════════════════════════ */
    .badge {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 9px;
        border-radius: 20px;
        font-size: var(--t-micro);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        white-space: nowrap;
    }}
    .badge-success {{ background: var(--success-bg); color: var(--success); }}
    .badge-warning {{ background: var(--warning-bg); color: var(--warning); }}
    .badge-danger  {{ background: var(--danger-bg);  color: var(--danger);  }}
    .badge-info    {{ background: var(--info-bg);    color: var(--info);    }}
    .badge-neutral {{ background: var(--surface2);   color: var(--text3);   border: 1px solid var(--border); }}

    /* ════════════════════════════════════════════
       ALERT / INFO BOXES
    ════════════════════════════════════════════ */
    .info-box {{
        background: var(--info-bg);
        border-left: 3px solid var(--info);
        padding: 12px 16px;
        border-radius: 0 var(--r-sm) var(--r-sm) 0;
        margin: 8px 0;
        font-size: var(--t-body);
        color: var(--text);
        line-height: 1.5;
    }}
    .warning-box {{
        background: var(--warning-bg);
        border-left: 3px solid var(--warning);
        padding: 12px 16px;
        border-radius: 0 var(--r-sm) var(--r-sm) 0;
        margin: 8px 0;
        font-size: var(--t-body);
        color: var(--text);
        line-height: 1.5;
    }}
    .danger-box {{
        background: var(--danger-bg);
        border-left: 3px solid var(--danger);
        padding: 12px 16px;
        border-radius: 0 var(--r-sm) var(--r-sm) 0;
        margin: 8px 0;
        font-size: var(--t-body);
        color: var(--text);
        line-height: 1.5;
    }}
    .success-box {{
        background: var(--success-bg);
        border-left: 3px solid var(--success);
        padding: 12px 16px;
        border-radius: 0 var(--r-sm) var(--r-sm) 0;
        margin: 8px 0;
        font-size: var(--t-body);
        color: var(--text);
        line-height: 1.5;
    }}

    /* ════════════════════════════════════════════
       EMPTY STATE
    ════════════════════════════════════════════ */
    .empty-state {{
        text-align: center;
        padding: 48px 32px;
        background: var(--surface);
        border-radius: var(--r-lg);
        border: 1px dashed var(--border);
    }}
    .empty-icon {{
        font-size: 2.5rem;
        margin-bottom: 12px;
        opacity: 0.5;
    }}
    .empty-title {{
        font-size: var(--t-h2);
        font-weight: 700;
        color: var(--text);
        margin-bottom: 6px;
    }}
    .empty-desc {{
        font-size: var(--t-body);
        color: var(--text3);
        max-width: 320px;
        margin: 0 auto;
        line-height: 1.5;
    }}

    /* ════════════════════════════════════════════
       CHAT v2
    ════════════════════════════════════════════ */
    .chat-bubble-user {{
        background: var(--blue);
        color: white;
        padding: 10px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 6px 0 6px 15%;
        font-size: var(--t-body);
        line-height: 1.55;
        box-shadow: 0 2px 8px rgba(0,82,204,0.25);
    }}
    .chat-bubble-assistant {{
        background: var(--surface);
        color: var(--text);
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 6px 15% 6px 0;
        font-size: var(--t-body);
        line-height: 1.55;
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
    }}
    .chat-meta {{
        font-size: var(--t-micro);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 5px;
        opacity: 0.7;
    }}
    .chat-source {{
        font-size: var(--t-micro);
        color: var(--text3);
        margin-top: 6px;
        padding-top: 6px;
        border-top: 1px solid var(--border);
    }}
    .chat-thread {{
        max-height: 520px;
        overflow-y: auto;
        padding: 8px 0;
        scroll-behavior: smooth;
    }}

    /* ════════════════════════════════════════════
       CHECKLIST ITEMS
    ════════════════════════════════════════════ */
    .checklist-item {{
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 12px 16px;
        background: var(--surface);
        border-radius: var(--r-md);
        margin: 6px 0;
        border: 1px solid var(--border);
        font-size: var(--t-body);
        transition: border-color 0.15s;
    }}
    .checklist-item:hover {{ border-color: var(--teal); }}
    .check-icon {{
        width: 22px;
        height: 22px;
        background: var(--teal-dim);
        color: var(--teal);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 1px;
    }}

    /* ════════════════════════════════════════════
       FILE UPLOAD ZONE
    ════════════════════════════════════════════ */
    [data-testid="stFileUploader"] {{
        border: 2px dashed var(--blue) !important;
        border-radius: var(--r-lg) !important;
        background: var(--blue-dim) !important;
        padding: 8px !important;
        transition: border-color 0.2s, background 0.2s;
    }}
    [data-testid="stFileUploader"]:hover {{
        border-color: var(--blue-light) !important;
        background: rgba(0,102,255,0.07) !important;
    }}

    /* ════════════════════════════════════════════
       BUTTONS
    ════════════════════════════════════════════ */
    .stButton > button {{
        font-family: 'Inter', sans-serif !important;
        font-size: var(--t-body) !important;
        font-weight: 600 !important;
        border-radius: var(--r-sm) !important;
        transition: all 0.15s ease !important;
    }}
    .stButton > button[kind="primary"] {{
        background: var(--blue) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 2px 6px rgba(0,82,204,0.30) !important;
        padding: 0.55rem 1.5rem !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: var(--blue-light) !important;
        box-shadow: 0 4px 12px rgba(0,82,204,0.40) !important;
        transform: translateY(-1px) !important;
    }}
    .stButton > button:not([kind="primary"]) {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
    }}
    .stButton > button:not([kind="primary"]):hover {{
        border-color: var(--blue) !important;
        color: var(--blue) !important;
        background: var(--blue-dim) !important;
    }}

    /* ════════════════════════════════════════════
       TABS
    ════════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background: var(--surface2);
        border-radius: var(--r-md) var(--r-md) 0 0;
        border: 1px solid var(--border);
        border-bottom: none;
        padding: 4px 4px 0 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: var(--r-sm) var(--r-sm) 0 0;
        padding: 8px 18px;
        font-weight: 500;
        font-size: var(--t-caption);
        color: var(--text2);
        border: none;
        background: transparent;
        transition: color 0.15s;
    }}
    .stTabs [aria-selected="true"] {{
        background: var(--surface) !important;
        color: var(--blue) !important;
        font-weight: 700;
        box-shadow: 0 -2px 0 var(--blue) inset;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-top: none;
        border-radius: 0 0 var(--r-md) var(--r-md);
        padding: var(--sp-4) !important;
    }}

    /* ════════════════════════════════════════════
       EXPANDERS
    ════════════════════════════════════════════ */
    [data-testid="stExpander"] {{
        border: 1px solid var(--border) !important;
        border-radius: var(--r-md) !important;
        background: var(--surface) !important;
        box-shadow: var(--shadow-sm) !important;
        margin-bottom: 6px !important;
    }}
    [data-testid="stExpander"]:hover {{
        border-color: var(--blue) !important;
    }}

    /* ════════════════════════════════════════════
       INPUTS & SELECTBOX
    ════════════════════════════════════════════ */
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input {{
        font-family: 'Inter', sans-serif !important;
        font-size: var(--t-body) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r-sm) !important;
        background: var(--surface) !important;
        color: var(--text) !important;
        transition: border-color 0.15s !important;
    }}
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stTextInput"] input:focus {{
        border-color: var(--blue) !important;
        box-shadow: 0 0 0 3px rgba(0,82,204,0.12) !important;
        outline: none !important;
    }}

    /* ════════════════════════════════════════════
       SELECTBOX
    ════════════════════════════════════════════ */
    [data-testid="stSelectbox"] > div > div {{
        border: 1px solid var(--border) !important;
        border-radius: var(--r-sm) !important;
        background: var(--surface) !important;
        font-size: var(--t-body) !important;
    }}

    /* ════════════════════════════════════════════
       DIVIDERS
    ════════════════════════════════════════════ */
    hr {{
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: var(--sp-5) 0 !important;
    }}

    /* ════════════════════════════════════════════
       PROGRESS BAR
    ════════════════════════════════════════════ */
    [data-testid="stProgress"] > div > div {{
        background: var(--blue) !important;
        border-radius: 4px !important;
    }}
    [data-testid="stProgress"] > div {{
        background: var(--border) !important;
        border-radius: 4px !important;
    }}

    /* ════════════════════════════════════════════
       SPINNER
    ════════════════════════════════════════════ */
    [data-testid="stSpinner"] {{
        color: var(--blue) !important;
    }}

    /* ════════════════════════════════════════════
       METRIC
    ════════════════════════════════════════════ */
    [data-testid="metric-container"] {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--r-md);
        padding: var(--sp-3) var(--sp-4);
        box-shadow: var(--shadow-sm);
    }}

    /* ════════════════════════════════════════════
       STEP TRACKER
    ════════════════════════════════════════════ */
    .step-row {{
        display: flex;
        align-items: center;
        gap: 0;
        margin: var(--sp-4) 0;
    }}
    .step-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }}
    .step-circle {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: var(--t-micro);
        font-weight: 700;
        z-index: 1;
        position: relative;
    }}
    .step-circle.done  {{ background: var(--teal); color: white; }}
    .step-circle.active{{ background: var(--blue); color: white; box-shadow: 0 0 0 4px var(--blue-dim); }}
    .step-circle.idle  {{ background: var(--surface2); color: var(--text3); border: 2px solid var(--border); }}
    .step-label {{
        font-size: var(--t-micro);
        font-weight: 600;
        color: var(--text3);
        margin-top: 4px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    .step-label.active {{ color: var(--blue); }}
    .step-label.done   {{ color: var(--teal); }}
    .step-connector {{
        flex: 1;
        height: 2px;
        background: var(--border);
        margin-top: -16px;
        z-index: 0;
    }}
    .step-connector.done {{ background: var(--teal); }}

    /* ════════════════════════════════════════════
       ACTIVITY ITEM
    ════════════════════════════════════════════ */
    .activity-item {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        background: var(--surface);
        border-radius: var(--r-sm);
        margin: 4px 0;
        border: 1px solid var(--border2);
        font-size: var(--t-body);
        transition: border-color 0.15s;
    }}
    .activity-item:hover {{ border-color: var(--border); }}
    .activity-name {{
        font-weight: 500;
        color: var(--text);
        max-width: 170px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    /* ════════════════════════════════════════════
       DOCUMENT TYPE CARDS
    ════════════════════════════════════════════ */
    .doc-type-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--r-md);
        padding: 16px 12px;
        text-align: center;
        transition: border-color 0.15s, box-shadow 0.15s;
        height: 100%;
    }}
    .doc-type-card:hover {{
        border-color: var(--blue);
        box-shadow: var(--shadow-sm);
    }}

    /* ════════════════════════════════════════════
       INSIGHT CARD
    ════════════════════════════════════════════ */
    .insight-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--r-md);
        padding: 16px;
        height: 100%;
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.18s, transform 0.18s;
    }}
    .insight-card:hover {{
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }}

    /* ════════════════════════════════════════════
       LOAN CARD
    ════════════════════════════════════════════ */
    .loan-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--r-md);
        padding: var(--sp-4);
        margin: 8px 0;
        box-shadow: var(--shadow-sm);
    }}
    .loan-card-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border2);
    }}

    /* ════════════════════════════════════════════
       ACTION ITEM (Next steps)
    ════════════════════════════════════════════ */
    .action-item {{
        display: flex;
        align-items: flex-start;
        gap: 14px;
        padding: 14px 16px;
        background: var(--surface);
        border-radius: var(--r-md);
        border: 1px solid var(--border);
        margin: 6px 0;
        transition: border-color 0.15s;
    }}
    .action-num {{
        width: 28px;
        height: 28px;
        border-radius: var(--r-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: var(--t-caption);
        font-weight: 800;
        flex-shrink: 0;
        margin-top: 1px;
    }}

    /* ════════════════════════════════════════════
       SCROLLBAR
    ════════════════════════════════════════════ */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--text3); }}
    </style>
    """, unsafe_allow_html=True)


# ── Component helpers ─────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "") -> None:
    sub_html = f"<p class='page-subtitle'>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"<div class='page-hero'>"
        f"<h1 class='page-title'>{title}</h1>"
        f"{sub_html}"
        f"</div>"
        f"<div class='page-divider'></div>",
        unsafe_allow_html=True,
    )


def section_header(icon: str, title: str) -> None:
    st.markdown(
        f"<div class='section-header'>"
        f"<div class='section-dot'></div>"
        f"<span class='section-title'>{title}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def kpi_card(
    label: str,
    value: str,
    sub: str = "",
    color: str = "",
    accent: str = "",
    icon: str = "",
    icon_bg: str = "",
) -> str:
    accent_color = accent or color or C["blue"]
    value_style = f"color:{color};" if color else ""
    _icon_bg = icon_bg or C["blue_dim"]
    icon_html = (
        f"<div class='kpi-icon' style='background:{_icon_bg}'>{icon}</div>"
        if icon else ""
    )
    sub_html = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
    return (
        f"<div class='kpi-card'>"
        f"<div class='kpi-accent' style='background:{accent_color}'></div>"
        f"{icon_html}"
        f"<div class='kpi-body'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value' style='{value_style}'>{value}</div>"
        f"{sub_html}"
        f"</div>"
        f"</div>"
    )


def badge(text: str, variant: str = "neutral") -> str:
    return f"<span class='badge badge-{variant}'>{text}</span>"


def info_box(text: str, variant: str = "info") -> None:
    st.markdown(f"<div class='{variant}-box'>{text}</div>", unsafe_allow_html=True)


def empty_state(icon: str, title: str, desc: str) -> None:
    st.markdown(
        f"<div class='empty-state'>"
        f"<div class='empty-icon'>{icon}</div>"
        f"<div class='empty-title'>{title}</div>"
        f"<div class='empty-desc'>{desc}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def checklist_item(text: str) -> None:
    st.markdown(
        f"<div class='checklist-item'>"
        f"<div class='check-icon'>✓</div>"
        f"<span style='font-size:var(--t-body);color:var(--text);line-height:1.5'>{text}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def step_tracker(steps: list[str], current: int) -> None:
    """current = 0-based index of active step; steps before it are 'done'."""
    parts = ["<div class='step-row'>"]
    for i, label in enumerate(steps):
        if i < current:
            circle_cls, label_cls, num = "done", "done", "✓"
        elif i == current:
            circle_cls, label_cls, num = "active", "active", str(i + 1)
        else:
            circle_cls, label_cls, num = "idle", "", str(i + 1)

        parts.append(
            f"<div class='step-item'>"
            f"<div class='step-circle {circle_cls}'>{num}</div>"
            f"<div class='step-label {label_cls}'>{label}</div>"
            f"</div>"
        )
        if i < len(steps) - 1:
            conn_cls = "done" if i < current else ""
            parts.append(f"<div class='step-connector {conn_cls}'></div>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
