import cv2
import subprocess
import os
import tkinter

debug = os.name != "posix"
if debug:
    from debug import debug_cfg as cfg
else:
    from rpi import rpi_cfg as cfg


class Display:

    def __init__(self):
        cv2.namedWindow("Display", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Display", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.moveWindow("Display", 0, 0)

        self.tk = tkinter.Tk()

    def show_camera_image(self, frame):
        resized = cv2.resize(frame, (cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT))
        cv2.imshow("Display", resized)

        if cv2.waitKey(1) == ord('q'):
            exit()
