"""
========================
Flask API Endpoints - MongoDB Integration Examples
========================

This file shows how to update Flask endpoints to use MongoDB for persistent storage.
Copy these patterns into your app.py file.

IMPORTANT: Replace the existing in-memory storage calls with these MongoDB-backed versions.

KEY CHANGES:
1. POST /api/game/attempt - Save game attempt to MongoDB
2. GET /api/game/user-stats/:userId - Query MongoDB for user stats
3. POST /api/ai/progress-report - Generate analytics from MongoDB data
"""

from flask import request, jsonify
from mongodb_integration import mongodb_manager
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import json

# ========================
# 1. SAVE GAME ATTEMPT
# ========================
# Replace: struggle_detector.record_attempt()
# With: MongoDB save

def save_game_attempt_example():
    """
    POST /api/game/attempt
    Save a single game attempt to MongoDB
    
    Frontend should send:
    {
        "userId": "507f1f77bcf86cd799439011",  // MongoDB ObjectId from Express
        "level": "easy",
        "word": "Good",
        "sinhalaWord": "හොඳ",
        "englishTranslation": "Good",
        "correct": true,
        "confidence": 0.95,
        "timeTaken": 2.5,
        "hintsProvided": ["Watch carefully", "Focus on positions"],
        "sessionId": "session_123"
    }
    """
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['userId', 'level', 'word', 'correct', 'confidence']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {required_fields}'
            }), 400
        
        # Count previous attempts for this word (for hint system)
        attempt_number = 1
        recent = mongodb_manager.get_recent_attempts(data['userId'], limit=20)
        if recent:
            same_word_attempts = [a for a in recent if a.get('word') == data['word']]
            attempt_number = len(same_word_attempts) + 1
        
        attempt_data = {
            'userId': data['userId'],
            'level': data['level'],
            'word': data['word'],
            'sinhalaWord': data.get('sinhalaWord'),
            'englishTranslation': data.get('englishTranslation'),
            'correct': data['correct'],
            'confidence': float(data.get('confidence', 0)),
            'timeTaken': float(data.get('timeTaken', 0)),
            'attemptNumber': attempt_number,
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
                data['level']
            )
            
            return jsonify({
                'success': True,
                'attemptId': result.get('_id'),
                'isStruggling': is_struggling,
                'message': 'Attempt saved successfully'
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


# ========================
# 2. GET USER GAME STATISTICS
# ========================
# Replace: struggle_detector.get_level_performance()
# With: MongoDB queries

def get_user_stats_example():
    """
    GET /api/game/user-stats/:userId
    Get overall user statistics from MongoDB
    
    Returns:
    {
        "success": true,
        "stats": {
            "totalAttempts": 150,
            "correctAttempts": 120,
            "wordsLearned": 45,
            "overallAccuracy": 80.0,
            "avgTime": 2.3,
            "avgConfidence": 0.88,
            "firstAttempt": "2025-01-15T10:30:00",
            "lastAttempt": "2025-01-27T14:22:00"
        }
    }
    """
    
    try:
        user_id = request.args.get('userId') or request.view_args.get('userId')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'userId is required'
            }), 400
        
        stats = mongodb_manager.get_user_stats(user_id)
        
        if stats:
            return jsonify({
                'success': True,
                'stats': stats
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
    
    except Exception as e:
        print(f"❌ Error getting user stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================
# 3. GET LEVEL STATISTICS
# ========================

def get_level_stats_example():
    """
    GET /api/game/level-stats/:userId/:level
    Get statistics for a specific level
    
    Returns:
    {
        "success": true,
        "level": "easy",
        "stats": {
            "total": 50,
            "correct": 42,
            "accuracy": 84.0,
            "avgTime": 2.1,
            "avgConfidence": 0.87
        }
    }
    """
    
    try:
        user_id = request.view_args.get('userId')
        level = request.view_args.get('level')
        
        if not user_id or not level:
            return jsonify({
                'success': False,
                'error': 'userId and level are required'
            }), 400
        
        valid_levels = ['basic', 'easy', 'medium', 'hard']
        if level not in valid_levels:
            return jsonify({
                'success': False,
                'error': f'Invalid level. Must be one of: {valid_levels}'
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


# ========================
# 4. GET WORD STATISTICS
# ========================

def get_word_stats_example():
    """
    GET /api/game/word-stats/:userId
    Get performance for each word learned
    
    Returns:
    {
        "success": true,
        "words": [
            {
                "word": "good",
                "sinhalaWord": "හොඳ",
                "englishTranslation": "Good",
                "level": "easy",
                "total": 8,
                "correct": 7,
                "accuracy": 87.5,
                "avgTime": 2.2,
                "lastAttempt": "2025-01-27T14:22:00"
            },
            ...
        ]
    }
    """
    
    try:
        user_id = request.view_args.get('userId')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'userId is required'
            }), 400
        
        word_stats = mongodb_manager.get_word_stats(user_id)
        
        if word_stats is not None:
            return jsonify({
                'success': True,
                'words': word_stats
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve word statistics'
            }), 500
    
    except Exception as e:
        print(f"❌ Error getting word stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================
# 5. GET RECENT ATTEMPTS
# ========================

def get_recent_attempts_example():
    """
    GET /api/game/recent-attempts/:userId?limit=10
    Get recent game attempts for activity feed
    
    Returns:
    {
        "success": true,
        "attempts": [
            {
                "_id": "507f1f77bcf86cd799439011",
                "userId": "507f1f77bcf86cd799439010",
                "word": "Good",
                "level": "easy",
                "correct": true,
                "confidence": 0.95,
                "timeTaken": 2.5,
                "createdAt": "2025-01-27T14:22:00"
            },
            ...
        ]
    }
    """
    
    try:
        user_id = request.view_args.get('userId')
        limit = request.args.get('limit', 10, type=int)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'userId is required'
            }), 400
        
        attempts = mongodb_manager.get_recent_attempts(user_id, limit=limit)
        
        # Convert ObjectIds to strings for JSON serialization
        attempts_clean = []
        for attempt in attempts:
            attempt['_id'] = str(attempt['_id'])
            attempt['userId'] = str(attempt['userId'])
            attempts_clean.append(attempt)
        
        return jsonify({
            'success': True,
            'attempts': attempts_clean
        }), 200
    
    except Exception as e:
        print(f"❌ Error getting recent attempts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================
# 6. UPDATED PROGRESS REPORT (MONGODB VERSION)
# ========================
# Replace the existing progress_report endpoint in app.py with this version

def progress_report_mongodb_version():
    """
    POST /api/ai/progress-report
    Generate comprehensive progress report from MongoDB data
    
    Frontend sends:
    {
        "userId": "507f1f77bcf86cd799439011"
    }
    
    Returns comprehensive analytics including:
    - Overall accuracy and performance
    - Level-by-level breakdown
    - Word-level performance
    - Skill gaps and recommendations
    - Achievements and insights
    - Predictions for next level
    """
    
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'userId is required'
            }), 400
        
        # ========================
        # Get all user statistics from MongoDB
        # ========================
        
        overall_stats = mongodb_manager.get_user_stats(user_id)
        word_stats = mongodb_manager.get_word_stats(user_id)
        
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
                    'message': 'No attempts recorded yet. Start playing to generate analytics!'
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
        # SKILL GAPS (Words with low accuracy)
        # ========================
        
        skill_gaps = []
        if word_stats:
            for word in word_stats:
                if word['accuracy'] < 70:
                    skill_gaps.append({
                        'word': word['word'],
                        'sinhalaWord': word['sinhalaWord'],
                        'english': word['englishTranslation'],
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
        # RECOMMENDATIONS (Words to practice)
        # ========================
        
        recommendations = []
        if word_stats:
            for word in word_stats:
                accuracy = word['accuracy']
                if 50 <= accuracy < 85:
                    recommendations.append({
                        'word': word['word'],
                        'sinhalaWord': word['sinhalaWord'],
                        'english': word['englishTranslation'],
                        'level': word['level'],
                        'accuracy': round(accuracy, 1),
                        'priority': 1 if accuracy < 70 else 2,
                        'reason': 'Good progress! Keep practicing to master this sign.'
                    })
        
        recommendations.sort(key=lambda x: (x['priority'], -x['accuracy']))
        
        # ========================
        # CURRENT LEVEL DETERMINATION
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
        
        # ========================
        # AI PREDICTIONS
        # ========================
        
        next_level_score = min(accuracy + 10, 95)
        confidence = 75 if total_attempts >= 10 else 50
        time_to_master = "2-3 weeks" if accuracy >= 60 else "3-4 weeks"
        
        # Playtime estimate
        total_playtime_minutes = int(total_attempts * 1.5)
        
        # Calculate streak (check recent days)
        recent = mongodb_manager.get_recent_attempts(user_id, limit=100)
        recent_dates = set()
        if recent:
            for attempt in recent:
                attempt_date = attempt['createdAt'].date() if isinstance(attempt['createdAt'], datetime) else attempt['createdAt']
                recent_dates.add(attempt_date)
        current_streak = len(recent_dates)
        
        # ========================
        # BUILD FINAL REPORT
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
            'recommendations': recommendations[:5],
            'next_level_unlocked': None
        }
        
        print(f"✅ Generated report for {user_id}: {words_learned} words, {accuracy:.1f}% accuracy")
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
    
    except Exception as e:
        print(f"❌ Error generating progress report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================
# 7. INTEGRATION INSTRUCTIONS FOR app.py
# ========================
"""
STEPS TO INTEGRATE INTO YOUR EXISTING app.py:

1. At the top of app.py, add:
   ================================
   from mongodb_integration import mongodb_manager
   from bson.objectid import ObjectId
   
   2. Replace the existing progress_report endpoint with progress_report_mongodb_version()
   
   3. Add these new endpoints:
   ================================
   @app.route('/api/game/attempt', methods=['POST'])
   def save_attempt():
       return save_game_attempt_example()
   
   @app.route('/api/game/user-stats/<user_id>', methods=['GET'])
   def user_stats(user_id):
       request.view_args = {'userId': user_id}
       return get_user_stats_example()
   
   @app.route('/api/game/level-stats/<user_id>/<level>', methods=['GET'])
   def level_stats(user_id, level):
       request.view_args = {'userId': user_id, 'level': level}
       return get_level_stats_example()
   
   @app.route('/api/game/word-stats/<user_id>', methods=['GET'])
   def word_stats(user_id):
       request.view_args = {'userId': user_id}
       return get_word_stats_example()
   
   @app.route('/api/game/recent-attempts/<user_id>', methods=['GET'])
   def recent_attempts(user_id):
       request.view_args = {'userId': user_id}
       return get_recent_attempts_example()
   
   @app.route('/api/ai/progress-report', methods=['POST'])
   def progress_report():
       return progress_report_mongodb_version()
   
   4. At shutdown, add:
   ================================
   @app.teardown_appcontext
   def shutdown_session(exception=None):
       mongodb_manager.disconnect()
   
   5. Test the endpoints with frontend requests that include userId
"""
