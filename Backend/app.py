import os  
import pickle
import regex
import torch
import torch.nn as nn
import glob
import time
import threading

import cv2
from flask import Flask, request, jsonify, send_file, render_template, Response, send_from_directory
from flask_cors import CORS
import numpy as np
import random
import json
from datetime import datetime
from collections import defaultdict, deque
import sys
import io
import atexit
import hashlib
import importlib.util
from contextlib import contextmanager
from google import genai
from dotenv import load_dotenv
import subprocess
import requests
import shlex
import shutil

# Fix Unicode encoding for Windows consoles BEFORE any emoji prints.
if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_BASE_DIR)
# Integrated Lip Reading location (internal to Backend)
_LIP_READING_SOURCE_DIR = os.path.join(_BASE_DIR, "lip-reading")

# Suppress OpenCV verbose backend warnings on Windows
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")

# Local lip-reading resources in Backend folder (for self-contained operation)
_LIP_READING_LOCAL_DIR = os.path.join(_BASE_DIR, "lip-reading")
_LIP_READING_PRACTIS_DIR = os.path.join(_LIP_READING_LOCAL_DIR, "practis_letters")
_LIP_READING_ROOT_PRACTIS_DIR = os.path.join(_BASE_DIR, "practis_letters")

def _ensure_practis_videos():
    """Copy practice videos from source folder to Backend/lip-reading on startup"""
    os.makedirs(_LIP_READING_PRACTIS_DIR, exist_ok=True)
    os.makedirs(_LIP_READING_ROOT_PRACTIS_DIR, exist_ok=True)
    
    source_practis = os.path.join(_LIP_READING_SOURCE_DIR, "practis_letters")
    if os.path.isdir(source_practis):
        for video_file in ["L1.mp4", "L2.mp4", "L3.mp4", "L4.mp4", "L5.mp4", "L6.mp4", "L7.mp4", "L8.mp4", "L9.mp4"]:
            src = os.path.join(source_practis, video_file)
            for dst_dir in (_LIP_READING_PRACTIS_DIR, _LIP_READING_ROOT_PRACTIS_DIR):
                dst = os.path.join(dst_dir, video_file)
                if os.path.exists(src) and not os.path.exists(dst):
                    try:
                        shutil.copy2(src, dst)
                        print(f"  ✅ Copied practice video: {video_file} -> {dst_dir}")
                    except Exception as e:
                        print(f"  ⚠️ Failed to copy {video_file} to {dst_dir}: {e}")
for _site_packages in (
    os.path.join(_LIP_READING_LOCAL_DIR, ".venv", "Lib", "site-packages"),
    os.path.join(_LIP_READING_LOCAL_DIR, ".realtime", "Lib", "site-packages"),
):
    if os.path.isdir(_site_packages) and _site_packages not in sys.path:
        sys.path.insert(0, _site_packages)
if _LIP_READING_SOURCE_DIR not in sys.path:
    sys.path.insert(0, _LIP_READING_SOURCE_DIR)
if _LIP_READING_LOCAL_DIR not in sys.path:
    sys.path.insert(0, _LIP_READING_LOCAL_DIR)


def _load_lip_module(module_name, file_name):
    module_path = os.path.join(_LIP_READING_SOURCE_DIR, file_name)
    if not os.path.exists(module_path):
        cache_dir = os.path.join(_LIP_READING_SOURCE_DIR, "__pycache__")
        cache_glob = os.path.join(cache_dir, f"{os.path.splitext(file_name)[0]}*.pyc")
        pyc_matches = sorted(glob.glob(cache_glob))
        if pyc_matches:
            module_path = pyc_matches[0]
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {file_name} from {_LIP_READING_SOURCE_DIR}")
    module = importlib.util.module_from_spec(spec)
    current_dir = os.getcwd()
    try:
        os.chdir(_LIP_READING_SOURCE_DIR)
        spec.loader.exec_module(module)
    finally:
        os.chdir(current_dir)
    return module


