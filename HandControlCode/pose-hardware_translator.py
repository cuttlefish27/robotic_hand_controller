import serial
import socket
import threading
import queue
import numpy as np
from serial.tools import list_ports
import math
import time


last_send = 0
SENDPERIOD = 0.02
filter = None

work_available = threading.Semaphore(0)

def pointercalculateA(theta):
    theta1 = -theta[0]
    theta2 = -theta[1]

    


    x1 = 0.5
    y1 = 0.9
    z1 = 0.70

    A_1 = np.array([[x1 * np.cos(theta2) + z1 * np.sin(theta2)],
                    [x1 * np.sin(theta1) * np.sin(theta2) + y1 * np.cos(theta1) - z1 * np.sin(theta1)*np.cos(theta2) - 0.55 * np.sin(theta1)],
                    [-x1 * np.cos(theta1) * np.sin(theta2) + y1 * np.sin(theta1) + z1 * np.cos(theta1)*np.cos(theta2) + 0.55 * np.cos(theta1)],
                    [1]
                    ])
    A_2 = np.array([[x1 * np.cos(theta2) + z1 * np.sin(theta2)],
                    [x1 * np.sin(theta1) * np.sin(theta2) - y1 * np.cos(theta1) - z1 * np.sin(theta1)*np.cos(theta2) - 0.55 * np.sin(theta1)],
                    [-x1 * np.cos(theta1) * np.sin(theta2) - y1 * np.sin(theta1) + z1 * np.cos(theta1)*np.cos(theta2) + 0.55 * np.cos(theta1)],
                    [1]
                    ])
    
    #print("A1 = ", A_1)
    #print("A2 = ", A_2)

    return A_1, A_2


def pointercalculateL(theta):

    gx1 = 0.7
    gx2 = 0.7
    gy1 = 0.91
    gy2 = -0.91
    gz1 = -0.6
    gz2 = -0.6

    G_1 = np.array([[gx1], [gy1], [gz1], [1]])
    G_2 = np.array([[gx2], [gy2], [gz2], [1]])

    A_1, A_2 = pointercalculateA(theta)

    

    L1 = np.linalg.norm(G_1 - A_1)
    L2 = np.linalg.norm(G_2 - A_2)

    
    return L1, L2

def thumbcalculateL(thumbCurl):
    theta3 = thumbCurl[0] + math.radians(10)
    theta4 = thumbCurl[1]

    P3 = np.array([[0],
                   [0.828],
                   [0.73],
                   [1]
                   ])

    P4 = np.array([[0],
                   [0.862],
                   [0.734],
                   [1]
                   ])
    
    G3 = np.array([[2.563-1.82],
                   [3.63],
                   [1.75+0.5],
                   [1]
                   ])
    
    G4 = np.array([[0],
                   [2.607],
                   [0.555],
                   [1]
                   ])
    


    T3 = np.array([[1,0,0,0],
                   [0, math.cos(theta3), -math.sin(theta3), 5.54],
                   [0, math.sin(theta3), math.cos(theta3), 0],
                   [0,0,0,1]
                   ])

    T4 = np.array([[1,0,0,0],
                   [0, math.cos(theta4), -math.sin(theta4), 3.305],
                   [0, math.sin(theta4), math.cos(theta4), 0],
                   [0,0,0,1]
                   ])


    A3 = T3 @ P3
    A4 = T4 @ P4

    L3 = np.linalg.norm(G3-A3)
    L4 = np.linalg.norm(G4-A4)

    return L3, L4


