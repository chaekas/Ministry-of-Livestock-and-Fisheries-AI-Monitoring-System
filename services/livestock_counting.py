"""Livestock counting helpers using a locally configured YOLO model."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

DEFAULT_MODEL_PATH = "models/livestock_counting.pt"


def get_model_path() -> Path:
    """Return the configured livestock model path."""
    return Path(os.getenv("LIVESTOCK_YOLO_MODEL", DEFAULT_MODEL_PATH))


def load_model() -> Any:
    """Load trained livestock weights; never silently substitute a generic model."""
    model_path = get_model_path()
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Livestock detection weights were not found at '{model_path}'. "
            "Place a suitable trained livestock YOLO model there or set "
            "LIVESTOCK_YOLO_MODEL to its path."
        )
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "YOLO dependencies are not installed. Install requirements-ai.txt "
            "in a compatible Python environment."
        ) from exc
    return YOLO(str(model_path))


def count_video_sampled_frames(
    model: Any,
    video_path: str,
    confidence: float = 0.35,
    sample_every: int = 15,
    max_samples: int = 120,
) -> list[dict[str, int]]:
    """Count detections in sampled frames; this is not a unique-animal total."""
    import cv2

    if sample_every < 1 or max_samples < 1:
        raise ValueError("Sampling settings must be positive integers.")
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise ValueError("The uploaded video could not be opened.")
    results: list[dict[str, int]] = []
    frame_index = 0
    sampled = 0
    try:
        while sampled < max_samples:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % sample_every == 0:
                prediction = model.predict(source=frame, conf=confidence, verbose=False)[0]
                count = 0 if prediction.boxes is None else len(prediction.boxes)
                results.append({"frame": frame_index, "animal_count": count})
                sampled += 1
            frame_index += 1
    finally:
        capture.release()
    if not results:
        raise ValueError("No readable frames were found in the uploaded video.")
    return results
