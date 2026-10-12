from ultralytics import YOLO
import os
import datetime
import threading
import time
import json
import pandas as pd
import requests
import importlib
import psutil
import sseclient
from threading import Thread
from filelock import FileLock

try:
    from gpiozero import DigitalOutputDevice
except Exception:
    DigitalOutputDevice = None

# set boot time when device starts up, used for telemetry uptime calculation - est time
BOOT_TIME_EPOCH = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())

class ManualCommandListener:
    def __init__(self, manual_command_url, pi_id, horn_gpio, light_gpio, cfg):
        self.manual_command_url = manual_command_url
        self.pi_id = pi_id
        self.horn_gpio = horn_gpio
        self.light_gpio = light_gpio
        self.cfg = cfg
        self.running = True
    
    def start(self):
        """Connect to SSE endpoint and listen for commands"""
        try:
            url = f"{self.manual_command_url}"
            print(f'Pi connecting to manual command stream at {url}')
            
            while self.running:
                try:
                    response = requests.get(url, stream=True, timeout=40)
                    print(f'Started manual command listener for Pi \'{self.cfg.get("piId", "pi-1")}\'')
                    
                    for line in response.iter_lines():
                        if not self.running:
                            break
                        
                        if line:
                            line = line.decode('utf-8') if isinstance(line, bytes) else line
                            
                            if line.startswith('data:'):
                                data_str = line[5:].strip()  # Remove 'data:' prefix
                                try:
                                    command = json.loads(data_str)
                                    print(f'📡 Received command: {command}')
                                    _handle_manual_trigger(command, self.horn_gpio, self.light_gpio, self.cfg)
                                except json.JSONDecodeError as e:
                                    print(f'Failed to parse command: {e}')
                            elif line.startswith(':'):
                                # Keep-alive, ignore
                                pass
                
                except requests.exceptions.RequestException as e:
                    print(f'Connection error: {e}')
                    if self.running:
                        print(f"Pi '{self.cfg.get('piId', 'pi-1')}' reconnecting in 5s...")
                        time.sleep(5)
                except Exception as e:
                    print(f'Error in command listener: {e}')
                    if self.running:
                        time.sleep(5)
        
        except Exception as e:
            print(f'Failed to start manual command listener: {e}')
    
    def stop(self):
        self.running = False
        



class Detector:

    def __init__(self):
        self.isDetected = False
        self.event = threading.Event()
        self.event.clear()
        self.mutex = threading.Lock()
        self.cond = threading.Condition()
        self.trigger_time = datetime.datetime.now()
        self.alarm_length = 10

    def get_detected(self):
        return self.isDetected

    def set_detected(self, val):
        self.isDetected = val
        if self.isDetected:
            self.trigger_time = datetime.datetime.now()

    def set_alarm_length(self, val):
        self.alarm_length = val

    def check_reset(self):
        interval = (datetime.datetime.now() - self.trigger_time).total_seconds()
        if interval > self.alarm_length and self.isDetected:
            self.isDetected = False
            return True
        return False


class GPIOTrigger:
    def __init__(self, pin: int | None):
        self.pin = pin
        self._device = None

        if self.pin is None:
            return

        if DigitalOutputDevice is None:
            raise RuntimeError(
                "GPIO output requested but gpiozero is not available. "
                "Install it on the Raspberry Pi (e.g. pip install gpiozero)."
            )

        self._device = DigitalOutputDevice(self.pin, active_high=True, initial_value=False)

    def on(self):
        if self._device is not None:
            self._device.on()

    def off(self):
        if self._device is not None:
            self._device.off()

    def toggle(self):
        if self._device is not None:
            state = getattr(self._device, "value", False)
            if state:
                self._device.off()
            else:
                self._device.on()

    def pulse(self, duration):
        if self._device is not None:
            self._device.on()
            time.sleep(duration)
            self._device.off()

    def close(self):
        if self._device is not None:
            try:
                self._device.off()
            finally:
                self._device.close()
                self._device = None


def upload_image(filename, animal, timestamp, confidence, upload_url: str):
    try:
        with open(filename, 'rb') as f:
            files = {'image': f}
            data = {
                'animal': animal,
                'timestamp': timestamp,
                'filename': os.path.basename(filename),
                'confidence': confidence,
            }

            response = requests.post(upload_url, files=files, data=data)

            if response.status_code in [200, 201]:
                print(f"Successfully uploaded {filename}")
            else:
                print(f"Failed to upload {filename}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error uploading image: {e}")

