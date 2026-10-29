"""Fish counting inference helpers using a configured custom YOLO model."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

DEFAULT_MODEL_PATH = "models/fish_counting.pt"


def get_model_path() -> Path:
    """Return the configured fish YOLO weights path."""
    return Path(os.getenv("FISH_YOLO_MODEL", DEFAULT_MODEL_PATH))


def load_model() -> Any:
    """Load the configured YOLO model, raising a clear error if unavailable."""
    model_path = get_model_path()
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Fish detection weights were not found at '{model_path}'. "
            "Place a suitable trained fish-detection .pt file there or set "
            "FISH_YOLO_MODEL to its path."
        )
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "YOLO dependencies are not installed. Follow README.md to install "
            "the optional AI requirements in a compatible Python environment."
        ) from exc
    return YOLO(str(model_path))


def count_image(model: Any, image: Any, confidence: float = 0.35) -> tuple[int, Any]:
    """Count detections in one uploaded image and return count plus annotated RGB image."""
    import cv2

    results = model.predict(source=image, conf=confidence, verbose=False)
    result = results[0]
    count = 0 if result.boxes is None else len(result.boxes)
    annotated_bgr = result.plot()
    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
    return count, annotated_rgb


def count_video_sampled_frames(
    model: Any,
    video_path: str,
    confidence: float = 0.35,
    sample_every: int = 15,
    max_samples: int = 120,
) -> list[dict[str, int]]:
    """Count detections in sampled frames; this is not a unique-animal video count."""
    import cv2

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
                results.append({"frame": frame_index, "fish_count": count})
                sampled += 1
            frame_index += 1
    finally:
        capture.release()
    if not results:
        raise ValueError("No readable frames were found in the uploaded video.")
    return results
