import requests
import cv2
import numpy as np

url = 'http://127.0.0.1:5001/video_feed'
r = requests.get(url, stream=True, timeout=10)
buf = b''
frame = None

for chunk in r.iter_content(chunk_size=4096):
    if not chunk:
        continue
    buf += chunk
    a = buf.find(b'\xff\xd8')
    z = buf.find(b'\xff\xd9')
    if a != -1 and z != -1 and z > a:
        jpg = buf[a:z+2]
        buf = buf[z+2:]
        arr = np.frombuffer(jpg, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is not None:
            break

if frame is None:
    print('NO_FRAME')
else:
    print('SHAPE', frame.shape)
    print('MEAN', float(frame.mean()))
    print('STD', float(frame.std()))
