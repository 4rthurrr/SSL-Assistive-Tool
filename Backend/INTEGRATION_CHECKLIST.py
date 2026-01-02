"""
========================
IMPLEMENTATION CHECKLIST FOR app.py
========================

Copy-paste sections of this file into your Backend/app.py to integrate MongoDB.
Follow the order: 1, 2, 3, 4, 5, 6

BEFORE YOU START:
- Make sure mongodb_integration.py is in Backend/ folder
- Verify MongoDB is running and MONGODB_URI is set in .env
- Have a user_id from Express login for testing
"""

# ========================
# STEP 1: ADD IMPORTS AT TOP OF app.py
# ========================

# Add these imports near other imports at the top of Backend/app.py:

"""
from mongodb_integration import mongodb_manager
from bson.objectid import ObjectId
import json
"""

# Then your existing imports continue...
# (Flask, torch, numpy, etc.)


# ========================
# STEP 2: REMOVE OLD IN-MEMORY STORAGE
# ========================

# In your app.py, REMOVE or COMMENT OUT these old global variables:

"""
# OLD - DELETE OR COMMENT OUT:
# user_game_states = {}  
# struggle_detector = StruggleDetector()

# These are now handled by MongoDB!
"""


# ========================
# STEP 3: ADD NEW ENDPOINT - SAVE GAME ATTEMPT
# ========================

"""
Add this endpoint to replace the old game attempt saving:

@app.route('/api/game/attempt', methods=['POST', 'OPTIONS'])
def save_game_attempt():
    '''Save a game attempt to MongoDB'''
    
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['userId', 'level', 'word', 'correct', 'confidence']
        if not all(field in data for field in required):
            return jsonify({
                'success': False,
                'error': f'Missing fields: {required}'
            }), 400
        
        # Prepare attempt data for MongoDB
        attempt_data = {
            'userId': data['userId'],  # MongoDB ObjectId from Express
            'level': data['level'],
            'word': data['word'],
            'sinhalaWord': data.get('sinhalaWord'),
            'englishTranslation': data.get('englishTranslation'),
            'correct': bool(data['correct']),
            'confidence': float(data.get('confidence', 0)),
            'timeTaken': float(data.get('timeTaken', 0)),
            'hintsProvided': data.get('hintsProvided', []),
            'feedbackGiven': data.get('feedbackGiven'),
            'sessionId': data.get('sessionId'),
            'modelVersion': data.get('modelVersion')
        }
        
        # Save to MongoDB
        result = mongodb_manager.save_game_attempt(attempt_data)
        
        if result:
            # Check if user is struggling (for hint system)
            is_struggling = mongodb_manager.is_struggling(
                data['userId'],
                data['word'],
                data['level'],
                threshold=2
            )
            
            return jsonify({
                'success': True,
                'message': 'Attempt saved',
                'isStruggling': is_struggling
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save attempt'
            }), 500
    
    except Exception as e:
        print(f"❌ Error saving attempt: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
"""


# ========================
# STEP 4: ADD NEW ENDPOINTS - GET STATISTICS
# ========================

"""
Add these new endpoints for analytics:

@app.route('/api/game/user-stats/<user_id>', methods=['GET', 'OPTIONS'])
def get_user_stats(user_id):
    '''Get overall user statistics from MongoDB'''
    
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        stats = mongodb_manager.get_user_stats(user_id)
        
        if stats:
            return jsonify({
                'success': True,
                'stats': stats
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No data found'
            }), 404
    
    except Exception as e:
        print(f"❌ Error getting user stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/game/level-stats/<user_id>/<level>', methods=['GET', 'OPTIONS'])
def get_level_stats(user_id, level):
    '''Get statistics for a specific level'''
    
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        if level not in ['basic', 'easy', 'medium', 'hard']:
            return jsonify({
                'success': False,
                'error': 'Invalid level'
            }), 400
        
        stats = mongodb_manager.get_level_stats(user_id, level)
        
        return jsonify({
            'success': True,
            'level': level,
            'stats': stats
        }), 200
    
    except Exception as e:
        print(f"❌ Error getting level stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/game/word-stats/<user_id>', methods=['GET', 'OPTIONS'])
def get_word_stats(user_id):
    '''Get word-level performance from MongoDB'''
    
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        word_stats = mongodb_manager.get_word_stats(user_id)
        
        if word_stats is not None:
            return jsonify({
                'success': True,
                'words': word_stats
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to get word stats'
            }), 500
    
    except Exception as e:
        print(f"❌ Error getting word stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/game/recent-attempts/<user_id>', methods=['GET', 'OPTIONS'])
def get_recent_attempts(user_id):
    '''Get recent game attempts for activity feed'''
    
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        limit = request.args.get('limit', 10, type=int)
        attempts = mongodb_manager.get_recent_attempts(user_id, limit=limit)
        
        # Convert ObjectIds to strings for JSON
        if attempts:
            for attempt in attempts:
                attempt['_id'] = str(attempt['_id'])
                attempt['userId'] = str(attempt['userId'])
        
        return jsonify({
            'success': True,
            'attempts': attempts or []
        }), 200
    
    except Exception as e:
        print(f"❌ Error getting recent attempts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
"""


