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
FEATURES_PER_FRAME = 132  # NEW MODEL: 33 landmarks × 4 values (x, y, z, visibility)


class LandmarkFrame(BaseModel):
    """Single frame of landmark data"""
    landmarks: List[float]


def preprocess_landmarks(sequence: List[LandmarkFrame]) -> np.ndarray:
    """
    Preprocess landmark sequence for model inference
    
    Args:
        sequence: List of 50 LandmarkFrame objects, each containing landmark coordinates
        
    Returns:
        Preprocessed numpy array ready for model input
        Shape: (1, 50, 132) - batch_size=1, 50 frames, 132 features per frame
        
    Raises:
        ValueError: If sequence length or feature count is incorrect
    """
    try:
        # Validate sequence length
        if len(sequence) != SEQUENCE_LENGTH:
            raise ValueError(
                f"Expected {SEQUENCE_LENGTH} frames, got {len(sequence)}"
            )
        
        # Convert to numpy array
        frames_list = []
        for i, frame in enumerate(sequence):
            landmarks = frame.landmarks
            
            # Validate number of features
            if len(landmarks) != FEATURES_PER_FRAME:
                raise ValueError(
                    f"Frame {i}: Expected {FEATURES_PER_FRAME} features, got {len(landmarks)}"
                )
            
            frames_list.append(landmarks)
        
        # Stack into array: (50, 132)
        sequence_array = np.array(frames_list, dtype=np.float32)
        logger.info(f"Sequence array shape: {sequence_array.shape}")
        
        # Expand dimensions to add batch: (1, 50, 132)
        sequence_array = np.expand_dims(sequence_array, axis=0)
        logger.info(f"Final shape: {sequence_array.shape}")
        
        return sequence_array
        
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
