import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import LabelEncoder
from video_to_csv import extract_single_video

# --- Configuration (Must match training script) ---
MODEL_PATH = "sinhala_lip_reading_model.h5"
DATASET_PATH = "extracted_data_csv"  # Used to reconstruct the LabelEncoder
MAX_FRAMES = 135


def _patch_dense_from_config():
    original_dense_from_config = tf.keras.layers.Dense.from_config

    def dense_from_config(config):
        config = dict(config)
        config.pop("quantization_config", None)
        return original_dense_from_config(config)

    tf.keras.layers.Dense.from_config = dense_from_config


def get_label_encoder():
    """Reconstructs the label encoder based on folder names."""
    classes = sorted(os.listdir(DATASET_PATH))
    le = LabelEncoder()
    le.fit(classes)
    return le


def predict_single_csv(file_path, model, le):

    try:
        # 1. Load and Clean Data
        df = pd.read_csv(file_path, header=None)
        data = df.values

        # 2. Reshape and Pad (Model expects shape: [1, MAX_FRAMES, features])
        data_expanded = [data]
        padded_data = pad_sequences(
            data_expanded,
            maxlen=MAX_FRAMES,
            padding='post',
            truncating='post',
            dtype='float32'
        )

        # 3. Predict
        prediction = model.predict(padded_data, verbose=0)
        class_index = np.argmax(prediction)
        confidence = np.max(prediction) * 100

        predicted_word = le.inverse_transform([class_index])[0]

        return predicted_word, confidence ,prediction

    except Exception as e:
        return f"Error: {e}", 0



# 1. Load Model & Labels
if not os.path.exists(MODEL_PATH):
    print(f"❌ Error: {MODEL_PATH} not found. Train the model first!")
    exit()

print("Loading model...")
_patch_dense_from_config()
loaded_model = tf.keras.models.load_model(MODEL_PATH)
label_encoder = get_label_encoder()

# 2. Test on a specific file
# REPLACE THIS with a path to a real CSV file you want to test

def predict_video(video_path):

    global loaded_model , label_encoder

    extract_single_video(video_path, "Temp_predict_CSV/buffer.csv")

    test_file = "Temp_predict_CSV/buffer.csv"
    if os.path.exists(test_file):
        word, conf , prediction = predict_single_csv(test_file, loaded_model, label_encoder)

        print("-" * 30)
        print(f"FILE: {os.path.basename(test_file)}")
        print(f"PREDICTED WORD: {word}")
        print(f"CONFIDENCE: {conf:.2f}%")
        print("-" * 30)

        return [1,str(word), round(float(conf),2) , prediction]

    else:
        print(f"Please provide a valid path for 'test_file'. Current path '{test_file}' does not exist.")
        return [0, 0, 0 ,0]