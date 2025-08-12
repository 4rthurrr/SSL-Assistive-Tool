"""
Configuration management for SSL Video-to-Text Translation
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ModelConfig:
    """Model configuration"""
    num_classes: int = 384  # Updated for SSL400 dataset (384 classes)
    sequence_model: str = 'lstm'  # 'lstm' or 'transformer'
    sequence_length: int = 60  # Updated for SSL400: 3 seconds × 20 fps = 60 frames
    cnn_feature_dim: int = 512
    keypoint_feature_dim: int = 128
    pretrained_backbone: bool = True
    
    # LSTM specific
    lstm_hidden_dim: int = 256
    lstm_num_layers: int = 2
    
    # Transformer specific
    transformer_d_model: int = 512
    transformer_nhead: int = 8
    transformer_num_layers: int = 6


@dataclass
class TrainingConfig:
    """Training configuration"""
    batch_size: int = 8
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    epochs: int = 100
    optimizer: str = 'adam'  # 'adam' or 'sgd'
    scheduler: str = 'cosine'  # 'cosine', 'step', 'plateau'
    gradient_clip_val: float = 1.0
    label_smoothing: float = 0.1
    
    # Learning rate scheduling
    step_size: int = 30
    gamma: float = 0.1
    patience: int = 10
    factor: float = 0.5
    
    # Transfer learning
    freeze_backbone: bool = False
    pretrained_model_path: Optional[str] = None
    
    # Few-shot learning
    few_shot_enabled: bool = False
    few_shot_support_size: int = 5
    few_shot_episodes: int = 1000


@dataclass
class DataConfig:
    """Data configuration"""
    train_data_path: str = "data/ssl400/train"
    val_data_path: str = "data/ssl400/val"
    test_data_path: str = "data/ssl400/test"
    
    # Data loading
    num_workers: int = 4
    pin_memory: bool = True
    
    # SSL400 specific settings
    video_fps: int = 20  # SSL400 dataset is recorded at 20 FPS
    video_duration: float = 3.0  # SSL400 videos are 3 seconds long
    expected_frames: int = 60  # 20 FPS × 3 seconds = 60 frames
    
    # Data augmentation
    rotation_limit: float = 15.0
    scale_limit: float = 0.1
    noise_var_limit: float = 0.05
    brightness_contrast_limit: float = 0.2
    temporal_jitter_ratio: float = 0.1
    
    # Preprocessing
    target_fps: int = 20  # Match SSL400 dataset FPS
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5


@dataclass
class InferenceConfig:
    """Inference configuration"""
    model_path: str = "models/ssl_translation_best.pth"
    device: str = "auto"  # 'auto', 'cuda', 'cpu'
    batch_size: int = 1
    
    # API settings
    host: str = "0.0.0.0"
    port: int = 8000
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    timeout: float = 30.0
    
    # Performance
    enable_tensorrt: bool = False
    enable_onnx: bool = False
    half_precision: bool = False


@dataclass
class ValidationConfig:
    """Validation configuration"""
    metrics: list = None
    cross_validation_folds: int = 5
    test_batch_size: int = 16
    
    # Real-world testing
    real_world_test_videos: list = None
    unit_test_videos: list = None
    
    # Performance thresholds
    min_accuracy: float = 0.8
    max_wer: float = 0.3
    max_latency_ms: float = 100.0
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = ["top_1_accuracy", "word_error_rate", "latency_ms_per_frame"]
        if self.real_world_test_videos is None:
            self.real_world_test_videos = []
        if self.unit_test_videos is None:
            self.unit_test_videos = []


@dataclass
class SSLTranslationConfig:
    """Complete SSL Translation configuration"""
    model: ModelConfig
    training: TrainingConfig
    data: DataConfig
    inference: InferenceConfig
    validation: ValidationConfig
    
    # Experiment settings
    experiment_name: str = "ssl_translation_v1"
    output_dir: str = "outputs"
    log_level: str = "INFO"
    seed: int = 42
    
    # SSL400 dataset specific
    ssl400_classes: list = None
    ssl400_dataset_type: str = "original"  # "original", "mediapipe_video", or "mediapipe_csv"
    
    def __post_init__(self):
        if self.ssl400_classes is None:
            # SSL400 has 384 classes - will be loaded from actual dataset
            self.ssl400_classes = [f"ssl_class_{i:03d}" for i in range(384)]


def create_default_config() -> SSLTranslationConfig:
    """Create default configuration"""
    return SSLTranslationConfig(
        model=ModelConfig(),
        training=TrainingConfig(),
        data=DataConfig(),
        inference=InferenceConfig(),
        validation=ValidationConfig()
    )


def save_config(config: SSLTranslationConfig, file_path: str) -> None:
    """Save configuration to JSON file"""
    config_dict = asdict(config)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(config_dict, f, indent=2)


def load_config(file_path: str) -> SSLTranslationConfig:
    """Load configuration from JSON file"""
    with open(file_path, 'r') as f:
        config_dict = json.load(f)
    
    # Convert nested dictionaries back to dataclasses
    model_config = ModelConfig(**config_dict['model'])
    training_config = TrainingConfig(**config_dict['training'])
    data_config = DataConfig(**config_dict['data'])
    inference_config = InferenceConfig(**config_dict['inference'])
    validation_config = ValidationConfig(**config_dict['validation'])
    
    # Remove nested configs from main dict
    for key in ['model', 'training', 'data', 'inference', 'validation']:
        config_dict.pop(key)
    
    return SSLTranslationConfig(
        model=model_config,
        training=training_config,
        data=data_config,
        inference=inference_config,
        validation=validation_config,
        **config_dict
    )


def update_config_from_args(config: SSLTranslationConfig, args: dict) -> SSLTranslationConfig:
    """Update configuration with command line arguments"""
    
    # Update model config
    if 'num_classes' in args:
        config.model.num_classes = args['num_classes']
    if 'sequence_model' in args:
        config.model.sequence_model = args['sequence_model']
    if 'sequence_length' in args:
        config.model.sequence_length = args['sequence_length']
    
    # Update training config
    if 'batch_size' in args:
        config.training.batch_size = args['batch_size']
    if 'learning_rate' in args:
        config.training.learning_rate = args['learning_rate']
    if 'epochs' in args:
        config.training.epochs = args['epochs']
    if 'optimizer' in args:
        config.training.optimizer = args['optimizer']
    
    # Update data config
    if 'train_data_path' in args:
        config.data.train_data_path = args['train_data_path']
    if 'val_data_path' in args:
        config.data.val_data_path = args['val_data_path']
    if 'num_workers' in args:
        config.data.num_workers = args['num_workers']
    
    # Update inference config
    if 'model_path' in args:
        config.inference.model_path = args['model_path']
    if 'port' in args:
        config.inference.port = args['port']
    
    # Update experiment name
    if 'experiment_name' in args:
        config.experiment_name = args['experiment_name']
    
    return config


# SSL400 Class Names (example - replace with actual class names)
SSL400_CLASSES = [
    # Basic greetings and common words
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
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    
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
    "big", "small", "tall", "short", "fat", "thin", "old", "young", "new", "old_thing",
    "beautiful", "ugly", "clean", "dirty", "expensive", "cheap", "easy", "difficult",
    
    # Questions words
    "what", "where", "when", "who", "why", "how", "which",
    
    # Pronouns
    "I", "you", "he", "she", "we", "they", "this", "that", "here", "there",
    
    # Additional common signs to reach 400
    # (This would continue with more specific SSL vocabulary)
] + [f"ssl_gesture_{i:03d}" for i in range(200, 400)]  # Placeholder for remaining classes


if __name__ == "__main__":
    # Example usage
    config = create_default_config()
    
    # Update with SSL400 classes
    config.ssl400_classes = SSL400_CLASSES[:400]  # Ensure exactly 400 classes
    config.model.num_classes = len(config.ssl400_classes)
    
    # Save example config
    save_config(config, "configs/default_config.json")
    print("Default configuration saved to configs/default_config.json")
    
    # Load and verify
    loaded_config = load_config("configs/default_config.json")
    print(f"Loaded config with {loaded_config.model.num_classes} classes")
    print(f"Experiment name: {loaded_config.experiment_name}")
    print(f"Model type: {loaded_config.model.sequence_model}")
    print(f"Training epochs: {loaded_config.training.epochs}")