# ========================
# STEP 5: REPLACE PROGRESS REPORT ENDPOINT
# ========================

"""
Replace your existing /api/ai/progress-report endpoint with this MongoDB version:

@app.route('/api/ai/progress-report', methods=['POST', 'OPTIONS'])
def progress_report():
    '''Generate progress report from MongoDB data'''
    
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'userId required'
            }), 400
        
        # Get data from MongoDB (not in-memory)
        overall_stats = mongodb_manager.get_user_stats(user_id)
        word_stats = mongodb_manager.get_word_stats(user_id)
        
        # If no data, return empty report
        if not overall_stats or overall_stats.get('totalAttempts', 0) == 0:
            return jsonify({
                'success': True,
                'report': {
                    'summary': {
                        'words_learned': 0,
                        'overall_accuracy': 0,
                        'total_playtime_minutes': 0,
                        'current_streak': 0,
                        'current_level': 'basic',
                        'total_attempts': 0,
                        'correct_attempts': 0
                    },
                    'message': 'No attempts recorded. Start playing to generate analytics!'
                }
            }), 200
        
        # ========================
        # LEVEL PROGRESS
        # ========================
        
        level_progress = {}
        level_stats = {}
        
        for level in ['basic', 'easy', 'medium', 'hard']:
            stats = mongodb_manager.get_level_stats(user_id, level)
            level_stats[level] = stats
            
            level_progress[level] = {
                'level': level,
                'total': stats['total'],
                'correct': stats['correct'],
                'accuracy': round(stats['accuracy'], 1),
                'avgTime': round(stats['avgTime'], 2),
                'status': 'completed' if stats['accuracy'] >= 70 else 'in-progress' if stats['total'] > 0 else 'locked'
            }
        
        # ========================
        # SKILL GAPS
        # ========================
        
        skill_gaps = []
        if word_stats:
            for word in word_stats:
                if word['accuracy'] < 70:
                    skill_gaps.append({
                        'word': word['word'],
                        'sinhalaWord': word.get('sinhalaWord'),
                        'english': word.get('englishTranslation'),
                        'level': word['level'],
                        'accuracy': round(word['accuracy'], 1),
                        'attempts': word['total'],
                        'suggestions': [
                            'Watch the sign video carefully',
                            'Practice the hand movements slowly',
                            'Break down the word syllable by syllable'
                        ]
                    })
        
        skill_gaps.sort(key=lambda x: x['accuracy'])
        
        # ========================
        # RECOMMENDATIONS
        # ========================
        
        recommendations = []
        if word_stats:
            for word in word_stats:
                accuracy = word['accuracy']
                if 50 <= accuracy < 85:
                    recommendations.append({
                        'word': word['word'],
                        'sinhalaWord': word.get('sinhalaWord'),
                        'english': word.get('englishTranslation'),
                        'level': word['level'],
                        'accuracy': round(accuracy, 1),
                        'priority': 1 if accuracy < 70 else 2,
                        'reason': 'Good progress! Keep practicing to master this sign.'
                    })
        
        recommendations.sort(key=lambda x: (x['priority'], -x['accuracy']))
        
        # ========================
        # CURRENT LEVEL
        # ========================
        
        current_level = 'basic'
        if level_stats['basic']['accuracy'] >= 70:
            current_level = 'easy'
        if level_stats['easy']['accuracy'] >= 70:
            current_level = 'medium'
        if level_stats['medium']['accuracy'] >= 70:
            current_level = 'hard'
        
        # ========================
        # INSIGHTS & ACHIEVEMENTS
        # ========================
        
        accuracy = overall_stats['overallAccuracy']
        words_learned = overall_stats['wordsLearned']
        total_attempts = overall_stats['totalAttempts']
        correct_attempts = overall_stats['correctAttempts']
        
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
        
        achievements = []
        if words_learned >= 5:
            achievements.append({'name': 'First Steps', 'icon': '👣'})
        if words_learned >= 10:
            achievements.append({'name': 'Vocabulary Builder', 'icon': '📚'})
        if accuracy >= 80:
            achievements.append({'name': 'High Achiever', 'icon': '🏆'})
        if total_attempts >= 20:
            achievements.append({'name': 'Dedicated Learner', 'icon': '⭐'})
        
        # ========================
        # PREDICTIONS
        # ========================
        
        next_level_score = min(accuracy + 10, 95)
        confidence = 75 if total_attempts >= 10 else 50
        time_to_master = "2-3 weeks" if accuracy >= 60 else "3-4 weeks"
        
        total_playtime_minutes = int(total_attempts * 1.5)
        
        # Calculate streak
        recent = mongodb_manager.get_recent_attempts(user_id, limit=100)
        recent_dates = set()
        if recent:
            for attempt in recent:
                attempt_date = attempt.get('createdAt', datetime.now())
                if isinstance(attempt_date, datetime):
                    recent_dates.add(attempt_date.date())
        current_streak = len(recent_dates)
        
        # ========================
        # BUILD REPORT
        # ========================
        
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
            'skill_gaps': skill_gaps[:5],
            'recommendations': recommendations[:5]
        }
        
        print(f"✅ Generated report: {words_learned} words, {accuracy:.1f}% accuracy")
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
    
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
"""


