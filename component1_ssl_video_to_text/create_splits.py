#!/usr/bin/env python3
"""
SSL400 Dataset Train/Validation Split Creator
Creates train/val splits from the processed SSL400 flat structure
"""

import argparse
import json
import shutil
import random
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_train_val_split(videos_dir: str, train_ratio: float = 0.8, val_ratio: float = 0.2):
    """
    Create train/validation splits from SSL400 flat structure
    
    Args:
        videos_dir: Path to the videos directory with class folders
        train_ratio: Ratio of videos for training (default: 0.8)
        val_ratio: Ratio of videos for validation (default: 0.2)
    """
    
    videos_path = Path(videos_dir)
    parent_dir = videos_path.parent
    
    # Create train/val directories
    train_dir = parent_dir / "train"
    val_dir = parent_dir / "val"
    
    train_dir.mkdir(exist_ok=True)
    val_dir.mkdir(exist_ok=True)
    
    logger.info(f"Creating train/validation splits...")
    logger.info(f"Train ratio: {train_ratio}, Val ratio: {val_ratio}")
    
    # Get all class directories
    class_dirs = [d for d in videos_path.iterdir() if d.is_dir()]
    logger.info(f"Found {len(class_dirs)} classes")
    
    total_videos = 0
    train_videos = 0
    val_videos = 0
    
    # Process each class
    for class_dir in class_dirs:
        class_name = class_dir.name
        
        # Get all video files in this class
        video_files = []
        for ext in ['.mov', '.MOV', '.mp4', '.MP4', '.avi', '.AVI']:
            video_files.extend(list(class_dir.glob(f"*{ext}")))
        
        if not video_files:
            logger.warning(f"No videos found in class: {class_name}")
            continue
        
        # Shuffle videos for random split
        random.shuffle(video_files)
        
        # Calculate split indices
        n_videos = len(video_files)
        n_train = max(1, int(n_videos * train_ratio))  # At least 1 video for training
        n_val = n_videos - n_train
        
        # Create class directories in train/val
        train_class_dir = train_dir / class_name
        val_class_dir = val_dir / class_name
        
        train_class_dir.mkdir(exist_ok=True)
        if n_val > 0:
            val_class_dir.mkdir(exist_ok=True)
        
        # Copy training videos
        for i in range(n_train):
            src_path = video_files[i]
            dst_path = train_class_dir / src_path.name
            shutil.copy2(src_path, dst_path)
            train_videos += 1
        
        # Copy validation videos
        for i in range(n_train, n_videos):
            src_path = video_files[i]
            dst_path = val_class_dir / src_path.name
            shutil.copy2(src_path, dst_path)
            val_videos += 1
        
        total_videos += n_videos
        
        if n_val > 0:
            logger.debug(f"{class_name}: {n_train} train, {n_val} val")
        else:
            logger.debug(f"{class_name}: {n_train} train, {n_val} val (warning: no validation videos)")
    
    # Create summary
    summary = {
        "total_classes": len(class_dirs),
        "total_videos": total_videos,
        "train_videos": train_videos,
        "val_videos": val_videos,
        "train_ratio": train_videos / total_videos if total_videos > 0 else 0,
        "val_ratio": val_videos / total_videos if total_videos > 0 else 0,
        "split_info": {
            "train_path": str(train_dir),
            "val_path": str(val_dir),
            "source_path": str(videos_path)
        }
    }
    
    # Save summary
    summary_file = parent_dir / "split_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("✅ Train/Validation split completed!")
    logger.info(f"📊 Total: {total_videos} videos, {len(class_dirs)} classes")
    logger.info(f"🏋️  Training: {train_videos} videos ({train_videos/total_videos*100:.1f}%)")
    logger.info(f"✅ Validation: {val_videos} videos ({val_videos/total_videos*100:.1f}%)")
    logger.info(f"📁 Train data: {train_dir}")
    logger.info(f"📁 Val data: {val_dir}")
    logger.info(f"📄 Summary: {summary_file}")
    
    return summary

def main():
    parser = argparse.ArgumentParser(description="Create train/validation splits for SSL400 dataset")
    parser.add_argument("--videos-dir", required=True, help="Path to videos directory")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Training ratio (default: 0.8)")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Validation ratio (default: 0.2)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible splits")
    
    args = parser.parse_args()
    
    # Validate ratios
    if abs(args.train_ratio + args.val_ratio - 1.0) > 0.001:
        logger.error(f"Train and validation ratios must sum to 1.0, got {args.train_ratio + args.val_ratio}")
        return
    
    # Set random seed
    random.seed(args.seed)
    
    # Create splits
    summary = create_train_val_split(
        args.videos_dir,
        args.train_ratio,
        args.val_ratio
    )
    
    if summary["val_videos"] == 0:
        logger.warning("⚠️  No validation videos created. Consider adjusting ratios or adding more videos.")
    
    print("\n🚀 Ready for training! Use these paths:")
    print(f"--train_data_path \"{summary['split_info']['train_path']}\"")
    print(f"--val_data_path \"{summary['split_info']['val_path']}\"")

if __name__ == "__main__":
    main()
