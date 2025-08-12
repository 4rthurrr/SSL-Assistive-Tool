# SSL Video-to-Text Translation Setup Script for Windows
# Run this script to set up the complete development environment

param(
    [switch]$SkipVenv = $false,
    [switch]$Verbose = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$colors = @{
    Red = "Red"
    Green = "Green" 
    Yellow = "Yellow"
    Cyan = "Cyan"
}

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $colors.Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $colors.Red
}

function Write-Header {
    param([string]$Message)
    Write-Host $Message -ForegroundColor $colors.Cyan
    Write-Host ("=" * $Message.Length) -ForegroundColor $colors.Cyan
}

try {
    Write-Header "🚀 Setting up SSL Video-to-Text Translation System"

    # Check Python version
    Write-Status "Checking Python version..."
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Python is not installed or not in PATH. Please install Python 3.10+."
        exit 1
    }
    
    if ($pythonVersion -notmatch "3\.(10|11|12)") {
        Write-Error-Custom "Python 3.10+ is required. Current version: $pythonVersion"
        exit 1
    }
    Write-Status "Python version OK: $pythonVersion"

    # Create virtual environment
    if (-not $SkipVenv) {
        Write-Status "Creating virtual environment..."
        if (-not (Test-Path "venv")) {
            python -m venv venv
            Write-Status "Virtual environment created."
        } else {
            Write-Warning "Virtual environment already exists."
        }

        # Activate virtual environment
        Write-Status "Activating virtual environment..."
        if (Test-Path "venv\Scripts\Activate.ps1") {
            & "venv\Scripts\Activate.ps1"
        } elseif (Test-Path "venv\Scripts\activate.bat") {
            cmd /c "venv\Scripts\activate.bat"
        } else {
            Write-Error-Custom "Could not find virtual environment activation script."
            exit 1
        }
    }

    # Upgrade pip
    Write-Status "Upgrading pip..."
    python -m pip install --upgrade pip setuptools wheel

    # Install requirements
    Write-Status "Installing Python dependencies..."
    pip install -r requirements.txt

    # Create necessary directories
    Write-Status "Creating project directories..."
    $directories = @(
        "models",
        "data\ssl400\train",
        "data\ssl400\val", 
        "data\ssl400\test",
        "logs",
        "temp",
        "outputs",
        "checkpoints",
        "configs"
    )

    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            if ($Verbose) { Write-Status "Created directory: $dir" }
        }
    }

    # Generate default configuration
    Write-Status "Generating default configuration..."
    python src/config.py

    # Run tests to verify installation
    Write-Status "Running installation verification tests..."
    try {
        python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
        python -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"
        python -c "import mediapipe; print('MediaPipe imported successfully')"
    } catch {
        Write-Warning "Some dependencies may not be properly installed. Check the error messages above."
    }

    # Check CUDA availability
    Write-Status "Checking CUDA availability..."
    $cudaAvailable = python -c "import torch; print(torch.cuda.is_available())" 2>&1
    if ($cudaAvailable -match "True") {
        Write-Status "CUDA is available for GPU acceleration"
    } else {
        Write-Warning "CUDA not available. Using CPU mode."
    }

    # Create sample scripts
    Write-Status "Creating sample usage scripts..."

    # Training script example
    @"
@echo off
REM Example training script
python src/train.py ^
    --experiment_name ssl_demo ^
    --train_data_path data/ssl400/train ^
    --val_data_path data/ssl400/val ^
    --num_classes 50 ^
    --batch_size 4 ^
    --epochs 10 ^
    --sequence_model lstm ^
    --learning_rate 0.001
"@ | Out-File -FilePath "train_example.bat" -Encoding UTF8

    # API start script
    @"
@echo off
REM Start the SSL translation API
set SSL_MODEL_PATH=models/ssl_translation_best.pth
set SSL_CONFIG_PATH=configs/default_config.json
python src/inference_api.py
"@ | Out-File -FilePath "start_api.bat" -Encoding UTF8

    # Demo script
    @"
