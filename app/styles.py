"""
styles.py
---------
Design system for SAFETrace AI: a "case-file / evidence-board" visual
identity — dark investigation-room base, an amber case-flag accent, and a
functional type split (Space Grotesk for headings, IBM Plex Sans for UI
copy, IBM Plex Mono for anything an investigator reads as exact data:
IDs, timestamps, track numbers, scores).
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
COLOR_BG = "#0B0E14"            # base background — charcoal, not pure black
COLOR_PANEL = "#12161F"         # card / panel surface
COLOR_PANEL_RAISED = "#161B26"  # slightly lifted surface (hover state)
COLOR_BORDER = "#232838"        # hairline border
COLOR_BORDER_STRONG = "#323A50"

COLOR_ACCENT = "#E8A33D"        # amber "case-flag" accent — primary interactive color
COLOR_ACCENT_DIM = "#8A6529"

COLOR_HIGH = "#E5484D"          # HIGH priority / rejected — red
COLOR_MEDIUM = "#D9A441"        # MEDIUM priority — gold
COLOR_LOW = "#4C9A6A"           # LOW priority / verified — green
COLOR_PENDING = "#8890A0"       # neutral / pending review
COLOR_VERIFIED = COLOR_LOW      # alias — verified evidence uses the same green
COLOR_REJECTED = COLOR_HIGH     # alias — rejected evidence uses the same red

TEXT_PRIMARY = "#E4E7ED"
TEXT_MUTED = "#8890A0"
TEXT_FAINT = "#5A6274"

PRIORITY_COLORS = {
    "HIGH": COLOR_HIGH,
    "MEDIUM": COLOR_MEDIUM,
    "LOW": COLOR_LOW,
}

STATUS_COLORS = {
    "Pending Review": COLOR_PENDING,
    "Verified": COLOR_LOW,
    "Rejected": COLOR_HIGH,
}

FONT_DISPLAY = "'Space Grotesk', sans-serif"
FONT_BODY = "'IBM Plex Sans', sans-serif"
FONT_MONO = "'IBM Plex Mono', monospace"


def inject_global_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: {FONT_BODY};
        }}

        .stApp {{
            background-color: {COLOR_BG};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {COLOR_PANEL};
            border-right: 1px solid {COLOR_BORDER};
        }}

        /* ---- Case-file header ---- */
        .safetrace-header {{
            background-color: {COLOR_PANEL};
            border: 1px solid {COLOR_BORDER};
            border-left: 4px solid {COLOR_ACCENT};
            border-radius: 4px;
            padding: 1.3rem 1.6rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.6rem;
        }}
        .safetrace-header .header-text h1 {{
            font-family: {FONT_DISPLAY};
            color: {TEXT_PRIMARY};
            margin: 0;
            font-size: 1.7rem;
            font-weight: 700;
            letter-spacing: 0.2px;
        }}
        .safetrace-header .header-text p {{
            color: {TEXT_MUTED};
            margin: 0.2rem 0 0 0;
            font-size: 0.92rem;
        }}
        .safetrace-header .header-stamp {{
            font-family: {FONT_MONO};
            color: {COLOR_ACCENT};
            font-size: 0.78rem;
            border: 1px solid {COLOR_ACCENT_DIM};
            padding: 0.25rem 0.55rem;
            border-radius: 3px;
            white-space: nowrap;
        }}

        /* ---- Stat cards ---- */
        .stat-card {{
            background-color: {COLOR_PANEL};
            border: 1px solid {COLOR_BORDER};
            border-top: 2px solid {COLOR_ACCENT};
            border-radius: 4px;
            padding: 1rem 1.1rem;
            text-align: left;
        }}
        .stat-card .stat-label {{
            color: {TEXT_MUTED};
            font-size: 0.75rem;
            letter-spacing: 0.4px;
            margin-bottom: 0.35rem;
        }}
        .stat-card .stat-value {{
            font-family: {FONT_MONO};
            color: {TEXT_PRIMARY};
            font-size: 1.9rem;
            font-weight: 600;
        }}

        /* ---- Evidence / lead card (exhibit-tag styling) ---- */
        .evidence-card {{
            background-color: {COLOR_PANEL};
            border: 1px solid {COLOR_BORDER};
            border-left: 3px solid {COLOR_BORDER_STRONG};
            border-radius: 4px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
            transition: border-left-color 0.15s ease, background-color 0.15s ease;
        }}
        .evidence-card:hover {{
            border-left-color: {COLOR_ACCENT};
            background-color: {COLOR_PANEL_RAISED};
        }}
        .evidence-card .evidence-id {{
            font-family: {FONT_MONO};
            color: {TEXT_PRIMARY};
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.45rem;
            letter-spacing: 0.2px;
        }}
        .evidence-field {{
            color: {TEXT_MUTED};
            font-size: 0.85rem;
            margin: 0.2rem 0;
        }}
        .evidence-field b {{
            color: {TEXT_PRIMARY};
            font-weight: 500;
        }}
        .evidence-field .mono-value {{
            font-family: {FONT_MONO};
            color: {TEXT_PRIMARY};
        }}

        /* ---- Badges (status / priority tags) ---- */
        .badge {{
            display: inline-block;
            padding: 0.18rem 0.6rem;
            border-radius: 3px;
            font-family: {FONT_MONO};
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.3px;
        }}

        /* ---- Section titles ---- */
        .section-title {{
            font-family: {FONT_DISPLAY};
            color: {TEXT_PRIMARY};
            font-size: 1.1rem;
            font-weight: 600;
            margin: 1.3rem 0 0.7rem 0;
            padding-left: 0.65rem;
            border-left: 3px solid {COLOR_ACCENT};
        }}

        /* ---- Disclaimer box ---- */
        .disclaimer-box {{
            background-color: rgba(232, 163, 61, 0.06);
            border: 1px dashed {COLOR_ACCENT_DIM};
            border-radius: 3px;
            padding: 0.55rem 0.85rem;
            color: {TEXT_MUTED};
            font-size: 0.8rem;
            margin-top: 0.6rem;
            font-style: italic;
        }}

        /* ---- Buttons: sharpen the default Streamlit look ---- */
        .stButton > button {{
            font-family: {FONT_BODY};
            border-radius: 3px;
            border: 1px solid {COLOR_BORDER_STRONG};
            font-weight: 500;
        }}
        .stButton > button:hover {{
            border-color: {COLOR_ACCENT};
            color: {COLOR_ACCENT};
        }}

        /* ---- Dataframes / metrics ---- */
        [data-testid="stMetricValue"] {{
            font-family: {FONT_MONO};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def priority_badge_html(priority: str) -> str:
    color = PRIORITY_COLORS.get(priority.upper(), COLOR_PENDING)
    return (
        f'<span class="badge" style="background-color:{color}1A;'
        f'color:{color};border:1px solid {color}55;">{priority.upper()}</span>'
    )


def status_badge_html(status: str) -> str:
    color = STATUS_COLORS.get(status, COLOR_PENDING)
    return (
        f'<span class="badge" style="background-color:{color}1A;'
        f'color:{color};border:1px solid {color}55;">{status.upper()}</span>'
    )
