import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
import sentencepiece as spm
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Add parent dir
from learned_models import SSLTranslationModel
import random

# CONFIG
DATA_FILE = "../data/training_data.json"
TOKENIZER_MODEL = "../models/sinhala_tokenizer.model"
MODEL_SAVE_PATH = "../models/ssl_model.pth"
VOCAB_SAVE_PATH = "../models/target_vocab.json"
BATCH_SIZE = 32
EPOCHS = 10 # Starting small
LEARNING_RATE = 0.0005
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class SSLDataset(Dataset):
    def __init__(self, samples, sp_tokenizer, target_vocab):
        self.samples = samples
        self.sp = sp_tokenizer
        self.target_vocab = target_vocab
        self.pad_id = 0 # Assume <pad> is 0 in SP? Check. Default SP uses 3? 
        # Actually SP: <unk>=0, <s>=1, </s>=2. user defined usually follow.
        # We will check SP vocab.
        
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        item = self.samples[idx]
        text = item['input']
        concepts = item['output']
        
        # Source: Tokenize
        # sp.encode(text, out_type=int) 
        src_ids = self.sp.encode(text, out_type=int)
        
        # Target: Map Concept IDs to Ints
        tgt_ids = [self.target_vocab['<start>']] + \
                  [self.target_vocab.get(c, self.target_vocab['<unk>']) for c in concepts] + \
                  [self.target_vocab['<end>']]
                  
        return torch.tensor(src_ids, dtype=torch.long), torch.tensor(tgt_ids, dtype=torch.long)

def collate_fn(batch):
    src_batch, tgt_batch = zip(*batch)
    # Pad
    src_padded = pad_sequence(src_batch, padding_value=0, batch_first=False) # Transformer expects (S, N) usually
    tgt_padded = pad_sequence(tgt_batch, padding_value=0, batch_first=False) # (T, N)
    return src_padded, tgt_padded

def build_target_vocab(samples):
    unique_concepts = set()
    for s in samples:
        unique_concepts.update(s['output'])
        
    # Valid tokens
    vocab = {"<pad>": 0, "<start>": 1, "<end>": 2, "<unk>": 3}
    idx = 4
    for c in sorted(list(unique_concepts)):
        vocab[c] = idx
        idx += 1
        
    print(f"Built Target Vocab: {len(vocab)} tokens")
    return vocab

def train():
    print(f"Training on {DEVICE}")
    
    # 1. Load Data
    if not os.path.exists(DATA_FILE):
        print("Data file not found. Run prepare_data.py first.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        samples = json.load(f)
        
    # shuffle
    random.shuffle(samples)
    
    # 2. Load Tokenizer
    if not os.path.exists(TOKENIZER_MODEL):
        print("Tokenizer not found.")
        return
        
    sp = spm.SentencePieceProcessor(model_file=TOKENIZER_MODEL)
    src_vocab_size = sp.get_piece_size()
    print(f"Source Vocab Size: {src_vocab_size}")
    
    # 3. Build Target Vocab
    target_vocab = build_target_vocab(samples)
    with open(VOCAB_SAVE_PATH, "w") as f:
        json.dump(target_vocab, f, indent=2)
        
    tgt_vocab_size = len(target_vocab)
    
    # 4. Dataset
    dataset = SSLDataset(samples, sp, target_vocab)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    
    # 5. Model
    model = SSLTranslationModel(src_vocab_size=src_vocab_size, 
                                tgt_vocab_size=tgt_vocab_size,
                                d_model=256,
                                nhead=4,
                                num_encoder_layers=2, # Keep small for speed
                                num_decoder_layers=2).to(DEVICE)
                                
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss(ignore_index=0) # Pad ID
    
    # 6. Loop
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0
        for i, (src, tgt) in enumerate(dataloader):
            src, tgt = src.to(DEVICE), tgt.to(DEVICE)
            
            # Target Input (shifted right) and Target Output
            tgt_input = tgt[:-1, :] # Drop last
            tgt_out = tgt[1:, :]    # Drop first (<start>)
            
            # Masks
            tgt_mask = model.generate_square_subsequent_mask(tgt_input.size(0)).to(DEVICE)
            
            # Padding Masks (Transposed for (N, S) requirement of mask usually?)
            # PyTorch Transformer src_key_padding_mask expects (N, S)
            # Our data is (S, N). transpose(0, 1)
            src_padding_mask = (src == 0).transpose(0, 1)
            tgt_padding_mask = (tgt_input == 0).transpose(0, 1)
            
            optimizer.zero_grad()
            output = model(src, tgt_input, 
                           tgt_mask=tgt_mask, 
                           src_key_padding_mask=src_padding_mask, 
                           tgt_key_padding_mask=tgt_padding_mask)
            
            # Reshape for Loss
            # output: (T, N, V) -> (T*N, V)
            # tgt_out: (T, N) -> (T*N)
            loss = criterion(output.view(-1, tgt_vocab_size), tgt_out.reshape(-1))
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            if i % 100 == 0:
                print(f"Epoch {epoch+1} Batch {i} Loss: {loss.item():.4f}")
            
            # Save Checkpoint periodically (e.g. every 2000 batches) to allow early testing
            if i > 0 and i % 2000 == 0:
                torch.save(model.state_dict(), MODEL_SAVE_PATH)
                print(f"   💾 Saved intermediate checkpoint to {MODEL_SAVE_PATH}")
                
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1} Complete. Avg Loss: {avg_loss:.4f}")
        
        # Save Checkpoint
        torch.save(model.state_dict(), MODEL_SAVE_PATH)
        print(f"Model saved to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train()
