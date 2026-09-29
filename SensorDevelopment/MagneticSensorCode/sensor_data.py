import random
import collections
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import serial
from serial.tools import list_ports

def find_ports():
    for p in list_ports.comports():
        if "CP2102" in p.description:
            return p.device
    return None

SERIAL_PORT = None 
if SERIAL_PORT is None:
    SERIAL_PORT = find_ports()
    print("Using port:", SERIAL_PORT)

if SERIAL_PORT is None:
    raise Exception("Serial Device not found")

BAUD = 115200

ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0)

# 1. Configuration
MAX_POINTS = 50  # Keep only the last 50 data points on screen
UPDATE_INTERVAL = 50  # Update every 200 milliseconds (5Hz)



x_data = collections.deque(maxlen=MAX_POINTS)
y_data = collections.deque(maxlen=MAX_POINTS)


fig, ax = plt.subplots()
line, = ax.plot([], [], label="Sensor Value", color="blue")
ax.set_ylabel("Reading")
ax.set_xlabel("Time (Ticks)")
ax.grid()
ax.legend()


ax.set_xlim(0, MAX_POINTS)
ax.set_ylim(0, 3.3)

counter = 0

def update(frame):
    global counter

    latest_reading = None

    # Read all values currently waiting in the serial buffer
    while ser.in_waiting:
        raw = ser.readline()

        if not raw:
            break

        try:
            latest_reading = float(raw.decode("utf-8").strip())
        except ValueError:
            continue

    # Nothing new received
    if latest_reading is None:
        return line,

    # Add newest value
    x_data.append(counter)
    y_data.append(latest_reading)
    counter += 1

    # Update graph
    line.set_data(x_data, y_data)

    # Shift X-axis
    if counter > MAX_POINTS:
        ax.set_xlim(counter - MAX_POINTS, counter)

    return line,

# 4. Start the animation loop
ani = FuncAnimation(fig, update, interval=UPDATE_INTERVAL, cache_frame_data=False)
plt.show()
