"""
Landmark Utilities Module
Handles preprocessing of landmark sequences for model inference
"""

import logging
import numpy as np
from typing import List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Model input dimensions
SEQUENCE_LENGTH = 50  # Number of frames
FEATURES_PER_FRAME = 132  # 33 landmarks × 4 values (x, y, z, visibility)

# MediaPipe pose landmark indices (used for body-center normalization)
LM_LEFT_SHOULDER  = 11
LM_RIGHT_SHOULDER = 12
LM_LEFT_HIP       = 23
LM_RIGHT_HIP      = 24


class LandmarkFrame(BaseModel):
    """Single frame of landmark data"""
    landmarks: List[float]


def _normalize_sequence(seq: np.ndarray) -> np.ndarray:
    """
    Normalize a (frames, 132) sequence to be position- and scale-invariant.

    For every frame:
      1. Body center = mean x/y of left shoulder, right shoulder, left hip, right hip
      2. Scale       = Euclidean distance between left shoulder and right shoulder
      3. Subtract center from all landmark x, y; divide x, y, z by scale
      4. Visibility values (every 4th element) are left unchanged

    This exactly mirrors the normalize_sequence() used in retrain_fixed.py so that
    inference coordinates match training coordinates.
    """
    seq = seq.copy()
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
        scale    = np.sqrt((rs_x - ls_x) ** 2 + (rs_y - ls_y) ** 2)
        if scale < 1e-6:
            scale = 1.0

        for lm in range(33):
            base = lm * 4
            frame[base]     = (frame[base]     - center_x) / scale  # x
            frame[base + 1] = (frame[base + 1] - center_y) / scale  # y
            frame[base + 2] =  frame[base + 2]              / scale  # z
            # base+3 is visibility — unchanged

        seq[f] = frame
    return seq


def preprocess_landmarks(sequence: List[LandmarkFrame]) -> np.ndarray:
    """
    Preprocess landmark sequence for model inference.

    Converts raw webcam MediaPipe coordinates to a body-center-normalized
    representation that matches the training pipeline in retrain_fixed.py.

    Returns:
        np.ndarray of shape (1, 50, 132) ready for model.predict()
    """
    try:
        if len(sequence) != SEQUENCE_LENGTH:
            raise ValueError(f"Expected {SEQUENCE_LENGTH} frames, got {len(sequence)}")

        frames_list = []
        for i, frame in enumerate(sequence):
            landmarks = frame.landmarks
            if len(landmarks) != FEATURES_PER_FRAME:
                raise ValueError(
                    f"Frame {i}: Expected {FEATURES_PER_FRAME} features, got {len(landmarks)}"
                )
            frames_list.append(landmarks)

        # Shape: (50, 132)
        sequence_array = np.array(frames_list, dtype=np.float32)

        # Apply the same body-center + shoulder-width normalization used during training
        sequence_array = _normalize_sequence(sequence_array)
        logger.info(f"Normalized sequence shape: {sequence_array.shape}")

        # Add batch dimension → (1, 50, 132)
        return np.expand_dims(sequence_array, axis=0)

    except Exception as e:
        logger.error(f"Failed to preprocess landmarks: {e}")
        raise ValueError(f"Landmark preprocessing failed: {e}")


def normalize_landmarks(landmarks: np.ndarray) -> np.ndarray:
    """
    Normalize landmark coordinates (optional utility)
    
    Args:
        landmarks: Raw landmark coordinates
        
    Returns:
        Normalized landmarks
    """
    # Add normalization logic if needed
    # For example: center around origin, scale to unit range, etc.
    return landmarks


def validate_landmark_format(frame: LandmarkFrame) -> bool:
    """
    Validate that a landmark frame has correct format
    
    Args:
        frame: LandmarkFrame object
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(frame.landmarks, list):
        return False
    
    if len(frame.landmarks) != FEATURES_PER_FRAME:
        return False
    
    # Check all values are numeric
    try:
        [float(x) for x in frame.landmarks]
        return True
    except (ValueError, TypeError):
        return False
