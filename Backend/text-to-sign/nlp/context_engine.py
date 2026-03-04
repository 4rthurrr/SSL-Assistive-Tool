"""
Local Context Engine - No External API Required
Handles English to Sinhala translation and text preprocessing locally.
Now supports Sinhala-to-Sinhala synonym resolving via AI Embeddings.
Uses CONCEPT_DEFINITIONS for Vocabulary.
"""

from concepts import CONCEPT_DEFINITIONS

# Build reverse map: English -> Sinhala (for English input support)
english_to_sinhala = {}
# Build direct map: Sinhala -> Canonical Sinhala (for validation)
sinhala_vocabulary = set()

for cid, data in CONCEPT_DEFINITIONS.items():
    # Store lowercase English label -> Canonical Sinhala word
    eng_label = data['label']
    canonical_sin = data['sinhala']
    
    if eng_label:
        english_to_sinhala[eng_label.lower()] = canonical_sin
        
    sinhala_vocabulary.add(canonical_sin)
    for syn in data['synonyms']:
        sinhala_vocabulary.add(syn)


# ---------------------------------------------------------
# AI-DRIVEN CONTEXT ENGINE
# Relies on english_to_sinhala (Direct Map) + AI Semantic Search.
# ---------------------------------------------------------

def is_sinhala(text):
    """Check if text contains Sinhala characters"""
    for char in text:
        if '\u0D80' <= char <= '\u0DFF':
            return True
    return False

# ---------------------------------------------------------
# AI / ML INTEGRATION: WORD EMBEDDINGS
# ---------------------------------------------------------
import os
from embeddings_handler import EmbeddingsHandler

base_dir   = os.path.dirname(os.path.abspath(__file__))     # .../text-to-sign/nlp
_ts_dir    = os.path.dirname(base_dir)                       # .../text-to-sign
_root_dir  = os.path.dirname(_ts_dir)                        # .../Backend
model_path = os.path.join(_ts_dir, "models", "word2vec.model")  # text-to-sign/models/

# ---------------------------------------------------------
# DEFINE DATA GENERATION FOR AI
# ---------------------------------------------------------
def generate_training_data():
    """
    Generates a temporary CSV containing Sinhala-English pairs from our grammar map.
    This allows the AI to learn the association between Sinhala words and their English Concepts.
    """
    training_file = os.path.join(_root_dir, "data", "bilingual_pairs.csv")
    
    # If file exists, we can skip or overwrite to ensure freshness
    # Let's overwrite to ensure it matches current code
    with open(training_file, 'w', encoding='utf-8') as f:
        
        for cid, data in CONCEPT_DEFINITIONS.items():
            eng_label = data['label']
            synonyms = data['synonyms']
            
            # 1. Base Pairs: Sinhala -> English (Label)
            for sin in synonyms:
                f.write(f"{sin},{eng_label}\n")
            
            # 2. Augmentation: Synonym Pairs (Sinhala <-> Sinhala)
            if len(synonyms) > 1:
                # Pair every synonym with every other synonym in the group
                for i in range(len(synonyms)):
                    for j in range(len(synonyms)):
                        if i != j:
                            f.write(f"{synonyms[i]},{synonyms[j]}\n")
            
    return training_file

training_data_path = generate_training_data()

# Initialize Handler
ai_embeddings = EmbeddingsHandler(
    model_path=model_path,
    data_path=training_data_path 
)

def translate_sinhala_context(text):
    """
    Processes Sinhala input. matches words to known vocabulary using AI.
    Useful if user types a synonym not strictly in our main map.
    Returns: Canonical Sinhala words that map to Concepts.
    """
    words = text.split()
    resolved_words = []
    
    # We want to map unknown Sinhala synonyms to Known Sinhala Keys
    known_sinhala_keys = list(sinhala_vocabulary)
    
    # Suffixes to strip (Naive morphological analysis)
    suffixes = ["ට", " ද", "ෙන්", "ේ", "ටත්", "ගෙන්", "ව"]
    
    for word in words:
        clean_word = word.strip('.,!?;:\'\"()[]{}')
        if not clean_word:
            continue

        # Helper to check match and return Canonical Sinhala
        def get_canonical(s_word):
            # Check against CONCEPT definitions via synonyms
            for cid, data in CONCEPT_DEFINITIONS.items():
                if s_word in data['synonyms']:
                    return data['sinhala'] # Return canonical for consistency
            return None

        # A. Try exact word
        canonical = get_canonical(clean_word)
        
        # B. Try stripping suffixes
        if not canonical:
            for suffix in suffixes:
                if clean_word.endswith(suffix):
                    stem = clean_word[:-len(suffix)]
                    canonical = get_canonical(stem)
                    if canonical:
                        print(f"✂️ Suffix Stripped: '{clean_word}' -> '{stem}'")
                        break
        
        # C. AI Semantic Search (if still not found)
        if not canonical:
            candidates_to_check = [clean_word]
            
            # Also check the stemmed version if we found one in step B but it wasn't in the exact map
            for suffix in suffixes:
                if clean_word.endswith(suffix):
                    stem = clean_word[:-len(suffix)]
                    if stem != clean_word:
                        candidates_to_check.append(stem)
                    break
            
            for check_word in candidates_to_check:
                print(f"🧪 [NOVELTY #7 CHECK] analyzing unknown word form: '{check_word}'...")
                closest_word, score = ai_embeddings.get_closest_word(check_word, known_sinhala_keys)
                
                if closest_word:
                     print(f"✅ [AI SUCCESS] Recovered Concept: '{check_word}' -> '{closest_word}' (Confidence: {score:.2f})")
                     canonical = get_canonical(closest_word)
                     if canonical:
                         break
            
        # Append result (Canonical or Original)
        resolved_words.append(canonical if canonical else clean_word)
                
    return ' '.join(resolved_words)

