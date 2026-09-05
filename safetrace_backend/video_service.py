"""
video_service.py
-----------------
Business logic for CCTV / sample video records.
"""

from datetime import datetime, timezone
from typing import Optional, Dict

from database import get_connection
from case_service import case_exists


def _next_video_id(conn) -> str:
    row = conn.execute(
        "SELECT video_id FROM videos ORDER BY CAST(SUBSTR(video_id, 5) AS INTEGER) DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return "VID-001"
    last_num = int(row["video_id"].split("-")[1])
    return f"VID-{last_num + 1:03d}"


class CaseNotFoundError(Exception):
    pass


def create_video(data) -> Dict:
    if not case_exists(data.case_id):
        raise CaseNotFoundError(f"Case {data.case_id} does not exist")

    conn = get_connection()
    try:
        video_id = _next_video_id(conn)
        uploaded_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO videos
               (video_id, case_id, camera_id, location, filename, uploaded_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (video_id, data.case_id, data.camera_id, data.location, data.filename, uploaded_at, "Uploaded"),
        )
        conn.commit()
        return {"video_id": video_id, "status": "Uploaded"}
    finally:
        conn.close()


def get_video(video_id: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def video_exists(video_id: str) -> bool:
    return get_video(video_id) is not None


def mark_video_analyzed(video_id: str) -> None:
    conn = get_connection()
    try:
        conn.execute("UPDATE videos SET status = ? WHERE video_id = ?", ("Analyzed", video_id))
        conn.commit()
    finally:
        conn.close()