import RPi.GPIO as GPIO
import time
import asyncio

OUTPUT_PIN = 8

GPIO.setmode(GPIO.BOARD)
GPIO.setup(OUTPUT_PIN, GPIO.OUT, initial=GPIO.LOW)


async def open_for_seconds(seconds: int):
	GPIO.output(OUTPUT_PIN, GPIO.HIGH)
	await asyncio.sleep(seconds)
	GPIO.output(OUTPUT_PIN, GPIO.LOW)


if __name__ == "__main__":
	print("Opening in 5 seconds")
	time.sleep(10)
	print("Opened")
	#with Lock() as lock:
		#lock.open_for_seconds(10)
	open_for_seconds(10)
	GPIO.cleanup(OUTPUT_PIN)
	print("Closed")