def translate_english_to_sinhala(text):
    """
    Translates English text to Sinhala using local dictionary + AI Semantic Search.
    Returns Sinhala sentence that can be processed by NLP grammar.
    """
    # Normalize text: lowercase
    text_lower = text.lower()
    
    # Handle multi-word phrases first (greedy matching)
    phrases = {
        "good morning": "සුබ උදෑසනක්",
        "good night": "සුබ රාත්‍රියක්",
        "good evening": "සුබ සැන්දෑවක්",
        "how are you": "කොහොමද",
        "thank you": "ස්තූතියි",
        "bus stop": "බස් නැවතුම",
        "bus stand": "බස් නැවතුම",
        "train station": "දුම්රිය ස්ථානය",
        "police station": "පොලිසිය",
        "i know": "මම දන්නවා",
        "don't know": "දන්නේ නෑ",
        "dont know": "දන්නේ නෑ",
    }
    
    for phrase, replacement in phrases.items():
        if phrase in text_lower:
            text_lower = text_lower.replace(phrase, replacement)
            
    words = text_lower.split()
    translated_words = []
    
    # Get available vocabulary for semantic search
    # These are the English words we definitively know how to translate
    known_vocabulary = list(english_to_sinhala.keys())
    
    for word in words:
        # Remove punctuation
        clean_word = word.strip('.,!?;:\'\"()[]{}')
        if not clean_word:
            continue
            
        # 1. Exact Match Check
        if clean_word in english_to_sinhala:
            translated_words.append(english_to_sinhala[clean_word])
        else:
            # 2. Stemming Fallback
            root = clean_word
            stem_found = False
            
            # Simple stemming attempts
            suffixes = ['s', 'ing', 'ed']
            for suffix in suffixes:
                if clean_word.endswith(suffix):
                    stem = clean_word[:-len(suffix)]
                    if stem in english_to_sinhala:
                        translated_words.append(english_to_sinhala[stem])
                        stem_found = True
                        break
            
            if stem_found:
                continue

            # 3. AI Semantic Search (Word Embeddings)
            # If word is unknown, ask AI: "What word in our vocabulary is closest to this?"
            print(f"🔍 AI Looking up synonym for: '{clean_word}'...")
            closest_word, score = ai_embeddings.get_closest_word(clean_word, known_vocabulary)
            
            if closest_word:
                print(f"✅ AI Match: '{clean_word}' ~ '{closest_word}' ({score:.2f})")
                translated_words.append(english_to_sinhala[closest_word])
            else:
                # Keep original if truly not found
                print(f"❌ No match found for '{clean_word}'")
                translated_words.append(clean_word)
    
    return ' '.join(translated_words)



def process_input(user_text):
    """
    LOCAL Context Engine - Comprehensive Dictionary Version
    """
    if not user_text or not user_text.strip():
        return user_text
    
    text = user_text.strip()
    
    # Check if input is already Sinhala
    if is_sinhala(text):
        print(f"DEBUG [LOCAL]: Input is Sinhala. Running Context Enhancement...")
        optimized_sinhala = translate_sinhala_context(text)
        print(f"DEBUG [LOCAL]: Sinhala '{text}' -> Optimized '{optimized_sinhala}'")
        return optimized_sinhala
    
    # Input is English - translate to Sinhala
    translated = translate_english_to_sinhala(text)
    print(f"DEBUG [LOCAL]: English '{text}' -> Sinhala '{translated}'")
    
    return translated


# For backward compatibility
def get_available_vocabulary():
    """Returns a string list of available Sinhala words from the grammar map."""
    return ", ".join(sinhala_vocabulary)

