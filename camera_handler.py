import cv2
import numpy

import face_detection
import asyncio
import os
import users
from logger import logger

debug = os.name != "posix"
debug_captures = (0,)

# environment configuration

if debug:
    logger.debug("Debug is enabled. Importing debug implementations...")
    from debug import debug_lock_controller as lock_controller
    from debug import debug_screen as screen
    from debug import debug_cfg as cfg
else:
    logger.info("Debug is disabled. Importing production implementations...")
    from rpi import rpi_lock_controller as lock_controller
    from rpi import rpi_screen as screen
    from rpi import rpi_cfg as cfg


# setup cameras

class Capture:
    current_frame: [numpy.ndarray, None]
    index: int

    _source: cv2.VideoCapture
    _task: asyncio.Task
    _is_running: bool
    _is_updated: bool

    CAPTURING_INTERVAL = .1

    def __init__(self, index, source):
        self.index = index
        self._source = source
        self.current_frame = None
        self._is_updated = False

    def get_if_updated(self) -> [numpy.ndarray, None]:
        if self._is_updated:
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
                    self.current_frame = frame
                    self._is_updated = True
                else:
                    logger.error(f"Failed to read image from camera {self.index}: ret is False")
            except Exception as ex:
                logger.error(f"Failed to read image from camera {self.index}", exc_info=ex)

            await asyncio.sleep(self.CAPTURING_INTERVAL)

        logger.debug(f"Stopped capturing from camera {self.index}")

    def stop_capturing(self):
        self._is_running = False
        self.source.release()


def get_available_captures() -> list[Capture]:
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            break
        else:
            capture = Capture(index, cap)
            arr.append(capture)
        
        index += 1
    return arr


def get_available_captures_debug() -> list[Capture]:
    arr = []
    for ind in debug_captures:
        cap = cv2.VideoCapture(ind)
        capture = Capture(ind, cap)
        arr.append(capture)
    return arr


captures = get_available_captures_debug() if debug else get_available_captures()
logger.info(f"Found {len(captures)} captures")

# setup recognizer
recognizer = face_detection.Recognizer()

print(f"Path: {cfg.AUTHORIZED_FACES_PATH}")

# setup faces user_manager

path = cfg.AUTHORIZED_FACES_PATH
logger.info(f"Faces directory: {os.path.join(os.getcwd(), path)}")
user_manager = users.UserManager(path, cfg.INIT_URL, cfg.UPDATE_URL, recognizer)

logger.info("Initialization completed")

