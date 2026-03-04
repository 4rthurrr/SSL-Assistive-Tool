import os  
import pickle
import regex
import torch
import torch.nn as nn
from flask import Flask, request, jsonify, send_file
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
from google import genai
from dotenv import load_dotenv

# Fix Unicode encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
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
    
    if mongodb_manager and hasattr(mongodb_manager, 'disconnect'):
        atexit.register(mongodb_manager.disconnect)
    
    app.run(host="0.0.0.0", port=5001, debug=False)