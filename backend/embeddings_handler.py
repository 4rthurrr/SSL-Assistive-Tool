import os
import re
try:
    from gensim.models import Word2Vec, KeyedVectors
    import numpy as np
    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False
    print("Warning: Gensim not installed. Semantic search will fallback to exact match.")

class EmbeddingsHandler:
    def __init__(self, model_path="models/word2vec.model", data_path=None):
        self.model = None
        self.dims = 100
        
        # Resolve paths relative to this file's directory if they are relative
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(model_path):
            model_path = os.path.join(base_dir, model_path)
        if data_path and not os.path.isabs(data_path):
            data_path = os.path.join(base_dir, data_path)
            
        if not GENSIM_AVAILABLE:
            return

        # 1. Try Loading Pre-trained/Existing Model
        if os.path.exists(model_path):
            print(f"Loading embeddings from {model_path}...")
            try:
                self.model = Word2Vec.load(model_path)
            except:
                # Try loading as KeyedVectors (e.g. Google News bin)
                try:
                    self.model = KeyedVectors.load_word2vec_format(model_path, binary=True)
                except Exception as e:
                    print(f"Failed to load model: {e}")

        # 2. If no model, Train on available data
        if self.model is None:
            # Priority: Robust Synthetic Data -> Grammar Dataset
            primary_data = "data/vocabulary_expanded.txt"
            if os.path.exists(os.path.join(base_dir, primary_data)):
                print(f"Training embeddings on FAST dataset: {primary_data}...")
                self.train_on_local_data(os.path.join(base_dir, primary_data), model_path)
            elif data_path and os.path.exists(data_path):
                print("Training embeddings on LEGACY dataset (pairs.csv)...")
                self.train_on_local_data(data_path, model_path)
    
    def train_on_local_data(self, csv_path, save_path):
        """
        Trains a quick Word2Vec model on the `pairs.csv` vocabulary 
        so we at least have embeddings for the words we use.
        """
        sentences = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Naive tokenizer: split by comma, then underscore/space
                parts = re.split(r'[_, ]+', line.strip().lower())
                # REMOVED isalpha() check because it fails for Sinhala on some systems
                clean_parts = [p.strip() for p in parts if len(p.strip()) > 1]
                if clean_parts:
                    sentences.append(clean_parts)
        
        if not sentences:
            print("No training data found in pairs.csv")
            return

        # Train Word2Vec
        # Small dataset optimization: Smaller vector size, more epochs
        # Custom settings for Large Dataset vs Small
        epochs = 5 if len(sentences) > 10000 else 100
        
        print(f"Training Word2Vec on {len(sentences)} sentences (Epochs: {epochs})...")
        self.model = Word2Vec(sentences, vector_size=50, window=5, min_count=1, workers=4, epochs=epochs)
        if "vocabulary_expanded.txt" in csv_path:
             print("Training with High Epochs for Synthetic Data...")
             self.model.train(sentences, total_examples=len(sentences), epochs=50) # 50 is enough for 6k lines
        else:
             self.model.train(sentences, total_examples=len(sentences), epochs=5)
        self.model.save(save_path)
        print(f"Local embeddings model saved to {save_path}")

    def get_closest_word(self, word, vocabulary_list, threshold=0.6):
        """
        Finds the word in `vocabulary_list` that is most similar to `word`.
        Returns (best_match_word, similarity_score).
        Returns None if no good match found.
        """
        if not self.model or not GENSIM_AVAILABLE:
            return None, 0.0

        word = word.lower()
        
        # Check if query word exists in model
        if word not in self.model.wv:
            return None, 0.0
            
        best_word = None
        best_sim = -1.0
        
        # We only care about matching words that actually exist in our System's Vocabulary (vocabulary_list)
        # Because we can only sign words we have videos/grammar for.
        for vocab_word in vocabulary_list:
            vocab_lower = vocab_word.lower()
            if vocab_lower in self.model.wv:
                sim = self.model.wv.similarity(word, vocab_lower)
                if sim > best_sim:
                    best_sim = sim
                    best_word = vocab_word
        
        if best_sim >= threshold:
            return best_word, best_sim
        
        return None, best_sim
