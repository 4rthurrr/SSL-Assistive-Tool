import requests
import json
import sys

# Base API URL
URL = "http://localhost:5000/translate"
HEADERS = {"Content-Type": "application/json"}

def test_sinhala_sentences():
    print(f"\n🇱🇰 Testing Sinhala Sentences (Phase 2 Validation)...")
    print("===================================================")

    test_cases = [
        {
            "category": "Morphology (Singular/Indefinite)",
            "input": "බල්ලෙක් බත් කනවා", # Dog(indefinite) Rice Eat
            "expected_display": "බල්ලා බත් කනවා" # Should map to concept Balla
        },
        {
            "category": "Negation (Grammar)",
            "input": "මම කිරි බොන්නේ නෑ", # I Milk Drink(emph) Not
            "expected_display": "මම කිරි බොනවා නෑ" # Should identify NOT and reorder if needed
        },
        {
            "category": "Time & Future (Grammar)",
            "input": "හෙට මම ගෙදර යනවා", # Tomorrow I Home Go
            "expected_display": "හෙට මම ගෙදර යනවා" # Time should be at start
        },
        {
            "category": "Question (Grammar)",
            "input": "ඔයා කොහෙද යන්නේ", # You Where Going
            "expected_display": "ඔයා යනවා කොහෙද" # Question word 'Where' usually moved to end in SSL structure validation (or kept if object)
            # Actually our rule moves Questions to the VERY END.
            # So: [YOU, GO, WHERE]
        },
        {
             "category": "Vocabulary (Complex)",
             "input": "මගේ තාත්තා දොස්තර", # My Father Doctor
             "expected_display": "මගේ තාත්තා දොස්තර"
        }
    ]

    for case in test_cases:
        print(f"\n🔹 Category: {case['category']}")
        print(f"   Input: '{case['input']}'")
        
        try:
            response = requests.post(URL, json={"text": case['input'], "style": "normal"})
            if response.status_code == 200:
                data = response.json()
                grammar = data.get('ssl_grammar', [])
                display = data.get('ssl_grammar_display', [])
                
                print(f"   SSL Concepts: {grammar}")
                print(f"   SSL Display:  {display}")
                
            else:
                print(f"   ❌ Failed: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_sinhala_sentences()
