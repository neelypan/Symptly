import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

_client = None
_useFallback = False
_store = {'episodes': {}, 'checkins': {}}

try:
    if SUPABASE_URL and SUPABASE_KEY:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            _client.table('episodes').select('id').limit(1).execute()
        except Exception as exc:
            print('[database] Supabase reachable but episodes query failed '
                  f'({exc}) — using in-memory store. Fix table GRANTs/RLS or use '
                  'the service_role key to enable persistence.')
            _useFallback = True
    else:
        print('[database] SUPABASE_URL/SUPABASE_KEY not set — using in-memory store.')
        _useFallback = True
except Exception as exc:  # pragma: no cover - defensive init
    print(f'[database] Supabase init failed ({exc!r}) — using in-memory store.')
    _useFallback = True


def usingFallback():
    return _useFallback


def _nowIso():
    return datetime.now(timezone.utc).isoformat()


def createEpisode(userId, title='New health issue', status='active'):
    startedAt = _nowIso()
    if _useFallback:
        episodeId = str(uuid.uuid4())
        row = {
            'id': episodeId, 'user_id': userId, 'title': title, 'status': status,
            'started_at': startedAt, 'resolved_at': None, 'resolution_note': None,
        }
        _store['episodes'][episodeId] = row
        return dict(row)
    res = _client.table('episodes').insert({
        'user_id': userId, 'title': title, 'status': status, 'started_at': startedAt,
    }).execute()
    return res.data[0]


def listEpisodes(userId):
    if _useFallback:
        rows = [dict(e) for e in _store['episodes'].values() if e['user_id'] == userId]
        return sorted(rows, key=lambda r: r['started_at'], reverse=True)
    res = (_client.table('episodes').select('*')
           .eq('user_id', userId).order('started_at', desc=True).execute())
    return res.data or []


def getEpisode(episodeId, userId):
    if _useFallback:
        row = _store['episodes'].get(episodeId)
        return dict(row) if row and row['user_id'] == userId else None
    res = (_client.table('episodes').select('*')
           .eq('id', episodeId).eq('user_id', userId).limit(1).execute())
    return res.data[0] if res.data else None


def addCheckin(episodeId, symptoms, predictions):
    createdAt = _nowIso()
    if _useFallback:
        checkinId = str(uuid.uuid4())
        row = {
            'id': checkinId, 'episode_id': episodeId, 'symptoms': symptoms,
            'predictions': predictions, 'created_at': createdAt,
        }
        _store['checkins'][checkinId] = row
        return dict(row)
    res = _client.table('checkins').insert({
        'episode_id': episodeId, 'symptoms': symptoms,
        'predictions': predictions, 'created_at': createdAt,
    }).execute()
    return res.data[0]


def deleteCheckin(checkinId, episodeId):
    if _useFallback:
        row = _store['checkins'].get(checkinId)
        if row and row['episode_id'] == episodeId:
            del _store['checkins'][checkinId]
        return
    (_client.table('checkins').delete()
     .eq('id', checkinId).eq('episode_id', episodeId).execute())


def listCheckins(episodeId):
    if _useFallback:
        rows = [dict(c) for c in _store['checkins'].values() if c['episode_id'] == episodeId]
        return sorted(rows, key=lambda r: r['created_at'])
    res = (_client.table('checkins').select('*')
           .eq('episode_id', episodeId).order('created_at', desc=False).execute())
    return res.data or []


def getEpisodeSymptoms(episodeId):
    """Combined, de-duplicated symptom ids across all of an episode's check-ins."""
    seen = []
    for checkin in listCheckins(episodeId):
        for symptom in (checkin.get('symptoms') or []):
            if symptom not in seen:
                seen.append(symptom)
    return seen


def getLatestPredictions(episodeId):
    for checkin in reversed(listCheckins(episodeId)):
        if checkin.get('predictions'):
            return checkin['predictions']
    return []


def updateEpisodeTitle(episodeId, userId, title):
    if _useFallback:
        row = _store['episodes'].get(episodeId)
        if row and row['user_id'] == userId:
            row['title'] = title
        return
    (_client.table('episodes').update({'title': title})
     .eq('id', episodeId).eq('user_id', userId).execute())


def resolveEpisode(episodeId, userId, note=None):
    if _useFallback:
        row = _store['episodes'].get(episodeId)
        if row and row['user_id'] == userId:
            row['status'] = 'resolved'
            row['resolved_at'] = _nowIso()
            row['resolution_note'] = note
        return
    (_client.table('episodes').update({
        'status': 'resolved', 'resolved_at': _nowIso(), 'resolution_note': note,
    }).eq('id', episodeId).eq('user_id', userId).execute())
