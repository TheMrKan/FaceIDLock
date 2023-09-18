import cv2


class Display:

    def __init__(self):
        cv2.namedWindow("Display")

    def show_camera_image(self, frame):
        cv2.imshow("Display", frame)
        cv2.waitKey(1)