# Deep Dive: Processing "මට තේ එකක් ඕන" (Mata The Ekak Ona)

This document explains the exact **End-to-End Workflow** for processing the Sinhala sentence "I want a tea" through your Frontend and Backend.

---

## 1. Frontend Layer (@frontend)
**File:** `src/App.js`

1.  **User Input:** user types "මට තේ එකක් ඕන".
2.  **API Call:** When "Translate" is clicked, React sends a POST request:
    ```javascript
    axios.post('http://localhost:5000/translate', { 
        text: "මට තේ එකක් ඕන" 
    })
    ```
3.  **Visualization:** It waits for the response (video URL & token list) to render the `<video>` player and the `Confetti` animation.

---

## 2. Backend Layer (@backend)
**File:** `app.py` -> `nlp_grammar.py`

The request hits `get_ssl_sequence()`. Here is the 4-Step logic applied to your sentence:

### Step 1: Tokenization
*   **Input:** "මට තේ එකක් ඕන"
*   **Action:** Splits string by spaces.
*   **Result:** `["මට", "තේ", "එකක්", "ඕන"]`

### Step 2: Concept Mapping (The "Database" Check)
*   **File:** `concepts.py` (The Dictionary)
*   **Logic:** It looks for exact matches or defined synonyms.
    *   "මට" (Mata) ➔ Found in `CONCEPT_I` synonyms ➔ **Mapped**.
    *   "තේ" (The) ➔ Found in `CONCEPT_TEA` synonyms ➔ **Mapped**.
    *   "ඕන" (Ona) ➔ Found in `CONCEPT_WANT` synonyms ➔ **Mapped**.
    *   "එකක්" (Ekak) ➔ **NOT FOUND** in simple dictionary ➔ **Marked as `RAW_TOKEN:එකක්`**.

### Step 3: Normalization (The "Similarity" Check)
*   **Files:** `nlp_grammar.py` & `embeddings_handler.py`
*   **Logic:** The system sees `RAW_TOKEN:එකක්`. It calls the **Word2Vec Strategy**:
    *   *"Hey AI, what is 'එකක්' similar to?"*
    *   AI Vector Model calculates Cosine Similarity.
    *   It finds "එකක්" is 85% similar to "එක" (Eka - One).
    *   System looks up "එක" ➔ Found `CONCEPT_ONE`.
*   **Action:** Replaces `RAW_TOKEN` with `CONCEPT_ONE`.
*   **Result:** `[CONCEPT_I, CONCEPT_TEA, CONCEPT_ONE, CONCEPT_WANT]`

### Step 4: Grammar & Stop Words (The "Ignore" Check)
*   **File:** `nlp_grammar.py` (Function `step4_apply_ssl_grammar`)
*   **Logic:** It checks the `STOP_CONCEPTS` list.
    *   Is `CONCEPT_I` a stop word? No.
    *   Is `CONCEPT_TEA` a stop word? No.
    *   Is `CONCEPT_ONE` a stop word? No.
    *   Is `CONCEPT_WANT` a stop word? No.
    *   *(Note: If the word was "IS" or "THE", it would be removed here).*
*   **Reordering:** Checks SOV structure (Subject-Object-Verb).
    *   Current: I (Sub) - Tea (Obj) - One (Adj) - Want (Verb).
    *   Sinhala/SSL Order is preserved.
*   **Final Sequence:** `[CONCEPT_I, CONCEPT_TEA, CONCEPT_ONE, CONCEPT_WANT]`

---

## 3. Video Generation Layer
**File:** `video_manager.py`

1.  **Lookup:** Takes the final IDs:
    *   `CONCEPT_I` ➔ Finds `videos/I.mp4`
    *   `CONCEPT_TEA` ➔ Finds `videos/Tea.mp4`
    *   `CONCEPT_ONE` ➔ Finds `videos/One.mp4`
    *   `CONCEPT_WANT` ➔ Finds `videos/Want.mp4`
2.  **Stitching:** Uses `MoviePy` to join these 4 clips into `output_generated.mp4`.
3.  **Response:** Sends the file URL back to React.

---
### Summary for Viva
"The system uses a **Hybrid Pipeline**. 'Mata' and 'Ona' are found directly in the database (`concepts.py`). 'Ekak', however, is technically 'Unknown', so our **Word2Vec AI** analyzes it, determines it means 'One', and maps it to `CONCEPT_ONE`. Finally, all concepts are validated against SSL Grammar rules in `nlp_grammar.py` before video generation."
