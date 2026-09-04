"""
candidate_analyzer.py
----------------------
Turns a raw track summary into a "Potential Candidate" record.

IMPORTANT / SAFETY NOTE:
This module NEVER confirms that a tracked person is the missing person.
Every record produced here is explicitly labelled as a
"Potential Candidate" (see config.STATUS_POTENTIAL_CANDIDATE). Final
identification is always a decision for a human investigator, using this
output only as a lead to review -- not as a verdict.

The structure here is deliberately left open so a future appearance /
re-identification model (e.g. face or clothing embeddings) can be slotted
in later without changing the output shape that Member 2 depends on.
"""

try:
    from . import config
except ImportError:  # allows `python candidate_analyzer.py` direct execution
    import config


def build_candidate(track_summary: dict) -> dict:
    """
    Convert a single track summary into a Potential Candidate record.

    Args:
        track_summary: dict produced by video_processor, expected to have
            keys: track_id, duration, average_confidence, frame_count,
            crop_paths (and optionally first_seen / last_seen).

    Returns:
        dict: a Potential Candidate record, e.g.
            {
                "track_id": 7,
                "duration": 17.2,
                "average_confidence": 0.89,
                "num_observations": 510,
                "crop_paths": [...],
                "status": "Potential Candidate"
            }
    """
    return {
        "track_id": track_summary.get("track_id"),
        "duration": track_summary.get("duration"),
        "average_confidence": track_summary.get("average_confidence"),
        "num_observations": track_summary.get("frame_count"),
        "crop_paths": track_summary.get("crop_paths", []),
        # Placeholder for a future re-identification / appearance-matching
        # score. Left as None in Round 1 -- no such model exists yet.
        "reid_similarity_score": None,
        "status": config.STATUS_POTENTIAL_CANDIDATE,
    }


def build_candidates(track_summaries: list) -> list:
    """Apply build_candidate() to a whole list of track summaries."""
    return [build_candidate(t) for t in track_summaries]
