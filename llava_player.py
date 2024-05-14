# Copyright (c) 2024, OPENZEKA.  All rights reserved.

import PySimpleGUI as sg
from PIL import Image, ImageTk
from client_se import ClientSE
from threading import Thread
import time
import ollama
from io import BytesIO
import base64
import numpy as np
from collections import deque
import json

frame:np.array =  None
prompt:str = "Describe the scene concisely."
output = deque()
is_prompt_changed:bool = False
is_connected = False
is_loaded = False
cam_types = ['CSI','USB', 'RTSP/HTTP']
cse_target = "http://0.0.0.0:7005"
cam_path = "http://renzo.dyndns.tv/mjpg/video.mjpg"
interframe_duration = 1 / 33  # get how long to delay between frames

model_selection = "llava:7b-v1.6"

client:ClientSE = None

def connect(client, stream_engine_ip, cam_type, cam_path, token):
    client = ClientSE(stream_engine_ip, token)
    ret, msg = client.check()
    print(msg)
    if not ret:
        data = json.loads(msg)
        if 'error' in data:
            sg.popup(data['error'])
        return None
    print(cam_type)
    if cam_type == cam_types[0]:
        client.open_csi(cam_path, sensor_mode=4, width=1920, height=1080, fps=30)
    elif cam_type == cam_types[1]:
        client.open_usb(cam_path, width=640, height=480, fps=30)
    else:
        client.open_ip(cam_path)
    client.run()

    return client

def ask_llava(image, text):
    global is_prompt_changed
    image = Image.fromarray(image)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    img_byte = buffer.getvalue()
    convert2 = base64.b64encode(img_byte)
    print(20*"*")
    out = []
    for response in ollama.generate(model_selection, text, images=[convert2.decode('utf-8')], stream=True):
        print(response['response'], end='', flush=True)
        out.append(response['response'])
        if is_prompt_changed :
            print(5*'\n')
            is_prompt_changed = False
            break

    print('\n'+20*"-")

    return "".join(out)

def run():
    print("Lava running.... ")
    while True:
        try:
            if frame is None:
                continue
            output.append(ask_llava(frame, prompt)+"\n\n")
            time.sleep(3)
        except Exception as e:
            print(e)
            pass

def load_model():
    window['OUTPUT'].update(value="")
    
    llava = Thread(target=run, daemon=True)
    llava.start()
    
    sg.cprint("First time model answer is preparing...")

sg.theme('BluePurple')

col_1 = [[sg.Text(text="Token: "), sg.Input(default_text="Enter your token here", pad=((76,0),(0,0)), size=(50,5), key="TOKEN")],
         [sg.Text(text="Stream Engine IP: "), sg.Input(default_text=cse_target, size=(50,5), key="TARGET_IP")],
         [sg.Text(text="Camera Type: "), sg.Combo(values=cam_types, pad=((29,0),(0,0)), default_value=cam_types[2], size=(10,3), key="CAM_TYPE")],
         [sg.Text(text="Camera Source: ", enable_events=True, key="ON_CHANGE"), sg.Input(default_text=cam_path, pad=((18,0),(0,0)), size=(50,5), key="CAM_SRC")]]

layout = [[sg.Text("Prompt: ")],
          [sg.Multiline(default_text=prompt, size=(158,5), text_color="Black", expand_y=True, key="INPUT", reroute_cprint=True), sg.Column(layout=col_1)],
          [sg.Button('Load Model'), sg.Button('Change Prompt'), sg.Button('Connect', pad=((1043,0),(0,0))), sg.Button('Exit')],
          [sg.Image(size=(1280,720), key="FRAME"), sg.Multiline(default_text="", font = ("Arial", 15), text_color="Blue", expand_y=True, key="OUTPUT", reroute_cprint=True)]]

window = sg.Window('Cordatus Stream Engine - Live Multimodal Application', layout)

while True:  # Event Loop
    event, values = window.read(timeout=interframe_duration)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break

    if is_loaded == False and event == 'Load Model':
        load_model()
        is_loaded = True
        time.sleep(0.01)

    if is_connected == False and event == 'Connect':
        if client :
            client.close()
        stream_engine_ip = window['TARGET_IP'].get()
        cam_type = window['CAM_TYPE'].get()
        cam_path = window['CAM_SRC'].get()
        token = window['TOKEN'].get()
        client = connect(client, stream_engine_ip, cam_type, cam_path, token)
        if client:
            is_connected = True
        else:
            is_connected = False
        time.sleep(1)

    if client is None:
        continue

    if event == 'ON_CHANGE':
        is_connected = False

    if event == 'Change Prompt':
        prompt = window['INPUT'].get()
        is_prompt_changed = True        
        window['OUTPUT'].update(value= "")
        sg.cprint("Prompt has been changed: ", prompt)
        time.sleep(0.01)

    # if is_connected:
    ret, frame = client.read()
    if ret:
        pframe = ImageTk.PhotoImage(Image.fromarray(frame).resize((1280,720)))
        window['FRAME'].update(data=pframe)
    
    if len(output):
        sg.cprint(output.pop())

client.close()
time.sleep(1.0)
window.close()