"""
SSL Video-to-Text Translation Model
Hybrid CNN + LSTM/Transformer architecture for spatio-temporal gesture recognition
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
from typing import Dict, Tuple, Optional, List
import math
import numpy as np


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""
    
    def __init__(self, d_model: int, max_len: int = 1000):
        super().__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        return x + self.pe[:x.size(0), :]


class CNNBackbone(nn.Module):
    """CNN backbone for spatial feature extraction"""
    
    def __init__(self, pretrained: bool = True, feature_dim: int = 512):
        super().__init__()
        
        # Use ResNet-18 as backbone (can be changed to ResNet-50 for better performance)
        self.backbone = models.resnet18(pretrained=pretrained)
        
        # Remove the final classification layer
        self.backbone = nn.Sequential(*list(self.backbone.children())[:-1])
        
        # Add custom feature projection
        self.feature_projection = nn.Linear(512, feature_dim)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        # x shape: (batch_size * seq_len, 3, 224, 224)
        features = self.backbone(x)  # (batch_size * seq_len, 512, 1, 1)
        features = features.squeeze(-1).squeeze(-1)  # (batch_size * seq_len, 512)
        features = self.feature_projection(features)  # (batch_size * seq_len, feature_dim)
        features = self.dropout(features)
        return features


class KeypointEncoder(nn.Module):
    """Encode MediaPipe hand keypoints"""
    
    def __init__(self, input_dim: int = 126, hidden_dim: int = 256, output_dim: int = 128):
        super().__init__()
        # Input: 2 hands * 21 keypoints * 3 coordinates = 126
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, output_dim)
        )
        
    def forward(self, keypoints):
        # keypoints shape: (batch_size, seq_len, 2, 21, 3)
        batch_size, seq_len = keypoints.shape[:2]
        
        # Flatten keypoints
        keypoints_flat = keypoints.view(batch_size, seq_len, -1)  # (batch_size, seq_len, 126)
        
        # Encode
        encoded = self.encoder(keypoints_flat)  # (batch_size, seq_len, output_dim)
        return encoded


class LSTMSequenceHead(nn.Module):
    """LSTM-based sequence modeling head"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 256, num_layers: int = 2, num_classes: int = 400):
        super().__init__()
        
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),  # *2 for bidirectional
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, num_classes)
        )
        
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Use the last output for classification
        # Take both directions of the last timestep
        final_output = lstm_out[:, -1, :]  # (batch_size, hidden_dim * 2)
        
        logits = self.classifier(final_output)
        return logits


class TransformerSequenceHead(nn.Module):
    """Transformer-based sequence modeling head"""
    
    def __init__(self, input_dim: int, d_model: int = 512, nhead: int = 8, 
                 num_layers: int = 6, num_classes: int = 400, max_seq_len: int = 100):
        super().__init__()
        
        self.d_model = d_model
        self.input_projection = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=0.1,
            activation='gelu'
        )
        
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # Global average pooling + classification
        self.classifier = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(d_model // 2, num_classes)
        )
        
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        batch_size, seq_len, _ = x.shape
        
        # Project to model dimension
        x = self.input_projection(x)  # (batch_size, seq_len, d_model)
        x = x * math.sqrt(self.d_model)
        
        # Transpose for transformer (seq_len, batch_size, d_model)
        x = x.transpose(0, 1)
        
        # Add positional encoding
        x = self.pos_encoder(x)
        
        # Apply transformer
        transformer_out = self.transformer_encoder(x)  # (seq_len, batch_size, d_model)
        
        # Global average pooling
        pooled = transformer_out.mean(dim=0)  # (batch_size, d_model)
        
        # Classification
        logits = self.classifier(pooled)
        return logits


