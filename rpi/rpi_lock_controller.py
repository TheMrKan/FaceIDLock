
import RPi.GPIO as GPIO
import time
import asyncio

OUTPUT_PIN = 16
CAMERA_PIN = 12

GPIO.setmode(GPIO.BOARD)
GPIO.setup(OUTPUT_PIN, GPIO.OUT, initial=GPIO.LOW)
#GPIO.output(OUTPUT_PIN, GPIO.LOW)
GPIO.setup(CAMERA_PIN, GPIO.OUT, initial=GPIO.HIGH)

async def open_for_seconds(seconds: int):
	GPIO.output(OUTPUT_PIN, GPIO.HIGH)
	print("OPEN LOCK")
	await asyncio.sleep(seconds)
	print("CLOSE LOCK")
	GPIO.output(OUTPUT_PIN, GPIO.LOW)


if __name__ == "__main__":
	print("Opening in 5 seconds")
	time.sleep(5)
	print("Opened")
	#with Lock() as lock:
		#lock.open_for_seconds(10)
	asyncio.run(open_for_seconds(5))
	GPIO.cleanup(OUTPUT_PIN)
	print("Closed")

