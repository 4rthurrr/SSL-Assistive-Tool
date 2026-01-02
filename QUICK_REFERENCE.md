# Quick Reference Guide

## File Structure After Implementation

```
d:\Game new\
├── Backend/
│   ├── app.js                              (Express - unchanged core)
│   ├── app.py                              (Flask - UPDATED with MongoDB)
│   ├── package.json
│   ├── requirements_updated.txt            (NEW - Add pymongo)
│   ├── INTEGRATION_CHECKLIST.py            (NEW - Copy code from here)
│   │
│   ├── model/
│   │   ├── usermodel.js                    (Express user schema)
│   │   ├── GameProfile.js                  (Express game profile)
│   │   ├── question_model.js
│   │   └── GameAttempt.js                  (NEW - MongoDB game attempts schema)
│   │
│   ├── mongodb_integration.py              (NEW - Flask MongoDB manager)
│   ├── flask_mongodb_examples.py           (NEW - Example endpoints)
│   │
│   └── ... (other files unchanged)
│
├── frontend/
│   └── ... (needs userId updates)
│
├── MONGODB_INTEGRATION.md                  (NEW - Complete guide)
├── ARCHITECTURE.md                         (NEW - System design)
└── IMPLEMENTATION_SUMMARY.md               (NEW - This file)
```

---

## Implementation Workflow

```
1️⃣  SETUP (5-10 min)
    ├─ pip install pymongo
    ├─ Verify MongoDB running
    └─ Check MONGODB_URI in .env

2️⃣  CREATE FILES (already done ✅)
    ├─ Backend/model/GameAttempt.js
    ├─ Backend/mongodb_integration.py
    └─ Backend/flask_mongodb_examples.py

3️⃣  UPDATE app.py (30 min)
    ├─ Add imports (2 lines)
    ├─ Remove old storage (comment out 2 lines)
    ├─ Add save endpoint (copy 30 lines)
    ├─ Add stat endpoints (copy 50 lines)
    ├─ Update progress endpoint (copy 100 lines)
    └─ Add shutdown handler (5 lines)

4️⃣  TEST INTEGRATION (20 min)
    ├─ Save attempt (curl test)
    ├─ Get user stats (curl test)
    ├─ Verify MongoDB has data
    └─ Restart Flask and verify persistence

5️⃣  UPDATE FRONTEND (20 min)
    ├─ Get userId from Express login
    ├─ Send userId with game requests
    └─ Test end-to-end flow

TOTAL: ~1.5 hours
```

---

## Code Snippets Quick Reference

### 1. Flask Imports (Add to top of app.py)
```python
from mongodb_integration import mongodb_manager
from bson.objectid import ObjectId
```

### 2. Remove Old Code (Comment out)
```python
# user_game_states = {}
# struggle_detector = StruggleDetector()
```

### 3. Save Game Attempt
```python
@app.route('/api/game/attempt', methods=['POST'])
def save_game_attempt():
    data = request.get_json()
    result = mongodb_manager.save_game_attempt({
        'userId': data['userId'],
        'level': data['level'],
        'word': data['word'],
        'correct': data['correct'],
        'confidence': float(data.get('confidence', 0))
    })
    return jsonify({'success': result is not None}), 201
```

### 4. Get User Stats
```python
@app.route('/api/game/user-stats/<user_id>', methods=['GET'])
def get_user_stats(user_id):
    stats = mongodb_manager.get_user_stats(user_id)
    return jsonify({'success': True, 'stats': stats}), 200
```

### 5. Frontend: Send userId
```javascript
// After login
const userId = loginResponse.user._id;

// With game request
fetch('http://localhost:5001/api/game/attempt', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    userId: userId,
    level: 'easy',
    word: 'good',
    correct: true
  })
});
```

---

## Database Query Examples

### Save Attempt (Flask)
```python
# What Flask does internally:
attempt_data = {
    'userId': ObjectId('507f1f77bcf86cd799439011'),
    'level': 'easy',
    'word': 'good',
    'correct': True,
    'confidence': 0.95,
    'createdAt': datetime.now()
}
result = mongodb_manager.game_attempts.insert_one(attempt_data)
```

