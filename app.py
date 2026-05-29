import os
import re
import sys
import uuid
from functools import wraps
from datetime import datetime, timezone, timedelta

from flask import (
    Flask, request, jsonify, render_template, redirect, url_for, session, flash,
)
from dotenv import load_dotenv

# predict.py imports its sibling modules by bare name, so model/ must be on the path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'model'))

from predict import predict
from safety import checkForEmergency
from body_systems import getBodySystemGroups, systemsOverlap
import database as db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')

STALE_AFTER = timedelta(days=7)

#not using real email otp for testing, if publish i would set it up
def devUserId(email):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'symptly-user:' + email.strip().lower()))


def loginRequired(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get('userId'):
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapper


# --- date / staleness helpers ---------------------------------------------
def parseTs(ts):
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts
    cleaned = ts.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        # Trim sub-microsecond precision that fromisoformat (3.9) rejects.
        cleaned = re.sub(r'(\.\d{6})\d+', r'\1', cleaned)
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return None


def formatDate(ts):
    """Format as 'Nov 25 2025' (no leading zero on the day)."""
    dt = parseTs(ts)
    if not dt:
        return ''
    return f"{dt.strftime('%b')} {dt.day} {dt.year}"


def isStale(episode):
    if episode.get('status') != 'active':
        return False
    dt = parseTs(episode.get('started_at'))
    if not dt:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt) > STALE_AFTER


def autoTitle(predictions, startedAt):
    when = formatDate(startedAt)
    if predictions and predictions[0]['confidence'] > 60:
        return f"Likely {predictions[0]['disease'].strip()} — started {when}"
    return when


def decorateEpisode(episode):
    episode = dict(episode)
    episode['displayDate'] = formatDate(episode.get('started_at'))
    episode['isStale'] = isStale(episode)
    return episode

def runCheckin(episode, newSymptoms, isFirst=False):
    episodeId = episode['id']
    userId = episode['user_id']

    existing = db.getEpisodeSymptoms(episodeId)  # before this check-in is saved
    combined = list(dict.fromkeys(existing + newSymptoms))

    emergency = checkForEmergency(combined)
    
    predictions = predict(combined, topK=3)

    checkin = db.addCheckin(episodeId, newSymptoms, predictions)

    overlap = True
    if not isFirst and existing and newSymptoms:
        overlap = systemsOverlap(existing, newSymptoms)

    title = episode.get('title')
    if isFirst:
        title = autoTitle(predictions, episode.get('started_at'))
        db.updateEpisodeTitle(episodeId, userId, title)

    return {
        'isEmergency': bool(emergency),
        'emergency': emergency or None,
        'predictions': predictions,
        'overlap': overlap,
        'title': title,
        'checkinId': checkin['id'],
    }

@app.context_processor
def injectSidebar():
    active, resolved = [], []
    if session.get('userId'):
        try:
            for episode in db.listEpisodes(session['userId']):
                decorated = decorateEpisode(episode)
                (active if decorated.get('status') == 'active' else resolved).append(decorated)
        except Exception as exc:  # don't let a sidebar query break the page
            print(f'[sidebar] listEpisodes failed: {exc!r}')
    return {
        'sidebarActive': active,
        'sidebarResolved': resolved,
        'currentEmail': session.get('email'),
    }

@app.route('/')
def index():
    return redirect(url_for('episodes')) if session.get('userId') else redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        if not email:
            flash('Please enter your email to continue.')
            return redirect(url_for('login'))
        session['userId'] = devUserId(email)
        session['email'] = email
        return redirect(url_for('episodes'))
    return render_template('login.html')


@app.route('/auth/callback', methods=['POST'])
def authCallback():
    # used when i set up true supabase otp login
    data = request.get_json(silent=True) or request.form
    email = (data.get('email') or '').strip()
    if not email:
        return jsonify({'error': 'email required'}), 400
    session['userId'] = devUserId(email)
    session['email'] = email
    return jsonify({'ok': True, 'redirect': url_for('episodes')})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/episodes')
@loginRequired
def episodes():
    return render_template('episodes.html')


@app.route('/episode/new', methods=['GET', 'POST'])
@loginRequired
def episodeNew():
    if request.method == 'POST':
        symptoms = (request.get_json(silent=True) or {}).get('symptoms', [])
        if not symptoms:
            return jsonify({'error': 'Select at least one symptom.'}), 400
        episode = db.createEpisode(session['userId'])
        result = runCheckin(episode, symptoms, isFirst=True)
        result['episodeId'] = episode['id']
        return jsonify(result)
    prefill = [s for s in (request.args.get('symptoms') or '').split(',') if s]
    return render_template('new_episode.html',
                           symptomGroups=getBodySystemGroups(),
                           prefillSymptoms=prefill)


@app.route('/episode/<episodeId>')
@loginRequired
def episodeView(episodeId):
    episode = db.getEpisode(episodeId, session['userId'])
    if not episode:
        flash('That episode could not be found.')
        return redirect(url_for('episodes'))

    existing = db.getEpisodeSymptoms(episodeId)
    return render_template(
        'episode.html',
        episode=decorateEpisode(episode),
        symptomGroups=getBodySystemGroups(),
        existingSymptoms=existing,
        latestPredictions=db.getLatestPredictions(episodeId),
        emergency=checkForEmergency(existing),
    )


@app.route('/episode/<episodeId>/checkin', methods=['POST'])
@loginRequired
def episodeCheckin(episodeId):
    episode = db.getEpisode(episodeId, session['userId'])
    if not episode:
        return jsonify({'error': 'Episode not found.'}), 404
    symptoms = (request.get_json(silent=True) or {}).get('symptoms', [])
    if not symptoms:
        return jsonify({'error': 'Select at least one new symptom.'}), 400
    return jsonify(runCheckin(episode, symptoms, isFirst=False))


@app.route('/episode/<episodeId>/checkin/<checkinId>', methods=['DELETE'])
@loginRequired
def episodeCheckinDelete(episodeId, checkinId):
    episode = db.getEpisode(episodeId, session['userId'])
    if not episode:
        return jsonify({'error': 'Episode not found.'}), 404
    db.deleteCheckin(checkinId, episodeId)
    return jsonify({'ok': True})


@app.route('/episode/<episodeId>/resolve', methods=['POST'])
@loginRequired
def episodeResolve(episodeId):
    note = (request.get_json(silent=True) or {}).get('note')
    db.resolveEpisode(episodeId, session['userId'], note)
    return jsonify({'ok': True, 'redirect': url_for('episodes')})


@app.route('/predict', methods=['POST'])
def predictRoute():
    data = request.get_json(silent=True)
    if not data or 'symptoms' not in data:
        return jsonify({'error': 'Missing symptoms in request body'}), 400
    symptoms = data['symptoms']
    if not isinstance(symptoms, list) or len(symptoms) == 0:
        return jsonify({'error': 'symptoms must be a non-empty list'}), 400

    emergency = checkForEmergency(symptoms)
    predictions = predict(symptoms, topK=3)
    return jsonify({
        'isEmergency': bool(emergency),
        'emergency': emergency or None,
        'predictions': predictions,
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001)
