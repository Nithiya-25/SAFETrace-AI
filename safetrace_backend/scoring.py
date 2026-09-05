"""
scoring.py
----------
Explainable lead-scoring logic for SAFETrace AI.

The score is a simple, documented weighted sum — deliberately NOT a
black-box model, per project requirement (Section 11).

Weights (Round 1):
    Detection confidence      -> 40%
    Track duration             -> 20%
    Visual similarity          -> 30%   (optional / future component)
    Time / location relevance  -> 10%

IMPORTANT (Section 32):
Visual similarity is Member 1's responsibility (appearance / re-ID model)
and may not exist yet. `calculate_lead_score` accepts
`visual_similarity=None` in that case. When None, the visual similarity
term contributes 0 to the weighted score and the explanation clearly
states that the component is unavailable — it is never faked.

The final score is always a plain 0-100 float, and priority/reason are
derived from it. Nothing here claims to confirm identity — see
`PRIORITY_DISCLAIMER` and the API layer for the "Potential Lead /
Requires Investigator Verification" language required by Section 10.
"""

from typing import Optional, Tuple, Dict

WEIGHT_DETECTION = 0.40
WEIGHT_DURATION = 0.20
WEIGHT_VISUAL = 0.30
WEIGHT_TIME_LOCATION = 0.10

DEFAULT_DURATION_CAP_SECONDS = 30  # duration_score saturates at this many seconds
DEFAULT_TIME_LOCATION_SCORE = 0.5  # neutral default if not supplied

PRIORITY_DISCLAIMER = "Potential Lead - Requires Investigator Verification"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def duration_score(duration_seconds: float, cap_seconds: float = DEFAULT_DURATION_CAP_SECONDS) -> float:
    """Map a track duration (seconds) to a 0-1 score, saturating at cap_seconds."""
    if duration_seconds is None or cap_seconds <= 0:
        return 0.0
    return _clamp01(duration_seconds / cap_seconds)


def calculate_lead_score(
    detection_confidence: float,
    duration_seconds: float,
    visual_similarity: Optional[float] = None,
    time_location_score: Optional[float] = None,
    duration_cap_seconds: float = DEFAULT_DURATION_CAP_SECONDS,
) -> Tuple[float, Dict]:
    """
    Compute the explainable 0-100 lead score.

    Returns (score, components) where components is a dict describing
    each weighted piece for transparency / the `reason` field.
    """
    detection_confidence = _clamp01(detection_confidence or 0.0)
    dur_score = duration_score(duration_seconds, duration_cap_seconds)

    visual_available = visual_similarity is not None
    vis_value = _clamp01(visual_similarity) if visual_available else 0.0

    if time_location_score is None:
        time_location_score = DEFAULT_TIME_LOCATION_SCORE
    time_loc = _clamp01(time_location_score)

    weighted = (
        WEIGHT_DETECTION * detection_confidence
        + WEIGHT_DURATION * dur_score
        + WEIGHT_VISUAL * vis_value
        + WEIGHT_TIME_LOCATION * time_loc
    )

    score = round(weighted * 100, 1)
    score = max(0.0, min(100.0, score))

    components = {
        "detection_confidence_pct": round(detection_confidence * 100, 1),
        "duration_seconds": duration_seconds,
        "duration_score_pct": round(dur_score * 100, 1),
        "visual_similarity_available": visual_available,
        "visual_similarity_pct": round(vis_value * 100, 1) if visual_available else None,
        "time_location_score_pct": round(time_loc * 100, 1),
        "weights": {
            "detection_confidence": WEIGHT_DETECTION,
            "duration": WEIGHT_DURATION,
            "visual_similarity": WEIGHT_VISUAL,
            "time_location": WEIGHT_TIME_LOCATION,
        },
    }
    return score, components


def classify_priority(score: float) -> str:
    """Convert a 0-100 score into HIGH / MEDIUM / LOW."""
    if score >= 80:
        return "HIGH"
    if score >= 60:
        return "MEDIUM"
    return "LOW"


def explain_score(components: Dict) -> str:
    """Build a short, human-readable explanation string from score components."""
    reasons = []

    dc = components["detection_confidence_pct"]
    if dc >= 80:
        reasons.append(f"High detection confidence ({dc}%)")
    elif dc >= 50:
        reasons.append(f"Moderate detection confidence ({dc}%)")
    else:
        reasons.append(f"Low detection confidence ({dc}%)")

    dur = components.get("duration_seconds") or 0
    if dur >= 15:
        reasons.append(f"Long continuous track ({dur:.0f}s)")
    elif dur >= 5:
        reasons.append(f"Moderate track duration ({dur:.0f}s)")
    else:
        reasons.append(f"Short track duration ({dur:.0f}s)")

    if components["visual_similarity_available"]:
        vs = components["visual_similarity_pct"]
        if vs >= 80:
            reasons.append(f"Strong visual similarity ({vs}%)")
        elif vs >= 50:
            reasons.append(f"Moderate visual similarity ({vs}%)")
        else:
            reasons.append(f"Low visual similarity ({vs}%)")
    else:
        reasons.append("Visual similarity not yet available (future component from Member 1)")

    tl = components["time_location_score_pct"]
    if tl >= 80:
        reasons.append("High time/location relevance")
    elif tl >= 50:
        reasons.append("Moderate time/location relevance")
    else:
        reasons.append("Low time/location relevance")

    return "; ".join(reasons)