# 🛠️ Technologies We Used (The Master List)

Here is the definitive list of technologies for your "System Implementation" slide.

## 1. Frontend (The User Interface) 💻
*   **React.js:** Used for building a fast, component-based user interface.
    *   *Role:* Handles the chat input and displays the 3D avatar.
*   **React Three Fiber (R3F):** A powerful library to render 3D models in the browser.
    *   *Role:* Loads the `Avatar.glb` file and animates the bones in real-time.

## 2. Backend (The Brain) 🧠
*   **Flask (Python):** A lightweight web framework.
    *   *Role:* Connects the AI models to the React Frontend. It handles the API requests.
*   **Word2Vec (Gensim):** An NLP model for understanding words.
    *   *Role:* The "Smart Correction" layer. It maps unknown words (like "Pothak") to known roots ("Potha").

## 3. Video Engine (The Animator) 🎬
*   **MoviePy:** A programmatic video editing library.
    *   *Role:* The "Stitcher". It takes individual sign clips (`I.mp4`, `Want.mp4`) and merges them into one continuous video (`I_Want.mp4`).
*   **MediaPipe Holistic:** A Google AI framework.
    *   *Role:* The "Skeleton Extractor". We used this to capture the human movements for the dataset.

---
## 🗣️ Viva Explanation
*"We used **React.js** for a responsive frontend and **Flask** for the backend to handle our AI models efficiently.
For the core intelligence, we chose **Word2Vec** because it handles Sinhala morphology better than simple rules.
Finally, we used **MoviePy** to algorithmically stitch videos together in real-time."*
