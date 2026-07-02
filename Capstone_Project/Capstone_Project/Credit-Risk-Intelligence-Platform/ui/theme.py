# ui/theme.py — Full Dark Enterprise Theme v3.0
# ============================================================
# Complete dark theme — consistent across login, all pages,
# Docker container, and Azure deployment.
#
# v3.0 change: switched from mixed light/dark to fully dark.
# Main background: #0D1117 (GitHub dark style)
# All text: light on dark — proper contrast everywhere.
# Sidebar unchanged — was already dark.
# ============================================================
from __future__ import annotations
import streamlit as st

# ── Design tokens ─────────────────────────────────────────────────────────────
C = {
    # Surfaces — all dark now
    "shell":         "#0A0F1E",   # sidebar (unchanged)
    "shell_hover":   "#141B2D",
    "shell_border":  "#1E2A40",
    "bg":            "#0D1117",   # main page background (was #F4F6FA)
    "surface":       "#161B22",   # cards (was #FFFFFF)
    "surface2":      "#1C2128",   # secondary surface (was #F8FAFC)

    # Brand
    "blue":          "#2F81F7",   # brighter blue for dark bg
    "blue_light":    "#58A6FF",
    "blue_dim":      "rgba(47,129,247,0.12)",
    "teal":          "#3DC9B0",   # brighter teal for dark bg
    "teal_dim":      "rgba(61,201,176,0.12)",
    "gold":          "#F0B429",
    "gold_dim":      "rgba(240,180,41,0.12)",

    # Semantic — dark-mode versions
    "success":       "#3FB950",
    "success_bg":    "rgba(63,185,80,0.12)",
    "warning":       "#D29922",
    "warning_bg":    "rgba(210,153,34,0.12)",
    "danger":        "#F85149",
    "danger_bg":     "rgba(248,81,73,0.12)",
    "info":          "#2F81F7",
    "info_bg":       "rgba(47,129,247,0.12)",

    # Text — light on dark
    "text":          "#E6EDF3",   # primary text (was #091E42)
    "text2":         "#B1BAC4",   # secondary text (was #42526E)
    "text3":         "#8B949E",   # muted text (was #6B778C)
    "text_inv":      "#0D1117",   # inverted (for light bg elements)
    "text_inv2":     "rgba(13,17,23,0.65)",

    # Border / divider
    "border":        "#30363D",   # (was #DFE1E6)
    "border2":       "#21262D",   # (was #EBECF0)
    "divider":       "rgba(255,255,255,0.07)",
}

RISK_COLORS = {
    "Low":      C["success"],
    "Moderate": C["warning"],
    "High":     "#E3B341",
    "Critical": C["danger"],
}

RISK_BG = {
    "Low":      C["success_bg"],
    "Moderate": C["warning_bg"],
    "High":     "rgba(227,179,65,0.12)",
    "Critical": C["danger_bg"],
}

COLORS = {
    "navy":           C["shell"],
    "navy_light":     C["shell_hover"],
    "teal":           C["teal"],
    "teal_light":     "#56D4BB",
    "gold":           C["gold"],
    "gold_light":     "#F7C948",
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
    "sidebar_text":   C["text"],
}


