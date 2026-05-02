import os  
import pickle
import regex
import torch
import torch.nn as nn
import glob
import time
import threading
import cv2
import numpy as np
import random
import json
import sys
import io
import atexit
import hashlib
import importlib.util
import requests
import shlex
import shutil
from datetime import datetime
from collections import defaultdict, deque
from flask import Flask, request, jsonify, send_file, render_template, Response, send_from_directory
from flask_cors import CORS
from contextlib import contextmanager
from google import genai
from dotenv import load_dotenv

# Fix Unicode encoding for Windows consoles BEFORE any emoji prints.
if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

# ==============================================================================
# 🛠️ GLOBAL CONFIGURATION & SETUP
# ==============================================================================
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_BASE_DIR)
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")

# Initialize Flask App
app = Flask(
    __name__,
    template_folder=os.path.join(_BASE_DIR, "templates"),
    static_folder=os.path.join(_BASE_DIR, "static"),
)

# CORS Configuration
CORS(app, resources={
    r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["GET", "POST", "OPTIONS"]},
    r"/start_training": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/student_turn": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/stop_training": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/status": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["GET", "OPTIONS"]},
    r"/practice_video/*": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["GET", "OPTIONS"]},
    r"/video_feed": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["GET", "OPTIONS"]}
})

# MongoDB integration
try:
    from core.database.mongodb_integration import mongodb_manager
    print("✅ MongoDB integration loaded")
except Exception as e:
    print(f"⚠️ MongoDB integration failed: {e}")
    mongodb_manager = None

# ==============================================================================
# 👄 SECTION 1: LIP READING COMPONENT
# ==============================================================================

# --- Configuration ---
_LIP_READING_SOURCE_DIR = os.path.join(_BASE_DIR, "lip-reading")
_LIP_READING_LOCAL_DIR = _BASE_DIR
_LIP_READING_PRACTIS_DIR = os.path.join(_BASE_DIR, "practis_letters")
_LIP_READING_ROOT_PRACTIS_DIR = os.path.join(_BASE_DIR, "practis_letters")

LETTER_CONFIDENCE_INDEX = {
    "Letter A": 0, "Letter B": 1, "Letter C": 2,
    "Letter D": 3, "Letter E": 4, "Letter F": 5,
    "Letter G": 6, "Letter H": 7, "Letter I": 8,
}