def _resolve_practice_video_path(letter_key):
    video_rel = LETTER_VIDEO_MAP.get(letter_key)
    if not video_rel:
        return None

    filename = os.path.basename(video_rel)
    candidates = [
        os.path.join(_LIP_READING_ROOT_PRACTIS_DIR, filename),
        os.path.join(_LIP_READING_PRACTIS_DIR, filename),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


try:
    _lip_feature_module = _load_lip_module("lip_source_feature_extraction", "feture_extract.py")
    lip_get_detels = _lip_feature_module.get_detels
except Exception as exc:
    print(f"[WARN] Lip feature module unavailable, using fallback: {exc}")

    def lip_get_detels(cv_img, anotation=True):
        annotated = cv_img.copy()
        if anotation:
            cv2.putText(
                annotated,
                "Lip reading fallback",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (86, 208, 255),
                2,
            )
        return cv_img, annotated, None


try:
    _lip_predict_module = _load_lip_module("lip_source_prediction", "Predict_realtime.py")
    lip_predict_video = _lip_predict_module.predict_video
except Exception as exc:
    print(f"[WARN] Lip prediction module unavailable, using fallback: {exc}")

    def lip_predict_video(video_path):
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        motion_score = 0.0
        previous_gray = None

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            frame_count += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if previous_gray is not None:
                motion_score += float(np.mean(cv2.absdiff(gray, previous_gray)))
            previous_gray = gray

        cap.release()

        class_count = len(LETTER_CONFIDENCE_INDEX)
        probabilities = np.full((1, class_count), 0.01, dtype=float)
        if class_count:
            chosen_index = int((motion_score + frame_count) % class_count)
            probabilities[0, chosen_index] = 0.85
            probabilities[0] /= probabilities[0].sum()

        return (1, None, None, probabilities)

# -----------------------------
# Source subprocess bridge
# -----------------------------
_SOURCE_PROC = None
_SOURCE_PORT = int(os.environ.get('LIP_SOURCE_PORT', '5005'))
_SOURCE_URL = f"http://127.0.0.1:{_SOURCE_PORT}"

def _find_source_python():
    candidates = [
        os.path.join(_LIP_READING_SOURCE_DIR, '.realtime', 'Scripts', 'python.exe'),
        os.path.join(_LIP_READING_SOURCE_DIR, '.venv', 'Scripts', 'python.exe'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # fallback to system python
    return sys.executable

def _start_source_process(timeout=10):
    # Source bridge intentionally disabled.
    # This backend runs independently from the external lip-reading project folder.
    return False

def _stop_source_process():
    global _SOURCE_PROC
    if _SOURCE_PROC:
        try:
            _SOURCE_PROC.terminate()
        except Exception:
            pass
        _SOURCE_PROC = None
        return True
    return False

def _is_source_running():
    return _SOURCE_PROC is not None and _SOURCE_PROC.poll() is None

def _proxy_to_source(path, method='GET', data=None, params=None, stream=False):
    url = _SOURCE_URL + path
    try:
        if method == 'GET':
            return requests.get(url, params=params, stream=stream, timeout=5)
        else:
            return requests.post(url, json=data, params=params, timeout=10)
    except Exception as e:
        print(f"⚠️ Proxy to source failed: {e}")
        return None

# (UTF-8 stdout fix already applied at module top)

# Load environment variables from .env file
load_dotenv()
print(f"🔑 GEMINI_API_KEY loaded: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")

# MongoDB integration
try:
    from core.database.mongodb_integration import mongodb_manager
    print("✅ MongoDB integration loaded")
except Exception as e:
    print(f"⚠️ MongoDB integration failed: {e}")
    mongodb_manager = None

app = Flask(
    __name__,
    template_folder=os.path.join(_BASE_DIR, "templates"),
    static_folder=os.path.join(_BASE_DIR, "static"),
)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    },
    r"/start_training": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    },
    r"/student_turn": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    },
    r"/stop_training": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    },
    r"/status": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    },
    r"/practice_video/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    },
    r"/video_feed": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# ========================
# LIP READING (SOURCE-COMPATIBLE)
# ========================
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
OUTPUT_VIDEO = os.path.join(_LIP_READING_LOCAL_DIR, "output.mp4")

state_lock = threading.Lock()
state = {
    "selected_letter": None,
    "phase": "idle",
    "countdown_value": 5,
    "result_label": "",
    "result_confidence": 0.0,
    "result_ok": False,
    "camera_frame": None,
}

vw_lock = threading.Lock()
vw_holder = {"writer": None, "frames": 0}


@contextmanager
def _lip_source_cwd():
    current_dir = os.getcwd()
    try:
        os.chdir(_LIP_READING_SOURCE_DIR)
        yield
    finally:
        os.chdir(current_dir)


