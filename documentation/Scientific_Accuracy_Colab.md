# Scientific Accuracy Verification (Google Colab Version)

Use this script to verify your accuracy results independently in Google Colab.

### **Instructions**
1.  Open [Google Colab](https://colab.research.google.com/).
2.  Create a **New Notebook**.
3.  **Upload Files** (Click the Folder icon on the left):
    *   Upload `backend/data/vocabulary_expanded.txt`
    *   Upload `backend/models/word2vec.model`
4.  **Copy & Paste** the code below into a cell and run it (Play button).

---

```python
# --- STEP 1: INSTALL DEPENDENCIES ---
!pip install gensim

# --- STEP 2: IMPORT LIBRARIES ---
import os
import random
from gensim.models import Word2Vec

# --- STEP 3: DEFINE THE ACCURACY LOGIC ---
class SimpleEmbeddingsHandler:
    def __init__(self, model_path="word2vec.model"):
        print(f"Loading Model from {model_path}...")
        try:
            self.model = Word2Vec.load(model_path)
            print("✅ Model Loaded Successfully!")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self.model = None

    def get_closest_word(self, word, vocabulary_list, threshold=0.6):
        if not self.model: return None, 0.0
        
        # Exact match check
        word = word.lower()
        if word not in self.model.wv: return None, 0.0

        best_word = None
        best_sim = -1.0
        
        # Check against allowed vocabulary
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

# --- STEP 4: LOAD DATA & RUN TEST ---
def run_accuracy_test():
    if not os.path.exists("vocabulary_expanded.txt"):
        print("❌ ERROR: Please upload 'vocabulary_expanded.txt' to Colab files!")
        return

    print("📂 Loading Data...")
    all_pairs = []
    unique_roots = set()
    
    with open("vocabulary_expanded.txt", "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                variation = parts[0]
                root = parts[1]
                unique_roots.add(root)
                if variation != root:
                    all_pairs.append((variation, root))
    
    # Vocabulary List (Words the system actually knows)
    vocab_list = list(unique_roots)

    # Sample 1000 Cases
    SAMPLE_SIZE = 1000
    if len(all_pairs) < SAMPLE_SIZE:
        test_cases = all_pairs
    else:
        test_cases = random.sample(all_pairs, SAMPLE_SIZE)
    
    # Run Inference
    handler = SimpleEmbeddingsHandler()
    if not handler.model: return

    correct = 0
    total = len(test_cases)
    
    print(f"\n🚀 Running {total} Blind Tests...")
    print("-" * 60)
    print(f"{'Input':<20} | {'Expected':<15} | {'AI Predicted':<15} | {'Result'}")
    print("-" * 60)

    for i, (input_word, expected_root) in enumerate(test_cases):
        predicted, score = handler.get_closest_word(input_word, vocab_list)
        
        is_correct = (predicted == expected_root)
        if is_correct: correct += 1
        
        if i < 15: # Print first 15 samples
            status = "✅" if is_correct else "❌"
            print(f"{input_word:<20} | {expected_root:<15} | {str(predicted):<15} | {status}")

    accuracy = (correct / total) * 100
    print("-" * 60)
    print(f"\n📊 FINAL ACCURACY: {accuracy:.2f}% ({correct}/{total})")

# EXECUTE
run_accuracy_test()
```
