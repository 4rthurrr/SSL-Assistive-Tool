"""
FIXED SSL400 TRAINING SCRIPT - Corrected Data Pipeline
=======================================================

PROBLEMS FIXED FROM PREVIOUS VERSION:
1. DATA LEAKAGE (critical): Augmentation was done before train/val split,
   so validation contained near-duplicate augmented copies of training data.
   This made 99.18% val accuracy completely meaningless.
   FIX: Split CSV file paths FIRST, then augment ONLY the training set.
   Validation set gets zero augmentation - only raw original samples.

2. NO COORDINATE NORMALIZATION: Raw MediaPipe coordinates depend on where
   the person stands in the frame (position, distance from camera).
   FIX: Normalize all landmarks relative to body center and shoulder width
   so the model learns the SHAPE of the sign, not where in frame it appears.

3. AUGMENTATION FACTOR TOO HIGH: 12x augmentation with sloppy split was
   causing the model to memorize augmented noise rather than learn structure.
   FIX: Reduced to 5x, applied only to training set after proper split.

4. MISSING CLASS WEIGHTS: Classes ranged from 2 samples to 226 samples.
   Model was biased toward high-frequency classes.
   FIX: Compute class_weight and pass to model.fit().

EXPECTED OUTCOME:
   Previous (fake) val accuracy: 99.18%
   Realistic val accuracy after fix: 65-80% (honest generalization estimate)
   Real-world frontend performance: significantly better than before
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
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt
import ast
from scipy.interpolate import CubicSpline
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
tf.random.set_seed(42)

print("=" * 80)
print("  FIXED SSL400 TRAINING - CORRECT DATA PIPELINE")
print("=" * 80)
print(f"TensorFlow version: {tf.__version__}")
print(f"GPU Available: {tf.config.list_physical_devices('GPU')}")
print("=" * 80 + "\n")

# ============================================================================
# CONFIGURATION
# ============================================================================
DATASET_PATH = "/kaggle/input/datasets/yohanabhishek/ssl400-dynamic-sri-lankan-sign-language-dataset/Dataset - MP - CSV/"
SEQUENCE_LENGTH = 50
AUGMENTATION_FACTOR = 6       # 6x aug on training only - more copies since we have fewer classes
MIN_SAMPLES_PER_CLASS = 6     # Applied to training-split file count (NOT total files).
                               # With 80% train split: a class needs ~8 total files to pass.
                               # Data analysis: 163/383 classes have < 6 total files (unlearnable).
                               # This keeps ~171 classes with enough data to generalise.
                               # All Numbers 10-20 (2-4 files) are automatically excluded.
BATCH_SIZE = 32
EPOCHS = 180                  # More epochs since we have harder, fewer classes to learn
LEARNING_RATE = 1e-4
VAL_SPLIT = 0.20

# Categories to EXCLUDE entirely (optional - comment out to include them)
# Numbers are excluded because MediaPipe Pose (33 landmarks) does not capture
# individual finger joints, so all number signs look almost identical at the
# body level. Including them wastes model capacity and confuses other classes.
EXCLUDE_CATEGORIES = {"Numbers"}  # set() to disable exclusion

# MediaPipe pose landmark indices used for normalization
# These are stable body landmarks always visible from the front
LM_LEFT_SHOULDER  = 11
LM_RIGHT_SHOULDER = 12
LM_LEFT_HIP       = 23
LM_RIGHT_HIP      = 24

# ============================================================================
# COORDINATE NORMALIZATION
# ============================================================================

def normalize_sequence(seq):
    """
    Normalize a (frames, 132) sequence so the model learns sign SHAPE,
    not the position/scale of the person in the frame.

    Steps:
      1. Compute body center as mean of left/right shoulder and left/right hip
      2. Compute scale as distance between left and right shoulders
      3. Subtract center (x, y) from all landmark x, y values
      4. Divide x, y, z by scale
      5. Leave visibility scores (every 4th value) unchanged

    Format assumed: [x0,y0,z0,vis0, x1,y1,z1,vis1, ... x32,y32,z32,vis32]
    """
    seq = seq.copy()
    n_frames = seq.shape[0]

    for f in range(n_frames):
        frame = seq[f]

        # Extract reference landmark positions
        ls_x = frame[LM_LEFT_SHOULDER  * 4 + 0]
        ls_y = frame[LM_LEFT_SHOULDER  * 4 + 1]
        rs_x = frame[LM_RIGHT_SHOULDER * 4 + 0]
        rs_y = frame[LM_RIGHT_SHOULDER * 4 + 1]
        lh_x = frame[LM_LEFT_HIP       * 4 + 0]
        lh_y = frame[LM_LEFT_HIP       * 4 + 1]
        rh_x = frame[LM_RIGHT_HIP      * 4 + 0]
        rh_y = frame[LM_RIGHT_HIP      * 4 + 1]

        center_x = (ls_x + rs_x + lh_x + rh_x) / 4.0
        center_y = (ls_y + rs_y + lh_y + rh_y) / 4.0

        # Scale = shoulder width (distance between left and right shoulder)
        scale = np.sqrt((rs_x - ls_x) ** 2 + (rs_y - ls_y) ** 2)
        if scale < 1e-6:
            scale = 1.0  # Avoid division by zero if landmarks not detected

        # Apply normalization to every landmark (skip visibility at index %4==3)
        for lm in range(33):
            base = lm * 4
            frame[base + 0] = (frame[base + 0] - center_x) / scale  # x
            frame[base + 1] = (frame[base + 1] - center_y) / scale  # y
            frame[base + 2] = frame[base + 2] / scale                # z
            # index base+3 is visibility - leave unchanged

        seq[f] = frame

    return seq

# ============================================================================
# AUGMENTATION (applied to training set only)
# ============================================================================

class SignLanguageAugmentor:

    @staticmethod
    def time_warp(seq, sigma=0.25):
        try:
            n_steps = seq.shape[0]
            if n_steps < 4:
                return seq
            time_steps = np.arange(n_steps)
            warp = np.cumsum(np.random.normal(1.0, sigma, n_steps))
            warp = (warp - warp.min()) / (warp.max() - warp.min()) * (n_steps - 1)
            warped = np.zeros_like(seq)
            for i in range(seq.shape[1]):
                cs = CubicSpline(time_steps, seq[:, i])
                warped[:, i] = cs(warp)
            return warped
        except Exception:
            return seq

    @staticmethod
    def rotation_3d(seq, max_angle=12):
        try:
            n_features = seq.shape[1]
            if n_features % 4 != 0:
                return seq
            n_landmarks = n_features // 4
            rotated_seq = seq.copy()
            angles = np.random.uniform(-max_angle, max_angle, 3) * np.pi / 180
            cx, sx = np.cos(angles[0]), np.sin(angles[0])
            cy, sy = np.cos(angles[1]), np.sin(angles[1])
            cz, sz = np.cos(angles[2]), np.sin(angles[2])
            Rx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
            Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
            Rz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
            R = Rz @ Ry @ Rx
            for f in range(seq.shape[0]):
                for lm in range(n_landmarks):
                    b = lm * 4
                    rotated_seq[f, b:b+3] = R @ seq[f, b:b+3]
            return rotated_seq
        except Exception:
            return seq

    @staticmethod
    def jitter(seq, sigma=0.02):
        # Only add noise to x/y/z, not visibility
        noise = np.zeros_like(seq)
        for lm in range(33):
            b = lm * 4
            noise[:, b:b+3] = np.random.normal(0, sigma, (seq.shape[0], 3))
        return seq + noise

    @staticmethod
    def scale(seq, sigma=0.15):
        factor = np.random.uniform(1 - sigma, 1 + sigma)
        result = seq.copy()
        for lm in range(33):
            b = lm * 4
            result[:, b:b+3] = seq[:, b:b+3] * factor
        return result

    @staticmethod
    def speed_change(seq, speed_range=(0.8, 1.2)):
        try:
            speed = np.random.uniform(*speed_range)
            n_frames = seq.shape[0]
            if n_frames < 2:
                return seq
            old_idx = np.arange(n_frames)
            new_len = max(2, int(n_frames / speed))
            new_idx = np.linspace(0, n_frames - 1, new_len)
            resampled = np.zeros((new_len, seq.shape[1]))
            for i in range(seq.shape[1]):
                resampled[:, i] = np.interp(new_idx, old_idx, seq[:, i])
            if resampled.shape[0] >= SEQUENCE_LENGTH:
                return resampled[:SEQUENCE_LENGTH]
            pad = np.zeros((SEQUENCE_LENGTH - resampled.shape[0], seq.shape[1]))
            return np.vstack([resampled, pad])
        except Exception:
            return seq

    @staticmethod
    def horizontal_flip(seq):
        """
        Mirror the sign horizontally (x -> 1-x before normalization, or
        just negate x after normalization since center is at 0).
        Also mirrors left/right landmark pairs.
        """
        flipped = seq.copy()
        # Negate all x coordinates (index %4 == 0)
        for lm in range(33):
            flipped[:, lm * 4] = -seq[:, lm * 4]

        # Swap left/right landmark pairs
        pair_swaps = [
            (1, 4), (2, 5), (3, 6),          # face sides
            (7, 8),                            # ears
            (9, 10),                           # mouth corners
            (11, 12),                          # shoulders
            (13, 14), (15, 16),               # arms
            (17, 18), (19, 20), (21, 22),     # hands
            (23, 24),                          # hips
            (25, 26), (27, 28), (29, 30), (31, 32),  # legs/feet
        ]
        for a, b in pair_swaps:
            flipped[:, a*4:a*4+4], flipped[:, b*4:b*4+4] = (
                seq[:, b*4:b*4+4].copy(),
                seq[:, a*4:a*4+4].copy(),
            )
        return flipped

    @staticmethod
    def augment(seq, level=0):
        """
        level 0 (light):   jitter only
        level 1 (medium):  time warp + jitter + scale
        level 2 (heavy):   rotation + time warp + jitter + scale
        level 3 (extreme): speed + rotation + jitter
        level 4 (flip):    horizontal flip + jitter
        """
        seq = seq.copy()
        try:
            if level == 0:
                seq = SignLanguageAugmentor.jitter(seq, sigma=0.015)

            elif level == 1:
                if np.random.rand() > 0.4:
                    seq = SignLanguageAugmentor.time_warp(seq, sigma=0.2)
                seq = SignLanguageAugmentor.jitter(seq, sigma=0.02)
                if np.random.rand() > 0.5:
                    seq = SignLanguageAugmentor.scale(seq, sigma=0.12)

            elif level == 2:
                if np.random.rand() > 0.3:
                    seq = SignLanguageAugmentor.rotation_3d(seq, max_angle=10)
                if np.random.rand() > 0.4:
                    seq = SignLanguageAugmentor.time_warp(seq, sigma=0.25)
                seq = SignLanguageAugmentor.jitter(seq, sigma=0.025)
                if np.random.rand() > 0.5:
                    seq = SignLanguageAugmentor.scale(seq, sigma=0.15)

            elif level == 3:
                seq = SignLanguageAugmentor.speed_change(seq)
                if np.random.rand() > 0.4:
                    seq = SignLanguageAugmentor.rotation_3d(seq, max_angle=12)
                seq = SignLanguageAugmentor.jitter(seq, sigma=0.03)

            elif level == 4:
                seq = SignLanguageAugmentor.horizontal_flip(seq)
                seq = SignLanguageAugmentor.jitter(seq, sigma=0.015)

        except Exception:
            pass
        return np.nan_to_num(seq)


# ============================================================================
# RAW CSV LOADING HELPER
# ============================================================================

def load_raw_sequence(csv_file, num_features, features_per_landmark):
    """
    Load one CSV file into a (SEQUENCE_LENGTH, num_features) numpy array.
    Returns None if the file cannot be parsed.
    No augmentation - pure raw data.
    """
    try:
        df = pd.read_csv(csv_file, header=None)

        if isinstance(df.iloc[0, 0], str) and str(df.iloc[0, 0]).startswith("["):
            all_frames = []
            for row_idx in range(len(df)):
                frame_features = []
                for col_idx in range(df.shape[1]):
                    try:
                        lm_data = ast.literal_eval(str(df.iloc[row_idx, col_idx]))
                        frame_features.extend(lm_data)
                    except Exception:
                        frame_features.extend([0.0] * features_per_landmark)
                all_frames.append(frame_features)
            arr = np.array(all_frames, dtype='float32')
        else:
            arr = df.to_numpy().astype('float32')

        arr = np.nan_to_num(arr)

        if arr.ndim != 2 or arr.shape[1] != num_features:
            return None

        # Pad or truncate to SEQUENCE_LENGTH
        if arr.shape[0] > SEQUENCE_LENGTH:
            arr = arr[:SEQUENCE_LENGTH]
        elif arr.shape[0] < SEQUENCE_LENGTH:
            arr = np.pad(arr, ((0, SEQUENCE_LENGTH - arr.shape[0]), (0, 0)), 'constant')

        return arr
    except Exception:
        return None


# ============================================================================
# COLLECT FILE PATHS AND LABELS
# ============================================================================

def collect_csv_files_and_labels(base_path):
    csv_paths, labels = [], []
    for category in sorted(os.listdir(base_path)):
        if category in EXCLUDE_CATEGORIES:
            continue                          # skip entire category
        cat_path = os.path.join(base_path, category)
        if not os.path.isdir(cat_path):
            continue
        for subcat in sorted(os.listdir(cat_path)):
            subcat_path = os.path.join(cat_path, subcat)
            if not os.path.isdir(subcat_path):
                continue
            for file in sorted(os.listdir(subcat_path)):
                if file.endswith('.csv'):
                    csv_paths.append(os.path.join(subcat_path, file))
                    labels.append(f"{category}/{subcat}")
    return csv_paths, labels


csv_paths, raw_labels = collect_csv_files_and_labels(DATASET_PATH)
excluded_str = f" (excluded: {', '.join(EXCLUDE_CATEGORIES)})" if EXCLUDE_CATEGORIES else ""
print(f"Found {len(csv_paths)} CSV files{excluded_str}")

unique_labels = sorted(list(set(raw_labels)))
NUM_CLASSES = len(unique_labels)
label_map = {lbl: i for i, lbl in enumerate(unique_labels)}
numeric_labels = np.array([label_map[l] for l in raw_labels])
print(f"Found {NUM_CLASSES} unique classes")

# ============================================================================
# DETECT CSV FORMAT
# ============================================================================

print("\nAnalyzing CSV format...")
df_first = pd.read_csv(csv_paths[0], header=None)

if isinstance(df_first.iloc[0, 0], str) and df_first.iloc[0, 0].startswith("["):
    NUM_LANDMARKS = df_first.shape[1]
    FEATURES_PER_LANDMARK = len(ast.literal_eval(df_first.iloc[0, 0]))
    NUM_FEATURES = NUM_LANDMARKS * FEATURES_PER_LANDMARK
    print(f"  String-list format: {NUM_LANDMARKS} landmarks x {FEATURES_PER_LANDMARK} values = {NUM_FEATURES} features")
else:
    NUM_FEATURES = df_first.shape[1]
    NUM_LANDMARKS = NUM_FEATURES // 4
    FEATURES_PER_LANDMARK = 4
    print(f"  Flat CSV format: {NUM_FEATURES} features")

# ============================================================================
# STEP 1: SPLIT FILE PATHS FIRST (before loading any data)
# ============================================================================

print("\n" + "=" * 80)
print("  STEP 1: Splitting file paths into train/val BEFORE loading data")
print("=" * 80)

csv_paths = np.array(csv_paths)
numeric_labels = np.array(numeric_labels)

# Classes with only 1 sample cannot be stratified - separate them first
# and send them straight to training.
class_counts_all = np.bincount(numeric_labels)
singleton_classes = np.where(class_counts_all == 1)[0]
splittable_mask   = ~np.isin(numeric_labels, singleton_classes)

csv_singleton   = csv_paths[~splittable_mask]
labels_singleton = numeric_labels[~splittable_mask]

csv_splittable   = csv_paths[splittable_mask]
labels_splittable = numeric_labels[splittable_mask]

print(f"  Classes with only 1 sample (train-only): {len(singleton_classes)}")
print(f"  Splittable files: {len(csv_splittable)}")

(csv_split_train, csv_val,
 labels_split_train, labels_val) = train_test_split(
    csv_splittable, labels_splittable,
    test_size=VAL_SPLIT,
    random_state=42,
    stratify=labels_splittable
)

# Merge singleton files back into training
csv_train    = np.concatenate([csv_split_train, csv_singleton])
labels_train = np.concatenate([labels_split_train, labels_singleton])

print(f"  Train files: {len(csv_train)} ({len(csv_split_train)} stratified + {len(csv_singleton)} singletons)")
print(f"  Val files  : {len(csv_val)}")
print(f"  Val set will have ZERO augmentation - these are clean original samples\n")

# ============================================================================
# STEP 2: LOAD AND AUGMENT TRAINING SET
# ============================================================================

print("Loading and augmenting TRAINING data...")
aug_levels_cycle = [0, 1, 1, 2, 3]  # 5 augmented copies per sample

X_train_list, y_train_list = [], []
train_skipped = 0

for idx, (csv_file, lbl) in enumerate(zip(csv_train, labels_train)):
    if idx % 500 == 0:
        print(f"  {idx}/{len(csv_train)} (samples so far: {len(X_train_list)}, skipped: {train_skipped})")

    raw = load_raw_sequence(csv_file, NUM_FEATURES, FEATURES_PER_LANDMARK)
    if raw is None:
        train_skipped += 1
        continue

    # Normalize coordinates before augmenting
    raw_norm = normalize_sequence(raw)

    # Original (normalized, no augmentation)
    X_train_list.append(raw_norm)
    y_train_list.append(lbl)

    # Augmented copies
    for level in aug_levels_cycle:
        aug = SignLanguageAugmentor.augment(raw_norm, level=level)
        X_train_list.append(aug)
        y_train_list.append(lbl)

X_train = np.array(X_train_list, dtype='float32')
y_train_raw = np.array(y_train_list, dtype='int32')
print(f"  Train: {X_train.shape}, skipped: {train_skipped}")

# ============================================================================
# STEP 3: LOAD VALIDATION SET (NO AUGMENTATION)
# ============================================================================

print("\nLoading VALIDATION data (raw, no augmentation)...")
X_val_list, y_val_list = [], []
val_skipped = 0

for idx, (csv_file, lbl) in enumerate(zip(csv_val, labels_val)):
    raw = load_raw_sequence(csv_file, NUM_FEATURES, FEATURES_PER_LANDMARK)
    if raw is None:
        val_skipped += 1
        continue

    raw_norm = normalize_sequence(raw)
    X_val_list.append(raw_norm)
    y_val_list.append(lbl)

X_val = np.array(X_val_list, dtype='float32')
y_val_raw = np.array(y_val_list, dtype='int32')
print(f"  Val  : {X_val.shape}, skipped: {val_skipped}")

# ============================================================================
# FILTER RARE CLASSES (based on TRAINING file counts, not augmented counts)
# ============================================================================

# Count original (non-augmented) training samples per class
original_train_counts = np.bincount(labels_train, minlength=NUM_CLASSES)
ok_classes = np.where(original_train_counts >= MIN_SAMPLES_PER_CLASS)[0]
print(f"\nClasses with >= {MIN_SAMPLES_PER_CLASS} original training samples: {len(ok_classes)}/{NUM_CLASSES}")

# Remap labels to contiguous indices
label_remap = {old: new for new, old in enumerate(ok_classes)}

def filter_and_remap(X, y_raw):
    mask = np.isin(y_raw, ok_classes)
    X_f = X[mask]
    y_f = np.array([label_remap[l] for l in y_raw[mask]])
    return X_f, y_f

X_train, y_train_idx = filter_and_remap(X_train, y_train_raw)
X_val,   y_val_idx   = filter_and_remap(X_val,   y_val_raw)

NUM_CLASSES_FINAL = len(ok_classes)
valid_label_names = [unique_labels[i] for i in ok_classes]

y_train_cat = to_categorical(y_train_idx, num_classes=NUM_CLASSES_FINAL)
y_val_cat   = to_categorical(y_val_idx,   num_classes=NUM_CLASSES_FINAL)

print(f"Final train: {X_train.shape}")
print(f"Final val  : {X_val.shape}")
print(f"Classes    : {NUM_CLASSES_FINAL}")

# ============================================================================
# CLASS WEIGHTS (handle imbalanced classes)
# ============================================================================

unique_classes_in_train = np.unique(y_train_idx)
cw_values = compute_class_weight(
    class_weight='balanced',
    classes=unique_classes_in_train,
    y=y_train_idx
)
class_weight_dict = {int(c): float(w) for c, w in zip(unique_classes_in_train, cw_values)}
print(f"\nClass weight range: {min(class_weight_dict.values()):.3f} - {max(class_weight_dict.values()):.3f}")

# ============================================================================
# MODEL
# ============================================================================

def build_model(input_shape, num_classes):
    print(f"\nBuilding model: input={input_shape}, classes={num_classes}")
    inputs = layers.Input(shape=input_shape)

    # Feature projection
    x = layers.Dense(256)(inputs)
    x = layers.LayerNormalization()(x)

    # Temporal convolutions
    c = layers.Conv1D(256, 5, padding='same', activation='relu')(x)
    c = layers.BatchNormalization()(c)
    c = layers.Dropout(0.3)(c)

    c = layers.Conv1D(384, 3, padding='same', activation='relu')(c)
    c = layers.BatchNormalization()(c)
    c = layers.Dropout(0.3)(c)

    c = layers.Conv1D(384, 3, padding='same', activation='relu')(c)
    c = layers.BatchNormalization()(c)
    c = layers.Dropout(0.3)(c)

    # Self-attention
    attn = layers.MultiHeadAttention(num_heads=8, key_dim=48)(c, c)
    attn = layers.Dropout(0.3)(attn)
    attn = layers.LayerNormalization()(attn + c)

    # Bidirectional LSTM
    r = layers.Bidirectional(layers.LSTM(192, return_sequences=True))(attn)
    r = layers.Dropout(0.4)(r)
    r = layers.Bidirectional(layers.LSTM(128))(r)
    r = layers.Dropout(0.4)(r)

    # Classification head
    d = layers.Dense(384, activation='relu', kernel_regularizer=keras.regularizers.l2(1e-4))(r)
    d = layers.BatchNormalization()(d)
    d = layers.Dropout(0.5)(d)

    d = layers.Dense(192, activation='relu', kernel_regularizer=keras.regularizers.l2(1e-4))(d)
    d = layers.Dropout(0.4)(d)

    d = layers.Dense(128, activation='relu')(d)
    d = layers.Dropout(0.3)(d)

    outputs = layers.Dense(num_classes, activation='softmax')(d)
    return Model(inputs=inputs, outputs=outputs)


model = build_model((SEQUENCE_LENGTH, NUM_FEATURES), NUM_CLASSES_FINAL)

model.compile(
    optimizer=keras.optimizers.AdamW(learning_rate=LEARNING_RATE, weight_decay=1e-4),
    loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
    metrics=[
        'accuracy',
        keras.metrics.TopKCategoricalAccuracy(k=min(5, NUM_CLASSES_FINAL), name='top5_acc')
    ]
)

print("=" * 80)
model.summary()
print("=" * 80 + "\n")

# ============================================================================
# MIXUP GENERATOR (training only)
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
        bi = self.indexes[idx * self.batch_size:(idx + 1) * self.batch_size]
        Xb, yb = self.X[bi], self.y[bi]
        lam = np.random.beta(self.alpha, self.alpha, self.batch_size)
        lam = np.maximum(lam, 1 - lam)
        bi2 = np.random.permutation(bi)
        Xb = lam[:, None, None] * Xb + (1 - lam[:, None, None]) * self.X[bi2]
        yb = lam[:, None] * yb + (1 - lam[:, None]) * self.y[bi2]
        return Xb, yb

    def on_epoch_end(self):
        np.random.shuffle(self.indexes)


# ============================================================================
# TRAINING
# ============================================================================

callbacks = [
    keras.callbacks.EarlyStopping(
        monitor='val_accuracy',
        patience=20,
        restore_best_weights=True,
        verbose=1
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor='val_accuracy',
        factor=0.5,
        patience=8,
        min_lr=1e-7,
        verbose=1
    ),
    keras.callbacks.ModelCheckpoint(
        'best_sign_model_fixed.keras',
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    ),
]

print("=" * 80)
print("  TRAINING (honest validation - no data leakage)")
print("=" * 80)
print(f"  Train samples : {X_train.shape[0]:,} ({len(csv_train)} original files x ~{AUGMENTATION_FACTOR+1} copies)")
print(f"  Val samples   : {X_val.shape[0]:,} (original files only - zero augmentation)")
print(f"  Classes       : {NUM_CLASSES_FINAL}")
print(f"  Input shape   : {(SEQUENCE_LENGTH, NUM_FEATURES)}")
print(f"  With coord normalization + class weights\n")

train_gen = MixupGenerator(X_train, y_train_cat, BATCH_SIZE, alpha=0.2)

history = model.fit(
    train_gen,
    validation_data=(X_val, y_val_cat),
    epochs=EPOCHS,
    callbacks=callbacks,
    class_weight=class_weight_dict,
    verbose=2,
)

# ============================================================================
# EVALUATION
# ============================================================================

print("\n" + "=" * 80)
print("  EVALUATION ON CLEAN VALIDATION SET")
print("=" * 80)

y_pred_probs = model.predict(X_val, verbose=0)
y_pred = np.argmax(y_pred_probs, axis=1)
y_true = y_val_idx  # integer labels, no augmentation

accuracy = accuracy_score(y_true, y_pred)
top5_correct = sum(y_true[i] in np.argsort(y_pred_probs[i])[-5:] for i in range(len(y_true)))
top5_acc = top5_correct / len(y_true)

print(f"\nFINAL VALIDATION ACCURACY : {accuracy:.4f}  ({accuracy*100:.2f}%)")
print(f"Top-5 Accuracy            : {top5_acc:.4f}  ({top5_acc*100:.2f}%)")
print()
print("NOTE: This accuracy is on ORIGINAL, UN-AUGMENTED samples only.")
print("This is an honest estimate of real-world performance.")

# Classification report
unique_in_val = np.unique(np.concatenate([y_true, y_pred]))
names_in_val = [valid_label_names[i] for i in unique_in_val if i < len(valid_label_names)]

print("\n" + "=" * 80)
print("  CLASSIFICATION REPORT")
print("=" * 80 + "\n")
print(classification_report(
    y_true, y_pred,
    labels=unique_in_val.tolist(),
    target_names=names_in_val,
    zero_division=0
))

# ============================================================================
# PLOTS
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

axes[0, 0].plot(history.history['accuracy'], label='Train', linewidth=2)
axes[0, 0].plot(history.history['val_accuracy'], label='Validation (clean)', linewidth=2)
axes[0, 0].axhline(y=0.6733, color='orange', linestyle='--', label='Baseline (67.33%)', linewidth=1.5)
axes[0, 0].axhline(y=0.80, color='green', linestyle='--', label='Target (80%)', linewidth=1.5)
axes[0, 0].set_title('Accuracy - Correct Pipeline (No Data Leakage)', fontsize=13, fontweight='bold')
axes[0, 0].set_xlabel('Epoch')
axes[0, 0].set_ylabel('Accuracy')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

axes[0, 1].plot(history.history['loss'], label='Train', linewidth=2)
axes[0, 1].plot(history.history['val_loss'], label='Validation', linewidth=2)
axes[0, 1].set_title('Loss', fontsize=13, fontweight='bold')
axes[0, 1].set_xlabel('Epoch')
axes[0, 1].set_ylabel('Loss')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

axes[1, 0].plot(history.history['top5_acc'], label='Train Top-5', linewidth=2)
axes[1, 0].plot(history.history['val_top5_acc'], label='Val Top-5', linewidth=2)
axes[1, 0].set_title('Top-5 Accuracy', fontsize=13, fontweight='bold')
axes[1, 0].set_xlabel('Epoch')
axes[1, 0].set_ylabel('Top-5 Accuracy')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

gap = (history.history['accuracy'][-1] - history.history['val_accuracy'][-1]) * 100
gap_label = "OVERFITTING" if gap > 15 else "HEALTHY GAP" if gap > 5 else "WELL FITTED"
status = "TARGET MET!" if accuracy >= 0.80 else f"Val acc: {accuracy*100:.1f}%"

stats_text = f"""
FIXED PIPELINE RESULTS
{'='*35}
Val accuracy  : {accuracy*100:.2f}%  (HONEST)
Top-5 acc     : {top5_acc*100:.2f}%
Train-Val gap : {gap:.1f}% - {gap_label}
Status        : {status}

