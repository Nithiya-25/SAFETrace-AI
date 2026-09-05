"""
schemas.py
----------
Pydantic models used for request validation and response shaping.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

ALLOWED_STATUSES = ("Pending Review", "Verified", "Rejected")


# ---------------------------------------------------------------- Cases ----

class CaseCreate(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    last_seen_location: Optional[str] = None
    last_seen_time: Optional[str] = None
    description: Optional[str] = None
    reference_image: Optional[str] = None


class CaseOut(BaseModel):
    case_id: str
    name: str
    age: Optional[int]
    gender: Optional[str]
    last_seen_location: Optional[str]
    last_seen_time: Optional[str]
    description: Optional[str]
    reference_image: Optional[str]
    status: str
    created_at: str


class CaseCreateResponse(BaseModel):
    case_id: str
    status: str


# ---------------------------------------------------------------- Videos ---

class VideoCreate(BaseModel):
    case_id: str
    camera_id: Optional[str] = None
    location: Optional[str] = None
    filename: Optional[str] = None


class VideoOut(BaseModel):
    video_id: str
    case_id: str
    camera_id: Optional[str]
    location: Optional[str]
    filename: Optional[str]
    uploaded_at: str
    status: str


class VideoCreateResponse(BaseModel):
    video_id: str
    status: str


# ------------------------------------------------------------ AI Results ---

class DetectionIn(BaseModel):
    frame_number: Optional[int] = None
    timestamp: Optional[str] = None
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None
    confidence: Optional[float] = None


class TrackIn(BaseModel):
    track_id: int
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    duration: float = 0
    frame_count: Optional[int] = None
    average_confidence: float = 0
    crop_paths: List[str] = Field(default_factory=list)
    # Optional / future component. Member 1 may not have this in Round 1.
    # Leave unset (None) rather than sending a fake value.
    visual_similarity: Optional[float] = None
    # Optional relevance of the video's time/location to the case's
    # last-seen time/location. Defaults to a neutral 0.5 if not supplied.
    time_location_score: Optional[float] = None
    detections: List[DetectionIn] = Field(default_factory=list)


class AIResultIn(BaseModel):
    video_id: str
    tracks: List[TrackIn]


class AIResultResponse(BaseModel):
    video_id: str
    tracks_stored: int
    evidence_created: List[str]
    leads_created: List[str]


# -------------------------------------------------------------- Evidence ---

class EvidenceOut(BaseModel):
    evidence_id: str
    case_id: str
    video_id: str
    track_id: int
    camera_id: Optional[str]
    location: Optional[str]
    timestamp: Optional[str]
    evidence_image: Optional[str]
    detection_confidence: Optional[float]
    lead_score: Optional[float]
    status: str
    created_at: str


class EvidenceStatusUpdate(BaseModel):
    status: Literal["Pending Review", "Verified", "Rejected"]


# ----------------------------------------------------------------- Leads ---

class LeadOut(BaseModel):
    lead_id: str
    case_id: str
    evidence_id: str
    score: float
    priority: str
    reason: str
    status: str
    created_at: str