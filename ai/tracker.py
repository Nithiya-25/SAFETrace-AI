"""
tracker.py
----------
Handles person tracking: assigning a stable Track ID to each detected
person and keeping that ID consistent across frames for as long as the
person stays visible.

Implementation note:
Ultralytics YOLO ships with built-in ByteTrack and BoT-SORT trackers
(model.track(..., persist=True)). Rather than re-implementing tracking
math from scratch, this module wraps that functionality behind a small,
clean class so the rest of the pipeline doesn't need to know which
tracker library is used underneath. This keeps Round 1 simple and
reliable, per the "WORKING > COMPLEX" priority.
"""

from ultralytics import YOLO

try:
    from . import config
except ImportError:  # allows `python tracker.py` direct execution too
    import config


class PersonTracker:
    """
    Wraps YOLO + ByteTrack/BoT-SORT to detect AND track people frame by
    frame, returning stable track IDs.

    Usage:
        tracker = PersonTracker()
        for frame in frames:
            tracks = tracker.update(frame)
            # tracks -> list of dicts with track_id, bbox, confidence
    """

    def __init__(
        self,
        model_name: str = None,
        confidence_threshold: float = None,
        tracker_type: str = None,
    ):
        self.model_name = model_name or config.YOLO_MODEL_NAME
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else config.CONFIDENCE_THRESHOLD
        )
        self.tracker_type = tracker_type or config.TRACKER_TYPE

        self.model = YOLO(self.model_name)

        # Tracks whether we've started a tracking stream yet, so we know
        # when to reset track IDs (persist=True keeps IDs stable across
        # calls to .track() as long as the same model instance is reused).
        self._started = False

    def reset(self):
        """Start a fresh tracking session (new video / new set of IDs)."""
        self._started = False

    def update(self, frame):
        """
        Run detection + tracking on a single BGR frame.

        Returns:
            list[dict]: e.g.
                [
                    {
                        "track_id": 7,
                        "bbox": [x1, y1, x2, y2],
                        "confidence": 0.91,
                        "class_id": 0
                    },
                    ...
                ]

            Note: a detected person that hasn't yet been assigned a
            stable ID by the tracker (can happen for a frame or two on a
            brand-new track) is skipped -- we only report tracks that
            have a real ID.
        """
        results = self.model.track(
            source=frame,
            classes=[config.PERSON_CLASS_ID],
            conf=self.confidence_threshold,
            tracker=self.tracker_type,
            persist=True,
            verbose=False,
        )
        self._started = True

        tracks = []
        if not results:
            return tracks

        boxes = results[0].boxes
        if boxes is None or boxes.id is None:
            # No confirmed tracks in this frame yet.
            return tracks

        ids = boxes.id.int().tolist()
        for box, track_id in zip(boxes, ids):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])

            tracks.append(
                {
                    "track_id": int(track_id),
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": round(confidence, 4),
                    "class_id": class_id,
                }
            )

        return tracks
