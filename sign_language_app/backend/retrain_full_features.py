"""
IMPROVED TRAINING SCRIPT - Using ALL 33 Landmarks (132 Features)
================================================================

This script modifies your original Kaggle training to use ALL columns
from the CSV files instead of just Column 0 (wrist only).

Expected improvement: 67% → 80-85%+ accuracy

CHANGES FROM ORIGINAL:
1. Reads ALL 33 columns (not just column 0)
2. Extracts all [x, y, z, visibility] from each landmark
3. Input shape: (50, 132) instead of (50, 4)
4. Larger model capacity to handle more features
"""

import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import matplotlib.pyplot as plt
import ast
from scipy.interpolate import CubicSpline
import warnings
warnings.filterwarnings('ignore')

# Set seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

print("="*80)
print("  🚀 IMPROVED SSL400 TRAINING - FULL LANDMARK FEATURES")
print("="*80)
print(f"TensorFlow version: {tf.__version__}")
print(f"GPU Available: {tf.config.list_physical_devices('GPU')}")
print("="*80 + "\n")

# ============================================================================
# CONFIGURATION
# ============================================================================
DATASET_PATH = "/kaggle/input/ssl400-dynamic-sri-lankan-sign-language-dataset/Dataset - MP - CSV/"
SEQUENCE_LENGTH = 50
AUGMENTATION_FACTOR = 12
MIN_SAMPLES_PER_CLASS = 3
BATCH_SIZE = 32
EPOCHS = 120
LEARNING_RATE = 1e-4
USE_MIXUP = True
MIXUP_ALPHA = 0.2

# ============================================================================
# ADVANCED DATA AUGMENTATION
# ============================================================================