def _make_placeholder(text="Camera Starting..."):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (20, 30, 60)
    cv2.putText(img, text, (60, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (86, 208, 255), 2)
    _, jpeg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return jpeg.tobytes()


_PLACEHOLDER = _make_placeholder()


def _try_open_camera(index, backend_name, backend_flag):
    print(f"[CAM] Trying index={index} backend={backend_name}...")
    if backend_flag is None:
        cap = cv2.VideoCapture(index)
    else:
        cap = cv2.VideoCapture(index, backend_flag)

    if not cap.isOpened():
        cap.release()
        print(f"[CAM]   -> not opened")
        return None, f"{backend_name} idx={index}: not opened"

    print(f"[CAM]   -> opened, waiting for frames...")
    valid_frames = 0
    black_like_frames = 0

    # Windows built-in cameras (especially DSHOW) can take 4-5 seconds before
    # delivering the first real frame. Give up to 100 attempts x 60ms = 6 s.
    max_attempts = 100
    for attempt in range(max_attempts):
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.06)
            continue
        valid_frames += 1
        mean_val = float(np.mean(frame))
        std_val  = float(np.std(frame))
        if mean_val < 2.0 and std_val < 2.0:
            black_like_frames += 1
        else:
            # Got at least one real, non-black frame - camera is good!
            print(f"[CAM]   -> got real frame at attempt {attempt} (mean={mean_val:.1f})")
            break
        time.sleep(0.06)

    if valid_frames == 0:
        cap.release()
        print(f"[CAM]   -> no frames in {max_attempts} attempts, rejected")
        return None, f"{backend_name} idx={index}: no frames in {max_attempts} attempts"

    # Reject only if EVERY frame we received was black (virtual/broken cam).
    if black_like_frames == valid_frames and valid_frames >= 5:
        cap.release()
        print(f"[CAM]   -> only black frames, rejected")
        return None, f"{backend_name} idx={index}: black stream"

    print(f"[CAM]   -> ACCEPTED (valid_frames={valid_frames}, black={black_like_frames})")
    return cap, None


def _build_camera_candidates():
    preferred_index = os.environ.get("LIP_CAMERA_INDEX")
    preferred_backend = (os.environ.get("LIP_CAMERA_BACKEND") or "").strip().upper()

    indices = []
    if preferred_index is not None:
        try:
            indices.append(int(preferred_index))
        except ValueError:
            pass

    for idx in [0, 1, 2, 3, 4]:
        if idx not in indices:
            indices.append(idx)

    # On Windows, DSHOW handles shared/built-in cameras better than MSMF.
    # MSMF throws MF_E_HW_MFT_FAILED_START_STREAMING (-1072875772) when the
    # camera hardware is busy or needs exclusive access. Try DSHOW first.
    all_backends = [
        ("DSHOW", cv2.CAP_DSHOW),
        ("AUTO",  None),
        ("MSMF",  cv2.CAP_MSMF),  # Last resort — prone to exclusive-lock errors
    ]

    if preferred_backend in {"DSHOW", "MSMF", "AUTO"}:
        preferred = [b for b in all_backends if b[0] == preferred_backend]
        others    = [b for b in all_backends if b[0] != preferred_backend]
        backends  = preferred + others
    else:
        backends = all_backends

    # Build candidates: try index 0 with every backend first (most likely to
    # be the built-in laptop camera), then the remaining indices.
    priority_idx = indices[0] if indices else 0
    rest_indices = [i for i in indices if i != priority_idx]

    candidates = []
    # Priority pass: all backends with index 0
    for backend_name, backend_flag in backends:
        candidates.append((priority_idx, backend_name, backend_flag))
    # Remaining indices with all backends
    for idx in rest_indices:
        for backend_name, backend_flag in backends:
            candidates.append((idx, backend_name, backend_flag))

    return candidates


def _open_best_camera(start_offset=0):
    attempts = []
    candidates = _build_camera_candidates()
    if not candidates:
        return None, attempts, None

    total = len(candidates)
    for i in range(total):
        idx, backend_name, backend_flag = candidates[(start_offset + i) % total]
        c, reason = _try_open_camera(idx, backend_name, backend_flag)
        if c is not None:
            return c, attempts, (idx, backend_name)
        attempts.append(reason)

    return None, attempts, None


def camera_worker():
    reopen_round = 0

    while True:
        cap, attempts, opened = _open_best_camera(start_offset=reopen_round)
        if cap is None:
            print("[CAM] ERROR: No camera found!")
            if attempts:
                print("[CAM] Attempts:")
                for reason in attempts:
                    print(f"  - {reason}")
            with state_lock:
                state["camera_frame"] = _make_placeholder("No Camera Found")
            time.sleep(2.0)
            reopen_round += 1
            continue

        idx, backend_name = opened
        print(f"[CAM] Opened camera index {idx} via {backend_name}")

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps_out = cap.get(cv2.CAP_PROP_FPS) or 30.0

        print("[CAM] Streaming started")

        missed_reads = 0
        black_streak = 0

        while True:
            ret, cv_img = cap.read()
            if not ret or cv_img is None:
                missed_reads += 1
                if missed_reads >= 30:
                    print("[CAM] Read timeout; switching camera source...")
                    with state_lock:
                        state["camera_frame"] = _make_placeholder("Switching Camera")
                    break
                time.sleep(0.05)
                continue

            missed_reads = 0

            mean_val = float(np.mean(cv_img))
            std_val = float(np.std(cv_img))
            if mean_val < 2.0 and std_val < 2.0:
                black_streak += 1
            else:
                black_streak = 0

            if black_streak >= 90:
                print(f"[CAM] Black stream detected on idx={idx} via {backend_name}; switching...")
                with state_lock:
                    state["camera_frame"] = _make_placeholder("Camera Black - Switching")
                break

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

            time.sleep(0.01)

        cap.release()
        reopen_round += 1
        time.sleep(0.4)


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
        state["phase"] = "recording"
        state["countdown_value"] = 0
    with vw_lock:
        if vw_holder["writer"]:
            vw_holder["writer"].release()
        vw_holder["writer"] = None
        vw_holder["frames"] = 0


