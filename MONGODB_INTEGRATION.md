# MongoDB Integration Guide: Express + Flask Backend Architecture

## Overview

This guide integrates your two separate backend systems (Express.js and Flask) through MongoDB, creating a unified data architecture while maintaining each system's specialized responsibilities.

### Current Problems
- ❌ Flask uses in-memory storage → data lost on restart
- ❌ Two backends don't communicate
- ❌ No shared user ID system between backends
- ❌ Game progress not accessible from Express.js dashboard
- ❌ Analytics dashboard expects MongoDB data

### Solution
- ✅ MongoDB as shared database for game attempts
- ✅ Express.js handles authentication and user management (unchanged)
- ✅ Flask handles game logic and AI analytics
- ✅ Both backends use same MongoDB userId (ObjectId from Express)
- ✅ Persistent storage for game progress

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│                 http://localhost:3000 or 5173                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐        ┌──────────────────┐
│ Express.js       │        │  Flask           │
│ (Port 5000)      │        │  (Port 5001)     │
├──────────────────┤        ├──────────────────┤
│ • Login/Register │        │ • Game Logic     │
│ • User Profile   │        │ • AI Analytics   │
│ • Quiz Data      │        │ • Progress Gen   │
│ • GameProfile    │        │ • Hints/Feedback │
└────────┬─────────┘        └────────┬─────────┘
         │                           │
         └───────────────┬───────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │     MongoDB         │
              ├─────────────────────┤
              │ • users (Express)   │
              │ • gameProfiles      │
              │ • gameAttempts ◄─── │ (NEW - shared)
              │ • questions         │
              └─────────────────────┘

DATA FLOW:
1. User logs in via Express → receives MongoDB userId
2. Frontend makes game request to Flask with userId
3. Flask saves attempt to MongoDB (via mongodb_integration.py)
4. Flask queries MongoDB for analytics
5. Express.js can also query MongoDB for dashboard
```

---

## Step 1: Install Python Dependencies

Add MongoDB Python driver to Flask environment:

```bash
pip install pymongo
```

Update your `Backend/requirements.txt`:
```
pymongo>=4.5.0
```

---

## Step 2: Environment Variables

Both Express.js and Flask need the same MongoDB URI. Update your `.env` files:

**Express.js** (`.env`):
```env
MONGODB_URI=mongodb://localhost:27017/
```

**Flask** (`.env` or use same):
```env
MONGODB_URI=mongodb://localhost:27017/
```

If using MongoDB Atlas (cloud):
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/sinhala_game_db
```

---

## Step 3: MongoDB Schema

The GameAttempt schema is defined in `Backend/model/GameAttempt.js` and is automatically created by MongoDB when first document is inserted.

**Fields:**
- `userId`: MongoDB ObjectId reference to user (Index: fast queries)
- `level`: Level of difficulty (Index: for level analysis)
- `word`: Sinhala word (Index: for word performance)
- `sinhalaWord`: Sinhala script version
- `englishTranslation`: English meaning
- `correct`: Boolean (Index: for accuracy calculation)
- `confidence`: 0-100 score from AI model
- `timeTaken`: Seconds
- `attemptNumber`: 1st, 2nd, etc. attempt
- `hintsProvided`: Array of hints given
- `feedbackGiven`: Feedback message
- `sessionId`: Groups attempts in same session
- `createdAt`: Timestamp (Index: for time-series queries)
- `updatedAt`: Timestamp

**Indexes Created:**
- `userId + createdAt` → Quick access to user's recent attempts
- `userId + level + correct` → Level analysis and accuracy
- `userId + word` → Word performance tracking

---

## Step 4: Python MongoDB Integration Module

The file `Backend/mongodb_integration.py` provides:

1. **MongoDBManager class** - Main interface for all MongoDB operations
2. **InMemoryAttemptStorage class** - Fallback if MongoDB unavailable
3. **Global instance** - `mongodb_manager` ready to use

### Key Methods:

```python
# Save a game attempt
mongodb_manager.save_game_attempt({
    'userId': '507f1f77bcf86cd799439011',
    'level': 'easy',
    'word': 'good',
    'correct': True,
    'confidence': 0.95,
    'timeTaken': 2.5
})

# Get overall user stats
stats = mongodb_manager.get_user_stats(user_id)
# Returns: {'totalAttempts': 150, 'wordsLearned': 45, 'overallAccuracy': 80.0, ...}

# Get level-specific stats
level_stats = mongodb_manager.get_level_stats(user_id, 'easy')
# Returns: {'total': 50, 'correct': 42, 'accuracy': 84.0, ...}

# Get performance per word
word_stats = mongodb_manager.get_word_stats(user_id)
# Returns: [{'word': 'good', 'accuracy': 87.5, 'total': 8, ...}, ...]

# Get recent attempts
recent = mongodb_manager.get_recent_attempts(user_id, limit=10)

# Check if user is struggling with word
struggling = mongodb_manager.is_struggling(user_id, word='good', level='easy')
```

