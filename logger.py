import logging
import os
import datetime
import sys

import cfg

debug = os.name != "posix"

logger = logging.getLogger("test")

if not os.path.exists(cfg.LOGS_PATH):
    os.mkdir(cfg.LOGS_PATH)
filename = os.path.join(cfg.LOGS_PATH, f"{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log")

logger = logging.getLogger("FaceRecognitionMain")
logger.setLevel(logging.DEBUG if debug else logging.INFO)
streamHandler = logging.StreamHandler(sys.stdout)
fileHandler = logging.FileHandler(filename, mode="w")
formatter = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s")
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
logger.debug(f"Logging to the '{filename}'")

