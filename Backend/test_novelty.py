import requests
import json
import sys

try:
    url = "http://localhost:5000/translate"
    # "The dog eats rice" (Morphological variation: Ballek -> Balla)
    payload = {
        "text": "බල්ලෙක් බත් කනවා", 
        "style": "normal"
    }
    headers = {"Content-Type": "application/json"}
    
    print(f"Sending payload: {payload}")
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    # print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"SSL Grammar: {data.get('ssl_grammar')}")
        print(f"SSL Display: {data.get('ssl_grammar_display')}")
        if 'CONCEPT_DOG' in str(data) or 'බල්ලා' in str(data):
             print("✅ VERIFIED: AI successfully mapped 'බල්ලෙක්' to 'බල්ලා' (Dog)!")
        else:
             print("⚠️ PARTIAL SUCCESS: Request worked but checking mapping...")
    elif response.status_code == 404:
        # 404 means video not found, but we care about the grammar/concept mapping in the response
        data = response.json()
        print(f"SSL Grammar (from 404): {data.get('ssl_grammar')}")
        print(f"SSL Grammar Display: {data.get('ssl_grammar_display')}")
        if 'CONCEPT_DOG' in str(data) or 'බල්ලා' in str(data):
             print("✅ VERIFIED: AI successfully mapped 'බල්ලෙක්' to 'බල්ලා' (Dog)!")
        else:
             print("❌ FAILED: Mapping incorrect.")


    print("\n--- Test 2: Grammar Structure (Novelty #2) ---")
    payload2 = {
        "text": "I go to school", 
        "style": "normal"
    }
    print(f"Sending payload: {payload2}")
    response2 = requests.post(url, json=payload2)
    
    if response2.status_code == 200:
        data = response2.json()
        print(f"SSL Grammar: {data.get('ssl_grammar')}")
        # Expect I, School, Go order
        if data.get('ssl_grammar') == ['CONCEPT_I', 'CONCEPT_SCHOOL', 'CONCEPT_GO']:
             print("✅ VERIFIED: Grammar corrected to SOV (I School Go)!")
        else:
             print(f"⚠️ PARTIAL: Grammar output {data.get('ssl_grammar')}")
    else:
        print(f"❌ FAILED: Server returned {response2.status_code}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ ERROR: {e}")