---

## Step 5: Update Flask app.py

### 5a. Import MongoDB Manager

Add to top of `Backend/app.py`:

```python
from mongodb_integration import mongodb_manager
from bson.objectid import ObjectId
```

### 5b. Replace Game Attempt Saving

**OLD (In-memory):**
```python
@app.route('/api/game/attempt', methods=['POST'])
def save_attempt():
    user_id = request.json.get('userId')
    struggle_detector.record_attempt(user_id, word, level, correct, time_taken)
    # Data lost on restart!
```

**NEW (MongoDB):**
```python
@app.route('/api/game/attempt', methods=['POST'])
def save_attempt():
    data = request.get_json()
    
    attempt_data = {
        'userId': data['userId'],  # From Express login
        'level': data['level'],
        'word': data['word'],
        'sinhalaWord': data.get('sinhalaWord'),
        'englishTranslation': data.get('englishTranslation'),
        'correct': data['correct'],
        'confidence': float(data.get('confidence', 0)),
        'timeTaken': float(data.get('timeTaken', 0)),
        'hintsProvided': data.get('hintsProvided', []),
        'sessionId': data.get('sessionId')
    }
    
    result = mongodb_manager.save_game_attempt(attempt_data)
    
    if result:
        is_struggling = mongodb_manager.is_struggling(
            data['userId'],
            data['word'],
            data['level']
        )
        return jsonify({
            'success': True,
            'isStruggling': is_struggling
        }), 201
    else:
        return jsonify({'success': False, 'error': 'Failed to save'}), 500
```

### 5c. Add New Endpoints

```python
@app.route('/api/game/user-stats/<user_id>', methods=['GET'])
def get_user_stats(user_id):
    """Get overall stats from MongoDB"""
    stats = mongodb_manager.get_user_stats(user_id)
    return jsonify({'success': True, 'stats': stats}), 200

@app.route('/api/game/level-stats/<user_id>/<level>', methods=['GET'])
def get_level_stats(user_id, level):
    """Get level-specific stats from MongoDB"""
    stats = mongodb_manager.get_level_stats(user_id, level)
    return jsonify({'success': True, 'level': level, 'stats': stats}), 200

@app.route('/api/game/word-stats/<user_id>', methods=['GET'])
def get_word_stats(user_id):
    """Get word-level performance from MongoDB"""
    word_stats = mongodb_manager.get_word_stats(user_id)
    return jsonify({'success': True, 'words': word_stats}), 200
```

### 5d. Update Progress Report Endpoint

Replace your existing progress report endpoint with the MongoDB version:

```python
@app.route('/api/ai/progress-report', methods=['POST'])
def progress_report():
    """Generate analytics from MongoDB data"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'userId required'}), 400
        
        # Get stats from MongoDB (not in-memory)
        overall_stats = mongodb_manager.get_user_stats(user_id)
        word_stats = mongodb_manager.get_word_stats(user_id)
        
        if not overall_stats or overall_stats.get('totalAttempts', 0) == 0:
            return jsonify({
                'success': True,
                'report': {'summary': {'words_learned': 0, 'overall_accuracy': 0}}
            }), 200
        
        # Calculate level progress
        level_progress = {}
        for level in ['basic', 'easy', 'medium', 'hard']:
            stats = mongodb_manager.get_level_stats(user_id, level)
            level_progress[level] = {
                'level': level,
                'total': stats['total'],
                'correct': stats['correct'],
                'accuracy': round(stats['accuracy'], 1),
                'status': 'completed' if stats['accuracy'] >= 70 else 'in-progress'
            }
        
        # Build and return report
        report = {
            'summary': {
                'words_learned': overall_stats['wordsLearned'],
                'overall_accuracy': round(overall_stats['overallAccuracy'], 1),
                'total_attempts': overall_stats['totalAttempts'],
                'correct_attempts': overall_stats['correctAttempts']
            },
            'level_progress': level_progress
            # ... add other fields as needed
        }
        
        return jsonify({'success': True, 'report': report}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 5e. Remove In-Memory Storage

You can now remove or comment out:
```python
# OLD - No longer needed
# struggle_detector = StruggleDetector()
# user_game_states = {}
```

---

## Step 6: Frontend Integration

The frontend (React) needs to send `userId` with game requests:

```javascript
// After user logs in with Express.js, get userId
const { userId } = loginResponse.user; // MongoDB ObjectId

// Save game attempt to Flask
const attemptResponse = await fetch('http://localhost:5001/api/game/attempt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        userId: userId,              // ← Send MongoDB userId
        level: 'easy',
        word: 'good',
        sinhalaWord: 'හොඳ',
        englishTranslation: 'Good',
        correct: true,
        confidence: 0.95,
        timeTaken: 2.5,
        hintsProvided: [],
        sessionId: sessionId
    })
});

// Get progress report
const reportResponse = await fetch('http://localhost:5001/api/ai/progress-report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        userId: userId  // ← Same MongoDB ObjectId
    })
});
```

---

## Step 7: Express.js Dashboard Integration

Now Express.js can also query game data:

```javascript
// In Express.js route
const GameAttempt = require('./model/GameAttempt');