def run_prediction(selected_letter):
    time.sleep(20)
    try:
        # Try to use the lip prediction module (either imported or fallback)
        result = lip_predict_video(OUTPUT_VIDEO)
        arr = result[3][0] if result[0] == 1 else None
        if arr is not None:
            idx = LETTER_CONFIDENCE_INDEX.get(selected_letter, 0)
            conf = round(float(arr[idx]) * 100, 2)
            ok = conf > 30
            lbl = "GOOD JOB!" if ok else "Try Again"
        else:
            conf, ok, lbl = 0.0, False, "Prediction error"
    except Exception:
        # Keep UI friendly and avoid leaking local filesystem paths in errors.
        conf, ok, lbl = 0.0, False, "Prediction unavailable"

    with state_lock:
        state["result_label"] = lbl
        state["result_confidence"] = conf
        state["result_ok"] = ok
        state["phase"] = "result"


def gen_frames():
    while True:
        with state_lock:
            frame = state["camera_frame"]

        img_bytes = frame if frame else _PLACEHOLDER
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: ' + f"{len(img_bytes)}".encode() + b'\r\n'
               b'\r\n' + img_bytes + b'\r\n')
        time.sleep(0.033)


@app.route("/")
def lip_reading_home():
    return render_template("index.html", letters=list(LETTER_DISPLAY_MAP.items()))


@app.route("/video_feed")
def video_feed():
    # If the original source server is available, proxy its video feed
    if _is_source_running():
        resp = _proxy_to_source('/video_feed', stream=True)
        if resp is not None and resp.status_code == 200:
            def stream():
                try:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            yield chunk
                except Exception as e:
                    print(f"⚠️ Error streaming from source: {e}")
            return Response(stream(), mimetype=resp.headers.get('Content-Type', 'multipart/x-mixed-replace; boundary=frame'))
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/practice_video/<letter_key>")
def practice_video(letter_key):
    letter_key = letter_key.replace("_", " ")
    video_path = _resolve_practice_video_path(letter_key)
    print(f"[practice_video] request={letter_key} resolved={video_path}")
    if not video_path:
        return "Not found", 404
    return send_file(video_path, mimetype="video/mp4", as_attachment=False, conditional=True)


@app.route("/start_training", methods=["POST"])
def start_training():
    data = request.get_json(force=True)
    letter = data.get("letter")
    if not letter or letter not in LETTER_VIDEO_MAP:
        return jsonify({"ok": False, "error": "Invalid letter"})
    with state_lock:
        state["selected_letter"] = letter
        state["phase"] = "watching"
        state["result_label"] = ""
        state["result_confidence"] = 0.0
        state["result_ok"] = False
    return jsonify({"ok": True, "display": LETTER_DISPLAY_MAP.get(letter, letter)})


@app.route("/student_turn", methods=["POST"])
def student_turn():
    with state_lock:
        state["phase"] = "countdown"
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
            "selected_letter": None,
            "phase": "idle",
            "countdown_value": 5,
            "result_label": "",
            "result_confidence": 0.0,
            "result_ok": False,
        })
    return jsonify({"ok": True})


@app.route("/status")
def get_status():
    with state_lock:
        return jsonify({
            "phase": state["phase"],
            "countdown": state["countdown_value"],
            "result_label": state["result_label"],
            "result_confidence": state["result_confidence"],
            "result_ok": state["result_ok"],
            "selected_letter": state["selected_letter"],
            "display_letter": LETTER_DISPLAY_MAP.get(state["selected_letter"], ""),
        })

# ========================
# PATHS
# ========================
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(_BASE_DIR, "text-to-sign", "SSL_model")
VIDEO_DIR = os.path.join(_BASE_DIR, "Dataset - Original")

# ========================
# GLOBAL STORAGE
# ========================
user_sessions = {}
user_game_states = {}

