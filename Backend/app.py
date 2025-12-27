import os  
import pickle
import regex
import torch
import torch.nn as nn
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import numpy as np
import random
import json
from datetime import datetime
from collections import defaultdict, deque

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
MODEL_DIR = r"D:\Game new\Backend\SSL_model"
VIDEO_DIR = r"D:\Game new\Backend\public\Dataset - Original-20251215T123918Z-3-001"

print(f"📁 VIDEO_DIR: {VIDEO_DIR}")
print(f"✓ Directory exists: {os.path.exists(VIDEO_DIR)}")

# ========================
# GLOBAL STORAGE - FIX: Initialize user_game_states
# ========================
user_sessions = {}
user_game_states = {}  # ← THIS WAS MISSING!

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

    print(f"\n✅ Mapped {len(video_map)} unique words (1 video per word)")
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
    print(f"📊 Levels: {list(level_words.keys())}")
    for level, words in level_words.items():
        print(f"   {level}: {len(words)} words")
except Exception as e:
    print(f"❌ Error loading metadata: {e}")
    # Fallback data for testing
    label_to_english = {}
    level_words = {'basic': [], 'easy': [], 'medium': [], 'hard': []}
    level_indices = {}
    input_dim, hidden_dim, num_classes = 128, 256, 100

# Build mapping (needs label_to_english to be loaded first)
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
    
    def get_level_performance(self, user_id, level):
        if user_id not in self.attempt_history:
            return {'total': 0, 'correct': 0, 'accuracy': 0}
        level_attempts = [a for a in self.attempt_history[user_id] if a.get('level') == level]
        total = len(level_attempts)
        correct = sum(1 for a in level_attempts if a['correct'])
        return {'total': total, 'correct': correct, 'accuracy': (correct / total * 100) if total > 0 else 0}

class HintGenerator:
    def __init__(self):
        self.hint_templates = {
            'encouragement': ["You're doing great! 💪", "හොඳින් කරනවා! 🌟"],
            'visual': ["Watch carefully 👀", "Focus on positions 👋"],
            'syllable': ["අකුරු {count} ක් තිබේ 📝"],
            'starts_with': ["'{letter}' අකුරෙන් ආරම්භ වේ ✏️"],
            'meaning': ["Meaning: {english} 🌍"]
        }
    
    def count_syllables(self, word):
        word_cleaned = regex.sub(r'^\d+\.\s*', '', word)
        syllables = regex.findall(r'\X', word_cleaned)
        return len([s for s in syllables if s.strip()])
    
    def generate_hint(self, word, attempt_number, english_meaning, level='easy'):
        hints = []
        if attempt_number <= 1:
            hints.append(random.choice(self.hint_templates['encouragement']))
        elif attempt_number == 2:
            hints.append(random.choice(self.hint_templates['visual']))
        elif attempt_number == 3:
            syl_count = self.count_syllables(word)
            hints.append(self.hint_templates['syllable'][0].format(count=syl_count))
        elif attempt_number == 4:
            first_letter = word[0] if word else ''
            hints.append(self.hint_templates['starts_with'][0].format(letter=first_letter))
        elif attempt_number >= 5 and english_meaning:
            hints.append(self.hint_templates['meaning'][0].format(english=english_meaning))
        return hints

struggle_detector = StruggleDetector()
hint_generator = HintGenerator()

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
            print(f"📝 Added '{word}' to used words for {self.user_id}. Total used: {len(self.used_words)}")
    
    def get_available_words(self, all_words):
        available = [w for w in all_words if w not in self.used_words]
        print(f"📊 Available words for {self.user_id}: {len(available)}/{len(all_words)}")
        return available
    
    def reset_game(self):
        self.used_words = []
        self.round = 0
        print(f"🔄 Reset game state for {self.user_id}")
    
    def is_game_complete(self):
        return self.round >= self.max_rounds

def get_game_state(user_id, level):
    key = f"{user_id}_{level}"
    if key not in user_game_states:
        user_game_states[key] = GameState(user_id, level)
        print(f"🎮 Created new game state for {user_id} (level: {level})")
    return user_game_states[key]

