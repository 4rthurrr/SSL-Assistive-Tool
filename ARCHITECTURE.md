# Complete Architecture Guide: Unified Backend System

## Problem Statement

Your current system has **two disconnected backend systems** that don't share data:

```
BEFORE (BROKEN ARCHITECTURE):
══════════════════════════════════════════════════════════════

┌─────────────────┐         ┌──────────────────┐
│  Express.js     │         │   Flask          │
│  (Port 5000)    │         │   (Port 5001)    │
├─────────────────┤         ├──────────────────┤
│ Users           │         │ Game Attempts    │
│ Authentication  │         │ (IN-MEMORY!)     │
│ GameProfile     │         │ Analytics        │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         │                           │
    ┌────▼────┐                 ┌────▼────┐
    │ MongoDB  │                │ Python   │
    │ (users)  │                │ Memory   │
    └──────────┘                └──────────┘

PROBLEMS:
❌ No shared user ID system
❌ No communication between backends
❌ Flask data lost on restart
❌ Analytics can't access persistent data
❌ Scalability issues (single Flask instance)
❌ No unified data source
```

## Solution: Unified Data Architecture

```
AFTER (UNIFIED ARCHITECTURE):
══════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│              http://localhost:3000/5173                  │
└─────────────────────┬──────────────────────────────────┘
                      │
                      │ (send userId with requests)
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌──────────────────┐      ┌──────────────────┐
│  Express.js      │      │  Flask           │
│  Port 5000       │      │  Port 5001       │
├──────────────────┤      ├──────────────────┤
│ ✓ Auth/Login     │      │ ✓ Game Logic     │
│ ✓ User Mgmt      │      │ ✓ AI Analytics   │
│ ✓ GameProfile    │      │ ✓ Hint System    │
│ ✓ Quizzes        │      │ ✓ Model Inference│
│ ✓ Dashboard      │      │ ✓ Feedback       │
│                  │      │                  │
│ Uses userId to   │      │ Queries MongoDB  │
│ query game data  │      │ with userId      │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         └────────────┬────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │     MONGODB            │
         │   (Unified Data)       │
         ├────────────────────────┤
         │ Collections:           │
         │ ├─ users (Express)     │
         │ ├─ gameProfiles        │
         │ ├─ gameAttempts ◄──────┼─ NEW! Both backends
         │ ├─ quizzes            │    use this collection
         │ └─ questions          │
         │                        │
         │ Shared Key: userId     │
         │ (MongoDB ObjectId)     │
         └────────────────────────┘

BENEFITS:
✅ Unified user ID system (MongoDB ObjectId)
✅ Persistent game data across Flask restarts
✅ Both backends read from same source
✅ Scalable (multiple Flask instances work)
✅ Real-time analytics possible
✅ Dashboard integration ready
✅ Better data integrity
```

---

## Data Flow Example: User Playing Game

