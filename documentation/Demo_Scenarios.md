# System Demo Scenarios & Input Examples

Use these specific text inputs during your presentation to demonstrate the strengths of your **Hybrid AI & Rule-Based Architecture**.

## 1. The "AI Flexibility" Test (Novelty Highlight)
**Input:** `මට පොතක් ඕන` (Mata Pothak Ona)
*   **English Meaning:** I want a book.
*   **Challenge:** The word `පොතක්` (Pothak - Indefinite) is **NOT** in the static dictionary. A standard rule-based system would fail here.
*   **What Happens:** 
    1.  Dictionary Lookup fails.
    2.  **Word2Vec AI** activates.
    3.  It calculates vector similarity: `Distance("Pothak", "Potha") < 0.2`.
    4.  It successfully maps it to `CONCEPT_BOOK`.
*   **Proof of Strength:** Shows the system handles **Morphology** without hardcoding every variation.

## 2. The "Complex Grammar" Test
**Input:** `මම හෙට ගෙදර යනවා` (Mama heta gedara yanawa)
*   **English Meaning:** I go home tomorrow.
*   **Challenge:** Long sentence with Time (`Heta`), Place (`Gedara`), and Action (`Yanawa`).
*   **What Happens:** 
    1.  **NLP Engine** tokenizes the sentence.
    2.  Maps `Mama` (I), `Heta` (Tomorrow), `Gedara` (Home), `Yanawa` (Go).
    3.  The **Video Stitcher** retrieves 4 distinct clips.
    4.  **Novelty:** It automatically smooths the transitions between clips using `MoviePy` to create a continuous sentence flow.

## 3. The "Unknown Word" Test (AI Inference)
**Input:** `බල්ලෙක් දුවනවා` (Ballek duwanawa)
*   **English Meaning:** A dog runs.
*   **Challenge:** `බල්ලෙක්` (Ballek - A dog) vs `බල්ලා` (Balla - The dog).
*   **What Happens:**
    *   The system recognizes "Ballek" is morphologically similar to "Balla".
    *   It plays the sign for `DOG` + `RUN`.
    *   This demonstrates **Generalization**: You didn't teach it "Ballek" explicitly, but it learned the pattern from the synthetic training data.

## 4. The "English Input" Test (Cross-Lingual)
**Input:** `I want water`
*   **Challenge:** User types in English.
*   **What Happens:** 
    1.  **Context Engine** detects English characters.
    2.  Translates `I` -> `Mata`, `Want` -> `Ona`, `Water` -> `Wathura`.
    3.  Signs the Sinhala sequence: `[ME] [WATER] [WANT]`.
*   **Proof:** Shows the system is **Bilingual** and accessible to non-native speakers.

---

## ⚡ Quick Copy-Paste List for Demo
| Feature to Show | Input Text (Sinhala) | Input Text (English) |
| :--- | :--- | :--- |
| **Basic Noun** | `මම පොතක් කියවනවා` | `I read a book` |
| **AI Morphology** | `මට වතුර ටිකක් ඕන` | `I want some water` |
| **Family/Emotion** | `මම අම්මාට ආදරෙයි` | `I love mother` |
| **Questions** | `ඔයාගේ නම මොකද්ද` | `What is your name` |
