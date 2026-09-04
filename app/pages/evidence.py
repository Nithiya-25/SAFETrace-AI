"""
pages/evidence.py
-------------------
Evidence browsing page: cards, table toggle, filters, verify/reject actions.
"""

import streamlit as st
import pandas as pd
import api_client
from components import render_header, section_title, handle_api_exception, render_evidence_card
from api_client import BackendUnavailableError, APIError


def render():
    render_header("🔎 Evidence", "Potential Evidence Review")

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

    with st.spinner("Loading evidence..."):
        try:
            evidence_list = api_client.get_evidence(selected_case_id)
        except Exception as e:
            handle_api_exception(e, "Could not load evidence.")
            return

    if not evidence_list:
        st.info("No evidence found for this case yet. Run CCTV Analysis first.")
        return

    # --- Filters ---
    section_title("Filters")
    fcol1, fcol2, fcol3 = st.columns(3)
    df = pd.DataFrame(evidence_list)

    with fcol1:
        status_options = ["All"] + sorted(df["status"].dropna().unique().tolist()) if "status" in df.columns else ["All"]
        status_filter = st.selectbox("Status", status_options)
    with fcol2:
        camera_col = "camera_id" if "camera_id" in df.columns else "camera"
        camera_options = ["All"] + sorted(df[camera_col].dropna().unique().tolist()) if camera_col in df.columns else ["All"]
        camera_filter = st.selectbox("Camera", camera_options)
    with fcol3:
        view_mode = st.radio("View", ["Cards", "Table"], horizontal=True)

    filtered = evidence_list
    if status_filter != "All":
        filtered = [e for e in filtered if e.get("status") == status_filter]
    if camera_filter != "All":
        filtered = [e for e in filtered if e.get("camera_id", e.get("camera")) == camera_filter]

    section_title(f"Evidence ({len(filtered)})")

    if not filtered:
        st.info("No evidence matches the selected filters.")
        return

    if view_mode == "Table":
        st.dataframe(pd.DataFrame(filtered), use_container_width=True, hide_index=True)
        return

    def handle_verify(evidence_id):
        _update_status(evidence_id, "Verified")

    def handle_reject(evidence_id):
        _update_status(evidence_id, "Rejected")

    for evidence in filtered:
        render_evidence_card(evidence, on_verify=handle_verify, on_reject=handle_reject, key_prefix="ev")


def _update_status(evidence_id, status):
    try:
        with st.spinner(f"Updating evidence {evidence_id}..."):
            api_client.update_evidence_status(evidence_id, status)
        st.success(f"Evidence {evidence_id} marked as {status}")
        st.rerun()
    except BackendUnavailableError as e:
        handle_api_exception(e)
    except APIError as e:
        st.error(f"❌ Could not update evidence status.")
        st.caption(str(e))
    except Exception:
        st.error("❌ Could not update evidence status.")
