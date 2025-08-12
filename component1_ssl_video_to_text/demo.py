#!/usr/bin/env python3
"""
SSL Video-to-Text Demo Script
Quick demonstration of the SSL translation system
"""

import cv2
import torch
import numpy as np
import asyncio
import base64
import argparse
import json
from pathlib import Path
from typing import List, Dict
import time

from src.inference_api import SSLTranslationAPI, VideoFrameRequest
from src.model import create_ssl_model
from src.data_loader import SSLVideoPreprocessor


class SSLTranslationDemo:
    """Demo application for SSL Video-to-Text translation"""
    
    def __init__(self, model_path: str, config_path: str = None):
        self.model_path = model_path
        self.config_path = config_path
        
        # Initialize API
        try:
            self.api = SSLTranslationAPI(model_path, config_path)
            print(f"✓ Model loaded successfully")
            print(f"  - Classes: {len(self.api.class_names)}")
            print(f"  - Device: {self.api.device}")
        except Exception as e:
            print(f"✗ Failed to load model: {e}")
            raise
    
    async def demo_webcam_translation(self, camera_id: int = 0, max_frames: int = 100):
        """Demo real-time webcam translation"""
        print(f"\nStarting webcam demo (Camera {camera_id})...")
        print("Press 'q' to quit")
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"✗ Cannot open camera {camera_id}")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        frame_count = 0
        translations = []
        
        try:
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    print("✗ Failed to capture frame")
                    break
                
                # Skip frames for efficiency (process every 5th frame)
                if frame_count % 5 == 0:
                    try:
                        # Convert frame to base64
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # Create request
                        frame_request = VideoFrameRequest(
                            video_frame=frame_base64,
                            timestamp_ms=int(time.time() * 1000)
                        )
                        
                        # Get translation
                        translation = await self.api.translate_frame(frame_request)
                        translations.append(translation)
                        
                        # Display result on frame
                        text = f"{translation.text} ({translation.confidence:.2f})"
                        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                                  1, (0, 255, 0), 2)
                        cv2.putText(frame, f"Frame: {frame_count}", (10, 60), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        
                        print(f"Frame {frame_count}: {translation.text} "
                              f"(conf: {translation.confidence:.3f}, "
                              f"time: {translation.processing_time_ms:.1f}ms)")
                        
                    except Exception as e:
                        print(f"✗ Translation error: {e}")
                
                # Show frame
                cv2.imshow('SSL Translation Demo', frame)
                
                # Check for quit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                frame_count += 1
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        # Print summary
        if translations:
            avg_confidence = np.mean([t.confidence for t in translations])
            avg_processing_time = np.mean([t.processing_time_ms for t in translations])
            
            print(f"\n📊 Demo Summary:")
            print(f"  - Processed frames: {len(translations)}")
            print(f"  - Average confidence: {avg_confidence:.3f}")
            print(f"  - Average processing time: {avg_processing_time:.1f}ms")
            
            # Show unique translations
            unique_translations = list(set([t.text for t in translations]))
            print(f"  - Unique translations: {len(unique_translations)}")
            print(f"  - Translations: {', '.join(unique_translations[:10])}")
    
    async def demo_video_file_translation(self, video_path: str):
        """Demo video file translation"""
        print(f"\nTranslating video file: {video_path}")
        
        if not Path(video_path).exists():
            print(f"✗ Video file not found: {video_path}")
            return
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        print(f"  - Duration: {duration:.1f}s")
        print(f"  - FPS: {fps}")
        print(f"  - Total frames: {total_frames}")
        
        translations = []
        frame_count = 0
        start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every 10th frame for efficiency
                if frame_count % 10 == 0:
                    try:
                        # Convert frame to base64
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # Calculate timestamp
                        timestamp_ms = int((frame_count / fps) * 1000) if fps > 0 else frame_count * 33
                        
                        frame_request = VideoFrameRequest(
                            video_frame=frame_base64,
                            timestamp_ms=timestamp_ms
                        )
                        
                        translation = await self.api.translate_frame(frame_request)
                        translations.append(translation)
                        
                        print(f"  Frame {frame_count}/{total_frames}: {translation.text} "
                              f"(t={timestamp_ms/1000:.1f}s, conf={translation.confidence:.3f})")
                        
                    except Exception as e:
                        print(f"✗ Error processing frame {frame_count}: {e}")
                
                frame_count += 1
        
        finally:
            cap.release()
        
        processing_time = time.time() - start_time
        
        # Generate transcript
        transcript = self.generate_transcript(translations)
        
        print(f"\n📄 Video Translation Results:")
        print(f"  - Processed {len(translations)} frames in {processing_time:.1f}s")
        print(f"  - Processing speed: {len(translations)/processing_time:.1f} frames/s")
        print(f"  - Transcript: {transcript}")
        
        # Save results
        output_path = Path(video_path).stem + "_translation.json"
        self.save_translation_results(translations, transcript, output_path)
        print(f"  - Results saved to: {output_path}")
    
    def generate_transcript(self, translations: List) -> str:
        """Generate a readable transcript from translations"""
        if not translations:
            return ""
        
        # Group consecutive similar translations
        grouped_translations = []
        current_text = translations[0].text
        current_start = translations[0].timestamp_ms
        current_confidence = translations[0].confidence
        
        for translation in translations[1:]:
            if translation.text == current_text:
                # Update confidence to average
                current_confidence = (current_confidence + translation.confidence) / 2
            else:
                # Add current group
                grouped_translations.append({
                    'text': current_text,
                    'start_time': current_start,
                    'end_time': translation.timestamp_ms,
                    'confidence': current_confidence
                })
                
                # Start new group
                current_text = translation.text
                current_start = translation.timestamp_ms
                current_confidence = translation.confidence
        
        # Add last group
        grouped_translations.append({
            'text': current_text,
            'start_time': current_start,
            'end_time': translations[-1].timestamp_ms,
            'confidence': current_confidence
        })
        
        # Create transcript
        transcript_parts = []
        for group in grouped_translations:
            if group['confidence'] > 0.5:  # Only include high-confidence translations
                start_sec = group['start_time'] / 1000
                text = group['text']
                transcript_parts.append(f"[{start_sec:.1f}s] {text}")
        
        return " ".join([part.split('] ')[-1] for part in transcript_parts])
    
    def save_translation_results(self, translations: List, transcript: str, output_path: str):
        """Save translation results to JSON file"""
        results = {
            'transcript': transcript,
            'detailed_translations': [
                {
                    'text': t.text,
                    'confidence': t.confidence,
                    'timestamp_ms': t.timestamp_ms,
                    'processing_time_ms': t.processing_time_ms
                }
                for t in translations
            ],
            'statistics': {
                'total_translations': len(translations),
                'average_confidence': np.mean([t.confidence for t in translations]),
                'average_processing_time_ms': np.mean([t.processing_time_ms for t in translations]),
                'unique_signs': len(set([t.text for t in translations]))
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
    
    async def demo_batch_translation(self, image_folder: str):
        """Demo batch image translation"""
        print(f"\nBatch translating images from: {image_folder}")
        
        image_folder = Path(image_folder)
        if not image_folder.exists():
            print(f"✗ Folder not found: {image_folder}")
            return
        
        # Find image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_files = [f for f in image_folder.glob('*') if f.suffix.lower() in image_extensions]
        
        if not image_files:
            print("✗ No image files found")
            return
        
        print(f"Found {len(image_files)} images")
        
        translations = []
        
        for i, image_file in enumerate(image_files):
            try:
                # Load and encode image
                with open(image_file, 'rb') as f:
                    image_base64 = base64.b64encode(f.read()).decode('utf-8')
                
                frame_request = VideoFrameRequest(
                    video_frame=image_base64,
                    timestamp_ms=i * 1000  # 1 second intervals
                )
                
                translation = await self.api.translate_frame(frame_request)
                translations.append(translation)
                
                print(f"  {image_file.name}: {translation.text} (conf: {translation.confidence:.3f})")
                
            except Exception as e:
                print(f"✗ Error processing {image_file.name}: {e}")
        
        # Summary
        if translations:
            avg_confidence = np.mean([t.confidence for t in translations])
            print(f"\n📊 Batch Translation Summary:")
            print(f"  - Images processed: {len(translations)}")
            print(f"  - Average confidence: {avg_confidence:.3f}")
            
            # Most common translations
            translation_counts = {}
            for t in translations:
                translation_counts[t.text] = translation_counts.get(t.text, 0) + 1
            
            sorted_translations = sorted(translation_counts.items(), key=lambda x: x[1], reverse=True)
            print(f"  - Most common: {sorted_translations[:5]}")
    
    def demo_model_info(self):
        """Display model information"""
        print(f"\n🤖 Model Information:")
        print(f"  - Model path: {self.model_path}")
        print(f"  - Config path: {self.config_path}")
        print(f"  - Device: {self.api.device}")
        print(f"  - Model loaded: {self.api.model_loaded}")
        print(f"  - Number of classes: {len(self.api.class_names)}")
        print(f"  - Sequence length: {self.api.sequence_length}")
        
        # Performance stats
        stats = self.api.get_performance_stats()
        print(f"\n📈 Performance Statistics:")
        print(f"  - Total inferences: {stats['total_inferences']}")
        if stats['total_inferences'] > 0:
            print(f"  - Average latency: {stats['average_inference_time_ms']:.1f}ms")
            print(f"  - Min latency: {stats['min_inference_time_ms']:.1f}ms")
            print(f"  - Max latency: {stats['max_inference_time_ms']:.1f}ms")
        
        # Sample classes
        print(f"\n📝 Sample SSL Classes:")
        for i, class_name in enumerate(self.api.class_names[:10]):
            print(f"  {i}: {class_name}")
        if len(self.api.class_names) > 10:
            print(f"  ... and {len(self.api.class_names) - 10} more classes")


async def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description='SSL Video-to-Text Translation Demo')
    parser.add_argument('--model_path', type=str, required=True, 
                       help='Path to trained SSL model')
    parser.add_argument('--config_path', type=str, default=None,
                       help='Path to model configuration')
    parser.add_argument('--demo_type', type=str, 
                       choices=['webcam', 'video', 'batch', 'info'], 
                       default='info', help='Type of demo to run')
    parser.add_argument('--input_path', type=str, default=None,
                       help='Input path (video file or image folder)')
    parser.add_argument('--camera_id', type=int, default=0,
                       help='Camera ID for webcam demo')
    parser.add_argument('--max_frames', type=int, default=100,
                       help='Maximum frames to process in webcam demo')
    
    args = parser.parse_args()
    
    # Validate model path
    if not Path(args.model_path).exists():
        print(f"✗ Model file not found: {args.model_path}")
        print("Please ensure you have a trained model file.")
        return
    
    try:
        # Initialize demo
        demo = SSLTranslationDemo(args.model_path, args.config_path)
        
        # Run selected demo
        if args.demo_type == 'info':
            demo.demo_model_info()
        
        elif args.demo_type == 'webcam':
            await demo.demo_webcam_translation(args.camera_id, args.max_frames)
        
        elif args.demo_type == 'video':
            if not args.input_path:
                print("✗ Please provide --input_path for video demo")
                return
            await demo.demo_video_file_translation(args.input_path)
        
        elif args.demo_type == 'batch':
            if not args.input_path:
                print("✗ Please provide --input_path for batch demo")
                return
            await demo.demo_batch_translation(args.input_path)
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🎯 SSL Video-to-Text Translation Demo")
    print("=" * 40)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
