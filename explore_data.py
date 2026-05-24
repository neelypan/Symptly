import pandas as pd
df = pd.read_csv('./data/Training.csv')
df = df.drop(columns=['Unnamed: 133'])
print('shape', df.shape)
print('head',df.head())
print('columns list', df.columns.tolist())
print('value counts',df.iloc[:,-1].value_counts())
print("missing vals", df.isnull().sum().sum())