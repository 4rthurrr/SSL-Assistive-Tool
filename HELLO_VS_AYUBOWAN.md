# Hello vs Ayubowan - Translation Note

## Important Distinction

In Sri Lankan Sign Language, **"Hello"** and **"Ayubowan" (ආයුබෝවන්)** are **two different signs/words**.

### Why They're Different

1. **"Hello"** - English greeting
   - Used in casual, modern contexts
   - International/English influence
   - Display: `Hello` (stays in English)

2. **"Ayubowan" (ආයුබෝවන්)** - Traditional Sinhala greeting
   - Traditional Sri Lankan greeting
   - Means "May you live long"
   - Display: `ආයුබෝවන්` (in Sinhala)

### Display Examples

#### When user signs "Hello":
```
Hello          ← English word (not translated)
Hello          ← Same in both languages
Greetings/Hello
Confidence: 95.2% ✅
```

#### When user signs "Ayubowan" (if this sign exists):
```
ආයුබෝවන්      ← Traditional Sinhala greeting
Ayubowan       ← Romanized
Greetings/Ayubowan
Confidence: 95.2% ✅
```

## Implementation

### Updated Translation
```python
# In sinhala_translations.py
SINHALA_TRANSLATIONS = {
    "Greetings/Hello": "Hello",      # ← Stays as English
    "Greetings/Ayubowan": "ආයුබෝවන්",  # ← Different sign (if exists)
    # ... other translations
}
```

### Why This Matters

In bilingual Sri Lankan education:
- Students learn both **English words** (like "Hello")
- Students learn **Sinhala words** (like "ආයුබෝවන්")
- These are distinct vocabulary items, not translations of each other

### Other Words That Stay English

Some words are kept in English because they are:
1. **International terms**: "Hello", "Okay", "Sorry" (in some contexts)
2. **Borrowed words**: Already used in Sinhala with English pronunciation
3. **Technical terms**: Computer, Internet, Email (when used in English context)

### Current Implementation

After the update:
- ✅ "Hello" displays as "Hello" in both English and Sinhala fields
- ✅ "Ayubowan" (if separate sign) displays as "ආයුබෝවන්"
- ✅ Clear distinction between international and traditional greetings

## Testing

### Test Case 1: Hello Sign
```
Input: Perform "Hello" gesture
Expected Output:
  Sinhala field: Hello
  English field: Hello
  Category: Greetings/Hello
```

### Test Case 2: Ayubowan Sign (if exists in model)
```
Input: Perform "Ayubowan" gesture
Expected Output:
  Sinhala field: ආයුබෝවන්
  English field: Ayubowan
  Category: Greetings/Ayubowan
```

## Notes for Future

If the SSL400 dataset has separate signs for:
- "Hello" (modern/English)
- "Ayubowan" (traditional/Sinhala)

They should be treated as **distinct vocabulary items**, not translations.

**Status**: ✅ Updated - "Hello" now displays as "Hello" in both languages.

---

**Updated**: January 2026  
**Reason**: Maintain distinction between English and Sinhala greetings
