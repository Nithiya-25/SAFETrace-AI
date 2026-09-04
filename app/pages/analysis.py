"""
pages/analysis.py
-------------------
CCTV video upload + analysis trigger + result display.
"""

import streamlit as st
import api_client
from components import render_header, section_title, handle_api_exception
from api_client import BackendUnavailableError, APIError


def render():
    render_header("🎥 CCTV Analysis", "Upload and analyze CCTV footage")

    with st.spinner("Loading cases..."):
        try:
            cases = api_client.get_cases()
        except Exception as e:
            handle_api_exception(e, "Could not load cases.")
            return

    if not cases:
        st.info("No cases available. Create a case first from **➕ Create Case**.")
        return

    id_col = "case_id" if "case_id" in cases[0] else "id"
    case_options = {c[id_col]: c.get("name", c[id_col]) for c in cases}

    selected_case_id = st.selectbox(
        "Select Case",
        list(case_options.keys()),
        format_func=lambda cid: f"{cid} — {case_options[cid]}",
    )

    camera_id = st.text_input("Camera ID", placeholder="e.g. CAM-03")
    location = st.text_input("Location", placeholder="e.g. Demo Railway Station")
    video_file = st.file_uploader("Upload CCTV Video", type=["mp4", "avi", "mov", "mkv"])

    analyze_clicked = st.button("ANALYZE VIDEO", use_container_width=True)

    if analyze_clicked:
        if not video_file or not camera_id or not location:
            st.warning("Please provide Camera ID, Location, and a video file.")
            return

        try:
            with st.spinner("Uploading CCTV video..."):
                video_result = api_client.create_video(selected_case_id, camera_id, location, video_file)
            st.success("✓ Video uploaded")

            video_id = (video_result or {}).get("video_id", (video_result or {}).get("id"))

            with st.spinner("Analyzing CCTV footage..."):
                analysis_result = api_client.analyze_video(
                    video_id=video_id,
                    case_id=selected_case_id,
                    camera_id=camera_id,
                    location=location,
                )

            st.success("Analysis Complete")
            render_analysis_result(analysis_result, video_file.name, camera_id, location)

        except BackendUnavailableError as e:
            handle_api_exception(e)
        except APIError as e:
            st.error("❌ CCTV analysis failed.\nPlease try again.")
            st.caption(str(e))
        except Exception:
            st.error("❌ CCTV analysis failed.\nPlease try again.")


def render_analysis_result(result: dict, video_name: str, camera_id: str, location: str):
    result = result or {}
    section_title("Analysis Completed")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Video:** {video_name}")
        st.markdown(f"**Camera:** {camera_id}")
        st.markdown(f"**Location:** {location}")
    with col2:
        st.markdown(f"**People Tracked:** {result.get('people_tracked', '—')}")
        st.markdown(f"**Potential Leads:** {result.get('potential_leads', '—')}")

    lcol1, lcol2, lcol3 = st.columns(3)
    with lcol1:
        st.metric("High Priority", result.get("high_priority", "—"))
    with lcol2:
        st.metric("Medium Priority", result.get("medium_priority", "—"))
    with lcol3:
        st.metric("Low Priority", result.get("low_priority", "—"))

    annotated_video_url = result.get("annotated_video_url") or result.get("annotated_video_path")
    if annotated_video_url:
        section_title("Annotated CCTV Video")
        try:
            st.video(annotated_video_url)
        except Exception:
            st.caption(f"Annotated video available at: {annotated_video_url}")

    st.caption("View full evidence and leads from the **🔎 Evidence** and **🚨 Priority Leads** pages.")
