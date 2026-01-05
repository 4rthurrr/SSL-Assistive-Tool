"""
Test Sinhala Translations Display
Verify that Sinhala Unicode characters are being returned correctly
"""

from sinhala_translations import get_display_names

# Test various signs to verify Sinhala display
test_signs = [
    "Family/Mother",
    "Family/Father",
    "Greetings/Hello",
    "Greetings/Thank you",
    "Numbers/One",
    "Colors/Red",
    "Animals/Dog",
    "Verbs/Eat",
]

print("=" * 70)
print("SINHALA TRANSLATION TEST")
print("=" * 70)
print()

for sign in test_signs:
    result = get_display_names(sign)
    
    print(f"Sign: {result['full_english']}")
    print(f"  English: {result['english']}")
    print(f"  Sinhala: {result['sinhala']}")
    print(f"  Sinhala Bytes: {result['sinhala'].encode('utf-8')}")
    print()

print("=" * 70)
print("VERIFICATION")
print("=" * 70)
print()

# Check specific characters
mother_sinhala = get_display_names("Family/Mother")["sinhala"]
print(f"'Mother' in Sinhala: {mother_sinhala}")
print(f"Expected: මව")
print(f"Match: {mother_sinhala == 'මව'}")
print()

thank_you_sinhala = get_display_names("Greetings/Thank you")["sinhala"]
print(f"'Thank you' in Sinhala: {thank_you_sinhala}")
print(f"Expected: ස්තුතියි")
print(f"Match: {thank_you_sinhala == 'ස්තුතියි'}")
print()

hello_sinhala = get_display_names("Greetings/Hello")["sinhala"]
print(f"'Hello' in Sinhala: {hello_sinhala}")
print(f"Is English: {hello_sinhala == 'Hello'}")
print(f"Contains Sinhala chars: {any(ord(c) > 127 for c in hello_sinhala)}")
print()

print("=" * 70)
print("✅ Test Complete!")
print("=" * 70)
