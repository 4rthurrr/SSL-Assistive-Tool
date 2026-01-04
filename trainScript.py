import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, classification_report
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Bidirectional, Conv1D, MaxPooling1D, Dropout, BatchNormalization
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2

# --- Configuration ---
DATASET_PATH = "extracted_data_csv"
MAX_FRAMES = 135  # Must match your extraction script
BATCH_SIZE = 16  # Reduced batch size for better updates on small data
EPOCHS = 200


def load_dataset():
    """
    Robust data loader with error checking.
    """
    print("Loading dataset...")

    # Debug: Print where the script is looking
    abs_path = os.path.abspath(DATASET_PATH)
    print(f"Looking for data at: {abs_path}")

    # 1. Verify Folder Exists
    if not os.path.exists(DATASET_PATH):
        print(f"\n❌ CRITICAL ERROR: The folder '{DATASET_PATH}' was not found.")
        print("Please check your PyCharm project structure.")
        print(f"Your script is running in: {os.getcwd()}")
        exit()

    X_list = []
    y_list = []

    classes = os.listdir(DATASET_PATH)
    print(f"Found classes: {classes}")

    # 2. Verify Classes Exist
    if not classes:
        print(f"\n❌ CRITICAL ERROR: The folder '{DATASET_PATH}' is empty!")
        exit()

    for class_name in classes:
        class_dir = os.path.join(DATASET_PATH, class_name)
        if not os.path.isdir(class_dir):
            continue

        csv_files = glob.glob(os.path.join(class_dir, "*.csv"))

        if not csv_files:
            print(f"⚠️ Warning: Folder '{class_name}' has no CSV files. Skipping.")
            continue

        for file in csv_files:
            try:
                df = pd.read_csv(file, header=None)
                data = df.values

                # Skip empty files
                if data.shape[0] == 0:
                    continue

                X_list.append(data)
                y_list.append(class_name)

            except Exception as e:
                print(f"Error reading {file}: {e}")

    # 3. Verify Data was loaded
    if len(X_list) == 0:
        print("\n❌ CRITICAL ERROR: No valid data loaded.")
        print("Check if your CSV files contain numbers.")
        exit()

    # --- Padding Sequences ---
    X_padded = pad_sequences(
        X_list,
        maxlen=MAX_FRAMES,
        padding='post',
        truncating='post',
        dtype='float32'
    )

    # --- Encode Labels ---
    le = LabelEncoder()
    y_encoded = le.fit_transform(y_list)
    y_categorical = tf.keras.utils.to_categorical(y_encoded)

    print(f"\n✅ Data Loaded Successfully.")
    print(f"Input Shape: {X_padded.shape}")
    print(f"Labels Shape: {y_categorical.shape}")

    return X_padded, y_categorical, le


def build_lite_crnn_model(input_shape, num_classes):
    """
    Lite Version: Optimized for small datasets (<500 samples)
    Uses L2 Regularization and high Dropout to prevent overfitting.
    """
    model = Sequential()

    # 1. Conv1D (Smaller filters: 64 -> 32)
    model.add(Conv1D(filters=32, kernel_size=3, activation='relu', input_shape=input_shape))
    model.add(BatchNormalization())
    model.add(MaxPooling1D(pool_size=2))
    model.add(Dropout(0.5))  # High dropout

    # 2. Bidirectional LSTMs (Smaller units + Regularization)
    model.add(Bidirectional(LSTM(64, return_sequences=True, kernel_regularizer=l2(0.01))))
    model.add(Dropout(0.5))

    model.add(Bidirectional(LSTM(32, kernel_regularizer=l2(0.01))))
    model.add(Dropout(0.5))

    # 3. Dense
    model.add(Dense(32, activation='relu', kernel_regularizer=l2(0.01)))
    model.add(Dense(num_classes, activation='softmax'))

    # Slower learning rate for stability
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.0005)

    model.compile(
        optimizer=optimizer,
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    return model


def plot_history(history):
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    epochs_range = range(len(acc))

    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label='Training Accuracy')
    plt.plot(epochs_range, val_acc, label='Validation Accuracy')
    plt.legend(loc='lower right')
    plt.title('Accuracy')

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label='Training Loss')
    plt.plot(epochs_range, val_loss, label='Validation Loss')
    plt.legend(loc='upper right')
    plt.title('Loss')
    plt.show()


def plot_confusion_matrix(y_test, y_pred, classes):
    y_test_indices = np.argmax(y_test, axis=1)
    y_pred_indices = np.argmax(y_pred, axis=1)

    cm = confusion_matrix(y_test_indices, y_pred_indices)

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.show()

    print("\nClassification Report:")
    print(classification_report(y_test_indices, y_pred_indices, target_names=classes, zero_division=0))


if __name__ == "__main__":
    # 1. Load Data
    X, y, label_encoder = load_dataset()
    num_classes = len(label_encoder.classes_)

    input_shape = (MAX_FRAMES, X.shape[2])

    # 2. Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Build Lite Model
    model = build_lite_crnn_model(input_shape, num_classes)
    model.summary()

    # 4. Train
    # Relaxed Early Stopping: Patience 35 (waits longer)
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=35,
        restore_best_weights=True
    )

    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=10,
        min_lr=0.00001,
        verbose=1
    )

    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stop, reduce_lr]
    )

    # 5. Save & Evaluate
    model.save("sinhala_lip_reading_model.h5")
    print("\nModel saved successfully.")

    print("Evaluating...")
    model.evaluate(X_test, y_test)

    plot_history(history)

    y_pred = model.predict(X_test)
    plot_confusion_matrix(y_test, y_pred, label_encoder.classes_)