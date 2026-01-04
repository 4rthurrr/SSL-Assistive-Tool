# 🔍 Training Script Analysis - CSV Structure Found!

## **CRITICAL DISCOVERY:**

### **Your Training Script Uses:**
```python
# Line 155-156: Format Detection
if isinstance(df_first.iloc[0, 0], str) and df_first.iloc[0, 0].startswith("["):
    sample_arr = ast.literal_eval(df_first.iloc[0, 0])
    NUM_FEATURES = len(sample_arr)
```

### **What This Means:**
- **Each CSV column** contains a **STRING** like `"[0.470, 0.356, -0.524, 0.999]"`
- The script parses it with `ast.literal_eval()` to extract the array
- **NUM_FEATURES = 4** (from the first column's array length)

---

## **🚨 THE TRUTH ABOUT YOUR MODEL:**

### **Your Model Input: (50, 4)**
- **50 frames** (temporal sequence)
- **4 features** per frame

### **Your CSV Structure:**
- **33 columns** (33 landmarks)
- **Each column** = `[x, y, z, visibility]` (4 values)

### **⚠️ BUT THE SCRIPT ONLY USES THE FIRST COLUMN!**

Look at line 177-182:
```python
if isinstance(df.iloc[0, 0], str) and df.iloc[0, 0].startswith("["):
    arr_list = [ast.literal_eval(str(cell)) for cell in df.iloc[:, 0].values]
    # ☝️ df.iloc[:, 0] = ONLY COLUMN 0 (first landmark)!
    arr = np.array(arr_list, dtype='float32')
```

---

## **💡 WHAT THIS MEANS:**

### **Training Data Processing:**
1. Read CSV file
2. Extract **ONLY the first column** (`df.iloc[:, 0]`)
3. Parse each row's first column string: `"[x, y, z, visibility]"`
4. Stack 50 frames → Shape (50, 4)
5. Train model on **ONE LANDMARK only** (likely **wrist** or first hand landmark)

### **The 4 Features Are:**
```python
[x, y, z, visibility]
```
From **ONE landmark** (Column 0 in CSV = Landmark #1)

---

## **🎯 SOLUTION FOR FRONTEND:**

We need to extract **THE SAME 4 VALUES** from **ONE LANDMARK**:

### **Option 1: Wrist (Most Likely)**
```javascript
const wrist = landmarks[0];  // MediaPipe wrist
const features = [
    wrist.x,           // X coordinate
    wrist.y,           // Y coordinate
    wrist.z,           // Z depth
    wrist.visibility   // Visibility score
];
```

### **Option 2: Index Finger Tip**
```javascript
const indexTip = landmarks[8];  // MediaPipe index finger tip
const features = [
    indexTip.x,
    indexTip.y,
    indexTip.z,
    indexTip.visibility
];
```

---

## **📊 CSV Column Mapping:**

Based on MediaPipe Holistic standard:
- **Column 0**: Right Hand Wrist (Landmark 0)
- **Column 1**: Right Hand Thumb CMC (Landmark 1)
- **Column 2**: Right Hand Thumb MCP (Landmark 2)
- ...
- **Column 20**: Right Hand Pinky Tip (Landmark 20)
- **Column 21**: Left Hand Wrist (Landmark 0)
- **Column 22**: Left Hand Thumb CMC (Landmark 1)
- ...
- **Column 32**: Face/Pose landmark

**Most likely: Column 0 = Right Hand Wrist**

---

## **🔧 NEXT STEP:**

Update `index_new.html` to extract:
```javascript
// Collect 50 frames × 4 features from ONE landmark
const features = [
    landmark.x,
    landmark.y,
    landmark.z || 0,        // Z-depth (may need to calculate)
    landmark.visibility || 1.0  // Visibility
];
```

---

## **❓ REMAINING QUESTION:**

**Which landmark is in Column 0 of your CSV?**
- Is it **wrist** (most common for gesture recognition)?
- Is it **index finger tip**?
- Is it a **face landmark**?

**Check your CSV generation script** or the **skeleton videos** to confirm which landmark was tracked as Column 0.
