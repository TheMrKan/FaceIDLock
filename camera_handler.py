import cv2
import numpy

import face_detection
import asyncio
import os
import users
from logger import logger
import datetime
import time
import display

debug = os.name != "posix"
debug_captures = (0,)

# environment configuration

if debug:
    logger.debug("Debug is enabled. Importing debug implementations...")
    from debug import debug_lock_controller as lock_controller
    from debug import debug_cfg as cfg
else:
    logger.info("Debug is disabled. Importing production implementations...")
    from rpi import rpi_lock_controller as lock_controller
    from rpi import rpi_cfg as cfg


# setup cameras

class Capture:
    current_frame: [numpy.ndarray, None]
    index: int
    direction: bool    # False - for entering; True - for exiting
    delay: float
    flip_y: bool
    flip_x: bool

    _source: cv2.VideoCapture
    _task: asyncio.Task
    _is_running: bool
    _is_updated: bool
    _delay_started: datetime.datetime

    CAPTURING_INTERVAL = .01

    def __init__(self, index, source):
        self.index = index
        self._source = source
        self.current_frame = None
        self._is_updated = False
        self.display_released = False

        source.set(cv2.CAP_PROP_CONVERT_RGB, 1)

        self.direction = self._source.get(cv2.CAP_PROP_BACKLIGHT) == -1
        if self.index < len(cfg.DELAYS):
            self.delay = cfg.DELAYS[self.direction]
        else:
            self.delay = 0
        self._delay_started = None

        self.flip_y = self.direction in cfg.FLIP_Y
        self.flip_x = self.direction in cfg.FLIP_X

    def get_if_updated(self, reset_status: bool = True) -> [numpy.ndarray, None]:
        if self._is_updated:
            if reset_status:
                self._is_updated = False
            return self.current_frame
        return None

    def start_capturing(self) -> asyncio.Task:
        self._is_running = True
        self._task = asyncio.create_task(self.capturing_coroutine())

        return self._task

    async def capturing_coroutine(self):
        logger.debug(f"Started capturing from camera {self.index}")

        while self._is_running:
            try:
                ret, frame = await asyncio.get_event_loop().run_in_executor(None, self._source.read)
                if ret:
                    if self.flip_y:
                        frame = cv2.flip(frame, 0)
                    if self.flip_x:
                        frame = cv2.flip(frame, 1)

                    self.current_frame = frame

                    if not self.direction:

                        if not self.display_released:
                            if self.is_waiting:
                                display.show_idle((datetime.datetime.now() - self._delay_started).total_seconds() / self.delay)
                            else:
                                display.show_idle(0)

                        display.show_camera_image(frame)

                    self._is_updated = True
                else:
                    logger.error(f"Failed to read image from camera {self.index}: ret is False")
            except Exception as ex:
                logger.error(f"Failed to read image from camera {self.index}", exc_info=ex)

            await asyncio.sleep(self.CAPTURING_INTERVAL)

        logger.debug(f"Stopped capturing from camera {self.index}")

    def stop_capturing(self):
        self._is_running = False
        self._source.release()

    def start_waiting(self):
        if self.delay > 0:
            self._delay_started = datetime.datetime.now()

    def stop_waiting(self):
        self._delay_started = None

    @property
    def is_waiting(self) -> bool:
        return self._delay_started is not None

    @property
    def is_delay_elapsed(self) -> bool:
        if self.delay == 0 or self._delay_started is None:
            return True

        return (datetime.datetime.now() - self._delay_started).total_seconds() >= self.delay


def get_available_captures() -> list:
    index = 0
    arr = []
    streak = 0
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            streak += 1
            if streak > 5:
                break
        else:
            capture = Capture(index, cap)
            arr.append(capture)
        
        index += 1
    return arr


def get_available_captures_debug() -> list:
    arr = []
    for ind in debug_captures:
        cap = cv2.VideoCapture(ind)
        capture = Capture(ind, cap)
        arr.append(capture)
    return arr


