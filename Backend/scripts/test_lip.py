import requests
import time

BASE='http://127.0.0.1:5001'
print('POST /start_training')
r=requests.post(BASE+'/start_training', json={'letter':'Letter A'})
print(r.status_code, r.text)
print('GET /status')
r=requests.get(BASE+'/status')
print(r.status_code, r.json())
print('POST /student_turn')
r=requests.post(BASE+'/student_turn')
print(r.status_code, r.text)
print('GET /status')
for i in range(6):
    r=requests.get(BASE+'/status')
    print(i, r.json())
    time.sleep(1)
print('POST /stop_training')
r=requests.post(BASE+'/stop_training')
print(r.status_code, r.text)
