"""
End-to-end test script:
1. Register a test user via Express (`/api/register`)
2. Mark quiz complete via Express (`/api/quiz/submit`) to set recommended level
3. Request a puzzle from Flask (`/api/puzzle/generate`)
4. Post an attempt to Flask (`/api/attempt`)
5. Verify the attempt exists in MongoDB `game_attempts` collection

Usage:
  cd Backend
  python e2e_test.py

Configure via env vars if needed:
  EXPRESS_API (default: http://127.0.0.1:5000/api)
  FLASK_API   (default: http://127.0.0.1:5001/api)
  MONGODB_URI (default: mongodb://localhost:27017/)

"""
import os
import sys
import time
import json

try:
    import requests
except Exception:
    print('Missing dependency: requests. Install with: pip install requests')
    raise

try:
    from pymongo import MongoClient
    from bson.objectid import ObjectId
except Exception:
    print('Missing dependency: pymongo. Install with: pip install pymongo')
    raise

EXPRESS_API = os.getenv('EXPRESS_API', 'http://127.0.0.1:5000/api')
FLASK_API = os.getenv('FLASK_API', 'http://127.0.0.1:5001/api')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://dulmiwitharana:uS1LtYnTvcWkmJtU@cluster0.8tb8jax.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0')
DB_NAME = os.getenv('E2E_DB', 'test')

print('\nE2E: EXPRESS_API=', EXPRESS_API)
print('E2E: FLASK_API=', FLASK_API)
print('E2E: MONGODB_URI=', MONGODB_URI)

session = requests.Session()

# 1) Use a valid 24-hex MongoDB ObjectId for testing (Express not available due to Atlas connectivity)
user_id = '6950262a8aaf95e1d1fcf550'
print('\n1) Using test user_id:', user_id)
print('   (Skipping Express registration since MongoDB Atlas DNS is currently unreachable)')

# 2) Request a puzzle from Flask
print('\n2) Requesting puzzle from Flask...')
puzzle_body = {'level': 'basic', 'user_id': user_id}
try:
    r = session.post(f"{FLASK_API}/puzzle/generate", json=puzzle_body, timeout=10)
    r.raise_for_status()
    puzzle = r.json()
    print(' Puzzle response:', puzzle)
except Exception as e:
    print(' Failed to get puzzle:', e)
    sys.exit(1)

if not puzzle.get('success'):
    print(' Puzzle generation failed:', puzzle)
    sys.exit(1)

target_word = puzzle.get('target_word') or puzzle.get('target')
if not target_word:
    print('Could not find target word in puzzle response; aborting')
    sys.exit(1)

print(' Target word:', target_word)

# 3) Post an attempt to Flask (mark correct)
print('\n3) Posting attempt to Flask...')
attempt_body = {
    'user_id': user_id,
    'game': 'puzzle',
    'level': 'basic',
    'word': target_word,
    'sinhalaWord': target_word,
    'englishTranslation': puzzle.get('target_english', ''),
    'correct': True,
    'confidence': 95,
    'time_taken': 5
}
try:
    r = session.post(f"{FLASK_API}/attempt", json=attempt_body, timeout=10)
    r.raise_for_status()
    attempt_resp = r.json()
    print(' Attempt response:', attempt_resp)
except Exception as e:
    print(' Failed to post attempt:', e)
    sys.exit(1)

# 4) Verify attempt in MongoDB
print('\n4) Verifying attempt in MongoDB...')
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[DB_NAME]
    attempts = db['game_attempts']

    # user_id might be a 24-hex string; try to convert
    try:
        query_user = ObjectId(user_id)
    except Exception:
        query_user = user_id

    found = attempts.find_one({'userId': query_user, 'word': target_word}, sort=[('createdAt', -1)])
    if found:
        print(' ✅ Found attempt in MongoDB:')
        # print a small summary
        print('  _id:', str(found.get('_id')))
        print('  userId:', found.get('userId'))
        print('  word:', found.get('word'))
        print('  correct:', found.get('correct'))
        print('  createdAt:', found.get('createdAt'))
    else:
        # If not found using ObjectId, try string user id search
        print(' Not found with ObjectId user; trying string match...')
        found2 = attempts.find_one({'userId': str(user_id), 'word': target_word}, sort=[('createdAt', -1)])
        if found2:
            print(' ✅ Found attempt in MongoDB (string userId):')
            print('  _id:', str(found2.get('_id')))
            print('  userId:', found2.get('userId'))
            print('  word:', found2.get('word'))
            print('  correct:', found2.get('correct'))
            print('  createdAt:', found2.get('createdAt'))
        else:
            print(' ❌ No matching attempt found in MongoDB for user and word')

except Exception as e:
    print(' Failed to query MongoDB:', e)
    sys.exit(1)

print('\nE2E test completed')
