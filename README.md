<<<<<<< HEAD
# SSL-Assistive-Tool
AI-Powered Sinhala Sign Language Assistive Technology Platform for Deaf / Mute Children
=======
# Game Application - AI Tutor for Sign Language Learning

A full-stack application combining React frontend and Node.js/Python backend for interactive sign language learning with AI-powered analytics.

## 📁 Project Structure

```
Game new/
├── frontend/          # React + Vite frontend application
├── Backend/           # Node.js Express server + Python AI models
└── README.md         # This file
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v14+) and npm
- **Python** (v3.8+) and pip
- **MongoDB** (local or connection string)

### Installation & Setup

#### 1. Clone/Navigate to Project

```bash
cd "d:\Game new"
```

#### 2. Backend Setup

**Option A: Node.js Express Server**

```bash
cd Backend
npm install
```

**Option B: Python ML Server (SSL Model)**

```bash
cd Backend/SSL_model
pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
```

---

## 🔧 Running the Application

### Start Backend (Node.js)

```bash
cd Backend
npm start
```

Server runs on: **http://localhost:3000** (or configured PORT in .env)

### Start Python Flask Server (Optional - for ML Model)

```bash
cd Backend/SSL_model
python app.py
```

Flask runs on: **http://localhost:5000**

### Start Frontend (React + Vite)

```bash
cd frontend
npm run dev
```

Frontend runs on: **http://localhost:5173**

---

## 📜 Available Scripts

### Frontend Scripts

```bash
npm run dev      # Start development server (Vite)
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

### Backend Scripts

```bash
npm start        # Start with nodemon (auto-reload)
npm test         # Run tests (if configured)
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in `Backend/` directory:

```env
PORT=3000
MONGODB_URI=mongodb://localhost:27017/game_app
NODE_ENV=development
FLASK_API_URL=http://localhost:5000
```

---

## 📦 Dependencies

### Frontend
- **React 19** - UI library
- **Vite** - Build tool
- **React Router DOM** - Navigation
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Backend (Node.js)
- **Express** - Web framework
- **Mongoose** - MongoDB ODM
- **Cors** - Cross-origin requests
- **Dotenv** - Environment variables
- **Nodemon** - Development auto-reload
- **Axios** - HTTP client

### Backend (Python ML)
- **Flask** - Web framework
- **PyTorch** - Deep learning
- **NumPy** - Numerical computing
- **python-dotenv** - Environment variables

---

## 📂 Key Files & Directories

```
Backend/
├── app.js                 # Express server entry point
├── app.py                 # Python Flask app
├── controllers/           # Request handlers
├── model/                 # MongoDB schemas
├── route/                 # API routes
├── data/                  # Static data (questions.json)
├── SSL_model/             # Sign Language Recognition model
│   ├── sinhala_sign_model.pth  # PyTorch model weights
│   └── requirements.txt        # Python dependencies
└── public/                # Static files

frontend/
├── src/
│   ├── components/        # React components
│   ├── App.jsx           # Main app component
│   └── main.jsx          # Entry point
├── vite.config.js        # Vite configuration
└── package.json          # Dependencies
```

---

## 🎮 Features

- **Sign Language Recognition** - Real-time sign detection using PyTorch model
- **Interactive Games** - Multiple game modes for learning
- **AI Analytics Dashboard** - Track learning progress
- **User Authentication** - Login/Register system
- **Game Profiles** - Personalized user profiles
- **Multilingual Support** - Sinhala word puzzles and more

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change port in Backend/.env or kill existing process
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows
```

### MongoDB Connection Issues
- Ensure MongoDB is running
- Check connection string in `.env`
- Verify database exists

### Node Modules Issues
```bash
rm -rf node_modules
npm install  # or npm ci for exact versions
```

### Python Virtual Environment (Optional)
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
```

---

## 📝 License

ISC

---

## 👥 Contributors

Your team here

---

## 💡 Notes

- Frontend uses Vite for fast hot module replacement (HMR)
- Backend uses Nodemon for automatic restart on file changes
- Python ML model requires PyTorch (large download ~600MB)
- Ensure all three servers (Node, Flask, React) are running for full functionality

>>>>>>> f1a4dbf (first commit)