# ── Global CSS ────────────────────────────────────────────────────────────────
def inject_global_css() -> None:
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

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
        --t-display: 2rem;
        --t-h1:      1.375rem;
        --t-h2:      1rem;
        --t-body:    0.875rem;
        --t-caption: 0.75rem;
        --t-micro:   0.6875rem;
        --sp-1:4px;--sp-2:8px;--sp-3:12px;--sp-4:16px;
        --sp-5:24px;--sp-6:32px;--sp-7:48px;--sp-8:64px;
        --r-sm:6px;--r-md:10px;--r-lg:14px;--r-xl:20px;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.04);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04);
        --shadow-lg: 0 8px 24px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05);
    }}

    *, *::before, *::after {{ box-sizing: border-box; }}

    html, body, .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        background-color: {C['bg']} !important;
        color: {C['text']} !important;
    }}

    /* Force dark bg on ALL Streamlit containers */
    .main .block-container,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"] {{
        background-color: {C['bg']} !important;
        color: {C['text']} !important;
    }}

    /* All text elements default to light */
    p, span, div, label, h1, h2, h3, h4, h5, h6 {{
        color: {C['text']};
    }}

    #MainMenu, footer, header {{ visibility:hidden !important; height:0 !important; }}
    .stDeployButton {{ display:none !important; }}

    .block-container {{
        padding: 32px 40px 64px 40px !important;
        max-width: 1440px !important;
        background-color: {C['bg']} !important;
    }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: {C['shell']} !important;
        border-right: 1px solid {C['shell_border']} !important;
        min-width: 252px !important;
        max-width: 252px !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding: 0 !important;
        background: {C['shell']} !important;
    }}
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown div,
    [data-testid="stSidebar"] .stMarkdown span {{
        color: rgba(255,255,255,0.55) !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: {C['shell_border']} !important;
        margin: 4px 16px !important;
    }}

    /* ── Sidebar nav radio ── */
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {{
        display: none !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] > div {{
        gap: 1px !important;
        background: transparent !important;
        padding: 0 8px !important;
    }}
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
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:first-child {{
        display: none !important;
    }}
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
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {{
        background: rgba(255,255,255,0.07) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked),
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-selected="true"] {{
        background: rgba(47,129,247,0.22) !important;
        border-left: 3px solid {C['blue']} !important;
        padding-left: 9px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) > div:last-child p,
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) > div:last-child,
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-selected="true"] > div:last-child p,
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-selected="true"] > div:last-child {{
        color: #ffffff !important;
        font-weight: 700 !important;
    }}
    .nav-group-label {{
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: rgba(255,255,255,0.28);
        padding: 12px 20px 2px 20px;
        margin: 0;
    }}

    /* ── Page header ── */
    .page-hero {{ margin-bottom: var(--sp-5); }}
    .page-title {{
        font-size: var(--t-h1);
        font-weight: 700;
        color: {C['text']};
        letter-spacing: -0.02em;
        line-height: 1.2;
        margin: 0 0 4px 0;
    }}
    .page-subtitle {{
        font-size: var(--t-body);
        color: {C['text2']};
        margin: 0;
        font-weight: 400;
    }}
    .page-divider {{
        height: 1px;
        background: {C['border']};
        margin: var(--sp-4) 0 var(--sp-5) 0;
    }}

    /* ── KPI Cards ── */
    .kpi-card {{
        background: {C['surface']};
        border-radius: var(--r-md);
        border: 1px solid {C['border']};
        box-shadow: var(--shadow-sm);
        padding: var(--sp-4) var(--sp-4) var(--sp-4) 0;
        display: flex;
        align-items: stretch;
        overflow: hidden;
        transition: box-shadow 0.18s ease, transform 0.18s ease;
        height: 100%;
    }}
    .kpi-card:hover {{ box-shadow: var(--shadow-md); transform: translateY(-1px); }}
    .kpi-accent {{ width:4px; border-radius:4px 0 0 4px; flex-shrink:0; margin-right:var(--sp-3); }}
    .kpi-body {{ flex:1; min-width:0; }}
    .kpi-label {{
        font-size: var(--t-micro);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: {C['text3']};
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: var(--t-display);
        font-weight: 800;
        color: {C['text']};
        line-height: 1.15;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
        margin-bottom: 4px;
        word-break: break-word;
    }}
    .kpi-sub {{ font-size: var(--t-caption); color: {C['text3']}; font-weight: 400; }}
    .kpi-icon {{
        width:36px; height:36px; border-radius:var(--r-sm);
        display:flex; align-items:center; justify-content:center;
        font-size:1.1rem; flex-shrink:0; align-self:flex-start; margin-right:var(--sp-3);
    }}

    /* ── Section headers ── */
    .section-header {{ display:flex; align-items:center; gap:8px; margin:24px 0 14px 0; }}
    .section-dot {{ width:3px; height:18px; background:{C['blue']}; border-radius:2px; flex-shrink:0; }}
    .section-title {{ font-size:var(--t-h2); font-weight:700; color:{C['text']}; letter-spacing:-0.01em; }}

    /* ── Badges ── */
    .badge {{
        display:inline-flex; align-items:center; gap:4px;
        padding:2px 9px; border-radius:20px;
        font-size:var(--t-micro); font-weight:700;
        letter-spacing:0.04em; text-transform:uppercase;
    }}
    .badge-success {{ background:{C['success_bg']}; color:{C['success']}; }}
    .badge-warning {{ background:{C['warning_bg']}; color:{C['warning']}; }}
    .badge-danger  {{ background:{C['danger_bg']};  color:{C['danger']};  }}
    .badge-info    {{ background:{C['info_bg']};    color:{C['info']};    }}
    .badge-neutral {{ background:{C['surface2']};   color:{C['text3']};   border:1px solid {C['border']}; }}

    /* ── Alert boxes ── */
    .info-box {{
        background: {C['info_bg']}; border-left:3px solid {C['info']};
        padding:12px 16px; border-radius:0 var(--r-sm) var(--r-sm) 0;
        margin:8px 0; font-size:var(--t-body); color:{C['text']}; line-height:1.5;
    }}
    .warning-box {{
        background: {C['warning_bg']}; border-left:3px solid {C['warning']};
        padding:12px 16px; border-radius:0 var(--r-sm) var(--r-sm) 0;
        margin:8px 0; font-size:var(--t-body); color:{C['text']}; line-height:1.5;
    }}
    .danger-box {{
        background: {C['danger_bg']}; border-left:3px solid {C['danger']};
        padding:12px 16px; border-radius:0 var(--r-sm) var(--r-sm) 0;
        margin:8px 0; font-size:var(--t-body); color:{C['text']}; line-height:1.5;
    }}
    .success-box {{
        background: {C['success_bg']}; border-left:3px solid {C['success']};
        padding:12px 16px; border-radius:0 var(--r-sm) var(--r-sm) 0;
        margin:8px 0; font-size:var(--t-body); color:{C['text']}; line-height:1.5;
    }}

    /* ── Empty state ── */
    .empty-state {{
        text-align:center; padding:48px 32px;
        background:{C['surface']}; border-radius:var(--r-lg);
        border:1px dashed {C['border']};
    }}
    .empty-icon {{ font-size:2.5rem; margin-bottom:12px; opacity:0.5; }}
    .empty-title {{ font-size:var(--t-h2); font-weight:700; color:{C['text']}; margin-bottom:6px; }}
    .empty-desc {{ font-size:var(--t-body); color:{C['text3']}; max-width:320px; margin:0 auto; line-height:1.5; }}

    /* ── Chat ── */
    .chat-bubble-user {{
        background: {C['blue']}; color: white;
        padding:10px 16px; border-radius:18px 18px 4px 18px;
        margin:6px 0 6px 15%; font-size:var(--t-body); line-height:1.55;
        box-shadow:0 2px 8px rgba(47,129,247,0.3);
    }}
    .chat-bubble-assistant {{
        background: {C['surface']}; color: {C['text']};
        padding:12px 16px; border-radius:18px 18px 18px 4px;
        margin:6px 15% 6px 0; font-size:var(--t-body); line-height:1.55;
        border:1px solid {C['border']}; box-shadow:var(--shadow-sm);
    }}
    .chat-meta {{ font-size:var(--t-micro); font-weight:600; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:5px; opacity:0.7; }}
    .chat-source {{ font-size:var(--t-micro); color:{C['text3']}; margin-top:6px; padding-top:6px; border-top:1px solid {C['border']}; }}
    .chat-thread {{ max-height:520px; overflow-y:auto; padding:8px 0; scroll-behavior:smooth; }}

    /* ── Checklist ── */
    .checklist-item {{
        display:flex; align-items:flex-start; gap:12px;
        padding:12px 16px; background:{C['surface']};
        border-radius:var(--r-md); margin:6px 0;
        border:1px solid {C['border']}; font-size:var(--t-body);
    }}
    .checklist-item:hover {{ border-color:{C['teal']}; }}
    .check-icon {{
        width:22px; height:22px; background:{C['teal_dim']}; color:{C['teal']};
        border-radius:50%; display:flex; align-items:center; justify-content:center;
        font-size:0.75rem; font-weight:700; flex-shrink:0; margin-top:1px;
    }}

    /* ── File upload ── */
    [data-testid="stFileUploader"] {{
        border:2px dashed {C['blue']} !important;
        border-radius:var(--r-lg) !important;
        background:{C['blue_dim']} !important;
        padding:8px !important;
    }}
    [data-testid="stFileUploader"]:hover {{
        border-color:{C['blue_light']} !important;
        background:rgba(47,129,247,0.08) !important;
    }}

    /* ── Buttons ── */
    .stButton > button {{
        font-family:'Inter',sans-serif !important;
        font-size:var(--t-body) !important;
        font-weight:600 !important;
        border-radius:var(--r-sm) !important;
        transition:all 0.15s ease !important;
    }}
    .stButton > button[kind="primary"] {{
        background:{C['blue']} !important;
        color:white !important; border:none !important;
        box-shadow:0 2px 6px rgba(47,129,247,0.35) !important;
        padding:0.55rem 1.5rem !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background:{C['blue_light']} !important;
        box-shadow:0 4px 12px rgba(47,129,247,0.45) !important;
        transform:translateY(-1px) !important;
    }}
    .stButton > button:not([kind="primary"]) {{
        background:{C['surface']} !important;
        border:1px solid {C['border']} !important;
        color:{C['text']} !important;
    }}
    .stButton > button:not([kind="primary"]):hover {{
        border-color:{C['blue']} !important;
        color:{C['blue']} !important;
        background:{C['blue_dim']} !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap:0; background:{C['surface2']};
        border-radius:var(--r-md) var(--r-md) 0 0;
        border:1px solid {C['border']}; border-bottom:none;
        padding:4px 4px 0 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius:var(--r-sm) var(--r-sm) 0 0;
        padding:8px 18px; font-weight:500;
        font-size:var(--t-caption); color:{C['text2']};
        border:none; background:transparent;
    }}
    .stTabs [aria-selected="true"] {{
        background:{C['surface']} !important;
        color:{C['blue']} !important;
        font-weight:700; box-shadow:0 -2px 0 {C['blue']} inset;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        background:{C['surface']};
        border:1px solid {C['border']}; border-top:none;
        border-radius:0 0 var(--r-md) var(--r-md);
        padding:var(--sp-4) !important;
    }}

    /* ── Expanders ── */
    [data-testid="stExpander"] {{
        border:1px solid {C['border']} !important;
        border-radius:var(--r-md) !important;
        background:{C['surface']} !important;
        box-shadow:var(--shadow-sm) !important;
        margin-bottom:6px !important;
    }}
    [data-testid="stExpander"]:hover {{ border-color:{C['blue']} !important; }}
    [data-testid="stExpander"] summary {{
        color:{C['text']} !important;
    }}

    /* ── Inputs ── */
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input {{
        font-family:'Inter',sans-serif !important;
        font-size:var(--t-body) !important;
        border:1px solid {C['border']} !important;
        border-radius:var(--r-sm) !important;
        background:{C['surface2']} !important;
        color:{C['text']} !important;
    }}
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stTextInput"] input:focus {{
        border-color:{C['blue']} !important;
        box-shadow:0 0 0 3px {C['blue_dim']} !important;
        outline:none !important;
    }}
    /* Input labels */
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stNumberInput"] label,
    [data-testid="stRadio"] label {{
        color:{C['text2']} !important;
        font-size:var(--t-caption) !important;
        font-weight:600 !important;
    }}

    /* ── Selectbox ── */
    [data-testid="stSelectbox"] > div > div {{
        border:1px solid {C['border']} !important;
        border-radius:var(--r-sm) !important;
        background:{C['surface2']} !important;
        color:{C['text']} !important;
        font-size:var(--t-body) !important;
    }}

    /* ── Number input ── */
    [data-testid="stNumberInput"] input {{
        background:{C['surface2']} !important;
        color:{C['text']} !important;
        border-color:{C['border']} !important;
    }}

    /* ── Radio buttons (main area, not sidebar) ── */
    .main [data-testid="stRadio"] > div > label > div:last-child {{
        color:{C['text']} !important;
    }}

    /* ── Slider ── */
    [data-testid="stSlider"] > div {{
        color:{C['text']} !important;
    }}

    /* ── Dataframe / table ── */
    [data-testid="stDataFrame"],
    .stDataFrame {{
        background:{C['surface']} !important;
        border:1px solid {C['border']} !important;
        border-radius:var(--r-md) !important;
    }}

    /* ── Divider ── */
    hr {{
        border:none !important;
        border-top:1px solid {C['border']} !important;
        margin:var(--sp-5) 0 !important;
    }}

    /* ── Progress ── */
    [data-testid="stProgress"] > div > div {{
        background:{C['blue']} !important; border-radius:4px !important;
    }}
    [data-testid="stProgress"] > div {{
        background:{C['border']} !important; border-radius:4px !important;
    }}

    /* ── Spinner ── */
    [data-testid="stSpinner"] {{ color:{C['blue']} !important; }}

    /* ── Metric ── */
    [data-testid="metric-container"] {{
        background:{C['surface']};
        border:1px solid {C['border']};
        border-radius:var(--r-md);
        padding:var(--sp-3) var(--sp-4);
        box-shadow:var(--shadow-sm);
    }}
    [data-testid="metric-container"] label {{
        color:{C['text3']} !important;
    }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{
        color:{C['text']} !important;
    }}

    /* ── Action items ── */
    .action-item {{
        display:flex; align-items:flex-start; gap:14px;
        padding:14px 16px; background:{C['surface']};
        border-radius:var(--r-md); border:1px solid {C['border']};
        margin:6px 0;
    }}
    .action-num {{
        width:28px; height:28px; border-radius:var(--r-sm);
        display:flex; align-items:center; justify-content:center;
        font-size:var(--t-caption); font-weight:800; flex-shrink:0; margin-top:1px;
    }}

    /* ── Cards ── */
    .doc-type-card {{
        background:{C['surface']}; border:1px solid {C['border']};
        border-radius:var(--r-md); padding:16px 12px;
        text-align:center; height:100%;
        transition:border-color 0.15s, box-shadow 0.15s;
    }}
    .doc-type-card:hover {{ border-color:{C['blue']}; box-shadow:var(--shadow-sm); }}
    .insight-card {{
        background:{C['surface']}; border:1px solid {C['border']};
        border-radius:var(--r-md); padding:16px; height:100%;
        box-shadow:var(--shadow-sm);
    }}
    .loan-card {{
        background:{C['surface']}; border:1px solid {C['border']};
        border-radius:var(--r-md); padding:var(--sp-4); margin:8px 0;
        box-shadow:var(--shadow-sm);
    }}
    .loan-card-header {{
        display:flex; align-items:center; gap:10px;
        margin-bottom:12px; padding-bottom:12px;
        border-bottom:1px solid {C['border2']};
    }}

    /* ── Activity item ── */
    .activity-item {{
        display:flex; justify-content:space-between; align-items:center;
        padding:10px 14px; background:{C['surface']};
        border-radius:var(--r-sm); margin:4px 0;
        border:1px solid {C['border2']}; font-size:var(--t-body);
    }}
    .activity-name {{ font-weight:500; color:{C['text']}; }}

    /* ── Step tracker ── */
    .step-row {{ display:flex; align-items:center; gap:0; margin:var(--sp-4) 0; }}
    .step-item {{ display:flex; flex-direction:column; align-items:center; flex:1; position:relative; }}
    .step-circle {{
        width:32px; height:32px; border-radius:50%;
        display:flex; align-items:center; justify-content:center;
        font-size:var(--t-micro); font-weight:700; z-index:1; position:relative;
    }}
    .step-circle.done   {{ background:{C['teal']}; color:white; }}
    .step-circle.active {{ background:{C['blue']}; color:white; box-shadow:0 0 0 4px {C['blue_dim']}; }}
    .step-circle.idle   {{ background:{C['surface2']}; color:{C['text3']}; border:2px solid {C['border']}; }}
    .step-label {{ font-size:var(--t-micro); font-weight:600; color:{C['text3']}; margin-top:4px; text-align:center; text-transform:uppercase; letter-spacing:0.06em; }}
    .step-label.active {{ color:{C['blue']}; }}
    .step-label.done   {{ color:{C['teal']}; }}
    .step-connector {{ flex:1; height:2px; background:{C['border']}; margin-top:-16px; z-index:0; }}
    .step-connector.done {{ background:{C['teal']}; }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width:6px; height:6px; }}
    ::-webkit-scrollbar-track {{ background:transparent; }}
    ::-webkit-scrollbar-thumb {{ background:{C['border']}; border-radius:3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background:{C['text3']}; }}
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
    sub:   str = "",
    color: str = "",
    accent: str = "",
    icon:  str = "",
    icon_bg: str = "",
) -> str:
    accent_color = accent or color or C["blue"]
    value_len = len(value)
    if value_len <= 6:      size = "var(--t-display)"
    elif value_len <= 12:   size = "1.35rem"
    elif value_len <= 18:   size = "1.1rem"
    else:                   size = "0.95rem"
    value_style = f"font-size:{size};"
    if color:               value_style += f"color:{color};"
    _icon_bg  = icon_bg or C["blue_dim"]
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
        f"<span style='font-size:var(--t-body);color:{C['text']};line-height:1.5'>{text}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def step_tracker(steps: list[str], current: int) -> None:
    parts = ["<div class='step-row'>"]
    for i, label in enumerate(steps):
        if i < current:
            circle_cls, label_cls, num = "done",   "done",   "✓"
        elif i == current:
            circle_cls, label_cls, num = "active", "active", str(i + 1)
        else:
            circle_cls, label_cls, num = "idle",   "",       str(i + 1)
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
