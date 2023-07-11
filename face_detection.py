import face_recognition as recog
import cv2
import numpy

import users


class NoFacesDetectedException(Exception):
    pass


class Recognizer:

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def get_face_encoding(self, image: numpy.ndarray, bounds: tuple[int, int, int, int] = None) -> list[float]:
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

    def get_matching_encoding_index(self, target_encoding: list[float], encodings: list[list[float]]):
        try:
            return recog.compare_faces(encodings, target_encoding, tolerance=0.5).index(True)
        except ValueError:
            return -1


class Detector:

    faces = []
    image = None

    def __init__(self, image):
        self.image = self.gray = image
        #self.gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def detect(self) -> int:

        self.faces = faceCascade.detectMultiScale(
                self.gray,
                scaleFactor=1.4,
                minNeighbors=3,
                minSize=(30, 30)
        )

        return len(self.faces)

    def get_first_face(self):
        if len(self.faces) == 0:
            raise NoFacesDetectedException

        x, y, w, h = self.faces[0]
        x0, x1 = max(0, x - 80), min(self.image.shape[1], x + w + 80)
        y0, y1 = max(0, y - 80), min(self.image.shape[0], y + h + 80)
        face = self.image[y0:y1, x0:x1]
        return face

    def identify_face(self, repository: users.UserManager) -> bool:
        try:
            target_face_encoding = recog.face_encodings(self.image)[0]
        except IndexError:
            raise NoFacesDetectedException

        print("Identifying face...")

        results = recog.compare_faces(repository.get_faces(), target_face_encoding)
        print(f"Identifying result: {any(results)}")
        return any(results)


