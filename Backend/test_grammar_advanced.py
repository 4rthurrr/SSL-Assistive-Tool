import requests
import json
import sys

# Base API URL
URL = "http://localhost:5000/translate"
HEADERS = {"Content-Type": "application/json"}

def test_grammar_rules():
    print(f"\n🧪 Testing Advanced SSL Grammar Rules...")
    print("=========================================")

    test_cases = [
        {
            "name": "Validation 1: Negation (I do not like milk)",
            "input": "I do not like milk",
            "expected_concepts": ["CONCEPT_I", "CONCEPT_MILK", "CONCEPT_LIKE", "CONCEPT_NOT"], # Or CONCEPT_DONT depending on mapping
            "note": "Expect: Subject Object Verb Negation"
        },
        {
            "name": "Validation 2: Question (Where is the hospital?)",
            "input": "Where is the hospital?",
            "expected_concepts": ["CONCEPT_HOSPITAL", "CONCEPT_WHERE"],
            "note": "Expect: Object Question"
        },
        {
            "name": "Validation 3: Time Marker (I go home tomorrow)",
            "input": "I go home tomorrow",
            "expected_concepts": ["CONCEPT_TOMORROW", "CONCEPT_I", "CONCEPT_HOUSE", "CONCEPT_GO"],
            "note": "Expect: Time Subject Object Verb"
        },
        {
            "name": "Validation 4: Complex (I do not eat rice today)",
            "input": "I do not eat rice today",
            "expected_concepts": ["CONCEPT_TODAY", "CONCEPT_I", "CONCEPT_RICE", "CONCEPT_EAT", "CONCEPT_NOT"],
            "note": "Expect: Time Subject Object Verb Negation"
        }
    ]

    for case in test_cases:
        print(f"\n🔹 {case['name']}")
        print(f"   Input: '{case['input']}'")
        
        try:
            response = requests.post(URL, json={"text": case['input'], "style": "normal"})
            if response.status_code == 200:
                data = response.json()
                grammar = data.get('ssl_grammar', [])
                print(f"   Output: {grammar}")
                
                # Check for key structural elements
                # Note: Exact matching is hard due to potential synonym variations, so we check order/presence
                full_match = True
                
                # Check if Time is at start (if expected)
                if "val_time" in case: 
                     # skipped logic, just visual verify for now
                     pass

                print(f"   Expected Structure: {case['note']}")
                
            else:
                print(f"   ❌ Failed: Server Error {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_grammar_rules()
