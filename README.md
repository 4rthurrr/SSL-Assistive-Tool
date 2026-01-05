# SSL-Assistive-Tool 🤟

**AI-Powered Sinhala Sign Language Assistive Technology Platform for Deaf/Mute Children**

[![Research Project](https://img.shields.io/badge/Type-Research%20Project-blue.svg)](https://github.com/4rthurrr/SSL-Assistive-Tool)
[![Status](https://img.shields.io/badge/Status-Active%20Development-green.svg)](https://github.com/4rthurrr/SSL-Assistive-Tool)

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Project Architecture](#project-architecture)
- [Research Components](#research-components)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Branch Organization](#branch-organization)
- [Contributing](#contributing)
- [Research Team](#research-team)
- [License](#license)

## 🎯 Overview

SSL-Assistive-Tool is an innovative research project aimed at breaking communication barriers for deaf and mute children in Sri Lanka through AI-powered Sinhala Sign Language (SSL) technology. The platform combines cutting-edge computer vision, natural language processing, and machine learning to create a comprehensive assistive technology solution.

### Mission

To empower deaf and mute children in Sri Lanka by providing accessible, AI-driven tools that facilitate communication, learning, and social interaction through Sinhala Sign Language recognition and generation.

### Research Focus

- **Sign Language Recognition**: Real-time video-to-text translation of SSL gestures
- **Sign Language Generation**: Text-to-avatar conversion for SSL visualization
- **Educational Tools**: Interactive learning games and exercises
- **Accessibility**: Culturally appropriate Sinhala language support

## ✨ Key Features

### 1. SSL Video-to-Text Translation
- Real-time sign language gesture recognition using computer vision
- MediaPipe-based hand and pose landmark detection
- Deep learning models (LSTM/GRU) for sequence-to-sequence translation
- Support for continuous sign language recognition
- Sinhala language output with proper Unicode rendering

### 2. Text-to-SSL Avatar Generation
- Convert Sinhala text to animated sign language gestures
- AI-powered avatar generation using Gemini API
- Culturally appropriate sign translations (e.g., "Hello" → "Ayubowan")
- Visual representation of SSL for learning purposes

### 3. Interactive Learning Tools
- Educational games for SSL practice
- Progressive difficulty levels
- Real-time feedback and scoring
- Engaging interface designed for children

### 4. Advanced ML Pipeline
- Custom dataset preprocessing and augmentation
- Landmark-based feature extraction
- Model training with TensorFlow/Keras
- Performance optimization and accuracy improvements

## 🏗️ Project Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend Layer                     │
│          (React.js / Interactive UI)                 │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                   Backend Layer                      │
│          (Flask API / Business Logic)                │
└─────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴──────────────────┐
        ▼                                     ▼
┌──────────────────┐              ┌──────────────────┐
│  ML Model Layer  │              │  External APIs    │
│  (TensorFlow)    │              │  (Gemini API)     │
│  - LSTM/GRU      │              │  - Avatar Gen     │
│  - MediaPipe     │              │  - Translation    │
└──────────────────┘              └──────────────────┘
```

## 🔬 Research Components

### Component 1: SSL Video Recognition System
- **Location**: `SSL-Video-to-Text-Translation` branch
- **Technology**: MediaPipe, TensorFlow, OpenCV
- **Features**: 
  - Hand and pose landmark detection
  - Temporal sequence modeling
  - Real-time inference
  - Sinhala text output

### Component 2: SSL Avatar Generation
- **Location**: `Chathuka---Text-to-SSL-avatar` branch
- **Technology**: Gemini API, React.js, Flask
- **Features**:
  - Text-to-gesture translation
  - Animated avatar generation
  - Cultural context awareness
  - Image generation and rendering

### Component 3: Interactive Learning Platform
- **Location**: `test/ssl-game` branch
- **Technology**: React.js, Game Design
- **Features**:
  - Gamified SSL learning
  - Progress tracking
  - Interactive exercises
  - Child-friendly interface

### Component 4: Lip Reading Module (Experimental)
- **Location**: `lip-reading` branch
- **Technology**: Computer Vision, Deep Learning
- **Status**: Experimental/Research phase

## 🛠️ Technology Stack

### Frontend
- **Framework**: React.js
- **UI Components**: Custom components optimized for children
- **Languages**: JavaScript, HTML5, CSS3
- **Features**: Responsive design, real-time video processing

### Backend
- **Framework**: Flask (Python)
- **API Design**: RESTful architecture
- **Processing**: Real-time video stream handling
- **Features**: Model inference, data processing

### Machine Learning
- **Frameworks**: TensorFlow, Keras
- **Computer Vision**: MediaPipe, OpenCV
- **Models**: LSTM, GRU, CNN architectures
- **Tools**: NumPy, Pandas, scikit-learn

### AI Services
- **Gemini API**: Text generation and image creation
- **Translation Services**: Sinhala language processing

### Development Tools
- **Version Control**: Git, GitHub
- **Python**: 3.8+
- **Package Management**: pip, npm

## 📁 Repository Structure

```
SSL-Assistive-Tool/
├── main                        # Main branch (documentation)
├── dev                         # Development integration branch
│   ├── Backend/                # Flask API and ML models
│   └── frontend/               # React application
├── SSL-Video-to-Text-Translation  # Video recognition research
│   ├── model-keras/            # ML model implementations
│   ├── sign_language_app/      # Application code
│   └── documentation/          # Research docs
├── Chathuka---Text-to-SSL-avatar  # Avatar generation
│   ├── backend/                # API services
│   └── frontend/               # UI components
├── test/ssl-game               # Learning game prototype
├── dulmi_ssl                   # Feature development branch
└── lip-reading                 # Experimental lip reading
```

## 🚀 Getting Started

### Prerequisites

```bash
# Python 3.8 or higher
python --version

# Node.js 14+ and npm
node --version
npm --version

# Git
git --version
```

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/4rthurrr/SSL-Assistive-Tool.git
   cd SSL-Assistive-Tool
   ```

2. **Checkout Development Branch**
   ```bash
   git checkout dev
   ```

3. **Backend Setup**
   ```bash
   cd Backend
   pip install -r requirements.txt
   
   # Set up environment variables
   export GEMINI_API_KEY="your_api_key_here"
   
   # Run the backend server
   python app.py
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

5. **Access the Application**
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:5000`

### Quick Start for Specific Components

#### SSL Video-to-Text Translation
```bash
git checkout SSL-Video-to-Text-Translation
cd sign_language_app
pip install -r requirements.txt
python app.py
```

#### Text-to-SSL Avatar
```bash
git checkout Chathuka---Text-to-SSL-avatar
# Follow setup instructions in component README
```

## 🌿 Branch Organization

| Branch Name | Purpose | Status |
|------------|---------|--------|
| `main` | Documentation and project overview | Stable |
| `dev` | Integration and development | Active |
| `SSL-Video-to-Text-Translation` | Video recognition research | Active |
| `Chathuka---Text-to-SSL-avatar` | Avatar generation system | Active |
| `test/ssl-game` | Learning game development | Testing |
| `dulmi_ssl` | Feature experiments | Development |
| `lip-reading` | Lip reading research | Experimental |

## 🤝 Contributing

We welcome contributions from researchers, developers, and accessibility advocates! Here's how you can help:

### Development Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Areas for Contribution
- Improving ML model accuracy
- Expanding SSL gesture vocabulary
- Enhancing UI/UX for children
- Adding new languages or dialects
- Documentation and tutorials
- Testing and bug fixes

### Code Standards
- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript
- Write clear commit messages
- Include tests for new features
- Update documentation as needed

## 👥 Research Team

This project is developed by a dedicated team of researchers and developers committed to accessibility technology:

- **Shanuka Amantha** ([@4rthurrr](https://github.com/4rthurrr)) - Lead Developer, ML Research
- **Dulmi Witharana** ([@dulmiwitharana](https://github.com/dulmiwitharana)) - Full-stack Development
- **Chathuka** - Avatar Generation System
- **Erandi Withanage** ([@edwithanage](https://github.com/edwithanage)) - Research Contributor

## 📊 Research Publications

*Documentation of research papers and publications will be added as they become available.*

## 🎓 Academic Context

This project is developed as part of academic research in:
- Computer Vision and Pattern Recognition
- Natural Language Processing
- Human-Computer Interaction
- Accessibility Technology
- Machine Learning Applications

## 🔒 Privacy and Ethics

- All user data is processed with strict privacy guidelines
- No personal information is stored without consent
- The platform is designed with child safety in mind
- Adheres to ethical AI principles

## 📝 License

This project is currently in active research and development. License information will be updated upon project completion.

## 🙏 Acknowledgments

- MediaPipe team for computer vision tools
- TensorFlow/Keras community
- Google Gemini API
- Sri Lankan deaf community for insights and feedback
- Academic advisors and mentors

## 📧 Contact

For research inquiries, collaborations, or support:

- **Project Lead**: Shanuka Amantha
- **Email**: [Contact through GitHub](https://github.com/4rthurrr)
- **Repository**: [SSL-Assistive-Tool](https://github.com/4rthurrr/SSL-Assistive-Tool)

## 🔮 Future Roadmap

- [ ] Expand SSL vocabulary to 500+ signs
- [ ] Mobile application development (iOS/Android)
- [ ] Real-time video call translation
- [ ] Multi-user collaborative learning
- [ ] Integration with educational institutions
- [ ] Offline mode for low-connectivity areas
- [ ] Performance optimization for edge devices
- [ ] Community-driven gesture database

---

**Made with ❤️ for the deaf and mute community of Sri Lanka**

*Last Updated: January 2026*
