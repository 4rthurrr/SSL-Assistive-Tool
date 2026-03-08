import cv2


def record_snippet(cap, duration_frames=100, output_name="output.mp4"):
    # 1. Setup Writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # IMPORTANT: Ensure width/height are integers and not 0
    out = cv2.VideoWriter(output_name, fourcc, fps, (width, height))

    frames_recorded = 0
    print(f"Recording {duration_frames} frames to {output_name}...")

    while frames_recorded < duration_frames:
        # FIXED LINE BELOW: Use cap.read()
        ret, frame = cap.read()

        if not ret:
            print("End of video file reached during recording.")
            break

        # Write the frame to the file
        out.write(frame)
        frames_recorded += 1

        # Visual feedback
        cv2.putText(frame, f"REC: {frames_recorded}/{duration_frames}",
                    (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('Camera', frame)

        # We use a small delay so the UI stays responsive
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    out.release()
    print("Recording saved successfully.")


# --- Main Loop ---
cap = cv2.VideoCapture('mocCam.mp4')

if not cap.isOpened():
    print("Error: Could not open mocCam.mp4. Check the file path.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video finished.")
            break

        cv2.imshow('Camera', frame)

        key = cv2.waitKey(20) & 0xFF  # Adjust waitKey for video playback speed
        if key == ord('r'):
            record_snippet(cap, duration_frames=50)
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()