class SignLanguageAugmentor:
    """Advanced augmentation for sign language landmark sequences"""
    
    @staticmethod
    def time_warp(seq, sigma=0.3):
        """Non-linear time warping using cubic spline interpolation"""
        try:
            n_steps = seq.shape[0]
            if n_steps < 2:
                return seq
            
            time_steps = np.arange(n_steps)
            warp = np.cumsum(np.random.normal(1.0, sigma, n_steps))
            warp = (warp - warp.min()) / (warp.max() - warp.min()) * (n_steps - 1)
            
            warped = np.zeros_like(seq)
            for i in range(seq.shape[1]):
                cs = CubicSpline(time_steps, seq[:, i])
                warped[:, i] = cs(warp)
            
            return warped
        except:
            return seq
    
    @staticmethod
    def rotation_3d(seq, max_angle=15):
        """3D rotation around x, y, z axes"""
        try:
            n_frames = seq.shape[0]
            n_features = seq.shape[1]
            
            # Only rotate XYZ coordinates (not visibility scores)
            # Assuming format: [x1,y1,z1,vis1, x2,y2,z2,vis2, ...]
            # We'll rotate every 4th group of [x,y,z] and skip visibility
            
            if n_features % 4 != 0:
                return seq
            
            n_landmarks = n_features // 4
            rotated_seq = seq.copy()
            
            # Generate rotation angles
            angles = np.random.uniform(-max_angle, max_angle, 3) * np.pi / 180
            
            # Rotation matrices
            Rx = np.array([[1, 0, 0],
                           [0, np.cos(angles[0]), -np.sin(angles[0])],
                           [0, np.sin(angles[0]), np.cos(angles[0])]])
            
            Ry = np.array([[np.cos(angles[1]), 0, np.sin(angles[1])],
                           [0, 1, 0],
                           [-np.sin(angles[1]), 0, np.cos(angles[1])]])
            
            Rz = np.array([[np.cos(angles[2]), -np.sin(angles[2]), 0],
                           [np.sin(angles[2]), np.cos(angles[2]), 0],
                           [0, 0, 1]])
            
            R = Rz @ Ry @ Rx
            
            # Apply rotation to each landmark's XYZ
            for frame_idx in range(n_frames):
                for lm_idx in range(n_landmarks):
                    base_idx = lm_idx * 4
                    xyz = seq[frame_idx, base_idx:base_idx+3]
                    rotated_xyz = R @ xyz
                    rotated_seq[frame_idx, base_idx:base_idx+3] = rotated_xyz
                    # Keep visibility unchanged
            
            return rotated_seq
        except:
            return seq
    
    @staticmethod
    def jitter(seq, sigma=0.03):
        """Add Gaussian noise"""
        noise = np.random.normal(0, sigma, seq.shape)
        return seq + noise
    
    @staticmethod
    def scale(seq, sigma=0.2):
        """Random scaling"""
        scale_factor = np.random.uniform(1 - sigma, 1 + sigma)
        return seq * scale_factor
    
    @staticmethod
    def shift(seq, max_shift=0.1):
        """Random spatial translation"""
        shift = np.random.uniform(-max_shift, max_shift, seq.shape[1])
        return seq + shift
    
    @staticmethod
    def speed_change(seq, speed_range=(0.8, 1.2)):
        """Change signing speed"""
        try:
            speed = np.random.uniform(*speed_range)
            n_frames = seq.shape[0]
            
            if n_frames < 2:
                return seq
            
            old_indices = np.arange(n_frames)
            new_length = max(2, int(n_frames / speed))
            new_indices = np.linspace(0, n_frames - 1, new_length)
            
            resampled = np.zeros((new_length, seq.shape[1]))
            for i in range(seq.shape[1]):
                resampled[:, i] = np.interp(new_indices, old_indices, seq[:, i])
            
            if resampled.shape[0] > SEQUENCE_LENGTH:
                return resampled[:SEQUENCE_LENGTH]
            else:
                pad = np.zeros((SEQUENCE_LENGTH - resampled.shape[0], seq.shape[1]))
                return np.vstack([resampled, pad])
        except:
            return seq
    
    @staticmethod
    def augment(seq, aug_level='medium'):
        """Apply random combination of augmentations"""
        seq = seq.copy()
        
        try:
            if aug_level == 'light':
                seq = SignLanguageAugmentor.jitter(seq, sigma=0.02)
            
            elif aug_level == 'medium':
                if np.random.rand() > 0.5:
                    seq = SignLanguageAugmentor.time_warp(seq, sigma=0.2)
                if np.random.rand() > 0.5:
                    seq = SignLanguageAugmentor.jitter(seq, sigma=0.03)
                if np.random.rand() > 0.5:
                    seq = SignLanguageAugmentor.scale(seq, sigma=0.15)
            
            elif aug_level == 'heavy':
                if np.random.rand() > 0.3:
                    seq = SignLanguageAugmentor.rotation_3d(seq, max_angle=10)
                if np.random.rand() > 0.3:
                    seq = SignLanguageAugmentor.time_warp(seq, sigma=0.3)
                if np.random.rand() > 0.5:
                    seq = SignLanguageAugmentor.jitter(seq, sigma=0.04)
                if np.random.rand() > 0.5:
                    seq = SignLanguageAugmentor.scale(seq, sigma=0.2)
            
            elif aug_level == 'extreme':
                seq = SignLanguageAugmentor.speed_change(seq)
                if np.random.rand() > 0.5:
                    seq = SignLanguageAugmentor.rotation_3d(seq, max_angle=15)
                seq = SignLanguageAugmentor.jitter(seq, sigma=0.05)
        except:
            pass
        
        return np.nan_to_num(seq)

# ============================================================================
# DATA LOADING - MODIFIED TO USE ALL COLUMNS
# ============================================================================

def collect_csv_files_and_labels(base_path):
    csv_paths, labels = [], []
    for category in os.listdir(base_path):
        cat_path = os.path.join(base_path, category)
        if not os.path.isdir(cat_path):
            continue
        for subcat in os.listdir(cat_path):
            subcat_path = os.path.join(cat_path, subcat)
            if not os.path.isdir(subcat_path):
                continue
            for file in os.listdir(subcat_path):
                if file.endswith('.csv'):
                    csv_paths.append(os.path.join(subcat_path, file))
                    labels.append(f"{category}/{subcat}")
    return csv_paths, labels

