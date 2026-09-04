"""
streamlit_app.py
------------------
Entry point for the SAFETrace AI Investigator Dashboard.

Run with:
    streamlit run app/streamlit_app.py
"""

import sys
import os
import streamlit as st

# Ensure local imports (api_client, components, styles, pages/*) resolve
# regardless of the working directory Streamlit is launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from styles import inject_global_css
import api_client

st.set_page_config(
    page_title="SAFETrace AI — Investigator Dashboard",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.markdown("## SAFETrace AI")
st.sidebar.caption("Investigator Dashboard")
st.sidebar.markdown("---")
st.sidebar.markdown("### Navigation")

PAGES = {
    "🏠 Dashboard": "dashboard",
    "📁 Cases": "cases",
    "➕ Create Case": "create_case",
    "🎥 CCTV Analysis": "analysis",
    "🔎 Evidence": "evidence",
    "🚨 Priority Leads": "leads",
    "📊 Analytics": "analytics_page",
}

selection = st.sidebar.radio("Go to", list(PAGES.keys()), label_visibility="collapsed")

st.sidebar.markdown("---")

# Backend connectivity indicator
backend_ok = api_client.check_backend_health()
if backend_ok:
    st.sidebar.success("🟢 Backend Connected")
else:
    st.sidebar.error("🔴 Backend Unavailable")
st.sidebar.caption(f"URL: {api_client.BACKEND_URL}")

# ---------------------------------------------------------------------------
# Route to selected page
# ---------------------------------------------------------------------------
module_name = PAGES[selection]

if module_name == "dashboard":
    from pages import dashboard as page
elif module_name == "cases":
    from pages import cases as page
elif module_name == "create_case":
    from pages import create_case as page
elif module_name == "analysis":
    from pages import analysis as page
elif module_name == "evidence":
    from pages import evidence as page
elif module_name == "leads":
    from pages import leads as page
elif module_name == "analytics_page":
    from pages import analytics_page as page
else:
    page = None

if page:
    page.render()
