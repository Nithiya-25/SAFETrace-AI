"""
database.py
------------
SQLite connection handling and schema initialization for SAFETrace AI.

Design notes:
- Round-1 prototype uses plain sqlite3 (no ORM) to keep the stack simple.
- init_db() is idempotent: safe to call every time the app starts.
- All timestamps stored as ISO-8601 strings (created_at / uploaded_at).
"""

import os
import sqlite3

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# Allows tests (or alternate deployments) to point at a different DB file
# without touching the production database.
DB_PATH = os.environ.get("SAFETRACE_DB_PATH") or os.path.join(PROJECT_ROOT, "data", "safetrace.db")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row access by column name."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    case_id             TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    age                 INTEGER,
    gender              TEXT,
    last_seen_location  TEXT,
    last_seen_time      TEXT,
    description         TEXT,
    reference_image     TEXT,
    status              TEXT DEFAULT 'Active',
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS videos (
    video_id     TEXT PRIMARY KEY,
    case_id      TEXT NOT NULL,
    camera_id    TEXT,
    location     TEXT,
    filename     TEXT,
    uploaded_at  TEXT NOT NULL,
    status       TEXT DEFAULT 'Uploaded',
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

-- Member 1's track_id is only unique *within* a video, so the true
-- primary key here is (video_id, track_id). See Section 6 of the spec.
CREATE TABLE IF NOT EXISTS tracks (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id            INTEGER NOT NULL,
    video_id            TEXT NOT NULL,
    first_seen          TEXT,
    last_seen           TEXT,
    duration            REAL,
    frame_count         INTEGER,
    average_confidence  REAL,
    UNIQUE (video_id, track_id),
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

CREATE TABLE IF NOT EXISTS detections (
    detection_id  TEXT PRIMARY KEY,
    track_id      INTEGER NOT NULL,
    video_id      TEXT NOT NULL,
    frame_number  INTEGER,
    timestamp     TEXT,
    x1 REAL, y1 REAL, x2 REAL, y2 REAL,
    confidence    REAL,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id           TEXT PRIMARY KEY,
    case_id               TEXT NOT NULL,
    video_id              TEXT NOT NULL,
    track_id              INTEGER NOT NULL,
    camera_id             TEXT,
    location              TEXT,
    timestamp             TEXT,
    evidence_image        TEXT,
    detection_confidence  REAL,
    lead_score            REAL,
    status                TEXT DEFAULT 'Pending Review',
    created_at            TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(case_id),
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

CREATE TABLE IF NOT EXISTS leads (
    lead_id      TEXT PRIMARY KEY,
    case_id      TEXT NOT NULL,
    evidence_id  TEXT NOT NULL,
    score        REAL,
    priority     TEXT,
    reason       TEXT,
    status       TEXT DEFAULT 'Pending Review',
    created_at   TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(case_id),
    FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id)
);
"""


def init_db() -> None:
    """Create the database file and all tables if they do not already exist."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()