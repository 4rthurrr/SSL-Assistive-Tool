# Training Folder Guide: `backend/training/`

This folder contains the scripts used to "Teach" the AI how to translate Sinhala to Sign Language.

## 1. `prepare_data.py` (The Chef 👨‍🍳)
*   **Purpose:** Prepares the raw ingredients (Data) for cooking (Training).
*   **Input:** `backend/data/grammar_dataset.csv` (Raw CSV).
*   **Actions:** 
    1.  Reads the CSV.
    2.  Validates that every Gloss exists in our system.
    3.  Trains the **Tokenizer** (Splitter) to understand Sinhala characters.
*   **Output:** `backend/data/training_data.json` (Clean, ready-to-use data).

## 2. `train_pipeline.py` (The Modern Engine 🚀)
*   **Purpose:** Trains the **Main Translation Model** (Transformer Architecture).
*   **Logic:**
    *   It uses the advanced `SSLTranslationModel` (Transformer).
    *   It learns complex patterns and context.
*   **Output:** 
    *   `backend/models/ssl_model.pth` (The Brain).
    *   `backend/models/target_vocab.json` (The Vocabulary).

## 3. `train_grammar.py` (The Legacy Engine 📜)
*   **Purpose:** An older, simpler training script (Seq2Seq).
*   **Status:** **Backup / Experimental**.
*   **Logic:** Uses a simpler "Sequence to Sequence" RNN model. We keep it for research comparison or as a fallback if the Transformer is too heavy.

---

## ⚡ How to Run a Retraining Cycle
If you add new sentences to `grammar_dataset.csv`:
1.  **Prepare:** `python backend/training/prepare_data.py`
2.  **Train:** `python backend/training/train_pipeline.py`
3.  **Restart:** `python app.py`
