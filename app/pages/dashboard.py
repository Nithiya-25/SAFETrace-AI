"""
pages/dashboard.py
-------------------
Main landing page: overview stats, recent cases, high priority leads, recent evidence.
"""

import streamlit as st
import api_client
from components import render_header, render_stat_cards, section_title, handle_api_exception, render_lead_card


def render():
    render_header()

    # --- Stats row ---
    with st.spinner("Loading dashboard statistics..."):
        try:
            stats = api_client.get_dashboard_stats()
            cases = api_client.get_cases()
        except Exception as e:
            handle_api_exception(e, "Could not load dashboard statistics.")
            stats, cases = None, []

    if stats:
        active_cases = stats.get("active_cases", len(cases))
        videos_analyzed = stats.get("videos_analyzed", "—")
        evidence_generated = stats.get("evidence_generated", "—")
        high_leads = stats.get("high_priority_leads", "—")
    else:
        active_cases = len(cases) if cases else 0
        videos_analyzed = "—"
        evidence_generated = "—"
        high_leads = "—"

    render_stat_cards(
        [
            ("Active Cases", active_cases),
            ("Videos Analyzed", videos_analyzed),
            ("Evidence Generated", evidence_generated),
            ("High Priority Leads", high_leads),
        ]
    )

    # --- Recent cases ---
    section_title("📁 Recent Cases")
    if cases:
        import pandas as pd
        df = pd.DataFrame(cases)
        display_cols = [c for c in ["case_id", "name", "last_seen_location", "status"] if c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols].head(5), use_container_width=True, hide_index=True)
        else:
            st.dataframe(df.head(5), use_container_width=True, hide_index=True)
    else:
        st.info("No cases yet. Create one from the **➕ Create Case** page.")

    # --- High priority leads (best-effort, across most recent case) ---
    section_title("🚨 High Priority Leads")
    if cases:
        try:
            latest_case = cases[0]
            case_id = latest_case.get("case_id", latest_case.get("id"))
            leads = api_client.get_leads(case_id) if case_id else []
            high = [l for l in leads if str(l.get("priority", "")).upper() == "HIGH"]
            if high:
                for lead in high[:3]:
                    render_lead_card(lead)
            else:
                st.info("No high priority leads for the most recent case yet.")
        except Exception as e:
            handle_api_exception(e, "Could not load leads.")
    else:
        st.info("Leads will appear here once cases have been analyzed.")
