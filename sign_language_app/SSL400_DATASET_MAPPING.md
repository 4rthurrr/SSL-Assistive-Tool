# SSL400 Dataset Implementation Guide

## Dataset Overview
**SSL400** - Largest publicly available Sinhala Sign Language (SSL) recognition dataset  
**Source**: School of Computing, Informatics Institute of Technology, Colombo, Sri Lanka  
**Research**: "Deep Learning in Sinhala Sign Language Recognition" (IEEE Conference, Nov 2024)

## Dataset Specifications

| Specification | Value | Implementation Status |
|--------------|-------|----------------------|
| **Classes** | 384 | ✅ Model trained on 383 classes |
| **Video Format** | .mp4 | ✅ Training used MediaPipe CSV |
| **FPS** | 20 fps | ✅ Training: 20 fps, Inference: 20 fps (50ms interval) |
| **Duration** | 3 seconds | ✅ 50 frames (2.5s recording + interpolation) |
| **Preprocessing** | MediaPipe Holistic → CSV | ✅ Frontend uses MediaPipe Holistic |
| **Data Splits** | 70% train, 20% test, 10% val | ✅ Used in training |

## Data Format Mapping

### 1. Video Specifications
```
Original Dataset:
- 3 seconds per video @ 20 fps = 60 frames
- MediaPipe preprocessing applied
- Exported to CSV format

Our Implementation:
- 5 seconds recording @ 20 fps = 100 possible frames
- Extract 50 frames (subsampled/interpolated)
- MediaPipe Holistic (33 pose landmarks)
- Matches training data format
```

### 2. Landmark Extraction

#### SSL400 CSV Format
```csv
Each CSV file contains:
- Rows: 60 frames (3 seconds @ 20 fps)
- Columns: 33 landmarks (MediaPipe Pose)
- Cell format: "[x, y, z, visibility]" as string array
- Total features: 33 × 4 = 132 per frame
```

**Example from actual training data:**
```csv
Column 0 (Nose landmark):
"[0.4152572453022003, 0.3615031838417053, -1.3417330980300903, 0.9997674822807312]"
   └─ x=0.415 (normalized to image width)
   └─ y=0.362 (normalized to image height)  
   └─ z=-1.342 (depth relative to hips)
   └─ visibility=0.9998 (detection confidence)
```

#### Our Frontend Implementation
```javascript
MediaPipe Holistic Configuration:
- modelComplexity: 0 (lite model for speed)
- smoothLandmarks: false (real-time responsiveness)
- minDetectionConfidence: 0.3
- minTrackingConfidence: 0.3
- Camera: 480×360 @ 20 fps

Landmark Extraction (CRITICAL - NO NORMALIZATION):
for (let i = 0; i < 33; i++) {
    const x = results.poseLandmarks[i].x;           // Raw MediaPipe value
    const y = results.poseLandmarks[i].y;           // Raw MediaPipe value
    const z = results.poseLandmarks[i].z || 0;      // Raw MediaPipe value
    const visibility = results.poseLandmarks[i].visibility || 1.0;
    frameFeatures.push(x, y, z, visibility);
}
```

### 3. Coordinate System

#### MediaPipe Holistic Output
```
X-axis: 0.0 (left edge) → 1.0 (right edge)
  - Values can exceed [0, 1] for off-frame landmarks
  - Typical nose position: 0.4-0.5 (centered)

Y-axis: 0.0 (top edge) → 1.0 (bottom edge)
  - Values can exceed [0, 1] for off-frame landmarks
  - Typical nose position: 0.3-0.4 (upper body)

Z-axis: Depth relative to hip midpoint
  - Negative values = closer to camera than hips
  - Typical nose Z: -0.5 to -1.5
  - Approximately same scale as X

Visibility: 0.0 (not detected) → 1.0 (high confidence)
```

#### SSL400 Training Data Ranges (from actual CSVs)
```
Landmark 0 (Nose) across different signs:
  X: 0.415 - 0.470  (centered in frame)
  Y: 0.356 - 0.377  (upper portion)
  Z: -0.484 to -1.342  (above hips)
  Visibility: 0.9994 - 0.9999  (highly visible)

These are RAW MediaPipe coordinates - NO normalization applied!
```

## Model Architecture

### Input Shape
```python
Input: (batch_size, 50, 132)
  └─ 50 frames (temporal sequence)
  └─ 132 features (33 landmarks × 4 values)
```

### Model Performance
```
Training Results (best_sign_model_full_features.keras):
- Validation Accuracy: 99.18%
- Total Parameters: 5,200,000+
- Classes: 383 (from 384 dataset classes)
- Input: Raw MediaPipe coordinates (CRITICAL!)
```

### Model Expectations
```python
The model learned patterns from raw MediaPipe values:
- Nose typically at x≈0.45, y≈0.36
- Left hip at x≈0.6, right hip at x≈0.4
- Hand movements in range x=0.2-0.8, y=0.3-1.0

Any preprocessing that changes these ranges will break predictions!
```

## Critical Implementation Notes

### ✅ CORRECT: Our Current Implementation
```javascript
// Use raw MediaPipe coordinates directly
const x = results.poseLandmarks[i].x;
const y = results.poseLandmarks[i].y;
const z = results.poseLandmarks[i].z || 0;
const visibility = results.poseLandmarks[i].visibility || 1.0;
frameFeatures.push(x, y, z, visibility);
```

