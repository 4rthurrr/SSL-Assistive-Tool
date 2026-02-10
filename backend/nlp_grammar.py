from sinling import SinhalaTokenizer
try:
    from concepts import get_concept_by_sinhala, get_sinhala_display, normalize_concept, get_all_synonyms
except ImportError:
    # Handle direct execution vs module import
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from concepts import get_concept_by_sinhala, get_sinhala_display, normalize_concept, get_all_synonyms

from embeddings_handler import EmbeddingsHandler

# Init Embeddings (Lazy or Global)
# Using pure python object to simulate singleton behavior in this module
_ai_embeddings = None
def get_embeddings_handler():
    global _ai_embeddings
    if _ai_embeddings is None:
        _ai_embeddings = EmbeddingsHandler()
    return _ai_embeddings

# --- PIPELINE CONFIGURATION ---
STOP_CONCEPTS = {
    # "CONCEPT_I",   # Removed: User explicit request + Video exists
    "CONCEPT_IS",    # Copula often dropped
    "CONCEPT_AM", 
    "CONCEPT_ARE",
    "CONCEPT_A", 
    "CONCEPT_THE"
}

def step1_tokenize(text):
    """
    STEP 1: SINHALA TOKENIZATION
    - Accept Sinhala Unicode text input.
    - Perform tokenization directly on Sinhala characters.
    """
    tokenizer = SinhalaTokenizer()
    # Simple pre-cleaning
    clean_text = text.replace(".", " . ").replace(",", " . ")
    tokens = clean_text.split() 
    return tokens

def step2_map_to_concepts(tokens):
    """
    STEP 2: SEMANTIC CONCEPT MAPPING
    - Map Sinhala tokens to internal language-neutral Concept IDs.
    - PRESERVE OOV tokens for Step 3 Normalization.
    """
    mapped_sequence = []
    
    for token in tokens:
        clean_token = token.strip('.,!?;:\'\"')
        if not clean_token:
            continue
            
        cid = get_concept_by_sinhala(clean_token)
        if cid:
            mapped_sequence.append(cid)
        else:
            # Pass RAW token for Word2Vec lookup in Step 3
            # We prefix it to distinguish from valid CIDs
            mapped_sequence.append(f"RAW_TOKEN:{clean_token}") 
            
    return mapped_sequence

def step3_normalize_concepts(concept_sequence):
    """
    STEP 3: CONCEPT NORMALIZATION (OOV HANDLING)
    - Strategy A: Map OOV concepts to Supported concepts (Manual Map)
    - Strategy B: Use Sinhala Word2Vec embeddings (Dynamic)
    """
    normalized_sequence = []
    embeddings = get_embeddings_handler()
    all_synonyms = get_all_synonyms()
    
    for item in concept_sequence:
        
        # Case 1: Item is a Raw Token (OOV from Step 2)
        if item.startswith("RAW_TOKEN:"):
            raw_token = item.split(":", 1)[1]
            print(f"⚠️ OOV Token detected: '{raw_token}'. Attempting AI Normalization...")
            
            # Strategy B: Word2Vec Lookup
            closest_word, score = embeddings.get_closest_word(raw_token, all_synonyms)
            
            if closest_word and score > 0.6: # Threshold
                 found_cid = get_concept_by_sinhala(closest_word)
                 if found_cid:
                     print(f"   ✅ AI Normalized: '{raw_token}' -> '{closest_word}' -> {found_cid} (Score: {score:.2f})")
                     normalized_sequence.append(found_cid)
                 else:
                     print(f"   ❌ AI found word '{closest_word}' but it has no Concept ID? (Bug check)")
            else:
                print(f"   ❌ AI Normalization Failed for '{raw_token}'")
                # Drop or keep? Strict pipeline usually implies dropping unsupported content 
                # to avoid breaking Video Manager
                pass 
                
        # Case 2: Item is a Valid Concept ID
        else:
            cid = item
            # Strategy A: Check Manual Map first
            norm_cid = normalize_concept(cid)
            
            if norm_cid != cid:
                print(f"   🔄 Manual Normalized: {cid} -> {norm_cid}")
                normalized_sequence.append(norm_cid)
            else:
                # Strategy B Check: Is this a Known Concept but Unsupported (No Video)?
                # We assume for now if it's in concepts.py but NOT in manual map, it's "Supported"
                # OR we could run embedding check if we knew it was missing.
                # Since the user specifically complained about "hardcoding", strict reliance on Manual Map is risky.
                # However, without a list of "Missing" videos, we don't know when to trigger AI.
                # For this implementation, we assume if it's a Valid CID, it's good, 
                # UNLESS the user intentionally provided OOV CIDs which Manual Map handles.
                normalized_sequence.append(norm_cid)

    return normalized_sequence

def step4_apply_ssl_grammar(concept_sequence):
    """
    STEP 4: SSL GRAMMAR REORDERING
    - Reorder Concept IDs according to SSL grammar.
    - Remove tense markers / stop concepts.
    """
    final_sequence = []
    
    # 1. Filter Stop Concepts (Subject Drop etc.)
    filtered_sequence = [cid for cid in concept_sequence if cid not in STOP_CONCEPTS]
    
    # 2. Reordering Logic (Basic SOV Validation)
    # Since Sinhala IS SOV, and SSL is SOV, we mainly need to keep the order 
    # but ensure specific constructs like Time comes first, Questions last.
    
    # Simple Pass-through for now as Sinhala input order "Mama Potha Kiyawanawa" (Subject Object Verb)
    # matches SSL "Book Read" (Object Verb) after Subject drop.
    final_sequence = filtered_sequence
    
    return final_sequence

def get_ssl_sequence(text):
    """
    ORCHESTRATOR: Executes the Strict Concept Pipeline
    """
    print(f"\n🚀 Starting Pipeline for: '{text}'")
    
    # 1. Tokenize
    tokens = step1_tokenize(text)
    print(f"   [1] Tokens: {tokens}")
    
    # 2. Map
    concepts = step2_map_to_concepts(tokens)
    print(f"   [2] Concepts: {concepts}")
    
    # 3. Normalize
    normalized_concepts = step3_normalize_concepts(concepts)
    print(f"   [3] Normalized: {normalized_concepts}")
    
    # 4. Grammar
    ssl_sequence = step4_apply_ssl_grammar(normalized_concepts)
    print(f"   [4] SSL Sequence: {ssl_sequence}")
    
    return ssl_sequence

def get_ssl_display_sequence(concept_sequence):
    """
    Converts Concept IDs -> Canonical Sinhala Words for UI Display.
    """
    display_sequence = []
    for cid in concept_sequence:
        sinhala_word = get_sinhala_display(cid)
        if sinhala_word:
            display_sequence.append(sinhala_word)
        else:
            display_sequence.append(cid)
            
    return display_sequence