```
┌─────────────────────────────────────────────────────────────┐
│                   USER JOURNEY                              │
└─────────────────────────────────────────────────────────────┘

STEP 1: USER REGISTRATION & LOGIN
────────────────────────────────────────────────────────────
Frontend (React)
    │
    ├─► POST /api/users/register
    │   └─► Backend: Express.js
    │       └─► Creates user in MongoDB
    │           └─► Returns: { userId: "507f...", token: "..." }
    │
    └─► Frontend stores userId and token


STEP 2: USER STARTS PLAYING GAME
────────────────────────────────────────────────────────────
Frontend (React)
    │
    ├─► GET /sign-language-game
    │   └─► Loads game interface
    │
    └─► Sends userId to Flask with game request


STEP 3: USER ATTEMPTS A WORD
────────────────────────────────────────────────────────────
Frontend (React)
    │
    ├─► Records: Hand position data, video, timing
    │
    ├─► Sends to Flask:
    │   POST /api/game/attempt
    │   {
    │     "userId": "507f...",         ◄─ MongoDB ObjectId
    │     "level": "easy",
    │     "word": "good",
    │     "correct": true,
    │     "confidence": 0.95
    │   }
    │
    └─► Flask processes:
        │
        ├─► 1. Receives request with userId
        │
        ├─► 2. Validates MongoDB ObjectId format
        │
        ├─► 3. Saves to MongoDB:
        │   db.gameAttempts.insert({
        │     userId: ObjectId("507f..."),
        │     level: "easy",
        │     word: "good",
        │     correct: true,
        │     confidence: 0.95,
        │     createdAt: Date.now()
        │   })
        │
        ├─► 4. Queries MongoDB for struggle detection:
        │   db.gameAttempts.find({
        │     userId: ObjectId("507f..."),
        │     word: "good",
        │     level: "easy"
        │   }).limit(5).sort({createdAt: -1})
        │
        ├─► 5. Detects: User struggling (3 failures in last 5)
        │
        └─► 6. Returns to Frontend:
            {
              "success": true,
              "isStruggling": true,
              "message": "Attempt saved"
            }


STEP 4: USER REQUESTS PROGRESS REPORT
────────────────────────────────────────────────────────────
Frontend (React)
    │
    ├─► POST /api/ai/progress-report
    │   { "userId": "507f..." }
    │
    └─► Flask queries MongoDB:
        │
        ├─► 1. Overall stats:
        │   db.gameAttempts.aggregate([
        │     { $match: { userId: ObjectId("507f...") } },
        │     { $group: {
        │         _id: null,
        │         totalAttempts: { $sum: 1 },
        │         correct: { $sum: { $cond: ["$correct", 1, 0] } }
        │       }
        │     }
        │   ])
        │
        ├─► 2. Level progress:
        │   Same query, but group by level
        │
        ├─► 3. Word performance:
        │   Group by word, calculate accuracy per word
        │
        └─► Returns comprehensive report:
            {
              "summary": {
                "words_learned": 45,
                "overall_accuracy": 82.5,
                "total_attempts": 150
              },
              "level_progress": {...},
              "skill_gaps": [...],
              "recommendations": [...]
            }


STEP 5: EXPRESS.JS DASHBOARD QUERIES GAME DATA
────────────────────────────────────────────────────────────
Dashboard User (Parent/Teacher)
    │
    ├─► GET /api/dashboard/user-progress/:userId
    │   └─► Express.js route:
    │       └─► Queries MongoDB directly:
    │           db.gameAttempts.find({userId: ObjectId("507f...")})
    │
    └─► Returns game progress to show alongside user info


STEP 6: FLASK RESTART - DATA PERSISTS
────────────────────────────────────────────────────────────
Admin restarts Flask server
    │
    ├─► Flask shuts down
    │   └─► OLD: All in-memory data lost ❌
    │
    ├─► Flask starts again
    │   └─► Connects to MongoDB
    │
    └─► User's data still there!
        └─► NEW: All attempts still in MongoDB ✅


┌─────────────────────────────────────────────────────────────┐
│  KEY INSIGHT: userId is the unique identifier everywhere    │
│  Express generates it from user registration                 │
│  Both backends use it to read/write to same MongoDB docs     │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Model: Game Attempt Document

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  
  // REFERENCE TO USER (Shared Identifier)
  "userId": ObjectId("507f1f77bcf86cd799439011"),
  
  // GAME CONTEXT
  "level": "easy",
  "word": "good",
  "sinhalaWord": "හොඳ",
  "englishTranslation": "Good",
  "sessionId": "session_abc123",
  
  // ATTEMPT RESULT
  "correct": true,
  "confidence": 0.95,      // 0-100 from ML model
  "timeTaken": 2.5,         // seconds
  "attemptNumber": 3,       // 1st, 2nd, 3rd attempt, etc
  
  // FEEDBACK & HINTS
  "hintsProvided": [
    "Watch the sign video carefully",
    "Focus on hand positions"
  ],
  "feedbackGiven": "Great attempt! Your hand position was correct.",
  
  // METADATA
  "modelVersion": "lstm_v1.0",
  "createdAt": ISODate("2025-01-27T14:22:30.123Z"),
  "updatedAt": ISODate("2025-01-27T14:22:30.123Z")
}
```

**Why This Structure:**
- `userId` links to Express.js user → Enables Express dashboard
- Indexed fields (`userId`, `createdAt`, `level`) → Fast queries
- Stores complete context → No need to reconstruct logic
- Timestamps → Enable streak detection, progress over time
- Confidence scores → Enable ML-driven adaptive difficulty

---

## API Endpoints

### Express.js Endpoints (Unchanged)
```
POST   /api/users/register       - Create new user
POST   /api/users/login          - Authenticate user
GET    /api/users/:userId        - Get user profile
POST   /api/gameProfile          - Create/update game profile
```

### Flask Endpoints (New MongoDB-backed)
```
POST   /api/game/attempt                  - Save game attempt
GET    /api/game/user-stats/:userId       - Get user overall stats
GET    /api/game/level-stats/:userId/:level - Get level progress
GET    /api/game/word-stats/:userId       - Get word performance
GET    /api/game/recent-attempts/:userId  - Get activity feed
POST   /api/ai/progress-report            - Generate analytics report
```

### Express.js Dashboard Endpoints (Can Now Be Added)
```
GET    /api/dashboard/user-progress/:userId - Query game data
GET    /api/dashboard/class-analytics      - Aggregate student data
GET    /api/dashboard/trends               - Historical progress
```

---

## MongoDB Indexes (Automatically Created)

```javascript
// Composite indexes for common query patterns

// 1. User's recent attempts (fast activity feed)
db.gameAttempts.createIndex({ userId: 1, createdAt: -1 })

// 2. Level analysis and accuracy (fast analytics)
db.gameAttempts.createIndex({ userId: 1, level: 1, correct: 1 })

// 3. Word performance tracking (fast per-word stats)
db.gameAttempts.createIndex({ userId: 1, word: 1 })

// These enable queries like:
// - Find all attempts for user (sorted by time): ~10ms
// - Calculate level accuracy: ~15ms
// - Get performance by word: ~10ms
```

---

## Implementation Sequence

