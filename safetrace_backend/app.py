"""
app.py
------
FastAPI application for SAFETrace AI - Backend / Database / Evidence /
Lead Scoring module (Member 2).

Run with:
    uvicorn backend.app:app --reload

SAFETrace is an investigation-support prototype. It never claims to
confirm a missing person's identity. All AI-derived records are surfaced
as "Potential Lead" candidates that require human investigator review.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import database
import case_service
import video_service
import evidence_service
from schemas import (
    CaseCreate, CaseOut, CaseCreateResponse,
    VideoCreate, VideoOut, VideoCreateResponse,
    AIResultIn, AIResultResponse,
    EvidenceOut, EvidenceStatusUpdate,
    LeadOut,
)

app = FastAPI(
    title="SAFETrace AI - Backend API",
    description=(
        "Investigation-support backend. Stores cases, videos, AI tracks, "
        "evidence, and prioritized leads. This system never confirms "
        "identity — all output requires human investigator verification."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    database.init_db()


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "SAFETrace AI Backend",
        "status": "running",
        "disclaimer": "Investigation-support prototype. No output confirms identity.",
    }


# ---------------------------------------------------------------- Cases ----

@app.post("/cases", response_model=CaseCreateResponse, tags=["cases"])
def create_case(payload: CaseCreate):
    return case_service.create_case(payload)


@app.get("/cases", response_model=list[CaseOut], tags=["cases"])
def list_cases():
    return case_service.get_all_cases()


@app.get("/cases/{case_id}", response_model=CaseOut, tags=["cases"])
def get_case(case_id: str):
    case = case_service.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id} does not exist")
    return case


# ---------------------------------------------------------------- Videos ---

@app.post("/videos", response_model=VideoCreateResponse, tags=["videos"])
def create_video(payload: VideoCreate):
    try:
        return video_service.create_video(payload)
    except video_service.CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/videos/{video_id}", response_model=VideoOut, tags=["videos"])
def get_video(video_id: str):
    video = video_service.get_video(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail=f"Video {video_id} does not exist")
    return video


# ------------------------------------------------------------ AI Results ---

@app.post("/ai-results", response_model=AIResultResponse, tags=["ai-integration"])
def submit_ai_results(payload: AIResultIn):
    """
    Integration point for Member 1's AI/CV module.
    Receives tracks for a video and produces Evidence + Lead records.
    """
    try:
        return evidence_service.process_ai_results(payload)
    except evidence_service.VideoNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -------------------------------------------------------------- Evidence ---

@app.get("/cases/{case_id}/evidence", response_model=list[EvidenceOut], tags=["evidence"])
def get_case_evidence(case_id: str):
    if not case_service.case_exists(case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} does not exist")
    return evidence_service.get_evidence_for_case(case_id)


@app.patch("/evidence/{evidence_id}/status", response_model=EvidenceOut, tags=["evidence"])
def update_evidence_status(evidence_id: str, payload: EvidenceStatusUpdate):
    """
    Investigator review action.
    'Verified' means a human investigator reviewed the evidence — it does
    NOT mean the AI independently confirmed identity.
    """
    try:
        return evidence_service.update_evidence_status(evidence_id, payload.status)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ----------------------------------------------------------------- Leads ---

@app.get("/cases/{case_id}/leads", response_model=list[LeadOut], tags=["leads"])
def get_case_leads(case_id: str):
    """Return prioritized leads for a case, highest score first."""
    if not case_service.case_exists(case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} does not exist")
    return evidence_service.get_leads_for_case(case_id)
