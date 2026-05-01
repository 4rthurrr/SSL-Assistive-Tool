import requests

url = 'http://127.0.0.1:5001/practice_video/Letter_A'
resp = requests.get(url, stream=True, timeout=10)
print('status', resp.status_code)
print('content-type', resp.headers.get('Content-Type'))
print('content-length', resp.headers.get('Content-Length'))
chunk = next(resp.iter_content(chunk_size=64), b'')
print('first-bytes', len(chunk))
print(chunk[:16])
