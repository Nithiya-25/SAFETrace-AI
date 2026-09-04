"""
config.py
---------
Central configuration for the SAFETrace AI computer-vision module.

Keep this file simple. Every other module imports its settings from here
so behaviour can be tuned in one place without touching pipeline code.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Root of the SAFETrace project (this file lives in <ROOT>/ai/config.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
SAMPLE_VIDEOS_DIR = os.path.join(DATA_DIR, "sample_videos")

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
ANNOTATED_VIDEOS_DIR = os.path.join(OUTPUT_DIR, "annotated_videos")
PERSON_CROPS_DIR = os.path.join(OUTPUT_DIR, "person_crops")
TRACKS_DIR = os.path.join(OUTPUT_DIR, "tracks")

TRACKS_CSV_PATH = os.path.join(TRACKS_DIR, "tracks.csv")
TRACKS_JSON_PATH = os.path.join(TRACKS_DIR, "tracks.json")

# ---------------------------------------------------------------------------
# YOLO detection settings
# ---------------------------------------------------------------------------

# Any Ultralytics YOLO weights file works here. "yolov8n.pt" (nano) is the
# fastest / smallest and is a good default for a Round-1 prototype.
# It is auto-downloaded by ultralytics the first time it is used.
YOLO_MODEL_NAME = "yolov8n.pt"

# COCO class id for "person"
PERSON_CLASS_ID = 0

# Minimum confidence for a detection to be kept
CONFIDENCE_THRESHOLD = 0.40

# ---------------------------------------------------------------------------
# Tracking settings
# ---------------------------------------------------------------------------

# Ultralytics ships tracker configs for both algorithms:
#   "bytetrack.yaml"  -> ByteTrack
#   "botsort.yaml"    -> BoT-SORT
TRACKER_TYPE = "bytetrack.yaml"

# ---------------------------------------------------------------------------
# Crop saving settings
# ---------------------------------------------------------------------------

# Save one representative crop every N frames a track is visible
# (i.e. NOT every single frame -- keeps disk usage sane).
CROP_SAVE_INTERVAL = 30

# Hard cap on how many crops we keep per track
MAX_CROPS_PER_TRACK = 5

# Minimum crop size (in pixels) to bother saving -- filters out tiny,
# low-quality boxes far in the background.
MIN_CROP_WIDTH = 20
MIN_CROP_HEIGHT = 40

# ---------------------------------------------------------------------------
# Video processing settings
# ---------------------------------------------------------------------------

# Resize frames before running inference for speed. Set to None to disable.
INFERENCE_FRAME_WIDTH = None  # e.g. 960 to downscale, None = original size

# Annotated output video codec (mp4 container, widely compatible)
OUTPUT_VIDEO_CODEC = "mp4v"

# Drawing settings for the annotated video
BOX_COLOR = (0, 200, 0)          # BGR
BOX_THICKNESS = 2
TEXT_COLOR = (255, 255, 255)     # BGR
TEXT_SCALE = 0.55
TEXT_THICKNESS = 1

# ---------------------------------------------------------------------------
# Candidate status labels
#
# IMPORTANT: SAFETrace never confirms an identity. Every track produced by
# this module is only ever labelled as a "Potential Candidate" / lead for a
# human investigator to review.
# ---------------------------------------------------------------------------

STATUS_POTENTIAL_CANDIDATE = "Potential Candidate"


def ensure_output_dirs():
    """Create every output directory this module writes to, if missing."""
    for d in (
        SAMPLE_VIDEOS_DIR,
        ANNOTATED_VIDEOS_DIR,
        PERSON_CROPS_DIR,
        TRACKS_DIR,
    ):
        os.makedirs(d, exist_ok=True)
