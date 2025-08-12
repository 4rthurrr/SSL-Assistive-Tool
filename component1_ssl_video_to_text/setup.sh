#!/bin/bash

# SSL Video-to-Text Translation Setup Script
# Run this script to set up the complete development environment

set -e  # Exit on any error

echo "🚀 Setting up SSL Video-to-Text Translation System"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
if ! python3 --version | grep -q "3.10\|3.11\|3.12"; then
    print_error "Python 3.10+ is required. Please install a compatible version."
    exit 1
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created."
else
    print_warning "Virtual environment already exists."
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
print_status "Creating project directories..."
mkdir -p models
mkdir -p data/ssl400/{train,val,test}
mkdir -p logs
mkdir -p temp
mkdir -p outputs
mkdir -p checkpoints
mkdir -p configs

# Generate default configuration
print_status "Generating default configuration..."
python src/config.py

# Run tests to verify installation
print_status "Running installation tests..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"
python -c "import mediapipe; print('MediaPipe imported successfully')"

# Check CUDA availability
print_status "Checking CUDA availability..."
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
if python -c "import torch; exit(0 if torch.cuda.is_available() else 1)"; then
    print_status "CUDA is available for GPU acceleration"
else
    print_warning "CUDA not available. Using CPU mode."
fi

# Create sample scripts
print_status "Creating sample usage scripts..."

# Training script example
cat > train_example.sh << 'EOF'
#!/bin/bash
# Example training script
python src/train.py \
    --experiment_name ssl_demo \
    --train_data_path data/ssl400/train \
    --val_data_path data/ssl400/val \
    --num_classes 50 \
    --batch_size 4 \
    --epochs 10 \
    --sequence_model lstm \
    --learning_rate 0.001
EOF

chmod +x train_example.sh

# API start script
cat > start_api.sh << 'EOF'
#!/bin/bash
# Start the SSL translation API
export SSL_MODEL_PATH="models/ssl_translation_best.pth"
export SSL_CONFIG_PATH="configs/default_config.json"
python src/inference_api.py
EOF

chmod +x start_api.sh

# Demo script
cat > run_demo.sh << 'EOF'
#!/bin/bash
# Run demo (requires trained model)
python demo.py \
    --model_path models/ssl_translation_best.pth \
    --demo_type info
EOF

chmod +x run_demo.sh

# Create development helper scripts
cat > dev_tools.sh << 'EOF'
#!/bin/bash
# Development tools

case "$1" in
    "test")
        echo "Running tests..."
        python tests/test_ssl_translation.py
        ;;
    "format")
        echo "Formatting code..."
        black src/ tests/
        ;;
    "lint")
        echo "Linting code..."
        flake8 src/ tests/
        ;;
    "validate")
        echo "Running validation..."
        python src/validation.py --model_path models/ssl_translation_best.pth --run_latency
        ;;
    *)
        echo "Usage: $0 {test|format|lint|validate}"
        ;;
esac
EOF

chmod +x dev_tools.sh

print_status "Setup completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Prepare your SSL dataset:"
echo "   - Place training videos in data/ssl400/train/"
echo "   - Place validation videos in data/ssl400/val/"
echo "   - Create corresponding label files"
echo ""
echo "2. Train your model:"
echo "   ./train_example.sh"
echo ""
echo "3. Start the API server (after training):"
echo "   ./start_api.sh"
echo ""
echo "4. Run demos (after training):"
echo "   ./run_demo.sh"
echo ""
echo "5. Development tools:"
echo "   ./dev_tools.sh test     # Run tests"
echo "   ./dev_tools.sh format   # Format code"
echo "   ./dev_tools.sh lint     # Lint code"
echo "   ./dev_tools.sh validate # Run validation"
echo ""
echo "📁 Project Structure:"
echo "===================="
echo "component1_ssl_video_to_text/"
echo "├── src/              # Source code"
echo "├── tests/            # Test suite"
echo "├── models/           # Trained models"
echo "├── data/             # Training data"
echo "├── configs/          # Configuration files"
echo "├── logs/             # Log files"
echo "├── outputs/          # Training outputs"
echo "└── checkpoints/      # Model checkpoints"
echo ""
echo "🎯 Performance Targets:"
echo "======================"
echo "- Top-1 Accuracy: >80%"
echo "- Word Error Rate: <30%"
echo "- Latency: <100ms per frame"
echo ""
echo "📚 Documentation:"
echo "=================="
echo "- API docs: http://localhost:8000/docs (when API is running)"
echo "- README: component1_ssl_video_to_text/README.md"
echo ""
print_status "SSL Video-to-Text Translation system is ready for development!"
