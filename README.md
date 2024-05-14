# Cordatus Stream Engine - Live Multimodal Application
![Run the application](/assets/llava_player_gui_opt.mp4)

In this application, we have demonstrated an example on how to extend our [CSE Camera Player Agent](https://github.com/CordatusAI/cse-camera-agent) GUI application to communicate in real-time with a LLaVA model deployed on the Ollama project. This sample GUI application aims to provide a foundation for VLM applications where camera streaming is required. It is built on top of CSE Camera Player Agent to benefit from Cordatus Stream Engine's low latency hardware accelerated live camera streaming capabilities for custom AI applications.

Agent is designed and tested to work with local camera sources including USB, CSI and RTSP/HTTP but it can also be used if the remote client necessary ports are forwarded accordingly.

### LLaVA (Large Language and Vision Assistant)
LLaVA is a cutting-edge multimodal AI model, meaning it can understand and process both text and images. It's trained on a massive dataset, allowing it to analyze and interpret visual information. Currently, this application is using LLaVA version 1.6.

https://github.com/haotian-liu/LLaVA

### Ollama
Ollama isn't a directly comparable model, but rather a platform that interacts with LLaVA. It provides an interface for users to leverage LLaVA's capabilities. You can use Ollama to perform various tasks with LLaVA, such as generating image descriptions or extracting text from images.

https://github.com/ollama/ollama

## Test Your Cameras and Cordatus Stream Engine Service
In order to work with physical cameras using this agent, Cordatus Client needs to be up and running on the target device with the source is attached.

For RTSP/HTTP sources, at least one of the main-stream or sub-stream needs to be accessible within the same network. You can test RTSP/HTTP stream availablity by using VLC Media Player prior to this agent.

![RTSP Stream Test Sample](/assets/vlc_hikvision_cam.png)

If Cordatus Client is already running, the Cordatus Stream Engine should be available on port 7005 by default if it is not already occupied by some other application or service.

You can always check the port of the Cordatus Stream Engine service via the following terminal command:
```
ps -ef | grep cordatus_se
```
![Service Port](/assets/cse_port.png)

## 1. Run Ollama
```
docker run -d --rm --gpus=all \
           -p 11434:11434 \
           --name=ollama-server \
           -v ollama:/root/.ollama \
           ollama/ollama:latest
```

## 2. Building the Project Locally
Depending on the Python version that your project requires, build the sample image by providing the version information as follows:
```
./build_locally.sh 3.8

or

./build_locally.sh 3.11
```
To run the container:
```
xhost + && \
docker run -ti --rm --gpus=all \
           --network=host \
           -v /tmp/.X11-unix:/tmp/.X11-unix \
           -e DISPLAY=$DISPLAY \
           cordatus-multimodal-app:v1.0-x86-py3.8.19

or

xhost + && \
docker run -ti --rm --gpus=all \
           --network=host \
           -v /tmp/.X11-unix:/tmp/.X11-unix \
           -e DISPLAY=$DISPLAY \
           cordatus-multimodal-app:v1.0-x86-py3.11.9
```

## 3. Get Your Cordatus AI Token
Navigate to the https://cordatus.ai and login to your account. Under the Devices tab, click on the `Actions` button of the target device and select `Generate Token`. This screen will provide you the necessary token information.

![Retrieve your token](/assets/retrieve_token.gif)

## 4. Running the Sample GUI Application

![Run the application](/assets/llava_player_gui_run.gif)

```
python3 llava_player.py
```

## Custom Code Integration
Defining variables, camera types list, default target and a default HTTP camera source:
```
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
```

## Target Device Connection Function
```
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
```

## Model Answer Generation Based on the Prompt
```
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
```
```
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
```

## First Time Model Initialization
```
def load_model():
    window['OUTPUT'].update(value="")
    
    llava = Thread(target=run, daemon=True)
    llava.start()
    
    sg.cprint("First time model answer is preparing...")
```

## GUI Elements and Layout
You can customize the application layout as you wish by adding new PySimpleGUI elements inside the layout array. 
```
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
```

### Establishing Connection and Opening the Camera
In order to establish the connection between the local/remote target device and open the camera source, the `connect()` function will be called inside the `while` loop. Then we will be receiving the frames via the `read()` function call inside an infinite `while` loop:
```
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
```
