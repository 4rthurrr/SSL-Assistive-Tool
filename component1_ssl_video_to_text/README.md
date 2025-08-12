# SSL Video-to-Text Translation - Component 1

## Overview

This component provides real-time Sinhala Sign Language (SSL) video-to-text translation using a hybrid CNN + LSTM/Transformer architecture. It ingests live or recorded SSL video streams and outputs timestamped Sinhala text transcripts.

## Features

- **Real-time Translation**: Process video frames and output timestamped text
- **Hybrid Architecture**: CNN for spatial features + LSTM/Transformer for temporal modeling
- **MediaPipe Integration**: 21-keypoint hand tracking for enhanced accuracy
- **Transfer Learning**: Pre-trained backbone with fine-tuning support
- **Few-shot Learning**: Support for new SSL classes with minimal data
- **REST API**: RESTful endpoints for integration
- **Performance Optimized**: Sub-100ms latency per frame
- **Comprehensive Testing**: Unit, integration, and real-world tests

## Architecture

### Model Components

1. **CNN Backbone**: ResNet-18/50 for spatial feature extraction
2. **MediaPipe Hands**: 21-keypoint hand tracking (up to 2 hands)
3. **Keypoint Encoder**: MLP for keypoint feature encoding
4. **Sequence Model**: LSTM or Transformer for temporal modeling
5. **Classification Head**: Final prediction layer

### Data Pipeline

1. **Frame Capture**: Video frame extraction
2. **Preprocessing**: Normalization, noise reduction, resize to 224x224
3. **Hand Detection**: MediaPipe keypoint extraction
4. **Augmentation**: Rotation, scaling, temporal jittering (training only)
5. **Sequence Formation**: Fixed-length sequences for temporal modeling

## Quick Start

### Prerequisites

- Python 3.10+
- CUDA (optional, for GPU acceleration)
- SSL400 dataset (or your custom SSL dataset)

### Installation

1. **Clone and setup**:
```bash
cd component1_ssl_video_to_text
pip install -r requirements.txt
```

2. **Download pre-trained model** (when available):
```bash
# Place your trained model at:
# models/ssl_translation_best.pth
```

3. **Configure settings**:
```bash
python src/config.py  # Creates default config
```

### Training

1. **Prepare your data**:
   - Organize videos in train/val/test splits
   - Create corresponding label files
   - Update data paths in config

2. **Train the model**:
```bash
python src/train.py \
    --experiment_name ssl_v1 \
    --train_data_path data/ssl400/train \
    --val_data_path data/ssl400/val \
    --num_classes 400 \
    --batch_size 8 \
    --epochs 100 \
    --sequence_model lstm
```

3. **Monitor training**:
```bash
tensorboard --logdir runs/
```

### Inference

1. **Start the API server**:
```bash
python src/inference_api.py
```

2. **Test with a single frame**:
```python
import requests
import base64

# Encode your image
with open("test_frame.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# Make request
response = requests.post("http://localhost:8000/ssl/translate", json={
    "video_frame": image_base64,
    "timestamp_ms": 1000
})

result = response.json()
print(f"Translation: {result['text']}")
print(f"Confidence: {result['confidence']}")
```

3. **Process a video file**:
```bash
curl -X POST "http://localhost:8000/ssl/translate/video" \
     -F "video=@your_video.mp4"
```

### Docker Deployment

1. **Build and run**:
```bash
docker-compose up --build
```

2. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## API Endpoints

### POST `/ssl/translate`
Translate a single video frame.

**Request:**
```json
{
  "video_frame": "base64_encoded_image",
  "timestamp_ms": 1000
}
```

**Response:**
```json
{
  "text": "hello",
  "confidence": 0.95,
  "timestamp_ms": 1000,
  "processing_time_ms": 45.2
}
```

### POST `/ssl/translate/batch`
Translate multiple frames at once.

### POST `/ssl/translate/video`
Upload and translate an entire video file.

### GET `/ssl/status`
Get API status and model information.

### GET `/ssl/performance`
Get performance statistics.

### GET `/ssl/classes`
Get list of supported SSL classes.

## Performance Metrics

### Accuracy Targets
- **Top-1 Accuracy**: >80%
- **Word Error Rate**: <30%
- **Latency**: <100ms per frame

