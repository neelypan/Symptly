import torch.nn as nn

class SymptomClassifier(nn.Module):
    def __init__(self, inputSize, numClasses):
        super().__init__()
        self.fc1 = nn.Linear(inputSize, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, numClasses)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x
