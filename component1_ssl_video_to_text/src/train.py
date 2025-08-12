"""
SSL Video-to-Text Training Script
Implements transfer learning and few-shot learning protocols
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse
from tqdm import tqdm
import logging
from sklearn.metrics import accuracy_score, classification_report

from model import create_ssl_model, FewShotLearningWrapper
from data_loader import create_ssl_dataloader, SSL400Dataset


class SSLTrainer:
    """SSL Video-to-Text Translation Trainer"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Setup logging
        self.setup_logging()
        
        # Create model
        self.model = self.create_model()
        self.model.to(self.device)
        
        # Setup loss and optimizer
        self.criterion = nn.CrossEntropyLoss(label_smoothing=config.get('label_smoothing', 0.1))
        self.optimizer = self.setup_optimizer()
        self.scheduler = self.setup_scheduler()
        
        # Metrics tracking
        self.best_accuracy = 0.0
        self.train_losses = []
        self.val_accuracies = []
        
        # TensorBoard
        self.writer = SummaryWriter(log_dir=f"runs/{config['experiment_name']}")
        
        # Few-shot learning
        if config.get('few_shot_enabled', False):
            self.few_shot_wrapper = FewShotLearningWrapper(
                self.model, 
                support_set_size=config.get('few_shot_support_size', 5)
            )
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{self.config['experiment_name']}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_model(self) -> nn.Module:
        """Create and initialize model"""
        model = create_ssl_model(
            num_classes=self.config['num_classes'],
            sequence_model=self.config['sequence_model'],
            pretrained_backbone=self.config['pretrained_backbone'],
            **self.config.get('model_params', {})
        )
        
        # Load pretrained weights if specified
        if self.config.get('pretrained_model_path'):
            self.load_pretrained_weights(model, self.config['pretrained_model_path'])
        
        return model
    
    def load_pretrained_weights(self, model: nn.Module, pretrained_path: str):
        """Load pretrained weights for transfer learning"""
        self.logger.info(f"Loading pretrained weights from {pretrained_path}")
        
        try:
            checkpoint = torch.load(pretrained_path, map_location=self.device)
            
            # Handle different checkpoint formats
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            else:
                state_dict = checkpoint
            
            # Filter out classifier weights if num_classes changed
            if self.config.get('freeze_backbone', False):
                # Freeze CNN backbone
                for name, param in model.cnn_backbone.named_parameters():
                    param.requires_grad = False
                    
            model_dict = model.state_dict()
            filtered_dict = {}
            
            for k, v in state_dict.items():
                if k in model_dict and model_dict[k].shape == v.shape:
                    filtered_dict[k] = v
                else:
                    self.logger.warning(f"Skipping layer {k} due to size mismatch")
            
            model_dict.update(filtered_dict)
            model.load_state_dict(model_dict)
            
            self.logger.info(f"Loaded {len(filtered_dict)} layers from pretrained model")
            
        except Exception as e:
            self.logger.error(f"Failed to load pretrained weights: {e}")
    
    def setup_optimizer(self) -> torch.optim.Optimizer:
        """Setup optimizer with different learning rates for different parts"""
        backbone_params = []
        other_params = []
        
        for name, param in self.model.named_parameters():
            if 'cnn_backbone' in name and self.config.get('freeze_backbone', False):
                continue  # Skip frozen parameters
            elif 'cnn_backbone' in name:
                backbone_params.append(param)
            else:
                other_params.append(param)
        
        param_groups = [
            {'params': backbone_params, 'lr': self.config['learning_rate'] * 0.1},  # Lower LR for backbone
            {'params': other_params, 'lr': self.config['learning_rate']}
        ]
        
        if self.config['optimizer'] == 'adam':
            return optim.Adam(param_groups, weight_decay=self.config.get('weight_decay', 1e-4))
        elif self.config['optimizer'] == 'sgd':
            return optim.SGD(
                param_groups, 
                momentum=self.config.get('momentum', 0.9),
                weight_decay=self.config.get('weight_decay', 1e-4)
            )
        else:
            raise ValueError(f"Unknown optimizer: {self.config['optimizer']}")
    
    def setup_scheduler(self) -> torch.optim.lr_scheduler._LRScheduler:
        """Setup learning rate scheduler"""
        if self.config['scheduler'] == 'cosine':
            return optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, 
                T_max=self.config['epochs']
            )
        elif self.config['scheduler'] == 'step':
            return optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=self.config.get('step_size', 30),
                gamma=self.config.get('gamma', 0.1)
            )
        elif self.config['scheduler'] == 'plateau':
            return optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                mode='max',
                patience=self.config.get('patience', 10),
                factor=self.config.get('factor', 0.5)
            )
        else:
            return optim.lr_scheduler.StepLR(self.optimizer, step_size=1000, gamma=1.0)  # No scheduling
    
    def train_epoch(self, train_loader: DataLoader, epoch: int) -> float:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0
        num_batches = len(train_loader)
        
        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch}")
        
        for batch_idx, batch in enumerate(progress_bar):
            frames = batch['frames'].to(self.device)
            keypoints = batch['keypoints'].to(self.device)
            labels = batch['label'].to(self.device)
            
            # Zero gradients
            self.optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(frames, keypoints)
            loss = self.criterion(outputs['logits'], labels)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            if self.config.get('gradient_clip_val', 0) > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), 
                    self.config['gradient_clip_val']
                )
            
            self.optimizer.step()
            
            total_loss += loss.item()
            
            # Update progress bar
            progress_bar.set_postfix({
                'Loss': f"{loss.item():.4f}",
                'Avg Loss': f"{total_loss / (batch_idx + 1):.4f}"
            })
            
            # Log to tensorboard
            global_step = epoch * num_batches + batch_idx
            self.writer.add_scalar('Train/Loss', loss.item(), global_step)
        
        avg_loss = total_loss / num_batches
        return avg_loss
    
    def validate(self, val_loader: DataLoader) -> Tuple[float, float]:
        """Validate model"""
        self.model.eval()
        total_loss = 0.0
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validating"):
                frames = batch['frames'].to(self.device)
                keypoints = batch['keypoints'].to(self.device)
                labels = batch['label'].to(self.device)
                
                outputs = self.model(frames, keypoints)
                loss = self.criterion(outputs['logits'], labels)
                
                total_loss += loss.item()
                
                predictions = torch.argmax(outputs['logits'], dim=-1)
                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        avg_loss = total_loss / len(val_loader)
        accuracy = accuracy_score(all_labels, all_predictions)
        
        return avg_loss, accuracy
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader):
        """Main training loop"""
        self.logger.info("Starting training...")
        self.logger.info(f"Device: {self.device}")
        self.logger.info(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        
        for epoch in range(self.config['epochs']):
            # Training
            train_loss = self.train_epoch(train_loader, epoch)
            self.train_losses.append(train_loss)
            
            # Validation
            val_loss, val_accuracy = self.validate(val_loader)
            self.val_accuracies.append(val_accuracy)
            
            # Learning rate scheduling
            if isinstance(self.scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                self.scheduler.step(val_accuracy)
            else:
                self.scheduler.step()
            
            # Logging
            self.logger.info(
                f"Epoch {epoch}: Train Loss: {train_loss:.4f}, "
                f"Val Loss: {val_loss:.4f}, Val Accuracy: {val_accuracy:.4f}"
            )
            
            # TensorBoard logging
            self.writer.add_scalar('Train/Epoch_Loss', train_loss, epoch)
            self.writer.add_scalar('Val/Loss', val_loss, epoch)
            self.writer.add_scalar('Val/Accuracy', val_accuracy, epoch)
            self.writer.add_scalar('LR', self.optimizer.param_groups[0]['lr'], epoch)
            
            # Save best model
            if val_accuracy > self.best_accuracy:
                self.best_accuracy = val_accuracy
                self.save_checkpoint(epoch, val_accuracy, is_best=True)
                self.logger.info(f"New best accuracy: {val_accuracy:.4f}")
            
            # Save regular checkpoint
            if (epoch + 1) % self.config.get('save_frequency', 10) == 0:
                self.save_checkpoint(epoch, val_accuracy)
        
        self.logger.info(f"Training completed. Best accuracy: {self.best_accuracy:.4f}")
    
    def save_checkpoint(self, epoch: int, accuracy: float, is_best: bool = False):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'accuracy': accuracy,
            'config': self.config,
            'train_losses': self.train_losses,
            'val_accuracies': self.val_accuracies
        }
        
        # Save regular checkpoint
        checkpoint_path = f"checkpoints/{self.config['experiment_name']}_epoch_{epoch}.pth"
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        torch.save(checkpoint, checkpoint_path)
        
        # Save best checkpoint
        if is_best:
            best_path = f"checkpoints/{self.config['experiment_name']}_best.pth"
            torch.save(checkpoint, best_path)
    
    def few_shot_training(self, support_loader: DataLoader, query_loader: DataLoader, n_way: int = 5):
        """Few-shot learning training"""
        if not hasattr(self, 'few_shot_wrapper'):
            raise ValueError("Few-shot learning not enabled in config")
        
        self.few_shot_wrapper.train()
        
        # Meta-learning optimizer
        meta_optimizer = optim.Adam(self.few_shot_wrapper.parameters(), lr=0.001)
        
        for episode in range(self.config.get('few_shot_episodes', 1000)):
            meta_optimizer.zero_grad()
            
            # Sample support and query sets
            support_batch = next(iter(support_loader))
            query_batch = next(iter(query_loader))
            
            # Prepare data
            support_frames = support_batch['frames'][:n_way].to(self.device)
            support_keypoints = support_batch['keypoints'][:n_way].to(self.device)
            support_labels = support_batch['label'][:n_way].to(self.device)
            
            query_frames = query_batch['frames'].to(self.device)
            query_keypoints = query_batch['keypoints'].to(self.device)
            query_labels = query_batch['label'].to(self.device)
            
            # Forward pass
            similarities = self.few_shot_wrapper(
                support_frames.unsqueeze(1),  # Add shot dimension
                support_keypoints.unsqueeze(1),
                support_labels,
                query_frames,
                query_keypoints
            )
            
            # Compute loss
            loss = self.criterion(similarities, query_labels)
            
            # Backward pass
            loss.backward()
            meta_optimizer.step()
            
            if episode % 100 == 0:
                self.logger.info(f"Few-shot episode {episode}: Loss: {loss.item():.4f}")


def create_training_config(args) -> Dict:
    """Create training configuration from arguments"""
    return {
        'experiment_name': args.experiment_name,
        'num_classes': args.num_classes,
        'sequence_model': args.sequence_model,
        'pretrained_backbone': args.pretrained_backbone,
        'pretrained_model_path': args.pretrained_model_path,
        'freeze_backbone': args.freeze_backbone,
        'batch_size': args.batch_size,
        'sequence_length': args.sequence_length,
        'learning_rate': args.learning_rate,
        'weight_decay': args.weight_decay,
        'epochs': args.epochs,
        'optimizer': args.optimizer,
        'scheduler': args.scheduler,
        'gradient_clip_val': args.gradient_clip_val,
        'label_smoothing': args.label_smoothing,
        'few_shot_enabled': args.few_shot_enabled,
        'few_shot_support_size': args.few_shot_support_size,
        'model_params': {
            'lstm_hidden_dim': args.lstm_hidden_dim,
            'lstm_num_layers': args.lstm_num_layers,
            'transformer_d_model': args.transformer_d_model,
            'transformer_nhead': args.transformer_nhead,
            'transformer_num_layers': args.transformer_num_layers
        }
    }


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description='SSL Video-to-Text Training')
    
    # Model parameters
    parser.add_argument('--experiment_name', type=str, default='ssl_translation_v1')
    parser.add_argument('--num_classes', type=int, default=400)
    parser.add_argument('--sequence_model', type=str, choices=['lstm', 'transformer'], default='lstm')
    parser.add_argument('--pretrained_backbone', action='store_true', default=True)
    parser.add_argument('--pretrained_model_path', type=str, default=None)
    parser.add_argument('--freeze_backbone', action='store_true', default=False)
    
    # Training parameters
    parser.add_argument('--batch_size', type=int, default=8)
    parser.add_argument('--sequence_length', type=int, default=32)
    parser.add_argument('--learning_rate', type=float, default=1e-3)
    parser.add_argument('--weight_decay', type=float, default=1e-4)
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--optimizer', type=str, choices=['adam', 'sgd'], default='adam')
    parser.add_argument('--scheduler', type=str, choices=['cosine', 'step', 'plateau'], default='cosine')
    parser.add_argument('--gradient_clip_val', type=float, default=1.0)
    parser.add_argument('--label_smoothing', type=float, default=0.1)
    
    # Few-shot learning
    parser.add_argument('--few_shot_enabled', action='store_true', default=False)
    parser.add_argument('--few_shot_support_size', type=int, default=5)
    
    # Model-specific parameters
    parser.add_argument('--lstm_hidden_dim', type=int, default=256)
    parser.add_argument('--lstm_num_layers', type=int, default=2)
    parser.add_argument('--transformer_d_model', type=int, default=512)
    parser.add_argument('--transformer_nhead', type=int, default=8)
    parser.add_argument('--transformer_num_layers', type=int, default=6)
    
    # Data parameters
    parser.add_argument('--train_data_path', type=str, required=True)
    parser.add_argument('--val_data_path', type=str, required=True)
    parser.add_argument('--num_workers', type=int, default=4)
    
    args = parser.parse_args()
    
    # Create configuration
    config = create_training_config(args)
    
    # Load data (placeholder - implement based on your data format)
    # You'll need to implement load_ssl_data function based on your data structure
    # train_video_paths, train_labels = load_ssl_data(args.train_data_path)
    # val_video_paths, val_labels = load_ssl_data(args.val_data_path)
    
    # Example placeholder data loading
    train_video_paths = []  # Load your training video paths
    train_labels = []       # Load corresponding labels
    val_video_paths = []    # Load validation video paths  
    val_labels = []         # Load corresponding labels
    
    # Create data loaders
    train_loader = create_ssl_dataloader(
        train_video_paths, 
        train_labels,
        batch_size=args.batch_size,
        sequence_length=args.sequence_length,
        is_training=True,
        num_workers=args.num_workers
    )
    
    val_loader = create_ssl_dataloader(
        val_video_paths,
        val_labels, 
        batch_size=args.batch_size,
        sequence_length=args.sequence_length,
        is_training=False,
        num_workers=args.num_workers
    )
    
    # Create trainer and start training
    trainer = SSLTrainer(config)
    trainer.train(train_loader, val_loader)


if __name__ == "__main__":
    main()
