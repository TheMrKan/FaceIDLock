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

    DEFAULT_RECT_COLOR = (255, 255, 255)
    GRANTED_RECT_COLOR = (0, 255, 0)
    DENIED_RECT_COLOR = (0, 0, 255)

    def __init__(self):
        cv2.namedWindow("Display", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Display", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.moveWindow("Display", 0, 0)

        self.rect_color = self.DEFAULT_RECT_COLOR
        self.filling = 1
        self.current_frame = None

        self.tk = tkinter.Tk()

    def show_granted(self, refresh: bool = True):
        self.filling = 1
        self.rect_color = self.GRANTED_RECT_COLOR

        if refresh and self.current_frame is not None:
            self._refresh_ui()

    def show_idle(self, progress: float = 0):
        self.filling = progress
        self.rect_color = self.DEFAULT_RECT_COLOR

    def show_denied(self, refresh: bool = True):
        self.filling = 1
        self.rect_color = self.DENIED_RECT_COLOR

        if refresh and self.current_frame is not None:
            self._refresh_ui()

    @staticmethod
    def overlay_image_alpha(img, img_overlay, x, y, alpha_mask):
        """Overlay `img_overlay` onto `img` at (x, y) and blend using `alpha_mask`.

        `alpha_mask` must have same HxW as `img_overlay` and values in range [0, 1].
        """
        # Image ranges
        y1, y2 = max(0, y), min(img.shape[0], y + img_overlay.shape[0])
        x1, x2 = max(0, x), min(img.shape[1], x + img_overlay.shape[1])

        # Overlay ranges
        y1o, y2o = max(0, -y), min(img_overlay.shape[0], img.shape[0] - y)
        x1o, x2o = max(0, -x), min(img_overlay.shape[1], img.shape[1] - x)

        # Exit if nothing to do
        if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
            return

        # Blend overlay within the determined ranges
        img_crop = img[y1:y2, x1:x2]
        img_overlay_crop = img_overlay[y1o:y2o, x1o:x2o]
        alpha = alpha_mask[y1o:y2o, x1o:x2o, np.newaxis]
        alpha_inv = 1.0 - alpha

        img_crop[:] = alpha * img_overlay_crop + alpha_inv * img_crop

    def _draw_dashed_line(self, frame, p0, p1, thickness, color, dashes, dash_length):

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

    def _draw_dashed_rect(self, frame, center, size, thickness, color, filling=0):
        # 0 <= filling <= 100
        filling = min(1, max(0, filling))

        # длина дэша, при которой gap равен 0
        max_length = math.ceil(size / cfg.RECT_LINES)

        # левый верхний угол квадрата
        x0, y0 = int(center[0] - size / 2), int(center[1] - size / 2)

        dash_length = int(cfg.RECT_LINE_MIN + max(filling, 0) * (max_length - cfg.RECT_LINE_MIN) * filling)
        #print(dash_length)

        self._draw_dashed_line(frame, (x0, y0), (x0 + size, y0), thickness, color, cfg.RECT_LINES, dash_length)
        self._draw_dashed_line(frame, (x0, y0 + size), (x0 + size, y0 + size), thickness, color, cfg.RECT_LINES, dash_length)

        self._draw_dashed_line(frame, (x0, y0), (x0, y0 + size), thickness, color, cfg.RECT_LINES, dash_length)
        self._draw_dashed_line(frame, (x0 + size, y0), (x0 + size, y0 + size), thickness, color, cfg.RECT_LINES, dash_length)

        return frame

    def _draw_ui(self, frame):
        h, w = frame.shape[:2]

        rect_size = int(min(w, h) * cfg.DETECTION_ZONE_SIZE)
        self._draw_dashed_rect(frame, (int(w / 2), int(h / 2)), rect_size, 2, self.rect_color, self.filling)

    def _refresh_ui(self):
        if self.current_frame is None:
            return

        frame = self.current_frame.copy()

        self._draw_ui(frame)
        cv2.imshow("Display", frame)

    def show_camera_image(self, frame):

        frame = frame.copy()
        h, w = frame.shape[:2]

        t_ratio = cfg.DISPLAY_WIDTH / cfg.DISPLAY_HEIGHT

        nw, nh = w, h

        if t_ratio < w / h:
            nw = h * t_ratio
        else:
            nh = w / t_ratio

        frame = frame[int(h / 2 - nh / 2):int(h / 2 + nh / 2), int(w / 2 - nw / 2):int(w / 2 + nw / 2)]

        frame = cv2.resize(frame, (cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT))

        self.current_frame = frame.copy()

        self._draw_ui(frame)

        cv2.imshow("Display", frame)

        if cv2.waitKey(1) == ord('q'):
            exit()