LETTER_DISPLAY_MAP = {
    "Letter A": "Letter - \u0d85",
    "Letter B": "Letter - \u0d86",
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

DURATION_FRAMES = 135
OUTPUT_VIDEO = os.path.join(_LIP_READING_LOCAL_DIR, "output.mp4")

# --- State Management ---
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

# --- Internal Helpers ---
def _ensure_practis_videos():
    os.makedirs(_LIP_READING_PRACTIS_DIR, exist_ok=True)
    os.makedirs(_LIP_READING_ROOT_PRACTIS_DIR, exist_ok=True)
    source_practis = os.path.join(_LIP_READING_SOURCE_DIR, "practis_letters")
    if os.path.isdir(source_practis):
        for video_file in ["L1.mp4", "L2.mp4", "L3.mp4", "L4.mp4", "L5.mp4", "L6.mp4", "L7.mp4", "L8.mp4", "L9.mp4"]:
            src = os.path.join(source_practis, video_file)
            for dst_dir in (_LIP_READING_PRACTIS_DIR, _LIP_READING_ROOT_PRACTIS_DIR):
                dst = os.path.join(dst_dir, video_file)
                if os.path.exists(src) and not os.path.exists(dst):
                    try: shutil.copy2(src, dst)
                    except Exception: pass

def _resolve_practice_video_path(letter_key):
    video_rel = LETTER_VIDEO_MAP.get(letter_key)
    if not video_rel: return None
    filename = os.path.basename(video_rel)
    for candidate in [os.path.join(_LIP_READING_ROOT_PRACTIS_DIR, filename), os.path.join(_LIP_READING_PRACTIS_DIR, filename)]:
        if os.path.exists(candidate): return candidate
    return None

def _make_placeholder(text="Camera Starting..."):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (20, 30, 60)
    cv2.putText(img, text, (60, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (86, 208, 255), 2)
    _, jpeg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return jpeg.tobytes()

_PLACEHOLDER = _make_placeholder()

# --- Module Loading ---
try:
    from feture_extract import get_detels as lip_get_detels
    from Predict_realtime import predict_video as lip_predict_video
except ImportError:
    def lip_get_detels(img, anotation=True): return img, img, None
    def lip_predict_video(video_path): return [0, 0, 0, 0]

# --- Camera Engine ---
def _try_open_camera(index, backend_name, backend_flag):
    if backend_flag is None: cap = cv2.VideoCapture(index)
    else: cap = cv2.VideoCapture(index, backend_flag)
    if not cap.isOpened():
        cap.release()
        return None, f"{backend_name} idx={index}: not opened"
    max_attempts = 100
    for attempt in range(max_attempts):
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.06); continue
        mean_val, std_val = float(np.mean(frame)), float(np.std(frame))
        if mean_val >= 2.0 or std_val >= 2.0: break
        time.sleep(0.06)
    return cap, None

def _build_camera_candidates():
    p_idx = os.environ.get("LIP_CAMERA_INDEX")
    indices = [int(p_idx)] if p_idx else []
    for i in [0, 1, 2, 3, 4]: 
        if i not in indices: indices.append(i)
    backends = [("DSHOW", cv2.CAP_DSHOW), ("AUTO", None), ("MSMF", cv2.CAP_MSMF)]
    candidates = []
    p_idx_val = indices[0]
    for b_name, b_flag in backends: candidates.append((p_idx_val, b_name, b_flag))
    for idx in indices[1:]:
        for b_name, b_flag in backends: candidates.append((idx, b_name, b_flag))
    return candidates

def _open_best_camera(start_offset=0):
    candidates = _build_camera_candidates()
    total = len(candidates)
    for i in range(total):
        idx, b_name, b_flag = candidates[(start_offset + i) % total]
        cap, _ = _try_open_camera(idx, b_name, b_flag)
        if cap is not None: return cap, [], (idx, b_name)
    return None, [], None

def camera_worker():
    reopen_round = 0
    while True:
        cap, _, opened = _open_best_camera(start_offset=reopen_round)
        if cap is None:
            with state_lock: state["camera_frame"] = _make_placeholder("No Camera Found")
            time.sleep(2.0); reopen_round += 1; continue
        idx, b_name = opened
        time.sleep(1.0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps_out = cap.get(cv2.CAP_PROP_FPS) or 30.0
        missed_reads, black_streak = 0, 0
        while True:
            ret, cv_img = cap.read()
            if not ret or cv_img is None:
                missed_reads += 1
                if missed_reads >= 30: break
                time.sleep(0.05); continue
            missed_reads = 0
            mean_val, std_val = float(np.mean(cv_img)), float(np.std(cv_img))
            if mean_val < 2.0 and std_val < 2.0:
                black_streak += 1
            else: black_streak = 0
            if black_streak >= 200: break
            try: org_image, annotated, _ = lip_get_detels(cv_img, anotation=True)
            except Exception: org_image, annotated = cv_img.copy(), cv_img.copy()
            with state_lock: phase = state["phase"]
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
                        vw_holder["writer"].release(); vw_holder["writer"] = None; vw_holder["frames"] = 0
                        with state_lock: 
                            state["phase"] = "analyzing"
                            sel = state["selected_letter"]
                        threading.Thread(target=run_prediction, args=(sel,), daemon=True).start()
            elif phase == "countdown":
                with state_lock: cd = state["countdown_value"]
                cv2.putText(annotated, f"Get Ready! {cd}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 200, 0), 3)
            elif phase == "analyzing":
                cv2.putText(annotated, "Analyzing...", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (86, 208, 255), 3)
            _, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 72])
            with state_lock: state["camera_frame"] = jpeg.tobytes()
            time.sleep(0.01)
        cap.release(); reopen_round += 1; time.sleep(0.4)

# --- Prediction Logic ---
def run_countdown():
    for i in range(5, 0, -1):
        with state_lock:
            if state["phase"] != "countdown": return
            state["countdown_value"] = i
        time.sleep(1)
    with state_lock:
        if state["phase"] != "countdown": return
        state["phase"] = "recording"
        state["countdown_value"] = 0
    with vw_lock:
        if vw_holder["writer"]: vw_holder["writer"].release()
        vw_holder["writer"] = None; vw_holder["frames"] = 0

def run_prediction(selected_letter):
    time.sleep(5)
    if not os.path.exists(OUTPUT_VIDEO):
        with state_lock: state["result_label"], state["phase"] = "Recording failed", "result"
        return
    try:
        result = lip_predict_video(OUTPUT_VIDEO)
        arr = result[3][0] if result[0] == 1 else None
        if arr is not None:
            idx = LETTER_CONFIDENCE_INDEX.get(selected_letter, 0)
            conf = round(float(arr[idx]) * 100, 2)
            ok = conf > 30
            lbl = "GOOD JOB!" if ok else "Try Again"
        else: conf, ok, lbl = 0.0, False, "Prediction error"
    except Exception: conf, ok, lbl = 0.0, False, "Prediction unavailable"
    with state_lock:
        state.update({"result_label": lbl, "result_confidence": conf, "result_ok": ok, "phase": "result"})

# --- Lip Reading API Endpoints ---
@app.route("/")
def lip_reading_home():
    return render_template("index.html", letters=list(LETTER_DISPLAY_MAP.items()))

@app.route("/video_feed")
def video_feed():
    def gen_frames():
        while True:
            with state_lock: frame = state["camera_frame"]
            img_bytes = frame if frame else _PLACEHOLDER
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n' b'Content-Length: ' + f"{len(img_bytes)}".encode() + b'\r\n' b'\r\n' + img_bytes + b'\r\n')
            time.sleep(0.033)
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/practice_video/<letter_key>")
def practice_video(letter_key):
    v_path = _resolve_practice_video_path(letter_key.replace("_", " "))
    if not v_path: return "Not found", 404
    return send_file(v_path, mimetype="video/mp4", as_attachment=False, conditional=True)

@app.route("/start_training", methods=["POST"])
def start_training():
    data = request.get_json(force=True)
    letter = data.get("letter")
    if not letter or letter not in LETTER_VIDEO_MAP: return jsonify({"ok": False, "error": "Invalid letter"})
    with state_lock: state.update({"selected_letter": letter, "phase": "watching", "result_label": "", "result_confidence": 0.0, "result_ok": False})
    return jsonify({"ok": True, "display": LETTER_DISPLAY_MAP.get(letter, letter)})

@app.route("/student_turn", methods=["POST"])
def student_turn():
    with state_lock: state.update({"phase": "countdown", "countdown_value": 5})
    threading.Thread(target=run_countdown, daemon=True).start()
    return jsonify({"ok": True})

@app.route("/stop_training", methods=["POST"])
def stop_training():
    with vw_lock:
        if vw_holder["writer"]: vw_holder["writer"].release()
        vw_holder.update({"writer": None, "frames": 0})
    with state_lock: state.update({"selected_letter": None, "phase": "idle", "countdown_value": 5, "result_label": "", "result_confidence": 0.0, "result_ok": False})
    return jsonify({"ok": True})

@app.route("/status")
def get_status():
    with state_lock:
        return jsonify({
            "phase": state["phase"], "countdown": state["countdown_value"],
            "result_label": state["result_label"], "result_confidence": state["result_confidence"],
            "result_ok": state["result_ok"], "selected_letter": state["selected_letter"],
            "display_letter": LETTER_DISPLAY_MAP.get(state["selected_letter"], ""),
        })

# ==============================================================================
# ✨ SECTION 2: TEXT TO SSL TRANSLATOR
# ==============================================================================

# --- Path Config ---
MODEL_DIR = os.path.join(_BASE_DIR, "text-to-sign", "SSL_model")
VIDEO_DIR = os.path.join(_BASE_DIR, "Dataset - Original")

# --- Video Mapping Logic ---
def build_video_mapping():
    video_map = {}
    if not os.path.exists(VIDEO_DIR): return video_map
    for root, _, files in os.walk(VIDEO_DIR):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.webm', '.mkv')):
                base = os.path.splitext(file)[0]
                key = base.split('_')[0].lower() if '_' in base else base.lower()
                if key not in video_map:
                    video_map[key] = {'filename': file, 'full_path': os.path.join(root, file)}
    return video_map

# Load Translator Metadata
try:
    with open(os.path.join(MODEL_DIR, "model_ssl.pkl"), 'rb') as f:
        metadata = pickle.load(f)
    label_to_english = metadata['label_to_english']
    level_words = metadata['level_words']
    level_indices = metadata['level_indices']
    input_dim, hidden_dim, num_classes = metadata['input_dim'], metadata['hidden_dim'], metadata['num_classes']
except Exception:
    label_to_english, level_words = {}, {'basic': []}
    input_dim, hidden_dim, num_classes = 128, 256, 100

VIDEO_MAPPING = build_video_mapping()
for key, v_info in VIDEO_MAPPING.items():
    for sinhala, english in label_to_english.items():
        if english.lower() == key: v_info['sinhala_word'] = sinhala; break

def find_video_for_word(sinhala_word):
    english = label_to_english.get(sinhala_word, '').lower()
    if english in VIDEO_MAPPING: return english
    if sinhala_word.lower() in VIDEO_MAPPING: return sinhala_word.lower()
    for key in VIDEO_MAPPING.keys():
        if english and (key.startswith(english[:3]) or english.startswith(key[:3])): return key
    return None

# --- Translator API ---
@app.route('/api/videos/<video_key>', methods=['GET'])
def serve_video(video_key):
    video_key = video_key.lower().strip()
    if video_key not in VIDEO_MAPPING: return jsonify({'error': 'Video not found'}), 404
    f_path = VIDEO_MAPPING[video_key]['full_path']
    ext = os.path.splitext(f_path)[1].lower()
    mimetype = {'.mp4': 'video/mp4', '.webm': 'video/webm'}.get(ext, 'video/mp4')
    return send_file(f_path, mimetype=mimetype)

# ==============================================================================
# 🎮 SECTION 3: GAME & AI HINTS COMPONENT
# ==============================================================================

# --- AI Hint System ---
struggle_detector = type('SD', (), {'attempt_history': defaultdict(lambda: deque(maxlen=20)), 'record_attempt': lambda s, u, w, l, c, t: s.attempt_history[u].append({'word': w, 'level': l, 'correct': c}), 'get_attempt_count': lambda s, u, w: sum(1 for a in s.attempt_history[u] if a['word'] == word)})()
ai_hint_cache = {}

def generate_ai_hint(user_id, sinhala_word, english_word, attempt_count, recent_attempts, level='basic'):
    cache_key = f"{user_id}:{sinhala_word}:{attempt_count}"
    if cache_key in ai_hint_cache: return {'hint': ai_hint_cache[cache_key]}
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return {'hint': f"🔎 Hint: This word is about {english_word.lower()}"}
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"Secret word: '{sinhala_word}' ({english_word}). Give one short clue (max 8 words) without saying the word."
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = resp.text.strip() if hasattr(resp, 'text') else str(resp).strip()
        hint = f"🔎 Hint: {text.split('Hint:')[-1].strip()}"
        ai_hint_cache[cache_key] = hint
        return {'hint': hint}
    except Exception: return {'hint': f"🔎 Hint: It means {english_word.lower()}"}

# --- Game Engine Model ---
class LSTMPuzzleModel(nn.Module):
    def __init__(self, i_dim, h_dim, n_cls):
        super().__init__()
        self.lstm = nn.LSTM(i_dim, h_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(nn.Linear(h_dim*2, 128), nn.ReLU(), nn.Linear(128, n_cls))
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

model_game = LSTMPuzzleModel(input_dim, hidden_dim, num_classes)
try:
    model_game.load_state_dict(torch.load(os.path.join(MODEL_DIR, "sinhala_sign_model.pth"), map_location='cpu'))
    model_game.eval()
except Exception: pass

user_game_states = {}
class GameState:
    def __init__(self, u_id, lvl): self.user_id, self.level, self.used_words, self.round, self.max_rounds = u_id, lvl, [], 0, 10
    def add_used_word(self, w): (w not in self.used_words) and self.used_words.append(w)
    def get_available_words(self, all_w): return [w for w in all_w if w not in self.used_words]

# --- Game API Endpoints ---
@app.route('/api/puzzle/generate', methods=['POST'])
def generate_puzzle():
    data = request.json
    u_id, lvl = data.get('user_id', 'default'), data.get('level', 'basic')
    key = f"{u_id}_{lvl}"
    if key not in user_game_states: user_game_states[key] = GameState(u_id, lvl)
    gs = user_game_states[key]
    gs.round += 1
    w_list = [w for w in level_words.get(lvl, []) if find_video_for_word(w)]
    avail = gs.get_available_words(w_list)
    if len(avail) < 4: gs.used_words, avail = [], w_list
    target = random.choice(avail); gs.add_used_word(target)
    v_key = find_video_for_word(target)
    opts = random.sample([w for w in avail if w != target], 3) + [target]
    random.shuffle(opts)
    return jsonify({'success': True, 'target_word': target, 'video_url': f"/api/videos/{v_key}", 'options': [{'word': w, 'english': label_to_english.get(w, '')} for w in opts], 'round': gs.round})

@app.route('/api/attempt', methods=['POST'])
def record_attempt():
    data = request.json
    u_id, word, correct = data.get('user_id', 'default'), data.get('word'), data.get('correct', False)
    if mongodb_manager: 
        mongodb_manager.save_game_attempt({'userId': u_id, 'word': word, 'correct': correct, 'game': 'puzzle'})
    # Hint logic
    hint_data = None
    if not correct:
        hint_data = generate_ai_hint(u_id, word, label_to_english.get(word, ''), 2, [], data.get('level'))
    return jsonify({'success': True, 'hint': hint_data.get('hint') if hint_data else None})

@app.route('/api/ai/progress-report', methods=['POST'])
def get_progress_report():
    u_id = request.json.get('user_id', 'default')
    # Mock report for logic preservation
    return jsonify({'success': True, 'report': {'summary': {'words_learned': 5, 'overall_accuracy': 80}}})

# ==============================================================================
# 🚀 SECTION 4: SERVER RUN
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "="*70 + "\n🚀 SignBridge Integrated API\n" + "="*70)
    _ensure_practis_videos()
    threading.Thread(target=camera_worker, daemon=True, name="CameraWorker").start()
    if mongodb_manager and hasattr(mongodb_manager, 'disconnect'): atexit.register(mongodb_manager.disconnect)
    app.run(host="0.0.0.0", port=5001, debug=False)