### Validation Results
Run comprehensive validation:
```bash
python src/validation.py \
    --model_path models/ssl_translation_best.pth \
    --test_data_path data/ssl400/test \
    --run_all
```

## Model Training Details

### Training Pseudocode
```python
for epoch in range(EPOCHS):
    for batch in dataloader:
        # Extract features
        features = model.backbone(batch.frames)
        keypoint_features = model.keypoint_encoder(batch.keypoints)
        combined = torch.cat([features, keypoint_features], dim=-1)
        
        # Sequence modeling
        outputs = model.sequence_head(combined)
        
        # Compute loss and optimize
        loss = criterion(outputs, batch.labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
```

### Hyperparameters
- **Learning Rate**: 1e-3
- **Batch Size**: 8
- **Sequence Length**: 32 frames
- **Optimizer**: Adam with weight decay 1e-4
- **Scheduler**: Cosine annealing

### Transfer Learning
1. Load pre-trained ResNet backbone
2. Freeze backbone layers (optional)
3. Fine-tune on SSL400 dataset
4. Gradual unfreezing for better performance

### Few-Shot Learning
Support for N-shot learning:
1. Create prototype representations
2. Compute similarities with query samples
3. Meta-learning optimization

## Testing

### Run Tests
```bash
# Run all tests
python tests/test_ssl_translation.py

# Run specific test categories
python -m pytest tests/ -v
```

### Unit Tests
- Model architecture validation
- Data preprocessing verification
- API endpoint functionality

### Integration Tests
- End-to-end video processing
- Real-time performance validation
- Known gesture recognition accuracy

## Dataset Requirements

### SSL400 Dataset
- **Structure**: Organized video files with corresponding labels
- **Format**: MP4, AVI, or other common video formats
- **Labels**: Text file or JSON with class mappings

### Additional Data Request Template
If you need additional labeled SSL video clips:

> **Request**: Please provide additional labeled video clips for SSL classes: 
> - [Class 1]: Description and examples needed
> - [Class 2]: Description and examples needed
> - ...
> 
> **Format**: MP4 videos, 2-10 seconds each
> **Quality**: 720p+ resolution, clear hand visibility
> **Annotation**: Frame-level or sequence-level labels

## Configuration

### Model Configuration
```json
{
  "model": {
    "num_classes": 400,
    "sequence_model": "lstm",
    "sequence_length": 32,
    "pretrained_backbone": true
  }
}
```

### Training Configuration
```json
{
  "training": {
    "batch_size": 8,
    "learning_rate": 0.001,
    "epochs": 100,
    "optimizer": "adam"
  }
}
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**:
   - Reduce batch size
   - Use gradient checkpointing
   - Enable mixed precision

2. **Low Accuracy**:
   - Check data quality and labeling
   - Increase training epochs
   - Use transfer learning
   - Adjust data augmentation

3. **High Latency**:
   - Enable GPU acceleration
   - Use model quantization
   - Optimize batch processing

4. **MediaPipe Issues**:
   - Ensure proper lighting in videos
   - Check hand visibility
   - Adjust confidence thresholds

### Performance Optimization

1. **Model Optimization**:
   - TensorRT optimization (NVIDIA GPUs)
   - ONNX conversion for cross-platform
   - Model pruning and quantization

2. **Infrastructure**:
   - GPU acceleration
   - Batch processing
   - Caching frequent requests

## Development

### Project Structure
```
component1_ssl_video_to_text/
├── src/
│   ├── config.py          # Configuration management
│   ├── data_loader.py     # Data loading and preprocessing
│   ├── model.py           # Model architecture
│   ├── train.py           # Training script
│   ├── inference_api.py   # REST API server
│   └── validation.py      # Performance validation
├── tests/
│   └── test_ssl_translation.py  # Test suite
├── configs/
│   └── default_config.json     # Default configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new functionality
3. Update documentation
4. Validate performance metrics

### Next Steps

Once Component 1 meets accuracy and latency targets, proceed to:
- **Component 2**: Text-to-SSL Animation
- **Component 3**: Real-time Video Processing
- **Component 4**: Complete System Integration

## License

This project is part of the SSL-Assistive-Tool for deaf/mute children's education.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review test outputs and validation results
3. Examine log files in the `logs/` directory
4. Monitor performance metrics via API endpoints
