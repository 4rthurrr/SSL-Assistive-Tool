import cv2
import os
import csv
import glob
import numpy as np
from tqdm import tqdm  # <--- NEW: Import tqdm for progress bar


try:
    from feture_extract import get_detels
except ImportError:
    print("Error: Could not import 'get_detels'. Check file name.")
    exit()


INPUT_ROOT = "dataset_video"
OUTPUT_ROOT = "extracted_data_csv"
TARGET_FPS = 30
MAX_FRAMES = 135
START_FRAME = 5


def get_next_filename(output_folder, prefix):
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


def process_videos():
    if not os.path.exists(INPUT_ROOT):
        print(f"Directory '{INPUT_ROOT}' not found.")
        return

    # --- Step 1: Count Total Videos for the Progress Bar ---
    print("Scanning dataset to count videos...")
    all_videos_list = []

    # We walk through first just to gather the file paths
    for root, dirs, files in os.walk(INPUT_ROOT):
        # Filter for video files
        video_files = [f for f in files if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        for video_file in video_files:
            # We store the root path and filename to process later
            all_videos_list.append((root, video_file))

    total_videos = len(all_videos_list)
    print(f"Found {total_videos} total videos. Starting extraction...\n")

    # --- Step 2: Process with Progress Bar ---
    # tqdm will handle the ETA (time remaining) automatically
    with tqdm(total=total_videos, unit="vid", desc="Extracting") as pbar:

        for root, video_file in all_videos_list:

            # Identify class folder from the path (e.g., 'dataset_video/aa' -> 'aa')
            class_folder = os.path.basename(root)

            output_class_path = os.path.join(OUTPUT_ROOT, class_folder)
            if not os.path.exists(output_class_path):
                os.makedirs(output_class_path)

            video_path = os.path.join(root, video_file)
            csv_filename = get_next_filename(output_class_path, class_folder)
            csv_path = os.path.join(output_class_path, csv_filename)

            # Update the progress bar description to show current file (optional, looks cool)
            pbar.set_postfix(current=f"{class_folder}/{video_file}")

            # --- Video Processing Logic ---
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                pbar.update(1)
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
                        org_image, calc_img, feture_cordinate = get_detels(frame, anotation=False)

                        if feture_cordinate and len(feture_cordinate) > 5:
                            validity_flag = feture_cordinate[0]
                            if validity_flag == 1:
                                normalized_points = feture_cordinate[5]
                                extracted_data.append(normalized_points)

                    except Exception as e:
                        # Use tqdm.write so it doesn't break the progress bar layout
                        tqdm.write(f"Error on {video_file} frame {frame_count}: {e}")

                frame_count += 1

            cap.release()

            if extracted_data:
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(extracted_data)
            else:
                tqdm.write(f"Warning: No valid data for {video_file}")

            # Update the progress bar by 1
            pbar.update(1)

    print("\nAll videos processed successfully!")


if __name__ == "__main__":
    process_videos()