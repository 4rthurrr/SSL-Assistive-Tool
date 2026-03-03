from sinling import SinhalaTokenizer
try:
    from concepts import get_concept_by_sinhala, get_sinhala_display, normalize_concept, get_all_synonyms
except ImportError:
    # Handle direct execution vs module import
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from concepts import get_concept_by_sinhala, get_sinhala_display, normalize_concept, get_all_synonyms

# ── Sentence-level semantic parser (new pipeline) ───────────────────────────
try:
    from sinhala_sentence_parser import parse_text_to_glosses as _parse_text_to_glosses
    _SENTENCE_PARSER_AVAILABLE = True
except ImportError:
    _SENTENCE_PARSER_AVAILABLE = False
    print("⚠️ sinhala_sentence_parser not found – falling back to flat pipeline")

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


# List of Concept IDs that function as Verbs (for SOV Reordering)
VERB_CONCEPTS = {
    "CONCEPT_GO", "CONCEPT_COME", "CONCEPT_EAT", "CONCEPT_DRINK", "CONCEPT_SLEEP", 
    "CONCEPT_RUN", "CONCEPT_WALK", "CONCEPT_JUMP", "CONCEPT_SIT", "CONCEPT_STAND", 
    "CONCEPT_DANCE", "CONCEPT_PLAY", "CONCEPT_WASH", "CONCEPT_COOK", "CONCEPT_CUT", 
    "CONCEPT_DRAW", "CONCEPT_WRITE", "CONCEPT_READ", "CONCEPT_WATCH", "CONCEPT_SEE", 
    "CONCEPT_LISTEN", "CONCEPT_TALK", "CONCEPT_TELL", "CONCEPT_GIVE", "CONCEPT_TAKE", 
    "CONCEPT_BRING", "CONCEPT_BUY", "CONCEPT_SELL", "CONCEPT_HELP", "CONCEPT_LOVE", 
    "CONCEPT_LIKE", "CONCEPT_WANT", "CONCEPT_STOP", "CONCEPT_OPEN", "CONCEPT_CLOSE",
    "CONCEPT_MAKE", "CONCEPT_USE", "CONCEPT_WORK", "CONCEPT_STUDY", "CONCEPT_TEACH"
}

NEGATION_CONCEPTS = {
    "CONCEPT_NO", "CONCEPT_NOT", "CONCEPT_DONT", "CONCEPT_CANT", "CONCEPT_NONE", 
    "CONCEPT_NOT_GOOD", "CONCEPT_NOT_LIKE", "CONCEPT_NOT_LIKE_(DISLIKE)"
}

QUESTION_CONCEPTS = {
    "CONCEPT_WHAT", "CONCEPT_WHERE", "CONCEPT_WHO", "CONCEPT_WHY", "CONCEPT_WHEN", 
    "CONCEPT_HOW_MANY", "CONCEPT_HOW_MUCH", "CONCEPT_WHICH", "CONCEPT_WHOSE", "CONCEPT_WHOM"
}

TIME_CONCEPTS = {
    "CONCEPT_TODAY", "CONCEPT_TOMORROW", "CONCEPT_YESTERDAY", "CONCEPT_NOW",
    "CONCEPT_MORNING", "CONCEPT_EVENING", "CONCEPT_NIGHT", "CONCEPT_WEEK",
    "CONCEPT_MONTH", "CONCEPT_YEAR", "CONCEPT_DAY_AFTER_TOMORROW",
    # Tense markers emitted by the semantic parser as explicit time signs
    "CONCEPT_PAST", "CONCEPT_FUTURE",
}

def step4_apply_ssl_grammar(concept_sequence):
    """
    STEP 4: SSL GRAMMAR REORDERING
    - Reorder Concept IDs according to SSL grammar (Subject-Object-Verb).
    - Remove tense markers / stop concepts.
    """
    final_sequence = []
    
    # 1. Filter Stop Concepts
    # Expand to include 'TO' which is often implicit in SSL
    EXPANDED_STOP_CONCEPTS = STOP_CONCEPTS.union({"CONCEPT_TO", "CONCEPT_OF"})
    
    clean_sequence = [cid for cid in concept_sequence if cid not in EXPANDED_STOP_CONCEPTS]
    
    # 2. Reordering Logic (Time -> SOV -> Negation -> Question)
    narrative_verbs = []
    negations = []
    questions = []
    time_markers = []
    other_concepts = []
    
    for cid in clean_sequence:
        if cid in VERB_CONCEPTS:
            narrative_verbs.append(cid)
        elif cid in NEGATION_CONCEPTS:
            negations.append(cid)
        elif cid in QUESTION_CONCEPTS:
            questions.append(cid)
        elif cid in TIME_CONCEPTS:
            time_markers.append(cid)
        else:
            other_concepts.append(cid)
            
    # Reassemble: [Time] + [Subject/Objects] + [Verbs] + [Negation] + [Question]
    final_sequence = time_markers + other_concepts + narrative_verbs + negations + questions
    
    if any([narrative_verbs, negations, questions, time_markers]):
        print(f"   🔄 Grammar Reordered: Time={time_markers} SOV={other_concepts}+{narrative_verbs} Neg={negations} Q={questions}")
    
    return final_sequence

def get_ssl_sequence_with_blocks(text: str) -> dict:
    """
    NEW sentence-aware orchestrator.
    Returns the full structured result from sinhala_sentence_parser:

        {
          "blocks": [ {clause_index, tense, gloss_sequence, display_sinhala, raw_clause}, … ],
          "flat_sequence":  [CONCEPT_*, …],   ← used by video stitcher
          "flat_display":   [sinhala_word, …], ← shown in UI
          "semantic_json":  { … }              ← for debugging / analytics
        }

    Falls back to the legacy flat pipeline when the parser is unavailable.
    """
    if _SENTENCE_PARSER_AVAILABLE:
        print(f"\n🧠 [semantic parser] Processing: '{text}'")
        result = _parse_text_to_glosses(text)
        print(f"   blocks  : {len(result['blocks'])}")
        print(f"   flat    : {result['flat_display']}")
        return result

    # ── fallback: wrap legacy output in the same shape ──────────────────────
    print(f"\n⚠️ Using legacy flat pipeline for: '{text}'")
    flat_sequence = get_ssl_sequence(text)
    flat_display  = get_ssl_display_sequence(flat_sequence)
    return {
        "blocks": [
            {
                "clause_index": 0,
                "tense": "UNKNOWN",
                "gloss_sequence": flat_sequence,
                "display_sinhala": flat_display,
                "raw_clause": text,
            }
        ],
        "flat_sequence": flat_sequence,
        "flat_display":  flat_display,
        "semantic_json":  {"original_text": text, "clauses": []},
    }


def get_ssl_sequence(text):
    """
    ORCHESTRATOR: Executes the Strict Concept Pipeline (legacy flat path).
    Kept for backward-compatibility; prefer get_ssl_sequence_with_blocks().
    """
    # If the new parser is available, delegate to it and return the flat list
    if _SENTENCE_PARSER_AVAILABLE:
        result = _parse_text_to_glosses(text)
        return result["flat_sequence"]

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
