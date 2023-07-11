
from rpi_lcd import LCD

lcd = LCD()

def idle():
	print("Screen: idle")
	lcd.clear()
	lcd.backlight(False)
	lcd.text("Waiting...", 2, "center")

def waiting(time_remaining: float):
	lcd.clear()
	lcd.backlight(True)
	lcd.text("Face detected", 1, "center")
	lcd.text(f"Recognizing in {time_remaining:.1f} seconds", 3, "center")

def recognizing():
	lcd.clear()
	lcd.backlight(True)
	lcd.text("Analizing...", 2, "center")

def granted():
	lcd.clear()
	lcd.backlight(True)
	lcd.text("ACCESS GRANTED", 2, "center")

def denied():
	lcd.clear()
	lcd.backlight(True)
	lcd.text("ACCESS DENIED", 2, "center")

def _test_started():
	lcd.clear()
	lcd.backlight(True)
	lcd.text("TEST STARTED", 1, "center")

def _test_finished():
	lcd.clear()
	lcd.backlight(True)
	lcd.text("TEST FINISHED", 1, "center")

if  __name__ == "__main__":
	import time
	import random

	_test_started()
	time.sleep(1)

	idle()
	time.sleep(3)
	for i in range(50, 0, -5):
		waiting(i / 10)
		time.sleep(0.5)
	recognizing()
	time.sleep(1)

	if random.random() > 0.5:
		granted()
	else:
		denied()
	time.sleep(2)
	idle()

	time.sleep(3)
	_test_finished()


#lcd.text("Hello", 1)
#lcd.text(" World", 1)
#lcd.text("Second line", 2)
#lcd.text("Русские буквы", 3)
#lcd.text("Last line", 4)
#lcd.backlight(False)
