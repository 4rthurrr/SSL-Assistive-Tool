import cv2
import csv
import os
from feture_extract import get_detels

# --- Simple Config ---
VIDEO_PATH = "input_video.mp4"
OUTPUT_CSV = "output_data.csv"
TARGET_FPS = 30
MAX_FRAMES = 135
START_FRAME = 5


def extract_single_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    interval = max(1, int(round(fps / TARGET_FPS)))

    extracted_data = []
    frame_count = 0

    print(f"[DIAG] Extracting from: {video_path}")
    print(f"[DIAG] Resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")

    while len(extracted_data) < MAX_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip initial frames and sample at interval
        if frame_count >= START_FRAME and (frame_count - START_FRAME) % interval == 0:
            try:
                # Assuming get_detels returns (img1, img2, features)
                _, _, features = get_detels(frame, anotation=False)

                # Validation logic from your original script
                if features and len(features) > 5 and features[0] == 1:
                    extracted_data.append(features[5])
            except:
                pass

        frame_count += 1

    cap.release()


    if extracted_data:
        with open(output_path, 'w', newline='') as f:
            csv.writer(f).writerows(extracted_data)
        print(f"Success! Saved {len(extracted_data)} frames to {output_path}")
    else:
        print("Done. No valid features found to save.")


# if __name__ == "__main__":
#     extract_single_video("testStudent.mp4", "Temp_predict_CSV/buffer.csv")