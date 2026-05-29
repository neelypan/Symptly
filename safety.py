# Emergency symptoms drawn from the dataset's column names, these are conditions where waiting on AI predictions could cause harm.
EMERGENCY_SYMPTOMS = {
    'chest_pain',
    'breathlessness',
    'altered_sensorium',
    'coma',
    'loss_of_balance',
    'weakness_of_one_body_side',
    'slurred_speech',
    'stomach_bleeding',
    'acute_liver_failure',
}


EMERGENCY_RESPONSE = {
    'isEmergency': True,
    'title': 'This may be a medical emergency',
    'message': (
        'Some symptoms you reported could indicate a serious medical emergency. '
        'Please seek immediate medical attention.'
    ),
    'resources': [
        {'label': 'US Emergency', 'value': '911'},
        {'label': 'UK Emergency', 'value': '999'},
        {'label': 'EU Emergency', 'value': '112'},
        {'label': 'Mental Health (US)', 'value': '988'},
        {'label': 'International Helplines', 'value': 'findahelpline.com'},
    ],
    'note': (
        'Symptly is an educational tool and is not equipped to assist with '
        'emergencies. Please reach out to a real person who can help right now.'
    )
}

# if any emergency symptom shows up we skip the AI and tell them to get help
def checkForEmergency(symptoms):
    if not symptoms:
        return None

    matched = [s for s in symptoms if s in EMERGENCY_SYMPTOMS]

    if matched:
        res = EMERGENCY_RESPONSE.copy()
        res['matchedSymptoms'] = matched  # so the UI can show which ones triggered it
        return res

    return None