class SSLTranslationModel(nn.Module):
    """Complete SSL Video-to-Text Translation Model"""
    
    def __init__(
        self,
        num_classes: int = 400,
        cnn_feature_dim: int = 512,
        keypoint_feature_dim: int = 128,
        sequence_model: str = 'lstm',  # 'lstm' or 'transformer'
        pretrained_backbone: bool = True,
        **kwargs
    ):
        super().__init__()
        
        self.num_classes = num_classes
        self.sequence_model_type = sequence_model
        
        # CNN backbone for spatial features
        self.cnn_backbone = CNNBackbone(
            pretrained=pretrained_backbone,
            feature_dim=cnn_feature_dim
        )
        
        # Keypoint encoder
        self.keypoint_encoder = KeypointEncoder(
            input_dim=126,  # 2 hands * 21 keypoints * 3 coordinates
            output_dim=keypoint_feature_dim
        )
        
        # Combined feature dimension
        combined_feature_dim = cnn_feature_dim + keypoint_feature_dim
        
        # Sequence modeling head
        if sequence_model == 'lstm':
            self.sequence_head = LSTMSequenceHead(
                input_dim=combined_feature_dim,
                hidden_dim=kwargs.get('lstm_hidden_dim', 256),
                num_layers=kwargs.get('lstm_num_layers', 2),
                num_classes=num_classes
            )
        elif sequence_model == 'transformer':
            self.sequence_head = TransformerSequenceHead(
                input_dim=combined_feature_dim,
                d_model=kwargs.get('transformer_d_model', 512),
                nhead=kwargs.get('transformer_nhead', 8),
                num_layers=kwargs.get('transformer_num_layers', 6),
                num_classes=num_classes
            )
        else:
            raise ValueError(f"Unknown sequence model: {sequence_model}")
    
    def forward(self, frames: torch.Tensor, keypoints: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass
        
        Args:
            frames: (batch_size, seq_len, 3, 224, 224)
            keypoints: (batch_size, seq_len, 2, 21, 3)
        
        Returns:
            Dict containing logits and features
        """
        batch_size, seq_len = frames.shape[:2]
        
        # Reshape frames for CNN processing
        frames_reshaped = frames.view(batch_size * seq_len, 3, 224, 224)
        
        # Extract CNN features
        cnn_features = self.cnn_backbone(frames_reshaped)  # (batch_size * seq_len, cnn_feature_dim)
        cnn_features = cnn_features.view(batch_size, seq_len, -1)  # (batch_size, seq_len, cnn_feature_dim)
        
        # Extract keypoint features
        keypoint_features = self.keypoint_encoder(keypoints)  # (batch_size, seq_len, keypoint_feature_dim)
        
        # Combine features
        combined_features = torch.cat([cnn_features, keypoint_features], dim=-1)  # (batch_size, seq_len, combined_dim)
        
        # Sequence modeling
        logits = self.sequence_head(combined_features)
        
        return {
            'logits': logits,
            'cnn_features': cnn_features,
            'keypoint_features': keypoint_features,
            'combined_features': combined_features
        }
    
    def get_predictions(self, frames: torch.Tensor, keypoints: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get predictions with confidence scores"""
        outputs = self.forward(frames, keypoints)
        logits = outputs['logits']
        
        probabilities = F.softmax(logits, dim=-1)
        predictions = torch.argmax(probabilities, dim=-1)
        confidence = torch.max(probabilities, dim=-1)[0]
        
        return predictions, confidence


class FewShotLearningWrapper(nn.Module):
    """Wrapper for few-shot learning capabilities"""
    
    def __init__(self, base_model: SSLTranslationModel, support_set_size: int = 5):
        super().__init__()
        self.base_model = base_model
        self.support_set_size = support_set_size
        
        # Meta-learning components
        self.prototype_network = nn.Sequential(
            nn.Linear(base_model.cnn_backbone.feature_projection.out_features + 
                     base_model.keypoint_encoder.encoder[-1].out_features, 256),
            nn.ReLU(),
            nn.Linear(256, 128)
        )
        
    def forward(self, 
                support_frames: torch.Tensor, 
                support_keypoints: torch.Tensor,
                support_labels: torch.Tensor,
                query_frames: torch.Tensor,
                query_keypoints: torch.Tensor) -> torch.Tensor:
        """
        Few-shot learning forward pass
        
        Args:
            support_frames: (n_way, n_shot, seq_len, 3, 224, 224)
            support_keypoints: (n_way, n_shot, seq_len, 2, 21, 3)
            support_labels: (n_way, n_shot)
            query_frames: (n_queries, seq_len, 3, 224, 224)
            query_keypoints: (n_queries, seq_len, 2, 21, 3)
        """
        # Extract features for support set
        n_way, n_shot = support_frames.shape[:2]
        support_frames_flat = support_frames.view(-1, *support_frames.shape[2:])
        support_keypoints_flat = support_keypoints.view(-1, *support_keypoints.shape[2:])
        
        support_outputs = self.base_model(support_frames_flat, support_keypoints_flat)
        support_features = support_outputs['combined_features']
        
        # Create prototypes
        support_features = support_features.view(n_way, n_shot, -1)
        prototypes = support_features.mean(dim=1)  # (n_way, feature_dim)
        
        # Extract features for query set
        query_outputs = self.base_model(query_frames, query_keypoints)
        query_features = query_outputs['combined_features']
        
        # Compute similarities
        query_features_expanded = query_features.unsqueeze(1)  # (n_queries, 1, feature_dim)
        prototypes_expanded = prototypes.unsqueeze(0)  # (1, n_way, feature_dim)
        
        distances = torch.norm(query_features_expanded - prototypes_expanded, dim=-1)  # (n_queries, n_way)
        similarities = -distances  # Convert to similarities
        
        return similarities


def create_ssl_model(
    num_classes: int = 400,
    sequence_model: str = 'lstm',
    pretrained_backbone: bool = True,
    **model_kwargs
) -> SSLTranslationModel:
    """Factory function to create SSL translation model"""
    
    model = SSLTranslationModel(
        num_classes=num_classes,
        sequence_model=sequence_model,
        pretrained_backbone=pretrained_backbone,
        **model_kwargs
    )
    
    return model


if __name__ == "__main__":
    # Test model creation and forward pass
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Create model
    model = create_ssl_model(num_classes=400, sequence_model='lstm')
    model.to(device)
    
    # Test with random data
    batch_size, seq_len = 2, 16
    frames = torch.randn(batch_size, seq_len, 3, 224, 224).to(device)
    keypoints = torch.randn(batch_size, seq_len, 2, 21, 3).to(device)
    
    # Forward pass
    outputs = model(frames, keypoints)
    print(f"Output logits shape: {outputs['logits'].shape}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Test predictions
    predictions, confidence = model.get_predictions(frames, keypoints)
    print(f"Predictions: {predictions}")
    print(f"Confidence: {confidence}")
