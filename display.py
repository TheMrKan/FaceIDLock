import cv2
import subprocess
import os
import tkinter
import numpy as np
import math

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

        self.timer = 0

        self.tk = tkinter.Tk()

    def draw_dashed_line(self, frame, p0, p1, thickness, color, dashes, dash_length):

        x0, y0 = p0
        x1, y1 = p1

        if y0 == y1:
            length = x1 - x0
            gap = (length - (dashes * dash_length)) / (dashes - 1)

            for i in range(dashes):
                _x0 = x0 + int(i * (dash_length + gap))
                _x1 = _x0 + dash_length
                cv2.rectangle(frame, (_x0, y0 - thickness // 2), (_x1, y0 + thickness // 2), color=color, thickness=-1)

        if x0 == x1:
            length = y1 - y0
            gap = (length - (dashes * dash_length)) / (dashes - 1)

            for i in range(dashes):
                _y0 = y0 + int(i * (dash_length + gap))
                _y1 = _y0 + dash_length
                cv2.rectangle(frame, (x0 - thickness // 2, _y0), (x1 + thickness // 2, _y1), color=color, thickness=-1)

    def draw_dashed_rect(self, frame, center, size, thickness, color, filling=1):
        # 0 <= filling <= 100
        filling = min(100, max(0, filling))

        # длина дэша, при которой gap равен 0
        max_length = math.ceil(size / cfg.RECT_LINES)

        # левый верхний угол квадрата
        x0, y0 = int(center[0] - size / 2), int(center[1] - size / 2)

        dash_length = int(cfg.RECT_LINE_MIN + max(filling, 0) * (max_length - cfg.RECT_LINE_MIN) * filling)
        print(dash_length)

        self.draw_dashed_line(frame, (x0, y0), (x0 + size, y0), thickness, color, cfg.RECT_LINES, dash_length)
        self.draw_dashed_line(frame, (x0, y0 + size), (x0 + size, y0 + size), thickness, color, cfg.RECT_LINES, dash_length)

        self.draw_dashed_line(frame, (x0, y0), (x0, y0 + size), thickness, color, cfg.RECT_LINES, dash_length)
        self.draw_dashed_line(frame, (x0 + size, y0), (x0 + size, y0 + size), thickness, color, cfg.RECT_LINES, dash_length)

        return frame

    def draw_ui(self, frame):
        h, w = frame.shape[:2]

        rect_size = int(min(w, h) * cfg.DETECTION_ZONE_SIZE)

        self.draw_dashed_rect(frame, (int(w / 2), int(h / 2)), rect_size, 2, (255, 255, 255), 0)

    def show_camera_image(self, frame):

        h, w = frame.shape[:2]

        t_ratio = cfg.DISPLAY_WIDTH / cfg.DISPLAY_HEIGHT

        nw, nh = w, h

        if t_ratio < w / h:
            nw = h * t_ratio
        else:
            nh = w / t_ratio

        frame = cv2.flip(frame[int(h / 2 - nh / 2):int(h / 2 + nh / 2), int(w / 2 - nw / 2):int(w / 2 + nw / 2)], 1)

        self.draw_ui(frame)

        cv2.imshow("Display", frame)

        if cv2.waitKey(1) == ord('q'):
            exit()