```
PHASE 1: Setup (30 minutes)
├─ Install pymongo: pip install pymongo
├─ Create mongodb_integration.py
├─ Create GameAttempt.js schema
├─ Update .env with MONGODB_URI
└─ Test MongoDB connection

PHASE 2: Flask Integration (1 hour)
├─ Import mongodb_integration in app.py
├─ Replace in-memory storage with MongoDB
├─ Add new endpoints (save attempt, get stats)
├─ Update progress_report to query MongoDB
├─ Test endpoints with Postman/curl
└─ Verify data persists after Flask restart

PHASE 3: Frontend Updates (30 minutes)
├─ Get userId from Express login response
├─ Send userId with game attempt requests
├─ Send userId with analytics requests
└─ Test end-to-end flow

PHASE 4: Express Dashboard (30 minutes)
├─ Create new endpoints to query gameAttempts
├─ Update dashboard to show game progress
├─ Link user info with game statistics
└─ Test dashboard functionality

TOTAL: ~2-2.5 hours implementation + testing
```

---

## Benefits Over Current Architecture

| Aspect | Current (In-Memory) | New (MongoDB) |
|--------|-------------------|---------------|
| **Data Persistence** | Lost on restart | Persistent forever |
| **Query Speed** | O(n) linear | O(1) indexed lookup |
| **Scalability** | Single Flask instance | Multiple instances |
| **Data Sharing** | No | Full access to all data |
| **User ID System** | Separate | Unified ObjectId |
| **Analytics** | Limited in-memory | Rich MongoDB aggregations |
| **Concurrent Users** | Limited | Unlimited |
| **Backup/Recovery** | None | MongoDB backup tools |
| **API Documentation** | None | Clear schema & examples |
| **Dashboard Integration** | Not possible | Easy from Express |

---

## Troubleshooting Common Issues

### Issue: "MongoDB Connection Error"
```
Solution:
1. Verify MongoDB is running: mongosh or check MongoDB Compass
2. Check MONGODB_URI format in .env
3. If using MongoDB Atlas, check IP whitelist
4. Check network connectivity to MongoDB server
```

### Issue: "ObjectId conversion error"
```
Solution:
1. Ensure userId from Express is valid MongoDB ObjectId
2. Use str_to_ObjectId() when needed
3. Frontend must send ObjectId string, not random ID
4. Check: print(type(user_id)) should be ObjectId
```

### Issue: "Data not being saved"
```
Solution:
1. Check MongoDB connection is successful (console logs)
2. Verify save_game_attempt() is being called (not old code)
3. Check MongoDB indexes are created
4. Verify createdAt timestamp is being set
5. Run: db.gameAttempts.find() in MongoDB to check data
```

### Issue: "Queries are slow"
```
Solution:
1. Ensure indexes are created (see MongoDB Indexes section)
2. Check query patterns in mongodb_integration.py
3. Use explain() to see query plan
4. Consider adding more indexes if needed
```

---

## Files Created/Modified

### New Files
- ✅ `Backend/model/GameAttempt.js` - MongoDB schema
- ✅ `Backend/mongodb_integration.py` - Flask MongoDB manager
- ✅ `Backend/flask_mongodb_examples.py` - Endpoint examples
- ✅ `Backend/INTEGRATION_CHECKLIST.py` - Implementation guide
- ✅ `Backend/requirements_updated.txt` - Updated dependencies
- ✅ `MONGODB_INTEGRATION.md` - Complete guide
- ✅ `ARCHITECTURE.md` - This file

### Modified Files
- 📝 `Backend/app.py` - Add imports, endpoints, remove in-memory storage
- 📝 `.env` - Add MONGODB_URI if not present

---

## Testing Checklist

- [ ] MongoDB running and accessible
- [ ] `pymongo` installed in Flask environment
- [ ] `mongodb_integration.py` in Backend folder
- [ ] Imports added to Flask `app.py`
- [ ] Old in-memory storage commented out
- [ ] New endpoints added to Flask
- [ ] Progress report endpoint updated
- [ ] Test save attempt endpoint
- [ ] Test get user stats endpoint
- [ ] Test progress report endpoint
- [ ] Data persists after Flask restart
- [ ] Frontend sends userId with requests
- [ ] Express dashboard can query game data

---

## Next Steps

1. **Install Dependencies**
   ```bash
   pip install pymongo
   ```

2. **Copy Integration Code**
   - Copy mongodb_integration.py to Backend/
   - Copy GameAttempt.js to Backend/model/

3. **Update Flask app.py**
   - Follow INTEGRATION_CHECKLIST.py
   - Replace in-memory with MongoDB calls

4. **Test Integration**
   - Run Flask and test endpoints
   - Verify data in MongoDB

5. **Update Frontend**
   - Send userId with game requests
   - Get userId from Express login

6. **Celebrate! 🎉**
   - Your system now has persistent, shared data

---

**Status**: ✅ Complete architecture designed and ready to implement
**Complexity**: Medium (mostly copy-paste with understanding)
**Time to implement**: 2-3 hours
**Support files**: 7 files with detailed comments and examples
