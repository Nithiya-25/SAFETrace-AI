"""
pages/cases.py
---------------
Case list page + case details view.
"""

import streamlit as st
import pandas as pd
import api_client
from components import render_header, section_title, handle_api_exception


def render():
    render_header("📁 Cases", "All Missing-Person Cases")

    with st.spinner("Loading cases..."):
        try:
            cases = api_client.get_cases()
        except Exception as e:
            handle_api_exception(e, "Could not load cases.")
            return

    if not cases:
        st.info("No cases found. Create one from the **➕ Create Case** page.")
        return

    df = pd.DataFrame(cases)
    id_col = "case_id" if "case_id" in df.columns else "id"

    section_title("Case List")
    display_cols = [c for c in ["case_id", "name", "last_seen_location", "status", "created_at"] if c in df.columns]
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True, hide_index=True)

    section_title("View Case Details")
    case_ids = df[id_col].tolist() if id_col in df.columns else []
    if not case_ids:
        return

    selected_id = st.selectbox("Select Case", case_ids)
    if not selected_id:
        return

    with st.spinner("Loading case details..."):
        try:
            case = api_client.get_case(selected_id)
        except Exception as e:
            handle_api_exception(e, "Could not load case details.")
            return

    if not case:
        st.warning("Case not found.")
        return

    render_case_details(case)


def render_case_details(case: dict):
    st.markdown(f"### CASE {case.get('case_id', case.get('id', '—'))}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {case.get('name', '—')}")
        st.markdown(f"**Age:** {case.get('age', '—')}")
        st.markdown(f"**Gender:** {case.get('gender', '—')}")
        st.markdown(f"**Status:** {case.get('status', '—')}")
    with col2:
        st.markdown(f"**Last Seen Location:** {case.get('last_seen_location', '—')}")
        st.markdown(f"**Last Seen Time:** {case.get('last_seen_time', '—')}")
        st.markdown(f"**Created:** {case.get('created_at', '—')}")

    if case.get("description"):
        st.markdown(f"**Description:** {case.get('description')}")

    ref_image = case.get("reference_image_url") or case.get("reference_image_path")
    if ref_image:
        st.image(ref_image, caption="Reference Image", width=200)

    st.markdown("---")
    st.caption("Use the sidebar to view CCTV Analysis, Evidence, and Priority Leads for this case.")