csv_paths, labels = collect_csv_files_and_labels(DATASET_PATH)
print(f"✓ Found {len(csv_paths)} CSV files")

unique_labels = sorted(list(set(labels)))
NUM_CLASSES = len(unique_labels)
label_map = {label: i for i, label in enumerate(unique_labels)}
print(f"✓ Found {NUM_CLASSES} unique classes")

# Detect format and determine number of features
print("\n🔍 Analyzing CSV format...")
df_first = pd.read_csv(csv_paths[0], header=None)

if isinstance(df_first.iloc[0, 0], str) and df_first.iloc[0, 0].startswith("["):
    # String-list format - Parse ALL columns
    print(f"  ✓ String-list format detected")
    print(f"  ✓ Number of columns (landmarks): {df_first.shape[1]}")
    
    # Parse first row to determine total features
    sample_row_features = []
    for col_idx in range(df_first.shape[1]):
        landmark_data = ast.literal_eval(df_first.iloc[0, col_idx])
        sample_row_features.extend(landmark_data)
    
    NUM_FEATURES = len(sample_row_features)
    NUM_LANDMARKS = df_first.shape[1]
    FEATURES_PER_LANDMARK = len(ast.literal_eval(df_first.iloc[0, 0]))
    
    print(f"  ✓ Features per landmark: {FEATURES_PER_LANDMARK}")
    print(f"  ✓ Total features: {NUM_FEATURES} ({NUM_LANDMARKS} landmarks × {FEATURES_PER_LANDMARK} values)")
else:
    # Normal CSV format
    NUM_FEATURES = df_first.shape[1]
    NUM_LANDMARKS = NUM_FEATURES // 4  # Assuming 4 values per landmark
    print(f"  ✓ Normal CSV: {NUM_FEATURES} features")

print("\n" + "="*80)
print(f"  📊 CRITICAL IMPROVEMENT")
print("="*80)
print(f"  OLD MODEL: Used only Column 0 (1 landmark = 4 features)")
print(f"  NEW MODEL: Using ALL {NUM_LANDMARKS} landmarks = {NUM_FEATURES} features")
print(f"  Improvement Factor: {NUM_FEATURES/4:.1f}x more information!")
print("="*80 + "\n")

# Load with augmentation
augmentor = SignLanguageAugmentor()
aug_levels = ['light', 'light', 'medium', 'medium', 'medium', 'heavy', 'heavy', 'heavy', 'extreme', 'extreme', 'extreme', 'extreme']

X, y = [], []
skipped_count = 0
print("Loading and augmenting data...")

for idx, (csv_file, label) in enumerate(zip(csv_paths, labels)):
    if idx % 500 == 0:
        print(f"  {idx}/{len(csv_paths)} files (samples: {len(X)}, skipped: {skipped_count})")
    
    try:
        df = pd.read_csv(csv_file, header=None)
        
        if isinstance(df.iloc[0, 0], str) and df.iloc[0, 0].startswith("["):
            # ✅ MODIFIED: Parse ALL columns, not just column 0
            all_frames = []
            for row_idx in range(len(df)):
                frame_features = []
                for col_idx in range(df.shape[1]):  # ✅ Loop through ALL columns
                    try:
                        landmark_data = ast.literal_eval(str(df.iloc[row_idx, col_idx]))
                        frame_features.extend(landmark_data)  # Flatten all landmarks into one row
                    except:
                        # If parsing fails, use zeros
                        frame_features.extend([0] * FEATURES_PER_LANDMARK)
                all_frames.append(frame_features)
            arr = np.array(all_frames, dtype='float32')
        else:
            arr = df.to_numpy().astype('float32')
        
        arr = np.nan_to_num(arr)
        
        if arr.ndim != 2 or arr.shape[1] != NUM_FEATURES:
            skipped_count += 1
            continue
        
        # Pad or truncate to SEQUENCE_LENGTH
        if arr.shape[0] > SEQUENCE_LENGTH:
            arr = arr[:SEQUENCE_LENGTH]
        elif arr.shape[0] < SEQUENCE_LENGTH:
            arr = np.pad(arr, ((0, SEQUENCE_LENGTH - arr.shape[0]), (0, 0)), 'constant')
        
        # Add original
        X.append(arr)
        y.append(label_map[label])
        
        # Add augmented versions
        for i in range(AUGMENTATION_FACTOR):
            aug_arr = augmentor.augment(arr, aug_level=aug_levels[i % len(aug_levels)])
            X.append(aug_arr)
            y.append(label_map[label])
    
    except Exception as e:
        skipped_count += 1

