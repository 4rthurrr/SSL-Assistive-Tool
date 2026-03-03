# Research Project Progress Report (PP1 - 50% Milestone)

**Component Title:** Concept-Based Sinhala NLP & SSL Mapping Engine
**Student ID:** IT22091352

---

## 1. Project Concept & Methodology
### Core Concept: "Semantic Concept Mapping"
Unlike traditional word-for-word translation, our system uses a **Concept-Based Approach**. We map colloquial Sinhala words to language-neutral "Concept IDs" (e.g., `CONCEPT_WANT`, `CONCEPT_WATER`). This solves the problem of Sinhala Diglossia (difference between spoken and written forms) by standardizing input into a semantic layer before generating Sign Language.

### Methodology
We follow a **Rule-Based Hybrid NLP Methodology**:
1.  **Strict Rule Adherence:** For defined vocabulary, we enforce 100% accurate mapping using a Dictionary.
2.  **Hybrid Fallback:** We plan to use Vector Embeddings (Word2Vec) only as a fallback for unknown words, preventing AI "hallucinations" in critical communication.

---

## 2. Technology Stack & Architecture
### Backend (The Brain)
*   **Language:** Python 3.9+
*   **Framework:** Flask (REST API)
*   **NLP Tools:** `sinling` (Tokenization), Custom `Rule-Based Pipeline`
*   **Data Structure:** `Concept Registry` (Dictionary-based Knowledge Graph)
*   **Video Engine:** `MoviePy` (for dynamic video concatenation)

### Frontend (The Interface)
*   **Framework:** React.js
*   **Styling:** Custom CSS (Child-Friendly, Neumorphic Design)
*   **Communication:** Axios (JSON Payload) to Backend

---

## 3. Workflow: Current Implementation (The 4-Step Pipeline)
The backbone of the system is fully implemented and functional.

1.  **Tokenization:** 
    *   Input: "මට තේ ඕන"
    *   Action: Splits text into `["මට", "තේ", "ඕන"]`.
2.  **Concept Mapping (Discovery):**
    *   Action: Looks up synonyms in `concepts.py`.
    *   Result: `[CONCEPT_I, CONCEPT_TEA, CONCEPT_WANT]`
3.  **Normalization & Optimization:**
    *   Action: Handles unknown words and maps duplicates to standard concepts.
4.  **SSL Grammar Reordering:**
    *   Action: Arranges concepts into Subject-Object-Verb (SOV) order required for Sign Language.
    *   Output: Triggers video retrieval for `[I, TEA, WANT]`.

---

## 4. Current Status: What is Implemented (50%)
We have successfully completed the **"Core Semantic Engine"**:

*   **[Completed] Rule-Based NLP Engine:** Able to translate colloquial sentences (e.g., "Mata bada gini") into accurate Sign Language sequences.
*   **[Completed] Concept Registry:** A database of 400+ Standard SSL Concepts mapped to colloquial Sinhala synonyms.
*   **[Completed] Video Generation Pipeline:** Dynamic stitching of sign language video clips in real-time.
*   **[Completed] Multi-Mode Output:**
    1.  **Normal Mode:** Standard human video playback.
    2.  **Skeleton Mode:** MediaPipe stick-figure visualization for clarity.
    3.  **AI Avatar Mode:** Experimental neural rendering integration.
*   **[Completed] Child-Friendly UI:** Gamified interface with "Pop-up" feedback (Confetti) and large interactive elements.

---

## 5. Next Steps: Remaining Implementation (50%)
The second half of the project focuses on **Expansion, Optimization, and Advanced Avatar Rendering**:

1.  **3D Avatar Development:**
    *   Replace the experimental "AI Avatar" with a fully rigged **3D Cartoon Character**.
    *   **Reason:** Better for children (friendlier) and allows strict cultural customization (Sri Lankan school uniform).
2.  **Vocabulary Expansion:**
    *   Scale the `Concept Registry` from 400 to 1000+ words to cover daily school conversations.
3.  **Smart Embedding Layer (Word2Vec):**
    *   Fully integrate the Vector Space model to handle *unknown* synonyms automatically (e.g., mapping "Pian" -> "Water" if it's a dialect word).
4.  **Mobile App Integration:**
    *   Optimize the backend to serve a lightweight mobile frontend for field usage.

---

## Summary for the Research Panel
"At the 50% mark, we have built a **stable, deterministic translation engine** that solves the core problem of mapping colloquial Sinhala to Sign Language concepts. We have moved away from unstable pure-AI approaches in favor of a **precision-first Rule-Based system**. The remaining work is focused on **scaling the vocabulary** and significantly upgrading the visual output to a **3D Interactive Avatar**."
