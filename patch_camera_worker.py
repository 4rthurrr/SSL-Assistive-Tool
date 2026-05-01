from pathlib import Path
import re

path = Path("Backend/app.py")
text = path.read_text(encoding="utf-8")

pattern = r"def camera_worker\(\):[\s\S]*?\n\n# Initialize local lip-reading resources at startup"

replacement = '''def _try_open_camera(index, backend_name, backend_flag):
    if backend_flag is None:
        cap = cv2.VideoCapture(index)
    else:
        cap = cv2.VideoCapture(index, backend_flag)

    if not cap.isOpened():
        cap.release()
        return None, f"{backend_name} idx={index}: not opened"

    valid_frames = 0
    black_like_frames = 0

    # Warm up and validate the stream.
    for _ in range(20):
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.02)
            continue
        valid_frames += 1
        mean_val = float(np.mean(frame))
        std_val = float(np.std(frame))
        if mean_val < 2.0 and std_val < 2.0:
            black_like_frames += 1
        time.sleep(0.02)

    if valid_frames == 0:
        cap.release()
        return None, f"{backend_name} idx={index}: no frames"

    # Ignore sources that only output black frames.
    if black_like_frames == valid_frames and valid_frames >= 5:
        cap.release()
        return None, f"{backend_name} idx={index}: black stream"

    return cap, None


def camera_worker():
    cap = None
    attempts = []

    preferred_index = os.environ.get("LIP_CAMERA_INDEX")
    indices = []
    if preferred_index is not None:
        try:
            indices.append(int(preferred_index))
        except ValueError:
            pass

    for idx in [0, 1, 2, 3, 4]:
        if idx not in indices:
            indices.append(idx)

    backends = [
        ("DSHOW", cv2.CAP_DSHOW),
        ("MSMF", cv2.CAP_MSMF),
        ("AUTO", None),
    ]

    for backend_name, backend_flag in backends:
        for idx in indices:
            c, reason = _try_open_camera(idx, backend_name, backend_flag)
            if c is not None:
                cap = c
                print(f"[CAM] Opened camera index {idx} via {backend_name}")
                break
            attempts.append(reason)
        if cap is not None:
            break

    if cap is None:
        print("[CAM] ERROR: No camera found!")
        if attempts:
            print("[CAM] Attempts:")
            for reason in attempts:
                print(f"  - {reason}")
        with state_lock:
            state["camera_frame"] = _make_placeholder("No Camera Found")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps_out = cap.get(cv2.CAP_PROP_FPS) or 30.0

    print("[CAM] Streaming started")

    missed_reads = 0

    while True:
        ret, cv_img = cap.read()
        if not ret or cv_img is None:
            missed_reads += 1
            if missed_reads >= 30:
                with state_lock:
                    state["camera_frame"] = _make_placeholder("Camera Disconnected")
            time.sleep(0.05)
            continue

        missed_reads = 0

        try:
            org_image, annotated, _ = lip_get_detels(cv_img, anotation=True)
        except Exception as e:
            print(f"[CAM] Annotation error: {e}")
            org_image = cv_img.copy()
            annotated = cv_img.copy()

        with state_lock:
            phase = state["phase"]

        if phase == "recording":
            h, w = org_image.shape[:2]
            with vw_lock:
                if vw_holder["writer"] is None:
                    vw_holder["writer"] = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, fps_out, (w, h))
                    vw_holder["frames"] = 0

                if vw_holder["frames"] < DURATION_FRAMES:
                    vw_holder["writer"].write(org_image)
                    vw_holder["frames"] += 1
                    fc = vw_holder["frames"]
                    cv2.putText(annotated, f"REC {fc}/{DURATION_FRAMES}", (30, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 220), 2)
                else:
                    vw_holder["writer"].release()
                    vw_holder["writer"] = None
                    vw_holder["frames"] = 0
                    with state_lock:
                        state["phase"] = "analyzing"
                        sel = state["selected_letter"]
                    threading.Thread(target=run_prediction, args=(sel,), daemon=True).start()

        elif phase == "countdown":
            with state_lock:
                cd = state["countdown_value"]
            cv2.putText(annotated, f"Get Ready! {cd}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 200, 0), 3)

        elif phase == "analyzing":
            cv2.putText(annotated, "Analyzing...", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (86, 208, 255), 3)

        _, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 72])
        with state_lock:
            state["camera_frame"] = jpeg.tobytes()


# Initialize local lip-reading resources at startup'''

new_text, count = re.subn(pattern, replacement, text, count=1)
if count != 1:
    raise SystemExit("Could not patch camera_worker block")

path.write_text(new_text, encoding="utf-8")
print("Patched camera worker")