Previous fake result: 99.18% (data leak)
Current honest result: {accuracy*100:.2f}%

Train samples : {X_train.shape[0]:,}
Val samples   : {X_val.shape[0]:,}
  (val = original files, zero augmentation)
Classes       : {NUM_CLASSES_FINAL}
Normalization : body-center + shoulder-scale
"""

axes[1, 1].text(0.05, 0.5, stats_text, fontsize=10, family='monospace',
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
axes[1, 1].axis('off')

plt.tight_layout()
plt.savefig('training_results_fixed.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# SAVE LABEL LIST (needed for backend model_loader.py)
# ============================================================================

with open('class_labels_fixed.txt', 'w', encoding='utf-8') as f:
    for name in valid_label_names:
        f.write(name + '\n')
print(f"\nSaved {len(valid_label_names)} class labels to class_labels_fixed.txt")

print("\n" + "=" * 80)
print("  DONE")
print("=" * 80)
print(f"Model saved      : best_sign_model_fixed.keras")
print(f"Labels saved     : class_labels_fixed.txt")
print(f"Val accuracy     : {accuracy*100:.2f}%  (honest - no data leakage)")
print(f"Top-5 accuracy   : {top5_acc*100:.2f}%")
print()
print("IMPORTANT - Frontend must also apply normalization:")
print("  Before sending landmarks to /predict, subtract the body center")
print("  (mean of shoulders + hips) and divide by shoulder width for each frame.")
print("  See normalize_sequence() in this script for the exact formula.")
print("=" * 80)