@echo off
REM Run demo (requires trained model)
python demo.py ^
    --model_path models/ssl_translation_best.pth ^
    --demo_type info
"@ | Out-File -FilePath "run_demo.bat" -Encoding UTF8

    # Development tools script
    @"
@echo off
REM Development tools

if "%1"=="test" (
    echo Running tests...
    python tests/test_ssl_translation.py
) else if "%1"=="format" (
    echo Formatting code...
    black src/ tests/
) else if "%1"=="lint" (
    echo Linting code...
    flake8 src/ tests/
) else if "%1"=="validate" (
    echo Running validation...
    python src/validation.py --model_path models/ssl_translation_best.pth --run_latency
) else (
    echo Usage: %0 {test^|format^|lint^|validate}
)
"@ | Out-File -FilePath "dev_tools.bat" -Encoding UTF8

    # PowerShell versions
    @"
# Example training script (PowerShell)
python src/train.py ``
    --experiment_name ssl_demo ``
    --train_data_path data/ssl400/train ``
    --val_data_path data/ssl400/val ``
    --num_classes 50 ``
    --batch_size 4 ``
    --epochs 10 ``
    --sequence_model lstm ``
    --learning_rate 0.001
"@ | Out-File -FilePath "train_example.ps1" -Encoding UTF8

    @"
# Start the SSL translation API (PowerShell)
`$env:SSL_MODEL_PATH = "models/ssl_translation_best.pth"
`$env:SSL_CONFIG_PATH = "configs/default_config.json"
python src/inference_api.py
"@ | Out-File -FilePath "start_api.ps1" -Encoding UTF8

    Write-Status "Setup completed successfully!"
    Write-Host ""
    
    Write-Header "📋 Next Steps"
    Write-Host "1. Prepare your SSL dataset:"
    Write-Host "   - Place training videos in data\ssl400\train\"
    Write-Host "   - Place validation videos in data\ssl400\val\"
    Write-Host "   - Create corresponding label files"
    Write-Host ""
    Write-Host "2. Train your model:"
    Write-Host "   .\train_example.bat  (or .ps1 for PowerShell)"
    Write-Host ""
    Write-Host "3. Start the API server (after training):"
    Write-Host "   .\start_api.bat  (or .ps1 for PowerShell)"
    Write-Host ""
    Write-Host "4. Run demos (after training):"
    Write-Host "   .\run_demo.bat"
    Write-Host ""
    Write-Host "5. Development tools:"
    Write-Host "   .\dev_tools.bat test      # Run tests"
    Write-Host "   .\dev_tools.bat format    # Format code"
    Write-Host "   .\dev_tools.bat lint      # Lint code"
    Write-Host "   .\dev_tools.bat validate  # Run validation"
    Write-Host ""
    
    Write-Header "📁 Project Structure"
    Write-Host "component1_ssl_video_to_text\"
    Write-Host "├── src\              # Source code"
    Write-Host "├── tests\            # Test suite"
    Write-Host "├── models\           # Trained models"
    Write-Host "├── data\             # Training data"
    Write-Host "├── configs\          # Configuration files"
    Write-Host "├── logs\             # Log files"
    Write-Host "├── outputs\          # Training outputs"
    Write-Host "└── checkpoints\      # Model checkpoints"
    Write-Host ""
    
    Write-Header "🎯 Performance Targets"
    Write-Host "- Top-1 Accuracy: >80%"
    Write-Host "- Word Error Rate: <30%"
    Write-Host "- Latency: <100ms per frame"
    Write-Host ""
    
    Write-Header "📚 Documentation"
    Write-Host "- API docs: http://localhost:8000/docs (when API is running)"
    Write-Host "- README: component1_ssl_video_to_text\README.md"
    Write-Host ""
    
    Write-Status "SSL Video-to-Text Translation system is ready for development!"

} catch {
    Write-Error-Custom "Setup failed: $($_.Exception.Message)"
    Write-Host $_.ScriptStackTrace
    exit 1
}
