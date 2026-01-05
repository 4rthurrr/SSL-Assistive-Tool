"""
Test Gemini API integration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend directory
env_path = Path(__file__).parent / "sign_language_app" / "backend" / ".env"
load_dotenv(env_path)

# Get API key
api_key = os.getenv("GEMINI_API_KEY", "")
print(f"API Key found: {bool(api_key)}")
print(f"API Key (first 20 chars): {api_key[:20] if api_key else 'NOT FOUND'}")

# Try to import and use the new google.genai
try:
    from google import genai
    print("✅ google.genai imported successfully")
    
    # Configure client
    client = genai.Client(api_key=api_key)
    print("✅ Client created successfully")
    
    # Test with a simple prompt
    print("\nTesting image generation with prompt: 'Mother'")
    prompt = "Mother, educational illustration, child-friendly, colorful, simple cartoon style, bright colors, suitable for teaching deaf children"
    
    print(f"Prompt: {prompt}")
    print("Calling Gemini API...")
    
    # List available models
    print("\nListing available models...")
    try:
        models = client.models.list()
        print("Available models:")
        for model in models:
            print(f"  - {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"    Methods: {model.supported_generation_methods}")
    except Exception as e:
        print(f"Error listing models: {e}")
    
    # Try with gemini-pro instead
    print("\n\n=== Testing with Gemini Pro (text generation) ===")
    text = "Mother"
    text_response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=f"Generate a detailed description of an educational illustration showing '{text}'. The description should be suitable for creating a child-friendly, colorful cartoon image for teaching deaf children sign language."
    )
    print(f"Text response: {text_response.text[:200]}...")
    
    print("\n✅ Test completed - Gemini API key is working for text generation")
    print("❌ Image generation (Imagen) requires Google Cloud Vertex AI, not available with free API key")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