def telemetry(upload_url):
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        # cpu temp
        cpu_temp = psutil.sensors_temperatures().get('cpu_thermal', [0])[0].current
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')
        telemetry_data = {
            'cpu_usage': cpu_usage,
            'cpu_temp': cpu_temp,
            'memory_total': memory_info.total,
            'memory_used': memory_info.used,
            'memory_percent': memory_info.percent,
            'disk_usage': disk_usage.percent,
            'uptime': BOOT_TIME_EPOCH
        }

        response = requests.post(upload_url, json=telemetry_data)

        if response.status_code == 200:
            print("Successfully sent telemetry data")
        else:
            print(f"Failed to send telemetry data. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error retrieving telemetry data: {e}")



def get_cv2():
    try:
        return importlib.import_module("cv2")
    except Exception as e:
        raise RuntimeError(
            "OpenCV import failed. Install either 'opencv-python' (GUI) or "
            "'opencv-python-headless' (headless)."
        ) from e


def flash_startup(light_gpio: GPIOTrigger | None, flashes: int, interval: float):
    if light_gpio is None:
        return
    
    print("Booting...")

    for _ in range(flashes):
        light_gpio.on()
        time.sleep(interval)
        light_gpio.off()
        time.sleep(interval)


def _read_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def _read_config(path: str, lock: FileLock) -> dict:
    with lock:
        with open(path, "r") as f:
            return json.load(f)


def _handle_manual_trigger(command, horn_gpio, light_gpio, cfg):
    device = command.get("device")
    action = command.get("action")

    if device == "horn":
        if horn_gpio is None:
            print("Manual horn requested, but horn GPIO is not configured.")
            return
        horn_gpio.pulse(float(cfg.get("hornPulseSeconds", 1.0)))
        print(f"Manual horn triggered on pin {horn_gpio.pin}")
        return

    if device == "light":
        if light_gpio is None:
            print("Manual lights requested, but light GPIO is not configured.")
            return
        light_gpio.toggle()
        print(f"Manual lights toggled on pin {light_gpio.pin}")
        return

    print(f"Unknown manual trigger: device={device}, action={action}")


