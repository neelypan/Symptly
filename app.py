from flask import Flask, request, jsonify
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'model'))

from predict import predict
from safety import checkForEmergency

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')



@app.route('/')
def home():
    return jsonify({
        'app': 'Symptly',
        'status': 'running',
        'version': '0.1.0'
    })


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/predict', methods=['POST'])
def predictRoute():
    data = request.get_json()
    
    if not data or 'symptoms' not in data:
        return jsonify({'error': 'Missing symptoms in request body'}), 400
    
    symptoms = data['symptoms']
    
    if not isinstance(symptoms, list):
        return jsonify({'error': 'symptoms must be a list'}), 400
    
    if len(symptoms) == 0:
        return jsonify({'error': 'symptoms list is empty'}), 400
    
    emergency = checkForEmergency(symptoms)
    if emergency:
        return jsonify(emergency), 200
    
    predictions = predict(symptoms, topK=3)
    
    return jsonify({
        'isEmergency': False,
        'predictions': predictions
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)