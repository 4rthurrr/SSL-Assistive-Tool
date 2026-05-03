"""
webmain.py  -  Deaf Kids Sign Language Training System (Flask Web)

Architecture  (simplest, most reliable):
  This PC:  cv2.VideoCapture(0)  -->  annotates frames (MediaPipe)
                                  -->  MJPEG stream  /video_feed
  Browser:  <img src="/video_feed">   (plain HTTP, no HTTPS needed)

Run:  python webmain.py
Open: http://localhost:5000   (same PC)
      http://<THIS_PC_IP>:5000  (any device on LAN - view only is fine)
"""

import os, time, threading
import numpy as np
import cv2
from flask import Flask, render_template, Response, jsonify, request, send_from_directory

from feture_extract import get_detels
from Predict_realtime import predict_video

# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")

# ─── Letter mappings ──────────────────────────────────────────────────────────
LETTER_DISPLAY_MAP = {
    "Letter A": "Letter - \u0d85",
    "Letter B": "Letter - \u0d89",
    "Letter C": "Letter - \u0d8b",
    "Letter D": "Letter - \u0db8",
    "Letter E": "Letter - \u0d94",
    "Letter F": "Letter - \u0da0",
    "Letter G": "Word - \u0d85\u0db8\u0dca\u0db8\u0dcf",
    "Letter H": "Word - \u0d9c\u0dc3",
    "Letter I": "Word - \u0db8\u0dbd",
}

LETTER_VIDEO_MAP = {
    "Letter A": "practis_letters/L1.mp4",
    "Letter B": "practis_letters/L2.mp4",
    "Letter C": "practis_letters/L3.mp4",
    "Letter D": "practis_letters/L4.mp4",
    "Letter E": "practis_letters/L5.mp4",
    "Letter F": "practis_letters/L6.mp4",
    "Letter G": "practis_letters/L7.mp4",
    "Letter H": "practis_letters/L8.mp4",
    "Letter I": "practis_letters/L9.mp4",
}

LETTER_CONFIDENCE_INDEX = {
    "Letter A": 0, "Letter B": 1, "Letter C": 2,
    "Letter D": 3, "Letter E": 4, "Letter F": 5,
    "Letter G": 6, "Letter H": 7, "Letter I": 8,
}

DURATION_FRAMES = 135
OUTPUT_VIDEO    = "output.mp4"

# ─── Shared state ─────────────────────────────────────────────────────────────
state_lock = threading.Lock()
state = {
    "selected_letter":   None,
    "phase":             "idle",   # idle|watching|countdown|recording|analyzing|result
    "countdown_value":   5,
    "result_label":      "",
    "result_confidence": 0.0,
    "result_ok":         False,
    "camera_frame":      None,     # latest annotated JPEG bytes (for MJPEG)
}

vw_lock   = threading.Lock()
vw_holder = {"writer": None, "frames": 0}

# ─── Placeholder frame (shown while camera is starting) ──────────────────────
def _make_placeholder(text="Camera Starting..."):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (20, 30, 60)   # dark blue background
    cv2.putText(img, text, (60, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (86, 208, 255), 2)
    _, jpeg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return jpeg.tobytes()

_PLACEHOLDER = _make_placeholder()

# ─── Camera worker ────────────────────────────────────────────────────────────
def camera_worker():
    # Try camera index 0 first, then 1
    # Use CAP_DSHOW on Windows to prevent Media Foundation from hanging
    cap = None
    for idx in [0, 1]:
        c = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        # c = cv2.VideoCapture('1.mp4')
        if c.isOpened():
            cap = c
            print(f"[CAM] Opened camera index {idx}")
            break
        c.release()

    if cap is None:
        print("[CAM] ERROR: No camera found!")
        with state_lock:
            state["camera_frame"] = _make_placeholder("No Camera Found")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    fourcc  = cv2.VideoWriter_fourcc(*"mp4v")
    fps_out = cap.get(cv2.CAP_PROP_FPS) or 30.0

    print("[CAM] Streaming started")

    while True:
        ret, cv_img = cap.read()
        if not ret or cv_img is None:
            time.sleep(0.05)
            continue

        # Face-mesh annotation
        try:
            org_image, annotated, _ = get_detels(cv_img, anotation=True)
        except Exception as e:
            print(f"[CAM] Annotation error: {e}")
            org_image = cv_img.copy()
            annotated = cv_img.copy()

        # Current phase
        with state_lock:
            phase = state["phase"]

        # Recording
        if phase == "recording":
            h, w = org_image.shape[:2]
            with vw_lock:
                if vw_holder["writer"] is None:
                    vw_holder["writer"] = cv2.VideoWriter(
                        OUTPUT_VIDEO, fourcc, fps_out, (w, h))
                    vw_holder["frames"] = 0

                if vw_holder["frames"] < DURATION_FRAMES:
                    vw_holder["writer"].write(org_image)
                    vw_holder["frames"] += 1
                    fc = vw_holder["frames"]
                    cv2.putText(annotated, f"REC {fc}/{DURATION_FRAMES}",
                                (30, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 220), 2)
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
            cv2.putText(annotated, f"Get Ready! {cd}",
                        (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 200, 0), 3)

        elif phase == "analyzing":
            cv2.putText(annotated, "Analyzing...",
                        (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (86, 208, 255), 3)

        # Encode to JPEG and store for MJPEG stream
        _, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 72])
        with state_lock:
            state["camera_frame"] = jpeg.tobytes()

    cap.release()


