"""
models.py
---------
Lightweight dataclasses describing each database row.

Round-1 uses plain sqlite3 rather than an ORM, so these classes are not
mapped automatically — they exist as a single readable reference for the
shape of each table, and a `from_row()` helper to build one from a
sqlite3.Row. Services can use dicts directly; these are provided for
type clarity when other members read this file.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Case:
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

    @staticmethod
    def from_row(row):
        return Case(**dict(row))


@dataclass
class Video:
    video_id: str
    case_id: str
    camera_id: Optional[str]
    location: Optional[str]
    filename: Optional[str]
    uploaded_at: str
    status: str

    @staticmethod
    def from_row(row):
        return Video(**dict(row))


@dataclass
class Track:
    track_id: int
    video_id: str
    first_seen: Optional[str]
    last_seen: Optional[str]
    duration: Optional[float]
    frame_count: Optional[int]
    average_confidence: Optional[float]

    @staticmethod
    def from_row(row):
        d = dict(row)
        d.pop("id", None)
        return Track(**d)


@dataclass
class Detection:
    detection_id: str
    track_id: int
    video_id: str
    frame_number: Optional[int]
    timestamp: Optional[str]
    x1: Optional[float]
    y1: Optional[float]
    x2: Optional[float]
    y2: Optional[float]
    confidence: Optional[float]

    @staticmethod
    def from_row(row):
        return Detection(**dict(row))


@dataclass
class Evidence:
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

    @staticmethod
    def from_row(row):
        return Evidence(**dict(row))


@dataclass
class Lead:
    lead_id: str
    case_id: str
    evidence_id: str
    score: float
    priority: str
    reason: str
    status: str
    created_at: str

    @staticmethod
    def from_row(row):
        return Lead(**dict(row))