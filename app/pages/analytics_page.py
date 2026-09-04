"""
pages/analytics_page.py
--------------------------
Simple analytics: aggregate stats + priority distribution + status charts.
Named analytics_page.py (not analytics.py) to avoid shadowing any
third-party `analytics` package.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import api_client
from components import render_header, render_stat_cards, section_title, handle_api_exception
from styles import COLOR_HIGH, COLOR_MEDIUM, COLOR_LOW, COLOR_PENDING, COLOR_VERIFIED, COLOR_REJECTED


def render():
    render_header("📊 Analytics", "Case & Evidence Statistics")

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

    # Aggregate evidence + leads across all cases (best-effort)
    all_evidence, all_leads = [], []
    with st.spinner("Aggregating analytics..."):
        for c in cases:
            cid = c.get(id_col)
            if not cid:
                continue
            try:
                all_evidence.extend(api_client.get_evidence(cid) or [])
            except Exception:
                pass
            try:
                all_leads.extend(api_client.get_leads(cid) or [])
            except Exception:
                pass

    total_cases = len(cases)
    total_evidence = len(all_evidence)
    high_leads = len([l for l in all_leads if str(l.get("priority", "")).upper() == "HIGH"])
    verified = len([e for e in all_evidence if e.get("status") == "Verified"])
    rejected = len([e for e in all_evidence if e.get("status") == "Rejected"])

    render_stat_cards(
        [
            ("Total Cases", total_cases),
            ("Total Evidence", total_evidence),
            ("High Priority Leads", high_leads),
            ("Verified", verified),
        ]
    )

    col1, col2 = st.columns(2)

    with col1:
        section_title("Priority Distribution")
        if all_leads:
            priority_df = pd.DataFrame(all_leads)
            priority_df["priority"] = priority_df.get("priority", pd.Series(dtype=str)).str.upper()
            counts = priority_df["priority"].value_counts().reindex(["HIGH", "MEDIUM", "LOW"]).fillna(0)
            fig = px.bar(
                x=counts.index,
                y=counts.values,
                labels={"x": "Priority", "y": "Count"},
                color=counts.index,
                color_discrete_map={"HIGH": COLOR_HIGH, "MEDIUM": COLOR_MEDIUM, "LOW": COLOR_LOW},
            )
            fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No lead data yet.")

    with col2:
        section_title("Evidence Status")
        if all_evidence:
            status_df = pd.DataFrame(all_evidence)
            if "status" in status_df.columns:
                counts = status_df["status"].value_counts()
                fig = px.pie(
                    names=counts.index,
                    values=counts.values,
                    color=counts.index,
                    color_discrete_map={
                        "Pending Review": COLOR_PENDING,
                        "Verified": COLOR_VERIFIED,
                        "Rejected": COLOR_REJECTED,
                    },
                )
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No status data yet.")
        else:
            st.info("No evidence data yet.")
