# 🤟 SignBridge — Sinhala Sign Language Learning Platform

A full-stack Sinhala Sign Language (SSL) learning platform with four integrated research components, built for children and beginner learners in Sri Lanka.

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup Guide](#setup-guide)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
  - [4. External Data & Models](#4-external-data--models)
- [Running the Application](#running-the-application)
- [Component Details](#component-details)
- [API Keys Configuration](#api-keys-configuration)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                  React Frontend (:3000)                   │
│   Home  │  Translator  │  Lip Reading  │  Sign-to-Text   │
│         │              │               │    (iframe)      │
└────┬────┴──────┬───────┴───────┬───────┴────────┬────────┘
     │           │               │                │
     ▼           ▼               ▼                ▼
┌────────────────────────────────────┐  ┌──────────────────┐
│   Flask Backend (:5001)            │  │ FastAPI Backend   │
│   • Text-to-SSL Translator        │  │    (:8001)        │
│   • Lip Reading                    │  │ • Sign-to-Text   │
│   • Games & AI Hints               │  │ • Visual Aid Gen │
│   • MongoDB (optional)             │  │ • Prediction API │
└────────────────────────────────────┘  └──────────────────┘
```

| Component | Owner | Backend | Port |
|-----------|-------|---------|------|
| Text-to-SSL Translator | Component 2 | Flask | 5001 |
| Lip Reading Practice | Component 3 | Flask | 5001 |
| Learning Games & AI Hints | Component 4 | Flask | 5001 |
| **Sign-to-Text Recognition** | **Component 1** | **FastAPI** | **8001** |

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.11.x | [python.org](https://www.python.org/downloads/release/python-3119/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **npm** | 9+ | Comes with Node.js |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) |

> ⚠️ **Python 3.11 is required.** Python 3.12+ may have compatibility issues with some ML libraries (TensorFlow, PyTorch, gensim). Python 3.14 is NOT supported.

---

## Project Structure

```
ssl full/
├── Backend/                          # All backend code
│   ├── app.py                        # Main Flask server (Components 2,3,4)
│   ├── requirements.txt              # Python dependencies (Flask + ML)
│   ├── .env                          # API keys (Gemini)
│   ├── sinhala_lip_reading_model.h5  # Lip reading model
│   ├── practis_letters/              # Practice videos (L1-L9.mp4)
│   ├── text-to-sign/                 # Text-to-SSL translator module
│   │   ├── SSL_model/                # Translator models (.pkl, .pth)
│   │   └── models/                   # Word2Vec / NLP models
│   ├── core/                         # MongoDB integration
│   ├── auth/                         # Authentication module
│   ├── game-engine/                  # Game logic
│   ├── templates/                    # Flask HTML templates
│   ├── static/                       # Static assets
│   └── sign_to_text/                 # ★ Component 1 (FastAPI)
│       ├── main.py                   # FastAPI server
│       ├── model_loader.py           # Model loading utilities
│       ├── landmark_utils.py         # MediaPipe landmark preprocessing
│       ├── sinhala_translations.py   # English ↔ Sinhala mappings
│       ├── prediction_enhancer.py    # F1 masking + temperature scaling
│       ├── .env                      # API keys (Gemini + AICC)
│       ├── requirements.txt          # Python dependencies (FastAPI + TF)
│       ├── best_sign_model_hands.keras  # Trained Keras model (353 classes)
│       ├── class_labels_hands.txt    # Class label definitions
│       ├── classification_report_hands.txt  # F1 scores for enhancer
│       └── frontend/                 # HTML/CSS/JS frontend
│           ├── index_new.html        # Main UI
│           ├── app.js                # Application logic
│           └── style.css             # Styles
│
└── frontend/                         # React frontend (all components)
    ├── package.json
    ├── src/
    │   ├── App.jsx                   # Main router + navbar
    │   ├── features/
    │   │   ├── LipReading/           # Lip reading UI
    │   │   ├── translator/           # Text-to-SSL UI
    │   │   ├── games/                # Games UI (puzzle, sentence)
    │   │   ├── analytics/            # AI analytics dashboard
    │   │   ├── auth/                 # Login / Register
    │   │   └── SignToText/           # ★ Sign-to-text iframe wrapper
    │   └── shared/                   # Shared components & styles
    └── public/
        └── practis_letters/          # Practice videos (duplicated for frontend)
```

---

## Setup Guide

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd "ssl full"
```

### 2. Backend Setup

#### Create a Python 3.11 virtual environment:

```bash
cd Backend
python -m venv .venv
```

> On Windows, if `python` points to a different version, use the full path:
> ```bash
> "C:\Users\<YourUser>\AppData\Local\Programs\Python\Python311\python.exe" -m venv .venv
> ```

#### Activate the virtual environment:

```bash
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows (CMD)
.\.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

#### Install main backend dependencies:

```bash
pip install -r requirements.txt
```

#### Install additional packages needed by all components:

```bash
pip install regex flask flask-cors python-dotenv google-genai numpy opencv-python pydantic uvicorn httpx Pillow torch tensorflow keras fastapi
```

#### Install Sign-to-Text (Component 1) dependencies:

```bash
pip install -r sign_to_text/requirements.txt
```

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

### 4. External Data & Models

The following files are **required** but may be too large for GitHub. If they are missing after cloning, obtain them from the team's shared drive:

#### Component 1 — Sign-to-Text

| File | Location | Size | Description |
|------|----------|------|-------------|
| `best_sign_model_hands.keras` | `Backend/sign_to_text/` | ~99 MB | Trained Keras LSTM model (353 sign classes) |
| `class_labels_hands.txt` | `Backend/sign_to_text/` | ~5 KB | Class label mapping |
| `classification_report_hands.txt` | `Backend/sign_to_text/` | ~20 KB | F1 scores for prediction enhancer |

#### Component 2 — Text-to-SSL Translator

| File | Location | Size | Description |
|------|----------|------|-------------|
| `model_ssl.pkl` | `Backend/text-to-sign/SSL_model/` | ~1 MB | Translator metadata |
| `word_model.pth` | `Backend/text-to-sign/SSL_model/` | ~15 MB | Word-level model |
| `sentence_model.pth` | `Backend/text-to-sign/SSL_model/` | ~2.4 MB | Sentence-level model |
| `sinhala_sign_model.pth` | `Backend/text-to-sign/SSL_model/` | ~1 MB | Game puzzle model |
| `word2vec_ssl.model` | `Backend/text-to-sign/models/` | ~10 MB | Word2Vec embeddings |
| `Dataset - Original/` | `Backend/` | ~500 MB+ | Sign language video dataset |

#### Component 3 — Lip Reading

| File | Location | Size | Description |
|------|----------|------|-------------|
| `sinhala_lip_reading_model.h5` | `Backend/` | ~1.2 MB | Lip reading model |
| `L1.mp4` – `L9.mp4` | `Backend/practis_letters/` | ~5 MB each | Practice letter videos |
| `L1.mp4` – `L9.mp4` | `frontend/public/practis_letters/` | ~5 MB each | Same videos for frontend |
| `face_landmarker.task` | `Backend/assets/` | ~3.6 MB | MediaPipe face model |

---

## Running the Application

### Quick Start (2 terminals)

**Terminal 1 — Both backends (Flask + FastAPI):**

```bash
cd Backend
.\.venv\Scripts\python.exe app.py
```

This single command starts:
- 🚀 Flask backend on **http://localhost:5001** (Components 2, 3, 4)
- 🤟 FastAPI backend on **http://localhost:8001** (Component 1 — Sign-to-Text)

**Terminal 2 — React frontend:**

```bash
cd frontend
npm start
```

This starts the React dev server on **http://localhost:3000**

### Open in browser

Navigate to **http://localhost:3000** to see the full application.

---

## Component Details

### 🤟 Component 1: Sign-to-Text Recognition

Real-time sign language recognition using webcam + MediaPipe hand/pose landmarks + LSTM deep learning model.

- **Tech Stack:** FastAPI, TensorFlow/Keras, MediaPipe (browser-side)
- **Features:**
  - Real-time webcam sign capture (50-frame sequences)
  - 353-class sign vocabulary
  - Prediction enhancer (F1 masking + temperature sharpening)
  - Multi-shot ensemble voting
  - AI-powered visual learning guide (Gemini image generation with AICC fallback)
  - English + Sinhala bilingual output

### ✨ Component 2: Text-to-SSL Translator

Type Sinhala text and see the corresponding sign language video.

- **Tech Stack:** Flask, PyTorch, Word2Vec
- **Features:** Sinhala text input → sign video lookup and playback

### 👄 Component 3: Lip Reading Practice

Practice Sinhala lip reading with live camera and guided exercises.

- **Tech Stack:** Flask, OpenCV, TensorFlow/Keras
- **Features:** Camera-based lip detection, letter practice videos, confidence scoring

### 🎮 Component 4: Learning Games & AI Hints

Interactive games to reinforce sign language learning.

- **Tech Stack:** Flask, PyTorch, Google Gemini AI
- **Features:** Word puzzle game, sentence game, AI-generated hints, progress analytics

---

## API Keys Configuration

### `Backend/.env`

```env
GEMINI_API_KEY=your_google_gemini_api_key
```

Get your key at: [Google AI Studio](https://aistudio.google.com/app/apikey)

### `Backend/sign_to_text/.env`

```env
GEMINI_API_KEY=your_google_gemini_api_key
AICC_API_KEY=your_aicc_api_key
```

- **GEMINI_API_KEY:** Same Google Gemini key (used for image generation)
- **AICC_API_KEY:** OpenAI-compatible proxy key from [api.ai.cc](https://api.ai.cc/console/token) (fallback when Gemini quota exhausted)

> 💡 The app works without API keys — only the Visual Aid image generation feature will be disabled.

---

## Troubleshooting

### Camera warnings in terminal

```
[ WARN:0@51.083] global cap_msmf.cpp:1815 CvCapture_MSMF::grabFrame videoio(MSMF): can't grab frame
```

**This is normal.** The Lip Reading component's camera thread runs in the background. If no camera is connected or it's in use by another app, it prints these warnings but doesn't crash.

### `ModuleNotFoundError: No module named 'xyz'`

Install the missing package in the venv:

```bash
.\.venv\Scripts\python.exe -m pip install <package-name>
```

### Sign-to-Text shows "Backend Offline"

The FastAPI server on port 8001 isn't running. Check that `app.py` started it (look for `✅ Sign-to-Text backend started` in the console). If not, start it manually:

```bash
cd Backend/sign_to_text
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001
```

### `npm start` fails

Make sure you ran `npm install` first:

```bash
cd frontend
npm install
npm start
```

### MongoDB warning

```
⚠️ MongoDB integration failed: No module named 'pymongo'
```

MongoDB is optional — the app works without it. To enable it:

```bash
pip install pymongo
```

---

## Team

| Member | Component | Research Area |
|--------|-----------|---------------|
| Member 1 | 🤟 Sign-to-Text | Real-time sign recognition & visual aid generation |
| Member 2 | ✨ Translator | Text-to-SSL video translation |
| Member 3 | 👄 Lip Reading | Lip reading practice system |
| Member 4 | 🎮 Games | Interactive learning games with AI hints |

---

## License

This project is part of an academic research submission.
