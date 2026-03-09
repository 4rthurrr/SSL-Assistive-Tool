# SSL Assistive Tool — Sign Language Recognition App

Real-time Sri Lankan Sign Language (SSL) recognition system that translates hand gestures into Sinhala and English text using a deep learning model, with AI-powered educational image generation.

## How It Works

1. **User performs a sign** in front of the webcam (5-second recording or auto-predict mode)
2. **MediaPipe Holistic** (running in the browser) extracts 33 body landmarks per frame → 132 values per frame (x, y, z, visibility)
3. **50 frames** are collected and sent to the backend API as a JSON payload
4. **Backend normalizes** the landmarks (body-centered, scale-invariant) and feeds them into the Keras model
5. **Model predicts** the sign class (185 possible signs) with confidence scores
6. **Results returned** to the browser: English label, Sinhala translation, top-5 predictions, and confidence bars
7. **Image generation** (optional): User can generate an educational image for the predicted sign using Google Gemini API

## Project Structure

```
sign_language_app/
├── backend/
│   ├── main.py                  # FastAPI server — API endpoints, image generation
│   ├── model_loader.py          # Loads Keras model and class labels
│   ├── landmark_utils.py        # Landmark normalization (matches training pipeline)
│   ├── image_utils.py           # Image processing utilities
│   ├── sinhala_translations.py  # Sinhala translations for all 185 sign classes
│   ├── ssl400_labels.py         # SSL400 dataset label definitions
│   ├── best_sign_model_fixed.keras   # Active model (185 classes)
│   ├── class_labels_fixed.txt        # Class label list (one per line)
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # API keys (not committed to git)
├── frontend/
│   ├── index_new.html           # Main UI (webcam, predictions, image gen)
│   ├── app.js                   # Frontend logic (MediaPipe, recording, API calls)
│   ├── style.css                # Styles
│   └── image_generator.html     # Standalone image generation page
└── README.md                    # This file
```

## Prerequisites

- **Python 3.11** (TensorFlow does not support 3.13+)
- **Webcam** (for live sign recognition)
- **Google Gemini API Key** (free tier, for image generation feature only)

## Installation

### 1. Clone and navigate to the project

```bash
cd sign_language_app/backend
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi` + `uvicorn` — Web server
- `tensorflow` — Deep learning model inference
- `numpy` — Numerical operations
- `google-genai` — Gemini API for image generation
- `python-dotenv` — Environment variable loading
- `Pillow` — Image processing

### 3. Set up the `.env` file

Create a `.env` file in the `backend/` folder:

```env
GEMINI_API_KEY=your_api_key_here
```

Get a free API key from: https://aistudio.google.com/app/apikey

> **Note:** The Gemini API key is only needed for the image generation feature. Sign prediction works without it.

## Running the App

### Start the server

```bash
cd sign_language_app/backend
py -3.11 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Open in browser

```
http://localhost:8000/static/index_new.html
```

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/predict` | POST | Predict sign from landmark sequence |
| `/predict-single` | POST | Predict from a single frame |
| `/generate-image` | POST | Generate educational image via Gemini |
| `/health` | GET | Server health check |
| `/static/*` | GET | Serves frontend files |

## Model Details

- **Architecture:** Conv1D (3 layers) → MultiHeadAttention (8 heads) → BiLSTM (2 layers) → Dense
- **Input shape:** `(50, 132)` — 50 frames × 132 landmark values
- **Output:** 185 sign classes across categories (Adjectives, Nouns, Verbs, Greetings, etc.)
- **Accuracy:** 88.85% top-1, 94.84% top-5

## Features

- **Manual mode:** Record a 5-second sign and get prediction
- **Auto-predict mode:** Continuous prediction with temporal smoothing
- **Demo mode:** Select a sign from dropdown for testing
- **Sinhala output:** All 185 signs translated to Sinhala (සිංහල)
- **Confidence bars:** Visual display of top-5 predictions
- **AI image generation:** Educational images generated via Google Gemini
- **Anchor quality check:** Warns if body landmarks are not visible enough
- **No special hardware:** Runs on any machine with a webcam and browser