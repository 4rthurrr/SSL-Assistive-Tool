"""
Landmark Utilities Module
Handles preprocessing of landmark sequences for model inference.
Supports both production pose-only input (132 features) and future
pose+hand input (300 features).
"""

import logging
import numpy as np
from typing import List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Model input dimensions
SEQUENCE_LENGTH = 50  # Number of frames
POSE_FEATURES_PER_FRAME = 132  # 33 pose landmarks x 4 values
FULL_FEATURES_PER_FRAME = 300  # 33 pose + 21 left hand + 21 right hand x 4
SUPPORTED_FEATURE_COUNTS = {POSE_FEATURES_PER_FRAME, FULL_FEATURES_PER_FRAME}
FEATURES_PER_FRAME = 300  # 75 landmarks × 4 values (x, y, z, visibility/presence)

# MediaPipe pose landmark indices (used for body-center normalization)
LM_LEFT_SHOULDER  = 11
LM_RIGHT_SHOULDER = 12
LM_LEFT_HIP       = 23
LM_RIGHT_HIP      = 24


class LandmarkFrame(BaseModel):
    """Single frame of landmark data"""
    landmarks: List[float]


def _normalize_sequence(seq: np.ndarray, center_z_axis: bool = True) -> np.ndarray:
    """
    Normalize a (frames, N) sequence to be position- and scale-invariant.
    Works with both 132 features (33 pose) and 300 features (75 landmarks).

    For every frame:
      1. Body center = mean x/y/z of left shoulder, right shoulder, left hip, right hip
      2. Scale       = Euclidean distance between left shoulder and right shoulder
      3. Subtract center from all landmark x, y, z; divide x, y, z by scale
      4. Visibility/presence values (every 4th element) are left unchanged

    This exactly mirrors the normalize_sequence() used in retrain_fixed.py so that
    inference coordinates match training coordinates.
    """
    seq = seq.copy()
    n_landmarks = seq.shape[1] // 4  # 33 for 132, 75 for 300

    for f in range(seq.shape[0]):
        frame = seq[f]

        ls_x = frame[LM_LEFT_SHOULDER  * 4]
        ls_y = frame[LM_LEFT_SHOULDER  * 4 + 1]
        rs_x = frame[LM_RIGHT_SHOULDER * 4]
        rs_y = frame[LM_RIGHT_SHOULDER * 4 + 1]
        lh_x = frame[LM_LEFT_HIP       * 4]
        lh_y = frame[LM_LEFT_HIP       * 4 + 1]
        rh_x = frame[LM_RIGHT_HIP      * 4]
        rh_y = frame[LM_RIGHT_HIP      * 4 + 1]

        center_x = (ls_x + rs_x + lh_x + rh_x) / 4.0
        center_y = (ls_y + rs_y + lh_y + rh_y) / 4.0

        # Z center: average depth of the 4 anchor landmarks
        ls_z = frame[LM_LEFT_SHOULDER  * 4 + 2]
        rs_z = frame[LM_RIGHT_SHOULDER * 4 + 2]
        lh_z = frame[LM_LEFT_HIP       * 4 + 2]
        rh_z = frame[LM_RIGHT_HIP      * 4 + 2]
        center_z = (ls_z + rs_z + lh_z + rh_z) / 4.0

        scale    = np.sqrt((rs_x - ls_x) ** 2 + (rs_y - ls_y) ** 2)
        if scale < 1e-6:
            scale = 1.0

        for lm in range(n_landmarks):
            base = lm * 4
            # Preserve missing landmarks. This is especially important for the
            # hands300 model: a missing hand arrives as all zeros. If we
            # normalize those zeros against the body center, the model sees a
            # fake hand location instead of "hand not detected".
            if frame[base + 3] <= 1e-8 and np.all(np.abs(frame[base:base + 3]) <= 1e-8):
                frame[base:base + 4] = 0.0
                continue

            frame[base]     = (frame[base]     - center_x) / scale  # x
            frame[base + 1] = (frame[base + 1] - center_y) / scale  # y
            if center_z_axis:
                frame[base + 2] = (frame[base + 2] - center_z) / scale  # z
            else:
                frame[base + 2] = frame[base + 2] / scale  # z, legacy pose-only model
            # base+3 is visibility/presence — unchanged

        seq[f] = frame
    return seq


def _coerce_features(landmarks: List[float], expected_features: int, frame_index: int) -> List[float]:
    """Match one frame to the loaded model's expected feature count."""
    actual_features = len(landmarks)

    if expected_features not in SUPPORTED_FEATURE_COUNTS:
        raise ValueError(
            f"Unsupported model input width: {expected_features}. "
            f"Supported widths are {sorted(SUPPORTED_FEATURE_COUNTS)}"
        )

    if actual_features == expected_features:
        return landmarks

    if expected_features == POSE_FEATURES_PER_FRAME and actual_features == FULL_FEATURES_PER_FRAME:
        return landmarks[:POSE_FEATURES_PER_FRAME]

    if expected_features == FULL_FEATURES_PER_FRAME and actual_features == POSE_FEATURES_PER_FRAME:
        raise ValueError(
            f"Frame {frame_index}: Expected 300 features, got 132. "
            "The loaded model requires pose+hand landmarks, but the request contains pose-only data."
        )

    accepted = (
        f"{POSE_FEATURES_PER_FRAME} or {FULL_FEATURES_PER_FRAME}"
        if expected_features == POSE_FEATURES_PER_FRAME
        else str(expected_features)
    )
    raise ValueError(f"Frame {frame_index}: Expected {accepted} features, got {actual_features}")


def preprocess_landmarks(
    sequence: List[LandmarkFrame],
    expected_features: int = FULL_FEATURES_PER_FRAME,
) -> np.ndarray:
    """
    Preprocess landmark sequence for model inference.

    Converts raw webcam MediaPipe coordinates to a body-center-normalized
    representation that matches the loaded model.

    If the loaded model is pose-only (132 features), a full 300-feature
    frontend frame is safely trimmed to the first 132 pose features.

    Returns:
        np.ndarray of shape (1, 50, expected_features) ready for model.predict()
    """
    try:
        if len(sequence) != SEQUENCE_LENGTH:
            raise ValueError(f"Expected {SEQUENCE_LENGTH} frames, got {len(sequence)}")

        frames_list = []
        for i, frame in enumerate(sequence):
            landmarks = _coerce_features(frame.landmarks, expected_features, i)
            frames_list.append(landmarks)

        # Shape: (50, expected_features)
        sequence_array = np.array(frames_list, dtype=np.float32)

        # Apply the same normalization used during training.
        # The deployed 132-feature model used z / scale. The newer 300-feature
        # hand pipeline uses z-centering as well.
        sequence_array = _normalize_sequence(
            sequence_array,
            center_z_axis=(expected_features == FULL_FEATURES_PER_FRAME),
        )
        logger.info(f"Normalized sequence shape: {sequence_array.shape}")

        # Add batch dimension → (1, 50, 300)
        return np.expand_dims(sequence_array, axis=0)

    except Exception as e:
        logger.error(f"Failed to preprocess landmarks: {e}")
        raise ValueError(f"Landmark preprocessing failed: {e}")


def validate_landmark_format(
    frame: LandmarkFrame,
    expected_features: int = FULL_FEATURES_PER_FRAME,
) -> bool:
    """
    Validate that a landmark frame has correct format
    """
    if not isinstance(frame.landmarks, list):
        return False

    try:
        _coerce_features(frame.landmarks, expected_features, 0)
    except ValueError:
        return False

    try:
        [float(x) for x in frame.landmarks]
        return True
    except (ValueError, TypeError):
        return False