def detection(
    detector,
    horn_gpio: GPIOTrigger | None = None,
    light_gpio: GPIOTrigger | None = None,
    config_path: str = "config.json",
):
    bootstrap = _read_json(config_path)
    lock = FileLock(bootstrap["configLockPath"], thread_local=False)
    cfg = _read_config(config_path, lock)

    cv2 = get_cv2()
    debug = cfg["debug"]
    static_dir = cfg["staticDir"]
    os.makedirs(static_dir, exist_ok=True)
    model = YOLO(cfg["yoloModel"], task=cfg["yoloTask"])
    motion_thresh = cfg["motionThresh"]
    min_change_area = cfg["minChangeArea"]
    blur_k = int(cfg["gaussianBlurKernel"])
    blur_ksize = (blur_k, blur_k)

    last_detection = None
    time_between = 0
    time_since = 0
    last_image = datetime.datetime.now()

    cap = cv2.VideoCapture(cfg["cameraIndex"])
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        exit()

    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture initial frame.")
        cap.release()
        return

    prev_gray = cv2.cvtColor(cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE), cv2.COLOR_BGR2GRAY)
    animals: list = []
    trig_alarm: list = []
    gen_interval = 0
    det_interval = 0
    image_limit = 0
    class_names: dict = {}
    data: dict = cfg

    # initial psutil to prevent stale data
    last_telemetry = 0.0
    interval_telemetry = cfg.get("telemetryInterval", 30)
    telemetry_url = cfg.get("telemetryUploadUrl", "")
    
    # Setup manual command listener once before main loop
    manual_command_listener = None
    manual_command_url = cfg.get("manualCommandUrl", "")
    pi_id = cfg.get("piId", "default_pi")
    
    if manual_command_url:
        try:
            manual_command_listener = ManualCommandListener(manual_command_url, pi_id, horn_gpio, light_gpio, cfg)
            listener_thread = Thread(target=manual_command_listener.start, daemon=True)
            listener_thread.start()
            print(f"Started manual command listener for Pi '{pi_id}'")
        except Exception as e:
            print(f"Failed to start manual command listener: {e}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        # To compensate for device having camera sideways
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_delta = cv2.absdiff(prev_gray, gray)
        blur = cv2.GaussianBlur(frame_delta, blur_ksize, 0)
        thresh = cv2.threshold(blur, motion_thresh, 255, cv2.THRESH_BINARY)[1]
        motion_pixels = cv2.countNonZero(thresh)
        motion_detected = motion_pixels > min_change_area

        prev_gray = gray.copy()

        try:
            data = _read_config(config_path, lock)
            animals = data["detect"]
            trig_alarm = data["triggerAlarm"]
            gen_interval = data["genInterval"]
            det_interval = data["detInterval"]
            image_limit = data["imgLimit"]
            class_names = data["classNames"]
            detector.set_alarm_length(data["alarmLen"])
        except Exception:
            print("Configuration Error")

        # send telemetry data every 30 seconds
        now = time.monotonic()
        if telemetry_url and (now - last_telemetry) >= interval_telemetry:
            last_telemetry = now
            telemetry_thread = Thread(target=telemetry, args=(telemetry_url,), daemon=True)
            telemetry_thread.start()


        if detector.check_reset():
            if horn_gpio is not None:
                horn_gpio.off()
                print("Horn pin " + str(horn_gpio.pin) + " Off")
            if light_gpio is not None:
                light_gpio.off()
                print("Light pin " + str(light_gpio.pin) + " Off")

        if motion_detected:
            results = model(frame, verbose=False)

            now = datetime.datetime.now()

            time_since = (now - last_image).total_seconds()
            if time_since > gen_interval:
                last_image = now
                camera_path = os.path.join(data["staticDir"], "camera.png")
                if not cv2.imwrite(camera_path, frame):
                    print("Failed to save camera image")

            detections = results[0].boxes
            for box in detections:
                cls_id = int(box.cls.item())
                if cls_id not in animals:
                    continue
                label = class_names.get(str(cls_id))
                if label is None:
                    continue
                
                if box.conf < 0.50:
                    continue

                if last_detection is None:
                    time_between = det_interval + 1
                else:
                    time_between = (now - last_detection).total_seconds()

                if time_between > det_interval:
                    print(label + " Detected: " + str(now))
                    last_detection = now
                    det_log_path = data["detectionLogPath"]
                    with open(det_log_path, "a") as file:
                        file.write(label + " Detected: " + str(now) + "\n")
                    safe_ts = str(now).replace(" ", "-").replace(":", "-")
                    filename = os.path.join(data["staticDir"], f"{label}-{safe_ts}.png")
                    imgs_csv = data["imagesCsvPath"]
                    upload_url_rt = data["uploadUrl"]
                    try:
                        imgs = pd.read_csv(imgs_csv)
                    except FileNotFoundError:
                        imgs = pd.DataFrame(columns=["filename", "confidence"])

                    confidence = float(box.conf[0])
                    imgs = pd.concat(
                        [imgs, pd.DataFrame([[filename, confidence]], columns=["filename", "confidence"])],
                        ignore_index=True,
                    )
                    if imgs.size > image_limit:
                        start = imgs.size - image_limit
                        imgs = imgs.iloc[start:]
                    imgs.to_csv(imgs_csv, index=False)
                    if not cv2.imwrite(filename, frame):
                        print(f"Failed to save detection image: {filename}")
                    else:
                        print(f"Saved detection image: {filename}")

                    upload_thread = Thread(
                        target=upload_image,
                        args=(filename, label, now, float(box.conf[0]), upload_url_rt),
                        daemon=True,
                    )
                    upload_thread.start()

                    if cls_id in trig_alarm:
                        with detector.cond:
                            detector.set_detected(True)
                            detector.cond.notify()
                        if horn_gpio is not None:
                            horn_gpio.on()
                            print("Horn pin " + str(horn_gpio.pin) + " Triggered: " + str(now))
                        if light_gpio is not None:
                            light_gpio.on()
                            print("Light pin " + str(light_gpio.pin) + " Triggered: " + str(now))
                        break

    # Cleanup
    if manual_command_listener is not None:
        manual_command_listener.stop()
        print(f"Manual command listener for Pi '{pi_id}' stopped")
    
    cap.release()
    if debug and hasattr(cv2, "destroyAllWindows"):
        cv2.destroyAllWindows()
    if horn_gpio is not None:
        horn_gpio.close()
    if light_gpio is not None:
        light_gpio.close()


if __name__ == "__main__":
    _main_config_path = "config.json"
    main_cfg = _read_json(_main_config_path)

    det = Detector()
    det.set_alarm_length(main_cfg["alarmLen"])
    horn_gpio = GPIOTrigger(pin=main_cfg["hornGpioPin"])
    light_gpio = GPIOTrigger(pin=main_cfg["lightGpioPin"])

    flash_startup(
        light_gpio,
        main_cfg["startupFlashCount"],
        main_cfg["startupFlashIntervalSeconds"],
    )
    detection(det, horn_gpio=horn_gpio, light_gpio=light_gpio, config_path=_main_config_path)