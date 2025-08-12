"""
SSL Video-to-Text Inference API
Real-time SSL translation API with timestamped output
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import numpy as np
import cv2
import base64
from io import BytesIO
from PIL import Image
import time
from typing import Dict, List, Optional, Tuple
import asyncio
import uvicorn
import logging
from datetime import datetime
import json
import os

from model import create_ssl_model
from data_loader import SSLVideoPreprocessor, decode_base64_frame


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API
class VideoFrameRequest(BaseModel):
    video_frame: str  # base64-encoded image
    timestamp_ms: int


class TranslationResponse(BaseModel):
    text: str
    confidence: float
    timestamp_ms: int
    processing_time_ms: float


class BatchTranslationRequest(BaseModel):
    frames: List[VideoFrameRequest]


class BatchTranslationResponse(BaseModel):
    translations: List[TranslationResponse]
    total_processing_time_ms: float


class ModelStatus(BaseModel):
    status: str
    model_loaded: bool
    supported_classes: int
    version: str


class SSLTranslationAPI:
    """SSL Video-to-Text Translation API Server"""
    
    def __init__(self, model_path: str, config_path: Optional[str] = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.preprocessor = SSLVideoPreprocessor()
        self.class_names = []
        self.model_loaded = False
        
        # Load model configuration
        self.config = self.load_config(config_path) if config_path else {}
        
        # Sequence buffer for temporal modeling
        self.sequence_length = self.config.get('sequence_length', 32)
        self.frame_buffer = []
        self.keypoint_buffer = []
        
        # Load model
        self.load_model(model_path)
        
        # Performance tracking
        self.inference_times = []
        
    def load_config(self, config_path: str) -> Dict:
        """Load model configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def load_model(self, model_path: str):
        """Load trained SSL model"""
        try:
            logger.info(f"Loading model from {model_path}")
            
            # Load checkpoint
            checkpoint = torch.load(model_path, map_location=self.device)
            
            # Extract configuration from checkpoint
            if 'config' in checkpoint:
                model_config = checkpoint['config']
            else:
                # Default configuration
                model_config = {
                    'num_classes': 400,
                    'sequence_model': 'lstm',
                    'pretrained_backbone': True
                }
            
            # Create model
            self.model = create_ssl_model(**model_config)
            
            # Load state dict
            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            
            # Load class names if available
            if 'class_names' in checkpoint:
                self.class_names = checkpoint['class_names']
            else:
                # Create default class names
                self.class_names = [f"class_{i}" for i in range(model_config['num_classes'])]
            
            self.model_loaded = True
            logger.info(f"Model loaded successfully. Classes: {len(self.class_names)}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")
    
    def preprocess_frame(self, frame: np.ndarray) -> Tuple[torch.Tensor, torch.Tensor]:
        """Preprocess single frame"""
        processed_frame, keypoints = self.preprocessor.process_frame(
            frame, apply_augmentation=False
        )
        
        # Convert to tensors
        if isinstance(processed_frame, np.ndarray):
            processed_frame = torch.from_numpy(processed_frame).float()
        
        keypoints_tensor = torch.from_numpy(keypoints).float()
        
        return processed_frame, keypoints_tensor
    
    def update_sequence_buffer(self, frame: torch.Tensor, keypoints: torch.Tensor):
        """Update sequence buffer for temporal modeling"""
        self.frame_buffer.append(frame)
        self.keypoint_buffer.append(keypoints)
        
        # Keep only the last sequence_length frames
        if len(self.frame_buffer) > self.sequence_length:
            self.frame_buffer = self.frame_buffer[-self.sequence_length:]
            self.keypoint_buffer = self.keypoint_buffer[-self.sequence_length:]
    
    def get_sequence_batch(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get padded sequence batch for inference"""
        # Pad sequence if needed
        current_length = len(self.frame_buffer)
        
        if current_length == 0:
            # Return empty tensors
            frames = torch.zeros(1, self.sequence_length, 3, 224, 224)
            keypoints = torch.zeros(1, self.sequence_length, 2, 21, 3)
        else:
            # Pad if sequence is shorter than required
            frames_list = self.frame_buffer.copy()
            keypoints_list = self.keypoint_buffer.copy()
            
            while len(frames_list) < self.sequence_length:
                if len(frames_list) > 0:
                    frames_list.insert(0, frames_list[0])  # Repeat first frame
                    keypoints_list.insert(0, keypoints_list[0])  # Repeat first keypoints
                else:
                    frames_list.append(torch.zeros(3, 224, 224))
                    keypoints_list.append(torch.zeros(2, 21, 3))
            
            # Stack into batches
            frames = torch.stack(frames_list[-self.sequence_length:]).unsqueeze(0)  # [1, seq_len, 3, 224, 224]
            keypoints = torch.stack(keypoints_list[-self.sequence_length:]).unsqueeze(0)  # [1, seq_len, 2, 21, 3]
        
        return frames.to(self.device), keypoints.to(self.device)
    
    async def translate_frame(self, frame_request: VideoFrameRequest) -> TranslationResponse:
        """Translate single frame"""
        if not self.model_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        start_time = time.time()
        
        try:
            # Decode base64 frame
            frame = decode_base64_frame(frame_request.video_frame)
            
            # Preprocess frame
            processed_frame, keypoints = self.preprocess_frame(frame)
            
            # Update sequence buffer
            self.update_sequence_buffer(processed_frame, keypoints)
            
            # Get sequence batch
            frames_batch, keypoints_batch = self.get_sequence_batch()
            
            # Inference
            with torch.no_grad():
                predictions, confidence = self.model.get_predictions(frames_batch, keypoints_batch)
            
            # Convert to text
            predicted_class = predictions.item()
            confidence_score = confidence.item()
            
            if predicted_class < len(self.class_names):
                predicted_text = self.class_names[predicted_class]
            else:
                predicted_text = f"unknown_class_{predicted_class}"
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            self.inference_times.append(processing_time)
            
            return TranslationResponse(
                text=predicted_text,
                confidence=confidence_score,
                timestamp_ms=frame_request.timestamp_ms,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")
    
    async def translate_batch(self, batch_request: BatchTranslationRequest) -> BatchTranslationResponse:
        """Translate batch of frames"""
        start_time = time.time()
        
        translations = []
        for frame_request in batch_request.frames:
            translation = await self.translate_frame(frame_request)
            translations.append(translation)
        
        total_time = (time.time() - start_time) * 1000
        
        return BatchTranslationResponse(
            translations=translations,
            total_processing_time_ms=total_time
        )
    
    def get_status(self) -> ModelStatus:
        """Get API status"""
        return ModelStatus(
            status="running" if self.model_loaded else "error",
            model_loaded=self.model_loaded,
            supported_classes=len(self.class_names),
            version="1.0.0"
        )
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.inference_times:
            return {
                "average_inference_time_ms": 0,
                "min_inference_time_ms": 0,
                "max_inference_time_ms": 0,
                "total_inferences": 0
            }
        
        return {
            "average_inference_time_ms": np.mean(self.inference_times),
            "min_inference_time_ms": np.min(self.inference_times),
            "max_inference_time_ms": np.max(self.inference_times),
            "total_inferences": len(self.inference_times)
        }


# Global API instance
api_instance = None


# FastAPI app
app = FastAPI(
    title="SSL Video-to-Text Translation API",
    description="Real-time Sinhala Sign Language to Text Translation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize API on startup"""
    global api_instance
    
    # Get model path from environment or use default
    model_path = os.getenv("SSL_MODEL_PATH", "models/ssl_translation_best.pth")
    config_path = os.getenv("SSL_CONFIG_PATH", None)
    
    try:
        api_instance = SSLTranslationAPI(model_path, config_path)
        logger.info("SSL Translation API started successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")


@app.post("/ssl/translate", response_model=TranslationResponse)
async def translate_single_frame(frame_request: VideoFrameRequest):
    """
    Translate a single video frame to text
    
    - **video_frame**: Base64-encoded image
    - **timestamp_ms**: Timestamp in milliseconds
    """
    if not api_instance:
        raise HTTPException(status_code=503, detail="API not initialized")
    
    return await api_instance.translate_frame(frame_request)


@app.post("/ssl/translate/batch", response_model=BatchTranslationResponse)
async def translate_batch_frames(batch_request: BatchTranslationRequest):
    """
    Translate a batch of video frames to text
    
    - **frames**: List of video frames with timestamps
    """
    if not api_instance:
        raise HTTPException(status_code=503, detail="API not initialized")
    
    return await api_instance.translate_batch(batch_request)


@app.post("/ssl/translate/video")
async def translate_video_file(video: UploadFile = File(...)):
    """
    Translate an uploaded video file
    
    - **video**: Video file upload
    """
    if not api_instance:
        raise HTTPException(status_code=503, detail="API not initialized")
    
    try:
        # Save uploaded video temporarily
        video_path = f"temp_{int(time.time())}_{video.filename}"
        with open(video_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # Process video
        cap = cv2.VideoCapture(video_path)
        translations = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert frame to base64
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Create frame request
            timestamp_ms = int(frame_count * 1000 / cap.get(cv2.CAP_PROP_FPS))
            frame_request = VideoFrameRequest(
                video_frame=frame_base64,
                timestamp_ms=timestamp_ms
            )
            
            # Translate frame
            translation = await api_instance.translate_frame(frame_request)
            translations.append(translation)
            
            frame_count += 1
            
            # Limit processing for demo (process every 5th frame)
            if frame_count % 5 != 0:
                continue
        
        cap.release()
        os.remove(video_path)  # Clean up
        
        return {"translations": translations}
        
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")


@app.get("/ssl/status", response_model=ModelStatus)
async def get_status():
    """Get API status and model information"""
    if not api_instance:
        return ModelStatus(
            status="error",
            model_loaded=False,
            supported_classes=0,
            version="1.0.0"
        )
    
    return api_instance.get_status()


@app.get("/ssl/performance")
async def get_performance_stats():
    """Get performance statistics"""
    if not api_instance:
        raise HTTPException(status_code=503, detail="API not initialized")
    
    return api_instance.get_performance_stats()


@app.get("/ssl/classes")
async def get_supported_classes():
    """Get list of supported SSL classes"""
    if not api_instance:
        raise HTTPException(status_code=503, detail="API not initialized")
    
    return {"classes": api_instance.class_names}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    uvicorn.run(
        "inference_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
