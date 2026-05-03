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
from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv
import base64
import io
import json
import httpx
from PIL import Image, ImageDraw, ImageFont

from model_loader import (
    get_active_labels_path,
    get_active_model_path,
    load_model,
    get_class_labels,
)
from landmark_utils import preprocess_landmarks
from sinhala_translations import get_display_names, get_sinhala_translation
from prediction_enhancer import (
    parse_classification_report,
    build_viable_mask,
    enhance_predictions,
    get_recommended_signs,
    DEFAULT_TEMPERATURE,
)

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
model_input_features = None
model_output_classes = None
viable_mask = None          # Boolean mask: True for classes with F1 > 0
f1_scores = None            # Per-class F1 scores from classification report


def _last_dim(shape):
    if isinstance(shape, list):
        shape = shape[0]
    return int(shape[-1])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to load model at startup
    """
    global model, class_labels, model_input_features, model_output_classes
    global viable_mask, f1_scores
    
    logger.info("Loading sign language model...")
    try:
        model = load_model()
        class_labels = get_class_labels()
        model_input_features = _last_dim(model.input_shape)
        model_output_classes = _last_dim(model.output_shape)
        if model_output_classes != len(class_labels):
            raise ValueError(
                f"Model/label mismatch: model outputs {model_output_classes} classes, "
                f"but labels file contains {len(class_labels)} labels"
            )



        # Load prediction enhancer (suppresses zero-F1 classes + sharpens)
        f1_scores = parse_classification_report()
        if f1_scores:
            viable_mask, suppressed = build_viable_mask(class_labels, f1_scores)
            logger.info(
                f"Prediction enhancer active: {int(viable_mask.sum())} viable classes, "
                f"{len(suppressed)} suppressed"
            )
        else:
            viable_mask = None
            logger.warning("No classification report found — enhancer disabled")

        logger.info(
            f"Model loaded successfully! {len(class_labels)} classes available. "
            f"Input features/frame: {model_input_features}"
        )
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
    sinhala: Optional[str] = None
    style: Optional[str] = "educational, child-friendly, simple illustration"


class ImageGenerationResponse(BaseModel):
    """Response model for image generation"""
    success: bool
    image_url: Optional[str] = None
    error: Optional[str] = None
    text: str
    sinhala: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Sign Language Recognition API is active",
        "model_loaded": model is not None,
        "model_input_features": model_input_features,
        "model_output_classes": model_output_classes,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "num_classes": len(class_labels) if class_labels else 0,
        "model_input_features": model_input_features,
        "model_output_classes": model_output_classes,
        "model_path": get_active_model_path(),
        "labels_path": get_active_labels_path(),
    }


def _ensure_model_ready():
    if model is None or class_labels is None:
        logger.error("Model not loaded")
        raise HTTPException(status_code=500, detail="Model not loaded")


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
        landmarks_array = preprocess_landmarks(
            request.sequence,
            expected_features=model_input_features,
        )
        
        # Step 3: Run prediction
        logger.info("Running prediction...")
        predictions = model.predict(landmarks_array, verbose=0)
        
        # Step 4: Get prediction results
        probabilities = predictions[0]

        # Enhance: suppress zero-F1 classes + temperature sharpen
        if viable_mask is not None:
            probabilities = enhance_predictions(probabilities, viable_mask)
        
        # Get top prediction
        top_index = int(probabilities.argmax())
        top_confidence = float(probabilities[top_index])
        top_sign = class_labels[top_index]
        
        # Get display names (English and Sinhala) for top prediction
        top_display = get_display_names(top_sign)
        
        # Return top 5 candidates. The response field is still named top_3 for
        # frontend compatibility, but low-confidence SSL predictions benefit
        # from showing a slightly wider candidate set.
        top_3_indices = np.argsort(probabilities)[-5:][::-1]
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


class EnsembleRequest(BaseModel):
    """Request model for multi-shot ensemble prediction (up to 5 sequences)"""
    sequences: List[List[LandmarkFrame]]  # List of sequences, each 50 frames


@app.post("/predict-ensemble", response_model=PredictResponse)
async def predict_ensemble(request: EnsembleRequest):
    """
    Average probabilities across multiple recorded sequences for a more stable prediction.
    Accepts 2-5 sequences, averages the softmax outputs, and returns the aggregated result.
    """
    global model, class_labels

    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    if not (2 <= len(request.sequences) <= 5):
        raise HTTPException(status_code=400, detail="Provide between 2 and 5 sequences")

    try:
        all_probs = []
        for seq in request.sequences:
            if len(seq) != 50:
                raise ValueError(f"Each sequence must have exactly 50 frames, got {len(seq)}")
            arr = preprocess_landmarks(seq, expected_features=model_input_features)
            preds = model.predict(arr, verbose=0)
            all_probs.append(preds[0])

        # Average probability vectors → more stable than single-shot
        avg_probs = np.mean(all_probs, axis=0)

        # Enhance: suppress zero-F1 classes + temperature sharpen
        if viable_mask is not None:
            avg_probs = enhance_predictions(avg_probs, viable_mask)

        top_index = int(avg_probs.argmax())
        top_confidence = float(avg_probs[top_index])
        top_sign = class_labels[top_index]
        top_display = get_display_names(top_sign)

        top_3_indices = np.argsort(avg_probs)[-5:][::-1]
        top_3 = []
        for idx in top_3_indices:
            sign_name = class_labels[idx]
            display = get_display_names(sign_name)
            top_3.append(
                PredictionResult(
                    sign=sign_name,
                    confidence=round(float(avg_probs[idx]) * 100, 2),
                    sinhala=display["sinhala"],
                    english=display["english"]
                )
            )

        confidence_pct = top_confidence * 100
        logger.info(f"🎯 ENSEMBLE ({len(request.sequences)} shots): {top_sign} ({confidence_pct:.2f}%)")

        return PredictResponse(
            prediction=top_sign,
            confidence=round(top_confidence * 100, 2),
            top_3=top_3,
            sinhala=top_display["sinhala"],
            english=top_display["english"]
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ensemble prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Ensemble prediction failed: {str(e)}")


# Fonts for caption overlay — resolved once at module load
_FONT_DIR = Path("C:/Windows/Fonts")
_FONT_EN  = str(_FONT_DIR / "arialbd.ttf")   # Arial Bold for English
_FONT_SI  = str(_FONT_DIR / "Nirmala.ttf")    # Nirmala UI for Sinhala


def _add_caption_banner(image_bytes: bytes, english: str, sinhala: str) -> bytes:
    """Overlay a white caption banner with English + Sinhala text onto the image."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    W, H = img.size

    # Banner height: ~16 % of image height, min 80 px
    banner_h = max(80, int(H * 0.16))
    en_size  = max(28, int(banner_h * 0.38))
    si_size  = max(24, int(banner_h * 0.34))
    padding  = max(8,  int(banner_h * 0.08))

    # Create new canvas: original + banner at bottom
    canvas = Image.new("RGBA", (W, H + banner_h), (255, 255, 255, 255))
    canvas.paste(img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    banner_y = H  # top of banner

    try:
        font_en = ImageFont.truetype(_FONT_EN, en_size)
    except OSError:
        font_en = ImageFont.load_default()
    try:
        font_si = ImageFont.truetype(_FONT_SI, si_size)
    except OSError:
        font_si = font_en

    # Draw English label
    en_bbox = draw.textbbox((0, 0), english, font=font_en)
    en_w = en_bbox[2] - en_bbox[0]
    en_x = (W - en_w) // 2
    en_y = banner_y + padding
    draw.text((en_x, en_y), english, font=font_en, fill=(30, 30, 30, 255))

    # Draw Sinhala label below English
    if sinhala:
        si_bbox = draw.textbbox((0, 0), sinhala, font=font_si)
        si_w = si_bbox[2] - si_bbox[0]
        si_x = (W - si_w) // 2
        si_y = en_y + (en_bbox[3] - en_bbox[1]) + padding
        draw.text((si_x, si_y), sinhala, font=font_si, fill=(74, 20, 140, 255))  # purple

    out = io.BytesIO()
    canvas.convert("RGB").save(out, format="PNG")
    return out.getvalue()


def _build_image_prompt(word: str, category: str) -> str:
    """Build a category-aware, scene-rich prompt so generated images are instantly meaningful."""
    cat = category.lower()
    w   = word

    if cat == "verbs":
        # Action words: show the universal everyday human gesture for this action.
        # CRITICAL: Do NOT show sign language hand shapes or finger spelling.
        # Show a real-life scene where a person is naturally performing this action.
        return (
            f"Create a photorealistic scene showing a person naturally performing the everyday action '{w}'. "
            f"IMPORTANT: Do NOT show any sign language hand gestures or finger spelling. "
            f"Show the real-world action as anyone would do it in daily life — for example: "
            f"'Come' → a smiling person facing the camera with their whole arm raised and hand "
            f"waving forward in a broad, natural beckoning gesture, as if calling a friend to walk over to them; "
            f"'Run' → a person mid-sprint on a track, leaning forward with arms pumping; "
            f"'Eat' → a person happily raising a fork of food to their smiling mouth; "
            f"'Sit' → a person just settling into a chair. "
            f"Apply the same vivid real-life storytelling to '{w}'. "
            f"Expressive face, natural body language, clean uncluttered background. No text, no watermarks."
        )

    if cat == "adjectives":
        # Quality words: use objects/scenes — avoid defaulting to a person whenever possible.
        return (
            f"Create a photorealistic image that powerfully and instantly conveys the concept '{w}' "
            f"through an object, animal, or scene — NOT just a person. "
            f"Choose the single most iconic visual shorthand — for example: "
            f"'Cold' → a snow-covered mountain peak with icicles and frost; "
            f"'Hot' → a blazing campfire with glowing orange flames; "
            f"'Beautiful' → a vibrant flower garden at golden-hour sunrise; "
            f"'Fast' → a cheetah in full sprint with motion blur; "
            f"'Heavy' → a massive boulder or a person straining to lift a loaded barbell. "
            f"Apply the same iconic object-first principle to '{w}'. "
            f"Vivid colours, sharp focus, clean simple background. No text, no watermarks."
        )

    if cat == "colors":
        return (
            f"Create a bold, photorealistic image that is entirely dominated by the color '{w}'. "
            f"Use a beautiful natural scene or iconic object where '{w}' fills most of the frame — "
            f"for example: 'Red' → a sweeping field of red poppies under a blue sky; "
            f"'Blue' → a crystal-clear tropical ocean stretching to the horizon; "
            f"'Yellow' → a sunflower field at midday. "
            f"Maximally vibrant saturation, clean simple composition. No text, no watermarks."
        )

    if cat in ("greetings", "interjection"):
        return (
            f"Create a warm, photorealistic scene that visually captures the meaning of '{w}'. "
            f"Show clear facial expressions and natural body language — NOT sign language gestures. "
            f"For example: 'Hello' → two people waving and smiling broadly as they meet; "
            f"'Thank you' → a person with hands pressed together and a grateful bow; "
            f"'Sorry' → a person with a remorseful expression, hand over heart. "
            f"Apply the same expressiveness to '{w}'. Natural lighting, friendly warm atmosphere. No text, no watermarks."
        )

    if cat == "people":
        return (
            f"Create a warm, photorealistic portrait that clearly and immediately represents a '{w}'. "
            f"Use contextual props and setting so the role is unmistakable without any labels — "
            f"for example: 'Mother' → a caring woman smiling warmly while holding a young child; "
            f"'Father' → a man laughing while playing with a child in a park; "
            f"'Doctor' → a person in a white coat holding a stethoscope in a bright clinic; "
            f"'Teacher' → a person at a chalkboard pointing to writing, students in background. "
            f"Apply the same contextual clarity to '{w}'. Warm natural lighting, approachable expression. No text, no watermarks."
        )

    if cat == "numbers":
        return (
            f"Create a photorealistic image representing the number '{w}' using objects. "
            f"Show exactly that many of a simple, recognisable everyday item arranged neatly — "
            f"for example: '3' → three bright red apples in a row; '5' → five colourful balloons. "
            f"Large, clear, vivid objects against a clean plain background. No text, no watermarks."
        )

    if cat == "days":
        return (
            f"Create a photorealistic close-up of a desk calendar or wall calendar open to the day '{w}', "
            f"with that day's name clearly visible on the page and a bold circle or ring around it. "
            f"Warm natural lighting, clean minimal desk or wall setting. "
            f"The calendar should look real and tactile. "
            f"No extra text overlays, no watermarks."
        )

    if cat == "months":
        return (
            f"Create a photorealistic close-up of a wall calendar page for the month '{w}', "
            f"showing the month name at the top with a seasonal background. "
            f"Natural lighting. No extra text overlays, no watermarks."
        )

    if cat == "places":
        return (
            f"Create a photorealistic establishing shot of a '{w}'. "
            f"Show the most iconic view of this location type. "
            f"Natural lighting, clear composition. No text, no watermarks."
        )

    if cat == "vehicles":
        return (
            f"Create a photorealistic image of a '{w}' as the clear focal point. "
            f"Vivid colours, natural lighting, uncluttered background. No text, no watermarks."
        )

    # Default
    return (
        f"Create a realistic, high-quality educational image representing the word '{w}'. "
        f"Use natural lighting, realistic textures, and vivid colours. "
        f"Simple, uncluttered composition. No text, no watermarks, no captions."
    )


async def _generate_via_aicc(prompt: str) -> bytes | None:
    """Generate image via AICC (OpenAI-compatible proxy) using gpt-image-1."""
    aicc_key = os.getenv("AICC_API_KEY", "")
    if not aicc_key:
        return None
    for mdl in ["gpt-image-1", "gpt-image-1-mini"]:
        try:
            logger.info(f"Generating image via AICC ({mdl})...")
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(
                    "https://api.ai.cc/v1/images/generations",
                    headers={"Authorization": f"Bearer {aicc_key}", "Content-Type": "application/json"},
                    json={"model": mdl, "prompt": prompt, "n": 1, "size": "1024x1024"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    item = data.get("data", [{}])[0]
                    b64_str = item.get("b64_json")
                    if b64_str:
                        logger.info(f"AICC image generated via {mdl}")
                        return base64.b64decode(b64_str)
                    url = item.get("url")
                    if url:
                        img_resp = await client.get(url, timeout=30.0)
                        if img_resp.status_code == 200:
                            logger.info(f"AICC image downloaded via {mdl}")
                            return img_resp.content
                else:
                    logger.warning(f"AICC {mdl}: HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"AICC {mdl} failed: {str(e)[:150]}")
    return None


@app.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """Generate educational images. Tries Gemini first, then AICC fallback."""
    raw_text = request.text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    sinhala_word = request.sinhala or ""
    if not sinhala_word:
        looked_up = get_sinhala_translation(raw_text)
        if looked_up != raw_text:
            sinhala_word = looked_up
    if "/" in raw_text:
        category = raw_text.split("/")[0].strip()
        text = raw_text.split("/")[-1].strip()
    else:
        category = ""
        text = raw_text
    prompt = _build_image_prompt(text, category)

    # Strategy 1: Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_exhausted = False
    if gemini_api_key:
        for mn in ["gemini-2.5-flash-image", "gemini-3-pro-image-preview", "gemini-3.1-flash-image-preview"]:
            try:
                logger.info(f"Image gen: trying {mn}")
                ai_client = genai.Client(api_key=gemini_api_key)
                response = await ai_client.aio.models.generate_content(
                    model=mn, contents=prompt,
                    config=genai_types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
                )
                for part in response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        raw_bytes = part.inline_data.data
                        if isinstance(raw_bytes, str):
                            raw_bytes = base64.b64decode(raw_bytes)
                        captioned = _add_caption_banner(raw_bytes, text.upper(), sinhala_word)
                        b64 = base64.b64encode(captioned).decode()
                        return ImageGenerationResponse(success=True, image_url=f"data:image/png;base64,{b64}", text=text, sinhala=sinhala_word or None)
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    gemini_exhausted = True
                logger.warning(f"{mn}: {str(e)[:120]}")

    # Strategy 2: AICC fallback
    logger.info("Trying AICC fallback...")
    aicc_bytes = await _generate_via_aicc(prompt)
    if aicc_bytes:
        captioned = _add_caption_banner(aicc_bytes, text.upper(), sinhala_word)
        b64 = base64.b64encode(captioned).decode()
        return ImageGenerationResponse(success=True, image_url=f"data:image/png;base64,{b64}", text=text, sinhala=sinhala_word or None)

    if gemini_exhausted:
        raise HTTPException(status_code=429, detail="Image generation quota exhausted on all providers.")
    raise HTTPException(status_code=502, detail="Image generation failed on all providers")


@app.get("/classes")
async def get_classes():
    """Get list of all available sign classes"""
    return {"classes": class_labels, "count": len(class_labels) if class_labels else 0}


@app.get("/recommended-signs")
async def recommended_signs():
    """Get signs recommended for demo - high F1 and enough test support."""
    if not f1_scores:
        return {"signs": [], "count": 0}
    recs = get_recommended_signs(f1_scores, min_f1=0.40, min_support=2)
    for r in recs:
        display = get_display_names(r["sign"])
        r["sinhala"] = display["sinhala"]
        r["english"] = display["english"]
    return {"signs": recs, "count": len(recs)}


# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent / "frontend"


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
