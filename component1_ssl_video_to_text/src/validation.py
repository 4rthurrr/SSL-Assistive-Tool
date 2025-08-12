"""
SSL Video-to-Text Performance Validation
Comprehensive testing suite for accuracy, WER, and latency metrics
"""

import torch
import numpy as np
import cv2
import time
import json
from typing import Dict, List, Tuple, Optional
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import logging
from tqdm import tqdm
import editdistance
from jiwer import wer, cer
import pandas as pd

from model import create_ssl_model
from data_loader import create_ssl_dataloader, SSLVideoPreprocessor
from inference_api import SSLTranslationAPI


class SSLPerformanceValidator:
    """Comprehensive performance validation for SSL translation model"""
    
    def __init__(self, model_path: str, config_path: Optional[str] = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path
        self.config_path = config_path
        
        # Load model
        self.model = None
        self.api = None
        self.load_model()
        
        # Metrics storage
        self.results = {
            'accuracy_metrics': {},
            'word_error_rate': {},
            'latency_metrics': {},
            'confusion_matrix': None,
            'per_class_metrics': {},
            'real_world_test_results': {}
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_model(self):
        """Load model for validation"""
        try:
            # Load for direct model testing
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            if 'config' in checkpoint:
                model_config = checkpoint['config']
            else:
                model_config = {
                    'num_classes': 400,
                    'sequence_model': 'lstm',
                    'pretrained_backbone': True
                }
            
            self.model = create_ssl_model(**model_config)
            
            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            
            # Load API for end-to-end testing
            self.api = SSLTranslationAPI(self.model_path, self.config_path)
            
            self.logger.info("Model loaded successfully for validation")
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
    
    def validate_accuracy(self, test_loader) -> Dict:
        """Validate top-1 accuracy and related metrics"""
        self.logger.info("Validating accuracy metrics...")
        
        all_predictions = []
        all_labels = []
        all_confidences = []
        
        self.model.eval()
        with torch.no_grad():
            for batch in tqdm(test_loader, desc="Accuracy validation"):
                frames = batch['frames'].to(self.device)
                keypoints = batch['keypoints'].to(self.device)
                labels = batch['label'].to(self.device)
                
                predictions, confidence = self.model.get_predictions(frames, keypoints)
                
                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_confidences.extend(confidence.cpu().numpy())
        
        # Calculate metrics
        accuracy = accuracy_score(all_labels, all_predictions)
        precision, recall, f1, support = precision_recall_fscore_support(
            all_labels, all_predictions, average='weighted'
        )
        
        # Top-5 accuracy (if applicable)
        top5_accuracy = self._calculate_top5_accuracy(test_loader)
        
        # Confidence statistics
        confidence_stats = {
            'mean_confidence': np.mean(all_confidences),
            'std_confidence': np.std(all_confidences),
            'min_confidence': np.min(all_confidences),
            'max_confidence': np.max(all_confidences)
        }
        
        accuracy_metrics = {
            'top1_accuracy': accuracy,
            'top5_accuracy': top5_accuracy,
            'weighted_precision': precision,
            'weighted_recall': recall,
            'weighted_f1': f1,
            'confidence_stats': confidence_stats,
            'total_samples': len(all_labels)
        }
        
        # Store confusion matrix
        self.results['confusion_matrix'] = confusion_matrix(all_labels, all_predictions)
        
        # Per-class metrics
        self.results['per_class_metrics'] = self._calculate_per_class_metrics(
            all_labels, all_predictions
        )
        
        self.results['accuracy_metrics'] = accuracy_metrics
        return accuracy_metrics
    
    def _calculate_top5_accuracy(self, test_loader) -> float:
        """Calculate top-5 accuracy"""
        correct_top5 = 0
        total = 0
        
        self.model.eval()
        with torch.no_grad():
            for batch in test_loader:
                frames = batch['frames'].to(self.device)
                keypoints = batch['keypoints'].to(self.device)
                labels = batch['label'].to(self.device)
                
                outputs = self.model(frames, keypoints)
                logits = outputs['logits']
                
                # Get top-5 predictions
                _, top5_pred = torch.topk(logits, 5, dim=1)
                
                # Check if true label is in top-5
                correct_top5 += torch.sum(top5_pred == labels.unsqueeze(1)).item()
                total += labels.size(0)
        
        return correct_top5 / total if total > 0 else 0.0
    
    def _calculate_per_class_metrics(self, true_labels, pred_labels) -> Dict:
        """Calculate per-class precision, recall, and F1"""
        precision, recall, f1, support = precision_recall_fscore_support(
            true_labels, pred_labels, average=None
        )
        
        per_class_metrics = {}
        for class_idx in range(len(precision)):
            per_class_metrics[class_idx] = {
                'precision': precision[class_idx],
                'recall': recall[class_idx],
                'f1': f1[class_idx],
                'support': support[class_idx]
            }
        
        return per_class_metrics
    
    def validate_word_error_rate(self, test_data: List[Dict]) -> Dict:
        """Calculate Word Error Rate (WER) and Character Error Rate (CER)"""
        self.logger.info("Validating Word Error Rate...")
        
        reference_texts = []
        hypothesis_texts = []
        
        for sample in tqdm(test_data, desc="WER validation"):
            # Get ground truth text
            reference_text = sample['ground_truth_text']
            
            # Get model prediction
            predicted_text = self._predict_text_from_video(sample['video_path'])
            
            reference_texts.append(reference_text)
            hypothesis_texts.append(predicted_text)
        
        # Calculate WER and CER
        word_error_rate = wer(reference_texts, hypothesis_texts)
        char_error_rate = cer(reference_texts, hypothesis_texts)
        
        # Calculate edit distance statistics
        edit_distances = [
            editdistance.eval(ref.split(), hyp.split())
            for ref, hyp in zip(reference_texts, hypothesis_texts)
        ]
        
        wer_metrics = {
            'word_error_rate': word_error_rate,
            'character_error_rate': char_error_rate,
            'mean_edit_distance': np.mean(edit_distances),
            'std_edit_distance': np.std(edit_distances),
            'total_samples': len(test_data)
        }
        
        self.results['word_error_rate'] = wer_metrics
        return wer_metrics
    
    def _predict_text_from_video(self, video_path: str) -> str:
        """Predict text from video file"""
        cap = cv2.VideoCapture(video_path)
        predictions = []
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames for efficiency (process every 5th frame)
            if frame_count % 5 == 0:
                try:
                    # Convert frame to base64 for API
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Create request
                    from inference_api import VideoFrameRequest
                    frame_request = VideoFrameRequest(
                        video_frame=frame_base64,
                        timestamp_ms=int(frame_count * 1000 / cap.get(cv2.CAP_PROP_FPS))
                    )
                    
                    # Get prediction
                    import asyncio
                    translation = asyncio.run(self.api.translate_frame(frame_request))
                    predictions.append(translation.text)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process frame {frame_count}: {e}")
            
            frame_count += 1
        
        cap.release()
        
        # Combine predictions into text (simple concatenation)
        if predictions:
            # Remove duplicates and join
            unique_predictions = []
            for pred in predictions:
                if not unique_predictions or pred != unique_predictions[-1]:
                    unique_predictions.append(pred)
            
            return ' '.join(unique_predictions)
        else:
            return ""
    
    def validate_latency(self, test_samples: int = 100) -> Dict:
        """Measure inference latency per frame"""
        self.logger.info("Validating latency metrics...")
        
        # Generate random test data
        batch_size = 1
        seq_len = 32
        
        latencies = []
        frame_latencies = []
        
        for _ in tqdm(range(test_samples), desc="Latency validation"):
            # Create random input
            frames = torch.randn(batch_size, seq_len, 3, 224, 224).to(self.device)
            keypoints = torch.randn(batch_size, seq_len, 2, 21, 3).to(self.device)
            
            # Measure inference time
            start_time = time.time()
            
            with torch.no_grad():
                outputs = self.model(frames, keypoints)
            
            # Synchronize GPU if using CUDA
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            
            end_time = time.time()
            
            total_latency = (end_time - start_time) * 1000  # Convert to ms
            per_frame_latency = total_latency / seq_len
            
            latencies.append(total_latency)
            frame_latencies.append(per_frame_latency)
        
        # Calculate statistics
        latency_metrics = {
            'mean_latency_ms': np.mean(latencies),
            'std_latency_ms': np.std(latencies),
            'min_latency_ms': np.min(latencies),
            'max_latency_ms': np.max(latencies),
            'p95_latency_ms': np.percentile(latencies, 95),
            'p99_latency_ms': np.percentile(latencies, 99),
            'mean_per_frame_latency_ms': np.mean(frame_latencies),
            'std_per_frame_latency_ms': np.std(frame_latencies),
            'fps_estimate': 1000 / np.mean(frame_latencies),  # Frames per second
            'total_samples': test_samples
        }
        
        self.results['latency_metrics'] = latency_metrics
        return latency_metrics
    
    def real_world_testing(self, test_videos: List[str]) -> Dict:
        """Test on real-world videos with various conditions"""
        self.logger.info("Conducting real-world testing...")
        
        results = defaultdict(list)
        
        for video_path in tqdm(test_videos, desc="Real-world testing"):
            try:
                # Analyze video properties
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                
                # Process video and measure performance
                start_time = time.time()
                predicted_text = self._predict_text_from_video(video_path)
                processing_time = time.time() - start_time
                
                # Calculate metrics
                processing_fps = frame_count / processing_time if processing_time > 0 else 0
                real_time_factor = processing_fps / fps if fps > 0 else 0
                
                video_result = {
                    'video_path': video_path,
                    'duration_s': duration,
                    'fps': fps,
                    'resolution': f"{width}x{height}",
                    'frame_count': frame_count,
                    'predicted_text': predicted_text,
                    'processing_time_s': processing_time,
                    'processing_fps': processing_fps,
                    'real_time_factor': real_time_factor,
                    'success': True
                }
                
                results['successful_videos'].append(video_result)
                
            except Exception as e:
                self.logger.error(f"Failed to process video {video_path}: {e}")
                results['failed_videos'].append({
                    'video_path': video_path,
                    'error': str(e),
                    'success': False
                })
        
        # Calculate aggregate statistics
        successful_results = results['successful_videos']
        if successful_results:
            real_time_factors = [r['real_time_factor'] for r in successful_results]
            processing_times = [r['processing_time_s'] for r in successful_results]
            
            aggregate_stats = {
                'total_videos': len(test_videos),
                'successful_videos': len(successful_results),
                'failed_videos': len(results['failed_videos']),
                'success_rate': len(successful_results) / len(test_videos),
                'mean_real_time_factor': np.mean(real_time_factors),
                'std_real_time_factor': np.std(real_time_factors),
                'mean_processing_time_s': np.mean(processing_times),
                'videos_processed_real_time': sum(1 for rtf in real_time_factors if rtf >= 1.0)
            }
            
            results['aggregate_stats'] = aggregate_stats
        
        self.results['real_world_test_results'] = dict(results)
        return dict(results)
    
    def unit_test_known_gestures(self, known_gesture_tests: List[Dict]) -> Dict:
        """Unit tests for known gesture videos"""
        self.logger.info("Running unit tests for known gestures...")
        
        test_results = []
        
        for test_case in tqdm(known_gesture_tests, desc="Unit testing"):
            video_path = test_case['video_path']
            expected_text = test_case['expected_text']
            
            try:
                # Get prediction
                predicted_text = self._predict_text_from_video(video_path)
                
                # Check if prediction matches expected
                is_correct = predicted_text.strip().lower() == expected_text.strip().lower()
                
                test_result = {
                    'video_path': video_path,
                    'expected_text': expected_text,
                    'predicted_text': predicted_text,
                    'is_correct': is_correct,
                    'success': True
                }
                
            except Exception as e:
                test_result = {
                    'video_path': video_path,
                    'expected_text': expected_text,
                    'predicted_text': "",
                    'is_correct': False,
                    'error': str(e),
                    'success': False
                }
            
            test_results.append(test_result)
        
        # Calculate summary statistics
        total_tests = len(test_results)
        successful_tests = sum(1 for r in test_results if r['success'])
        correct_predictions = sum(1 for r in test_results if r.get('is_correct', False))
        
        unit_test_summary = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'correct_predictions': correct_predictions,
            'unit_test_accuracy': correct_predictions / total_tests if total_tests > 0 else 0,
            'test_execution_rate': successful_tests / total_tests if total_tests > 0 else 0,
            'detailed_results': test_results
        }
        
        return unit_test_summary
    
    def generate_report(self, output_path: str = "validation_report.json"):
        """Generate comprehensive validation report"""
        self.logger.info("Generating validation report...")
        
        # Add summary metrics
        summary = {
            'validation_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'model_path': self.model_path,
            'device': str(self.device),
            'summary_metrics': {}
        }
        
        # Extract key metrics for summary
        if 'accuracy_metrics' in self.results:
            summary['summary_metrics']['top1_accuracy'] = self.results['accuracy_metrics']['top1_accuracy']
        
        if 'word_error_rate' in self.results:
            summary['summary_metrics']['word_error_rate'] = self.results['word_error_rate']['word_error_rate']
        
        if 'latency_metrics' in self.results:
            summary['summary_metrics']['mean_latency_ms_per_frame'] = self.results['latency_metrics']['mean_per_frame_latency_ms']
            summary['summary_metrics']['fps_estimate'] = self.results['latency_metrics']['fps_estimate']
        
        # Combine all results
        full_report = {
            'summary': summary,
            'detailed_results': self.results
        }
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(full_report, f, indent=2, default=str)
        
        self.logger.info(f"Validation report saved to {output_path}")
        
        # Print summary to console
        self._print_summary(summary)
        
        return full_report
    
    def _print_summary(self, summary: Dict):
        """Print validation summary to console"""
        print("\n" + "="*60)
        print("SSL VIDEO-TO-TEXT VALIDATION SUMMARY")
        print("="*60)
        
        print(f"Model: {summary['model_path']}")
        print(f"Device: {summary['device']}")
        print(f"Validation Time: {summary['validation_timestamp']}")
        
        if 'summary_metrics' in summary:
            metrics = summary['summary_metrics']
            print(f"\nKey Performance Metrics:")
            print(f"- Top-1 Accuracy: {metrics.get('top1_accuracy', 'N/A'):.4f}")
            print(f"- Word Error Rate: {metrics.get('word_error_rate', 'N/A'):.4f}")
            print(f"- Latency per Frame: {metrics.get('mean_latency_ms_per_frame', 'N/A'):.2f} ms")
            print(f"- FPS Estimate: {metrics.get('fps_estimate', 'N/A'):.1f}")
        
        print("\n" + "="*60)
    
    def plot_confusion_matrix(self, output_path: str = "confusion_matrix.png"):
        """Plot and save confusion matrix"""
        if self.results['confusion_matrix'] is None:
            self.logger.warning("No confusion matrix available")
            return
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(
            self.results['confusion_matrix'],
            annot=False,
            cmap='Blues',
            fmt='d'
        )
        plt.title('SSL Translation Confusion Matrix')
        plt.xlabel('Predicted Class')
        plt.ylabel('True Class')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Confusion matrix saved to {output_path}")


def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SSL Video-to-Text Validation')
    parser.add_argument('--model_path', type=str, required=True, help='Path to trained model')
    parser.add_argument('--config_path', type=str, default=None, help='Path to model config')
    parser.add_argument('--test_data_path', type=str, required=True, help='Path to test data')
    parser.add_argument('--output_dir', type=str, default='validation_results', help='Output directory')
    parser.add_argument('--run_accuracy', action='store_true', help='Run accuracy validation')
    parser.add_argument('--run_wer', action='store_true', help='Run WER validation')
    parser.add_argument('--run_latency', action='store_true', help='Run latency validation')
    parser.add_argument('--run_real_world', action='store_true', help='Run real-world testing')
    parser.add_argument('--run_all', action='store_true', help='Run all validations')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize validator
    validator = SSLPerformanceValidator(args.model_path, args.config_path)
    
    # Run selected validations
    if args.run_all or args.run_accuracy:
        # You'll need to implement test data loading based on your format
        # test_loader = create_ssl_dataloader(test_video_paths, test_labels, ...)
        # validator.validate_accuracy(test_loader)
        pass
    
    if args.run_all or args.run_latency:
        validator.validate_latency()
    
    # Generate report
    report_path = os.path.join(args.output_dir, "validation_report.json")
    validator.generate_report(report_path)
    
    # Plot confusion matrix if available
    cm_path = os.path.join(args.output_dir, "confusion_matrix.png")
    validator.plot_confusion_matrix(cm_path)


if __name__ == "__main__":
    main()
