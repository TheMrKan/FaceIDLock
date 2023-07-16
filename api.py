from __future__ import annotations
import requests
import base64
import numpy
import aiohttp
from typing import Any
from dataclasses import dataclass
import json
import asyncio


class APIError(Exception):
    response_code: int
    reponse_text: str
    error_text: str

    def __init__(self, error_text: str, response_code: int, response_text: str):
        super().__init__()
        self.error_text = error_text
        self.response_code = response_code
        self.reponse_text = response_text

    @classmethod
    async def from_response(cls, text: str, response: aiohttp.ClientResponse) -> APIError:
        return cls(text, response.status, await response.text("utf-8"))


@dataclass
class RemoteUserData:
    user_id: int
    name: str
    encoding: list[float]


class RemoteChange:
    action = ""
    related_user_id = 0
    user_data: RemoteUserData | None

    is_valid = True
    error = None

    def __init__(self, data: dict[str, Any]):
        try:
            self.action = data["action"]
            self.related_user_id = data["user_id"]
            if self.action == "add":
                self.user_data = RemoteUserData(data["user_id"], data["fio"], data["encoding"])
        except Exception as ex:
            self.is_valid = False
            self.parsing_error = ex



async def request_users(url: str) -> list[RemoteUserData]:
    async with aiohttp.ClientSession() as aio_session:
        async with aio_session.get(url) as response:
            if response.status != 200:
                raise await APIError.from_response("Failed status code", response)
            data = dict(await response.json())
            result = data.get("result", None)
            if result is None:
                raise await APIError.from_response("Invalid response", response)

            result = []
            clients = json.loads(data.get("clients", "[]"))
            for client in clients:
                try:
                    remote_user = RemoteUserData(client["id"], client["fio"], client["encoding"])
                    result.append(remote_user)
                except KeyError:
                    continue

            return result


async def request_updates(url: str) -> list[RemoteChange]:
    async with aiohttp.ClientSession() as aio_session:
        async with aio_session.get(url) as response:
            if response.status != 200:
                raise await APIError.from_response("Failed status code", response)
            
            data = await response.json()
            #with open("response.txt","r") as f:
                #data = json.loads(f.read())

            result = data.get("result", None)
            if result is None:
                raise await APIError.from_response("Invalid response", response)
            elif result == "error, no users found":
                return []
            #with open("response.txt","w") as f:
               #f.write(await response.text())
            raw_changes = data.get("clients", None)
            if raw_changes is None:
                return []
            return [RemoteChange(raw) for raw in json.loads(raw_changes)]


async def debug_main():
    await request_updates("http://127.0.0.1:8000")

if __name__ == "__main__":
    asyncio.run(debug_main())
