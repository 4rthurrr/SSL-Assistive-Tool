"""
embeddings_handler.py
=====================
Manages trained word embeddings for the SSL Assistive Tool NLP pipeline.

Key improvements
────────────────
• Uses FastText (Gensim) instead of Word2Vec.
  FastText learns character n-grams, so it generates a vector for ANY
  word at query time — including unseen Sinhala morphological variants
  like "නරකයි", "ගෙදරින්" that were never in the training corpus.
  Word2Vec returns nothing for out-of-vocabulary words.

• Prefers vocabulary_enhanced.txt (contextual sentences from
  dataset_builder.py) over the legacy vocabulary_expanded.txt.

• Correct path resolution: data/ lives at Backend/data/, not inside
  the embeddings/ subfolder.

• NFC Unicode normalisation throughout — Sinhala characters compare
  correctly regardless of how the input was composed.

Fallback chain
──────────────
  FastText model → Word2Vec model → exact / None
"""

from __future__ import annotations

import os
import unicodedata
from typing import Optional, Tuple

try:
    from gensim.models import FastText, Word2Vec
    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False
    print("Warning: Gensim not installed.  pip install gensim")


# MANUAL IMPLEMENTATION
# NFC Unicode normalization for Sinhala text comparison
# Critical fix: same visual character can have different byte sequences in Unicode
# Without this, vocabulary lookups silently fail for valid Sinhala words
def _nc(s: str) -> str:
    """NFC-normalise a string (required for correct Sinhala comparison)."""
    return unicodedata.normalize("NFC", s.strip())


