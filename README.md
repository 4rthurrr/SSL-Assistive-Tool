# SSL-Assistive-Tool

Sinhala Sign Language assistive platform for children. The repository contains a React frontend, a Node.js API for authentication and game data, and a Python Flask service for AI-assisted translation and video mapping.

## Overview

- `frontend/` - React UI that runs in the browser.
- `Backend/app.js` - Node.js API with MongoDB, JWT auth, and game routes.
- `Backend/app.py` - Flask service for Sinhala sign language AI features.
- `Backend/start_all.py` - Optional launcher for the Flask-based helper services.

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+ with pip
- MongoDB connection string
- A `GEMINI_API_KEY` if you want AI hints enabled

## Environment Variables

Create a `Backend/.env` file with at least:

```env
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET=your_jwt_secret
GEMINI_API_KEY=your_gemini_api_key
PORT=5000
```

## Run the Project

### 1. Start the Node.js backend

This service runs on `http://localhost:5000` by default.

```bash
cd Backend
npm install
npm start
```

You should see health and API URLs in the terminal after startup.

### 2. Start the Flask AI service

This service runs on `http://localhost:5001`.

```bash
cd Backend
pip install -r requirements.txt
python app.py
```

### 3. Start the frontend

The frontend runs on `http://localhost:3000`.

```bash
cd frontend
npm install
npm start
```

## Optional helper launcher

If you want to start the Flask helper services together, run:

```bash
cd Backend
python start_all.py
```

## Troubleshooting

- If a port is already in use, stop the process that is holding it and start the service again.
- If Node or Python dependencies are missing, reinstall them inside the matching folder before retrying.
- If AI hints are unavailable, confirm that `GEMINI_API_KEY` is set in `Backend/.env`.

## Notes

- The frontend consumes APIs from the backend services, so keep the Node.js server and the Flask service running while using the app.
- The repository includes datasets, models, and media assets used by the sign language features and game modes.
