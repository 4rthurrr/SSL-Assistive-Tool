#!/usr/bin/env python3
"""
SSL400 Dataset Structure Analyzer and Integrator
Based on the actual downloaded SSL400 dataset structure shown by the user.
"""

import argparse
import json
import shutil
from pathlib import Path
import cv2
import logging
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSL400DatasetHandler:
    """Handles the specific SSL400 dataset structure as shown in user's screenshots"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            self.project_root = Path(__file__).parent
        else:
            self.project_root = Path(project_root)
        
        self.data_dir = self.project_root / "data"
        self.ssl400_dir = self.data_dir / "ssl400"
        
        # Based on the user's screenshots, the structure is:
        # archive/
        #   ├── Dataset - Original/
        #   │   ├── Adjectives/
        #   │   │   ├── Bad/
        #   │   │   │   ├── Bad_001.MOV
        #   │   │   │   ├── Bad_002.MOV
        #   │   │   │   └── ...
        #   │   │   ├── Beautiful/
        #   │   │   ├── Careful/
        #   │   │   └── ... (more adjective categories)
        #   │   ├── Adverb/
        #   │   ├── Colors/
        #   │   ├── Conjunctions/
        #   │   ├── Days/
        #   │   ├── Determiner/
        #   │   ├── Greetings/
        #   │   ├── Interjection/
        #   │   ├── Months/
        #   │   ├── Nouns/
        #   │   ├── Numbers/
        #   │   ├── People/
        #   │   ├── Places/
        #   │   ├── Preposition/
        #   │   ├── Vehicles/
        #   │   └── Verbs/
        #   ├── Dataset - MP - CSV/
        #   └── Dataset - MP - VID/
    
    def analyze_ssl400_structure(self, dataset_path: str) -> Dict:
        """
        Analyze the actual SSL400 dataset structure from user's download
        
        Args:
            dataset_path: Path to the 'archive' folder or 'Dataset - Original' folder
            
        Returns:
            Dict containing analysis results
        """
        try:
            dataset_root = Path(dataset_path)
            
            # Handle different possible entry points
            if dataset_root.name == "archive":
                original_dataset = dataset_root / "Dataset - Original"
            elif dataset_root.name == "Dataset - Original":
                original_dataset = dataset_root
            else:
                # Look for "Dataset - Original" in the provided path
                original_dataset = dataset_root / "Dataset - Original"
                if not original_dataset.exists():
                    # Maybe they pointed directly to a category folder
                    original_dataset = dataset_root
            
            if not original_dataset.exists():
                logger.error(f"Could not find 'Dataset - Original' in {dataset_path}")
                return {"valid": False, "error": "Dataset - Original folder not found"}
            
            logger.info(f"🔍 Analyzing SSL400 dataset structure at: {original_dataset}")
            
            # Get all category folders (Adjectives, Adverb, Colors, etc.)
            category_folders = [d for d in original_dataset.iterdir() if d.is_dir()]
            
            analysis = {
                "valid": True,
                "dataset_path": str(original_dataset),
                "structure_type": "hierarchical_categories",
                "categories": {},
                "total_categories": len(category_folders),
                "total_classes": 0,
                "total_videos": 0,
                "video_formats": set(),
                "sample_analysis": {}
            }
            
            # Analyze each category
            for category_folder in category_folders:
                category_name = category_folder.name
                logger.info(f"📂 Analyzing category: {category_name}")
                
                # Get all class folders within this category
                class_folders = [d for d in category_folder.iterdir() if d.is_dir()]
                
                category_info = {
                    "class_count": len(class_folders),
                    "classes": [],
                    "video_count": 0
                }
                
                # Analyze each class within the category
                for class_folder in class_folders:
                    class_name = class_folder.name
                    
                    # Count videos in this class
                    videos = []
                    for ext in [".MOV", ".mov", ".MP4", ".mp4", ".AVI", ".avi"]:
                        videos.extend(list(class_folder.glob(f"*{ext}")))
                    
                    class_info = {
                        "name": class_name,
                        "video_count": len(videos),
                        "video_files": [v.name for v in videos[:3]]  # Sample first 3
                    }
                    
                    category_info["classes"].append(class_info)
                    category_info["video_count"] += len(videos)
                    analysis["total_videos"] += len(videos)
                    
                    # Track video formats
                    for video in videos:
                        analysis["video_formats"].add(video.suffix.lower())
                
                analysis["categories"][category_name] = category_info
                analysis["total_classes"] += len(class_folders)
            
            # Convert set to list for JSON serialization
            analysis["video_formats"] = list(analysis["video_formats"])
            
            # Sample video analysis
            if analysis["total_videos"] > 0:
                sample_results = self._analyze_sample_videos(original_dataset)
                analysis["sample_analysis"] = sample_results
            
            logger.info(f"✅ SSL400 Analysis Complete:")
            logger.info(f"   📊 Categories: {analysis['total_categories']}")
            logger.info(f"   🏷️  Total Classes: {analysis['total_classes']}")
            logger.info(f"   🎥 Total Videos: {analysis['total_videos']}")
            logger.info(f"   📹 Video Formats: {analysis['video_formats']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing SSL400 structure: {e}")
            return {"valid": False, "error": str(e)}
    
    def _analyze_sample_videos(self, dataset_root: Path, max_samples: int = 10) -> Dict:
        """Analyze a sample of videos to determine format specifications"""
        sample_results = {
            "analyzed_count": 0,
            "valid_count": 0,
            "fps_stats": [],
            "duration_stats": [],
            "resolution_stats": [],
            "issues": []
        }
        
        sample_count = 0
        
        # Sample videos from different categories
        for category_folder in dataset_root.iterdir():
            if not category_folder.is_dir() or sample_count >= max_samples:
                break
                
            for class_folder in category_folder.iterdir():
                if not class_folder.is_dir() or sample_count >= max_samples:
                    break
                
                # Get first video from this class
                videos = []
                for ext in [".MOV", ".mov", ".MP4", ".mp4"]:
                    videos.extend(list(class_folder.glob(f"*{ext}")))
                
                if videos:
                    video_path = videos[0]
                    video_info = self._analyze_video_file(video_path)
                    
                    if video_info:
                        sample_results["valid_count"] += 1
                        sample_results["fps_stats"].append(video_info["fps"])
                        sample_results["duration_stats"].append(video_info["duration"])
                        sample_results["resolution_stats"].append(f"{video_info['width']}x{video_info['height']}")
                    
                    sample_results["analyzed_count"] += 1
                    sample_count += 1
        
        # Calculate averages
        if sample_results["fps_stats"]:
            sample_results["avg_fps"] = sum(sample_results["fps_stats"]) / len(sample_results["fps_stats"])
            sample_results["avg_duration"] = sum(sample_results["duration_stats"]) / len(sample_results["duration_stats"])
        
        return sample_results
    
    def _analyze_video_file(self, video_path: Path) -> Optional[Dict]:
        """Analyze individual video file"""
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
                "file_size_mb": video_path.stat().st_size / (1024 * 1024)
            }
            
        except Exception as e:
            logger.debug(f"Failed to analyze video {video_path}: {e}")
            return None
    
    def create_flat_structure(self, dataset_path: str, output_path: str = None) -> bool:
        """
        Convert hierarchical SSL400 structure to flat class structure for training
        
        Args:
            dataset_path: Path to SSL400 dataset
            output_path: Where to create the flat structure (default: data/ssl400/)
        """
        try:
            if output_path is None:
                output_path = self.ssl400_dir
            else:
                output_path = Path(output_path)
            
            # First analyze the structure
            analysis = self.analyze_ssl400_structure(dataset_path)
            if not analysis["valid"]:
                logger.error("Cannot create flat structure - analysis failed")
                return False
            
            logger.info("🔧 Creating flat class structure for training...")
            
            # Create output directory
            flat_videos_dir = output_path / "videos"
            flat_videos_dir.mkdir(parents=True, exist_ok=True)
            
            # Create class mapping
            class_mapping = {}
            class_id = 0
            
            dataset_root = Path(analysis["dataset_path"])
            
            # Process each category
            for category_name, category_info in analysis["categories"].items():
                category_folder = dataset_root / category_name
                
                logger.info(f"📂 Processing category: {category_name} ({category_info['class_count']} classes)")
                
                # Process each class in this category
                for class_folder in category_folder.iterdir():
                    if not class_folder.is_dir():
                        continue
                    
                    class_name = class_folder.name
                    full_class_name = f"{category_name}_{class_name}"  # e.g., "Adjectives_Bad"
                    
                    # Create class directory in flat structure
                    flat_class_dir = flat_videos_dir / f"class_{class_id:03d}_{full_class_name}"
                    flat_class_dir.mkdir(exist_ok=True)
                    
                    # Copy all videos from this class
                    videos_copied = 0
                    for video_file in class_folder.iterdir():
                        if video_file.is_file() and video_file.suffix.lower() in ['.mov', '.mp4', '.avi']:
                            # Copy video to flat structure
                            dest_path = flat_class_dir / video_file.name
                            if not dest_path.exists():
                                shutil.copy2(video_file, dest_path)
                                videos_copied += 1
                    
                    # Update class mapping
                    class_mapping[class_id] = {
                        "id": class_id,
                        "name": full_class_name,
                        "category": category_name,
                        "original_name": class_name,
                        "video_count": videos_copied
                    }
                    
                    logger.debug(f"   ✅ {class_name} -> class_{class_id:03d} ({videos_copied} videos)")
                    class_id += 1
            
            # Save class mapping
            mapping_file = output_path / "class_mapping.json"
            with open(mapping_file, 'w') as f:
                json.dump(class_mapping, f, indent=2)
            
            # Save analysis results
            analysis_file = output_path / "dataset_analysis.json"
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            # Create training configuration
            config = {
                "dataset_name": "SSL400",
                "total_classes": len(class_mapping),
                "structure_type": "flat",
                "video_path": str(flat_videos_dir),
                "class_mapping_path": str(mapping_file),
                "analysis_path": str(analysis_file),
                "created_from": str(dataset_root)
            }
            
            config_file = output_path / "ssl400_config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("✅ Flat structure creation complete!")
            logger.info(f"   📊 Total classes: {len(class_mapping)}")
            logger.info(f"   📁 Output location: {flat_videos_dir}")
            logger.info(f"   🏷️  Class mapping: {mapping_file}")
            logger.info(f"   ⚙️  Config: {config_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating flat structure: {e}")
            return False
    
    def generate_quick_start_script(self, dataset_path: str):
        """Generate a quick start script for this specific SSL400 dataset"""
        script_content = f'''@echo off
REM SSL400 Quick Start Script for Windows
REM Generated for your specific dataset structure

echo 🚀 SSL400 Dataset Quick Start
echo.

echo Step 1: Analyzing your SSL400 dataset structure...
python ssl400_dataset_handler.py analyze --dataset-path "{dataset_path}"

echo.
echo Step 2: Creating flat training structure...
python ssl400_dataset_handler.py create-flat --dataset-path "{dataset_path}" --output-path "data\\ssl400"

echo.
echo Step 3: Validating processed dataset...
python src\\validation.py --mode dataset --ssl400-path "data\\ssl400"

echo.
echo Step 4: Starting training...
python src\\train.py --config ssl400 --data-path "data\\ssl400\\videos"

echo.
echo ✅ SSL400 setup complete! Your SSL Video-to-Text system is ready.
pause
'''
        
        script_file = self.project_root / "ssl400_quick_start.bat"
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        logger.info(f"📜 Quick start script created: {script_file}")

def main():
    parser = argparse.ArgumentParser(description="SSL400 Dataset Handler for User's Specific Structure")
    parser.add_argument("command", choices=["analyze", "create-flat", "quick-start"], 
                       help="Command to execute")
    parser.add_argument("--dataset-path", required=True, 
                       help="Path to SSL400 dataset (archive folder or Dataset - Original folder)")
    parser.add_argument("--output-path", help="Output path for processed dataset")
    parser.add_argument("--project-root", help="Project root directory")
    
    args = parser.parse_args()
    
    handler = SSL400DatasetHandler(args.project_root)
    
    if args.command == "analyze":
        analysis = handler.analyze_ssl400_structure(args.dataset_path)
        if analysis["valid"]:
            print("\n📊 SSL400 Dataset Analysis Results:")
            print(json.dumps(analysis, indent=2))
        else:
            print(f"\n❌ Analysis failed: {analysis.get('error', 'Unknown error')}")
    
    elif args.command == "create-flat":
        success = handler.create_flat_structure(args.dataset_path, args.output_path)
        if success:
            print("\n✅ Flat structure created successfully!")
            print("Next: Run training with: python src/train.py --config ssl400")
        else:
            print("\n❌ Failed to create flat structure")
            exit(1)
    
    elif args.command == "quick-start":
        handler.generate_quick_start_script(args.dataset_path)
        print("\n📜 Quick start script generated!")

if __name__ == "__main__":
    main()