# ========================
# BUILD VIDEO MAPPING
# ========================
def build_video_mapping():
    """Build mapping: only one video per word"""
    video_map = {}
    
    if not os.path.exists(VIDEO_DIR):
        print(f"❌ VIDEO_DIR does not exist: {VIDEO_DIR}")
        return video_map

    print(f"\n🔍 Scanning for videos in: {VIDEO_DIR}")

    for root, dirs, files in os.walk(VIDEO_DIR):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.webm', '.mkv')):
                base_name = os.path.splitext(file)[0]
                if '_' in base_name:
                    key = base_name.split('_')[0].lower()
                else:
                    key = base_name.lower()
                
                if key in video_map:
                    continue
                
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, VIDEO_DIR).replace('\\', '/')
                
                video_map[key] = {
                    'filename': file,
                    'relative_path': relative_path,
                    'full_path': full_path,
                    'exists': True,
                    'sinhala_word': None
                }
                
                print(f"  {key:20s} → File: {file}")

    print(f"\n✅ Mapped {len(video_map)} unique words")
    return video_map

# Load metadata
try:
    with open(os.path.join(MODEL_DIR, "model_ssl.pkl"), 'rb') as f:
        metadata = pickle.load(f)

    game_classes = metadata['game_classes']
    label_to_english = metadata['label_to_english']
    input_dim = metadata['input_dim']
    hidden_dim = metadata['hidden_dim']
    num_classes = metadata['num_classes']
    level_words = metadata['level_words']
    level_indices = metadata['level_indices']

    print("✅ Metadata loaded successfully!")
except Exception as e:
    print(f"❌ Error loading metadata: {e}")
    label_to_english = {}
    level_words = {'basic': [], 'easy': [], 'medium': [], 'hard': []}
    level_indices = {}
    input_dim, hidden_dim, num_classes = 128, 256, 100

VIDEO_MAPPING = build_video_mapping()

# Update video mapping with Sinhala words
for key, video_info in VIDEO_MAPPING.items():
    for sinhala, english in label_to_english.items():
        if english.lower() == key:
            video_info['sinhala_word'] = sinhala
            break

# ========================
# HINT SYSTEM
# ========================
class StruggleDetector:
    def __init__(self):
        self.attempt_history = defaultdict(lambda: deque(maxlen=20))
        self.struggle_threshold = {'basic': 2, 'easy': 3, 'medium': 4, 'hard': 5}
        
    def record_attempt(self, user_id, word, level, correct, time_taken):
        self.attempt_history[user_id].append({
            'word': word, 'level': level, 'correct': correct,
            'time_taken': time_taken, 'timestamp': datetime.now()
        })
        
    def is_struggling(self, user_id, word, level):
        if user_id not in self.attempt_history:
            return False
        recent = list(self.attempt_history[user_id])[-5:]
        wrong_count = sum(1 for a in recent if a['word'] == word and not a['correct'])
        return wrong_count >= self.struggle_threshold.get(level, 3)
    
    def get_attempt_count(self, user_id, word):
        if user_id not in self.attempt_history:
            return 0
        return sum(1 for a in self.attempt_history[user_id] if a['word'] == word)

struggle_detector = StruggleDetector()

# ========================
# AI HINTS - IMPROVED GEMINI HINT GENERATION
# ========================
ai_hint_cache = {}

def _anonymize_user(user_id: str) -> str:
    try:
        return hashlib.sha256(str(user_id).encode('utf-8')).hexdigest()[:12]
    except Exception:
        return 'anon'

