# Word2Vec Implementation in Your Component

This document explains **how your system uses the Word2Vec AI Model** to handle "Unknown Words" (OOV - Out of Vocabulary). It refers to your specific coding files.

---

## 1. Where Represent Words as Vectors? (`embeddings_handler.py`)
This file is the **AI Engine** for synonyms. It acts as a "Smart Dictionary".

*   **Initialization (`__init__`)**:
    *   It loads your pre-trained model (`word2vec.model`) using the `gensim` library.
    *   If no model exists, it **automatically trains one** using your dataset (`grammar_dataset.csv`), ensuring the AI understands your specific Sinhala vocabulary.

*   **The "Brain" Function (`get_closest_word`)**:
    *   **Goal:** Find the meaning of an unknown word.
    *   **Logic:** It takes an unknown word (e.g., "bima"), converts it to a mathematical vector, and searches your known vocabulary for the closest match (e.g., "wathura" / Water).
    *   **Threshold:** It only accepts a match if the similarity score is **> 0.6** (60%), preventing bad guesses.

```python
# embeddings_handler.py (Line 80)
def get_closest_word(self, word, vocabulary_list, threshold=0.6):
    # ... checks similarity ...
    if sim > best_sim:
        best_word = vocab_word
    # ... returns best match if confidence is high ...
``` 


---

## 2. Where is it Used? (`nlp_grammar.py`)
This file is the **Pipeline Orchestrator**. It uses Word2Vec in **Step 3**.

*   **Step 2 (Mapping)**: Tries a direct dictionary lookup. If it fails, it marks the word as `RAW_TOKEN` (Unknown).
*   **Step 3 (Normalization - `step3_normalize_concepts`)**:
    *   This is where the Hybrid Logic happens.
    *   It catches those `RAW_TOKEN`s and asks the `EmbeddingHandler`: *"Do you know a synonym for this?"*
    *   If Word2Vec returns a match (e.g., "Smile"), it replaces the unknown word with `CONCEPT_SMILE`.

```python
# nlp_grammar.py (Line 80)
if item.startswith("RAW_TOKEN:"):
    # ...
    # Strategy B: Word2Vec Lookup
    closest_word, score = embeddings.get_closest_word(raw_token, all_synonyms)
    
    if closest_word and score > 0.6: 
         # Success! Mapping parameters found.
         found_cid = get_concept_by_sinhala(closest_word)
         normalized_sequence.append(found_cid)
```

---

## Summary for Presentation
"We use a **Hybrid NLP approach**. While known words use a fast Dictionary Lookup, **unknown words are passed to a Word2Vec Embedding Model**. This model calculates the semantic similarity (Cosine Similarity) between the unknown word and our known vocabulary. If a match is found with >60% confidence, the system automatically 'normalizes' it to the correct concept, allowing the system to understand Sinhala synonyms it was never explicitly taught."
