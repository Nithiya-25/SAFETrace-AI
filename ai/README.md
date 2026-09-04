# SAFETrace AI — Computer Vision Module (Member 1)

## 1. Purpose

This module is the AI / computer-vision pipeline for **SAFETrace AI**, a
missing-person investigation support system. It analyzes an authorized or
sample CCTV video and:

- Detects every **person** in the video (YOLO).
- Tracks each person across frames, assigning a stable **Track ID**.
- Records timestamps, bounding boxes, and detection confidence.
- Saves representative crops of each tracked person.
- Produces an annotated output video.
- Produces `tracks.csv` and a structured JSON output for Member 2's
  backend/database.

> **This module never confirms an identity.** Every tracked person is only
> ever labelled a **"Potential Candidate"**. Final verification is always
> made by a human investigator — the AI only surfaces leads to review.

---

## 2. Required Technologies

- Python 3.10 or 3.11
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) (person detection)
- Built-in ByteTrack (or BoT-SORT) tracker, shipped with Ultralytics
- OpenCV (`opencv-python`)
- NumPy
- Pandas
- Pillow

See `requirements.txt` in the project root for exact packages.

---

## 3. Installation

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

The first time you run the pipeline, Ultralytics will automatically
download the YOLO weights file (`yolov8n.pt` by default) — this needs an
internet connection once; after that it's cached locally.

---

## 4. Model & Tracker Used

- **Detection model:** `yolov8n.pt` (YOLOv8 "nano") — small and fast,
  good for a Round-1 prototype. Configurable in `ai/config.py`
  (`YOLO_MODEL_NAME`). Only the `person` class (COCO class id `0`) is kept.
- **Tracking algorithm:** ByteTrack by default (`tracker.yaml =
  bytetrack.yaml`), also configurable to BoT-SORT (`botsort.yaml`) in
  `ai/config.py` (`TRACKER_TYPE`).

---

## 5. Input Format

Any video file OpenCV can read (`.mp4`, `.avi`, `.mov`, etc). Place sample
videos in:

```text
data/sample_videos/
```

---

## 6. Output Format

Running the pipeline on a video produces:

```text
outputs/
├── annotated_videos/
│   └── <video_name>_annotated.mp4     # boxes, track IDs, confidence, timestamp
│
├── person_crops/
│   ├── track_1/
│   │   ├── frame_30.jpg
│   │   └── frame_60.jpg
│   └── track_2/
│       └── ...
│
└── tracks/
    ├── tracks.csv          # one row per person per frame
    ├── track_summary.csv   # one row per track (first/last seen, duration, avg confidence)
    └── tracks.json         # structured output, see below
```

### `tracks.csv` columns

```text
track_id, frame_number, timestamp, x1, y1, x2, y2, confidence
```

### `tracks.json` / structured Python output

```json
{
  "video_path": "data/sample_videos/test.mp4",
  "camera_id": "CAM-01",
  "tracks": [
    {
      "track_id": 7,
      "duration": 17.2,
      "average_confidence": 0.89,
      "num_observations": 510,
      "crop_paths": [
        "outputs/person_crops/track_7/frame_120.jpg",
        "outputs/person_crops/track_7/frame_180.jpg"
      ],
      "reid_similarity_score": null,
      "status": "Potential Candidate"
    }
  ],
  "annotated_video": "outputs/annotated_videos/test_annotated.mp4",
  "person_crops": [
    "outputs/person_crops/track_7/frame_120.jpg",
    "outputs/person_crops/track_7/frame_180.jpg"
  ],
  "performance": {
    "video_duration_seconds": 60.0,
    "processing_time_seconds": 24.3,
    "frames_processed": 1800,
    "total_detections": 5230,
    "unique_tracks": 14,
    "average_confidence": 0.87
  }
}
```

---

## 7. How to Run

### From the command line

```bash
python ai/video_processor.py --input data/sample_videos/test.mp4
```

Optional flags:

```bash
python ai/video_processor.py \
  --input data/sample_videos/test.mp4 \
  --output-video outputs/annotated_videos/custom_name.mp4 \
  --crop-dir outputs/person_crops \
  --camera-id CAM-01 \
  --csv-output outputs/tracks/tracks.csv \
  --json-output outputs/tracks/tracks.json
```

### As a Python library (for Member 2 / integration)

```python
from ai.video_processor import process_video

result = process_video("data/sample_videos/test.mp4", camera_id="CAM-01")

print(result["tracks"])            # list of Potential Candidate dicts
print(result["annotated_video"])   # path to annotated video
print(result["person_crops"])      # list of all saved crop paths
print(result["performance"])       # processing stats
```

The module works completely on its own — it has **no dependency on
Streamlit or any dashboard** and can be imported directly by Member 2's
backend.

---

## 8. Example Console Output

```text
===== SAFETrace AI: Processing Complete =====
Video Duration:     60.0 seconds
Processing Time:    24.3 seconds
Frames Processed:   1800
Total Detections:   5230
Unique Tracks:      14
Average Confidence: 0.87

Annotated video: outputs/annotated_videos/test_annotated.mp4
Tracks CSV:      outputs/tracks/tracks.csv
JSON output:     outputs/tracks/tracks.json
===============================================
```

---

## 9. Integration Instructions for Member 2

1. Call `process_video(video_path, camera_id=...)` from your backend, or
   run it as a subprocess via the CLI and then read `outputs/tracks/tracks.json`.
2. The returned dict's `"tracks"` list is ready to insert into your
   database — each entry already carries a `"status": "Potential Candidate"`
   field. **Do not** relabel or present these as confirmed identifications
   anywhere downstream; they are investigative leads only.
3. `"crop_paths"` / `"person_crops"` are file paths relative to wherever
   the pipeline was run from — copy or serve these files as needed for
   your dashboard/API.
4. `"annotated_video"` is a single playable `.mp4` you can stream or link
   to from the dashboard for human review.
5. The `"performance"` block is provided for logging/monitoring, not
   required for the core UI.

---

## 10. Module Layout

```text
ai/
├── detector.py            # YOLO person detection only
├── tracker.py             # detection + ByteTrack/BoT-SORT tracking, stable IDs
├── video_processor.py     # main pipeline: reads video, orchestrates everything
├── candidate_analyzer.py  # builds "Potential Candidate" records (never confirms identity)
├── config.py               # all settings (model, thresholds, paths)
└── README.md               # this file
```

## 11. Scope Note

This module covers **only** the AI / computer-vision pipeline. It does
**not** include the Streamlit dashboard, FastAPI backend, database, login,
case management, deployment, or documentation for those other pieces —
those are out of scope for Member 1.
