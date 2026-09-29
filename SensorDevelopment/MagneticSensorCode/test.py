import serial
import time

ser = serial.Serial(
    "/dev/cu.usbserial-0001",
    115200,
    timeout=1
)

print("Connected")

time.sleep(2)

while True:
    raw = ser.readline()
    print(repr(raw))