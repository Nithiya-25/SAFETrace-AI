import os
import sys
import tempfile

# ---------------------------------------------------------
# Create a temporary database for testing
# ---------------------------------------------------------

TEST_DB = tempfile.NamedTemporaryFile(
    suffix=".db",
    delete=False
).name

os.environ["SAFETRACE_DB_PATH"] = TEST_DB


# ---------------------------------------------------------
# Add the parent project folder to Python path
# ---------------------------------------------------------

PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, PROJECT_DIR)


# ---------------------------------------------------------
# Import project modules
# ---------------------------------------------------------

import database
import case_service
import video_service
import evidence_service

from schemas import (
    CaseCreate,
    VideoCreate,
    AIResultIn,
    TrackIn,
)


# ---------------------------------------------------------
# Initialize database before tests
# ---------------------------------------------------------

def setup_module(module):
    database.init_db()


# ---------------------------------------------------------
# Helper function
# ---------------------------------------------------------

def _make_case_and_video():

    case = case_service.create_case(
        CaseCreate(
            name="Evidence Test Person"
        )
    )

    video = video_service.create_video(
        VideoCreate(
            case_id=case["case_id"],
            camera_id="CAM-03",
            location="Test Station",
            filename="test.mp4"
        )
    )

    return case, video


# =========================================================
# TEST 1
# =========================================================

def test_ai_result_ingestion_creates_track_evidence_and_lead():

    case, video = _make_case_and_video()

    payload = AIResultIn(
        video_id=video["video_id"],

        tracks=[
            TrackIn(
                track_id=1,
                first_seen="00:00:05",
                last_seen="00:00:20",
                duration=15,
                frame_count=200,
                average_confidence=0.9,
                visual_similarity=0.8,
                time_location_score=0.9,
                crop_paths=[
                    "outputs/crops/track_1/frame_1.jpg"
                ]
            )
        ]
    )

    # Send AI result to evidence service
    result = evidence_service.process_ai_results(
        payload
    )

    # Check that one track was stored
    assert result["tracks_stored"] == 1

    # Check that one evidence was created
    assert len(result["evidence_created"]) == 1

    # Check that one lead was created
    assert len(result["leads_created"]) == 1

    # Get evidence for the case
    evidence_list = evidence_service.get_evidence_for_case(
        case["case_id"]
    )

    # There should be one evidence
    assert len(evidence_list) == 1

    # New evidence should be Pending Review
    assert evidence_list[0]["status"] == "Pending Review"

    # Lead score should exist
    assert evidence_list[0]["lead_score"] is not None


# =========================================================
# TEST 2
# =========================================================

def test_ai_result_unknown_video_raises():

    payload = AIResultIn(
        video_id="VID-999",
        tracks=[]
    )

    try:

        evidence_service.process_ai_results(
            payload
        )

        # If no error occurs, the test must fail
        assert False, "expected VideoNotFoundError"

    except evidence_service.VideoNotFoundError:

        # Correct error occurred
        pass


# =========================================================
# TEST 3
# =========================================================

def test_leads_sorted_by_score_descending():

    case, video = _make_case_and_video()

    payload = AIResultIn(

        video_id=video["video_id"],

        tracks=[
            TrackIn(
                track_id=1,
                duration=5,
                average_confidence=0.4,
                visual_similarity=0.3,
                time_location_score=0.3,
                crop_paths=[]
            ),

            TrackIn(
                track_id=2,
                duration=25,
                average_confidence=0.95,
                visual_similarity=0.9,
                time_location_score=0.9,
                crop_paths=[]
            )
        ]
    )

    # Process both tracks
    evidence_service.process_ai_results(
        payload
    )

    # Get leads
    leads = evidence_service.get_leads_for_case(
        case["case_id"]
    )

    # Extract scores
    scores = [
        lead["score"]
        for lead in leads
    ]

    # Check descending order
    assert scores == sorted(
        scores,
        reverse=True
    )


# =========================================================
# TEST 4
# =========================================================

def test_evidence_status_update_syncs_lead_status():

    case, video = _make_case_and_video()

    payload = AIResultIn(

        video_id=video["video_id"],

        tracks=[
            TrackIn(
                track_id=1,
                duration=10,
                average_confidence=0.8,
                crop_paths=[]
            )
        ]
    )

    # Process AI result
    result = evidence_service.process_ai_results(
        payload
    )

    # Get created evidence ID
    evidence_id = result["evidence_created"][0]

    # Change evidence status
    updated = evidence_service.update_evidence_status(
        evidence_id,
        "Verified"
    )

    # Check evidence status
    assert updated["status"] == "Verified"

    # Get leads
    leads = evidence_service.get_leads_for_case(
        case["case_id"]
    )

    # Find the lead connected to this evidence
    matching = [
        lead
        for lead in leads
        if lead["evidence_id"] == evidence_id
    ][0]

    # Lead status should also become Verified
    assert matching["status"] == "Verified"