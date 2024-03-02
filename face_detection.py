import traceback

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
        encodings = recog.face_encodings(image, known_face_locations=bounds)

        #cv2.imwrite("recog_img.png", image)

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
        x0, x1 = int(x), int(x + w)
        y0, y1 = int(y), int(y + h)
        face = (y0, x1, y1, x0)
        return face

    def get_matching_encoding_index(self, target_encoding: list, encodings: list):
        try:
            return recog.compare_faces(encodings, target_encoding, tolerance=0.5).index(True)
        except ValueError as ex:
            return -1



