
import face_recognition
import cv2
import api
import asyncio
import time
import json

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cv2.imwrite("test.png", frame)

'''with open("faces/encoded_users.json", "r") as f:
    data = json.loads(f.read())

local_users = [api.RemoteUserData(u["id"], u["name"], u["encoding"]) for u in data]

remote_users = asyncio.get_event_loop().run_until_complete(api.request_users(cfg.INIT_URL))
print([u.name for u in remote_users])'''

img = face_recognition.load_image_file("img.png")
print(img.shape)
enc = face_recognition.face_encodings(frame, model="large")
print(enc)
'''known_encodings_remote = [u.encoding for u in remote_users]
known_encodings_local = [u.encoding for u in local_users]
print(known_encodings_local)'''

'''distances_remote = face_recognition.face_distance(known_encodings_remote, enc)
distances_local = face_recognition.face_distance(known_encodings_local, enc)
[print(f"{remote_users[i].name}: {d}\n") for i, d in enumerate(distances_remote)]
print("\n\n\nLOCAL:\n\n\n")
[print(f"{local_users[i].name}: {d}\n") for i, d in enumerate(distances_local)]

'''