import face_recognition as recog
import cv2
import numpy
from debug import debug_cfg
import os

import users


class NoFacesDetectedException(Exception):
    pass

debug = os.name != "posix"
if debug:
    from debug import debug_cfg as cfg
else:
    from rpi import rpi_cfg as cfg


class Recognizer:

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    def get_face_encoding(self, image: numpy.ndarray, bounds: list = None):
        if debug_cfg.SAVE_RECOG_IMAGE:
            img = cv2.rectangle(image, (bounds[0][3], bounds[0][0]), (bounds[0][1], bounds[0][2]), (0, 255, 0), 2)
            cv2.imwrite(debug_cfg.SAVE_RECOG_IMAGE, img)
        print(image.shape)
        encodings = recog.face_encodings(image, known_face_locations=bounds)
        if not encodings:
            raise NoFacesDetectedException
        return encodings[0]

    def get_face_encoding_from_file(self, file_path: str):
        image = cv2.imread(file_path)
        return self.get_face_encoding(image)

    def find_face(self, image: numpy.ndarray):

        faces = self.face_cascade.detectMultiScale(
                image,
                scaleFactor=1.4,
                minNeighbors=3,
                minSize=(80, 80)
        )
        if len(faces) == 0:
            return None

        x, y, w, h = faces[0]
        x0, x1 = int(max(0, x - 20)), int(min(image.shape[1], x + w + 20))
        y0, y1 = int(max(0, y - 20)), int(min(image.shape[0], y + h + 20))
        face = (y0, x1, y1, x0)
        return face

    def get_matching_encoding_index(self, target_encoding: list, encodings: list):
        try:
            return recog.compare_faces(encodings, target_encoding, tolerance=0.5).index(True)
        except ValueError:
            return -1



