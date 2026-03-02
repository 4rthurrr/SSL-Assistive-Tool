# ═══════════════════════════════════════════════════════════════════════════════
# SSL SENTENCE GAME API - FLASK BACKEND (v8 compatible)
# ═══════════════════════════════════════════════════════════════════════════════

import os
import sys
import io
import json
import pickle
import random
import uuid
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

import numpy as np
import cv2
from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from flask_session import Session

# Fix Unicode encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ========================
# CONFIGURATION
# ========================
class Config:
    # Paths - UPDATE THESE FOR YOUR SYSTEM
    MODEL_DIR = r"/content/drive/MyDrive/SSL_model_v8"  # Colab path
    # For local Windows, use:
    # MODEL_DIR = r"D:\Downloads-D\Game_V2\Game_V2\Backend\SSL_model"
    
    VIDEO_OUT = os.path.join(MODEL_DIR, "sentence_videos")
    SECRET_KEY = 'ssl_game_secret_key_2024_v8'
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_FILE_DIR = './flask_sessions'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Game settings
    QUESTIONS_PER_LEVEL = 8
    MAX_ATTEMPTS = 5
    POINTS_PER_CORRECT = 10
    
    # Model params (should match training)
    WORD_EMBED_DIM = 128
    TRANSFORMER_DIM = 128
    N_HEADS = 4
    N_TF_LAYERS = 3
    DROPOUT = 0.3

# Create necessary directories
os.makedirs(Config.MODEL_DIR, exist_ok=True)
os.makedirs(Config.VIDEO_OUT, exist_ok=True)
os.makedirs(Config.SESSION_FILE_DIR, exist_ok=True)

# ========================
# INITIALIZE FLASK
# ========================
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type"]
    }
})

# Configure server-side sessions
Session(app)

print("\n" + "="*70)
print("🎮 SSL SENTENCE GAME API - V8 BACKEND")
print("="*70)
print(f"📁 Model directory: {Config.MODEL_DIR}")
print(f"📁 Video directory: {Config.VIDEO_OUT}")
print(f"🔌 CORS enabled for localhost:3000, 5173")

# ========================
# LOAD MODEL & METADATA
# ========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🖥 Device: {device}")

# Import torch (do this after printing to see device)
import torch
import torch.nn as nn
import torch.nn.functional as F

# ========================
# MODEL DEFINITIONS (must match training)
# ========================
class WordLSTM(nn.Module):
    def __init__(self, input_dim, hidden, n_cls, n_layers=3, dropout=0.3):
        super().__init__()
        self.bn = nn.BatchNorm1d(input_dim)
        self.lstm = nn.LSTM(input_dim, hidden, n_layers, batch_first=True,
                           dropout=dropout, bidirectional=True)
        self.attn = nn.Linear(hidden * 2, 1)
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden * 2, n_cls)
        self.embed_fc = nn.Linear(hidden * 2, Config.WORD_EMBED_DIM)

    def _attended(self, out):
        w = torch.softmax(self.attn(out), dim=1)
        ctx = (w * out).sum(1)
        return ctx

    def forward(self, x):
        B, T, D = x.shape
        xf = x.reshape(B * T, D)
        xf = self.bn(xf).reshape(B, T, D)
        out, _ = self.lstm(xf)
        ctx = self._attended(out)
        return self.fc(self.drop(ctx))

    def get_embedding(self, x):
        B, T, D = x.shape
        xf = x.reshape(B * T, D)
        xf = self.bn(xf).reshape(B, T, D)
        out, _ = self.lstm(xf)
        ctx = self._attended(out)
        return F.relu(self.embed_fc(ctx))


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=20):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                            (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]


class SentenceOrderingModel(nn.Module):
    def __init__(self, embed_dim, d_model, nhead, nlayers, max_words, dropout=0.1):
        super().__init__()
        self.proj = nn.Linear(embed_dim, d_model)
        self.pe = PositionalEncoding(d_model, max_len=max_words + 2)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model, nhead, dim_feedforward=d_model * 4,
            dropout=dropout, batch_first=True, activation='gelu'
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, nlayers)
        self.head = nn.Linear(d_model, max_words)
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        x = F.gelu(self.proj(x))
        x = self.pe(x)
        x = self.transformer(x)
        return self.head(self.drop(x))