X = np.array(X, dtype='float32')
y = np.array(y, dtype='int32')
print(f"\n✓ Total samples: {X.shape[0]} (skipped: {skipped_count})")
print(f"✓ Input shape: {X.shape} (batch, {SEQUENCE_LENGTH} frames, {NUM_FEATURES} features)")

# Filter rare classes
label_counts = np.bincount(y)
ok_labels = np.where(label_counts >= MIN_SAMPLES_PER_CLASS)[0]
print(f"✓ Classes with >={MIN_SAMPLES_PER_CLASS} samples: {len(ok_labels)}/{NUM_CLASSES}")

if len(ok_labels) == 0:
    MIN_SAMPLES_PER_CLASS = 1
    ok_labels = np.where(label_counts >= MIN_SAMPLES_PER_CLASS)[0]

mask = np.isin(y, ok_labels)
X_filtered = X[mask]
y_filtered = y[mask]

label_remapping = {old_label: new_label for new_label, old_label in enumerate(ok_labels)}
y_remapped = np.array([label_remapping[label] for label in y_filtered])
y_cat = to_categorical(y_remapped, num_classes=len(ok_labels))

valid_label_names = [unique_labels[i] for i in ok_labels]
NUM_CLASSES_FILTERED = len(ok_labels)

print(f"✓ Final: {X_filtered.shape[0]} samples, {NUM_CLASSES_FILTERED} classes")

# Split
X_train, X_val, y_train, y_val = train_test_split(
    X_filtered, y_cat, test_size=0.15, random_state=42, stratify=y_remapped
)
print(f"✓ Train: {X_train.shape}, Val: {X_val.shape}\n")

# ============================================================================
# ENHANCED MODEL - ADAPTED FOR MORE FEATURES
# ============================================================================

def build_enhanced_model(input_shape, num_classes):
    """Enhanced model adapted for larger feature count"""
    print(f"Building model for input shape: {input_shape}")
    
    inputs = layers.Input(shape=input_shape)
    
    # Larger dense layer to handle more features
    x = layers.Dense(256)(inputs)  # Increased from 128
    x = layers.LayerNormalization()(x)
    
    # Deeper CNN
    conv1 = layers.Conv1D(256, 5, padding='same', activation='relu')(x)
    conv1 = layers.BatchNormalization()(conv1)
    conv1 = layers.Dropout(0.3)(conv1)
    
    conv2 = layers.Conv1D(512, 3, padding='same', activation='relu')(conv1)  # Increased capacity
    conv2 = layers.BatchNormalization()(conv2)
    conv2 = layers.Dropout(0.3)(conv2)
    
    conv3 = layers.Conv1D(512, 3, padding='same', activation='relu')(conv2)
    conv3 = layers.BatchNormalization()(conv3)
    conv3 = layers.Dropout(0.3)(conv3)
    
    # Multi-head attention
    attention = layers.MultiHeadAttention(num_heads=8, key_dim=64)(conv3, conv3)
    attention = layers.Dropout(0.3)(attention)
    attention = layers.LayerNormalization()(attention + conv3)
    
    # Bidirectional LSTM
    lstm1 = layers.Bidirectional(layers.LSTM(256, return_sequences=True))(attention)
    lstm1 = layers.Dropout(0.4)(lstm1)
    
    lstm2 = layers.Bidirectional(layers.LSTM(128))(lstm1)
    lstm2 = layers.Dropout(0.4)(lstm2)
    
    # Classification head
    dense1 = layers.Dense(512, activation='relu', kernel_regularizer=keras.regularizers.l2(1e-4))(lstm2)
    dense1 = layers.BatchNormalization()(dense1)
    dense1 = layers.Dropout(0.5)(dense1)
    
    dense2 = layers.Dense(256, activation='relu', kernel_regularizer=keras.regularizers.l2(1e-4))(dense1)
    dense2 = layers.Dropout(0.4)(dense2)
    
    dense3 = layers.Dense(128, activation='relu')(dense2)
    dense3 = layers.Dropout(0.3)(dense3)
    
    outputs = layers.Dense(num_classes, activation='softmax')(dense3)
    
    return Model(inputs=inputs, outputs=outputs)

