import torch
import torch.nn as nn
import random

# Shared Language Class to avoid pickle issues across modules
class Lang:
    def __init__(self, name):
        self.name = name
        self.word2index = {"SOS": 0, "EOS": 1}
        self.word2count = {}
        self.index2word = {0: "SOS", 1: "EOS"}
        self.n_words = 2  # Count SOS and EOS

    def addSentence(self, sentence):
        for word in sentence.split(' '):
            self.addWord(word)

    def addWord(self, word):
        if word not in self.word2index:
            self.word2index[word] = self.n_words
            self.word2count[word] = 1
            self.index2word[self.n_words] = word
            self.n_words += 1
        else:
            self.word2count[word] += 1

class EncoderRNN(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(EncoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(input_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size)

    def forward(self, input, hidden):
        embedded = self.embedding(input).view(1, 1, -1)
        output, hidden = self.lstm(embedded, hidden)
        return output, hidden

    def initHidden(self, device):
        return (torch.zeros(1, 1, self.hidden_size, device=device),
                torch.zeros(1, 1, self.hidden_size, device=device))

class DecoderRNN(nn.Module):
    def __init__(self, hidden_size, output_size):
        super(DecoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(output_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size)
        self.out = nn.Linear(hidden_size, output_size)
        self.softmax = nn.LogSoftmax(dim=1)

    def forward(self, input, hidden):
        output = self.embedding(input).view(1, 1, -1)
        output = torch.relu(output)
        output, hidden = self.lstm(output, hidden)
        output = self.softmax(self.out(output[0]))
        return output, hidden

class Seq2SeqModel(nn.Module):
    def __init__(self, input_vocab_size, output_vocab_size, hidden_size=256, device='cpu'):
        super(Seq2SeqModel, self).__init__()
        self.encoder = EncoderRNN(input_vocab_size, hidden_size).to(device)
        self.decoder = DecoderRNN(hidden_size, output_vocab_size).to(device)
        self.device = device
        self.hidden_size = hidden_size
        self.SOS_token = 0
        self.EOS_token = 1

    def forward(self, input_tensor, target_tensor=None, teacher_forcing_ratio=0.5):
        # input_tensor: (seq_len)
        # target_tensor: (seq_len) if training
        
        input_length = input_tensor.size(0)
        target_length = target_tensor.size(0) if target_tensor is not None else 0
        
        encoder_hidden = self.encoder.initHidden(self.device)

        for ei in range(input_length):
            _, encoder_hidden = self.encoder(input_tensor[ei], encoder_hidden)

        decoder_input = torch.tensor([[self.SOS_token]], device=self.device)
        decoder_hidden = encoder_hidden

        outputs = []
        
        # Determine strict max length to prevent infinite loops (for inference)
        max_length = target_length if target_length > 0 else 20
        
        for di in range(max_length):
            decoder_output, decoder_hidden = self.decoder(decoder_input, decoder_hidden)
            topv, topi = decoder_output.topk(1)
            outputs.append(topi.item())
            
            if topi.item() == self.EOS_token:
                break

            if target_tensor is not None:
                # Teacher forcing: Feed the target as the next input
                use_teacher_forcing = random.random() < teacher_forcing_ratio
                if use_teacher_forcing:
                    decoder_input = target_tensor[di].view(1, 1)
                else:
                    decoder_input = topi.squeeze().detach()
            else:
                 decoder_input = topi.squeeze().detach()
                 
        return outputs, decoder_output # output only last strictly correct for simple loss
