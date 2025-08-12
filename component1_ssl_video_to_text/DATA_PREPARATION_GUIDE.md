# SSL400 Dataset Preparation Guide

## Overview

This guide explains exactly what data you need for training the SSL Video-to-Text translation model and how to organize it properly.

## Dataset Requirements

### SSL400 Dataset Structure

The system expects **400 different Sinhala Sign Language classes** with the following organization:

```
component1_ssl_video_to_text/
└── data/
    └── ssl400/
        ├── train/           # Training videos (70% of data)
        ├── val/             # Validation videos (15% of data)
        ├── test/            # Test videos (15% of data)
        ├── labels/          # Label files
        │   ├── train_labels.json
        │   ├── val_labels.json
        │   └── test_labels.json
        └── class_names.txt  # List of all 400 SSL classes
```

## Video Requirements

### Technical Specifications

| Attribute | Requirement | Recommended |
|-----------|------------|-------------|
| **Format** | MP4, AVI, MOV | MP4 |
| **Resolution** | Minimum 480p | 720p or higher |
| **Duration** | 2-10 seconds | 3-5 seconds |
| **Frame Rate** | 15-60 FPS | 30 FPS |
| **Quality** | Clear hand visibility | HD quality |
| **Lighting** | Good lighting conditions | Natural lighting |
| **Background** | Any (preferably contrasting) | Plain background |

### Content Requirements

- **Hand Visibility**: Both hands should be clearly visible
- **Sign Execution**: Complete sign gesture from start to finish
- **Signer Position**: Front-facing, hands within frame
- **Sign Quality**: Proper SSL execution by native signers
- **Consistency**: Same sign should be performed similarly across videos

## Data Volume Requirements

### Per Class Distribution

| Split | Videos per Class | Total Videos | Percentage |
|-------|------------------|--------------|------------|
| **Training** | 20-50 videos | 8,000-20,000 | 70% |
| **Validation** | 5-10 videos | 2,000-4,000 | 15% |
| **Test** | 5-10 videos | 2,000-4,000 | 15% |

### Minimum Requirements (for basic training)

```
Total Classes: 400 SSL signs
Minimum per class: 20 videos
Recommended per class: 30-50 videos

MINIMUM DATASET:
├── Training: 400 classes × 15 videos = 6,000 videos
├── Validation: 400 classes × 3 videos = 1,200 videos
└── Test: 400 classes × 2 videos = 800 videos
TOTAL: 8,000 videos minimum
```

### Recommended Dataset (for optimal performance)

```
RECOMMENDED DATASET:
├── Training: 400 classes × 35 videos = 14,000 videos
├── Validation: 400 classes × 7 videos = 2,800 videos
└── Test: 400 classes × 8 videos = 3,200 videos
TOTAL: 20,000 videos recommended
```

## SSL400 Classes

The system is configured for these 400 Sinhala Sign Language classes:

### Core Categories (200 classes)

1. **Basic Communication (20 classes)**
   - hello, goodbye, please, thank_you, sorry, yes, no
   - good_morning, good_evening, good_night, how_are_you, fine
   - excuse_me, welcome, congratulations, happy_birthday, etc.

2. **Family & People (25 classes)**
   - mother, father, sister, brother, grandmother, grandfather
   - child, baby, friend, teacher, student, doctor, nurse
   - man, woman, boy, girl, person, etc.

3. **Numbers (30 classes)**
   - 0-20: zero through twenty
   - 30, 40, 50, 60, 70, 80, 90, 100
   - first, second, third, etc.

4. **Colors (15 classes)**
   - red, blue, green, yellow, black, white, brown
   - pink, purple, orange, gray, etc.

5. **Body Parts (20 classes)**
   - head, face, eye, nose, mouth, ear, hand, finger
   - leg, foot, arm, shoulder, etc.

6. **Food & Drink (25 classes)**
   - water, milk, rice, bread, fruit, apple, banana
   - tea, coffee, eat, drink, hungry, thirsty, etc.

7. **Common Verbs (30 classes)**
   - go, come, sit, stand, walk, run, sleep, wake_up
   - work, play, read, write, learn, teach, help, etc.

8. **Emotions (15 classes)**
   - happy, sad, angry, afraid, love, like, hate
   - excited, tired, sick, etc.

9. **Time & Days (20 classes)**
   - today, yesterday, tomorrow, morning, afternoon
   - Monday through Sunday, etc.

### Extended Categories (200 additional classes)

10. **Places & Locations (25 classes)**
11. **Weather & Nature (20 classes)**
12. **Transportation (15 classes)**
13. **Animals (25 classes)**
14. **School & Education (20 classes)**
15. **Adjectives (30 classes)**
16. **Question Words (10 classes)**
17. **Pronouns & Demonstratives (15 classes)**
18. **Actions & Activities (40 classes)**

*Full class list available in `src/config.py`*

## File Organization

### Video Naming Convention

Use this naming convention for video files:

```
{class_name}_{signer_id}_{video_number}.mp4

Examples:
hello_signer001_001.mp4
hello_signer001_002.mp4
hello_signer002_001.mp4
goodbye_signer001_001.mp4
```

### Label File Format

Create JSON files with video-to-label mappings:

**train_labels.json**
```json
{
  "hello_signer001_001.mp4": "hello",
  "hello_signer001_002.mp4": "hello",
  "goodbye_signer001_001.mp4": "goodbye",
  "mother_signer002_001.mp4": "mother",
  ...
}
```

**class_names.txt**
```
hello
goodbye
please
thank_you
sorry
...
```

## Data Collection Guidelines

### Signer Requirements

- **Multiple Signers**: Use 5-20 different signers per class
- **Age Range**: Include various age groups
- **Signing Style**: Natural, fluent SSL execution
- **Consistency**: Same sign meaning across signers