model = build_enhanced_model((SEQUENCE_LENGTH, NUM_FEATURES), NUM_CLASSES_FILTERED)

optimizer = keras.optimizers.AdamW(learning_rate=LEARNING_RATE, weight_decay=1e-4)
loss = keras.losses.CategoricalCrossentropy(label_smoothing=0.1)

model.compile(
    optimizer=optimizer,
    loss=loss,
    metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=min(5, NUM_CLASSES_FILTERED), name='top5_acc')]
)

print("="*80)
model.summary()
print("="*80 + "\n")

# ============================================================================
# TRAINING WITH MIXUP
# ============================================================================

class MixupGenerator(keras.utils.Sequence):
    def __init__(self, X, y, batch_size, alpha=0.2):
        self.X = X
        self.y = y
        self.batch_size = batch_size
        self.alpha = alpha
        self.indexes = np.arange(len(X))
        self.on_epoch_end()
    
    def __len__(self):
        return len(self.X) // self.batch_size
    
    def __getitem__(self, idx):
        batch_indexes = self.indexes[idx * self.batch_size:(idx + 1) * self.batch_size]
        X_batch = self.X[batch_indexes]
        y_batch = self.y[batch_indexes]
        
        if self.alpha > 0:
            lam = np.random.beta(self.alpha, self.alpha, self.batch_size)
            lam = np.maximum(lam, 1 - lam)
            
            shuffle_indexes = np.random.permutation(batch_indexes)
            X_batch2 = self.X[shuffle_indexes]
            y_batch2 = self.y[shuffle_indexes]
            
            X_batch = lam[:, None, None] * X_batch + (1 - lam[:, None, None]) * X_batch2
            y_batch = lam[:, None] * y_batch + (1 - lam[:, None]) * y_batch2
        
        return X_batch, y_batch
    
    def on_epoch_end(self):
        np.random.shuffle(self.indexes)

callbacks = [
    keras.callbacks.EarlyStopping(monitor='val_loss', patience=18, restore_best_weights=True, verbose=1),
    keras.callbacks.ReduceLROnPlateau(monitor='val_accuracy', factor=0.5, patience=8, min_lr=1e-7, verbose=1),
    keras.callbacks.ModelCheckpoint('best_sign_model_full_features.keras', monitor='val_accuracy', save_best_only=True, verbose=1)
]

print("🚀 Training with FULL landmark features...\n")
print(f"  Previous model: (50, 4) - Only wrist")
print(f"  Current model: (50, {NUM_FEATURES}) - All {NUM_LANDMARKS} landmarks")
print(f"  Expected improvement: 67% → 80-85%+\n")

if USE_MIXUP:
    train_gen = MixupGenerator(X_train, y_train, BATCH_SIZE, alpha=MIXUP_ALPHA)
    history = model.fit(train_gen, validation_data=(X_val, y_val), epochs=EPOCHS, callbacks=callbacks, verbose=2)
else:
    history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=EPOCHS, batch_size=BATCH_SIZE, callbacks=callbacks, verbose=2)

# ============================================================================
# EVALUATION
# ============================================================================

model.load_weights('best_sign_model_full_features.keras')

y_pred_probs = model.predict(X_val, verbose=0)
y_pred = np.argmax(y_pred_probs, axis=1)
y_true = np.argmax(y_val, axis=1)

accuracy = accuracy_score(y_true, y_pred)

