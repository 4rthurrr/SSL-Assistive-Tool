import cv2
import os
import csv
import numpy as np
import time
from multiprocessing import Pool, cpu_count, freeze_support, Manager

# --- Import your custom function ---
try:
    from feture_extract import get_detels
except ImportError:
    print("Error: Could not import 'get_detels'. Check file name.")
    exit()

# --- Configuration ---
INPUT_ROOT = "dataset_video"
OUTPUT_ROOT = "extracted_data_csv"
TARGET_FPS = 30
MAX_FRAMES = 135
START_FRAME = 5


def get_next_filename_local(output_folder, prefix):
    """
    Since only ONE CPU accesses this folder, we can safely check files
    without complex locking mechanisms.
    """
    import glob  # Import locally to avoid pickling issues

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        return f"{prefix}_001.csv"

    existing_files = glob.glob(os.path.join(output_folder, f"{prefix}_*.csv"))

    if not existing_files:
        return f"{prefix}_001.csv"

    max_count = 0
    for file_path in existing_files:
        try:
            filename = os.path.basename(file_path)
            number_part = os.path.splitext(filename)[0].split('_')[-1]
            count = int(number_part)
            if count > max_count:
                max_count = count
        except ValueError:
            continue

    return f"{prefix}_{max_count + 1:03d}.csv"


def process_class_folder(args):
    """
    This worker function processes ONE entire folder (e.g., all videos in 'aa').
    """
    class_folder, input_root, output_root, lock = args

    input_class_path = os.path.join(input_root, class_folder)
    output_class_path = os.path.join(output_root, class_folder)

    # Create output directory if not exists
    if not os.path.exists(output_class_path):
        os.makedirs(output_class_path)

    # Get all videos in this specific folder
    video_files = [f for f in os.listdir(input_class_path)
                   if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]

    if not video_files:
        return f"Folder {class_folder}: Empty"

    processed_count = 0

    # --- Process videos sequentially within this folder ---
    for video_file in video_files:
        video_path = os.path.join(input_class_path, video_file)

        # Determine filename locally (Safe because we own this folder)
        csv_filename = get_next_filename_local(output_class_path, class_folder)
        csv_path = os.path.join(output_class_path, csv_filename)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            continue

        original_fps = cap.get(cv2.CAP_PROP_FPS)
        if original_fps == 0 or np.isnan(original_fps):
            original_fps = 30

        frame_interval = max(1, int(round(original_fps / TARGET_FPS)))

        extracted_data = []
        frame_count = 0

        while True:
            if len(extracted_data) >= MAX_FRAMES:
                break

            ret, frame = cap.read()
            if not ret:
                break

            if frame_count < START_FRAME:
                frame_count += 1
                continue

            if (frame_count - START_FRAME) % frame_interval == 0:
                try:
                    # Annotation=False for speed
                    _, _, feture_cordinate = get_detels(frame, anotation=False)

                    if feture_cordinate and len(feture_cordinate) > 5:
                        validity_flag = feture_cordinate[0]
                        if validity_flag == 1:
                            normalized_points = feture_cordinate[5]
                            extracted_data.append(normalized_points)

                except Exception:
                    pass

            frame_count += 1

        cap.release()

        if extracted_data:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(extracted_data)
            processed_count += 1

    # Use lock just to print safely to console so lines don't mix
    with lock:
        print(f"✅ Completed Folder: {class_folder} | Extracted {processed_count} videos")

    return f"{class_folder}: {processed_count}"


if __name__ == "__main__":
    freeze_support()

    # 1. Setup Multiprocessing Manager for Locking
    manager = Manager()
    print_lock = manager.Lock()

    if not os.path.exists(INPUT_ROOT):
        print("Input folder not found!")
        exit()

    # 2. Get list of Class Folders (e.g., aa, va, la...)
    class_folders = [d for d in os.listdir(INPUT_ROOT) if os.path.isdir(os.path.join(INPUT_ROOT, d))]

    print(f"Found {len(class_folders)} Class Folders.")
    print(f"CPUs available: {cpu_count()}")

    # Use roughly 80% of CPUs to keep system stable
    workers = max(1, cpu_count() - 1)
    print(f"Starting {workers} Parallel Workers (1 CPU per Folder)...")
    print("-" * 50)

    # 3. Prepare Arguments for Workers
    # Each worker needs: (folder_name, input_root, output_root, lock)
    tasks = [(folder, INPUT_ROOT, OUTPUT_ROOT, print_lock) for folder in class_folders]

    # 4. Start the Pool
    # We map 'tasks' to the 'process_class_folder' function
    start_time = time.time()

    with Pool(processes=workers) as pool:
        pool.map(process_class_folder, tasks)

    end_time = time.time()
    print("-" * 50)
    print(f"🎉 All Done! Total time: {end_time - start_time:.2f} seconds")