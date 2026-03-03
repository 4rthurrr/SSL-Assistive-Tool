import requests
import json
import random

# Base API URL
URL = "http://localhost:5000/translate"
HEADERS = {"Content-Type": "application/json"}

# List of concepts from concepts.py to randomly test
TEST_WORDS = [
    "දහය", "one", "school", "dog", "mother", "father", "sister", 
    "home", "eat", "drink", "happy", "today", "tomorrow", "bus",
    "train", "love", "money", "water", "help", "thank you"
]

def test_vocabulary_coverage():
    print(f"\n🧪 Testing Vocabulary Coverage on {len(TEST_WORDS)} words...")
    success_count = 0
    
    for word in TEST_WORDS:
        payload = {"text": word, "style": "normal"}
        try:
            response = requests.post(URL, json=payload)
            data = response.json()
            
            grammar = data.get('ssl_grammar', [])
            
            if response.status_code == 200 and grammar:
                print(f"✅ '{word}' -> {grammar}")
                success_count += 1
            else:
                print(f"❌ '{word}' Failed (Status: {response.status_code})")
                
        except Exception as e:
            print(f"❌ Error testing '{word}': {e}")
            
    print(f"\n📊 Result: {success_count}/{len(TEST_WORDS)} Success Rate")

if __name__ == "__main__":
    test_vocabulary_coverage()