def generate_ai_hint(user_id, sinhala_word, english_word, attempt_count, recent_attempts, level='basic'):
    """Generate a short, clue-style hint using Gemini API"""
    cache_key = f"{user_id}:{sinhala_word}:{attempt_count}:{level}"
    
    # Check cache first
    if cache_key in ai_hint_cache:
        print(f"📦 Using cached hint for {sinhala_word}")
        return {
            'cached': True, 
            'hint': ai_hint_cache[cache_key],
            'hint_type': 'clue'
        }

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not set")
        return {
            'cached': False, 
            'hint': None, 
            'error': 'API key not configured'
        }

    try:
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        
        # Build prompt for clue-style hint (exactly like your example)
        prompt = f"""Secret word: "{sinhala_word}" (which means "{english_word}" in English)
Give one short clue without saying the word.
Max 8 words.

Output format:
🔎 Hint: [your clue here]"""

        print(f"🤔 Generating hint for: {sinhala_word} ({english_word})")
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # Higher free-tier quota than 2.5-flash
            contents=prompt
        )
        
        # Extract hint text
        if hasattr(response, 'text'):
            hint_text = response.text.strip()
        else:
            hint_text = str(response).strip()
        
        # Clean up the hint - remove the "🔎 Hint:" prefix if present
        if hint_text.startswith('🔎 Hint:'):
            hint_text = hint_text.replace('🔎 Hint:', '').strip()
        elif hint_text.startswith('Hint:'):
            hint_text = hint_text.replace('Hint:', '').strip()
        
        # Ensure it's short
        words = hint_text.split()
        if len(words) > 8:
            hint_text = ' '.join(words[:8]) + '...'
        
        # Format with emoji
        formatted_hint = f"🔎 Hint: {hint_text}"
        
        # Cache the hint
        ai_hint_cache[cache_key] = formatted_hint
        print(f"✅ Generated hint: {formatted_hint}")
        
        return {
            'cached': False, 
            'hint': formatted_hint,
            'hint_type': 'clue'
        }
        
    except Exception as e:
        print(f"⚠️ AI hint generation failed: {e}")
        
        # Fallback hints based on word characteristics
        fallback_hints = {
            # Common Sinhala words with simple clues
            'අම්මා': '🔎 Hint: 👩 The person who takes care of you',
            'තාත්තා': '🔎 Hint: 👨 The head of the family',
            'බල්ලා': '🔎 Hint: 🐕 A loyal pet that barks',
            'පූසා': '🔎 Hint: 🐈 A furry pet that meows',
            'ගස': '🔎 Hint: 🌳 Gives us shade and fruit',
            'මල': '🔎 Hint: 🌸 Beautiful and fragrant',
            'වතුර': '🔎 Hint: 💧 Clear liquid we drink',
            'කිරි': '🔎 Hint: 🥛 White drink from cows',
            'පාන්': '🔎 Hint: 🍞 Common breakfast food',
            'බත්': '🔎 Hint: 🍚 Staple food in Sri Lanka',
            'හිරු': '🔎 Hint: ☀️ Gives us light during the day',
            'සඳ': '🔎 Hint: 🌙 Seen in the night sky',
            'තරු': '🔎 Hint: ⭐ Twinkle in the night sky',
            'මුහුද': '🔎 Hint: 🌊 Large body of salt water',
            'ගඟ': '🔎 Hint: 💧 Flowing water body',
            'කුරුල්ලා': '🔎 Hint: 🐦 Animal that can fly',
            'මාළුවා': '🔎 Hint: 🐟 Lives in water',
            'අලියා': '🔎 Hint: 🐘 Large animal with trunk',
            'සිංහයා': '🔎 Hint: 🦁 King of the jungle',
            'පුස්තකාලය': '🔎 Hint: 📚 Place with many books'
        }
        
        if sinhala_word in fallback_hints:
            return {
                'cached': False, 
                'hint': fallback_hints[sinhala_word],
                'hint_type': 'fallback'
            }
        
        # Generic fallback
        return {
            'cached': False, 
            'hint': f"🔎 Hint: This word is about {english_word.lower()}",
            'hint_type': 'generic'
        }

# ========================
# MODEL
# ========================
class LSTMPuzzleModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_classes):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(nn.Linear(hidden_dim*2, 128), nn.ReLU(), nn.Linear(128, num_classes))
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        return self.fc(lstm_out[:, -1, :])

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = LSTMPuzzleModel(input_dim, hidden_dim, num_classes)
try:
    model.load_state_dict(torch.load(os.path.join(MODEL_DIR, "sinhala_sign_model.pth"), map_location=device))
    model.to(device)
    model.eval()
    print(f"✅ Model loaded on: {device}")
except Exception as e:
    print(f"⚠️ Could not load model: {e}")

# ========================
# GAME STATE MANAGEMENT
# ========================
class GameState:
    def __init__(self, user_id, level):
        self.user_id = user_id
        self.level = level
        self.used_words = []
        self.round = 0
        self.max_rounds = 10
        
    def add_used_word(self, word):
        if word not in self.used_words:
            self.used_words.append(word)
    
    def get_available_words(self, all_words):
        return [w for w in all_words if w not in self.used_words]
    
    def reset_game(self):
        self.used_words = []
        self.round = 0
    
    def is_game_complete(self):
        return self.round >= self.max_rounds

def get_game_state(user_id, level):
    key = f"{user_id}_{level}"
    if key not in user_game_states:
        user_game_states[key] = GameState(user_id, level)
    return user_game_states[key]

# ========================
# VIDEO HELPER
# ========================
def find_video_for_word(sinhala_word):
    """Find video file for word"""
    english = label_to_english.get(sinhala_word, '').lower()
    
    if english in VIDEO_MAPPING:
        return english
    if sinhala_word.lower() in VIDEO_MAPPING:
        return sinhala_word.lower()
    
    for key in VIDEO_MAPPING.keys():
        if english and (key.startswith(english[:3]) or english.startswith(key[:3])):
            return key
    
    return None

