# Technical Workflow: Processing "මට තේ එකක් ඕන"

This document explains exactly how the system takes the input **"මට තේ එකක් ඕන"** and decides which videos to play (and which words to ignore or find via AI).

---

## 1. The Tokenization (Breaking it down)
**File:** `nlp_grammar.py` -> `step1_tokenize`
The system first splits the sentence into individual words (tokens):
*   Input: `"මට තේ එකක් ඕන"`
*   Tokens: `["මට", "තේ", "එකක්", "ඕන"]`

---

## 2. How to Find Words? (The "Direct Database" Path)
**File:** `concepts.py` (The Registry)
The system checks if these words exist in your **Concept Registry**.

*   **"මට" (Mata):** The system checks `CONCEPT_I`. It sees `['මම', 'මට', 'මා']`. **MATCH FOUND!** -> `CONCEPT_I`.
*   **"තේ" (The):** The system checks `CONCEPT_TEA`. It sees `['තේ']`. **MATCH FOUND!** -> `CONCEPT_TEA`.
*   **"ඕන" (Ona):** The system checks `CONCEPT_WANT`. It sees `['ඕන', 'අවශ්‍යයි']`. **MATCH FOUND!** -> `CONCEPT_WANT`.
*   **"එකක්" (Ekak):** The system ensures it is in `CONCEPT_1_ONE` synonyms. **MATCH FOUND!** -> `CONCEPT_1_ONE`.

---

## 3. How to "Ignore" Words? (Stop Words Logic)
**File:** `nlp_grammar.py` -> `step4_apply_ssl_grammar`
Sometimes we want to ignore words causing grammatical noise (like "is", "the", "a").

*   **Mechanism:** We have a list called `STOP_CONCEPTS`.
*   **Example logic:**
    ```python
    STOP_CONCEPTS = {"CONCEPT_IS", "CONCEPT_THE", "CONCEPT_A"}
    # Loop through the found concepts
    if concept_id in STOP_CONCEPTS:
        # DROP IT (Do not add to final video list)
        continue
    ```
*   In your specific sentence "මට තේ එකක් ඕන", none of these are stop words, so **all 4 are kept**.

---

## 4. How to Handle "Not in Database" Logic? (AI / Word2Vec)
**File:** `embeddings_handler.py` -> `get_closest_word`
This answers: *"What if the user types a word I didn't add to the database?"*

Let's imagine the user typed **"පැන්සලක්"** (Pensalak - A pencil) but you only have "Pencil" (`CONCEPT_PENCIL` -> `['පැන්සල']`) in your database.

1.  **Direct Check Fails:** "පැන්සලක්" is NOT in `concepts.py`.
2.  **Mark as Unknown:** Pipeline labels it `RAW_TOKEN:පැන්සලක්`.
3.  **AI Layer Activates (Step 3 Normalization):**
    *   The system takes "පැන්සලක්" and converts it to a **Vector** (a list of numbers representing its meaning).
    *   It compares this vector against all known concept vectors (like Pencil, Pen, Book).
    *   **Math Calculation:** It calculates the **Cosine Similarity**.
        *   Similarity("පැන්සලක්", "පැන්සල") = **0.92 (92%)** -> High Match!
        *   Similarity("පැන්සලක්", "බල්ලා") = 0.12 (12%) -> No Match.
4.  **Result:** The AI says *"This unknown word is 92% similar to 'CONCEPT_PENCIL'"*.
5.  **Mapping:** The system automatically swaps "පැන්සලක්" -> `CONCEPT_PENCIL` and plays the "Pencil" video.

---

## 5. Final Output Generation
**File:** `video_manager.py`
The final list of Concept IDs `[CONCEPT_I, CONCEPT_TEA, CONCEPT_1_ONE, CONCEPT_WANT]` is sent to the Video Manager.

1.  It resolves file paths: `videos/I.mp4`, `videos/Tea.mp4`, `videos/One.mp4`, `videos/Want.mp4`.
2.  It stitches them together.
3.  It sends the result to the Frontend.

---
### Cheat Sheet for Viva
*   **Exact Match?** -> `concepts.py` (Dictionary)
*   **Unknown Word?** -> `embeddings_handler.py` (AI/Word2Vec)
*   **Useless Word?** -> `STOP_CONCEPTS` (Grammar Filter)