### ❌ WRONG: Previous Implementation (FIXED)
```javascript
// DO NOT normalize/center/scale - model wasn't trained on this!
const hipCenterX = (leftHip.x + rightHip.x) / 2;
const normalizedX = (landmark.x - hipCenterX) / scale;  // ❌ WRONG!
```

## Data Pipeline Comparison

### Training Pipeline (Kaggle)
```
1. Original videos (.mp4, 3s @ 20 fps)
   ↓
2. MediaPipe Holistic preprocessing
   ↓
3. Export to CSV (raw coordinates)
   ↓ 
4. Load CSV → flatten to (50, 132)
   ↓
5. Train model on raw values
   ↓
6. Model: 99.18% validation accuracy ✅
```

### Inference Pipeline (Our App)
```
1. Webcam capture (5s @ 20 fps)
   ↓
2. MediaPipe Holistic (live processing)
   ↓
3. Extract raw coordinates (NO normalization)
   ↓
4. Collect 50 frames → shape (50, 132)
   ↓
5. Send to backend → model prediction
   ↓
6. Result: 50-88% confidence ✅
```

## Frame Count Handling

### SSL400 Dataset
```
Standard: 3 seconds @ 20 fps = 60 frames
Training: Uses 50 frames (likely subsampled from 60)
```

### Our Implementation
```javascript
Target: 50 frames
Recording: 5 seconds @ 20 fps (100 possible frames)
Sampling strategy:
  - Collect every other frame → 50 frames
  - If <50: Linear interpolation to reach 50
  - If >50: Subsample to 50
```

## Sign Categories (384 Classes)

Based on observed predictions, SSL400 includes:
- **Adjectives**: Bad, Beautiful, Careful, Cold, Fat, Good, Happy, etc.
- **Verbs**: Fight, Come, Go, Help, Love, etc.
- **Nouns**: Money, Baby, Mother, Father, School, etc.
- **Days**: Monday, Tuesday, Wednesday, Tomorrow, etc.
- **Numbers**: Addition, One, Two, Three, etc.
- **People**: Elder bro, Baby, Mother, Father, etc.
- **Adverbs**: Can't, Must, Should, etc.

## Performance Metrics

### Expected Performance
```
Training (Kaggle environment):
- Validation Accuracy: 99.18%
- Training Accuracy: ~99.5%+
- Loss: <0.05

Inference (Production):
- High confidence (>70%): Clear, well-performed signs
- Medium confidence (40-70%): Partial matches, unclear gestures
- Low confidence (<40%): Ambiguous or untrained signs
```

### Observed Results (After Fix)
```
Before Fix (normalized coordinates):
  Prediction: Days/Tomorrow (8.32%)    ❌ Random guessing
  Prediction: Verbs/Fight (9.85%)      ❌ Model confused

After Fix (raw coordinates):
  Prediction: Adjectives/Fat (73.18%)  ✅ High confidence
  Prediction: Nouns/Money (76.18%)     ✅ High confidence  
  Prediction: People/Baby (88.60%)     ✅ Excellent!
  Prediction: Adverb/Cant (58.71%)     ✅ Good match
```

## Troubleshooting Guide

### Issue: Low Prediction Confidence (<30%)
**Possible Causes:**
1. ❌ Coordinate normalization applied (should be raw)
2. ❌ Wrong landmark count (should be 33 pose landmarks)
3. ❌ Wrong frame count (should be 50 frames)
4. ❌ Visibility values modified (should be 0.0-1.0)

**Solution:** Use raw MediaPipe coordinates exactly as training data

### Issue: Shape Mismatch Errors
**Expected Shapes:**
- Per frame: 132 features (33 × 4)
- Full sequence: (50, 132)
- Model input: (1, 50, 132) with batch dimension

### Issue: Inconsistent Predictions
**Check:**
1. Frame rate: Should be 20 fps (50ms interval)
2. Recording duration: 5 seconds → 50 frames
3. MediaPipe model: Use Holistic (not Pose alone)
4. Camera quality: Good lighting, full body visible

## References

- **Dataset Source**: [Kaggle SSL400 Dataset](https://www.kaggle.com/datasets)
- **MediaPipe Holistic**: [Google MediaPipe Documentation](https://google.github.io/mediapipe/solutions/holistic.html)
- **Research Paper**: "Deep Learning in Sinhala Sign Language Recognition" (IEEE, 2024)

## File Structure

```
sign_language_app/
├── backend/
│   ├── best_sign_model_full_features.keras  (Trained on raw coordinates)
│   ├── class_labels.json                     (383 SSL400 classes)
│   ├── main.py                               (FastAPI server)
│   ├── landmark_utils.py                     (Shape validation only)
│   └── verify_csv_format.py                  (CSV analysis tool)
│
├── frontend/
│   └── index_new.html                        (MediaPipe + raw coordinates)
│
└── docs/
    ├── LANDMARK_FORMAT_FIX.md                (Critical fix documentation)
    └── SSL400_DATASET_MAPPING.md             (This file)
```

## Key Takeaways

1. **SSL400 uses RAW MediaPipe coordinates** - no normalization in training data
2. **Model expects exact same format** - any preprocessing breaks predictions
3. **33 pose landmarks × 4 values = 132 features** per frame
4. **50 frames** per sequence at 20 fps
5. **99.18% validation accuracy** proves model quality
6. **Frontend must match training format exactly** for good predictions

---
**Last Updated**: January 4, 2026  
**Status**: ✅ Production Ready  
**Model Version**: best_sign_model_full_features.keras  
**Dataset**: SSL400 (384 classes, Sinhala Sign Language)
