import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras.utils import to_categorical
import matplotlib.pyplot as plt

# ==========================================
# CONFIGURATION
# ==========================================
DATASET_PATH = "dataset_folder"
SEQUENCE_LENGTH = 100  # Updated: Target frames (120 -> 100)
FEATURES = 40  # Updated: Data points per frame (30 -> 40)
TEST_SIZE = 0.2
BATCH_SIZE = 32
EPOCHS = 50


# ==========================================
# 1. DATA LOADING FUNCTION
# ==========================================
def load_data(dataset_path):
    print("Loading data...")
    sequences = []
    labels = []

    try:
        classes = sorted(os.listdir(dataset_path))
    except FileNotFoundError:
        print(f"ERROR: Folder '{dataset_path}' not found.")
        return None, None, None

    for label_name in classes:
        class_dir = os.path.join(dataset_path, label_name)
        if not os.path.isdir(class_dir):
            continue

        print(f"Processing Class: {label_name}")

        files = os.listdir(class_dir)
        for file_name in files:
            file_path = os.path.join(class_dir, file_name)

            try:
                # Load data (detects if comma or space separated)
                try:
                    data = np.loadtxt(file_path, delimiter=',')
                except ValueError:
                    data = np.loadtxt(file_path, delimiter=' ')  # Try space if comma fails

                # Handle 1D arrays (single frame or flattened file)
                if data.ndim == 1:
                    data = data.reshape(-1, FEATURES)

                # --- LENGTH FIXER (Your Request) ---
                current_length = data.shape[0]

                if current_length > SEQUENCE_LENGTH:
                    # CASE 1: TOO LONG -> Cut it
                    # taking frames 0 to 120
                    data = data[:SEQUENCE_LENGTH, :]

                elif current_length < SEQUENCE_LENGTH:
                    # CASE 2: TOO SHORT -> Pad it
                    padding_needed = SEQUENCE_LENGTH - current_length
                    # Create zeros (padding)
                    zero_padding = np.zeros((padding_needed, FEATURES))
                    # Stack original data on top of zeros
                    data = np.vstack((data, zero_padding))

                # Double check shape is correct
                if data.shape == (SEQUENCE_LENGTH, FEATURES):
                    sequences.append(data)
                    labels.append(label_name)
                else:
                    print(f"Skipping {file_name}: Could not fix shape {data.shape}")

            except Exception as e:
                print(f"Error reading {file_name}: {e}")

    return np.array(sequences), np.array(labels), classes


# ==========================================
# 2. MODEL DEFINITION
# ==========================================
def build_model(input_shape, num_classes):
    model = models.Sequential()

    model.add(layers.Input(shape=input_shape))

    # --- Conv1D Block (Smoothing Jitter) ---
    model.add(layers.Conv1D(64, kernel_size=3, padding='same', activation='relu'))
    model.add(layers.BatchNormalization())
    model.add(layers.Conv1D(64, kernel_size=3, padding='same', activation='relu'))
    model.add(layers.BatchNormalization())
    model.add(layers.MaxPooling1D(pool_size=2))  # 120 -> 60
    model.add(layers.Dropout(0.2))

    # --- GRU Block (Time Sequence) ---
    model.add(layers.Bidirectional(layers.GRU(128, return_sequences=True)))
    model.add(layers.Dropout(0.3))

    model.add(layers.Bidirectional(layers.GRU(64, return_sequences=False)))
    model.add(layers.Dropout(0.3))

    # --- Classification ---
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(num_classes, activation='softmax'))

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model


# ==========================================
# 3. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":

    # 1. Load
    X, y_raw, class_names = load_data(DATASET_PATH)

    if X is None or len(X) == 0:
        print("No valid data found. Check your folder path.")
        exit()

    print(f"\nFinal Dataset Shape: {X.shape}")
    # Shape should be (Num_Samples, 120, 30)

    # 2. Encode Labels
    label_encoder = LabelEncoder()
    y_one_hot = to_categorical(label_encoder.fit_transform(y_raw))
    num_classes = len(class_names)
    print(f"Classes: {class_names}")

    # 3. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y_one_hot, test_size=TEST_SIZE, random_state=42)

    # 4. Normalize (StandardScaler)
    # We fit the scaler on Train data only, then apply to Test
    scaler = StandardScaler()

    # Flatten to (N*T, F) for scaling
    N_train, T, F = X_train.shape
    X_train_flat = X_train.reshape(-1, F)
    X_train_scaled = scaler.fit_transform(X_train_flat)
    X_train = X_train_scaled.reshape(N_train, T, F)

    # Apply same scaler to Test
    N_test, _, _ = X_test.shape
    X_test_flat = X_test.reshape(-1, F)
    X_test_scaled = scaler.transform(X_test_flat)
    X_test = X_test_scaled.reshape(N_test, T, F)

    print("Data Normalized.")

    # 5. Train
    model = build_model((SEQUENCE_LENGTH, FEATURES), num_classes)

    early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    checkpoint = callbacks.ModelCheckpoint('best_lip_model.keras', save_best_only=True)

    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stop, checkpoint]
    )

    # 6. Save Scaler (Important for real-time use)
    import joblib

    joblib.dump(scaler, 'scaler.gz')
    print("Saved model and scaler.")

    # 7. Plot
    plt.plot(history.history['accuracy'], label='Train')
    plt.plot(history.history['val_accuracy'], label='Val')
    plt.legend()
    plt.show()