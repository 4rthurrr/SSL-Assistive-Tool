#!/usr/bin/env python3
"""
SSL400 Dataset Preparation Utility
Helps organize, validate, and prepare SSL video data for training
"""

import os
import json
import cv2
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict, Counter
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SSL400DataPrep:
    """SSL400 Dataset preparation utility"""
    
    def __init__(self, data_root: str = "data/ssl400"):
        self.data_root = Path(data_root)
        self.splits = ['train', 'val', 'test']
        
        # Expected SSL400 classes (from config.py)
        self.ssl400_classes = [
            # Basic greetings
            "hello", "goodbye", "please", "thank_you", "sorry", "yes", "no",
            "good_morning", "good_evening", "good_night", "how_are_you", "fine",
            
            # Family and people
            "mother", "father", "sister", "brother", "grandmother", "grandfather",
            "child", "baby", "friend", "teacher", "student", "doctor", "nurse",
            
            # Numbers (0-20)
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
            "seventeen", "eighteen", "nineteen", "twenty",
            
            # Colors
            "red", "blue", "green", "yellow", "black", "white", "brown", "pink", "purple", "orange",
            
            # Body parts
            "head", "face", "eye", "nose", "mouth", "ear", "hand", "finger", "leg", "foot",
            
            # Food and drink
            "water", "milk", "rice", "bread", "fruit", "apple", "banana", "tea", "coffee",
            "eat", "drink", "hungry", "thirsty",
            
            # Common verbs
            "go", "come", "sit", "stand", "walk", "run", "sleep", "wake_up", "work", "play",
            "read", "write", "learn", "teach", "help", "give", "take", "buy", "sell",
            
            # Emotions and feelings
            "happy", "sad", "angry", "afraid", "love", "like", "hate", "excited", "tired", "sick",
            
            # Time related
            "today", "yesterday", "tomorrow", "morning", "afternoon", "evening", "night",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
        ]
        
        # Add more classes to reach 400
        additional_classes = [
            # Places
            "home", "school", "hospital", "shop", "temple", "church", "office", "library",
            "park", "beach", "mountain", "city", "village",
            
            # Weather
            "sun", "rain", "cloud", "wind", "hot", "cold", "warm", "cool",
            
            # Transportation
            "car", "bus", "train", "bicycle", "boat", "airplane",
            
            # Animals
            "dog", "cat", "bird", "fish", "cow", "elephant", "lion", "tiger", "monkey",
            
            # School subjects
            "mathematics", "science", "history", "geography", "language", "art", "music", "sport",
            
            # Common adjectives
            "big", "small", "tall", "short", "fat", "thin", "old", "young", "new", "beautiful",
            "ugly", "clean", "dirty", "expensive", "cheap", "easy", "difficult",
            
            # Question words
            "what", "where", "when", "who", "why", "how", "which",
            
            # Pronouns
            "i", "you", "he", "she", "we", "they", "this", "that", "here", "there"
        ]
        
        self.ssl400_classes.extend(additional_classes)
        
        # Pad to exactly 400 classes if needed
        while len(self.ssl400_classes) < 400:
            self.ssl400_classes.append(f"ssl_gesture_{len(self.ssl400_classes):03d}")
        
        self.ssl400_classes = self.ssl400_classes[:400]  # Ensure exactly 400
    
    def setup_directories(self):
        """Create necessary directory structure"""
        logger.info("Setting up directory structure...")
        
        # Create main directories
        for split in self.splits:
            (self.data_root / split).mkdir(parents=True, exist_ok=True)
        
        (self.data_root / 'labels').mkdir(exist_ok=True)
        
        # Create class names file
        class_names_file = self.data_root / 'class_names.txt'
        with open(class_names_file, 'w') as f:
            for class_name in self.ssl400_classes:
                f.write(f"{class_name}\n")
        
        logger.info(f"Created directories and class names file with {len(self.ssl400_classes)} classes")
    
    def organize_videos_from_folder(self, source_folder: str, train_ratio: float = 0.7, 
                                   val_ratio: float = 0.15, test_ratio: float = 0.15):
        """Organize videos from a source folder into train/val/test splits"""
        source_path = Path(source_folder)
        
        if not source_path.exists():
            logger.error(f"Source folder not found: {source_folder}")
            return
        
        logger.info(f"Organizing videos from {source_folder}...")
        
        # Find all video files
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(source_path.glob(f"*{ext}"))
            video_files.extend(source_path.glob(f"**/*{ext}"))
        
        logger.info(f"Found {len(video_files)} video files")
        
        # Group by class (extract from filename)
        class_videos = defaultdict(list)
        
        for video_file in video_files:
            # Try to extract class name from filename
            filename = video_file.stem.lower()
            
            # Look for matching class names
            matched_class = None
            for class_name in self.ssl400_classes:
                if class_name.lower() in filename:
                    matched_class = class_name
                    break
            
            if matched_class:
                class_videos[matched_class].append(video_file)
            else:
                logger.warning(f"Could not match class for: {video_file.name}")
        
        logger.info(f"Organized into {len(class_videos)} classes")
        
        # Split each class into train/val/test
        all_splits = {'train': {}, 'val': {}, 'test': {}}
        
        for class_name, videos in class_videos.items():
            if len(videos) < 3:
                logger.warning(f"Class {class_name} has only {len(videos)} videos (minimum 3 needed)")
                continue
            
            # Shuffle videos
            import random
            random.shuffle(videos)
            
            # Calculate splits
            n_videos = len(videos)
            n_train = int(n_videos * train_ratio)
            n_val = int(n_videos * val_ratio)
            n_test = n_videos - n_train - n_val
            
            # Assign videos to splits
            train_videos = videos[:n_train]
            val_videos = videos[n_train:n_train + n_val]
            test_videos = videos[n_train + n_val:]
            
            # Copy videos to appropriate directories
            for split, videos_list in [('train', train_videos), ('val', val_videos), ('test', test_videos)]:
                for i, video_file in enumerate(videos_list):
                    # Create new filename
                    new_filename = f"{class_name}_video_{i+1:03d}{video_file.suffix}"
                    dest_path = self.data_root / split / new_filename
                    
                    # Copy file
                    shutil.copy2(video_file, dest_path)
                    all_splits[split][new_filename] = class_name
        
        # Create label files
        for split, labels in all_splits.items():
            labels_file = self.data_root / 'labels' / f'{split}_labels.json'
            with open(labels_file, 'w') as f:
                json.dump(labels, f, indent=2)
        
        logger.info("Video organization completed")
        self.print_dataset_summary()
    
    def validate_dataset(self) -> Dict:
        """Validate the dataset and return summary"""
        logger.info("Validating dataset...")
        
        validation_results = {
            'splits': {},
            'issues': [],
            'summary': {}
        }
        
        for split in self.splits:
            split_dir = self.data_root / split
            labels_file = self.data_root / 'labels' / f'{split}_labels.json'
            
            if not labels_file.exists():
                validation_results['issues'].append(f"Missing labels file: {labels_file}")
                continue
            
            # Load labels
            with open(labels_file, 'r') as f:
                labels = json.load(f)
            
            split_results = {
                'total_videos': 0,
                'classes': set(),
                'class_counts': Counter(),
                'video_issues': [],
                'duration_stats': [],
                'resolution_stats': []
            }
            
            for video_file, class_name in labels.items():
                video_path = split_dir / video_file
                
                if not video_path.exists():
                    split_results['video_issues'].append(f"Missing video: {video_file}")
                    continue
                
                # Validate video
                cap = cv2.VideoCapture(str(video_path))
                if not cap.isOpened():
                    split_results['video_issues'].append(f"Cannot open: {video_file}")
                    continue
                
                # Get video properties
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                duration = frame_count / fps if fps > 0 else 0
                
                # Check requirements
                if duration < 1 or duration > 15:
                    split_results['video_issues'].append(
                        f"Duration issue ({duration:.1f}s): {video_file}"
                    )
                
                if width < 480 or height < 360:
                    split_results['video_issues'].append(
                        f"Low resolution ({width}x{height}): {video_file}"
                    )
                
                # Collect stats
                split_results['duration_stats'].append(duration)
                split_results['resolution_stats'].append((width, height))
                split_results['class_counts'][class_name] += 1
                split_results['classes'].add(class_name)
                split_results['total_videos'] += 1
                
                cap.release()
            
            validation_results['splits'][split] = split_results
        
        # Generate summary
        total_videos = sum(s['total_videos'] for s in validation_results['splits'].values())
        all_classes = set()
        for split_data in validation_results['splits'].values():
            all_classes.update(split_data['classes'])
        
        validation_results['summary'] = {
            'total_videos': total_videos,
            'total_classes': len(all_classes),
            'missing_classes': set(self.ssl400_classes) - all_classes,
            'total_issues': sum(len(s['video_issues']) for s in validation_results['splits'].values())
        }
        
        return validation_results
    
    def print_dataset_summary(self):
        """Print dataset summary"""
        validation_results = self.validate_dataset()
        
        print("\n" + "="*60)
        print("SSL400 DATASET SUMMARY")
        print("="*60)
        
        summary = validation_results['summary']
        print(f"Total Videos: {summary['total_videos']}")
        print(f"Total Classes: {summary['total_classes']}")
        print(f"Missing Classes: {len(summary['missing_classes'])}")
        print(f"Total Issues: {summary['total_issues']}")
        
        print(f"\nSPLIT BREAKDOWN:")
        for split, data in validation_results['splits'].items():
            print(f"  {split.upper():5}: {data['total_videos']:5} videos, {len(data['classes']):3} classes")
            
            if data['duration_stats']:
                avg_duration = sum(data['duration_stats']) / len(data['duration_stats'])
                print(f"         Avg duration: {avg_duration:.1f}s")
            
            if data['video_issues']:
                print(f"         Issues: {len(data['video_issues'])}")
        
        # Show classes with low video counts
        print(f"\nCLASSES WITH FEW VIDEOS (<5):")
        low_count_classes = []
        for split, data in validation_results['splits'].items():
            for class_name, count in data['class_counts'].items():
                if count < 5:
                    low_count_classes.append(f"{class_name} ({split}): {count}")
        
        if low_count_classes:
            for item in low_count_classes[:10]:  # Show first 10
                print(f"  {item}")
            if len(low_count_classes) > 10:
                print(f"  ... and {len(low_count_classes) - 10} more")
        else:
            print("  None - Good!")
        
        print("\n" + "="*60)
    
    def create_sample_dataset(self, n_classes: int = 50, videos_per_class: int = 10):
        """Create a sample dataset for testing"""
        logger.info(f"Creating sample dataset with {n_classes} classes...")
        
        # Select first n_classes
        sample_classes = self.ssl400_classes[:n_classes]
        
        # Create dummy label files
        for split in self.splits:
            labels = {}
            videos_in_split = {
                'train': int(videos_per_class * 0.7),
                'val': int(videos_per_class * 0.15),
                'test': int(videos_per_class * 0.15)
            }
            
            for class_name in sample_classes:
                for i in range(videos_in_split.get(split, 2)):
                    video_name = f"{class_name}_sample_{i+1:02d}.mp4"
                    labels[video_name] = class_name
            
            # Save labels
            labels_file = self.data_root / 'labels' / f'{split}_labels.json'
            with open(labels_file, 'w') as f:
                json.dump(labels, f, indent=2)
        
        logger.info("Sample dataset structure created (you still need actual video files)")
    
    def generate_training_script(self, output_file: str = "train_ssl400.sh"):
        """Generate training script with appropriate parameters"""
        validation_results = self.validate_dataset()
        n_classes = validation_results['summary']['total_classes']
        total_videos = validation_results['summary']['total_videos']
        
        # Calculate appropriate batch size based on available data
        if total_videos < 1000:
            batch_size = 4
            epochs = 50
        elif total_videos < 5000:
            batch_size = 8
            epochs = 100
        else:
            batch_size = 16
            epochs = 150
        
        script_content = f"""#!/bin/bash
# SSL400 Training Script - Auto-generated
# Dataset: {n_classes} classes, {total_videos} total videos

echo "Starting SSL400 training..."
echo "Classes: {n_classes}"
echo "Total videos: {total_videos}"
echo "Batch size: {batch_size}"
echo "Epochs: {epochs}"

python src/train.py \\
    --experiment_name ssl400_training \\
    --train_data_path {self.data_root}/train \\
    --val_data_path {self.data_root}/val \\
    --num_classes {n_classes} \\
    --batch_size {batch_size} \\
    --sequence_length 32 \\
    --epochs {epochs} \\
    --learning_rate 0.001 \\
    --optimizer adam \\
    --scheduler cosine \\
    --sequence_model lstm \\
    --pretrained_backbone

echo "Training completed!"
echo "Check logs in: logs/"
echo "Model saved to: checkpoints/"
"""
        
        with open(output_file, 'w') as f:
            f.write(script_content)
        
        # Make executable on Unix systems
        os.chmod(output_file, 0o755)
        
        logger.info(f"Training script generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='SSL400 Dataset Preparation Utility')
    parser.add_argument('--data_root', type=str, default='data/ssl400', 
                       help='Root directory for dataset')
    parser.add_argument('--action', type=str, required=True,
                       choices=['setup', 'organize', 'validate', 'sample', 'train_script'],
                       help='Action to perform')
    parser.add_argument('--source_folder', type=str, 
                       help='Source folder containing videos (for organize action)')
    parser.add_argument('--n_classes', type=int, default=50,
                       help='Number of classes for sample dataset')
    parser.add_argument('--videos_per_class', type=int, default=10,
                       help='Videos per class for sample dataset')
    
    args = parser.parse_args()
    
    # Initialize data prep utility
    data_prep = SSL400DataPrep(args.data_root)
    
    if args.action == 'setup':
        data_prep.setup_directories()
        print(f"\n✅ Directory structure created at: {args.data_root}")
        print("📋 Next steps:")
        print(f"   1. Place your SSL videos in the created directories")
        print(f"   2. Run: python data_prep_utility.py --action validate")
    
    elif args.action == 'organize':
        if not args.source_folder:
            print("❌ Please provide --source_folder for organize action")
            return
        data_prep.setup_directories()
        data_prep.organize_videos_from_folder(args.source_folder)
    
    elif args.action == 'validate':
        data_prep.print_dataset_summary()
    
    elif args.action == 'sample':
        data_prep.setup_directories()
        data_prep.create_sample_dataset(args.n_classes, args.videos_per_class)
        print(f"\n✅ Sample dataset structure created")
        print(f"📁 {args.n_classes} classes, {args.videos_per_class} videos per class")
        print("⚠️  You still need to add actual video files")
    
    elif args.action == 'train_script':
        data_prep.generate_training_script()


if __name__ == "__main__":
    main()
