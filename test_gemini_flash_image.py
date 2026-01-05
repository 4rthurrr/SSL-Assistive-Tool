"""
Test Gemini Flash image generation
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

try:
    from google import genai
    print("✅ google.genai imported successfully")
    
    # Configure client
    client = genai.Client(api_key=api_key)
    print("✅ Client created successfully")
    
    # Test with gemini-2.0-flash-exp-image-generation
    print("\n=== Testing Gemini 2.0 Flash Image Generation ===")
    text = "Mother"
    prompt = f"{text}, educational illustration, child-friendly, colorful, simple cartoon style, bright colors, suitable for teaching deaf children"
    
    print(f"Prompt: {prompt}")
    print("Calling Gemini Flash Image Generation API...")
    
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp-image-generation',
        contents=prompt
    )
    
    print(f"✅ Response received!")
    print(f"Response type: {type(response)}")
    
    # Check if we have image data
    if hasattr(response, 'parts'):
        print(f"Parts: {len(response.parts)}")
        for i, part in enumerate(response.parts):
            print(f"  Part {i}: {type(part)}")
            if hasattr(part, 'inline_data'):
                print(f"    ✅ Has inline_data!")
                print(f"    MIME type: {part.inline_data.mime_type}")
                print(f"    Data size: {len(part.inline_data.data)} bytes")
            elif hasattr(part, 'text'):
                print(f"    Text: {part.text[:100]}...")
    
    print("\n✅ Gemini Flash image generation works!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
