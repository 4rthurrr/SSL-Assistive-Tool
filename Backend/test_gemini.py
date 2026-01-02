#!/usr/bin/env python
"""Test which Gemini models are available with your API key"""

import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ GEMINI_API_KEY not found in environment")
    exit(1)

print(f"🔑 API Key found: {api_key[:10]}...")

try:
    # Initialize client
    client = genai.Client(api_key=api_key)
    print("✅ Client initialized")
    
    # Try different model names
    test_models = [
        'gemini-2.0-flash-exp',
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro',
        'gemini-1.5-pro-latest',
        'gemini-pro',
    ]
    
    print("\n🔍 Testing available models:\n")
    
    for model_name in test_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Say 'Hello' in one word"
            )
            
            text = response.text if hasattr(response, 'text') else str(response)
            print(f"✅ {model_name:30s} - Working! Response: {text[:50]}")
            
        except Exception as e:
            error_msg = str(e)
            if '404' in error_msg or 'not found' in error_msg.lower():
                print(f"❌ {model_name:30s} - Not available")
            else:
                print(f"⚠️  {model_name:30s} - Error: {error_msg[:60]}")
    
    print("\n" + "="*70)
    print("Use any model marked with ✅ in your Flask app")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()