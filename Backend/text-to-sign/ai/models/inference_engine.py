import torch
import json
import sentencepiece as spm
from learned_models import SSLTranslationModel
import os

# Config (Must match training)
TOKENIZER_MODEL = "models/sinhala_tokenizer.model"
MODEL_PATH = "models/ssl_model.pth"
VOCAB_PATH = "models/target_vocab.json"
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MAX_LEN = 50

class LearnedInference:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.base_dir = base_dir
        self.model = None
        self.tokenizer = None
        self.target_vocab = None
        self.idx2concept = {}
        
        self.load_resources()
        
    def load_resources(self):
        print("🧠 Loading Learned SSL Model...")
        
        # 1. Load Tokenizer
        tok_path = os.path.join(self.base_dir, TOKENIZER_MODEL)
        if not os.path.exists(tok_path):
            raise FileNotFoundError(f"Tokenizer not found at {tok_path}")
        self.tokenizer = spm.SentencePieceProcessor(model_file=tok_path)
        src_vocab_size = self.tokenizer.get_piece_size()
        
        # 2. Load Vocab
        vocab_path = os.path.join(self.base_dir, VOCAB_PATH)
        if not os.path.exists(vocab_path):
            raise FileNotFoundError(f"Vocab not found at {vocab_path}")
        with open(vocab_path, "r") as f:
            self.target_vocab = json.load(f)
            
        self.idx2concept = {v: k for k, v in self.target_vocab.items()}
        tgt_vocab_size = len(self.target_vocab)
        
        # 3. Load Model
        model_path = os.path.join(self.base_dir, MODEL_PATH)
        self.model = SSLTranslationModel(src_vocab_size, tgt_vocab_size, 
                                         d_model=256, nhead=4, 
                                         num_encoder_layers=2, num_decoder_layers=2).to(DEVICE)
                                         
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=DEVICE))
            print("✅ Model weights loaded.")
        else:
            print("⚠️ Model ID warning: Model file not found. Using initialized weights (Untrained).")
            
        self.model.eval()

    def translate(self, text):
        """
        Translates Sinhala text -> List of Concept IDs
        """
        # Encode Source
        src_ids = self.tokenizer.encode(text, out_type=int)
        src_tensor = torch.tensor(src_ids, dtype=torch.long).unsqueeze(1).to(DEVICE) # (S, 1)
        
        # Greedy Decode
        # Start with <start>
        start_token = self.target_vocab.get('<start>', 1)
        end_token = self.target_vocab.get('<end>', 2)
        
        tgt_indices = [start_token]
        
        for i in range(MAX_LEN):
            tgt_tensor = torch.tensor(tgt_indices, dtype=torch.long).unsqueeze(1).to(DEVICE) # (T, 1)
            
            with torch.no_grad():
                # Forward
                tgt_mask = self.model.generate_square_subsequent_mask(tgt_tensor.size(0)).to(DEVICE)
                output = self.model(src_tensor, tgt_tensor, tgt_mask=tgt_mask)
                
                # Get last token logits
                logits = output[-1, 0, :]
                
                # CUSTOM OPTIMIZATION
                # Manual repetition penalty in Seq2Seq greedy decoding
                # Penalizes previously predicted concept tokens to prevent prediction loops
                # Bug fix: added after observing model producing repeated identical sign sequences
                # Repetition Penalty
                for prev_idx in tgt_indices:
                    if prev_idx == self.target_vocab.get('<start>'): continue
                    logits[prev_idx] /= 1.5 # Penalize previous tokens (Divide positive logits, need careful handling if negative)
                    # Better: Subtract a large value or multiply if probability. 
                    # For logits (unnormalized):
                    if logits[prev_idx] > 0:
                        logits[prev_idx] /= 2.0
                    else:
                        logits[prev_idx] *= 2.0
                
                predicted_id = logits.argmax(dim=-1).item()
                
            if predicted_id == end_token:
                break
                
            # Fallback: if it predicts start token again or same as last, force break or skip
            if predicted_id == tgt_indices[-1] and len(tgt_indices) > 3:
                 # Force break if looping tight
                 break
            
            tgt_indices.append(predicted_id)
            
        # Convert IDs back to Concepts
        concepts = []
        for idx in tgt_indices[1:]: # Skip <start>
            concept = self.idx2concept.get(idx, '<unk>')
            if concept not in ['<pad>', '<start>', '<end>']:
                concepts.append(concept)
                
        return concepts

# Test
if __name__ == "__main__":
    engine = LearnedInference()
    print(engine.translate("මම ගෙදර යනවා"))