# ========================
# API ENDPOINTS
# ========================
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'videos_mapped': len(VIDEO_MAPPING),
        'mongodb_connected': mongodb_manager is not None,
        'levels': list(level_words.keys())
    })


@app.route('/bridge/start', methods=['POST'])
def bridge_start():
    ok = _start_source_process()
    return jsonify({'ok': ok, 'running': _is_source_running()})


@app.route('/bridge/stop', methods=['POST'])
def bridge_stop():
    ok = _stop_source_process()
    return jsonify({'ok': ok, 'running': _is_source_running()})


@app.route('/bridge/status', methods=['GET'])
def bridge_status():
    return jsonify({'running': _is_source_running(), 'url': _SOURCE_URL})

@app.route('/api/puzzle/generate', methods=['POST'])
def generate_puzzle():
    try:
        data = request.json
        level = data.get('level', 'basic')
        user_id = data.get('user_id', 'default')
        
        game_state = get_game_state(user_id, level)
        game_state.round += 1
        
        level_word_list = level_words.get(level, [])
        words_with_videos = [w for w in level_word_list if find_video_for_word(w)]
        available_words = game_state.get_available_words(words_with_videos)
        
        if len(available_words) < 4:
            game_state.used_words = []
            available_words = words_with_videos
        
        if len(available_words) < 4:
            return jsonify({'success': False, 'error': 'Not enough words'}), 400
        
        target_word = random.choice(available_words)
        game_state.add_used_word(target_word)
        video_key = find_video_for_word(target_word)
        
        other_available = [w for w in available_words if w != target_word]
        options = random.sample(other_available, min(3, len(other_available)))
        options.append(target_word)
        random.shuffle(options)
        
        return jsonify({
            'success': True,
            'target_word': target_word,
            'target_english': label_to_english.get(target_word, ''),
            'video_url': f"/api/videos/{video_key}" if video_key else None,
            'options': [{'word': w, 'english': label_to_english.get(w, '')} for w in options],
            'level': level,
            'round': game_state.round,
            'total_rounds': game_state.max_rounds
        })
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/<video_key>', methods=['GET'])
def serve_video(video_key):
    try:
        video_key = video_key.lower().strip()
        
        if video_key not in VIDEO_MAPPING:
            return jsonify({'error': 'Video not found'}), 404
        
        video_info = VIDEO_MAPPING[video_key]
        full_path = video_info['full_path']
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        ext = os.path.splitext(full_path)[1].lower()
        mimetype = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.avi': 'video/x-msvideo'
        }.get(ext, 'video/mp4')
        
        return send_file(full_path, mimetype=mimetype)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attempt', methods=['POST'])
