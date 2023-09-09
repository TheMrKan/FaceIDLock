import os
import glob
import numpy
import datetime
import asyncio
import api
from logger import logger
from typing import Union, Any
import json
import aiofiles
import cv2

debug = os.name != "posix"
if debug:
    from debug import debug_cfg as cfg
else:
    from rpi import rpi_cfg as cfg


class User:
    MAX_OPENINGS_IN_ROW = 3
    ROW_BREAK_SECONDS = 15

    user_id: int
    name: str
    encoding: list[float]
    is_active: bool
    is_local: bool

    pre_lock_counter: int
    last_opening: Union[datetime.datetime, None]

    def __init__(self, user_id: int, name: str, encoding: Union[numpy.ndarray, list[float]], is_active: bool = True, is_local: bool = False):
        self.user_id = user_id
        self.name = name
        self.encoding = list(encoding)
        self.is_active = is_active
        self.is_local = is_local

        self.pre_lock_counter = 0
        self.last_opening = None

    def reset_locking_if_outdated(self):
        if self.last_opening is not None and (datetime.datetime.now() - self.last_opening).seconds > User.ROW_BREAK_SECONDS:
            self.pre_lock_counter = 0

    def track_opening_attempt(self):
        if self.pre_lock_counter + 1 <= User.MAX_OPENINGS_IN_ROW:
            self.pre_lock_counter += 1

        self.last_opening = datetime.datetime.now()

    def track_opening(self, direction: bool):
        """
        :param direction: False - for entering; True - for exiting
        """
        # send notification to the server
        if not self.is_local:
            asyncio.ensure_future(api.send_opening(cfg.OPENING_EVENT_URL, self.user_id, direction))

        logger.info(f"User {self} {'left' if direction else 'entered'}")

    def can_enter(self) -> bool:
        if not self.is_active:
            return False

        self.reset_locking_if_outdated()

        return self.pre_lock_counter < User.MAX_OPENINGS_IN_ROW

    def __str__(self):
        return f"{self.name}({self.user_id}{' LOCAL' if self.is_local else ''})"

    def __repr__(self):
        return self.__str__()


