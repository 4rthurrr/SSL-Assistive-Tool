import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import os
import pickle
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Add parent dir
from seq2seq_model import Seq2SeqModel, Lang
from sinling import SinhalaTokenizer

# Configuration
DATASET_PATH = "../data/grammar_dataset.csv"
MODEL_SAVE_PATH = "../checkpoints/grammar_model.pth"
VOCAB_SAVE_PATH = "../checkpoints/grammar_vocab.pkl"
HIDDEN_SIZE = 128
EPOCHS = 35
LEARNING_RATE = 0.01

# Lang class moved to seq2seq_model.py


def indexesFromSentence(lang, sentence):
    return [lang.word2index[word] for word in sentence.split(' ')]

def tensorFromSentence(lang, sentence, device):
    indexes = indexesFromSentence(lang, sentence)
    indexes.append(1) # EOS
    return torch.tensor(indexes, dtype=torch.long, device=device).view(-1, 1)

def train(input_tensor, target_tensor, model, optimizer, criterion):
    optimizer.zero_grad()
    loss = 0
    target_length = target_tensor.size(0)
    
    # Teacher forcing logic is handled inside model for this simple implementation
    # or we can pass target here.
    # The model forward defined previously returns list of predicted indices.
    # For proper Backprop in simple PyTorch, we often run step-by-step outside.
    # To keep it compatible with the defined class, let's adjust:
    
    # Actually, the previous Seq2SeqModel.forward returned INDICES (inference style).
    # For training we need LOGITS or PROBABILITIES (Outputs).
    # Let's interact with encoder/decoder directly here or Refactor Model.
    # Refactoring Logic inline here for simplicity since I can't overwrite model file easily without tool call.
    
    encoder_hidden = model.encoder.initHidden(model.device)
    input_length = input_tensor.size(0)

    encoder_outputs = torch.zeros(100, model.encoder.hidden_size, device=model.device)

    for ei in range(input_length):
        encoder_output, encoder_hidden = model.encoder(input_tensor[ei], encoder_hidden)
        
    decoder_input = torch.tensor([[0]], device=model.device) # SOS
    decoder_hidden = encoder_hidden

    for di in range(target_length):
        decoder_output, decoder_hidden = model.decoder(decoder_input, decoder_hidden)
        loss += criterion(decoder_output, target_tensor[di])
        decoder_input = target_tensor[di] # Teacher Forcing

    loss.backward()
    optimizer.step()

    return loss.item() / target_length

def main():
    if not os.path.exists("checkpoints"):
        os.makedirs("checkpoints")
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Load Data
    if not os.path.exists(DATASET_PATH):
        print("Dataset not found. Please create grammar_dataset.csv")
        return

    df = pd.read_csv(DATASET_PATH)
    
    input_lang = Lang("Sinhala")
    output_lang = Lang("SSL")
    
    pairs = []
    
    tokenizer = SinhalaTokenizer()
    
    for idx, row in df.iterrows():
        # Tokenize Sinhala properly
        sin_tokens = tokenizer.tokenize(str(row['sinhala_sentence']))
        sin_sent = ' '.join(sin_tokens)
        
        ssl_sent = str(row['ssl_gloss_sequence']).strip()
        
        input_lang.addSentence(sin_sent)
        output_lang.addSentence(ssl_sent)
        pairs.append((sin_sent, ssl_sent))
    
    print(f"Read {len(pairs)} sentence pairs")
    print(f"Input Vocab: {input_lang.n_words}, Output Vocab: {output_lang.n_words}")
    
    model = Seq2SeqModel(input_lang.n_words, output_lang.n_words, HIDDEN_SIZE, device)
    optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.NLLLoss()
    
    print("Starting Training...")
    
    print("Starting Training...")
    
    import random
    
    # Adaptive Epochs/Size
    # If dataset is huge, we don't need 100 epochs of full pass.
    # We use Stochastic sampling.
    
    SAMPLE_SIZE = 1000 # Samples per epoch
    if len(pairs) > SAMPLE_SIZE:
        print(f"Dataset too large ({len(pairs)}). Using random sampling of {SAMPLE_SIZE} per epoch.")
    
    for epoch in range(1, EPOCHS + 1):
        total_loss = 0
        
        # Select batch
        if len(pairs) > SAMPLE_SIZE:
            batch_pairs = random.sample(pairs, SAMPLE_SIZE)
        else:
            batch_pairs = pairs
            
        for pair in batch_pairs:
            input_tensor = tensorFromSentence(input_lang, pair[0], device)
            target_tensor = tensorFromSentence(output_lang, pair[1], device)
            
            # Simple Training Loop
            loss = train(input_tensor, target_tensor, model, optimizer, criterion)
            total_loss += loss
            
        if epoch % 5 == 0:
            print(f"Epoch {epoch}/{EPOCHS} - Loss: {total_loss / len(batch_pairs):.4f}")
            
    # Save Model
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    with open(VOCAB_SAVE_PATH, 'wb') as f:
        pickle.dump({'input': input_lang, 'output': output_lang}, f)
        
    print(f"Model saved to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    main()
