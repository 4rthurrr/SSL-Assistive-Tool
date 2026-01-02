import json
import urllib.request

url = "http://127.0.0.1:5001/api/attempt"
body = {
    "user_id": "6950262a8aaf95e1d1fcf550",
    "word": "happy",
    "level": "basic",
    "correct": False,
    "time_taken": 12
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(resp.read().decode('utf-8'))
except Exception as e:
    print('ERROR:', e)
