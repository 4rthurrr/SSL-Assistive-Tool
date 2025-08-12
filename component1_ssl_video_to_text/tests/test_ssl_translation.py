"""
SSL Video-to-Text Test Suite
Unit and integration tests for the SSL translation system
"""

import unittest
import torch
import numpy as np
import cv2
import asyncio
import tempfile
import os
import base64
from unittest.mock import Mock, patch, MagicMock
import json
from io import BytesIO
from PIL import Image

# Import modules to test
import sys
sys.path.append('src')

from model import create_ssl_model, SSLTranslationModel, FewShotLearningWrapper
from data_loader import SSLVideoPreprocessor, SSL400Dataset, decode_base64_frame
from inference_api import SSLTranslationAPI, VideoFrameRequest


class TestSSLVideoPreprocessor(unittest.TestCase):
    """Test SSL video preprocessing functionality"""
    
    def setUp(self):
        self.preprocessor = SSLVideoPreprocessor()
    
    def test_extract_hand_keypoints(self):
        """Test hand keypoint extraction"""
        # Create a test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Extract keypoints
        keypoints = self.preprocessor.extract_hand_keypoints(frame)
        
        # Check shape: (max_hands=2, keypoints=21, coordinates=3)
        self.assertEqual(keypoints.shape, (2, 21, 3))
        
        # Check value ranges (normalized coordinates should be [0,1])
        # Note: For empty frames, keypoints might be zeros
        self.assertTrue(np.all(keypoints >= 0))
        self.assertTrue(np.all(keypoints <= 1))
    
    def test_normalize_frame(self):
        """Test frame normalization"""
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Normalize
        normalized = self.preprocessor.normalize_frame(frame)
        
        # Check output shape (should be resized to 224x224)
        self.assertEqual(normalized.shape, (224, 224, 3))
        
        # Check value range (should be [0, 1])
        self.assertTrue(np.all(normalized >= 0))
        self.assertTrue(np.all(normalized <= 1))
        
        # Check data type
        self.assertEqual(normalized.dtype, np.float32)
    
    def test_temporal_jitter(self):
        """Test temporal jittering"""
        # Create test sequence
        sequence = [np.random.rand(224, 224, 3) for _ in range(10)]
        original_length = len(sequence)
        
        # Apply jittering multiple times
        jittered_lengths = []
        for _ in range(10):
            jittered = self.preprocessor.temporal_jitter(sequence.copy(), jitter_ratio=0.2)
            jittered_lengths.append(len(jittered))
        
        # Check that at least some sequences were modified
        self.assertTrue(any(length != original_length for length in jittered_lengths))
        
        # Check that sequences are not empty
        self.assertTrue(all(length > 0 for length in jittered_lengths))
    
    def test_process_frame(self):
        """Test complete frame processing"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Process frame
        processed_frame, keypoints = self.preprocessor.process_frame(frame, apply_augmentation=False)
        
        # Check processed frame
        if isinstance(processed_frame, torch.Tensor):
            self.assertEqual(processed_frame.shape, torch.Size([3, 224, 224]))
        else:
            self.assertEqual(processed_frame.shape, (224, 224, 3))
        
        # Check keypoints
        self.assertEqual(keypoints.shape, (2, 21, 3))


class TestSSLTranslationModel(unittest.TestCase):
    """Test SSL translation model functionality"""
    
    def setUp(self):
        self.device = torch.device('cpu')  # Use CPU for testing
        self.batch_size = 2
        self.seq_len = 8
        self.num_classes = 10  # Small number for testing
        
        # Create test model
        self.model = create_ssl_model(
            num_classes=self.num_classes,
            sequence_model='lstm',
            pretrained_backbone=False  # Disable pretrained for testing
        )
        self.model.to(self.device)
    
    def test_model_creation(self):
        """Test model creation"""
        self.assertIsInstance(self.model, SSLTranslationModel)
        self.assertEqual(self.model.num_classes, self.num_classes)
        self.assertEqual(self.model.sequence_model_type, 'lstm')
    
    def test_forward_pass(self):
        """Test model forward pass"""
        # Create test inputs
        frames = torch.randn(self.batch_size, self.seq_len, 3, 224, 224)
        keypoints = torch.randn(self.batch_size, self.seq_len, 2, 21, 3)
        
        # Forward pass
        outputs = self.model(frames, keypoints)
        
        # Check output structure
        self.assertIn('logits', outputs)
        self.assertIn('cnn_features', outputs)
        self.assertIn('keypoint_features', outputs)
        self.assertIn('combined_features', outputs)
        
        # Check logits shape
        expected_logits_shape = (self.batch_size, self.num_classes)
        self.assertEqual(outputs['logits'].shape, expected_logits_shape)
    
    def test_get_predictions(self):
        """Test prediction generation"""
        frames = torch.randn(self.batch_size, self.seq_len, 3, 224, 224)
        keypoints = torch.randn(self.batch_size, self.seq_len, 2, 21, 3)
        
        predictions, confidence = self.model.get_predictions(frames, keypoints)
        
        # Check shapes
        self.assertEqual(predictions.shape, (self.batch_size,))
        self.assertEqual(confidence.shape, (self.batch_size,))
        
        # Check value ranges
        self.assertTrue(torch.all(predictions >= 0))
        self.assertTrue(torch.all(predictions < self.num_classes))
        self.assertTrue(torch.all(confidence >= 0))
        self.assertTrue(torch.all(confidence <= 1))
    
    def test_transformer_model(self):
        """Test transformer variant"""
        transformer_model = create_ssl_model(
            num_classes=self.num_classes,
            sequence_model='transformer',
            pretrained_backbone=False,
            transformer_d_model=64,  # Small for testing
            transformer_nhead=4,
            transformer_num_layers=2
        )
        
        frames = torch.randn(self.batch_size, self.seq_len, 3, 224, 224)
        keypoints = torch.randn(self.batch_size, self.seq_len, 2, 21, 3)
        
        outputs = transformer_model(frames, keypoints)
        
        # Check output shape
        expected_shape = (self.batch_size, self.num_classes)
        self.assertEqual(outputs['logits'].shape, expected_shape)


class TestDataLoader(unittest.TestCase):
    """Test data loading functionality"""
    
    def test_decode_base64_frame(self):
        """Test base64 frame decoding"""
        # Create test image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        pil_image = Image.fromarray(test_image)
        
        # Convert to base64
        buffer = BytesIO()
        pil_image.save(buffer, format='PNG')
        base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Decode
        decoded_frame = decode_base64_frame(base64_string)
        
        # Check shape and type
        self.assertEqual(len(decoded_frame.shape), 3)
        self.assertEqual(decoded_frame.dtype, np.uint8)
    
    def test_ssl400_dataset_creation(self):
        """Test SSL400 dataset creation"""
        # Mock data
        video_paths = ['video1.mp4', 'video2.mp4']
        labels = ['class1', 'class2']
        
        with patch('cv2.VideoCapture'):
            dataset = SSL400Dataset(
                video_paths=video_paths,
                labels=labels,
                sequence_length=16,
                is_training=False
            )
            
            self.assertEqual(len(dataset), 2)
            self.assertEqual(dataset.sequence_length, 16)
            self.assertIn('class1', dataset.label_to_idx)
            self.assertIn('class2', dataset.label_to_idx)


class TestInferenceAPI(unittest.TestCase):
    """Test inference API functionality"""
    
    def setUp(self):
        # Create a mock model file
        self.temp_model_file = tempfile.NamedTemporaryFile(suffix='.pth', delete=False)
        
        # Create mock checkpoint
        mock_model = create_ssl_model(num_classes=10, pretrained_backbone=False)
        checkpoint = {
            'model_state_dict': mock_model.state_dict(),
            'config': {
                'num_classes': 10,
                'sequence_model': 'lstm',
                'pretrained_backbone': False
            },
            'class_names': [f'class_{i}' for i in range(10)]
        }
        
        torch.save(checkpoint, self.temp_model_file.name)
        self.temp_model_file.close()
    
    def tearDown(self):
        # Clean up temp file
        os.unlink(self.temp_model_file.name)
    
    def test_api_initialization(self):
        """Test API initialization"""
        api = SSLTranslationAPI(self.temp_model_file.name)
        
        self.assertTrue(api.model_loaded)
        self.assertEqual(len(api.class_names), 10)
        self.assertIsNotNone(api.model)
    
    def test_preprocess_frame(self):
        """Test frame preprocessing in API"""
        api = SSLTranslationAPI(self.temp_model_file.name)
        
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Preprocess
        processed_frame, keypoints = api.preprocess_frame(frame)
        
        # Check shapes
        self.assertEqual(processed_frame.shape, torch.Size([3, 224, 224]))
        self.assertEqual(keypoints.shape, torch.Size([2, 21, 3]))
    
    def test_sequence_buffer(self):
        """Test sequence buffer management"""
        api = SSLTranslationAPI(self.temp_model_file.name)
        
        # Add frames to buffer
        for i in range(5):
            frame = torch.randn(3, 224, 224)
            keypoints = torch.randn(2, 21, 3)
            api.update_sequence_buffer(frame, keypoints)
        
        self.assertEqual(len(api.frame_buffer), 5)
        self.assertEqual(len(api.keypoint_buffer), 5)
        
        # Get sequence batch
        frames_batch, keypoints_batch = api.get_sequence_batch()
        
        # Check batch shapes
        expected_seq_len = api.sequence_length
        self.assertEqual(frames_batch.shape, (1, expected_seq_len, 3, 224, 224))
        self.assertEqual(keypoints_batch.shape, (1, expected_seq_len, 2, 21, 3))
    
    async def test_translate_frame(self):
        """Test frame translation"""
        api = SSLTranslationAPI(self.temp_model_file.name)
        
        # Create test frame request
        test_frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        pil_image = Image.fromarray(test_frame)
        buffer = BytesIO()
        pil_image.save(buffer, format='PNG')
        base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        frame_request = VideoFrameRequest(
            video_frame=base64_string,
            timestamp_ms=1000
        )
        
        # Translate
        response = await api.translate_frame(frame_request)
        
        # Check response
        self.assertIsInstance(response.text, str)
        self.assertIsInstance(response.confidence, float)
        self.assertEqual(response.timestamp_ms, 1000)
        self.assertGreaterEqual(response.processing_time_ms, 0)
        self.assertGreaterEqual(response.confidence, 0)
        self.assertLessEqual(response.confidence, 1)
    
    def test_get_status(self):
        """Test status endpoint"""
        api = SSLTranslationAPI(self.temp_model_file.name)
        
        status = api.get_status()
        
        self.assertEqual(status.status, "running")
        self.assertTrue(status.model_loaded)
        self.assertEqual(status.supported_classes, 10)
        self.assertEqual(status.version, "1.0.0")


class TestIntegration(unittest.TestCase):
    """Integration tests for end-to-end functionality"""
    
    def setUp(self):
        # Create temporary model
        self.temp_model_file = tempfile.NamedTemporaryFile(suffix='.pth', delete=False)
        mock_model = create_ssl_model(num_classes=5, pretrained_backbone=False)
        checkpoint = {
            'model_state_dict': mock_model.state_dict(),
            'config': {
                'num_classes': 5,
                'sequence_model': 'lstm',
                'pretrained_backbone': False
            },
            'class_names': ['hello', 'goodbye', 'please', 'thank_you', 'sorry']
        }
        torch.save(checkpoint, self.temp_model_file.name)
        self.temp_model_file.close()
    
    def tearDown(self):
        os.unlink(self.temp_model_file.name)
    
    async def test_end_to_end_video_translation(self):
        """Test complete video-to-text translation pipeline"""
        # Create API
        api = SSLTranslationAPI(self.temp_model_file.name)
        
        # Create test video frames
        frames = []
        for i in range(10):
            # Create synthetic gesture frame
            frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            pil_image = Image.fromarray(frame)
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            frames.append(VideoFrameRequest(
                video_frame=base64_string,
                timestamp_ms=i * 100
            ))
        
        # Process frames sequentially
        translations = []
        for frame_request in frames:
            translation = await api.translate_frame(frame_request)
            translations.append(translation)
        
        # Check results
        self.assertEqual(len(translations), 10)
        
        # Check that all translations are valid
        for translation in translations:
            self.assertIn(translation.text, api.class_names)
            self.assertGreaterEqual(translation.confidence, 0)
            self.assertLessEqual(translation.confidence, 1)
            self.assertGreater(translation.processing_time_ms, 0)
    
    def test_known_gesture_video_translation(self):
        """Unit test: known gesture video → expected text"""
        # This would test with actual SSL video files
        # For now, we'll create a mock test
        
        # Create mock video processor
        processor = SSLVideoPreprocessor()
        
        # Create synthetic "known" gesture
        known_gesture_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Process frame
        processed_frame, keypoints = processor.process_frame(known_gesture_frame, apply_augmentation=False)
        
        # Verify processing completed without errors
        self.assertIsNotNone(processed_frame)
        self.assertIsNotNone(keypoints)
        
        # Check shapes
        if isinstance(processed_frame, torch.Tensor):
            self.assertEqual(processed_frame.shape, torch.Size([3, 224, 224]))
        else:
            self.assertEqual(processed_frame.shape, (224, 224, 3))
        
        self.assertEqual(keypoints.shape, (2, 21, 3))


class TestFewShotLearning(unittest.TestCase):
    """Test few-shot learning functionality"""
    
    def test_few_shot_wrapper_creation(self):
        """Test few-shot learning wrapper creation"""
        base_model = create_ssl_model(num_classes=10, pretrained_backbone=False)
        few_shot_model = FewShotLearningWrapper(base_model, support_set_size=5)
        
        self.assertIsInstance(few_shot_model, FewShotLearningWrapper)
        self.assertEqual(few_shot_model.support_set_size, 5)
    
    def test_few_shot_forward_pass(self):
        """Test few-shot learning forward pass"""
        base_model = create_ssl_model(num_classes=10, pretrained_backbone=False)
        few_shot_model = FewShotLearningWrapper(base_model)
        
        # Create test data
        n_way, n_shot, n_queries = 3, 2, 5
        seq_len = 8
        
        support_frames = torch.randn(n_way, n_shot, seq_len, 3, 224, 224)
        support_keypoints = torch.randn(n_way, n_shot, seq_len, 2, 21, 3)
        support_labels = torch.arange(n_way).unsqueeze(1).expand(-1, n_shot)
        
        query_frames = torch.randn(n_queries, seq_len, 3, 224, 224)
        query_keypoints = torch.randn(n_queries, seq_len, 2, 21, 3)
        
        # Forward pass
        similarities = few_shot_model(
            support_frames, support_keypoints, support_labels,
            query_frames, query_keypoints
        )
        
        # Check output shape
        self.assertEqual(similarities.shape, (n_queries, n_way))


def run_test_suite():
    """Run the complete test suite"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestSSLVideoPreprocessor))
    suite.addTest(unittest.makeSuite(TestSSLTranslationModel))
    suite.addTest(unittest.makeSuite(TestDataLoader))
    suite.addTest(unittest.makeSuite(TestInferenceAPI))
    suite.addTest(unittest.makeSuite(TestIntegration))
    suite.addTest(unittest.makeSuite(TestFewShotLearning))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


