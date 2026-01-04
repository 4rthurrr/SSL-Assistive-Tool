# 🎯 CRITICAL FIX: Raw MediaPipe Coordinates (January 4, 2026)

## Problem Identified
The model was trained with **RAW MediaPipe coordinates** but the frontend was applying **hip-centered normalization**, causing a complete mismatch in feature values. This made predictions completely inaccurate ("not even close").

## Root Cause Analysis

### Training Data Format (SSL400 Dataset)
From analyzing the actual CSV files (`Year_001.csv`, `Ayubowan_004.csv`, `Hello_001.csv`):

```
CSV Structure:
- Each row = 1 frame (50 rows per video)
- Each column = 1 landmark (33 pose landmarks)
- Each cell = string array: "[x, y, z, visibility]"
- Total: 33 landmarks × 4 values = 132 features per frame
```

**Sample Values (First Landmark - Nose):**
```
Year_001.csv:     x=0.415, y=0.362, z=-1.342, vis=0.9998
Ayubowan_004.csv: x=0.445, y=0.377, z=-0.484, vis=0.9999
Hello_001.csv:    x=0.470, y=0.357, z=-0.524, vis=0.9999
```

**Key Observations:**
- X: 0.4-0.5 (image-relative coordinates, 0.0-1.0 range)
- Y: 0.3-0.4 (image-relative coordinates, 0.0-1.0 range)
- Z: -0.5 to -1.3 (depth relative to hips, negative values)
- Visibility: 0.99+ (confidence, 0.0-1.0 range)
- **NO NORMALIZATION APPLIED** - these are raw MediaPipe outputs!

### Frontend Issue (BEFORE FIX)
The frontend was applying hip-centered normalization:
```javascript
// ❌ OLD CODE (WRONG)
const hipCenterX = (leftHip.x + rightHip.x) / 2;
const hipCenterY = (leftHip.y + rightHip.y) / 2;
const scale = shoulderHipDist;

const normalizedX = (landmark.x - hipCenterX) / scale;
const normalizedY = (landmark.y - hipCenterY) / scale;
const normalizedZ = (landmark.z - hipCenterZ) / scale;
```

This produced completely different values (e.g., `x=-0.5, y=0.2`) instead of expected (`x=0.45, y=0.36`).

## Solution Implemented

### ✅ Frontend Fix (index_new.html)
**Removed ALL normalization** - now using raw MediaPipe coordinates:
```javascript
// ✅ NEW CODE (CORRECT)
for (let i = 0; i < 33; i++) {
    if (results.poseLandmarks[i]) {
        // Use raw MediaPipe coordinates exactly as training data
        const x = results.poseLandmarks[i].x;
        const y = results.poseLandmarks[i].y;
        const z = results.poseLandmarks[i].z || 0;
        const visibility = results.poseLandmarks[i].visibility !== undefined 
            ? results.poseLandmarks[i].visibility 
            : 1.0;
        
        frameFeatures.push(x, y, z, visibility);
    }
}
```

### Backend Verification
Backend `landmark_utils.py` already passes raw coordinates through without modification:
```python
# Backend just validates and reshapes - no normalization
sequence_array = np.array(frames_list, dtype=np.float32)  # Shape: (50, 132)
sequence_array = np.expand_dims(sequence_array, axis=0)   # Shape: (1, 50, 132)
```

## Results After Fix

### Before Fix (with normalization)
- Predictions: 5-15% confidence
- User feedback: "huge difference in mapping, not even close"
- Example: Random predictions with <10% confidence

### After Fix (raw coordinates)
- Predictions: **50-88% confidence** 🎉
- Observed predictions:
  - `Adjectives/Fat` - **73.18%** confidence
  - `Nouns/Money` - **76.18%** confidence
  - `People/Baby` - **88.60%** confidence
  - `Adverb/Cant` - **58.71%** confidence

## Technical Details

### MediaPipe Holistic Coordinate System
MediaPipe outputs normalized coordinates:
- **X, Y**: Image-relative (0.0 = left/top, 1.0 = right/bottom)
  - Can exceed [0,1] range for landmarks outside frame
- **Z**: Depth relative to hip midpoint (negative = closer to camera)
  - Approximately same scale as X
- **Visibility**: Detection confidence (0.0 = not visible, 1.0 = highly visible)

### SSL400 Dataset Specifications
- **Format**: 3-second videos at 20 FPS
- **Preprocessing**: MediaPipe Holistic → CSV export
- **No additional normalization** applied during training
- **384 classes** (383 in model output)
- **33 pose landmarks** × 4 values = 132 features per frame
- **50 frames** per video (interpolated/subsampled from ~60 frames)

## Files Changed
1. `sign_language_app/frontend/index_new.html`
   - Lines 456-488: Removed normalization, use raw coordinates
   - Lines 493-498: Updated debug messages

## Verification
Run `verify_csv_format.py` to analyze training CSV structure:
```bash
cd sign_language_app/backend
python verify_csv_format.py
```

## Key Takeaway
**Training data preprocessing MUST exactly match inference preprocessing.**  
The model learned patterns from raw MediaPipe coordinates, so inference must provide the same raw coordinates - no normalization, no centering, no scaling.

---
**Status**: ✅ FIXED  
**Date**: January 4, 2026  
**Confidence Improvement**: From <15% to 50-88%  
**Issue**: Landmark preprocessing mismatch  
**Resolution**: Remove normalization, use raw MediaPipe values
