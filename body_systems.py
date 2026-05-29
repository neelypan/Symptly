# each symptom is mapped to a body system, unclear symptoms from the dataset are treated as general and are not included here
SYMPTOM_TO_SYSTEM = {
    # Respiratory
    'continuous_sneezing': 'respiratory',
    'cough': 'respiratory',
    'breathlessness': 'respiratory',
    'phlegm': 'respiratory',
    'throat_irritation': 'respiratory',
    'sinus_pressure': 'respiratory',
    'runny_nose': 'respiratory',
    'congestion': 'respiratory',
    'patches_in_throat': 'respiratory',
    'mucoid_sputum': 'respiratory',
    'rusty_sputum': 'respiratory',
    'blood_in_sputum': 'respiratory',
    
    # Digestive
    'stomach_pain': 'digestive',
    'acidity': 'digestive',
    'vomiting': 'digestive',
    'indigestion': 'digestive',
    'nausea': 'digestive',
    'loss_of_appetite': 'digestive',
    'constipation': 'digestive',
    'abdominal_pain': 'digestive',
    'diarrhoea': 'digestive',
    'pain_during_bowel_movements': 'digestive',
    'pain_in_anal_region': 'digestive',
    'bloody_stool': 'digestive',
    'irritation_in_anus': 'digestive',
    'passage_of_gases': 'digestive',
    'belly_pain': 'digestive',
    'distention_of_abdomen': 'digestive',
    'stomach_bleeding': 'digestive',
    
    # Neurological
    'headache': 'neurological',
    'dizziness': 'neurological',
    'altered_sensorium': 'neurological',
    'lack_of_concentration': 'neurological',
    'visual_disturbances': 'neurological',
    'spinning_movements': 'neurological',
    'loss_of_balance': 'neurological',
    'unsteadiness': 'neurological',
    'weakness_of_one_body_side': 'neurological',
    'slurred_speech': 'neurological',
    'coma': 'neurological',
    'blurred_and_distorted_vision': 'neurological',
    'pain_behind_the_eyes': 'neurological',
    
    # Musculoskeletal
    'joint_pain': 'musculoskeletal',
    'back_pain': 'musculoskeletal',
    'neck_pain': 'musculoskeletal',
    'knee_pain': 'musculoskeletal',
    'hip_joint_pain': 'musculoskeletal',
    'muscle_weakness': 'musculoskeletal',
    'stiff_neck': 'musculoskeletal',
    'swelling_joints': 'musculoskeletal',
    'movement_stiffness': 'musculoskeletal',
    'cramps': 'musculoskeletal',
    'muscle_pain': 'musculoskeletal',
    'painful_walking': 'musculoskeletal',
    'muscle_wasting': 'musculoskeletal',
    
    # Skin
    'itching': 'skin',
    'skin_rash': 'skin',
    'nodal_skin_eruptions': 'skin',
    'dischromic _patches': 'skin',
    'pus_filled_pimples': 'skin',
    'blackheads': 'skin',
    'scurring': 'skin',
    'skin_peeling': 'skin',
    'silver_like_dusting': 'skin',
    'small_dents_in_nails': 'skin',
    'inflammatory_nails': 'skin',
    'blister': 'skin',
    'red_sore_around_nose': 'skin',
    'yellow_crust_ooze': 'skin',
    'red_spots_over_body': 'skin',
    'bruising': 'skin',
    'brittle_nails': 'skin',
    
    # Urinary
    'burning_micturition': 'urinary',
    'spotting_ urination': 'urinary',
    'dark_urine': 'urinary',
    'yellow_urine': 'urinary',
    'bladder_discomfort': 'urinary',
    'foul_smell_of urine': 'urinary',
    'continuous_feel_of_urine': 'urinary',
    'polyuria': 'urinary',
    
    # Cardiovascular
    'chest_pain': 'cardiovascular',
    'fast_heart_rate': 'cardiovascular',
    'palpitations': 'cardiovascular',
    'swollen_legs': 'cardiovascular',
    'swollen_blood_vessels': 'cardiovascular',
    'prominent_veins_on_calf': 'cardiovascular',
}


# which body systems a set of symptoms touches (unknown ones fall back to 'general')
def getBodySystems(symptoms):
    systems = set()
    for s in symptoms:
        systems.add(SYMPTOM_TO_SYSTEM.get(s, 'general'))
    return systems


# do two symptom sets share a body system? used to guess if new symptoms belong to the same issue
def systemsOverlap(symptomsA, symptomsB):
    # drop 'general' since its too vague to judge overlap on
    systemsA = getBodySystems(symptomsA) - {'general'}
    systemsB = getBodySystems(symptomsB) - {'general'}

    # if either side is only general symptoms we cant tell, so assume related
    if not systemsA or not systemsB:
        return True

    return bool(systemsA & systemsB)



import os
import json

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_SCRIPT_DIR, 'model', 'symptomList.json'), 'r') as _f:
    SYMPTOM_LIST = json.load(_f)

SYSTEM_ORDER = [
    'respiratory', 'cardiovascular', 'neurological', 'digestive',
    'urinary', 'musculoskeletal', 'skin', 'general',
]
SYSTEM_LABELS = {
    'respiratory': 'Respiratory',
    'cardiovascular': 'Cardiovascular',
    'neurological': 'Neurological',
    'digestive': 'Digestive',
    'urinary': 'Urinary',
    'musculoskeletal': 'Musculoskeletal',
    'skin': 'Skin',
    'general': 'General',
}
SYSTEM_ICONS = {
    'respiratory': 'wind',
    'cardiovascular': 'heart',
    'neurological': 'brain',
    'digestive': 'utensils',
    'urinary': 'droplets',
    'musculoskeletal': 'bone',
    'skin': 'hand',
    'general': 'stethoscope',
}

_NAME_OVERRIDES = {
    'dischromic _patches': 'Discolored patches',
    'spotting_ urination': 'Spotting during urination',
    'foul_smell_of urine': 'Foul-smelling urine',
    'toxic_look_(typhos)': 'Toxic appearance',
    'scurring': 'Scarring',
    'cold_hands_and_feets': 'Cold hands and feet',
    'continuous_feel_of_urine': 'Constant urge to urinate',
    'swelled_lymph_nodes': 'Swollen lymph nodes',
    'swollen_extremeties': 'Swollen extremities',
    'extra_marital_contacts': 'Extramarital contact',
    'fluid_overload.1': 'Fluid overload',
}

_HIDDEN_IDS = {'fluid_overload.1'}


def cleanSymptomName(symptom):
    if symptom in _NAME_OVERRIDES:
        return _NAME_OVERRIDES[symptom]
    label = ' '.join(symptom.replace('_', ' ').split())
    return label[:1].upper() + label[1:] if label else symptom


def getSystemForSymptom(symptom):
    return SYMPTOM_TO_SYSTEM.get(symptom, 'general')


def getBodySystemGroups():
    buckets = {sys: [] for sys in SYSTEM_ORDER}
    for symptom in SYMPTOM_LIST:
        if symptom in _HIDDEN_IDS:
            continue
        system = getSystemForSymptom(symptom)
        buckets.setdefault(system, []).append({
            'id': symptom,
            'label': cleanSymptomName(symptom),
        })

    groups = []
    for system in SYSTEM_ORDER:
        items = sorted(buckets.get(system, []), key=lambda s: s['label'])
        if items:
            groups.append({
                'system': system,
                'label': SYSTEM_LABELS[system],
                'icon': SYSTEM_ICONS[system],
                'symptoms': items,
            })
    return groups