# ========================
# SSL GRAMMAR ENGINE (from v8)
# ========================
class SSLGrammar:
    """SSL grammar rules with SOV order (matches v8)"""
    
    TIME_WORDS = {
        "අද", "ඊයේ", "හෙට", "දැන්", "උදේ", "හවස", "රෑ", "ආයෙත්",
        "සඳුදා", "අඟහරුවාදා", "බ්‍රහස්පතින්දා"
    }
    
    SUBJECTS = {
        "මම", "ඔයා", "ඔහු", "ඇය", "අපි", "ඔවුන්",
        "අම්මා", "තාත්තා", "දරුවා", "අයියා", "අක්කා",
        "වෛද්‍යවරයා", "ගුරුවරයා", "සීයා", "මිනිසා",
        "ළමයින්", "දියණිය", "පුතා", "පවුල", "පූසා", 
        "අලියා", "බබා", "මිනිසුන්"
    }
    
    DATIVE = {
        "දරුවාට", "අම්මාට", "තාත්තාට", "වෛද්‍යවරයාට", "ගුරුවරයාට",
        "මට", "ඔයාට", "අපට", "ගෙදරට", "රෝහලට", "පාසලට",
        "සාප්පුවට", "වෙළඳපොලට", "වැඩට", "පාසලේ", "ගෙදරේ"
    }
    
    OBJECTS = {
        "බත්", "වතුර", "කිරි", "කෑම", "පොත", "බෙහෙත්", 
        "මුදල්", "කාරේ", "බෑගය", "පරිගණකය", "දුරකථනය",
        "බයිසිකලය", "බෝට්ටුව", "ඇඳුම", "ඇඳ", "ගෙදර", 
        "රෝහල", "පාසල", "සාප්පු"
    }
    
    VERBS = {
        # Present
        "කනවා", "බොනවා", "ඇවිදිනවා", "දුවනවා", "නිදාගන්නවා",
        "සෙල්ලම් කරනවා", "නටනවා", "අඬනවා", "හිනාවෙනවා", 
        "පනිනවා", "ලියනවා", "කියවනවා", "බලනවා", "හිතනවා",
        "යනවා", "එනවා", "උයනවා", "උගන්වනවා", "දෙනවා",
        "උදව් කරනවා", "හමුවෙනවා", "ගන්නවා", "විකුණනවා",
        "අරිනවා", "නවත්තනවා", "තෝරනවා", "අඳිනවා",
        "රැගෙනයනවා", "දන්නවා", "අහනවා", "කියනවා",
        "වැඩ කරනවා", "නානවා", "ගෙනෙනවා",
        # Past
        "ගියා", "ආවා", "කෑවා", "බිව්වා", "ලිව්වා", "දිව්වා",
        "උයලා", "දුන්නා", "උදව් කළා", "ඉගැන්නුවා", "ගත්තා",
        "නිදාගත්තා", "නැටුවා", "සෙල්ලම් කළා", "වැඩ කළා", "කියෙව්වා",
        # Hortative
        "යමු", "කමු", "බොමු", "නිදාගමු", "සෙල්ලම් කරමු",
        "කියවමු", "එමු"
    }
    
    STATES = {
        "බඩගිනියි", "පිපාසයි", "සතුටුයි", "මහන්සියි",
        "හොඳයි", "ලස්සනයි", "නිරෝගීයි", "ලොකුයි",
        "පුංචියි", "හරියි", "සීතලයි"
    }
    
    ADJECTIVES = {"හොඳ", "ලස්සන", "ලොකු", "පුංචි"}
    QUESTION_PARTS = {"ද"}
    QUESTION_WORDS = {"මොකද", "කොහෙද", "කවදාද", "ඇයි"}

    def tag(self, word):
        """Classify word by grammatical role"""
        if word in self.TIME_WORDS: return "TIME"
        if word in self.SUBJECTS: return "SUBJ"
        if word in self.DATIVE: return "DAT"
        if word in self.VERBS: return "VERB"
        if word in self.STATES: return "STATE"
        if word in self.QUESTION_PARTS: return "Q"
        if word in self.QUESTION_WORDS: return "WH"
        if word in self.ADJECTIVES: return "ADJ"
        if word in self.OBJECTS: return "OBJ"
        return "OBJ"  # Default

    def order(self, words):
        """Return words in correct SSL order: TIME → SUBJ → ADJ → DAT → OBJ → WH → VERB → STATE → Q"""
        buckets = defaultdict(list)
        for w in words:
            buckets[self.tag(w)].append(w)
        
        ordered = []
        ordered.extend(buckets["TIME"])
        ordered.extend(buckets["SUBJ"])
        ordered.extend(buckets["ADJ"])
        ordered.extend(buckets["DAT"])
        ordered.extend(buckets["OBJ"])
        ordered.extend(buckets["WH"])
        ordered.extend(buckets["VERB"])
        ordered.extend(buckets["STATE"])
        ordered.extend(buckets["Q"])
        
        return ordered if ordered else words

    def validate(self, user_order, correct_order):
        """Validate user's answer against correct order"""
        matched = sum(a == b for a, b in zip(user_order, correct_order))
        total = len(correct_order)
        score = matched / total if total else 0
        
        wrong = []
        for i, (u, c) in enumerate(zip(user_order, correct_order)):
            if u != c:
                wrong.append({
                    "position": i + 1,
                    "user_word": u,
                    "correct_word": c
                })
        
        return {
            "correct": user_order == correct_order,
            "score": round(score, 2),
            "matched": matched,
            "total": total,
            "wrong_positions": wrong,
            "emoji": "🎉" if score == 1 else ("👍" if score >= 0.6 else "💪"),
            "message": f"{matched}/{total} words correct"
        }


