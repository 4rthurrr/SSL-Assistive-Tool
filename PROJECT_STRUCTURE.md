# Game Application - AI Tutor for Sign Language Learning

A full-stack application combining React frontend and Node.js/Python backend for interactive sign language learning with AI-powered analytics.

## 📁 Project Structure

```
Game_V2/
├── frontend/          # React + Vite frontend application
├── Backend/           # Node.js Express server + Python AI models
├── package.json       # Root package.json (concurrently setup)
└── PROJECT_STRUCTURE.md # This file
```

## 🚀 Quick Start & Installation

### Prerequisites
- **Node.js** (v14+) and npm
- **Python** (v3.8+) and pip
- **MongoDB** (local or connection string)

### Step 1: Install All Node Dependencies
From the project root (`d:\Downloads-D\Game_V2\Game_V2`), run:
```bash
npm run install:all
```
This installs dependencies for the root, frontend, and backend folders.

### Step 2: Install Python Dependencies
```bash
cd Backend
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux
pip install -r requirements_updated.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file in the `Backend/` directory:
```env
PORT=5000
MONGODB_URI=mongodb://localhost:27017/game_app
NODE_ENV=development
MODEL_DIR=D:\Downloads-D\Game_V2\Game_V2\Backend\SSL_model
VIDEO_DIR=D:\Downloads-D\Game_V2\Game_V2\Backend\public\Dataset - Original-20251215T123918Z-3-001
GEMINI_API_KEY=your_api_key_here
```

## ⚙️ Running the Application

### ⭐ RECOMMENDED: Start Everything Concurrenty
From the project root:
```bash
npm run dev:windows
# or depending on OS:
# npm run dev:all 
```

This starts all services:
- **Frontend (React):** http://localhost:5173
- **Backend (Node.js):** http://localhost:5000
- **ML Server (Python Flask):** http://localhost:5001

## 🏛️ Architecture & Data Flow

The platform uses a unified data architecture where both the Express.js and Flask backends connect to a shared MongoDB database. 

1. **User Authentication:** Handled by Node/Express on port 5000. Express assigns a unique MongoDB `userId`.
2. **Game Interactions:** The frontend sends requests to the ML Server (Flask, port 5001) using the `userId`.
3. **Data Persistence:** Both Express and Flask read/write to the same MongoDB collections (`users`, `gameProfiles`, `gameAttempts`), ensuring progress is continuously tracked and available across backend sessions.

## 📂 Key Files
```
Backend/
├── app.js                 # Express server entry point handling Auth & Profiles
├── app.py                 # Python Flask app handling ML inference & Hint System
├── controllers/           # Request handlers for Express
├── model/                 # MongoDB schemas
├── route/                 # API routes for Express
├── SSL_model/             # Sign Language Recognition model weights
└── mongodb_integration.py # Flask MongoDB manager

frontend/
├── src/
│   ├── components/        # React components
│   ├── App.jsx           # Main app component
│   └── main.jsx          # Entry point
```
npm run dev:windows