router.get('/api/dashboard/user-progress/:userId', async (req, res) => {
    try {
        // Get user's overall stats from MongoDB
        const stats = await GameAttempt.getUserStats(req.params.userId);
        
        // Get word performance
        const wordPerf = await GameAttempt.getWordStats(req.params.userId);
        
        // Get recent attempts
        const recent = await GameAttempt.getRecentAttempts(req.params.userId, 10);
        
        res.json({
            success: true,
            overallStats: stats,
            wordPerformance: wordPerf,
            recentAttempts: recent
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
```

---

## Step 8: Testing

### Test Save Attempt

```bash
curl -X POST http://localhost:5001/api/game/attempt \
  -H "Content-Type: application/json" \
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
```

### Test Get User Stats

```bash
curl http://localhost:5001/api/game/user-stats/507f1f77bcf86cd799439011
```

### Test Progress Report

```bash
curl -X POST http://localhost:5001/api/ai/progress-report \
  -H "Content-Type: application/json" \
  -d '{"userId": "507f1f77bcf86cd799439011"}'
```

---

## Step 9: Migration (if you have existing in-memory data)

If you want to migrate old in-memory data:

```python
# Run once to migrate historical data
from mongodb_integration import mongodb_manager
from datetime import datetime, timedelta

def migrate_old_data():
    """Migrate data from struggle_detector to MongoDB"""
    # This depends on your current data structure
    # Example assuming old format:
    for user_id, attempts in struggle_detector.attempt_history.items():
        for attempt in attempts:
            mongodb_manager.save_game_attempt({
                'userId': user_id,
                'level': attempt.get('level'),
                'word': attempt.get('word'),
                'correct': attempt.get('correct'),
                'timeTaken': attempt.get('time_taken', 0),
                'createdAt': attempt.get('timestamp', datetime.now())
            })
    print("✅ Migration complete")

# Call once, then remove
# migrate_old_data()
```

---

## Troubleshooting

### "MongoDB Connection Error"
- Check MongoDB is running: `mongosh` or check MongoDB Atlas
- Verify `MONGODB_URI` in `.env`
- Check firewall/network access

### "ObjectId Error"
- Ensure userId is valid MongoDB ObjectId format
- Convert string to ObjectId: `ObjectId(user_id_string)`
- Frontend must send valid ObjectId from Express.js

### "Indexes not created"
- Indexes are created automatically on first insert
- Or manually: `db.game_attempts.createIndex({'userId': 1, 'createdAt': -1})`

### Data still being lost
- Verify MongoDB is connected (check console logs)
- Check `save_game_attempt` is being called (not old in-memory code)
- Verify `createdAt` field is being saved

---

## Benefits of This Architecture

| Aspect | Before | After |
|--------|--------|-------|
| **Data Persistence** | Lost on Flask restart | Persistent in MongoDB |
| **Scalability** | Limited to single Flask instance | Multiple instances can share data |
| **User ID System** | Separate in each backend | Unified MongoDB ObjectId |
| **Data Sharing** | No communication | Express.js can query game data |
| **Analytics** | In-memory only | Persistent, queryable |
| **Performance** | O(n) in-memory searches | Indexed MongoDB queries |
| **Reliability** | Data loss on crash | ACID transactions |

---

## Summary of Changes

1. ✅ Created `GameAttempt.js` MongoDB schema
2. ✅ Created `mongodb_integration.py` for Flask-MongoDB connection
3. ✅ Created `flask_mongodb_examples.py` with endpoint examples
4. ✅ Both backends now use MongoDB ObjectId from Express
5. ✅ Game progress persists across restarts
6. ✅ Analytics generated from persistent data
7. ✅ Ready for Express.js dashboard integration

---

## Files Modified/Created

- **NEW**: `Backend/model/GameAttempt.js` - MongoDB schema
- **NEW**: `Backend/mongodb_integration.py` - Flask MongoDB manager
- **NEW**: `Backend/flask_mongodb_examples.py` - Endpoint examples
- **NEW**: `MONGODB_INTEGRATION.md` - This guide
- **UPDATE**: `Backend/app.py` - Add imports and endpoints
- **UPDATE**: `.env` - Add MONGODB_URI if needed
- **UPDATE**: `Backend/requirements.txt` - Add pymongo

---

## Next Steps

1. Install `pymongo` in your Flask environment
2. Add MongoDB connection string to `.env`
3. Import `mongodb_integration.py` in Flask `app.py`
4. Replace in-memory game attempt storage with MongoDB calls
5. Update progress report endpoint to query MongoDB
6. Test endpoints with valid userId from Express.js
7. Integrate with React frontend to send userId with game requests
8. Update Express.js dashboard to query game data from MongoDB

---

**Status**: ✅ Architecture designed and implementation code ready
**Next Action**: Integrate into your existing `app.py` following the examples provided
