# SSL-Assistive-Tool
AI-Powered Sinhala Sign Language Assistive Technology Platform for Deaf / Mute Children.

## 🚀 How to Run the System

### 1. Start the Backend (Flask API)
The backend handles the AI translation and runs on **Port 5000**.

1.  Open a **Terminal**.
2.  Navigate to the `backend` folder:
    ```bash
    cd backend
    ```
3.  Install Dependencies (if not done):
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the Server:
    ```bash
    python app.py
    ```
    *You should see: `Running on http://127.0.0.1:5000`*

### 2. Start the Frontend (React App)
The frontend provides the user interface and runs on **Port 3000**.

1.  Open a **New Terminal** (Keep the backend running!).
2.  Navigate to the `frontend` folder:
    ```bash
    cd frontend
    ```
3.  Install Dependencies (if not done):
    ```bash
    npm install
    ```
4.  Start the App:
    ```bash
    npm start
    ```
    *This will automatically open `http://localhost:3000` in your browser.*

## 🛠 Troubleshooting

*   **Port Already in Use / Address Invalid:**
    *   This means the server is already running in the background.
    *   **Fix:** Run `taskkill /F /IM python.exe` (Windows) to stop all Python processes, then try `python app.py` again.
*   **Module Not Found:**
    *   Ensure you ran `pip install ...` inside the `backend` folder.
