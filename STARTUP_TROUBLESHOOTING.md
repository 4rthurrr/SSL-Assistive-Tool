# 🔧 Troubleshooting Guide - Getting Apps Running

## Current Issues & Fixes

### Issue 1: MongoDB Connection Error ❌
```
❌ MongoDB Connection Error: querySrv ENOTFOUND _mongodb._tcp.cluster0.8tb8jax.mongodb.net
```

**Root Cause**: DNS resolution failing for MongoDB Atlas

**Quick Fixes** (choose one):

#### Option A: Use Local MongoDB (Recommended for Development)
```bash
# 1. Install MongoDB Community (if not already)
# Download from: https://www.mongodb.com/try/download/community

# 2. Start MongoDB
mongod

# 3. In another terminal, verify it's running
mongosh

# 4. Update .env to use local MongoDB
```

Edit `Backend/.env`:
```env
MONGODB_URI=mongodb://localhost:27017/sinhala_game_db
```

Then restart Express.js:
```bash
npm run dev  # in root directory
```

#### Option B: Fix MongoDB Atlas Connection
1. Go to: https://cloud.mongodb.com/
2. Log in to your cluster
3. Click "Network Access" in left sidebar
4. Click "Add IP Address"
5. Select "Allow access from anywhere" (for dev only!)
6. Wait 5-10 minutes for changes to apply
7. Restart Express.js

#### Option C: Check Internet Connection
```bash
# Test DNS resolution
nslookup cluster0.8tb8jax.mongodb.net

# If that fails, check internet
ping 8.8.8.8
```

---

### Issue 2: Flask Unicode Encoding Error ❌
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4c1'
```

**Status**: ✅ FIXED!

I added Unicode handling to `Backend/app.py`. Flask should now start without this error.

**Verify the fix**: Look for this in `Backend/app.py` lines 1-20:
```python
import sys
import io

# Fix Unicode encoding for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

---

## ✅ How to Start Everything Correctly

### Step 1: Start MongoDB (Local)
```bash
# Terminal 1: Start MongoDB
mongod
# Should see: "waiting for connections on port 27017"
```

### Step 2: Start Backend (Express.js)
```bash
# Terminal 2: In project root
npm run dev
# Should see: ✅ MongoDB Connected Successfully
```

### Step 3: Start Frontend (React)
```bash
# Terminal 3: In project root  
npm run dev
# Should see: ➜ Local: http://localhost:5173/
```

### Step 4: Verify Everything Works
```bash
# Test Express.js health check
curl http://localhost:5000/api/health

# Test MongoDB connection
mongosh
use sinhala_game_db
db.users.find()
```

---

## 📋 Startup Order (Important!)

```
1. MongoDB (must be running first)
   ↓
2. Express.js Backend (port 5000)
   ↓
3. Flask Backend (port 5001) [optional for MongoDB integration]
   ↓
4. Frontend (port 5173)
```

---

## 🚀 Alternative: Skip MongoDB for Now

If you want to get running quickly without MongoDB:

1. Comment out MongoDB initialization in `Backend/app.js`
2. Use in-memory storage temporarily
3. Implement MongoDB later after verification

```javascript
// In Backend/app.js, around line 20-30
// Comment out:
// const connectDB = async () => { ... }
// connectDB();
```

---

## ✨ After Fixing Both Issues

You should see:

```
EXPRESS.JS OUTPUT:
✅ MongoDB Connected Successfully
📊 Database: sinhala_game_db
🔗 Mongoose connected
🎮 Sinhala Sign Language Game - Backend
🌐 Server: http://localhost:5000

FLASK OUTPUT:
✅ Metadata loaded successfully!
✅ Model loaded on: cpu
🎮 Sinhala Sign Language API
🌐 http://localhost:5001
📹 Videos: XX mapped

FRONTEND OUTPUT:
➜ Local: http://localhost:5173/
```

---

## 🆘 Still Not Working?

### Check MongoDB
```bash
# Is it running?
mongosh

# Create a test collection
use sinhala_game_db
db.test.insertOne({name: "test"})
db.test.find()
```

### Check Environment Variables
```bash
# PowerShell
cat Backend\.env

# Verify MONGODB_URI is accessible
```

### Check Port Conflicts
```bash
# Check if ports are in use
netstat -ano | findstr :5000
netstat -ano | findstr :5001
netstat -ano | findstr :5173
```

### Restart Everything Clean
```bash
# Kill all Node processes
taskkill /F /IM node.exe

# Kill Flask
# Ctrl+C in Flask terminal

# Kill MongoDB
# Ctrl+C in MongoDB terminal

# Then start in correct order
```

---

## 📞 Quick Reference

| Component | Port | Status Command |
|-----------|------|---|
| MongoDB | 27017 | `mongosh` |
| Express.js | 5000 | `curl http://localhost:5000/api/health` |
| Flask | 5001 | `curl http://localhost:5001/api/ai/progress-report` |
| Frontend | 5173 | Open `http://localhost:5173` in browser |

---

## 🎯 Next Steps After Getting Running

1. Test the application in browser
2. Create a test user (Register)
3. Log in
4. Try the game
5. Check MongoDB for saved data (if using MongoDB integration)
6. Then proceed with MongoDB integration setup (MONGODB_INTEGRATION.md)

---

**Questions?** Check QUICK_REFERENCE.md or MONGODB_INTEGRATION.md
