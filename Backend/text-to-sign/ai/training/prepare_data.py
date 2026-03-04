import os
import csv
import json
import sentencepiece as spm
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Add parent dir
from concept_registry import get_registry

# Configuration
DATASET_CSV = "../data/grammar_dataset.csv"  # Relative to this script in 'training/'
TOKENIZER_PREFIX = "../models/sinhala_tokenizer"
VOCAB_SIZE = 8000
OUTPUT_FILE = "../data/training_data.json"
MAX_SAMPLES = 1000000  # Limit for memory safety/demo, set to None for full dataset

def train_tokenizer(sentences):
    print("Training Tokenizer...")
    with open("temp_corpus.txt", "w", encoding="utf-8") as f:
        for s in sentences:
            f.write(s + "\n")
    
    # Train SentencePiece
    # Uses BPE algorithm
    try:
        spm.SentencePieceTrainer.train(
            input="temp_corpus.txt",
            model_prefix=TOKENIZER_PREFIX,
            vocab_size=min(VOCAB_SIZE, len(set("".join(sentences))) + 1000), # Cap vocab if dataset is small
            character_coverage=0.9995,
            model_type="bpe",
            user_defined_symbols=["<pad>", "<start>", "<end>"]
        )
        print("✅ Tokenizer training complete.")
    finally:
        if os.path.exists("temp_corpus.txt"):
            os.remove("temp_corpus.txt")

def prepare_data():
    print("🚀 Starting Data Preparation...")
    registry = get_registry()
    
    # Read CSV
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, DATASET_CSV)
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    sentences = []
    samples = []
    
    print(f"📂 Reading {DATASET_CSV}...")
    
    skipped_glosses = set()
    mapped_count = 0
    
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader) # Skip header
        except StopIteration:
            print("❌ Empty CSV")
            return
            
        for i, row in enumerate(reader):
            if MAX_SAMPLES and i >= MAX_SAMPLES:
                break
                
            if len(row) < 2: continue
            sinhala = row[0].strip()
            gloss_seq = row[1].strip()
            
            if not sinhala or not gloss_seq: continue
            
            # Use for tokenizer training
            sentences.append(sinhala)
            
            # Map Gloss -> Concepts
            glosses = gloss_seq.split()
            concept_ids = []
            
            # We want to train on VALID sequences only.
            # If a gloss is missing from registry, we might skip the sentence 
            # OR hopefully mapped everything.
            
            valid_sequence = True
            sequence_ids = []
            
            for g in glosses:
                cid = registry.get_concept_by_label(g)
                if not cid:
                    # Try some basic heuristics or check concepts.py directly if registry missed it
                    # But per rules, we trust registry (dataset folders).
                    
                    # For robust training, let's skip unknown concepts for now
                    # or log them.
                    if g not in skipped_glosses:
                        print(f"⚠️ Warning: Gloss '{g}' not found in registry (Dataset folders).")
                        skipped_glosses.add(g)
                    valid_sequence = False
                    break # Skip this word/sentence? 
                    
                    # Alternative: If strict, we can't train on this.
                    # Ideally we fix the dataset or registry.
                else:
                    sequence_ids.append(cid)
            
            if valid_sequence and sequence_ids:
                samples.append({
                    "input": sinhala,
                    "output": sequence_ids
                })
                mapped_count += 1
                
            if i % 10000 == 0:
                print(f"   Processed {i} rows... ({mapped_count} valid)")

    print(f"✅ Loaded {len(sentences)} sentences.")
    print(f"⚠️ Skipped {len(skipped_glosses)} unique unknown glosses.")
    
    # Train Tokenizer
    if sentences:
        train_tokenizer(sentences)
    else:
        print("❌ No sentences found to train tokenizer.")

    # Save processed data
    output_path = os.path.join(base_dir, OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(samples)} training samples to {OUTPUT_FILE}")

if __name__ == "__main__":
    prepare_data()