### Get User Stats (Flask)
```python
# Query: Get all attempts for user
stats = mongodb_manager.get_user_stats(user_id)
# Returns: {'totalAttempts': 150, 'correctAttempts': 120, ...}
```

### Get Level Performance (Flask)
```python
# Query: How well is user doing in 'easy' level?
stats = mongodb_manager.get_level_stats(user_id, 'easy')
# Returns: {'total': 50, 'correct': 42, 'accuracy': 84.0, ...}
```

### Query from Express.js (Optional)
```javascript
// Can now query gameAttempts collection directly
const GameAttempt = require('./model/GameAttempt');
const stats = await GameAttempt.getUserStats(userId);
```

---

## MongoDB Schema Reference

```json
{
  "_id": ObjectId,
  "userId": ObjectId,        // Link to user (from Express)
  "level": "easy",
  "word": "good",
  "sinhalaWord": "හොඳ",
  "englishTranslation": "Good",
  "correct": true,
  "confidence": 0.95,        // 0-100
  "timeTaken": 2.5,          // seconds
  "attemptNumber": 1,        // 1st, 2nd, etc
  "hintsProvided": [],
  "feedbackGiven": "",
  "sessionId": "session_123",
  "createdAt": ISODate,
  "updatedAt": ISODate
}
```

---

## API Endpoints Summary

```
NEW FLASK ENDPOINTS:

POST   /api/game/attempt
       Save a game attempt to MongoDB
       Input: {userId, level, word, correct, confidence, ...}

GET    /api/game/user-stats/:userId
       Get overall user statistics
       Returns: {totalAttempts, wordsLearned, overallAccuracy, ...}

GET    /api/game/level-stats/:userId/:level
       Get performance for a specific level
       Returns: {total, correct, accuracy, avgTime, ...}

GET    /api/game/word-stats/:userId
       Get performance for each word
       Returns: [{word, accuracy, total, attempts, ...}, ...]

GET    /api/game/recent-attempts/:userId?limit=10
       Get recent attempts for activity feed
       Returns: [attempt objects]

POST   /api/ai/progress-report
       Generate comprehensive progress report (UPDATED - uses MongoDB)
       Returns: {summary, level_progress, achievements, ...}
```

---

## Troubleshooting Flowchart

```
Error: "MongoDB Connection Error"
  ├─ Check: mongosh or MongoDB Compass can connect?
  │  └─ If NO: Start MongoDB or check connection string
  └─ Check: MONGODB_URI in .env?
     └─ If NO: Add MONGODB_URI=mongodb://localhost:27017/

Error: "Invalid userId format"
  ├─ Check: userId is 24 hex characters?
  │  └─ If NO: Must be valid MongoDB ObjectId from Express
  └─ Check: Frontend is sending userId from login response?
     └─ If NO: Update frontend to send correct userId

Error: "Data not being saved"
  ├─ Check: save_game_attempt endpoint is being called?
  │  └─ Check: Flask logs show "✅ Saved attempt"
  ├─ Check: Old code is commented out?
  │  └─ If NO: Comment out struggle_detector and user_game_states
  └─ Check: MongoDB has gameAttempts collection?
     └─ Run: db.gameAttempts.find() in MongoDB

Error: "Data lost after Flask restart"
  ├─ Check: Old in-memory code is still running?
  │  └─ If YES: Comment out and restart Flask
  ├─ Check: MongoDB connection is persistent?
  │  └─ Verify: MONGODB_URI is correct
  └─ Check: Data is in MongoDB collection?
     └─ Run: db.gameAttempts.countDocuments() - should be > 0
```

---

## Files to Read in Order

1. **Start here**: `Backend/INTEGRATION_CHECKLIST.py`
   - Copy code snippets directly
   - Follow step-by-step instructions

2. **For overview**: `ARCHITECTURE.md`
   - Understand system design
   - See data flow diagrams

3. **For details**: `MONGODB_INTEGRATION.md`
   - Complete setup guide
   - Troubleshooting section

4. **For reference**: `Backend/mongodb_integration.py`
   - Understand MongoDB manager
   - Check available methods