# ========================
# VIDEO HELPER
# ========================
def find_video_for_word(sinhala_word):
    """Find video file for word - returns video key (not path)"""
    english = label_to_english.get(sinhala_word, '').lower()
    
    if english in VIDEO_MAPPING:
        return english
    
    if sinhala_word.lower() in VIDEO_MAPPING:
        return sinhala_word.lower()
    
    for key in VIDEO_MAPPING.keys():
        if english and (key.startswith(english[:3]) or english.startswith(key[:3])):
            return key
    
    print(f"⚠️ No video: {sinhala_word} ({english})")
    return None

# ========================
# API ENDPOINTS
# ========================
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'videos_mapped': len(VIDEO_MAPPING),
        'video_dir_exists': os.path.exists(VIDEO_DIR),
        'levels': list(level_words.keys()),
        'active_sessions': len(user_game_states)
    })

@app.route('/api/puzzle/generate', methods=['POST'])
def generate_puzzle():
    try:
        data = request.json
        level = data.get('level', 'basic')
        user_id = data.get('user_id', 'default')
        
        if level not in level_words:
            return jsonify({'success': False, 'error': 'Invalid level'}), 400
        
        game_state = get_game_state(user_id, level)
        game_state.round += 1
        
        print(f"\n🎯 Round {game_state.round}/{game_state.max_rounds} for {user_id} (Level: {level})")
        
        level_word_list = level_words[level]
        
        words_with_videos = []
        for w in level_word_list:
            video_key = find_video_for_word(w)
            if video_key:
                words_with_videos.append(w)
        
        print(f"📊 Level '{level}': {len(words_with_videos)}/{len(level_word_list)} words with videos")
        
        available_words = game_state.get_available_words(words_with_videos)
        
        if len(available_words) < 4:
            print(f"⚠️ Not enough new words, resetting used words list")
            game_state.used_words = []
            available_words = words_with_videos
        
        if len(available_words) < 4:
            return jsonify({
                'success': False,
                'error': f'Not enough words with videos in {level} ({len(available_words)} available)'
            }), 400
        
        target_word = random.choice(available_words)
        game_state.add_used_word(target_word)
        video_key = find_video_for_word(target_word)
        
        other_available = [w for w in available_words if w != target_word]
        
        if len(other_available) >= 3:
            options = random.sample(other_available, 3)
        else:
            all_other = [w for w in words_with_videos if w != target_word]
            options = random.sample(all_other, min(3, len(all_other)))
        
        options.append(target_word)
        random.shuffle(options)
        
        print(f"✅ Selected word: {target_word} (English: {label_to_english.get(target_word, '')})")
        
        return jsonify({
            'success': True,
            'target_word': target_word,
            'target_english': label_to_english.get(target_word, ''),
            'video_url': f"/api/videos/{video_key}" if video_key else None,
            'options': [{'word': w, 'english': label_to_english.get(w, '')} for w in options],
            'level': level,
            'round': game_state.round,
            'total_rounds': game_state.max_rounds,
            'used_words_count': len(game_state.used_words)
        })
    except Exception as e:
        print(f"❌ Puzzle generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/<video_key>', methods=['GET'])
def serve_video(video_key):
    try:
        print(f"\n🎥 Video request: '{video_key}'")
        video_key = video_key.lower().strip()
        
        if video_key not in VIDEO_MAPPING:
            print(f"❌ Video key not found: '{video_key}'")
            return jsonify({'error': 'Video not found', 'video_key': video_key}), 404
        
        video_info = VIDEO_MAPPING[video_key]
        full_path = video_info['full_path']
        
        if not os.path.exists(full_path):
            print(f"❌ File does not exist on disk!")
            return jsonify({'error': 'Video file not found on disk'}), 404
        
        ext = os.path.splitext(full_path)[1].lower()
        mimetype_map = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.webm': 'video/webm',
            '.mkv': 'video/x-matroska'
        }
        mimetype = mimetype_map.get(ext, 'video/mp4')
        
        return send_file(full_path, mimetype=mimetype, as_attachment=False)
        
    except Exception as e:
        print(f"❌ Error serving video: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attempt', methods=['POST'])
def record_attempt():
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        word = data.get('word')
        level = data.get('level', 'basic')
        correct = data.get('correct', False)
        time_taken = data.get('time_taken', 0)
        
        struggle_detector.record_attempt(user_id, word, level, correct, time_taken)
        attempt_count = struggle_detector.get_attempt_count(user_id, word)
        
        hints = []
        if not correct and attempt_count >= 2:
            english = label_to_english.get(word, '')
            hints = hint_generator.generate_hint(word, attempt_count, english, level)
        
        return jsonify({
            'success': True,
            'show_hint': len(hints) > 0,
            'hints': hints,
            'attempt_number': attempt_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/puzzle/reset', methods=['POST'])
def reset_puzzle():
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        level = data.get('level', 'basic')
        
        key = f"{user_id}_{level}"
        if key in user_game_states:
            del user_game_states[key]
            print(f"🔄 Reset game state for {user_id} (level: {level})")
        
        return jsonify({'success': True, 'message': 'Game state reset'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Add this to your Flask backend (app.py or main.py) after the existing endpoints

@app.route('/api/ai/progress-report', methods=['POST'])
def get_progress_report():
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        
        print(f"\n📊 Generating AI progress report for: {user_id}")
        
        # Get user's attempt history
        if user_id not in struggle_detector.attempt_history:
            return jsonify({
                'success': False,
                'message': 'No data available. Play some games first!'
            })
        
        attempts = list(struggle_detector.attempt_history[user_id])
        
        if len(attempts) == 0:
            return jsonify({
                'success': False,
                'message': 'No gameplay data found'
            })
        
        # Calculate statistics
        total_attempts = len(attempts)
        correct_attempts = sum(1 for a in attempts if a['correct'])
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        # Get unique words learned
        unique_words = set(a['word'] for a in attempts if a['correct'])
        words_learned = len(unique_words)
        
        # Calculate level progress
        level_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'attempts': []})
        for attempt in attempts:
            level = attempt.get('level', 'basic')
            level_stats[level]['total'] += 1
            level_stats[level]['attempts'].append(attempt)
            if attempt['correct']:
                level_stats[level]['correct'] += 1
        
        level_progress = {}
        for level in ['basic', 'easy', 'medium', 'hard']:
            if level in level_stats:
                stats = level_stats[level]
                level_accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                level_progress[level] = {
                    'accuracy': round(level_accuracy, 1),
                    'total_attempts': stats['total'],
                    'correct_attempts': stats['correct'],
                    'unlocked': True  # For now, all unlocked
                }
            else:
                level_progress[level] = {
                    'accuracy': 0,
                    'total_attempts': 0,
                    'correct_attempts': 0,
                    'unlocked': level == 'basic'
                }
        
        # Find skill gaps (words with low accuracy)
        word_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
        for attempt in attempts:
            word = attempt['word']
            word_performance[word]['total'] += 1
            if attempt['correct']:
                word_performance[word]['correct'] += 1
        
        skill_gaps = []
        for word, perf in word_performance.items():
            if perf['total'] >= 2:  # At least 2 attempts
                word_accuracy = (perf['correct'] / perf['total'] * 100)
                if word_accuracy < 70:  # Struggling words
                    skill_gaps.append({
                        'word': word,
                        'english': label_to_english.get(word, ''),
                        'accuracy': round(word_accuracy, 1),
                        'attempts': perf['total'],
                        'suggestions': [
                            'Watch the sign video carefully',
                            'Practice the hand movements slowly',
                            'Break down the word syllable by syllable'
                        ]
                    })
        
        skill_gaps.sort(key=lambda x: x['accuracy'])
        
        # Generate recommendations (words to practice next)
        recommendations = []
        for word, perf in word_performance.items():
            word_accuracy = (perf['correct'] / perf['total'] * 100) if perf['total'] > 0 else 0
            if 50 <= word_accuracy < 85:  # Words in progress
                recommendations.append({
                    'word': word,
                    'english': label_to_english.get(word, ''),
                    'accuracy': round(word_accuracy, 1),
                    'priority': 1 if word_accuracy < 70 else 2,
                    'reason': 'Good progress! Keep practicing to master this sign.'
                })
        
        recommendations.sort(key=lambda x: (x['priority'], -x['accuracy']))
        
        # Calculate current level
        avg_accuracy_by_level = {
            level: (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            for level, stats in level_stats.items()
        }
        
        current_level = 'basic'
        if avg_accuracy_by_level.get('basic', 0) >= 70:
            current_level = 'easy'
        if avg_accuracy_by_level.get('easy', 0) >= 70:
            current_level = 'medium'
        if avg_accuracy_by_level.get('medium', 0) >= 70:
            current_level = 'hard'
        
        # Generate insights
        insights = []
        if accuracy >= 80:
            insights.append("🌟 Excellent accuracy! You're mastering sign language.")
        elif accuracy >= 60:
            insights.append("👍 Good progress! Keep practicing to improve.")
        else:
            insights.append("💪 Keep going! Practice makes perfect.")
        
        if words_learned >= 20:
            insights.append(f"🎓 You've learned {words_learned} words! Great vocabulary building.")
        
        if len(skill_gaps) > 0:
            insights.append(f"🎯 Focus on {len(skill_gaps)} challenging words for faster progress.")
        
        # Achievements
        achievements = []
        if words_learned >= 5:
            achievements.append({'name': 'First Steps', 'icon': '👣'})
        if words_learned >= 10:
            achievements.append({'name': 'Vocabulary Builder', 'icon': '📚'})
        if accuracy >= 80:
            achievements.append({'name': 'High Achiever', 'icon': '🏆'})
        if total_attempts >= 20:
            achievements.append({'name': 'Dedicated Learner', 'icon': '⭐'})
        
        # AI Predictions
        next_level_score = min(accuracy + 10, 95)  # Predict slight improvement
        confidence = 75 if total_attempts >= 10 else 50
        time_to_master = "2-3 weeks" if accuracy >= 60 else "3-4 weeks"
        
        # Calculate playtime (approximate)
        total_playtime_minutes = int(total_attempts * 1.5)  # Rough estimate: 1.5 min per attempt
        
        # Calculate streak (simplified - check recent days)
        recent_dates = set()
        for attempt in attempts[-20:]:  # Check last 20 attempts
            attempt_date = attempt.get('timestamp', datetime.now()).date()
            recent_dates.add(attempt_date)
        current_streak = len(recent_dates)
        
        # Build report
        report = {
            'summary': {
                'words_learned': words_learned,
                'overall_accuracy': round(accuracy, 1),
                'total_playtime_minutes': total_playtime_minutes,
                'current_streak': current_streak,
                'current_level': current_level,
                'total_attempts': total_attempts,
                'correct_attempts': correct_attempts
            },
            'level_progress': level_progress,
            'predictions': {
                'next_level_score': round(next_level_score, 1),
                'confidence': confidence,
                'time_to_master': time_to_master
            },
            'achievements': achievements,
            'insights': insights,
            'skill_gaps': skill_gaps[:5],  # Top 5
            'recommendations': recommendations[:5],  # Top 5
            'next_level_unlocked': None  # Can add logic later
        }
        
        print(f"✅ Generated report: {words_learned} words, {accuracy:.1f}% accuracy")
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        print(f"❌ Error generating progress report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Also make sure you have OPTIONS handler for CORS
@app.route('/api/ai/progress-report', methods=['OPTIONS'])
def progress_report_options():
    return '', 204
# ========================
# RUN
# ========================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎮 Sinhala Sign Language API")
    print(f"🌐 http://localhost:5001")
    print(f"📹 Videos: {len(VIDEO_MAPPING)} mapped")
    print("="*70 + "\n")
    app.run(host="0.0.0.0", port=5001, debug=True)