# ========================
# LOAD METADATA AND MODELS
# ========================
def load_metadata():
    """Load metadata from pickle file"""
    metadata_path = os.path.join(Config.MODEL_DIR, "metadata.pkl")
    sentences_path = os.path.join(Config.MODEL_DIR, "sentences.json")
    
    metadata = {}
    sentence_data = {"level_1": [], "level_2": [], "level_3": []}
    
    try:
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            print(f"✅ Loaded metadata: {list(metadata.keys())}")
        else:
            print(f"⚠️ Metadata not found at: {metadata_path}")
    except Exception as e:
        print(f"❌ Error loading metadata: {e}")
    
    try:
        if os.path.exists(sentences_path):
            with open(sentences_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Handle different possible structures
                if isinstance(loaded, dict):
                    if "level_1" in loaded:
                        sentence_data = loaded
                    elif "basic" in loaded:
                        sentence_data["level_1"] = loaded.get("basic", [])
                        sentence_data["level_2"] = loaded.get("daily", [])
                        sentence_data["level_3"] = loaded.get("complex", [])
                    else:
                        sentence_data["level_1"] = loaded.get("level_1", [])
                        sentence_data["level_2"] = loaded.get("level_2", [])
                        sentence_data["level_3"] = loaded.get("level_3", [])
                elif isinstance(loaded, list):
                    sentence_data["level_1"] = loaded[:len(loaded)//3]
                    sentence_data["level_2"] = loaded[len(loaded)//3:2*len(loaded)//3]
                    sentence_data["level_3"] = loaded[2*len(loaded)//3:]
            
            print(f"✅ Loaded sentences:")
            for level, sents in sentence_data.items():
                print(f"   - {level}: {len(sents)} sentences")
        else:
            print(f"⚠️ Sentences not found at: {sentences_path}")
            # Create fallback sentences
            sentence_data = create_fallback_sentences()
            
    except Exception as e:
        print(f"❌ Error loading sentences: {e}")
        sentence_data = create_fallback_sentences()
    
    return metadata, sentence_data


def create_fallback_sentences():
    """Create fallback sentences if JSON loading fails"""
    print("📝 Creating fallback sentences...")
    
    level_1 = [
        {"sinhala": "දරුවා ඇවිදිනවා", "words": ["දරුවා", "ඇවිදිනවා"], "english": "Child walks"},
        {"sinhala": "අම්මා එනවා", "words": ["අම්මා", "එනවා"], "english": "Mother comes"},
        {"sinhala": "මම කනවා", "words": ["මම", "කනවා"], "english": "I eat"},
        {"sinhala": "බබා නිදාගන්නවා", "words": ["බබා", "නිදාගන්නවා"], "english": "Baby sleeps"},
        {"sinhala": "පූසා දුවනවා", "words": ["පූසා", "දුවනවා"], "english": "Cat runs"},
        {"sinhala": "අපි යනවා", "words": ["අපි", "යනවා"], "english": "We go"},
        {"sinhala": "ඔයා එනවා", "words": ["ඔයා", "එනවා"], "english": "You come"},
        {"sinhala": "සීයා බලනවා", "words": ["සීයා", "බලනවා"], "english": "Grandfather looks"},
    ]
    
    level_2 = [
        {"sinhala": "මම බත් කනවා", "words": ["මම", "බත්", "කනවා"], "english": "I eat rice"},
        {"sinhala": "අම්මා වතුර බොනවා", "words": ["අම්මා", "වතුර", "බොනවා"], "english": "Mother drinks water"},
        {"sinhala": "දරුවා පොත කියවනවා", "words": ["දරුවා", "පොත", "කියවනවා"], "english": "Child reads a book"},
        {"sinhala": "මම ගෙදර යනවා", "words": ["මම", "ගෙදර", "යනවා"], "english": "I go home"},
        {"sinhala": "දරුවා පාසලට යනවා", "words": ["දරුවා", "පාසලට", "යනවා"], "english": "Child goes to school"},
        {"sinhala": "අම්මා කෑම උයනවා", "words": ["අම්මා", "කෑම", "උයනවා"], "english": "Mother cooks food"},
        {"sinhala": "මම බඩගිනියි", "words": ["මම", "බඩගිනියි"], "english": "I am hungry"},
        {"sinhala": "අම්මා ලස්සනයි", "words": ["අම්මා", "ලස්සනයි"], "english": "Mother is beautiful"},
    ]
    
    level_3 = [
        {"sinhala": "අද මම රෝහලට ගියා", "words": ["අද", "මම", "රෝහලට", "ගියා"], "english": "Today I went to hospital"},
        {"sinhala": "ඔයා බත් කනවාද", "words": ["ඔයා", "බත්", "කනවා", "ද"], "english": "Do you eat rice?"},
        {"sinhala": "අම්මා දරුවාට කිරි දෙනවා", "words": ["අම්මා", "දරුවාට", "කිරි", "දෙනවා"], "english": "Mother gives milk to child"},
        {"sinhala": "අපි පාසලට යමු", "words": ["අපි", "පාසලට", "යමු"], "english": "Let's go to school"},
        {"sinhala": "ඊයේ දරුවා පාසලට ගියා", "words": ["ඊයේ", "දරුවා", "පාසලට", "ගියා"], "english": "Yesterday child went to school"},
        {"sinhala": "වෛද්‍යවරයා දරුවාට උදව් කළා", "words": ["වෛද්‍යවරයා", "දරුවාට", "උදව්", "කළා"], "english": "Doctor helped child"},
        {"sinhala": "හෙට අපි සාප්පුවට යමු", "words": ["හෙට", "අපි", "සාප්පුවට", "යමු"], "english": "Tomorrow let's go to shop"},
        {"sinhala": "ඔයා කොහෙද යන්නේ", "words": ["ඔයා", "කොහෙද", "යන්නේ"], "english": "Where are you going?"},
    ]
    
    return {
        "level_1": level_1,
        "level_2": level_2,
        "level_3": level_3
    }


def load_models(metadata):
    """Load trained PyTorch models"""
    word_model = None
    sent_model = None
    
    try:
        # Get model parameters from metadata
        num_classes = metadata.get('num_classes', 0)
        input_dim = metadata.get('input_dim', 132)
        lstm_hidden = metadata.get('lstm_hidden', 256)
        max_words = metadata.get('max_words', 10)
        
        if num_classes > 0:
            # Initialize word model
            word_model = WordLSTM(
                input_dim=input_dim,
                hidden=lstm_hidden,
                n_cls=num_classes,
                n_layers=3,
                dropout=0.3
            ).to(device)
            
            # Load weights
            word_path = os.path.join(Config.MODEL_DIR, "word_model.pth")
            if os.path.exists(word_path):
                word_model.load_state_dict(
                    torch.load(word_path, map_location=device)
                )
                word_model.eval()
                print("✅ Word model loaded")
            else:
                print(f"⚠️ Word model not found at: {word_path}")
                word_model = None
            
            # Initialize sentence model
            sent_model = SentenceOrderingModel(
                embed_dim=Config.WORD_EMBED_DIM,
                d_model=Config.TRANSFORMER_DIM,
                nhead=Config.N_HEADS,
                nlayers=Config.N_TF_LAYERS,
                max_words=max_words,
                dropout=Config.DROPOUT
            ).to(device)
            
            # Load weights
            sent_path = os.path.join(Config.MODEL_DIR, "sentence_model.pth")
            if os.path.exists(sent_path):
                sent_model.load_state_dict(
                    torch.load(sent_path, map_location=device)
                )
                sent_model.eval()
                print("✅ Sentence model loaded")
            else:
                print(f"⚠️ Sentence model not found at: {sent_path}")
                sent_model = None
        
    except Exception as e:
        print(f"⚠️ Error loading models: {e}")
        word_model = None
        sent_model = None
    
    return word_model, sent_model


# Load everything
metadata, sentence_data = load_metadata()
word_model, sent_model = load_models(metadata)

# Create word to index mapping
all_words = set()
for level_sentences in sentence_data.values():
    for sent in level_sentences:
        all_words.update(sent.get('words', []))
word_list = sorted(list(all_words))
word_to_idx = {w: i for i, w in enumerate(word_list)}
print(f"📚 Loaded {len(word_list)} unique words for game")

# Initialize grammar engine
grammar = SSLGrammar()


# ========================
# VIDEO GENERATION
# ========================
def generate_sentence_videos():
    """Generate placeholder videos for sentences if they don't exist"""
    if not os.path.exists(Config.VIDEO_OUT):
        os.makedirs(Config.VIDEO_OUT)
        print(f"📁 Created video directory: {Config.VIDEO_OUT}")
    
    existing = list(Path(Config.VIDEO_OUT).glob("*.mp4"))
    expected_count = sum(len(sentence_data.get(level, [])) for level in sentence_data)
    
    if len(existing) >= expected_count:
        print(f"✅ Videos already exist: {len(existing)} files")
        return
    
    print(f"🎥 Generating {expected_count - len(existing)} missing sentence videos...")
    
    for level, sentences in sentence_data.items():
        for i, sent in enumerate(sentences[:Config.QUESTIONS_PER_LEVEL]):
            safe_name = sent['sinhala'].replace(' ', '_')[:40]
            out_path = os.path.join(Config.VIDEO_OUT, f"{level}_{i:02d}_{safe_name}.mp4")
            
            if not os.path.exists(out_path):
                try:
                    # Create a simple video with text
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(out_path, fourcc, 20.0, (640, 480))
                    
                    for _ in range(30):  # 1.5 seconds at 20 fps
                        frame = np.zeros((480, 640, 3), dtype=np.uint8)
                        # Add background
                        cv2.rectangle(frame, (0, 0), (640, 480), (40, 40, 40), -1)
                        
                        # Add Sinhala text
                        y_pos = 240
                        for word in sent['words']:
                            cv2.putText(frame, word, (50, y_pos), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                            y_pos += 40
                        
                        # Add English translation
                        cv2.putText(frame, sent['english'], (50, 400),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
                        
                        out.write(frame)
                    
                    out.release()
                    print(f"  ✅ Created: {os.path.basename(out_path)}")
                except Exception as e:
                    print(f"  ❌ Failed: {e}")


# Generate videos in background
def background_video_generation():
    time.sleep(2)  # Wait for server to start
    generate_sentence_videos()

video_thread = threading.Thread(target=background_video_generation, daemon=True)
video_thread.start()


# ========================
# GAME SESSION MANAGER
# ========================
class GameSession:
    """Manages a player's game session"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_level = None
        self.current_question_index = 0
        self.questions = []
        self.score = 0
        self.attempts = 0
        self.max_attempts = Config.MAX_ATTEMPTS
        self.game_over = False
        self.level_complete = False
        self.stars_earned = 0
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
    
    def update_activity(self):
        self.last_activity = datetime.now()
    
    def reset_attempts(self):
        self.attempts = 0
        self.game_over = False
    
    def increment_attempts(self):
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            self.game_over = True
        return self.game_over
    
    def add_score(self, points=Config.POINTS_PER_CORRECT):
        self.score += points
    
    def calculate_stars(self):
        """Calculate stars based on score (max 3)"""
        max_possible = len(self.questions) * Config.POINTS_PER_CORRECT
        if max_possible == 0:
            return 0
        percentage = (self.score / max_possible) * 100
        if percentage >= 90:
            return 3
        elif percentage >= 70:
            return 2
        elif percentage >= 50:
            return 1
        return 0


class GameEngine:
    """Main game engine"""
    
    def __init__(self, sentence_data, grammar, word_model=None, sent_model=None):
        self.sentence_data = sentence_data
        self.grammar = grammar
        self.word_model = word_model
        self.sent_model = sent_model
        self.sessions = {}  # user_id -> GameSession
        self.level_names = {
            "level_1": "🌱 Beginner",
            "level_2": "📘 Intermediate",
            "level_3": "🏆 Advanced"
        }
        self.level_descriptions = {
            "level_1": "Simple actions with family (2 words)",
            "level_2": "Eating, going, and describing (2-3 words)",
            "level_3": "Past tense, questions, and helping others (3-4 words)"
        }
    
    def get_or_create_session(self, user_id):
        """Get existing session or create new one"""
        if user_id not in self.sessions:
            self.sessions[user_id] = GameSession(user_id)
        return self.sessions[user_id]
    
    def get_available_levels(self):
        """Return metadata for all levels"""
        levels = {}
        for level_id, sentences in self.sentence_data.items():
            available = [s for s in sentences if s.get('words')]
            levels[level_id] = {
                "id": level_id,
                "name": self.level_names.get(level_id, level_id),
                "description": self.level_descriptions.get(level_id, ""),
                "question_count": min(len(available), Config.QUESTIONS_PER_LEVEL),
                "total_questions": len(available),
                "available": len(available) > 0
            }
        return levels
    
    def get_level_questions(self, level_id, count=Config.QUESTIONS_PER_LEVEL):
        """Get random questions for a level"""
        if level_id not in self.sentence_data:
            return []
        
        sentences = self.sentence_data[level_id]
        if not sentences:
            return []
        
        # Filter sentences that have words
        valid = [s for s in sentences if s.get('words')]
        if not valid:
            return []
        
        # Select random sentences
        selected = random.sample(valid, min(count, len(valid)))
        
        questions = []
        for i, sent in enumerate(selected):
            correct_words = sent['words'].copy()
            shuffled = correct_words.copy()
            random.shuffle(shuffled)
            
            # Add distractors if needed
            if len(shuffled) < 8:
                all_words = [w for s in valid for w in s['words']]
                other_words = list(set(all_words) - set(correct_words))
                if other_words:
                    distractors = random.sample(other_words, min(3, len(other_words)))
                    shuffled.extend(distractors)
                    random.shuffle(shuffled)
            
            # Generate video URL
            safe_name = sent['sinhala'].replace(' ', '_')[:40]
            video_filename = f"{level_id}_{i:02d}_{safe_name}.mp4"
            video_url = f"/api/sentence-video/{video_filename}"
            
            questions.append({
                "id": str(uuid.uuid4())[:8],
                "sinhala": sent['sinhala'],
                "sentence_sinhala": sent['sinhala'],
                "english": sent['english'],
                "sentence_english": sent['english'],
                "correct_order": correct_words,
                "shuffled_words": shuffled,
                "word_count": len(correct_words),
                "video_url": video_url,
                "video_filename": video_filename,
                "level": level_id
            })
        
        return questions
    
    def start_level(self, user_id, level_id):
        """Start a level for a user"""
        session = self.get_or_create_session(user_id)
        
        # Validate level exists
        if level_id not in self.sentence_data:
            return {"success": False, "error": f"Level {level_id} not found"}
        
        # Get questions
        questions = self.get_level_questions(level_id)
        if not questions:
            return {"success": False, "error": f"No questions available for {level_id}"}
        
        # Initialize session
        session.current_level = level_id
        session.current_question_index = 0
        session.score = 0
        session.attempts = 0
        session.game_over = False
        session.level_complete = False
        session.questions = questions
        session.update_activity()
        
        first_question = questions[0] if questions else None
        
        return {
            "success": True,
            "level": level_id,
            "level_name": self.level_names.get(level_id, level_id),
            "total_questions": len(questions),
            "first_question": first_question
        }
    
    def get_current_question(self, user_id):
        """Get current question for user"""
        session = self.get_or_create_session(user_id)
        session.update_activity()
        
        if not session.questions or session.level_complete or session.game_over:
            return None
        
        if session.current_question_index >= len(session.questions):
            session.level_complete = True
            session.stars_earned = session.calculate_stars()
            return None
        
        question = session.questions[session.current_question_index]
        
        return {
            "question": question,
            "question_number": session.current_question_index + 1,
            "total_questions": len(session.questions),
            "score": session.score,
            "attempts": session.attempts,
            "max_attempts": session.max_attempts,
            "game_over": session.game_over,
            "level_complete": session.level_complete
        }
    
    def check_answer(self, user_id, user_order):
        """Check user's answer and update session"""
        session = self.get_or_create_session(user_id)
        session.update_activity()
        
        if session.game_over or session.level_complete:
            return {
                "success": False,
                "error": "Game over or level complete. Please start a new level."
            }
        
        if session.current_question_index >= len(session.questions):
            session.level_complete = True
            return {
                "success": False,
                "error": "No active question. Please start a new level."
            }
        
        current_q = session.questions[session.current_question_index]
        correct_order = current_q['correct_order']
        
        # Validate answer
        result = grammar.validate(user_order, correct_order)
        
        if result['correct']:
            # Correct answer
            session.add_score()
            session.current_question_index += 1
            session.reset_attempts()
            
            # Check if level complete
            if session.current_question_index >= len(session.questions):
                session.level_complete = True
                session.stars_earned = session.calculate_stars()
            
            return {
                "success": True,
                "correct": True,
                "result": result,
                "score": session.score,
                "next_question": session.current_question_index < len(session.questions),
                "level_complete": session.level_complete,
                "stars_earned": session.stars_earned if session.level_complete else None,
                "question_number": session.current_question_index + 1,
                "total_questions": len(session.questions)
            }
        else:
            # Wrong answer
            game_over = session.increment_attempts()
            
            return {
                "success": True,
                "correct": False,
                "result": result,
                "score": session.score,
                "attempts": session.attempts,
                "max_attempts": session.max_attempts,
                "game_over": game_over,
                "correct_answer": correct_order if game_over else None,
                "question_number": session.current_question_index + 1,
                "total_questions": len(session.questions)
            }
    
    def get_hint(self, user_id):
        """Get hint for current question"""
        session = self.get_or_create_session(user_id)
        session.update_activity()
        
        if session.game_over or session.level_complete:
            return None
        
        if session.current_question_index >= len(session.questions):
            return None
        
        current_q = session.questions[session.current_question_index]
        correct_order = current_q['correct_order']
        
        if not correct_order:
            return None
        
        # Provide hint based on progress
        if session.attempts == 0:
            return {
                "type": "first_word",
                "hint": f"First word should be: {correct_order[0]}",
                "first_word": correct_order[0]
            }
        elif session.attempts == 1:
            return {
                "type": "word_count",
                "hint": f"This sentence has {len(correct_order)} words",
                "word_count": len(correct_order)
            }
        elif session.attempts == 2:
            # Show first two words
            first_two = " → ".join(correct_order[:2])
            return {
                "type": "first_two",
                "hint": f"First two words: {first_two}",
                "first_two": correct_order[:2]
            }
        else:
            # Show whole sentence
            return {
                "type": "full_sentence",
                "hint": f"The correct order is: {' → '.join(correct_order)}",
                "correct_order": correct_order
            }
    
    def get_session_info(self, user_id):
        """Get current session info"""
        session = self.get_or_create_session(user_id)
        session.update_activity()
        
        return {
            "success": True,
            "score": session.score,
            "level": session.current_level,
            "level_name": self.level_names.get(session.current_level, ""),
            "question_index": session.current_question_index,
            "total_questions": len(session.questions),
            "attempts": session.attempts,
            "max_attempts": session.max_attempts,
            "game_over": session.game_over,
            "level_complete": session.level_complete,
            "stars_earned": session.stars_earned
        }
    
    def cleanup_old_sessions(self, max_age_hours=24):
        """Remove sessions older than max_age_hours"""
        now = datetime.now()
        to_delete = []
        for user_id, sess in self.sessions.items():
            if (now - sess.last_activity) > timedelta(hours=max_age_hours):
                to_delete.append(user_id)
        
        for user_id in to_delete:
            del self.sessions[user_id]
        
        if to_delete:
            print(f"🧹 Cleaned up {len(to_delete)} inactive sessions")


# Initialize game engine
game_engine = GameEngine(sentence_data, grammar, word_model, sent_model)
print("✅ Game engine initialized")


# ========================
# API ENDPOINTS
# ========================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'models_loaded': word_model is not None,
        'sentence_count': sum(len(s) for s in sentence_data.values()),
        'active_sessions': len(game_engine.sessions),
        'levels': game_engine.get_available_levels()
    })


@app.route('/api/levels', methods=['GET'])
def get_levels():
    """Get all available levels"""
    return jsonify({
        'success': True,
        'levels': game_engine.get_available_levels()
    })


@app.route('/api/start-level', methods=['POST'])
def start_level():
    """Start a new level"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id') or request.remote_addr
        level_id = data.get('level', 'level_1')
        
        result = game_engine.start_level(user_id, level_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in start_level: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/current-question', methods=['POST'])
def current_question():
    """Get current question for user"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id') or request.remote_addr
        
        question_data = game_engine.get_current_question(user_id)
        
        if question_data:
            return jsonify({
                'success': True,
                **question_data
            })
        else:
            # Check if level complete
            session = game_engine.get_or_create_session(user_id)
            if session.level_complete:
                return jsonify({
                    'success': True,
                    'level_complete': True,
                    'score': session.score,
                    'stars_earned': session.stars_earned
                })
            elif session.game_over:
                return jsonify({
                    'success': True,
                    'game_over': True,
                    'score': session.score
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No active game session'
                }), 404
        
    except Exception as e:
        print(f"❌ Error in current_question: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/check', methods=['POST'])
def check_answer():
    """Check user's answer"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id') or request.remote_addr
        user_order = data.get('user_order', [])
        
        if not user_order:
            return jsonify({'success': False, 'error': 'No answer provided'}), 400
        
        result = game_engine.check_answer(user_id, user_order)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in check_answer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/hint', methods=['POST'])
def get_hint():
    """Get hint for current question"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id') or request.remote_addr
        
        hint = game_engine.get_hint(user_id)
        
        if hint:
            return jsonify({
                'success': True,
                'hint': hint
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No active question for hint'
            }), 404
        
    except Exception as e:
        print(f"❌ Error in get_hint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/score', methods=['POST'])
def get_score():
    """Get current session score"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id') or request.remote_addr
        
        session_info = game_engine.get_session_info(user_id)
        return jsonify(session_info)
        
    except Exception as e:
        print(f"❌ Error in get_score: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/reset-level', methods=['POST'])
def reset_level():
    """Reset current level"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id') or request.remote_addr
        level_id = data.get('level')
        
        if not level_id:
            # Get current level from session
            session = game_engine.get_or_create_session(user_id)
            level_id = session.current_level or 'level_1'
        
        result = game_engine.start_level(user_id, level_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in reset_level: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get mock leaderboard (placeholder)"""
    # This is a placeholder - implement actual leaderboard with database if needed
    mock_leaderboard = [
        {"rank": 1, "name": "Chamath", "score": 980, "stars": 45, "level": "Advanced"},
        {"rank": 2, "name": "Nimal", "score": 920, "stars": 42, "level": "Advanced"},
        {"rank": 3, "name": "Kamal", "score": 890, "stars": 40, "level": "Intermediate"},
        {"rank": 4, "name": "Sunil", "score": 850, "stars": 38, "level": "Intermediate"},
        {"rank": 5, "name": "Priya", "score": 820, "stars": 36, "level": "Beginner"},
        {"rank": 6, "name": "Anusha", "score": 780, "stars": 34, "level": "Beginner"},
        {"rank": 7, "name": "Ruwan", "score": 750, "stars": 32, "level": "Beginner"},
        {"rank": 8, "name": "Malini", "score": 720, "stars": 30, "level": "Beginner"},
    ]
    
    return jsonify({
        'success': True,
        'leaderboard': mock_leaderboard
    })


@app.route('/api/sentence-video/<path:filename>', methods=['GET'])
def serve_sentence_video(filename):
    """Serve sentence video file"""
    try:
        # Security check
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400
        
        video_path = os.path.join(Config.VIDEO_OUT, filename)
        print(f"📹 Serving video: {filename}")
        
        if not os.path.exists(video_path):
            # Try to find alternative
            base_name = filename.split('_')[0] if '_' in filename else filename
            for f in os.listdir(Config.VIDEO_OUT):
                if base_name in f and f.endswith('.mp4'):
                    video_path = os.path.join(Config.VIDEO_OUT, f)
                    print(f"   Found alternative: {f}")
                    break
            else:
                return jsonify({'error': 'Video not found'}), 404
        
        return send_file(video_path, mimetype='video/mp4')
        
    except Exception as e:
        print(f"❌ Video serving error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug-questions/<level_id>', methods=['GET'])
def debug_questions(level_id):
    """Debug endpoint to see questions for a level"""
    questions = game_engine.get_level_questions(level_id, 3)
    
    return jsonify({
        'success': True,
        'level': level_id,
        'question_count': len(questions),
        'questions': questions,
        'video_directory': Config.VIDEO_OUT,
        'video_exists': [os.path.exists(os.path.join(Config.VIDEO_OUT, q['video_filename'])) 
                         for q in questions]
    })


@app.route('/api/cleanup-sessions', methods=['POST'])
def cleanup_sessions():
    """Manually trigger session cleanup"""
    game_engine.cleanup_old_sessions()
    return jsonify({
        'success': True,
        'message': f'Active sessions: {len(game_engine.sessions)}'
    })


# ========================
# PERIODIC CLEANUP
# ========================
def periodic_cleanup():
    """Run cleanup every hour"""
    while True:
        time.sleep(3600)  # 1 hour
        try:
            game_engine.cleanup_old_sessions()
            print(f"🧹 Periodic cleanup completed. Active sessions: {len(game_engine.sessions)}")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()


# ========================
# ERROR HANDLERS
# ========================
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ========================
# MAIN
# ========================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌐 Server starting at: http://localhost:5002")
    print("📡 Available endpoints:")
    print("   GET  /api/health")
    print("   GET  /api/levels")
    print("   POST /api/start-level")
    print("   POST /api/current-question")
    print("   POST /api/check")
    print("   POST /api/hint")
    print("   POST /api/score")
    print("   POST /api/reset-level")
    print("   GET  /api/leaderboard")
    print("   GET  /api/sentence-video/<filename>")
    print("   GET  /api/debug-questions/<level_id>")
    print("   POST /api/cleanup-sessions")
    print("="*70 + "\n")
    
    # Run Flask
    app.run(
        host="0.0.0.0",
        port=5002,
        debug=False,
        threaded=True
    )