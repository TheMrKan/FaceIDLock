import asyncio


async def open_for_seconds(seconds: float):
    print(f"Open lock for {seconds} seconds")
    await asyncio.sleep(seconds)
    print("Close lock")