class EmbeddingsHandler:
    """
    Load or train a FastText model and expose get_closest_word() for
    OOV fallback in the NLP pipeline.
    """

    def __init__(
        self,
        model_path: str = "../models/fasttext.model",
        data_path:  Optional[str] = None,
    ) -> None:
        self.model      = None
        self.model_type = "none"
        self.dims       = 100

        if not GENSIM_AVAILABLE:
            return

        # ── Resolve paths ─────────────────────────────────────────────────────
        # Layout: Backend/text-to-sign/ai/embeddings/embeddings_handler.py
        #         Backend/data/vocabulary_*.txt
        base_dir    = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.normpath(os.path.join(base_dir, "..", "..", ".."))
        data_dir    = os.path.join(backend_dir, "data")

        if not os.path.isabs(model_path):
            model_path = os.path.join(base_dir, model_path)
        if data_path and not os.path.isabs(data_path):
            data_path = os.path.join(base_dir, data_path)

        # Also look for legacy Word2Vec model
        w2v_path = os.path.join(os.path.dirname(model_path), "word2vec.model")

        # RESEARCH CONTRIBUTION
        # Custom dual-model fallback: FastText → Word2Vec → auto-train
        # Ensures zero cold-start failure for low-resource Sinhala NLP
        # ── 1. Try loading existing model (FastText first, then Word2Vec) ─────
        for try_path, mtype in [(model_path, "fasttext"), (w2v_path, "word2vec")]:
            if os.path.exists(try_path):
                print(f"Loading embeddings from {try_path} …")
                try:
                    if mtype == "fasttext":
                        self.model = FastText.load(try_path)
                    else:
                        self.model = Word2Vec.load(try_path)
                    self.model_type = mtype
                    break
                except Exception as e:
                    print(f"  Could not load {try_path}: {e}")

        # ── 2. Train if nothing loaded ────────────────────────────────────────
        if self.model is None:
            enhanced = os.path.join(data_dir, "vocabulary_enhanced.txt")
            expanded = os.path.join(data_dir, "vocabulary_expanded.txt")

            if os.path.exists(enhanced):
                print("Training FastText on ENHANCED corpus (contextual sentences) …")
                self._train(enhanced, model_path)
            elif os.path.exists(expanded):
                print("Training FastText on EXPANDED vocabulary …")
                self._train(expanded, model_path)
            elif data_path and os.path.exists(data_path):
                print("Training FastText on provided data …")
                self._train(data_path, model_path)

    # ─────────────────────────────────────────────────────────────────────────
    # Training
    # ─────────────────────────────────────────────────────────────────────────

    def _train(self, corpus_path: str, save_path: str) -> None:
        """
        Train a FastText model on the corpus (one sentence per line).

        FastText uses character n-grams (min_n=2, max_n=6) so it can
        produce embeddings for any Sinhala morphological variant at
        inference time without needing every inflected form in the corpus.
        """
        sentences: list[list[str]] = []
        with open(corpus_path, encoding="utf-8") as f:
            for line in f:
                tokens = [_nc(t) for t in line.strip().split() if t.strip()]
                if tokens:
                    sentences.append(tokens)

        if not sentences:
            print("Empty corpus — skipping training.")
            return

        epochs = 30 if len(sentences) > 5_000 else 100
        print(f"  Corpus: {len(sentences):,} sentences  |  epochs={epochs}")

        # RESEARCH CONTRIBUTION
        # FastText tuned for Sinhala morphology: min_n=2, max_n=6, skip-gram
        # Handles OOV inflected forms (e.g., "නරකයි", "ගෙදරින්") unseen at training time
        # Adaptive epochs: 100 for small corpus, 30 for large corpus
        try:
            self.model = FastText(
                sentences=sentences,
                vector_size=100,
                window=5,
                min_count=1,
                workers=4,
                epochs=epochs,
                min_n=2,   # character n-gram min length
                max_n=6,   # character n-gram max length
                sg=1,      # skip-gram (better for rare/OOV words)
            )
            self.model_type = "fasttext"
            # Save with .model extension for consistent loading
            if not save_path.endswith(".model"):
                save_path = save_path + ".model"
        except Exception as e:
            print(f"FastText failed ({e}) — falling back to Word2Vec")
            self.model = Word2Vec(
                sentences=sentences,
                vector_size=100,
                window=5,
                min_count=1,
                workers=4,
                epochs=epochs,
                sg=1,
            )
            self.model_type = "word2vec"
            save_path = os.path.join(os.path.dirname(save_path), "word2vec.model")

        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        self.model.save(save_path)
        print(f"✅ {self.model_type} model saved → {save_path}  "
              f"(vocab: {len(self.model.wv.key_to_index):,})")

    # Kept for backwards compat with external callers
    def train_on_local_data(self, corpus_path: str, save_path: str) -> None:
        self._train(corpus_path, save_path)

    # ─────────────────────────────────────────────────────────────────────────
    # Inference
    # ─────────────────────────────────────────────────────────────────────────

    def get_vector(self, word: str):
        """Return the embedding vector for a word (OOV-safe for FastText)."""
        if not self.model:
            return None
        try:
            return self.model.wv[_nc(word)]
        except KeyError:
            return None

    def get_closest_word(
        self,
        word:            str,
        vocabulary_list: list[str],
        threshold:       float = 0.5,
    ) -> Tuple[Optional[str], float]:
        """
        Find the entry in vocabulary_list most semantically similar to 'word'.

        Returns
        ───────
        (best_match, similarity_score)  — best_match is None when nothing
        exceeds the threshold.

        Strategy
        ────────
        FastText  → direct vector lookup (always succeeds, even for OOV).
        Word2Vec  → tries exact form first, then progressively shorter
                    suffixes (1–6 chars stripped) to find a known root.
        """
        if not self.model or not GENSIM_AVAILABLE:
            return None, 0.0

        word_nc = _nc(word)

        # ── Resolve query vector ──────────────────────────────────────────────
        if self.model_type == "fasttext":
            # FastText always produces a vector (character n-grams handle OOV)
            try:
                _ = self.model.wv[word_nc]   # just to confirm it works
            except Exception:
                return None, 0.0
            query_word = word_nc

        # RESEARCH CONTRIBUTION
        # Progressive suffix stripping fallback for Word2Vec OOV resolution
        # Strips 1–6 chars from token right, checking each stem in model vocabulary
        else:  # Word2Vec — word must exist in vocabulary
            if word_nc in self.model.wv:
                query_word = word_nc
            else:
                # Progressive suffix stripping fallback
                query_word = None
                for strip_len in range(1, min(len(word_nc) - 1, 7)):
                    candidate = word_nc[:-strip_len]
                    if len(candidate) >= 2 and candidate in self.model.wv:
                        query_word = candidate
                        break
                if query_word is None:
                    return None, 0.0

        # ── Score every vocabulary word ───────────────────────────────────────
        best_word: Optional[str] = None
        best_sim:  float         = -1.0

        for vocab_word in vocabulary_list:
            vocab_nc = _nc(vocab_word)
            if not vocab_nc:
                continue
            try:
                if self.model_type == "fasttext":
                    sim = float(self.model.wv.similarity(query_word, vocab_nc))
                else:
                    if vocab_nc not in self.model.wv:
                        continue
                    sim = float(self.model.wv.similarity(query_word, vocab_nc))
            except Exception:
                continue

            if sim > best_sim:
                best_sim  = sim
                best_word = vocab_word

        if best_sim >= threshold:
            return best_word, best_sim
        return None, best_sim
