##CAN ONLY BE RUN IN A BLENDER INTERFACE

import bpy
import socket
import threading
import math


HOST = "127.0.0.1"
PORT = 8765

pos_loc = threading.Lock()

#Semaphore to wake the client thread when new data is available
work_available = threading.Semaphore(0)

pointertheta = None
thumbtheta = None

program_running = True

def getJointAngles(name, arm_eval):
    bone = arm_eval.pose.bones[name]
    bone_parent = bone.parent
    
    if(bone_parent == None):
        R_rest = bone.bone.matrix_local.to_3x3()
        R = bone.matrix.to_3x3()
        
        R_joint = R_rest.inverted() @ R
        
        euler = R_joint.to_euler('XYZ')
        return euler
    
    else:
        R_rest = bone.bone.matrix_local.to_3x3()
        R = bone.matrix.to_3x3()
    
        R_parent_rest = bone_parent.bone.matrix_local.to_3x3()
        R_parent = bone_parent.matrix.to_3x3()
        
        R_rest_rel = R_parent_rest.inverted() @ R_rest
        R_rel = R_parent.inverted() @ R
        
        R_joint = R_rest_rel.inverted() @ R_rel
        euler = R_joint.to_euler('XYZ')
        return euler
        
        

def client_process():

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    
    while True:
        work_available.acquire() 
          # wait here until new data is available
        if(not program_running):
            message = "EXIT\n"
            break
        
        global pointertheta
        global thumbtheta
        
        with pos_loc:
            if (pointertheta != None and thumbtheta != None):
                currTheta = f"{pointertheta[0]} {pointertheta[1]} {pointertheta[2]} {thumbtheta[0]} {thumbtheta[1]} {thumbtheta[2]} {thumbtheta[3]}\n"
                message = currTheta.encode('utf-8')
                print(f"{currTheta}")
                client.send(message)
    client.close()

def blender_processes():
    
    localPointerTheta = None
    
    localThumbTheta = None

    pointerarmature = bpy.data.objects["Armature"]
    thumbarmature = bpy.data.objects["ThumbArmature"]
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    pointerarm_eval = pointerarmature.evaluated_get(depsgraph)
    thumbarm_eval = thumbarmature.evaluated_get(depsgraph)
    
    peuler1 = getJointAngles("Bone",pointerarm_eval)
    peuler2 = getJointAngles("Bone.001",pointerarm_eval)
    peuler3 = getJointAngles("Bone.002",pointerarm_eval)
    peuler4 = getJointAngles("Bone.003",pointerarm_eval)

    localPointerTheta = (peuler1.x, peuler2.z, (peuler3.z + peuler4.z)/2)

    print(f"{localPointerTheta}")
    
    teuler2 = getJointAngles("Bone.001",thumbarm_eval)
    teuler4 = getJointAngles("Bone.003",thumbarm_eval)
    teuler5 = getJointAngles("Bone.004",thumbarm_eval)
    teuler6 = getJointAngles("Bone.006",thumbarm_eval)
    
    localThumbTheta = (-teuler2.z, math.radians(180) - (-teuler4.x + math.radians(90)), -teuler5.x, -teuler6.x)
    
    global thumbtheta
    global pointertheta

    with pos_loc:
        if (localPointerTheta != pointertheta or localThumbTheta != thumbtheta):
            pointertheta = localPointerTheta
            thumbtheta = localThumbTheta
            work_available.release()  # signal the client thread that new data is available

    return 0.1



bpy.app.timers.register(blender_processes)
#client_thread = threading.Thread(target=client_process, daemon=True)
#client_thread.start()