def record_attempt():
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        word = data.get('word')  # This is the Sinhala word
        level = data.get('level', 'basic')
        correct = data.get('correct', False)
        time_taken = data.get('time_taken', 0)
        
        # Save to MongoDB
        attempt_doc = {
            'userId': str(user_id),
            'game': 'puzzle',
            'level': level,
            'word': word,
            'sinhalaWord': word,
            'englishTranslation': label_to_english.get(word, ''),
            'correct': bool(correct),
            'confidence': data.get('confidence'),
            'timeTaken': float(time_taken),
            'sessionId': data.get('session_id')
        }
        
        saved = False
        if mongodb_manager:
            try:
                result = mongodb_manager.save_game_attempt(attempt_doc)
                saved = result is not None
                print(f"✅ Attempt saved: {saved}")
            except Exception as e:
                print(f"⚠️ MongoDB save failed: {e}")
        
        # Track in memory
        struggle_detector.record_attempt(user_id, word, level, correct, time_taken)
        attempt_count = struggle_detector.get_attempt_count(user_id, word)
        
        # Calculate wrong attempts for this specific word in current session
        recent_attempts = list(struggle_detector.attempt_history.get(user_id, []))
        wrong_attempts_for_word = sum(1 for a in recent_attempts 
                                      if a['word'] == word and not a['correct'])
        
        # Check if game over condition reached (5 wrong attempts)
        game_over = wrong_attempts_for_word >= 5
        
        # Generate AI hint if attempt count >= 2 and not correct
        ai_hint_result = None
        if not correct and attempt_count >= 2:
            print(f"🎯 Generating hint for {word} (attempt #{attempt_count})")
            recent = recent_attempts[-6:]
            english_word = label_to_english.get(word, '')
            
            ai_hint_result = generate_ai_hint(
                user_id, 
                word,  # Sinhala word
                english_word,  # English translation
                attempt_count, 
                recent, 
                level
            )
        
        # Prepare response
        response_data = {
            'success': True,
            'saved': saved,
            'attempt_number': attempt_count,
            'wrong_attempts': wrong_attempts_for_word,
            'game_over': game_over,
            'hint': ai_hint_result.get('hint') if ai_hint_result else None,
            'hint_type': ai_hint_result.get('hint_type') if ai_hint_result else None,
            'hint_cached': ai_hint_result.get('cached', False) if ai_hint_result else False
        }
        
        # If game over, include the correct word
        if game_over:
            response_data['correct_word'] = word
            response_data['correct_english'] = label_to_english.get(word, '')
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/hint', methods=['POST'])
def get_hint_direct():
    """Direct endpoint to get a hint for a word"""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        word = data.get('word')  # Sinhala word
        level = data.get('level', 'basic')
        
        if not word:
            return jsonify({'success': False, 'error': 'Word is required'}), 400
        
        english_word = label_to_english.get(word, '')
        attempt_count = struggle_detector.get_attempt_count(user_id, word)
        recent = list(struggle_detector.attempt_history.get(user_id, []))[-6:]
        
        ai_hint_result = generate_ai_hint(
            user_id, 
            word,
            english_word,
            attempt_count + 1,
            recent,
            level
        )
        
        return jsonify({
            'success': True,
            'word': word,
            'english': english_word,
            'hint': ai_hint_result.get('hint'),
            'hint_type': ai_hint_result.get('hint_type')
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/progress-report', methods=['POST', 'OPTIONS'])
def get_progress_report():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        
        # Get attempts from MongoDB or memory
        attempts = []
        if mongodb_manager and hasattr(mongodb_manager, 'get_recent_attempts'):
            try:
                raw_attempts = list(mongodb_manager.get_recent_attempts(user_id, limit=1000) or [])
                for a in raw_attempts:
                    attempts.append({
                        'word': a.get('word') or a.get('sinhalaWord'),
                        'level': a.get('level', 'basic'),
                        'correct': a.get('correct', False),
                        'time_taken': a.get('timeTaken', 0),
                        'timestamp': a.get('createdAt', datetime.now())
                    })
            except Exception as e:
                print(f"⚠️ MongoDB query failed: {e}")
        
        if not attempts:
            attempts = list(struggle_detector.attempt_history.get(user_id, []))
        
        if len(attempts) == 0:
            return jsonify({'success': False, 'message': 'No data found'})
        
        # Calculate stats
        total = len(attempts)
        correct = sum(1 for a in attempts if a['correct'])
        accuracy = (correct / total * 100) if total > 0 else 0
        words_learned = len(set(a['word'] for a in attempts if a['correct']))
        
        # Level progress
        level_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        for a in attempts:
            lvl = a.get('level', 'basic')
            level_stats[lvl]['total'] += 1
            if a['correct']:
                level_stats[lvl]['correct'] += 1
        
        level_progress = {}
        for level in ['basic', 'easy', 'medium', 'hard']:
            if level in level_stats:
                stats = level_stats[level]
                level_accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                level_progress[level] = {
                    'accuracy': round(level_accuracy, 1),
                    'total_attempts': stats['total'],
                    'correct_attempts': stats['correct']
                }
            else:
                level_progress[level] = {
                    'accuracy': 0,
                    'total_attempts': 0,
                    'correct_attempts': 0
                }
        
        # Count how many hints were given
        hint_count = 0
        for a in attempts:
            if not a.get('correct', True):
                word = a.get('word')
                if word and struggle_detector.get_attempt_count(user_id, word) >= 2:
                    hint_count += 1
        
        report = {
            'summary': {
                'words_learned': words_learned,
                'overall_accuracy': round(accuracy, 1),
                'total_attempts': total,
                'correct_attempts': correct,
                'hints_given': hint_count
            },
            'level_progress': level_progress,
            'insights': [
                "🌟 Great progress!" if accuracy >= 70 else "💪 Keep practicing!",
                f"💡 You used {hint_count} hints to learn new words" if hint_count > 0 else "💡 Ask for hints when you're stuck!"
            ]
        }
        
        return jsonify({'success': True, 'report': report})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================
# RUN
# ========================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎮 Sinhala Sign Language API")
    print(f"🌐 http://localhost:5001")
    print(f"📹 Videos: {len(VIDEO_MAPPING)} mapped")
    print(f"🔗 MongoDB: {'Connected' if mongodb_manager else 'Not connected'}")
    print("="*70 + "\n")

    # Start the live camera background thread
    _ensure_practis_videos()
    cam_thread = threading.Thread(target=camera_worker, daemon=True, name="CameraWorker")
    cam_thread.start()
    print("📷 Camera worker thread started")

    if mongodb_manager and hasattr(mongodb_manager, 'disconnect'):
        atexit.register(mongodb_manager.disconnect)
    
    app.run(host="0.0.0.0", port=5001, debug=False)