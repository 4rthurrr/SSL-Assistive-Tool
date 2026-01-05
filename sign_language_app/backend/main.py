"""
Sign Language Recognition API
FastAPI backend for real-time sign language prediction from landmark sequences
"""

import logging
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
from contextlib import asynccontextmanager
import httpx
from google import genai
from dotenv import load_dotenv
import base64
import io

from model_loader import load_model, get_class_labels
from landmark_utils import preprocess_landmarks
from sinhala_translations import get_display_names

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for model and labels
model = None
class_labels = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to load model at startup
    """
    global model, class_labels
    
    logger.info("Loading sign language model...")
    try:
        model = load_model()
        class_labels = get_class_labels()
        logger.info(f"Model loaded successfully! {len(class_labels)} classes available.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise e
    
    yield  # Application runs here
    
    # Cleanup on shutdown
    logger.info("Shutting down application...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Sign Language Recognition API",
    description="Real-time sign language prediction from webcam frames",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class LandmarkFrame(BaseModel):
    """Single frame of landmark data"""
    landmarks: List[float]  # Flattened landmark coordinates


class PredictRequest(BaseModel):
    """Request model for prediction endpoint"""
    sequence: List[LandmarkFrame]  # 50 frames of landmarks


class PredictionResult(BaseModel):
    """Single prediction result"""
    sign: str
    confidence: float
    sinhala: Optional[str] = None  # Sinhala translation
    english: Optional[str] = None  # English word only


class PredictResponse(BaseModel):
    """Response model for prediction endpoint"""
    prediction: str
    confidence: float
    top_3: list[PredictionResult]
    sinhala: Optional[str] = None  # Sinhala translation of top prediction
    english: Optional[str] = None  # English word only of top prediction


class ImageGenerationRequest(BaseModel):
    """Request model for image generation"""
    text: str
    style: Optional[str] = "educational, child-friendly, simple illustration"


class ImageGenerationResponse(BaseModel):
    """Response model for image generation"""
    success: bool
    image_url: Optional[str] = None
    error: Optional[str] = None
    text: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Sign Language Recognition API is active",
        "model_loaded": model is not None
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "num_classes": len(class_labels) if class_labels else 0
    }


@app.post("/predict", response_model=PredictResponse)
async def predict_sign(request: PredictRequest):
    """
    Predict sign language from a sequence of landmark frames
    
    Args:
        request: Contains sequence of 50 landmark frames
        
    Returns:
        Prediction result with sign name, confidence, and top-3 predictions
    """
    global model, class_labels
    
    # Check if model is loaded
    if model is None:
        logger.error("Model not loaded")
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Step 1: Validate sequence length
        if len(request.sequence) != 50:
            raise ValueError(f"Expected 50 frames, got {len(request.sequence)}")
        
        logger.info(f"Received sequence with {len(request.sequence)} frames")
        
        # DEBUG: Log first frame's first landmark to verify raw coordinates
        if len(request.sequence) > 0 and len(request.sequence[0].landmarks) >= 4:
            first_frame = request.sequence[0].landmarks
            nose_x, nose_y, nose_z, nose_vis = first_frame[0], first_frame[1], first_frame[2], first_frame[3]
            logger.info(f"🎯 First landmark (nose): x={nose_x:.6f}, y={nose_y:.6f}, z={nose_z:.6f}, vis={nose_vis:.6f}")
            
            # Verify coordinate ranges
            if nose_x < 0 or nose_x > 1.5:
                logger.warning(f"⚠️ SUSPICIOUS X value: {nose_x} (expected 0.4-0.5 for nose)")
            if nose_y < 0 or nose_y > 1.5:
                logger.warning(f"⚠️ SUSPICIOUS Y value: {nose_y} (expected 0.3-0.4 for nose)")
            if nose_z > 0:
                logger.warning(f"⚠️ SUSPICIOUS Z value: {nose_z} (expected negative)")
        
        # Step 2: Convert to numpy array and preprocess
        logger.info("Preprocessing landmark sequence...")
        landmarks_array = preprocess_landmarks(request.sequence)
        
        # Step 3: Run prediction
        logger.info("Running prediction...")
        predictions = model.predict(landmarks_array, verbose=0)
        
        # Step 4: Get prediction results
        probabilities = predictions[0]
        
        # Get top prediction
        top_index = int(probabilities.argmax())
        top_confidence = float(probabilities[top_index])
        top_sign = class_labels[top_index]
        
        # Get display names (English and Sinhala) for top prediction
        top_display = get_display_names(top_sign)
        
        # Get top 3 predictions with translations
        top_3_indices = np.argsort(probabilities)[-3:][::-1]
        top_3 = []
        for idx in top_3_indices:
            sign_name = class_labels[idx]
            display = get_display_names(sign_name)
            top_3.append(
                PredictionResult(
                    sign=sign_name,
                    confidence=round(float(probabilities[idx]) * 100, 2),
                    sinhala=display["sinhala"],
                    english=display["english"]
                )
            )
        
        # Log prediction with confidence assessment
        confidence_pct = top_confidence * 100
        if confidence_pct >= 70:
            logger.info(f"✅ HIGH CONFIDENCE: {top_sign} ({confidence_pct:.2f}%) - සිංහල: {top_display['sinhala']}")
        elif confidence_pct >= 50:
            logger.info(f"⚠️ MEDIUM CONFIDENCE: {top_sign} ({confidence_pct:.2f}%) - සිංහල: {top_display['sinhala']}")
        else:
            logger.warning(f"❌ LOW CONFIDENCE: {top_sign} ({confidence_pct:.2f}%) - සිංහල: {top_display['sinhala']}")
            logger.warning(f"   Top 3: {', '.join([f'{c.english}/{c.sinhala} ({c.confidence}%)' for c in top_3])}")
        
        return PredictResponse(
            prediction=top_sign,
            confidence=round(top_confidence * 100, 2),
            top_3=top_3,
            sinhala=top_display["sinhala"],
            english=top_display["english"]
        )
        
    except ValueError as e:
        logger.error(f"Landmark processing error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid landmark data: {str(e)}")
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """
    Generate educational images using Pollinations.ai with API key
    Creates AI-generated educational illustrations for sign language learning
    
    Args:
        request: Contains text to generate image from
        
    Returns:
        Image URL from Pollinations.ai
    """
    try:
        # Extract text and clean it
        text = request.text.strip()
        
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Remove category prefix if present (e.g., "Greetings/Hello" -> "Hello")
        if "/" in text:
            text = text.split("/")[-1].strip()
        
        logger.info(f"Generating AI image for '{text}' using Pollinations.ai")
        
        import urllib.parse
        
        # Create enhanced educational prompt
        prompt = f"{text}, educational illustration, child-friendly, colorful cartoon style, simple design, bright colors, suitable for teaching deaf children, clear and easy to understand"
        
        # Get Pollinations.ai API key from environment
        api_key = os.getenv("POLLINATIONS_API_KEY", "")
        
        if not api_key:
            logger.warning("POLLINATIONS_API_KEY not found, using free endpoint")
        
        # Try authenticated API first
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Authenticated API endpoint
                api_url = "https://enter.pollinations.ai/api/generate"
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "prompt": prompt,
                    "model": "flux",
                    "width": 512,
                    "height": 512,
                    "nologo": True,
                    "enhance": True
                }
                
                logger.info(f"Calling Pollinations.ai authenticated API")
                response = await client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                
                # Extract image URL from response
                if "url" in result:
                    image_url = result["url"]
                elif "image" in result:
                    image_data = result["image"]
                    if not image_data.startswith("data:"):
                        image_url = f"data:image/png;base64,{image_data}"
                    else:
                        image_url = image_data
                else:
                    # Use URL from response or construct it
                    encoded_prompt = urllib.parse.quote(prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true&enhance=true"
                
                logger.info(f"✅ Generated AI image for '{text}' using authenticated API")
                
            except Exception as api_error:
                logger.warning(f"Authenticated API failed: {api_error}, using free URL method")
                # Fallback to free URL-based method
                encoded_prompt = urllib.parse.quote(prompt)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=400&height=400&nologo=true&enhance=true"
                logger.info(f"✅ Generated AI image for '{text}' using free URL method")
        
        return ImageGenerationResponse(
            success=True,
            image_url=image_url,
            text=text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Provide informative fallback
        import urllib.parse
        encoded_text = urllib.parse.quote(text)
        fallback_url = f"https://via.placeholder.com/400x400/667eea/ffffff?text={encoded_text}"
        
        return ImageGenerationResponse(
            success=False,
            image_url=fallback_url,
            text=text
        )


@app.get("/classes")
async def get_classes():
    """Get list of all available sign classes"""
    return {
        "classes": class_labels,
        "count": len(class_labels) if class_labels else 0
    }


# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/style.css")
async def serve_css():
    """Serve CSS file at root level for backward compatibility"""
    css_file = FRONTEND_DIR / "style.css"
    if not css_file.exists():
        raise HTTPException(status_code=404, detail="CSS file not found")
    return FileResponse(str(css_file), media_type="text/css")

@app.get("/app.js")
async def serve_js():
    """Serve JS file at root level for backward compatibility"""
    js_file = FRONTEND_DIR / "app.js"
    logger.info(f"Serving app.js from: {js_file}")
    logger.info(f"File exists: {js_file.exists()}")
    logger.info(f"File size: {js_file.stat().st_size if js_file.exists() else 'N/A'} bytes")
    if not js_file.exists():
        raise HTTPException(status_code=404, detail=f"JS file not found at {js_file}")
    return FileResponse(str(js_file), media_type="application/javascript")


@app.get("/app")
async def serve_frontend():
    """Serve the frontend HTML page"""
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(str(index_file))

@app.get("/test")
async def serve_test():
    """Serve the connection test page"""
    test_file = FRONTEND_DIR / "test.html"
    if not test_file.exists():
        raise HTTPException(status_code=404, detail="Test page not found")
    return FileResponse(str(test_file))

@app.get("/fresh")
async def serve_fresh():
    """Serve the fresh frontend without cache issues"""
    fresh_file = FRONTEND_DIR / "index_new.html"
    if not fresh_file.exists():
        raise HTTPException(status_code=404, detail="Fresh frontend not found")
    return FileResponse(str(fresh_file))

@app.get("/image-generator")
async def serve_image_generator():
    """Serve the image generator page"""
    generator_file = FRONTEND_DIR / "image_generator.html"
    if not generator_file.exists():
        raise HTTPException(status_code=404, detail="Image generator page not found")
    return FileResponse(str(generator_file))

@app.get("/test-simple")
async def serve_test_simple():
    """Serve simple test page"""
    test_file = FRONTEND_DIR / "test_simple.html"
    if not test_file.exists():
        raise HTTPException(status_code=404, detail="Test page not found")
    return FileResponse(str(test_file))

# Mount static files at /static/ (MUST be last - it's a wildcard catch-all)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
