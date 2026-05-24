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
