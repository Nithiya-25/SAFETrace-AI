"""
api_client.py
--------------
Centralized API communication layer for the SAFETrace AI Streamlit dashboard.

All requests to Member 2's FastAPI backend go through this module.
No other file in the app should call `requests.get` / `requests.post` directly.
"""

import os
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Backend URL is configurable via environment variable so Member 4 can change
# it during deployment without touching frontend code.
BACKEND_URL = os.environ.get("SAFETRACE_BACKEND_URL", "http://localhost:8000")

DEFAULT_TIMEOUT = 10  # seconds


class BackendUnavailableError(Exception):
    """Raised when the backend cannot be reached at all."""
    pass


class APIError(Exception):
    """Raised when the backend responds with an error status."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------
def _request(method, path, **kwargs):
    """
    Wraps requests.request with consistent error handling.
    Never lets a raw exception bubble up to the UI layer.
    """
    url = f"{BACKEND_URL}{path}"
    try:
        response = requests.request(
            method, url, timeout=kwargs.pop("timeout", DEFAULT_TIMEOUT), **kwargs
        )
    except requests.exceptions.ConnectionError:
        raise BackendUnavailableError(
            "Cannot connect to SAFETrace backend. Please check that the API is running."
        )
    except requests.exceptions.Timeout:
        raise BackendUnavailableError("Backend request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise BackendUnavailableError(f"Unexpected network error: {e}")

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise APIError(detail, status_code=response.status_code)

    if response.content:
        try:
            return response.json()
        except ValueError:
            return response.content
    return None


def check_backend_health():
    """Returns True if backend is reachable, False otherwise."""
    try:
        _request("GET", "/health", timeout=3)
        return True
    except Exception:
        try:
            # fall back: some backends may not expose /health, try root
            _request("GET", "/", timeout=3)
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def create_case(payload: dict, image_file=None):
    """
    POST /cases
    payload: dict with name, age, gender, last_seen_location, last_seen_time, description
    image_file: optional Streamlit UploadedFile for the reference image
    """
    if image_file is not None:
        files = {"reference_image": (image_file.name, image_file.getvalue(), image_file.type)}
        return _request("POST", "/cases", data=payload, files=files)
    return _request("POST", "/cases", json=payload)


def get_cases():
    """GET /cases -> list of case dicts"""
    result = _request("GET", "/cases")
    return result if result else []


def get_case(case_id: str):
    """GET /cases/{case_id} -> case detail dict"""
    return _request("GET", f"/cases/{case_id}")


# ---------------------------------------------------------------------------
# Videos / CCTV Analysis
# ---------------------------------------------------------------------------
def create_video(case_id: str, camera_id: str, location: str, video_file):
    """
    POST /videos
    Registers a CCTV video against a case.
    """
    files = {"video_file": (video_file.name, video_file.getvalue(), video_file.type)}
    data = {"case_id": case_id, "camera_id": camera_id, "location": location}
    return _request("POST", "/videos", data=data, files=files)


def analyze_video(video_id: str = None, case_id: str = None, camera_id: str = None, location: str = None):
    """
    POST /ai-results
    Triggers AI analysis for an uploaded video. Backend contract may vary;
    we send whatever identifying info is available.
    """
    payload = {"video_id": video_id, "case_id": case_id, "camera_id": camera_id, "location": location}
    payload = {k: v for k, v in payload.items() if v is not None}
    return _request("POST", "/ai-results", json=payload)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------
def get_evidence(case_id: str):
    """GET /cases/{case_id}/evidence -> list of evidence dicts"""
    result = _request("GET", f"/cases/{case_id}/evidence")
    return result if result else []


def update_evidence_status(evidence_id: str, status: str):
    """
    PATCH /evidence/{evidence_id}/status
    status: "Verified" or "Rejected"
    """
    return _request("PATCH", f"/evidence/{evidence_id}/status", json={"status": status})


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------
def get_leads(case_id: str):
    """GET /cases/{case_id}/leads -> list of lead dicts"""
    result = _request("GET", f"/cases/{case_id}/leads")
    return result if result else []


# ---------------------------------------------------------------------------
# Dashboard summary stats
# ---------------------------------------------------------------------------
def get_dashboard_stats():
    """
    Attempts GET /stats for aggregate dashboard numbers.
    Falls back to deriving stats from /cases if not available.
    """
    try:
        return _request("GET", "/stats")
    except Exception:
        return None
