"""
video_processor.py
-------------------
Main processing pipeline for the SAFETrace AI computer-vision module.

Given a CCTV / sample video, this module:
  1. Opens the video and reads its metadata (FPS, frame count).
  2. Processes it frame by frame.
  3. Detects and tracks people (via tracker.py).
  4. Draws bounding boxes, Track IDs, confidence, and timestamp.
  5. Saves representative person crops (not every frame).
  6. Writes an annotated output video.
  7. Builds per-track summaries.
  8. Writes tracks.csv and a structured JSON output.
  9. Returns a structured dict that Member 2 can consume directly.

This module works standalone (no Streamlit / dashboard dependency) and
can be run from the command line or imported as a library.
"""

import argparse
import json
import os
import time
from collections import defaultdict

import cv2
import pandas as pd

try:
    from . import config
    from .tracker import PersonTracker
    from .candidate_analyzer import build_candidates
except ImportError:  # allows `python video_processor.py` direct execution
    import config
    from tracker import PersonTracker
    from candidate_analyzer import build_candidates


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def format_timestamp(frame_number: int, fps: float) -> str:
    """Convert a frame number into an HH:MM:SS.ss timestamp string."""
    if fps <= 0:
        fps = 30.0  # sane fallback if video metadata is missing/broken
    total_seconds = frame_number / fps
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"