### Recording Setup

1. **Camera Position**: Front-facing, chest-up framing
2. **Lighting**: Even, natural lighting preferred
3. **Background**: Plain or contrasting background
4. **Stability**: Stable camera (tripod recommended)
5. **Quality**: HD recording (720p minimum)

### Sign Execution

- **Complete Gesture**: Record full sign from neutral position to completion
- **Natural Speed**: Normal signing speed (not too slow/fast)
- **Clear Articulation**: Proper hand shapes and movements
- **Consistent Space**: Use consistent signing space

## Setup Instructions

### 1. Create Directory Structure

```bash
# Navigate to project directory
cd component1_ssl_video_to_text

# Create data directories
mkdir -p data/ssl400/{train,val,test,labels}

# Windows PowerShell
New-Item -ItemType Directory -Path "data\ssl400\train" -Force
New-Item -ItemType Directory -Path "data\ssl400\val" -Force
New-Item -ItemType Directory -Path "data\ssl400\test" -Force
New-Item -ItemType Directory -Path "data\ssl400\labels" -Force
```

### 2. Organize Your Videos

Place videos in appropriate directories:

```
data/ssl400/
├── train/
│   ├── hello_signer001_001.mp4
│   ├── hello_signer001_002.mp4
│   ├── goodbye_signer001_001.mp4
│   └── ...
├── val/
│   ├── hello_signer003_001.mp4
│   ├── goodbye_signer003_001.mp4
│   └── ...
└── test/
    ├── hello_signer004_001.mp4
    ├── goodbye_signer004_001.mp4
    └── ...
```

### 3. Create Label Files

Generate label mapping files:

```python
# Create train_labels.json
import json
import os

def create_labels_file(video_dir, output_file):
    labels = {}
    for filename in os.listdir(video_dir):
        if filename.endswith(('.mp4', '.avi', '.mov')):
            # Extract class name from filename
            class_name = filename.split('_')[0]
            labels[filename] = class_name
    
    with open(output_file, 'w') as f:
        json.dump(labels, f, indent=2)

# Generate all label files
create_labels_file('data/ssl400/train', 'data/ssl400/labels/train_labels.json')
create_labels_file('data/ssl400/val', 'data/ssl400/labels/val_labels.json')
create_labels_file('data/ssl400/test', 'data/ssl400/labels/test_labels.json')
```

## Data Validation

### Check Data Quality

Use this script to validate your dataset:

```python
import json
import os
import cv2

def validate_dataset(data_dir, labels_file):
    # Load labels
    with open(labels_file, 'r') as f:
        labels = json.load(f)
    
    issues = []
    class_counts = {}
    
    for video_file, class_name in labels.items():
        video_path = os.path.join(data_dir, video_file)
        
        # Check if video exists
        if not os.path.exists(video_path):
            issues.append(f"Missing video: {video_file}")
            continue
        
        # Check video properties
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            issues.append(f"Cannot open video: {video_file}")
            continue
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Validate video properties
        if duration < 1 or duration > 15:
            issues.append(f"Duration issue ({duration:.1f}s): {video_file}")
        if width < 480 or height < 360:
            issues.append(f"Resolution too low ({width}x{height}): {video_file}")
        
        # Count classes
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        cap.release()
    
    return issues, class_counts

# Validate all splits
for split in ['train', 'val', 'test']:
    issues, counts = validate_dataset(
        f'data/ssl400/{split}',
        f'data/ssl400/labels/{split}_labels.json'
    )
    
    print(f"\n{split.upper()} SET VALIDATION:")
    print(f"Issues found: {len(issues)}")
    print(f"Classes: {len(counts)}")
    print(f"Total videos: {sum(counts.values())}")
    
    if issues:
        print("Issues:")
        for issue in issues[:10]:  # Show first 10 issues
            print(f"  - {issue}")
```

## Training Configuration

Update the training script to use your dataset:

```python
# Modify train.py arguments
python src/train.py \
    --experiment_name ssl400_training \
    --train_data_path data/ssl400/train \
    --val_data_path data/ssl400/val \
    --num_classes 400 \
    --batch_size 8 \
    --sequence_length 32 \
    --epochs 100
```

## Alternative: Start with Smaller Dataset

If you don't have the full SSL400 dataset yet, you can start with a smaller subset:

### SSL50 (50 classes for initial testing)

```
Minimum viable dataset:
├── 50 most common SSL signs
├── 10-15 videos per class per split
├── Total: ~1,500 videos
└── Good for proof-of-concept
```

### SSL100 (100 classes for development)

```
Development dataset:
├── 100 essential SSL signs
├── 15-20 videos per class per split
├── Total: ~3,000 videos
└── Good for model development
```

## Data Augmentation

The system includes built-in data augmentation:

- **Spatial**: Rotation (±15°), scaling (±10%)
- **Temporal**: Frame jittering, sequence variations
- **Visual**: Brightness/contrast, noise injection
- **Geometric**: Slight perspective changes

This helps increase effective dataset size by 3-5x during training.

## Next Steps

1. **Collect/Organize Videos**: Gather SSL videos according to specifications
2. **Create Labels**: Generate JSON mapping files
3. **Validate Dataset**: Run validation scripts
4. **Start Training**: Use provided training scripts
5. **Monitor Progress**: Check TensorBoard for training metrics

## Support

If you need help with:
- **Data organization**: Follow the structure exactly as shown
- **Label creation**: Use the provided Python scripts
- **Video requirements**: Ensure all technical specs are met
- **Training issues**: Check logs and validation results

The system is designed to be flexible - you can start with fewer classes and expand gradually as you collect more data.