# ========================
# STEP 6: ADD SHUTDOWN HANDLER (OPTIONAL)
# ========================

"""
Add this near the bottom of your app.py, before the if __name__ == '__main__' block:

@app.teardown_appcontext
def shutdown_session(exception=None):
    '''Close MongoDB connection on app shutdown'''
    if hasattr(mongodb_manager, 'disconnect'):
        mongodb_manager.disconnect()
"""


# ========================
# COMPLETE EXAMPLE - WHERE TO ADD IN app.py
# ========================

"""
Here's the structure of how your complete app.py should look:

-----------------------------------------
from flask import Flask, request, jsonify, ...
from mongodb_integration import mongodb_manager  # ← ADD THIS
from bson.objectid import ObjectId               # ← ADD THIS
import json, datetime, torch, ...                # your other imports

app = Flask(__name__)
CORS(app, ...)

# CONFIG
MODEL_DIR = ...
VIDEO_DIR = ...

# NOTE: Remove or comment out old in-memory storage:
# user_game_states = {}  # DELETE
# struggle_detector = StruggleDetector()  # DELETE

# Keep your existing code:
VIDEO_MAPPING = build_video_mapping()
hint_generator = HintGenerator()
model = LSTMPuzzleModel(...)

# ... existing endpoints ...

# ADD NEW ENDPOINT: Save game attempt
@app.route('/api/game/attempt', methods=['POST', 'OPTIONS'])
def save_game_attempt():
    # ... see STEP 3 above ...
    pass

# ADD NEW ENDPOINTS: Get statistics
@app.route('/api/game/user-stats/<user_id>', methods=['GET', 'OPTIONS'])
def get_user_stats(user_id):
    # ... see STEP 4 above ...
    pass

# ... more stat endpoints ...

# REPLACE EXISTING: Progress report
@app.route('/api/ai/progress-report', methods=['POST', 'OPTIONS'])
def progress_report():
    # ... see STEP 5 above (MongoDB version) ...
    pass

# ADD SHUTDOWN HANDLER
@app.teardown_appcontext
def shutdown_session(exception=None):
    # ... see STEP 6 above ...
    pass

# AT BOTTOM:
if __name__ == '__main__':
    print('🎮 Sinhala Sign Language API')
    app.run(host='0.0.0.0', port=5001, debug=True)
-----------------------------------------
"""


# ========================
# TESTING YOUR INTEGRATION
# ========================

"""
After integration, test with:

1. Save an attempt:
   curl -X POST http://localhost:5001/api/game/attempt \\
     -H "Content-Type: application/json" \\
     -d '{
       "userId": "507f1f77bcf86cd799439011",
       "level": "easy",
       "word": "good",
       "sinhalaWord": "හොඳ",
       "englishTranslation": "Good",
       "correct": true,
       "confidence": 0.95,
       "timeTaken": 2.5
     }'

2. Get user stats:
   curl http://localhost:5001/api/game/user-stats/507f1f77bcf86cd799439011

3. Get progress report:
   curl -X POST http://localhost:5001/api/ai/progress-report \\
     -H "Content-Type: application/json" \\
     -d '{"userId": "507f1f77bcf86cd799439011"}'

IMPORTANT: Replace 507f1f77bcf86cd799439011 with a real user_id from Express login!
"""


print("""
================================
INTEGRATION CHECKLIST
================================

☐ 1. Copy imports to top of app.py
☐ 2. Comment out old in-memory storage
☐ 3. Add save_game_attempt endpoint
☐ 4. Add get_user_stats, get_level_stats, etc. endpoints
☐ 5. Replace progress_report with MongoDB version
☐ 6. Add shutdown handler
☐ 7. Verify MongoDB is running
☐ 8. Test endpoints with valid userId
☐ 9. Update frontend to send userId
☐ 10. Verify data persists in MongoDB

For help, see:
- MONGODB_INTEGRATION.md (detailed guide)
- flask_mongodb_examples.py (more examples)
- mongodb_integration.py (MongoDB manager)
""")
