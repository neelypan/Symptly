import torch
import torch.nn.functional as F
import json
import os

from symptom_classifier import SymptomClassifier

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# symptomList sets the input order, labelMap turns class indices back into disease names
with open(os.path.join(SCRIPT_DIR, 'symptomList.json'), 'r') as f:
    SYMPTOM_LIST = json.load(f)

with open(os.path.join(SCRIPT_DIR, 'labelMap.json'), 'r') as f:
    LABEL_MAP = json.load(f)

NUM_SYMPTOMS = len(SYMPTOM_LIST)
NUM_CLASSES = len(LABEL_MAP)

# load the trained weights once at import so the app reuses the same model
model = SymptomClassifier(NUM_SYMPTOMS, NUM_CLASSES)

model.load_state_dict(torch.load(
    os.path.join(SCRIPT_DIR, 'symptomClassifier.pt'),
    weights_only=True
))

model.eval()  # inference mode, turns off dropout


def symptomsToVector(symptoms):
    # multi-hot vector: 1 in the slot for each symptom the user has, 0 everywhere else
    vector = [0] * NUM_SYMPTOMS

    for sym in symptoms:
        if sym in SYMPTOM_LIST:
            idx = SYMPTOM_LIST.index(sym)
            vector[idx] = 1
        else:
            print(f'WARNING: unknown symptom "{sym}"')
    return torch.tensor([vector], dtype=torch.float32)

def predict(symptoms, topK=3):
    if not symptoms:
        return []

    inputTensor = symptomsToVector(symptoms)

    # softmax turns raw scores into probabilities so the percentages add up
    with torch.no_grad():
        rawScores = model(inputTensor)
        probs = F.softmax(rawScores, dim=1)
    
    # grab the topK highest-probability diseases
    topProbs, topIdxs = torch.topk(probs, topK, dim=1)

    res = []
    for prob, idx in zip(topProbs[0], topIdxs[0]):
        diseaseName = LABEL_MAP[str(idx.item())]
        confidence = round(prob.item() * 100, 2)
        res.append({
            'disease': diseaseName,
            'confidence': confidence
        })
    
    return res

if __name__ == '__main__':
    # quick sanity check when running this file directly
    testCases = [
        ['itching', 'skin_rash', 'nodal_skin_eruptions'],
        ['headache', 'high_fever', 'vomiting', 'fatigue'],
        ['chest_pain', 'breathlessness', 'sweating'],
        ['continuous_sneezing', 'runny_nose', 'cough'],
    ]
    
    for symptoms in testCases:
        print(f'symptoms: {symptoms}')
        res = predict(symptoms)
        for r in res:
            print(f"{r['disease']}: {r['confidence']}")