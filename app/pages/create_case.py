"""
pages/create_case.py
----------------------
Form for creating a new missing-person case.
"""

import streamlit as st
import api_client
from components import render_header, handle_api_exception
from api_client import BackendUnavailableError, APIError


def render():
    render_header("➕ Create Missing-Person Case", "Register a new investigation case")

    with st.form("create_case_form", clear_on_submit=False):
        name = st.text_input("Name", placeholder="e.g. Demo Person")
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=0, max_value=120, step=1)
        with col2:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])

        last_seen_location = st.text_input("Last Seen Location", placeholder="e.g. Demo Railway Station")
        last_seen_time = st.text_input("Last Seen Time", placeholder="e.g. 08:15")
        description = st.text_area("Description", placeholder="e.g. Blue shirt and black trousers")
        reference_image = st.file_uploader("Reference Image", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("CREATE CASE", use_container_width=True)

    if submitted:
        if not name or not last_seen_location:
            st.warning("Please fill in at least Name and Last Seen Location.")
            return

        payload = {
            "name": name,
            "age": int(age),
            "gender": gender,
            "last_seen_location": last_seen_location,
            "last_seen_time": last_seen_time,
            "description": description,
        }

        with st.spinner("Creating case..."):
            try:
                result = api_client.create_case(payload, image_file=reference_image)
            except BackendUnavailableError as e:
                handle_api_exception(e)
                return
            except APIError as e:
                st.error("❌ Case could not be created.")
                st.caption(str(e))
                return
            except Exception:
                st.error("❌ Case could not be created.")
                return

        case_id = (result or {}).get("case_id", (result or {}).get("id", "—"))
        status = (result or {}).get("status", "Active")

        st.success("Case Created Successfully")
        st.markdown(f"**Case ID:** {case_id}")
        st.markdown(f"**Status:** {status}")
