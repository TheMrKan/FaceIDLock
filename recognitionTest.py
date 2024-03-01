import cv2
import api
import asyncio
import time
import json
import users
import face_detection

AUTHORIZED_FACES_PATH = "faces"
INIT_URL = "https://fitnessneo.ru/get-faceid-users/"
UPDATE_URL = "https://fitnessneo.ru/get-new-faceid-users/"
OPENING_EVENT_URL = "https://fitnessneo.ru/add-event/"

my_face = cv2.imread("test.png")

recognizer = face_detection.Recognizer()

user_manager = users.UserManager(AUTHORIZED_FACES_PATH, INIT_URL, UPDATE_URL, recognizer)


async def main():
    await user_manager.load_local_users()
    await user_manager.load_remote_users()

    encoding = recognizer.get_face_encoding(my_face)

    all_users = [u.encoding for u in user_manager.local_users + user_manager.remote_users]
    print(all_users)
    index_both = recognizer.get_matching_encoding_index(encoding, all_users[:40])

    print(index_both)


asyncio.run(main())