def _safe_crop(frame, bbox):
    """Crop a frame to bbox, clamping to frame bounds. Returns None if invalid."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    if (x2 - x1) < config.MIN_CROP_WIDTH or (y2 - y1) < config.MIN_CROP_HEIGHT:
        return None
    return frame[y1:y2, x1:x2]


def _draw_annotations(frame, tracks, timestamp_str):
    """Draw bounding boxes, track IDs, confidence, and timestamp on a frame."""
    for t in tracks:
        x1, y1, x2, y2 = t["bbox"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), config.BOX_COLOR, config.BOX_THICKNESS)

        label = f"ID {t['track_id']} | {t['confidence']:.2f}"
        (text_w, text_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, config.TEXT_SCALE, config.TEXT_THICKNESS
        )
        cv2.rectangle(
            frame,
            (x1, max(0, y1 - text_h - 8)),
            (x1 + text_w + 4, y1),
            config.BOX_COLOR,
            -1,
        )
        cv2.putText(
            frame,
            label,
            (x1 + 2, max(text_h, y1 - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            config.TEXT_SCALE,
            config.TEXT_COLOR,
            config.TEXT_THICKNESS,
            cv2.LINE_AA,
        )

    # Video timestamp, top-left corner
    cv2.putText(
        frame,
        timestamp_str,
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return frame


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_video(
    video_path,
    output_video_path=None,
    crop_output_directory=None,
    camera_id=None,
    csv_output_path=None,
    json_output_path=None,
):
    """
    Process a CCTV/sample video end-to-end and produce all SAFETrace
    outputs (annotated video, person crops, tracks.csv, structured JSON).

    Args:
        video_path (str): path to the input video.
        output_video_path (str, optional): where to save the annotated
            video. Defaults to outputs/annotated_videos/<name>_annotated.mp4
        crop_output_directory (str, optional): base directory for person
            crops. Defaults to outputs/person_crops/
        camera_id (str, optional): identifier for the source camera, e.g.
            "CAM-01". Passed straight through to the structured output for
            Member 2's database.
        csv_output_path (str, optional): where to save tracks.csv.
            Defaults to outputs/tracks/tracks.csv
        json_output_path (str, optional): where to save the JSON output.
            Defaults to outputs/tracks/tracks.json

    Returns:
        dict: structured output described in the AI module spec, e.g.
            {
                "video_path": ...,
                "camera_id": ...,
                "tracks": [...],
                "annotated_video": ...,
                "person_crops": [...],
                "performance": {...}
            }
    """
    config.ensure_output_dirs()

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Input video not found: {video_path}")

    video_name = os.path.splitext(os.path.basename(video_path))[0]

    output_video_path = output_video_path or os.path.join(
        config.ANNOTATED_VIDEOS_DIR, f"{video_name}_annotated.mp4"
    )
    crop_output_directory = crop_output_directory or config.PERSON_CROPS_DIR
    csv_output_path = csv_output_path or config.TRACKS_CSV_PATH
    json_output_path = json_output_path or config.TRACKS_JSON_PATH

    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
    os.makedirs(crop_output_directory, exist_ok=True)
    os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*config.OUTPUT_VIDEO_CODEC)
    writer = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    tracker = PersonTracker()
    tracker.reset()

    # Raw per-detection records (one row per person per frame)
    detection_records = []

    # Per-track bookkeeping for summaries and crop saving
    track_first_frame = {}
    track_last_frame = {}
    track_confidences = defaultdict(list)
    track_frame_count = defaultdict(int)
    track_crops_saved = defaultdict(int)
    track_crop_paths = defaultdict(list)
    track_last_crop_frame = defaultdict(lambda: -config.CROP_SAVE_INTERVAL)

    frame_number = 0
    total_detections = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp_str = format_timestamp(frame_number, fps)
        tracks = tracker.update(frame)
        total_detections += len(tracks)

        for t in tracks:
            track_id = t["track_id"]
            bbox = t["bbox"]
            confidence = t["confidence"]

            # 1. Record raw detection info
            detection_records.append(
                {
                    "track_id": track_id,
                    "frame_number": frame_number,
                    "timestamp": timestamp_str,
                    "x1": bbox[0],
                    "y1": bbox[1],
                    "x2": bbox[2],
                    "y2": bbox[3],
                    "confidence": confidence,
                }
            )

            # 2. Update per-track bookkeeping
            if track_id not in track_first_frame:
                track_first_frame[track_id] = frame_number
            track_last_frame[track_id] = frame_number
            track_confidences[track_id].append(confidence)
            track_frame_count[track_id] += 1

            # 3. Save a representative crop every N frames (not every frame)
            frames_since_last_crop = frame_number - track_last_crop_frame[track_id]
            if (
                frames_since_last_crop >= config.CROP_SAVE_INTERVAL
                and track_crops_saved[track_id] < config.MAX_CROPS_PER_TRACK
            ):
                crop = _safe_crop(frame, bbox)
                if crop is not None:
                    track_dir = os.path.join(crop_output_directory, f"track_{track_id}")
                    os.makedirs(track_dir, exist_ok=True)
                    crop_filename = f"frame_{frame_number}.jpg"
                    crop_path = os.path.join(track_dir, crop_filename)
                    cv2.imwrite(crop_path, crop)

                    track_crop_paths[track_id].append(crop_path)
                    track_crops_saved[track_id] += 1
                    track_last_crop_frame[track_id] = frame_number

        # 4. Draw annotations and write the frame to the output video
        annotated_frame = _draw_annotations(frame, tracks, timestamp_str)
        writer.write(annotated_frame)

        frame_number += 1

    cap.release()
    writer.release()

    processing_time = time.time() - start_time

    # -----------------------------------------------------------------
    # Build per-track summaries
    # -----------------------------------------------------------------
    track_summaries = []
    for track_id in sorted(track_first_frame.keys()):
        first_frame = track_first_frame[track_id]
        last_frame = track_last_frame[track_id]
        confidences = track_confidences[track_id]
        avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0
        duration_seconds = round((last_frame - first_frame) / fps, 2) if fps > 0 else 0.0

        track_summaries.append(
            {
                "track_id": track_id,
                "first_seen": format_timestamp(first_frame, fps),
                "last_seen": format_timestamp(last_frame, fps),
                "duration": duration_seconds,
                "frame_count": track_frame_count[track_id],
                "average_confidence": avg_confidence,
                "crop_paths": track_crop_paths[track_id],
            }
        )

    # -----------------------------------------------------------------
    # Save tracks.csv (detection-level rows -- one row per person per frame)
    # -----------------------------------------------------------------
    detections_df = pd.DataFrame(detection_records)
    detections_df.to_csv(csv_output_path, index=False)

    # Also save a separate, smaller track-level summary CSV alongside it
    summary_csv_path = os.path.join(
        os.path.dirname(csv_output_path), "track_summary.csv"
    )
    summary_df = pd.DataFrame(
        [
            {
                "track_id": s["track_id"],
                "first_seen": s["first_seen"],
                "last_seen": s["last_seen"],
                "duration": s["duration"],
                "frame_count": s["frame_count"],
                "average_confidence": s["average_confidence"],
            }
            for s in track_summaries
        ]
    )
    summary_df.to_csv(summary_csv_path, index=False)

    # -----------------------------------------------------------------
    # Build Potential Candidate records (never a confirmed identity)
    # -----------------------------------------------------------------
    candidates = build_candidates(track_summaries)

    all_crop_paths = [p for s in track_summaries for p in s["crop_paths"]]

    performance = {
        "video_duration_seconds": round(total_frames / fps, 2) if fps > 0 else None,
        "processing_time_seconds": round(processing_time, 2),
        "frames_processed": frame_number,
        "total_detections": total_detections,
        "unique_tracks": len(track_summaries),
        "average_confidence": (
            round(
                sum(sum(c) for c in track_confidences.values())
                / sum(len(c) for c in track_confidences.values()),
                4,
            )
            if track_confidences
            else 0.0
        ),
    }

    structured_output = {
        "video_path": video_path,
        "camera_id": camera_id,
        "tracks": candidates,
        "annotated_video": output_video_path,
        "person_crops": all_crop_paths,
        "performance": performance,
    }

    with open(json_output_path, "w") as f:
        json.dump(structured_output, f, indent=2)

    _print_summary(performance, output_video_path, csv_output_path, json_output_path)

    return structured_output


def _print_summary(performance, output_video_path, csv_output_path, json_output_path):
    print("\n===== SAFETrace AI: Processing Complete =====")
    print(f"Video Duration:     {performance['video_duration_seconds']} seconds")
    print(f"Processing Time:    {performance['processing_time_seconds']} seconds")
    print(f"Frames Processed:   {performance['frames_processed']}")
    print(f"Total Detections:   {performance['total_detections']}")
    print(f"Unique Tracks:      {performance['unique_tracks']}")
    print(f"Average Confidence: {performance['average_confidence']}")
    print(f"\nAnnotated video: {output_video_path}")
    print(f"Tracks CSV:      {csv_output_path}")
    print(f"JSON output:     {json_output_path}")
    print("===============================================\n")


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def _parse_args():
    parser = argparse.ArgumentParser(
        description="SAFETrace AI - CCTV video person detection & tracking"
    )
    parser.add_argument(
        "--input", required=True, help="Path to input video, e.g. data/sample_videos/test.mp4"
    )
    parser.add_argument("--output-video", default=None, help="Path for the annotated output video")
    parser.add_argument("--crop-dir", default=None, help="Directory to save person crops")
    parser.add_argument("--camera-id", default=None, help="Optional camera identifier, e.g. CAM-01")
    parser.add_argument("--csv-output", default=None, help="Path for tracks.csv")
    parser.add_argument("--json-output", default=None, help="Path for the structured JSON output")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    process_video(
        video_path=args.input,
        output_video_path=args.output_video,
        crop_output_directory=args.crop_dir,
        camera_id=args.camera_id,
        csv_output_path=args.csv_output,
        json_output_path=args.json_output,
    )
