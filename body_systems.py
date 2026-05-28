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


def getBodySystems(symptoms):
    systems = set()
    for s in symptoms:
        systems.add(SYMPTOM_TO_SYSTEM.get(s, 'general'))
    return systems


def systemsOverlap(symptomsA, symptomsB):
    systemsA = getBodySystems(symptomsA) - {'general'}
    systemsB = getBodySystems(symptomsB) - {'general'}
    


    if not systemsA or not systemsB:
        return True
    
    return bool(systemsA & systemsB)