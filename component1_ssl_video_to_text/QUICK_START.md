# Quick Start Guide: SSL Video-to-Text with Minimal Data

## TL;DR - Start with 10 Classes

If you want to test the system quickly, start with just **10 SSL classes** instead of the full 400:

### Minimal Dataset Structure
```
data/ssl400/
├── train/           # 10 classes × 10 videos = 100 videos
├── val/             # 10 classes × 2 videos = 20 videos  
├── test/            # 10 classes × 2 videos = 20 videos
└── labels/          # JSON mapping files
```

**Total: Only 140 videos needed for initial testing!**

## Quick Setup (10 Classes)

### 1. Choose 10 Common SSL Signs
Start with these basic signs:
```
1. hello
2. goodbye  
3. please
4. thank_you
5. yes
6. no
7. mother
8. father
9. one
10. two
```

### 2. Video Requirements (Minimal)
- **Format**: MP4 (any resolution above 480p)
- **Duration**: 2-5 seconds per video
- **Content**: Clear SSL sign execution
- **Background**: Any (preferably not cluttered)

### 3. Automated Setup

```bash
# Run automated setup
cd component1_ssl_video_to_text
python data_prep_utility.py --action setup

# Create sample structure for 10 classes
python data_prep_utility.py --action sample --n_classes 10 --videos_per_class 14
```

### 4. Add Your Videos

Place your SSL videos in this structure:
```
data/ssl400/
├── train/
│   ├── hello_video_001.mp4      # 10 videos for hello
│   ├── hello_video_002.mp4
│   ├── ...
│   ├── goodbye_video_001.mp4    # 10 videos for goodbye
│   └── ...
├── val/
│   ├── hello_video_011.mp4      # 2 videos for hello
│   ├── goodbye_video_011.mp4    # 2 videos for goodbye
│   └── ...
└── test/
    ├── hello_video_013.mp4      # 2 videos for hello
    ├── goodbye_video_013.mp4    # 2 videos for goodbye
    └── ...
```

### 5. Validate Your Data
```bash
python data_prep_utility.py --action validate
```

### 6. Train the Model
```bash
# Generate training script
python data_prep_utility.py --action train_script

# Run training
./train_ssl400.sh
```

## Expected Training Results (10 Classes)

With just 10 classes and 140 videos:
- **Training Time**: 1-2 hours (CPU), 20-30 minutes (GPU)
- **Expected Accuracy**: 70-90% (depending on video quality)
- **Model Size**: ~50MB
- **Inference Speed**: 20-50ms per frame

## Scaling Up

Once your 10-class model works well:

### Phase 2: 50 Classes
- Add 40 more classes
- ~700 total videos
- Better accuracy and real-world performance

### Phase 3: 100 Classes  
- Add 50 more classes
- ~1,400 total videos
- Professional-level performance

### Phase 4: Full SSL400
- Complete 400-class dataset
- ~12,000+ total videos
- Production-ready system

## Practical Data Collection Tips

### Option 1: Record Yourself
- Use your phone/webcam
- Record each sign 14 times
- Vary: lighting, clothing, background, speed
- 10 signs × 14 videos × 3 seconds = ~7 minutes of video

### Option 2: Multiple Signers
- Get 2-3 people to sign
- Each person signs each gesture 4-5 times
- More diverse training data

### Option 3: Existing Videos
- Find SSL educational videos online
- Extract individual sign segments
- Ensure proper attribution/permissions

## File Naming Convention

Use consistent naming:
```
{class_name}_video_{number}.mp4

Examples:
hello_video_001.mp4
hello_video_002.mp4
goodbye_video_001.mp4
```

## Training Configuration (10 Classes)

The system will automatically adjust parameters:
```bash
Classes: 10
Batch Size: 4 (small dataset)
Epochs: 50 (faster training)
Learning Rate: 0.001
Sequence Length: 32 frames
```

## Testing Your Trained Model

After training:

1. **Start the API**:
   ```bash
   python src/inference_api.py
   ```

2. **Test with demo**:
   ```bash
   python demo.py --model_path checkpoints/ssl400_training_best.pth --demo_type info
   ```

3. **Real-time webcam test**:
   ```bash
   python demo.py --model_path checkpoints/ssl400_training_best.pth --demo_type webcam
   ```

## Troubleshooting

### "Not enough data" error
- Ensure minimum 3 videos per class per split
- Check file naming matches labels

### Low accuracy
- Add more videos per class
- Improve video quality (lighting, clarity)
- Use multiple signers

### Training too slow
- Reduce batch size to 2-4
- Use smaller sequence length (16 frames)
- Reduce number of epochs

## Next Steps After Success

1. ✅ **10 classes working** → Add 40 more classes (50 total)
2. ✅ **50 classes working** → Add 50 more classes (100 total)  
3. ✅ **100 classes working** → Scale to full SSL400
4. ✅ **SSL400 complete** → Move to Component 2

## Quick Commands Summary

```bash
# Setup (one time)
python data_prep_utility.py --action setup
python data_prep_utility.py --action sample --n_classes 10

# Add your videos to data/ssl400/train/, val/, test/

# Validate and train
python data_prep_utility.py --action validate
python data_prep_utility.py --action train_script
./train_ssl400.sh

# Test
python demo.py --model_path checkpoints/ssl400_training_best.pth --demo_type info
```

**Remember**: Start small, validate the approach, then scale up! 🚀
