"""
evidence_service.py
-------------------
Handles AI result ingestion, evidence creation,
lead scoring, evidence status updates, and lead retrieval.
"""

from datetime import datetime

import database
from scoring import (
    calculate_lead_score,
    classify_priority,
    explain_score,
    PRIORITY_DISCLAIMER,
)


class VideoNotFoundError(Exception):
    """Raised when AI results reference an unknown video."""
    pass


def _generate_id(conn, table, column, prefix, width=5):
    """Generate sequential IDs such as EV-00001 or LEAD-00001."""

    row = conn.execute(
        f"""
        SELECT {column}
        FROM {table}
        WHERE {column} LIKE ?
        ORDER BY {column} DESC
        LIMIT 1
        """,
        (f"{prefix}-%",)
    ).fetchone()

    if row is None:
        number = 1
    else:
        try:
            number = int(row[0].split("-")[-1]) + 1
        except (ValueError, AttributeError):
            number = 1

    return f"{prefix}-{number:0{width}d}"


def process_ai_results(payload):
    """
    Process AI results received from Member 1.

    Creates:
    - tracks
    - detections
    - evidence
    - leads
    """

    conn = database.get_connection()

    try:
        # ---------------------------------------------------------
        # 1. Check whether the video exists
        # ---------------------------------------------------------

        video = conn.execute(
            """
            SELECT *
            FROM videos
            WHERE video_id = ?
            """,
            (payload.video_id,)
        ).fetchone()

        if video is None:
            raise VideoNotFoundError(
                f"Video {payload.video_id} was not found"
            )

        video = dict(video)

        case_id = video["case_id"]
        camera_id = video["camera_id"]
        location = video["location"]

        tracks_stored = 0
        evidence_created = []
        leads_created = []

        # ---------------------------------------------------------
        # 2. Process each AI track
        # ---------------------------------------------------------

        for track in payload.tracks:

            # Store track
            conn.execute(
                """
                INSERT INTO tracks (
                    track_id,
                    video_id,
                    first_seen,
                    last_seen,
                    duration,
                    frame_count,
                    average_confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    track.track_id,
                    payload.video_id,
                    track.first_seen,
                    track.last_seen,
                    track.duration,
                    track.frame_count,
                    track.average_confidence,
                )
            )

            tracks_stored += 1

            # -----------------------------------------------------
            # 3. Store detections
            # -----------------------------------------------------

            for detection in track.detections:

                detection_id = _generate_id(
                    conn,
                    "detections",
                    "detection_id",
                    "DET"
                )

                conn.execute(
                    """
                    INSERT INTO detections (
                        detection_id,
                        track_id,
                        video_id,
                        frame_number,
                        timestamp,
                        x1,
                        y1,
                        x2,
                        y2,
                        confidence
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        detection_id,
                        track.track_id,
                        payload.video_id,
                        detection.frame_number,
                        detection.timestamp,
                        detection.x1,
                        detection.y1,
                        detection.x2,
                        detection.y2,
                        detection.confidence,
                    )
                )

            # -----------------------------------------------------
            # 4. Calculate lead score
            # -----------------------------------------------------

            score, components = calculate_lead_score(
                detection_confidence=track.average_confidence,
                duration_seconds=track.duration,
                visual_similarity=track.visual_similarity,
                time_location_score=track.time_location_score,
            )

            priority = classify_priority(score)

            explanation = explain_score(components)

            reason = (
                f"{PRIORITY_DISCLAIMER}. "
                f"{explanation}"
            )

            # -----------------------------------------------------
            # 5. Create evidence
            # -----------------------------------------------------

            evidence_id = _generate_id(
                conn,
                "evidence",
                "evidence_id",
                "EV"
            )

            evidence_image = (
                track.crop_paths[0]
                if track.crop_paths
                else None
            )

            created_at = datetime.utcnow().isoformat()

            conn.execute(
                """
                INSERT INTO evidence (
                    evidence_id,
                    case_id,
                    video_id,
                    track_id,
                    camera_id,
                    location,
                    timestamp,
                    evidence_image,
                    detection_confidence,
                    lead_score,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    case_id,
                    payload.video_id,
                    track.track_id,
                    camera_id,
                    location,
                    track.first_seen,
                    evidence_image,
                    track.average_confidence,
                    score,
                    "Pending Review",
                    created_at,
                )
            )

            evidence_created.append(evidence_id)

            # -----------------------------------------------------
            # 6. Create lead
            # -----------------------------------------------------

            lead_id = _generate_id(
                conn,
                "leads",
                "lead_id",
                "LEAD"
            )

            conn.execute(
                """
                INSERT INTO leads (
                    lead_id,
                    case_id,
                    evidence_id,
                    score,
                    priority,
                    reason,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    case_id,
                    evidence_id,
                    score,
                    priority,
                    reason,
                    "Pending Review",
                    created_at,
                )
            )

            leads_created.append(lead_id)

        # ---------------------------------------------------------
        # 7. Mark video as analyzed
        # ---------------------------------------------------------

        conn.execute(
            """
            UPDATE videos
            SET status = ?
            WHERE video_id = ?
            """,
            (
                "Analyzed",
                payload.video_id,
            )
        )

        conn.commit()

        # ---------------------------------------------------------
        # 8. Return result
        # ---------------------------------------------------------

        return {
            "video_id": payload.video_id,
            "tracks_stored": tracks_stored,
            "evidence_created": evidence_created,
            "leads_created": leads_created,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_evidence_for_case(case_id):
    """Return all evidence belonging to a case."""

    conn = database.get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM evidence
            WHERE case_id = ?
            ORDER BY created_at DESC
            """,
            (case_id,)
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def update_evidence_status(evidence_id, status):
    """
    Update evidence status and synchronize
    the linked lead status.
    """

    conn = database.get_connection()

    try:
        # Check evidence exists
        evidence = conn.execute(
            """
            SELECT *
            FROM evidence
            WHERE evidence_id = ?
            """,
            (evidence_id,)
        ).fetchone()

        if evidence is None:
            raise LookupError(
                f"Evidence {evidence_id} was not found"
            )

        # Update evidence
        conn.execute(
            """
            UPDATE evidence
            SET status = ?
            WHERE evidence_id = ?
            """,
            (
                status,
                evidence_id,
            )
        )

        # Update linked lead
        conn.execute(
            """
            UPDATE leads
            SET status = ?
            WHERE evidence_id = ?
            """,
            (
                status,
                evidence_id,
            )
        )

        conn.commit()

        # Return updated evidence
        updated = conn.execute(
            """
            SELECT *
            FROM evidence
            WHERE evidence_id = ?
            """,
            (evidence_id,)
        ).fetchone()

        return dict(updated)

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_leads_for_case(case_id):
    """Return leads sorted by score from highest to lowest."""

    conn = database.get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM leads
            WHERE case_id = ?
            ORDER BY score DESC, created_at ASC
            """,
            (case_id,)
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()