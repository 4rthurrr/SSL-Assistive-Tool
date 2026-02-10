# Technology Justification & Research Novelty

This document explains **Why** specific technologies were chosen and **How** this system advances beyond existing solutions.

---

## 1. The AI Component: Concept-Based NLP Integration (Backend)

### **Technology Used:**
*   **Word2Vec (Gensim)** trained on a **Synthetic Morphological Dataset**.
*   **Hybrid Rule-Engine** (Python Dictionary + Vector Similarity).

### **Why this Technology?**
*   **Constraint:** Sinhala is a "Low-Resource Language." There are no massive datasets like English has (e.g., Common Crawl).
*   **Solution:** Instead of training a massive Transformer (like ChatGPT) which requires millions of sentences, we used **Word2Vec**. It is lightweight, fast, and we could "teach" it Sinhala grammar by generating 6,000+ synthetic variations (e.g., teaching it that *Potha* and *Pothak* are related) without needing a massive corpus.

### **🆚 Difference from Existing Systems (The Novelty)**
*   **Existing Systems:**
    *   Most use simple **English-to-SSL mappings** (Translating English structure, which is wrong for Sinhala).
    *   Others use simple **Dictionary Lookups** (If you type "Books" instead of "Book", they crash or define "Not Found").
*   **Our Novelty (Hybrid Architecture):**
    *   We implemented a **Multi-Stage Fallback System**:
        1.  **Stage 1:** Exact Dictionary Match (Fastest).
        2.  **Stage 2:** Rule-Based Suffix Stripping (Grammar logic).
        3.  **Stage 3:** **AI Vector Search** (Matches "Ballek" to "Balla" mathematically).
    *   This guarantees high accuracy even for words the system hasn't explicitly seen, solving the "Morphological Richness" problem of Sinhala.

---

## 2. The 3D Avatar Engine: Web-Based Real-Time Rigging (Frontend)

### **Technology Used:**
*   **React Three Fiber (R3F)** & **Three.js**.
*   **MediaPipe Holistic** (for skeleton extraction).

### **Why this Technology?**
*   **Accessibility:** Most Avatar systems require installing heavy software (Unity/Unreal Engine). Our system runs **entirely in the web browser**.
*   **Performance:** R3F allows us to use the GPU directly via WebGL, enabling smooth 60FPS animation without plugins.

### **🆚 Difference from Existing Systems**
*   **Existing Systems:**
    *   Often play **Pre-rendered Videos** (MP4s) of avatars. This takes huge storage and cannot change dynamically.
    *   Or require a Desktop App (Unity executable).
*   **Our Novelty:**
    *   **Dynamic Skeleton-Driving:** We do not play a video of an avatar. We take the **Joint Coordinates (x,y,z)** and apply them to a 3D Bone structure in real-time.
    *   This means we can mathematically adjust the sign (e.g., speed it up, rotate the camera) which is impossible with pre-recorded video.

---

## 3. Video Generation: Algorithmic Concatenation

### **Technology Used:**
*   **MoviePy** (Python Video Editing Library).
*   **Flask** (Micro-framework).

### **Why this Technology?**
*   **Dynamic Learning:** We needed to stitch distinct words into a flow. MoviePy allows programmatic editing (trimming, cross-fading) on the server.

### **🆚 Difference from Existing Systems**
*   **Existing Systems:** Usually display word-videos one by one in a grid.
*   **Our Novelty:** We generate a **Single, Fluid Video Sentence**. The backend algorithmically calculates the timing of each clip to create a continuous learning experience, mimicking how a human signer strings sentences together.

---

## Summary Comparison Table

| Feature | Typical Existing System | Our Implementation | Benefit |
| :--- | :--- | :--- | :--- |
| **Translation** | English-based / Direct Map | **Sinhala Concept-Based + AI** | Handles Sinhala Grammar (SOV). |
| **New Words** | Fails ("Word Not Found") | **AI Vector Similarity** | Guesses closest meaning (Robust). |
| **Avatar** | Desktop App / Pre-rendered | **WebML (React Three Fiber)** | Accessible on any browser. |
| **Data Imputation** | None | **Synthetic Morphology** | Works with small datasets. |
