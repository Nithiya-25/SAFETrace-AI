"""
detector.py
-----------
Wraps an Ultralytics YOLO model and exposes a single, simple function
for detecting people in a video frame.

This module is intentionally "dumb": it only detects, it does not track.
Tracking (assigning stable IDs across frames) lives in tracker.py.
"""

from ultralytics import YOLO

try:
    from . import config
except ImportError:  # allows `python detector.py` direct execution too
    import config


class PersonDetector:
    """Loads a YOLO model once and detects people in individual frames."""

    def __init__(self, model_name: str = None, confidence_threshold: float = None):
        self.model_name = model_name or config.YOLO_MODEL_NAME
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else config.CONFIDENCE_THRESHOLD
        )

        # Loading the model downloads the weights on first use and caches
        # them locally afterwards.
        self.model = YOLO(self.model_name)

    def detect(self, frame):
        """
        Run YOLO on a single BGR frame (as returned by cv2.VideoCapture)
        and return only "person" detections.

        Returns:
            list[dict]: e.g.
                [
                    {
                        "bbox": [x1, y1, x2, y2],
                        "confidence": 0.91,
                        "class_id": 0
                    },
                    ...
                ]
        """
        results = self.model.predict(
            source=frame,
            classes=[config.PERSON_CLASS_ID],
            conf=self.confidence_threshold,
            verbose=False,
        )

        detections = []
        if not results:
            return detections

        boxes = results[0].boxes
        if boxes is None:
            return detections

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])

            detections.append(
                {
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": round(confidence, 4),
                    "class_id": class_id,
                }
            )

        return detections


if __name__ == "__main__":
    # Tiny manual smoke test: run detection on a single sample image/frame
    # if one is available. This is not the main pipeline entry point --
    # use video_processor.py for full video processing.
    import sys
    import cv2

    if len(sys.argv) < 2:
        print("Usage: python detector.py <path_to_image_or_video_frame>")
        sys.exit(0)

    frame = cv2.imread(sys.argv[1])
    if frame is None:
        print(f"Could not read image: {sys.argv[1]}")
        sys.exit(1)

    detector = PersonDetector()
    dets = detector.detect(frame)
    print(f"Found {len(dets)} person(s):")
    for d in dets:
        print(d)