screen.idle()


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
            face = recognizer.find_face(frame)
            if face is not None:
                logger.info(f"Detected face on camera {capture.index}. Analizing...")
                #screen.recognizing()
                show_denied = True
                try:
                    active_users = user_manager.get_all_active_users()
                    encoding = recognizer.get_face_encoding(frame, (face,))
                    if cfg.SAVE_RECOG_IMAGE:
                        cv2.imwrite(cfg.SAVE_RECOG_IMAGE, frame)
                    matching_index = recognizer.get_matching_encoding_index(encoding, [u.encoding for u in active_users])

                    if matching_index == -1:
                        result = False
                    else:
                        user = active_users[matching_index]
                        logger.debug(f"Detected user: {user}")
                        if user.can_enter():
                            result = True
                        else:
                            logger.debug("Access granted, but lock won't be opened because of row limit")
                            result = False
                            show_denied = False
                        user.track_opening()
                except face_detection.NoFacesDetectedException:
                    result = False
                    logger.error(f"Failed to identify faces from camera {capture.index}")

                if result:
                    logger.info(f"Access granted")
                    screen.granted()
                    await lock_controller.open_for_seconds(3)
                else:
                    logger.info(f"Access denied")
                    if show_denied:
                        screen.denied()
                    await asyncio.sleep(3)
                screen.idle()
                await asyncio.sleep(2)

        await asyncio.sleep(0.2)

    """
    wait = 0
    isWaiting = False
    lastUpdate = time.time()
    wasFoundPreviousFrame = False

    previousCam = 0

    #counter = 0
    while True:
        #print(f"save {counter}")
        #cv2.imwrite(f"test_{counter}.png", capturedFrame)
        #counter += 1

        #while not wasUpdated:
        #await asyncio.sleep(0.1)

        if not wasUpdated:
            await asyncio.sleep(0.1)
            continue

        if not isWaiting:
            previousCam = not previousCam

        if previousCam:
            frame = capturedFrame1
            cv2.imwrite(f"cam1.png", frame)
        else:
            frame = capturedFrame

        detector = face_detection.Detector(frame)
        faces = detector.detect()
        if isWaiting:
            if faces > 0:
                if wasFoundPreviousFrame:
                    cv2.imwrite(f"found_{counter}.png", frame)
                    wasFoundPreviousFrame = False
                wait -= time.time() - lastUpdate
                if wait <= 0:
                    print("Recognize")
                    screen.recognizing()
                    face = detector.get_first_face()
                    cv2.imwrite("example_out.jpg", face)
                    rv, img = cv2.imencode(".png", face)
                    result = api.request_confirmation(img)
                    if result:
                        print("SUCCESS")
                        screen.granted()
                        await lock_controller.open_for_seconds(5)
                        #ret, capturedFrame = cap.read()
                        wait = 5
                    else:
                        print("NOT RECOGNIZED")
                        screen.denied()
                        await asyncio.sleep(3)
                        #ret, capturedFrame = cap.read()
                        wait = 5
                    wasFoundPreviousFrame = True
                    screen.idle()
                    isWaiting = False
                else:
                    wasFoundPreviousFrame = False
                    print(f"Recognizing in {wait:.1f} seconds")
                    screen.waiting(wait)
            else:
                wasFoundPreviousFrame = False
                print("You left the detection zone")
                screen.idle()
                isWaiting = False
                wait = 0

        else:
            if faces > 0:
                print("New face detected. Recognizing in 3 seconds")
                wait = 0
                isWaiting = True

        lastUpdate = time.time()
        wasUpdated = False

        await asyncio.sleep(0.1)
        """


async def main():
    await asyncio.gather(detector_thread(), *[capture.start_capturing() for capture in captures])

asyncio.run(main())


'''while True:
    try:
        ret, frame = cap.read()
        #frame = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        #frame = cv2.imread("example.jpg")
        #cv2.imwrite(f"ex_out_0_{counter}.png", frame)
        #cv2.imwrite(f"ex_out_1_{counter}.png", frame1)
        #time.sleep(0.5)
        #counter += 1
        #if counter > 100:
        #    break
        counter += 1
        detector = face_detection.Detector(frame)
        faces = detector.detect()
        if isWaiting:
            if faces > 0:
                if wasFoundPreviousFrame:
                    cv2.imwrite(f"found_{counter}.png", frame)
                wait -= time.time() - lastUpdate
                if wait <= 0:
                    print("Recognize")
                    screen.recognizing()
                    face = detector.get_first_face()
                    cv2.imwrite("example_out.jpg", face)
                    rv, img = cv2.imencode(".png", face)
                    result = api.request_confirmation(img)
                    if result:
                        print("SUCCESS")
                        screen.granted()
                        lock_controller.open_for_seconds(5)
                        
                        wait = 10
                    else:
                        print("NOT RECOGNIZED")
                        screen.denied()
                        time.sleep(3)
                        wait = 1
                    wasFoundPreviousFrame = True
                    screen.idle()
                    isWaiting = False
                else:
                    wasFoundPreviousFrame = False
                    print(f"Recognizing in {wait:.1f} seconds")
                    screen.waiting(wait)
            else:
                wasFoundPreviousFrame = False
                print("You left the detection zone")
                screen.idle()
                isWaiting = False
                wait = 1

        else:
            if faces > 0:
                print("New face detected. Recognizing in 3 seconds")
                wait = 1
                isWaiting = True

        lastUpdate = time.time()
    except KeyboardInterrupt:
        break
    except:
        traceback.print_exc()
    time.sleep(0.2)
'''

#cap.release()
#cv2.destroyAllWindows()
