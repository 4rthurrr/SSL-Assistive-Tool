#!/usr/bin/env python3
"""
SSL400 Dataset Integration Utility
Specialized script for integrating the SSL400 dataset from IIT Colombo into the SSL Video-to-Text system.
"""

import argparse
import json
import shutil
from pathlib import Path
import cv2
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSL400Integrator:
    """Handles SSL400 dataset integration and validation"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            self.project_root = Path(__file__).parent
        else:
            self.project_root = Path(project_root)
        
        self.data_dir = self.project_root / "data"
        self.ssl400_dir = self.data_dir / "ssl400"
    
    def integrate_ssl400_dataset(self, ssl400_path: str, copy_files: bool = True) -> bool:
        """
        Integrate SSL400 dataset from IIT Colombo into the project structure.
        
        Args:
            ssl400_path: Path to the SSL400 dataset root directory
            copy_files: Whether to copy files or create symbolic links
            
        Returns:
            bool: Success status
        """
        try:
            ssl400_source = Path(ssl400_path)
            if not ssl400_source.exists():
                logger.error(f"SSL400 dataset not found at: {ssl400_source}")
                return False
            
            logger.info("🔧 Integrating SSL400 dataset from IIT Colombo...")
            
            # Create target directory structure
            self.ssl400_dir.mkdir(parents=True, exist_ok=True)
            
            # SSL400 specifications from IIT Colombo
            ssl400_specs = {
                "name": "SSL400",
                "source": "Informatics Institute of Technology (IIT), Colombo, Sri Lanka",
                "total_classes": 384,
                "video_specs": {
                    "fps": 20,
                    "duration_seconds": 3.0,
                    "expected_frames": 60,
                    "formats": ["mp4", "avi", "mov"]
                },
                "integration_date": str(Path().cwd()),
                "version": "1.0"
            }
            
            # Process dataset structure
            if copy_files:
                logger.info(f"📂 Copying SSL400 dataset to {self.ssl400_dir}")
                if (self.ssl400_dir / "videos").exists():
                    shutil.rmtree(self.ssl400_dir / "videos")
                shutil.copytree(ssl400_source, self.ssl400_dir / "videos")
            else:
                logger.info(f"🔗 Creating link to SSL400 dataset at {self.ssl400_dir}")
                link_target = self.ssl400_dir / "videos"
                if link_target.exists():
                    link_target.unlink()
                link_target.symlink_to(ssl400_source.absolute())
            
            # Validate dataset structure
            validation_results = self._validate_ssl400_structure()
            if not validation_results["valid"]:
                logger.error("❌ SSL400 dataset validation failed")
                return False
            
            # Update specs with actual findings
            ssl400_specs.update(validation_results["stats"])
            
            # Save metadata
            metadata_file = self.ssl400_dir / "ssl400_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(ssl400_specs, f, indent=2)
            
            # Create class mapping
            self._create_class_mapping(validation_results["classes"])
            
            # Generate training configuration
            self._generate_ssl400_config()
            
            logger.info("✅ SSL400 dataset integration complete!")
            logger.info(f"📊 Classes: {validation_results['stats']['actual_classes']}")
            logger.info(f"🎥 Videos: {validation_results['stats']['total_videos']}")
            logger.info(f"📁 Location: {self.ssl400_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error integrating SSL400 dataset: {e}")
            return False
    
    def _validate_ssl400_structure(self) -> Dict:
        """Validate SSL400 dataset structure and collect statistics"""
        video_dir = self.ssl400_dir / "videos"
        if not video_dir.exists():
            return {"valid": False, "error": "No videos directory found"}
        
        # Collect class directories
        class_dirs = [d for d in video_dir.iterdir() if d.is_dir()]
        class_names = [d.name for d in sorted(class_dirs)]
        
        stats = {
            "actual_classes": len(class_dirs),
            "total_videos": 0,
            "valid_videos": 0,
            "video_formats": set(),
            "fps_distribution": {},
            "duration_distribution": {}
        }
        
        # Sample videos for validation
        sample_count = 0
        max_samples = 20  # Validate first 20 videos for speed
        
        for class_dir in class_dirs:
            videos = []
            for ext in ["*.mp4", "*.avi", "*.mov"]:
                videos.extend(list(class_dir.glob(ext)))
            
            stats["total_videos"] += len(videos)
            
            # Validate sample videos from this class
            for video_path in videos[:2]:  # Max 2 per class for sampling
                if sample_count >= max_samples:
                    break
                
                video_info = self._analyze_video(video_path)
                if video_info:
                    stats["valid_videos"] += 1
                    stats["video_formats"].add(video_path.suffix.lower())
                    
                    fps = video_info.get("fps", 0)
                    duration = video_info.get("duration", 0)
                    
                    fps_range = self._get_fps_range(fps)
                    duration_range = self._get_duration_range(duration)
                    
                    stats["fps_distribution"][fps_range] = stats["fps_distribution"].get(fps_range, 0) + 1
                    stats["duration_distribution"][duration_range] = stats["duration_distribution"].get(duration_range, 0) + 1
                
                sample_count += 1
            
            if sample_count >= max_samples:
                break
        
        # Convert sets to lists for JSON serialization
        stats["video_formats"] = list(stats["video_formats"])
        
        # Validation checks
        valid = True
        issues = []
        
        if stats["actual_classes"] != 384:
            issues.append(f"Expected 384 classes, found {stats['actual_classes']}")
            # Don't fail - just warn
        
        if stats["valid_videos"] == 0:
            valid = False
            issues.append("No valid videos found")
        
        if sample_count > 0 and stats["valid_videos"] / sample_count < 0.8:
            issues.append(f"Low video validation rate: {stats['valid_videos']}/{sample_count}")
        
        return {
            "valid": valid,
            "stats": stats,
            "classes": class_names,
            "issues": issues,
            "sample_count": sample_count
        }
    
    def _analyze_video(self, video_path: Path) -> Dict:
        """Analyze a video file and extract metadata"""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return None
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "duration": duration,
                "size_mb": video_path.stat().st_size / (1024 * 1024)
            }
            
        except Exception as e:
            logger.debug(f"Failed to analyze video {video_path}: {e}")
            return None
    
    def _get_fps_range(self, fps: float) -> str:
        """Categorize FPS into ranges"""
        if fps < 15:
            return "low_fps_<15"
        elif fps < 25:
            return "standard_fps_15-25"
        elif fps < 35:
            return "high_fps_25-35"
        else:
            return "very_high_fps_35+"
    
    def _get_duration_range(self, duration: float) -> str:
        """Categorize duration into ranges"""
        if duration < 2:
            return "short_<2s"
        elif duration < 4:
            return "standard_2-4s"
        elif duration < 6:
            return "long_4-6s"
        else:
            return "very_long_6s+"
    
    def _create_class_mapping(self, class_names: List[str]):
        """Create class mapping file for SSL400"""
        class_mapping = {i: name for i, name in enumerate(class_names)}
        
        mapping_file = self.ssl400_dir / "class_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump(class_mapping, f, indent=2)
        
        # Also create reverse mapping
        reverse_mapping = {name: i for i, name in enumerate(class_names)}
        reverse_mapping_file = self.ssl400_dir / "class_to_id_mapping.json"
        with open(reverse_mapping_file, 'w') as f:
            json.dump(reverse_mapping, f, indent=2)
        
        logger.info(f"🏷️  Created class mappings with {len(class_names)} classes")
    
    def _generate_ssl400_config(self):
        """Generate SSL400-specific configuration file"""
        config = {
            "dataset": {
                "name": "SSL400",
                "type": "ssl400",
                "num_classes": 384,
                "data_path": str(self.ssl400_dir / "videos"),
                "class_mapping_path": str(self.ssl400_dir / "class_mapping.json")
            },
            "model": {
                "sequence_length": 60,
                "input_size": (224, 224),
                "num_keypoints": 21,
                "hidden_dim": 512
            },
            "training": {
                "batch_size": 8,
                "epochs": 100,
                "learning_rate": 0.001,
                "weight_decay": 0.0001
            },
            "video": {
                "target_fps": 20,
                "target_duration": 3.0,
                "expected_frames": 60
            }
        }
        
        config_file = self.ssl400_dir / "ssl400_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"⚙️  Generated SSL400 configuration: {config_file}")

def main():
    parser = argparse.ArgumentParser(description="SSL400 Dataset Integration Utility")
    parser.add_argument("--ssl400-path", required=True, help="Path to SSL400 dataset root directory")
    parser.add_argument("--copy-files", action="store_true", help="Copy files instead of creating links")
    parser.add_argument("--project-root", help="Project root directory (default: current directory)")
    
    args = parser.parse_args()
    
    integrator = SSL400Integrator(args.project_root)
    
    success = integrator.integrate_ssl400_dataset(
        ssl400_path=args.ssl400_path,
        copy_files=args.copy_files
    )
    
    if success:
        print("\n🎉 SSL400 dataset integration successful!")
        print("\nNext steps:")
        print("1. Run validation: python src/validation.py --mode dataset")
        print("2. Start training: python src/train.py --config ssl400")
        print("3. Test API: python src/inference_api.py")
    else:
        print("\n❌ SSL400 dataset integration failed. Check the logs above.")
        exit(1)

if __name__ == "__main__":
    main()
