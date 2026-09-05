"""
case_service.py
----------------
Business logic for missing-person case records.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict

from database import get_connection


def _next_case_id(conn) -> str:
    row = conn.execute(
        "SELECT case_id FROM cases ORDER BY CAST(SUBSTR(case_id, 4) AS INTEGER) DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return "MP-0001"
    last_num = int(row["case_id"].split("-")[1])
    return f"MP-{last_num + 1:04d}"


def create_case(data) -> Dict:
    conn = get_connection()
    try:
        case_id = _next_case_id(conn)
        created_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO cases
               (case_id, name, age, gender, last_seen_location, last_seen_time,
                description, reference_image, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                case_id,
                data.name,
                data.age,
                data.gender,
                data.last_seen_location,
                data.last_seen_time,
                data.description,
                data.reference_image,
                "Active",
                created_at,
            ),
        )
        conn.commit()
        return {"case_id": case_id, "status": "Active"}
    finally:
        conn.close()


def get_all_cases() -> List[Dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_case(case_id: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def case_exists(case_id: str) -> bool:
    return get_case(case_id) is not None