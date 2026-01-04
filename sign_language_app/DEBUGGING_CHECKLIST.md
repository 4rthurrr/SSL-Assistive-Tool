# 🔍 Debugging Checklist - Wrong Predictions

## Step 1: Verify Browser Cache Cleared
1. Press **Ctrl+Shift+Delete**
2. Clear "Cached images and files"
3. Clear "Cookies and site data"
4. Click "Clear data"

## Step 2: Hard Refresh the Page
1. Go to: `http://127.0.0.1:8000/fresh`
2. Press **Ctrl+F5** (hard refresh)
3. Or **Ctrl+Shift+R**

## Step 3: Open Browser Console
1. Press **F12**
2. Go to "Console" tab
3. Clear any old messages

## Step 4: Record a Test Sign
1. Click "Start Recording"
2. Perform a clear sign (e.g., waving hand)
3. Wait for recording to finish

## Step 5: Check Console Output

### ✅ CORRECT Output Should Look Like:
```
🎯 RAW COORDINATES CHECK - Nose (landmark 0):
   x=0.445232, y=0.361503, z=-0.524174, vis=0.999942
   ✅ CORRECT: x should be 0.4-0.5 (NOT negative, NOT >1)
   ✅ CORRECT: y should be 0.3-0.4
   ✅ CORRECT: z should be -0.4 to -1.4 (negative)
   Hip LEFT (landmark 23): x=0.577, y=0.524, z=-0.160
   Hip RIGHT (landmark 24): x=0.321, y=0.524, z=-0.107

📊 First frame captured:
   Total features: 132
   Format: 33 pose landmarks × 4 values (RAW MediaPipe coords)
   Sample (first 12...): [0.445, 0.362, -0.524, 0.999, ...]
```

### ❌ WRONG Output Would Look Like:
```
🎯 RAW COORDINATES CHECK - Nose (landmark 0):
   x=-0.123456, y=0.891234, z=0.234567, vis=0.999942
   ⚠️ X is negative or >1 → NORMALIZATION STILL ACTIVE!
   ⚠️ Z is positive → WRONG COORDINATE SYSTEM!
```

## Step 6: Check Server Terminal

The server terminal should show:
```
2026-01-04 23:56:XX - INFO - Received sequence with 50 frames
2026-01-04 23:56:XX - INFO - 🎯 First landmark (nose): x=0.445232, y=0.361503, z=-0.524174, vis=0.999942
2026-01-04 23:56:XX - INFO - Preprocessing landmark sequence...
2026-01-04 23:56:XX - INFO - Sequence array shape: (50, 132)
2026-01-04 23:56:XX - INFO - Final shape: (1, 50, 132)
2026-01-04 23:56:XX - INFO - Running prediction...
2026-01-04 23:56:XX - INFO - Prediction: Nouns/Money (76.18%)
```

### ⚠️ Warning Signs:
```
⚠️ SUSPICIOUS X value: -0.523 (expected 0.4-0.5 for nose)
⚠️ SUSPICIOUS Y value: 1.234 (expected 0.3-0.4 for nose)
⚠️ SUSPICIOUS Z value: 0.234 (expected negative)
```

## Step 7: Test Different Signs

Try these and note the results:

| Sign to Perform | Expected Confidence | What You Got |
|-----------------|---------------------|--------------|
| Wave hand (Hello) | 60-80% | ? |
| Point at yourself (Me/I) | 60-80% | ? |
| Thumbs up | 60-80% | ? |
| Peace sign | 60-80% | ? |

## Common Issues & Solutions

### Issue 1: Browser Still Using Old Code
**Symptoms**: Console shows old log format, no new debug messages  
**Solution**: 
- Close ALL browser tabs with the app
- Close browser completely
- Reopen browser
- Navigate to `http://127.0.0.1:8000/fresh`

### Issue 2: Server Not Running
**Symptoms**: "Connection refused" or no predictions  
**Solution**:
```powershell
cd "d:\shanuka git\SSL-Assistive-Tool\sign_language_app\backend"
& "D:/shanuka git/SSL-Assistive-Tool/.venv/Scripts/python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Issue 3: Wrong Model File
**Symptoms**: Shape mismatch errors  
**Solution**:
- Verify `best_sign_model_full_features.keras` is in backend folder
- Check model expects (None, 50, 132) input

### Issue 4: MediaPipe Not Detecting Body
**Symptoms**: "No pose detected" message  
**Solution**:
- Step back from camera (show full upper body)
- Ensure good lighting
- Wear contrasting clothes

## What to Share

If still getting wrong predictions, share:

1. **Console log** (copy/paste the nose coordinates)
2. **Server log** (the prediction output)
3. **What sign you performed**
4. **What prediction you got**
5. **Screenshot** (optional)

Example:
```
Console: x=0.445, y=0.362, z=-0.524
Server: Prediction: Verbs/Fight (9.85%)
Sign performed: Waving hand (Hello)
Expected: Greetings/Hello
```

## Expected Behavior After Fix

✅ **High confidence** (>60%) for clear, well-performed signs  
✅ **Nose coordinates**: x=0.4-0.5, y=0.3-0.4, z=-0.5 to -1.3  
✅ **No warnings** in server logs  
✅ **Consistent predictions** for same sign repeated

---
**If you see negative X values or positive Z values, the fix didn't apply!**
