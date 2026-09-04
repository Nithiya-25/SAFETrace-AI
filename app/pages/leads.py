"""
pages/leads.py
----------------
Priority leads page — grouped by HIGH / MEDIUM / LOW, with score explanations.
"""

import streamlit as st
import api_client
from components import render_header, section_title, handle_api_exception, render_lead_card


def render():
    render_header("🚨 Priority Leads", "AI-Prioritized Investigation Leads")

    with st.spinner("Loading cases..."):
        try:
            cases = api_client.get_cases()
        except Exception as e:
            handle_api_exception(e, "Could not load cases.")
            return

    if not cases:
        st.info("No cases available yet.")
        return

    id_col = "case_id" if "case_id" in cases[0] else "id"
    case_options = {c[id_col]: c.get("name", c[id_col]) for c in cases}
    selected_case_id = st.selectbox(
        "Select Case",
        list(case_options.keys()),
        format_func=lambda cid: f"{cid} — {case_options[cid]}",
    )

    with st.spinner("Retrieving priority leads..."):
        try:
            leads = api_client.get_leads(selected_case_id)
        except Exception as e:
            handle_api_exception(e, "Could not load leads.")
            return

    if not leads:
        st.info("No leads found for this case yet. Run CCTV Analysis first.")
        return

    priority_filter = st.selectbox("Priority", ["All", "HIGH", "MEDIUM", "LOW"])

    filtered = leads if priority_filter == "All" else [
        l for l in leads if str(l.get("priority", "")).upper() == priority_filter
    ]

    if not filtered:
        st.info("No leads match the selected priority.")
        return

    for priority in ["HIGH", "MEDIUM", "LOW"]:
        group = [l for l in filtered if str(l.get("priority", "")).upper() == priority]
        if not group:
            continue
        group_sorted = sorted(group, key=lambda l: l.get("lead_score", l.get("score", 0)), reverse=True)
        section_title(f"{priority} PRIORITY")
        for lead in group_sorted:
            render_lead_card(lead)