5. **For examples**: `Backend/flask_mongodb_examples.py`
   - See endpoint patterns
   - Learn MongoDB queries

---

## Testing Commands

### Test Save Attempt
```bash
curl -X POST http://localhost:5001/api/game/attempt \
  -H "Content-Type: application/json" \
  -d '{
    "userId":"507f1f77bcf86cd799439011",
    "level":"easy",
    "word":"good",
    "correct":true,
    "confidence":0.95,
    "timeTaken":2.5
  }'

Expected: {"success": true}
```

### Test Get Stats
```bash
curl http://localhost:5001/api/game/user-stats/507f1f77bcf86cd799439011

Expected: {"success": true, "stats": {"totalAttempts": 1, ...}}
```

### Test Progress Report
```bash
curl -X POST http://localhost:5001/api/ai/progress-report \
  -H "Content-Type: application/json" \
  -d '{"userId":"507f1f77bcf86cd799439011"}'

Expected: {"success": true, "report": {...}}
```

### Check MongoDB Data
```bash
mongosh
use sinhala_game_db
db.gameAttempts.find()
db.gameAttempts.countDocuments()
```

---

## Environment Setup

### Install Dependencies
```bash
cd Backend
pip install pymongo
```

### Update requirements.txt
```
flask==2.3.0
flask-cors==4.0.0
pymongo>=4.5.0        ← NEW
torch==2.0.0
numpy==1.24.0
```

### .env Configuration
```
MONGODB_URI=mongodb://localhost:27017/
# OR for MongoDB Atlas:
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/sinhala_game_db
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (React)                                            │
│ - User logs in with Express                                 │
│ - Gets userId (MongoDB ObjectId)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ (includes userId)
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
    ┌────────────┐             ┌──────────────┐
    │ Express.js │             │ Flask        │
    │ Port 5000  │             │ Port 5001    │
    └─────┬──────┘             └────────┬─────┘
          │                             │
          │ (returns userId)            │ (queries/saves to)
          │                             │
          └──────────────┬──────────────┘
                         │
                         ▼
                  ┌────────────────┐
                  │ MongoDB        │
                  │ - users        │
                  │ - gameAttempts │ ◄─ Shared data
                  │ - profiles     │
                  └────────────────┘
```

---

## Checklist Before Starting

- [ ] MongoDB is running (check with `mongosh`)
- [ ] Python environment is set up
- [ ] All created files are in correct locations
- [ ] `.env` file has `MONGODB_URI` set
- [ ] You have `pip show pymongo` installed
- [ ] You have a userId from Express login for testing
- [ ] You've read `Backend/INTEGRATION_CHECKLIST.py`
- [ ] You understand the data flow
- [ ] You're ready to modify `Backend/app.py`

---

## Success Indicators

After implementation:
- ✅ Flask starts without errors
- ✅ `mongodb_integration` imports successfully
- ✅ Can save game attempt via API
- ✅ Data appears in MongoDB collection
- ✅ Get stats endpoint returns data
- ✅ Progress report generates from MongoDB
- ✅ Data persists after Flask restart
- ✅ Frontend receives correct responses
- ✅ No `struggle_detector` errors in logs
- ✅ MongoDB indexes are created

---

## Time Estimate by Task

| Task | Time | Difficulty |
|------|------|-----------|
| Install pymongo | 2 min | ⭐ |
| Set up .env | 3 min | ⭐ |
| Copy files to Backend/ | 2 min | ⭐ |
| Update app.py imports | 3 min | ⭐ |
| Remove old code | 3 min | ⭐ |
| Add save endpoint | 10 min | ⭐⭐ |
| Add stat endpoints | 10 min | ⭐⭐ |
| Update progress endpoint | 15 min | ⭐⭐ |
| Test endpoints | 15 min | ⭐⭐ |
| Update frontend | 15 min | ⭐⭐ |
| **TOTAL** | **~90 min** | **Medium** |

---

## Next.js (After MongoDB Integration)

- Express.js dashboard to show game progress
- Real-time analytics and trends
- Advanced student performance analysis
- Teacher/parent reporting
- Mobile app compatibility

---

**Good luck! You've got this! 🚀**