print(f"\n{'='*80}")
print(f"🎯 FINAL VALIDATION ACCURACY: {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"{'='*80}\n")

# Top-5 accuracy
top5_correct = sum([y_true[i] in np.argsort(y_pred_probs[i])[-5:] for i in range(len(y_true))])
top5_acc = top5_correct / len(y_true)
print(f"📊 Top-5 Accuracy: {top5_acc:.4f} ({top5_acc*100:.2f}%)")

# Classification report
unique_classes_in_val = np.unique(np.concatenate([y_true, y_pred]))
valid_names_in_val = [valid_label_names[i] for i in unique_classes_in_val if i < len(valid_label_names)]

print("\n" + "="*80)
print("📋 CLASSIFICATION REPORT")
print("="*80 + "\n")
print(classification_report(
    y_true, 
    y_pred, 
    labels=unique_classes_in_val.tolist(),
    target_names=valid_names_in_val,
    zero_division=0
))

# Visualizations
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Accuracy plot
axes[0, 0].plot(history.history['accuracy'], label='Train', linewidth=2)
axes[0, 0].plot(history.history['val_accuracy'], label='Validation', linewidth=2)
axes[0, 0].axhline(y=0.6733, color='orange', linestyle='--', label='Old Model (67.33%)', linewidth=1.5)
axes[0, 0].axhline(y=0.80, color='green', linestyle='--', label='Target (80%)', linewidth=1.5)
axes[0, 0].set_title('Accuracy Progression - FULL FEATURES', fontsize=14, fontweight='bold')
axes[0, 0].set_xlabel('Epoch')
axes[0, 0].set_ylabel('Accuracy')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Loss plot
axes[0, 1].plot(history.history['loss'], label='Train', linewidth=2)
axes[0, 1].plot(history.history['val_loss'], label='Validation', linewidth=2)
axes[0, 1].set_title('Loss', fontsize=14, fontweight='bold')
axes[0, 1].set_xlabel('Epoch')
axes[0, 1].set_ylabel('Loss')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Top-5 accuracy
axes[1, 0].plot(history.history['top5_acc'], label='Train Top-5', linewidth=2)
axes[1, 0].plot(history.history['val_top5_acc'], label='Val Top-5', linewidth=2)
axes[1, 0].set_title('Top-5 Accuracy', fontsize=14, fontweight='bold')
axes[1, 0].set_xlabel('Epoch')
axes[1, 0].set_ylabel('Top-5 Accuracy')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Results summary
improvement = ((accuracy - 0.6733) / 0.6733) * 100
result_status = "✅ TARGET MET!" if accuracy >= 0.80 else f"📈 +{improvement:.1f}% improvement"

stats_text = f"""
FINAL RESULTS - FULL FEATURES
{'='*35}
Old Model (4 features):   67.33%
New Model ({NUM_FEATURES} features): {accuracy*100:.2f}%
Improvement:              {improvement:+.2f}%
Top-5 Acc:                {top5_acc*100:.2f}%
Status:                   {result_status}

Features Used:            {NUM_FEATURES}
Landmarks:                {NUM_LANDMARKS}
Classes:                  {NUM_CLASSES_FILTERED}
Train Samples:            {X_train.shape[0]:,}
Val Samples:              {X_val.shape[0]:,}
"""

axes[1, 1].text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
axes[1, 1].axis('off')

plt.tight_layout()
plt.savefig('training_results_full_features.png', dpi=150, bbox_inches='tight')
plt.show()

print("\n" + "="*80)
print("✅ TRAINING COMPLETE!")
print("="*80)
print(f"✅ Model saved: 'best_sign_model_full_features.keras'")
print(f"✅ Old model (4 features):    67.33%")
print(f"✅ New model ({NUM_FEATURES} features): {accuracy*100:.2f}%")
print(f"✅ Improvement:                {improvement:+.2f}%")
print(f"✅ 80% Target:                 {'✅ ACHIEVED!' if accuracy >= 0.80 else '📈 Getting closer!'}")
print("="*80)
print("\n🎯 Next steps:")
print("  1. Download 'best_sign_model_full_features.keras'")
print("  2. Update frontend to extract all landmarks (not just wrist)")
print("  3. Test with the improved model!")
print("="*80)
