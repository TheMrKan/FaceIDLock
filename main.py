import multiprocessing
import logging
import os
import types
import configparser
import datetime


class Core:

    debug: bool
    config: configparser.ConfigParser
    app_path: str

    def __init__(self):
        self.debug = os.name != "posix"
        self.config = self.load_config()

    def load_config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read("debug/debug.ini" if self.debug else "rpi/rpi.ini")
        return config

    def configure_logger(self) -> logging.Logger:
        logger = logging.getLogger("App")

        if not os.path.exists(self.config.LOG_PATH):
            os.mkdir(self.config.LOGS_PATH)
        filename = os.path.join(self.config["Paths"]["logs"], f"{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log")

        logger = logging.getLogger("FaceRecognitionMain")
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        streamHandler = logging.StreamHandler(sys.stdout)
        fileHandler = logging.FileHandler(filename, mode="w")
        formatter = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s")
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)
        logger.debug(f"Logging to the '{filename}'")

    def run(self):
        pass


if __name__ == "__main__":
    core = Core()
    core.run()