# Start camera immediately when the module loads (not lazy)
threading.Thread(target=camera_worker, daemon=True).start()
print("[CAM] Camera thread launched")


# ─── Countdown ────────────────────────────────────────────────────────────────
def run_countdown():
    for i in range(5, 0, -1):
        with state_lock:
            if state["phase"] != "countdown":
                return
            state["countdown_value"] = i
        time.sleep(1)
    with state_lock:
        if state["phase"] != "countdown":
            return
        state["phase"]           = "recording"
        state["countdown_value"] = 0
    with vw_lock:
        if vw_holder["writer"]:
            vw_holder["writer"].release()
        vw_holder["writer"] = None
        vw_holder["frames"] = 0


# ─── Prediction ───────────────────────────────────────────────────────────────
def run_prediction(selected_letter):
    time.sleep(20)
    try:
        result = predict_video(OUTPUT_VIDEO)
        # result = predict_video('output_frz2.mp4')
        arr    = result[3][0] if result[0] == 1 else None
        print("llllllllllllllllllllllllllllllllllllllllllllllllll - ", arr)
        if arr is not None:
            idx  = LETTER_CONFIDENCE_INDEX.get(selected_letter, 0)
            print("r5rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr - ", idx)
            conf = round(float(arr[idx]) * 100, 2)
            print("uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu- ", conf)
            ok   = conf > 30
            lbl  = "GOOD JOB!" if ok else "Try Again"
        else:
            conf, ok, lbl = 0.0, False, "Prediction error"
    except Exception as e:
        conf, ok, lbl = 0.0, False, f"Error: {e}"

    with state_lock:
        state["result_label"]      = lbl
        state["result_confidence"] = conf
        state["result_ok"]         = ok
        state["phase"]             = "result"


# ─── MJPEG generator ──────────────────────────────────────────────────────────
def gen_frames():
    while True:
        with state_lock:
            frame = state["camera_frame"]
        
        img_bytes = frame if frame else _PLACEHOLDER
        
        # Always yield something so the browser stream never disconnects
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: ' + f"{len(img_bytes)}".encode() + b'\r\n'
               b'\r\n' + img_bytes + b'\r\n')
        time.sleep(0.033)


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", letters=list(LETTER_DISPLAY_MAP.items()))

@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/practice_video/<letter_key>")
def practice_video(letter_key):
    letter_key = letter_key.replace("_", " ")
    video_rel  = LETTER_VIDEO_MAP.get(letter_key)
    if not video_rel:
        return "Not found", 404
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "practis_letters")
    return send_from_directory(directory, os.path.basename(video_rel))

@app.route("/start_training", methods=["POST"])
def start_training():
    data   = request.get_json(force=True)
    letter = data.get("letter")
    if not letter or letter not in LETTER_VIDEO_MAP:
        return jsonify({"ok": False, "error": "Invalid letter"})
    with state_lock:
        state["selected_letter"]   = letter
        state["phase"]             = "watching"
        state["result_label"]      = ""
        state["result_confidence"] = 0.0
        state["result_ok"]         = False
    return jsonify({"ok": True, "display": LETTER_DISPLAY_MAP.get(letter, letter)})

@app.route("/student_turn", methods=["POST"])
def student_turn():
    with state_lock:
        state["phase"]           = "countdown"
        state["countdown_value"] = 5
    threading.Thread(target=run_countdown, daemon=True).start()
    return jsonify({"ok": True})

@app.route("/stop_training", methods=["POST"])
def stop_training():
    with vw_lock:
        if vw_holder["writer"]:
            vw_holder["writer"].release()
            vw_holder["writer"] = None
        vw_holder["frames"] = 0
    with state_lock:
        state.update({
            "selected_letter":   None,
            "phase":             "idle",
            "countdown_value":   5,
            "result_label":      "",
            "result_confidence": 0.0,
            "result_ok":         False,
        })
    return jsonify({"ok": True})

@app.route("/status")
def get_status():
    with state_lock:
        return jsonify({
            "phase":             state["phase"],
            "countdown":         state["countdown_value"],
            "result_label":      state["result_label"],
            "result_confidence": state["result_confidence"],
            "result_ok":         state["result_ok"],
            "selected_letter":   state["selected_letter"],
            "display_letter":    LETTER_DISPLAY_MAP.get(state["selected_letter"], ""),
        })

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print("=" * 55)
    print("  Deaf Kids Training System - Flask Web UI")
    print(f"  Local:   http://localhost:5000")
    print(f"  Network: http://{local_ip}:5000")
    print("=" * 55)
    app.run(debug=False, host="0.0.0.0", port=5100, threaded=True)