captures = get_available_captures_debug() if debug else get_available_captures()
logger.info(f"Found {len(captures)} captures")

# setup display
display = display.Display()

# setup recognizer
recognizer = face_detection.Recognizer()

print(f"Path: {cfg.AUTHORIZED_FACES_PATH}")

# setup faces user_manager

path = cfg.AUTHORIZED_FACES_PATH
logger.info(f"Faces directory: {os.path.join(os.getcwd(), path)}")
user_manager = users.UserManager(path, cfg.INIT_URL, cfg.UPDATE_URL, recognizer)

logger.info("Initialization completed")

async def init_user_manager_remotes():
    await asyncio.create_task(user_manager.load_remote_users())
    user_manager.start_synchronization()


async def detector_thread():

    global captures
    global user_manager
    global recognizer

    asyncio.create_task(user_manager.load_local_users())
    asyncio.create_task(init_user_manager_remotes())

    if not captures:
        logger.critical("No available cameras found. Exiting...")
        exit()

    while True:

        for capture in captures:

            frame = capture.get_if_updated()
            if frame is None:
                continue

            lims = (0, cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT, 0)
            if not capture.direction:
                cx, cy = int(frame.shape[1] / 2), int(frame.shape[0] / 2)
                half_rect_size = int(min(frame.shape[0], frame.shape[1]) * cfg.DETECTION_ZONE_SIZE / 2)
                lims = (cy - half_rect_size, cx + half_rect_size, cy + half_rect_size, cx - half_rect_size)

                #frame = frame.copy()[100:480, 100:800]

            #p1 = time.time()
            face = recognizer.find_face(frame)
            #print("First time:", time.time()- p1)
            if face is None or face[0] < lims[0] or face[1] > lims[1] or face[2] > lims[2] or face[3] < lims[3]:
                if capture.is_waiting:
                    capture.stop_waiting()
            else:
                #screen.recognizing()
                if capture.delay > 0:
                    if capture.is_waiting:
                        if capture.is_delay_elapsed:
                            capture.stop_waiting()
                        else:
                            continue
                    else:
                        capture.start_waiting()
                        continue

                logger.info(f"Detected face on camera {capture.index}. Analizing...")

                show_denied = True
                try:
                    active_users = user_manager.get_all_active_users()
                    #p2 = time.time()
                    encoding = recognizer.get_face_encoding(frame, (face, ))
                    #print("Second time:", time.time()- p2)
                    matching_index = recognizer.get_matching_encoding_index(encoding, [u.encoding for u in active_users])

                    if matching_index == -1:
                        result = False
                    else:
                        user = active_users[matching_index]
                        logger.debug(f"Detected user: {user}")
                        if user.can_enter():
                            result = True
                            user.track_opening(capture.direction)
                            if cfg.SAVE_USER_IMAGE:
                                p = os.path.join(cfg.SAVE_USER_IMAGE,
                                                 f"{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_{user}.png")
                                img = cv2.rectangle(frame, (face[3], face[0]), (face[1], face[2]), (0, 255, 0), 2)
                                cv2.imwrite(p, img)
                        else:
                            logger.debug("Access granted, but lock won't be opened because of row limit")
                            result = False
                            show_denied = False
                        user.track_opening_attempt()
                except Exception as ex:
                    result = False
                    logger.error(f"Failed to identify faces from camera {capture.index}", exc_info=ex)

                if result:
                    logger.info(f"Access granted")
                    capture.display_released = True
                    display.show_granted()
                    await lock_controller.open_for_seconds(3)
                    display.show_idle()
                    capture.display_released = False
                else:
                    logger.info(f"Access denied")
                    if show_denied:
                        capture.display_released = True
                        display.show_denied()
                        await asyncio.sleep(1)
                        display.show_idle()
                        capture.display_released = False

                capture.stop_waiting()

        await asyncio.sleep(0.05)


async def main():
    await asyncio.gather(detector_thread(), *[capture.start_capturing() for capture in captures])



asyncio.run(main())