class UserManager:

    SYNC_INTERVAL_SECONDS = 30

    local_path: str
    local_users: list[User]
    remote_address_update: str
    remote_address_init: str
    remote_users: list[User]

    recognizer: Any

    def __init__(self, path: str, remote_address_init: str, remote_address_update: str, recognizer: Any = None):
        self.local_path = path
        self.remote_address_init = remote_address_init
        self.remote_address_update = remote_address_update
        self.logger = logger
        self.recognizer = recognizer

        self.local_users = []
        self.remote_users = []

        if self.local_path and not os.path.isdir(self.local_path):
            raise NotADirectoryError

    async def load_remote_users(self):
        logger.debug(f"Requesting initial database state from the remote server: '{self.remote_address_init}'")
        try:
            remote_users = await api.request_users(self.remote_address_init)
        except api.APIError as ex:
            logger.error(
                f"An API error occured during requesting initial database state.\nStatus code: {ex.response_code}\nResponse text: {ex.reponse_text}",
                exc_info=ex)
            return
        except ConnectionError as ex:
            logger.error(f"A connection error occured during requesting initial database state.", exc_info=ex)
            return
        except Exception as ex:
            logger.critical("An unexpected error occured during requesting initial database state.", exc_info=ex)
            return

        logger.debug(f"Received {len(remote_users)} users from the remote server. Adding...")
        added = 0
        for user in remote_users:
            try:
                await self.add_user(user.user_id, user.name, False, encoding=user.encoding)
                added += 1
            except Exception as ex:
                logger.error(f"Failed to add remote user {user.user_id}", exc_info=ex)
        logger.info(f"Successfully added {added} users from remote server")

    async def load_local_users(self):
        encoded_users_path = os.path.join(self.local_path, "encoded_users.json")
        if os.path.exists(encoded_users_path):
            logger.info(f"Loading encoded local users from '{encoded_users_path}'")
            async with aiofiles.open(encoded_users_path, mode='r', encoding='utf-8') as file:
                encoded_local_users = json.loads(await file.read())
                logger.debug(f"Read {len(encoded_local_users)} users from the file. Loading...")
                for encoded_user in encoded_local_users:
                    try:
                        await self.add_user(encoded_user["id"], encoded_user["name"], True, encoding=encoded_user["encoding"])
                    except Exception as ex:
                        logger.error(f"Failed to load local user. Data: {encoded_user}", exc_info=ex)
        else:
            logger.info(f"Encoded local users weren't found. Path: {encoded_users_path}")

        if self.recognizer is not None:
            logger.debug(f"Searching for new local users in {self.local_path}...")
            old_path = os.getcwd()
            os.chdir(self.local_path)
            new_user_files = glob.glob("*.png") + glob.glob("*.jpg")
            logger.info(f"Found new user images to load: {new_user_files}")
            added = 0
            for path in new_user_files:
                try:
                    name = path[:len(path)-4]    # remove extension
                    user_id = self.find_available_local_id()
                except Exception as ex:
                    logger.error(f"Failed to load user from image file {path} because of wrong name", exc_info=ex)
                    continue

                image = await asyncio.get_event_loop().run_in_executor(None, cv2.imread, path)
                if image is None:
                    logger.error(f"Failed to load image file {path}: file not found or not supported")
                    continue

                try:
                    await self.add_user(user_id, name, True, image=image)
                    os.remove(path)
                    added += 1
                except Exception as ex:
                    logger.error(f"Failed to add user {name} with ID {user_id} from image {path}", exc_info=ex)
                    continue
            os.chdir(old_path)
            logger.info(f"Successfully added {added} local users from files")
        else:
            logger.warning("New local users won't be added because recognizer is not specified")

        async with aiofiles.open(encoded_users_path, mode='w', encoding='utf-8') as f:
            json_str = json.dumps([{"id": u.user_id, "name": u.name, "encoding": u.encoding} for u in self.local_users])
            await f.write(json_str)

    def find_available_local_id(self) -> int:
        reserved_ids = [u.user_id for u in self.local_users]
        result = 0
        while result in reserved_ids:
            result += 1
        return result

    def start_synchronization(self):
        asyncio.create_task(self.synchronization_coroutine())

    async def synchronization_coroutine(self):
        while True:
            await asyncio.sleep(UserManager.SYNC_INTERVAL_SECONDS)

            logger.debug(f"Requesting updates from remote server: '{self.remote_address_update}'")
            try:
                updates = await api.request_updates(self.remote_address_update)
            except api.APIError as ex:
                logger.error(f"An API error occured during requesting remote updates.\nStatus code: {ex.response_code}\nResponse text: {ex.reponse_text}", exc_info=ex)
                continue
            except ConnectionError as ex:
                logger.error(f"A connection error occured during requesting remote updates.", exc_info=ex)
                continue
            except Exception as ex:
                logger.critical("An unexpected error occured during requesting remote updates.", exc_info=ex)
                continue

            logger.debug(f"Received {len(updates)} updates from the remote server. Applying...")
            applied = 0
            for update in updates:
                if update.is_valid:
                    try:
                        await self.apply_remote_update(update)
                        applied += 1
                    except Exception as ex:
                        update.is_valid = False
                        update.error = ex

                if not update.is_valid:
                    logger.error("Skipping invalid remote update", exc_info=update.error)
            logger.debug(f"Successfully applied {applied} valid updates")

    async def apply_remote_update(self, change: api.RemoteChange):
        if True:
            if change.action == "add":
                if change.user_data is None:
                    raise ValueError("User data cannot be None")
                await self.add_user(change.related_user_id, change.user_data.name, encoding=change.user_data.encoding)
            elif change.action == "delete":
                self.remove_user(change.related_user_id, False)
            else:
                raise NotImplementedError(f"Change action {change.action} is not implemented")

    async def add_user(self, user_id: int, name: str, is_local: bool = False, *args, encoding: list[float] = None, image: numpy.ndarray = None):
        users = self.local_users if is_local else self.remote_users
        search = [u for u in users if u.user_id == user_id]
        if search:
            raise KeyError(f"User with the same ID is already exists. Existing user: {search[0].name}; New user: {name}")

        if image is not None:
            if self.recognizer is not None:
                encoding = await asyncio.get_running_loop().run_in_executor(None, self.recognizer.get_face_encoding, image)
            else:
                logger.error("Failed to get encoding from image durring adding a new user: recognizer is not specified")

        if encoding is None:
            raise ValueError("The image and the encoding cannot be None at the same time")

        user = User(user_id, name, encoding, is_local=is_local)
        users.append(user)
        logger.info(f"User {user} was added to the {'local' if is_local else 'remote'} list")

    def remove_user(self, user_id: int, is_local: bool):
        users = self.local_users if is_local else self.remote_users
        search = [(i, u) for i, u in enumerate(users) if u.user_id == user_id]
        if not search:
            raise ValueError(f"User with ID {user_id} doesn't exist")
        del users[search[0][0]]
        logger.info(f"User {search[0][1]} was removed from the {'local' if is_local else 'remote'} list")

    def get_all_active_users(self):
        return [u for u in self.local_users if u.is_active] + [u for u in self.remote_users if u.is_active]
