"""
SSL Video-to-Text Data Loader
Handles video preprocessing, augmentation, and MediaPipe hand keypoint extraction
"""

import cv2
import mediapipe as mp
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import List, Tuple, Dict, Optional
import base64
from io import BytesIO
from PIL import Image
import random
import albumentations as A
from albumentations.pytorch import ToTensorV2


class SSLVideoPreprocessor:
    """Handles video preprocessing with MediaPipe Hands and OpenCV"""
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Data augmentation pipeline
        self.augmentation_pipeline = A.Compose([
            A.Rotate(limit=15, p=0.5),
            A.RandomScale(scale_limit=0.1, p=0.5),
            A.GaussNoise(var_limit=(0, 0.05), p=0.3),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])
        
    def extract_hand_keypoints(self, frame: np.ndarray) -> np.ndarray:
        """Extract 21 keypoints per hand using MediaPipe"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        keypoints = np.zeros((2, 21, 3))  # Max 2 hands, 21 keypoints, (x,y,z)
        
        if results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                if hand_idx >= 2:  # Only process first 2 hands
                    break
                    
                for point_idx, landmark in enumerate(hand_landmarks.landmark):
                    keypoints[hand_idx, point_idx] = [
                        landmark.x,
                        landmark.y,
                        landmark.z if hasattr(landmark, 'z') else 0
                    ]
        
        return keypoints
    
    def normalize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Normalize frame with noise reduction"""
        # Resize to standard size
        frame = cv2.resize(frame, (224, 224))
        
        # Noise reduction
        frame = cv2.bilateralFilter(frame, 9, 75, 75)
        
        # Normalize pixel values
        frame = frame.astype(np.float32) / 255.0
        
        return frame
    
    def temporal_jitter(self, sequence: List[np.ndarray], jitter_ratio: float = 0.1) -> List[np.ndarray]:
        """Apply temporal jittering to sequence"""
        if random.random() < 0.5:  # 50% chance to apply jitter
            seq_len = len(sequence)
            jitter_frames = int(seq_len * jitter_ratio)
            
            if jitter_frames > 0:
                # Remove random frames
                indices_to_remove = random.sample(range(seq_len), min(jitter_frames, seq_len - 1))
                sequence = [frame for i, frame in enumerate(sequence) if i not in indices_to_remove]
        
        return sequence
    
    def process_frame(self, frame: np.ndarray, apply_augmentation: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Process single frame and extract features"""
        # Extract hand keypoints
        keypoints = self.extract_hand_keypoints(frame)
        
        # Normalize frame
        normalized_frame = self.normalize_frame(frame)
        
        # Apply augmentation if training
        if apply_augmentation:
            augmented = self.augmentation_pipeline(image=normalized_frame)
            normalized_frame = augmented['image']
        
        return normalized_frame, keypoints


class SSL400Dataset(Dataset):
    """Dataset class for SSL400 with support for few-shot learning"""
    
    def __init__(
        self, 
        video_paths: List[str], 
        labels: List[str], 
        sequence_length: int = 32,
        is_training: bool = True,
        few_shot_classes: Optional[List[str]] = None
    ):
        self.video_paths = video_paths
        self.labels = labels
        self.sequence_length = sequence_length
        self.is_training = is_training
        self.preprocessor = SSLVideoPreprocessor()
        
        # Create label to index mapping
        unique_labels = list(set(labels))
        self.label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
        self.idx_to_label = {idx: label for label, idx in self.label_to_idx.items()}
        
        # Few-shot learning support
        self.few_shot_classes = few_shot_classes or []
        
    def __len__(self) -> int:
        return len(self.video_paths)
    
    def __getitem__(self, idx: int) -> Dict:
        video_path = self.video_paths[idx]
        label = self.labels[idx]
        
        # Load video sequence
        frames, keypoints = self._load_video_sequence(video_path)
        
        # Convert label to index
        label_idx = self.label_to_idx[label]
        
        return {
            'frames': torch.stack(frames),  # [seq_len, 3, 224, 224]
            'keypoints': torch.tensor(keypoints, dtype=torch.float32),  # [seq_len, 2, 21, 3]
            'label': torch.tensor(label_idx, dtype=torch.long),
            'label_text': label,
            'video_path': video_path
        }
    
    def _load_video_sequence(self, video_path: str) -> Tuple[List[torch.Tensor], np.ndarray]:
        """Load and process video sequence"""
        cap = cv2.VideoCapture(video_path)
        frames = []
        keypoints_sequence = []
        
        frame_count = 0
        while cap.read()[0] and frame_count < self.sequence_length:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process frame
            processed_frame, keypoints = self.preprocessor.process_frame(
                frame, apply_augmentation=self.is_training
            )
            
            frames.append(processed_frame)
            keypoints_sequence.append(keypoints)
            frame_count += 1
        
        cap.release()
        
        # Pad or truncate sequence to fixed length
        while len(frames) < self.sequence_length:
            frames.append(torch.zeros_like(frames[-1]) if frames else torch.zeros(3, 224, 224))
            keypoints_sequence.append(np.zeros((2, 21, 3)))
        
        frames = frames[:self.sequence_length]
        keypoints_sequence = np.array(keypoints_sequence[:self.sequence_length])
        
        # Apply temporal jittering if training
        if self.is_training:
            frames = self.preprocessor.temporal_jitter(frames)
        
        return frames, keypoints_sequence


def create_ssl_dataloader(
    video_paths: List[str],
    labels: List[str],
    batch_size: int = 8,
    sequence_length: int = 32,
    is_training: bool = True,
    num_workers: int = 4
) -> DataLoader:
    """Create DataLoader for SSL dataset"""
    dataset = SSL400Dataset(
        video_paths=video_paths,
        labels=labels,
        sequence_length=sequence_length,
        is_training=is_training
    )
    
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=is_training,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=is_training
    )


def decode_base64_frame(base64_string: str) -> np.ndarray:
    """Decode base64 encoded frame for API endpoint"""
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data))
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    return frame


if __name__ == "__main__":
    # Example usage
    preprocessor = SSLVideoPreprocessor()
    
    # Test with sample frame
    sample_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    processed_frame, keypoints = preprocessor.process_frame(sample_frame)
    
    print(f"Processed frame shape: {processed_frame.shape}")
    print(f"Keypoints shape: {keypoints.shape}")
    print(f"Sample keypoints (first hand, first 3 points): {keypoints[0, :3]}")