def CMD(theta, curl, thumbRot, thumbPinch, thumbCurl):
    global filter

    L1, L2 = pointercalculateL(theta)
    L3, L4 = thumbcalculateL(thumbCurl)
    L1_0 = 1.861
    L2_0 = 1.861
    L3_0 = 3
    L4_0 = 1.6
    dL1 = L1_0 - L1
    dL2 = L2_0 - L2

    dL3 = L3_0 - L3
    dL4 = L4_0 - L4

    dPhi1 = (dL1/0.45) * (180/math.pi)
    dPhi2 = 180 - ((dL2/0.45) * (180/math.pi))
    dPhi3 = (dL3/0.45) * (180/math.pi)
    dPhi4 = (dL4/0.45) * (180/math.pi)

    pointercurl = (-curl + (- theta[1])) * 180/math.pi

    #print("dPhi1 = ", dPhi1)
    #print("dPhi2 = ", dPhi2)

    thumbRot = thumbRot * 180/math.pi
    thumbPinch = thumbPinch * 180/math.pi

    if filter is None:
        filter = np.array([
                    dPhi1,
                    dPhi2,
                    pointercurl,
                    thumbRot,
                    thumbPinch,
                    dPhi3,
                    dPhi4,
                ])
    else:
        alpha = 0.5
        curr = np.array([
                    dPhi1,
                    dPhi2,
                    pointercurl,
                    thumbRot,
                    thumbPinch,
                    dPhi3,
                    dPhi4,
                ])
        filter = filter + alpha * (curr - filter)

    dPhi1, dPhi2, pointercurl, thumbRot, thumbPinch, dPhi3, dPhi4 = filter


    cmd = (str) (dPhi1) + " " + (str) (dPhi2) + " " + (str) (pointercurl) + " " + (str) (thumbRot) + " " + (str) (thumbPinch) + " " + (str) (dPhi3) + " " + (str) (dPhi4)
    print(f"L3: {dPhi3}, L4: {dPhi4}")
    
    return cmd


def find_ports():
    for p in list_ports.comports():
        if "CP2102" in p.description:
            return p.device
    return None

##Host and port info for sockets connection
HOST = "127.0.0.1"
PORT = 8765


## Port and Baud rate info for Serial connection

SERIAL_PORT = None 
if SERIAL_PORT == None:
    SERIAL_PORT = find_ports()

if SERIAL_PORT == None:
    raise Exception("Serial Device not found")

BAUD = 115200


serial_queue = queue.Queue()

message_lock = threading.Lock()
current_message = None



def serial_process():
    global current_message
    global last_send
    global SENDPERIOD

    ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0, write_timeout = 0)

    last_message = None

    while True:
        work_available.acquire()
        
        message = None
        with message_lock:
            message = current_message
        
        if message is None or message == last_message:
            time.sleep(0.001)
            continue
        if message == "EXIT":
            break

        last_message = message

        data = message.split()

        theta = ((float)(data[0]), (float)(data[1]))
        curl = (float)(data[2])
        thumbRot = (float)(data[3])
        thumbPinch = (float)(data[4])
        thumbCurl = ((float)(data[5]), (float)(data[6]))

        cmd = CMD(theta, curl, thumbRot, thumbPinch, thumbCurl)
        
        now = time.perf_counter()
        if now - last_send >= SENDPERIOD:
            ser.write((cmd + "\n").encode("utf-8"))
            last_send = now

    ser.close()

def socket_thread() :
    global current_message


    conn = None
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)


    server.settimeout(60)


    print("Server listening...")
    while True:

        try:
            conn, addr = server.accept()
            print("Connected:", addr)

        except socket.timeout:
            print("No client connected in time")
        if conn:
            buffer = ""
            while True:
                try:
                    buffer += conn.recv(1024).decode()
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        with message_lock:
                            current_message = line
                        work_available.release()
                except ConnectionResetError:
                    print("Client disconnected abruptly")
                    break
                except OSError as e:
                    print("Socket error: ", e)
                    break
            conn.close()
    




if SERIAL_PORT:
    print("starting serial process")
    serial_thread = threading.Thread(target=serial_process, daemon=False)
    serial_thread.start()

server_thread = threading.Thread(target=socket_thread, daemon=False)
server_thread.start()


serial_thread.join()
server_thread.join()

