import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import json
from torch.utils.data import DataLoader, TensorDataset

# load training data and get rid of extra column made by trailing columns in the csv file
df = pd.read_csv('data/Training.csv').drop(columns=['Unnamed: 133'])
print(f'dataframe shape {df.shape}') # verify shape is correct

# break data into X and y, where X is the symtpoms and y is the disease
X = df.drop(columns=['prognosis'])
y = df['prognosis']
print(f'(x,y) ({X.shape},{y.shape})') # verify shapes are correct
# more checks
print(f'X type: {type(X)}')
print(f'y type: {type(y)}')
print(f'y first 5 values: {y.head().tolist()}')

# convert string values in y to numbers
labelEncoder = LabelEncoder()
yEncoded = labelEncoder.fit_transform(y)
# check stuff
print('y encoded:', yEncoded)
print(f"First 10 encoded labels: {yEncoded[:10]}")
print(f"Number of classes: {len(labelEncoder.classes_)}")
print(f"First 5 class names: {labelEncoder.classes_[:5]}")

# write encoded and their string values to a json file for later
labelMap = {int(i): name for i, name in enumerate(labelEncoder.classes_)} 
with open('model/labelMap.json', 'w') as f:
    json.dump(labelMap, f, indent=2)

print(f'label map saved with {len(labelMap)} classes')

xTrain, xVal, yTrain, yVal = train_test_split(
    X, yEncoded,
    test_size=0.2,
    random_state=42,
    stratify=yEncoded
)

print(f"xTrain shape: {xTrain.shape}")   # should be (3936, 132)
print(f"xVal shape:   {xVal.shape}")     # should be (984, 132)
print(f"yTrain shape: {yTrain.shape}")   # should be (3936,)
print(f"yVal shape:   {yVal.shape}")     # should be (984,)

xTrainTensor = torch.tensor(xTrain.values, dtype=torch.float32)
yTrainTensor = torch.tensor(yTrain, dtype=torch.long)
xValTensor = torch.tensor(xVal.values, dtype=torch.float32)
yValTensor = torch.tensor(yVal, dtype=torch.long)

print(f"XTrainTensor shape: {xTrainTensor.shape}, dtype: {xTrainTensor.dtype}")
print(f"yTrainTensor shape: {yTrainTensor.shape}, dtype: {yTrainTensor.dtype}")


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

inputSize = xTrainTensor.shape[1]
numClasses = len(labelEncoder.classes_)
model = SymptomClassifier(inputSize, numClasses)
print(model)

trainDataset = TensorDataset(xTrainTensor, yTrainTensor)
valDataset = TensorDataset(xValTensor, yValTensor)

trainLoader = DataLoader(trainDataset, batch_size=32, shuffle=True)
valLoader = DataLoader(valDataset, batch_size=32, shuffle=False)

lossFunc = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

numEpochs = 50

for epoch in range(numEpochs):
    # Training:
    model.train()
    trainLoss, trainCorrect, trainTotal = 0, 0, 0
    
    for batchX, batchY in trainLoader:
        preds = model(batchX)
        loss = lossFunc(preds, batchY)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        trainLoss += loss.item()
        _, predictedClasses = torch.max(preds, 1)
        trainCorrect += (predictedClasses == batchY).sum().item()
        trainTotal += batchY.size(0)
        
    trainAccuracy = (trainCorrect / trainTotal)*100
    avgTrainLoss = trainLoss / len(trainLoader)
    
    # Validation:
    model.eval()
    valLoss, valCorrect, valTotal = 0, 0, 0
    
    with torch.no_grad(): # dont track gradients during validation bc they arent needed and it is faster and saved memory
        for batchX, batchY in valLoader:
            preds = model(batchX)
            loss = lossFunc(preds, batchY)
            
            valLoss += loss.item()
            _, predictedClasses = torch.max(preds, 1)
            valCorrect += (predictedClasses == batchY).sum().item()
            valTotal += batchY.size(0)
        
    valAccuracy = (valCorrect / valTotal) * 100
    avgValLoss = valLoss / len(valLoader)
    
    print(f'Epoch {epoch + 1}/{numEpochs} | '
          f'Train Loss: {avgTrainLoss:.4f} | Train Accuracy: {trainAccuracy:.2f}% | '
          f'Val Loss: {avgValLoss:.4f} | Val Accuracy: {valAccuracy:.2f}%')
        