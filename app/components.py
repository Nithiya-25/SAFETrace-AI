"""
components.py
--------------
Reusable Streamlit UI components shared across pages:
header banner, stat cards, evidence cards, lead cards, error banners,
loading helpers, and the "Potential Lead" disclaimer.
"""

import textwrap
from datetime import datetime
import streamlit as st
from styles import priority_badge_html, status_badge_html
from api_client import BackendUnavailableError, APIError


def _html(markup: str) -> str:
    """
    Streamlit's markdown renderer treats any line indented 4+ spaces as a
    code block, which causes raw HTML tags to print literally instead of
    rendering. This strips that indentation before we hand markup to
    st.markdown(..., unsafe_allow_html=True).
    """
    return textwrap.dedent(markup).strip()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def render_header(title="SAFETrace AI", subtitle="Investigation Intelligence Dashboard"):
    stamp = datetime.now().strftime("%d %b %Y — %H:%M")
    st.markdown(
        _html(f"""
            <div class="safetrace-header">
                <div class="header-text">
                    <h1>{title}</h1>
                    <p>{subtitle}</p>
                </div>
                <div class="header-stamp">SESSION {stamp}</div>
            </div>
        """),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Stat cards row
# ---------------------------------------------------------------------------
def render_stat_cards(stats: list):
    """
    stats: list of (label, value) tuples
    """
    cols = st.columns(len(stats))
    for col, (label, value) in zip(cols, stats):
        with col:
            st.markdown(
                _html(f"""
                    <div class="stat-card">
                        <div class="stat-label">{label}</div>
                        <div class="stat-value">{value}</div>
                    </div>
                """),
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Error / status banners
# ---------------------------------------------------------------------------
def render_backend_unavailable():
    st.error("⚠️ Backend unavailable.\n\nPlease check that the SAFETrace API is running.")


def render_error(message: str):
    st.error(f"❌ {message}")


def handle_api_exception(e: Exception, fallback_message="Something went wrong."):
    if isinstance(e, BackendUnavailableError):
        render_backend_unavailable()
    elif isinstance(e, APIError):
        render_error(str(e))
    else:
        render_error(fallback_message)


# ---------------------------------------------------------------------------
# Evidence card
# ---------------------------------------------------------------------------
def render_evidence_card(evidence: dict, on_verify=None, on_reject=None, key_prefix=""):
    """
    evidence: dict with keys like evidence_id, camera_id, location, timestamp,
              track_id, confidence, lead_score, status, crop_image_path/url
    """
    evidence_id = evidence.get("evidence_id", evidence.get("id", "—"))
    camera = evidence.get("camera_id", evidence.get("camera", "—"))
    location = evidence.get("location", "—")
    timestamp = evidence.get("timestamp", "—")
    track_id = evidence.get("track_id", "—")
    confidence = evidence.get("confidence", evidence.get("detection_confidence"))
    lead_score = evidence.get("lead_score")
    status = evidence.get("status", "Pending Review")
    image_url = evidence.get("crop_image_url") or evidence.get("crop_image_path")

    with st.container():
        st.markdown('<div class="evidence-card">', unsafe_allow_html=True)

        col_img, col_info = st.columns([1, 2])
        with col_img:
            if image_url:
                try:
                    st.image(image_url, use_container_width=True)
                except Exception:
                    st.markdown("*Image unavailable*")
            else:
                st.markdown("*No image available*")

        with col_info:
            st.markdown(f'<div class="evidence-id">EXHIBIT {evidence_id}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="evidence-field"><b>Camera:</b> <span class="mono-value">{camera}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="evidence-field"><b>Location:</b> {location}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="evidence-field"><b>Timestamp:</b> <span class="mono-value">{timestamp}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="evidence-field"><b>Track ID:</b> <span class="mono-value">{track_id}</span></div>', unsafe_allow_html=True)
            if confidence is not None:
                st.markdown(f'<div class="evidence-field"><b>Detection Confidence:</b> <span class="mono-value">{confidence}%</span></div>', unsafe_allow_html=True)
            if lead_score is not None:
                st.markdown(f'<div class="evidence-field"><b>Lead Score:</b> <span class="mono-value">{lead_score} / 100</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div style="margin-top:0.4rem;">{status_badge_html(status)}</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="disclaimer-box">Potential Lead — Requires Investigator Verification</div>',
            unsafe_allow_html=True,
        )

        if status == "Pending Review":
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("✅ VERIFY", key=f"{key_prefix}_verify_{evidence_id}", use_container_width=True):
                    if on_verify:
                        on_verify(evidence_id)
            with btn_col2:
                if st.button("❌ REJECT", key=f"{key_prefix}_reject_{evidence_id}", use_container_width=True):
                    if on_reject:
                        on_reject(evidence_id)
        elif status == "Verified":
            st.success("Investigator Verified Evidence")
        elif status == "Rejected":
            st.warning("Investigator Rejected Evidence")

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Lead card
# ---------------------------------------------------------------------------
def render_lead_card(lead: dict):
    """
    lead: dict with keys like evidence_id, lead_score, priority, camera_id,
          timestamp, reason (list[str] or str, optional — from backend only)
    """
    evidence_id = lead.get("evidence_id", lead.get("id", "—"))
    score = lead.get("lead_score", lead.get("score", "—"))
    priority = lead.get("priority", "LOW")
    camera = lead.get("camera_id", lead.get("camera", "—"))
    timestamp = lead.get("timestamp", "—")
    reason = lead.get("reason")

    with st.container():
        st.markdown('<div class="evidence-card">', unsafe_allow_html=True)
        header_col1, header_col2 = st.columns([3, 1])
        with header_col1:
            st.markdown(f'<div class="evidence-id">EXHIBIT {evidence_id}</div>', unsafe_allow_html=True)
        with header_col2:
            st.markdown(priority_badge_html(priority), unsafe_allow_html=True)

        st.markdown(f'<div class="evidence-field"><b>Lead Score:</b> <span class="mono-value">{score} / 100</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="evidence-field"><b>Camera:</b> <span class="mono-value">{camera}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="evidence-field"><b>Time:</b> <span class="mono-value">{timestamp}</span></div>', unsafe_allow_html=True)

        if reason:
            st.markdown('<div class="evidence-field"><b>Why this lead?</b></div>', unsafe_allow_html=True)
            if isinstance(reason, list):
                for r in reason:
                    st.markdown(f'<div class="evidence-field">✓ {r}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="evidence-field">✓ {reason}</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="disclaimer-box">HIGH PRIORITY POTENTIAL LEAD — Requires Investigator Verification</div>'
            if priority.upper() == "HIGH"
            else '<div class="disclaimer-box">Potential Lead — Requires Investigator Verification</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Section title helper
# ---------------------------------------------------------------------------
def section_title(text: str):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)
