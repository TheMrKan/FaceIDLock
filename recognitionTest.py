'''
import face_recognition
import api
import asyncio
import time
import json

with open("faces/encoded_users.json", "r") as f:
    data = json.loads(f.read())

local_users = [api.RemoteUserData(u["id"], u["name"], u["encoding"]) for u in data]

remote_users = asyncio.get_event_loop().run_until_complete(api.request_users(cfg.INIT_URL))
print([u.name for u in remote_users])

img = face_recognition.load_image_file("test.png")

enc = face_recognition.face_encodings(img, model="large")[0]
known_encodings_remote = [u.encoding for u in remote_users]
known_encodings_local = [u.encoding for u in local_users]
print(known_encodings_local)

distances_remote = face_recognition.face_distance(known_encodings_remote, enc)
distances_local = face_recognition.face_distance(known_encodings_local, enc)
[print(f"{remote_users[i].name}: {d}\n") for i, d in enumerate(distances_remote)]
print("\n\n\nLOCAL:\n\n\n")
[print(f"{local_users[i].name}: {d}\n") for i, d in enumerate(distances_local)]
'''

import cv2
img = cv2.imread("recog.png")

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
faces = face_cascade.detectMultiScale(
                img,
                scaleFactor=1.4,
                minNeighbors=3,
                minSize=(80, 80)
        )

print(faces)