async def run_async_tests():
    """Run async tests separately"""
    print("Running async integration tests...")
    
    # Create temporary model for testing
    temp_model_file = tempfile.NamedTemporaryFile(suffix='.pth', delete=False)
    mock_model = create_ssl_model(num_classes=5, pretrained_backbone=False)
    checkpoint = {
        'model_state_dict': mock_model.state_dict(),
        'config': {
            'num_classes': 5,
            'sequence_model': 'lstm',
            'pretrained_backbone': False
        },
        'class_names': ['hello', 'goodbye', 'please', 'thank_you', 'sorry']
    }
    torch.save(checkpoint, temp_model_file.name)
    temp_model_file.close()
    
    try:
        # Test async API functionality
        api = SSLTranslationAPI(temp_model_file.name)
        
        # Create test frame
        test_frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        pil_image = Image.fromarray(test_frame)
        buffer = BytesIO()
        pil_image.save(buffer, format='PNG')
        base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        frame_request = VideoFrameRequest(
            video_frame=base64_string,
            timestamp_ms=1000
        )
        
        # Test translation
        response = await api.translate_frame(frame_request)
        
        print(f"✓ Async translation test passed")
        print(f"  - Predicted text: {response.text}")
        print(f"  - Confidence: {response.confidence:.4f}")
        print(f"  - Processing time: {response.processing_time_ms:.2f}ms")
        
        # Test end-to-end workflow
        integration_test = TestIntegration()
        integration_test.setUp()
        await integration_test.test_end_to_end_video_translation()
        integration_test.tearDown()
        
        print("✓ End-to-end integration test passed")
        
    finally:
        # Clean up
        os.unlink(temp_model_file.name)


if __name__ == "__main__":
    print("SSL Video-to-Text Translation Test Suite")
    print("=" * 50)
    
    # Run synchronous tests
    print("\nRunning synchronous tests...")
    result = run_test_suite()
    
    # Run async tests
    print("\nRunning asynchronous tests...")
    asyncio.run(run_async_tests())
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\\n')[-2]}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    print(f"\nTest suite {'PASSED' if exit_code == 0 else 'FAILED'}")
    exit(exit_code)
