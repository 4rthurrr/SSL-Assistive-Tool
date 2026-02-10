# Backend Implementation Guide & Architecture

## 1. System Overview
The backend is a **Flask-based API** designed to act as a "Translation Bridge" between Sinhala Text and Sign Language Video generation. It uses a **Hybrid Architecture** combining Rule-Based Grammar with AI-Powered Semantic Mapping.

## 2. Core Components (The Files)

### **A. API Gateway (`app.py`)**
*   **Role:** The entry point. Handles HTTP requests from the Frontend.
*   **Key Endpoint:** `/translate` (POST)
    *   Accepts: `{ "text": "මට පොතක් ඕන", "style": "normal" }`
    *   Returns: `{ "video_url": "...", "ssl_grammar": [...] }`
*   **Workflow:**
    1.  Calls `context_engine` to pre-process text.
    2.  Calls `nlp_grammar` to convert Sinhala -> SSL Concepts.
    3.  Calls `video_manager` to find video files.
    4.  Stitches videos using `moviepy`.

### **B. The NLP Brain (`nlp_grammar.py`)**
*   **Role:** Converts natural Sinhala sentence into a Sign Language Sequence.
*   **The 4-Step Pipeline:**
    1.  **Tokenization:** Splits sentence into parts.
    2.  **Mapping:** Checks `concepts.py` for direct matches.
    3.  **Normalization (AI):** If a word is unknown (e.g., "Pothak"), it asks the **Word2Vec AI** (`embeddings_handler.py`) to find the closest match ("Potha").
    4.  **Reordering:** Logic to discard stop words ("a", "the") and move Verbs to the end (SOV Order).

### **C. The AI Layer (`embeddings_handler.py`)**
*   **Role:** Handles "Out of Vocabulary" words using Vector Math.
*   **Technology:** Gensim Word2Vec.
*   **Capabilities:**
    *   **Similarity Search:** `CosineSimilarity(Input, KnownConcept) > 0.6`
    *   **Morphology Awareness:** Trained on 6055+ synthetic examples to know that "Ballek" == "Balla".

### **D. Video Engine (`video_manager.py`)**
*   **Role:** The "Librarian".
*   **Logic:**
    *   Takes a Concept ID (e.g., `CONCEPT_HOME`).
    *   Looks up the English Label ("Home").
    *   Scans the `Dataset - Original` folder structure (Nouns/Verbs).
    *   Returns the absolute path to `001_Home.mp4`.

## 3. Data Flow Diagram
```mermaid
graph TD
    A[User Input: 'Mata Pothak Ona'] -->|POST /translate| B(Flask API)
    B -->|Clean Text| C{NLP Engine}
    C -->|Lookup| D[Dictionary Check]
    C -->|Unknown Word?| E[AI Word2Vec]
    E -->|'Pothak'='Potha'| C
    C -->|SSL Sequence: [ME, BOOK, WANT]| F[Video Manager]
    F -->|Fetch Clips| G[Dataset Folder]
    G -->|Clips| H[MoviePy Stitcher]
    H -->|Final.mp4| I[Frontend Player]
```

## 4. Key Implementation Features
*   **Dynamic Loading:** The `concepts.py` file is hot-reloaded, allowing you to add new words without restarting the server.
*   **Robust Error Handling:** If a video is missing, the system doesn't crash; it skips the word and logs a warning.
*   **Hybrid Fallbacks:** It tries exact match first, then AI, then ignores it. This ensures maximum accuracy.
