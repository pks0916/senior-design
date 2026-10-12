# SDPTeam12 - Bear-Be-Gone

Bear-Be-Gone is a real-time wildlife monitoring and deterrence system. It combines:

- A React + Vite frontend dashboard for live monitoring and manual controls
- A Flask + Socket.IO backend for telemetry, image uploads, and realtime events
- A Raspberry Pi detection script using YOLO for animal detection and GPIO triggers

## Repository Structure

- `frontend/` - React dashboard UI
- `backend/webserver.py` - Flask API + Socket.IO server
- `backend/yolo.py` - YOLO detection + telemetry + GPIO control loop
- `backend/config.json` - runtime configuration for detection and upload endpoints

## Prerequisites

Install the following before running locally:

- Node.js 20+ and npm
- Python 3.10+
- Camera source (USB/webcam or Pi camera, depending on environment)

For Raspberry Pi hardware control:

- A Raspberry Pi with GPIO access
- Horn and light connected to the pins configured in `backend/config.json`
- We recommend using Tailscale for running the device and frontend in tandem

### Note about installing packages on the Pi
There is a install script (install.sh) included. However, this sometimes has trouble running, as ultralytics will install open-cv, but we use opencv-headless. If it tells you that it cannot find opencv when you run, try to uninstall and reinstall the headless opencv library. We also recommend using Python version 3.10, as ultralytics support on newer versions is not fully implemented (as of this project).

## 1) Frontend Setup (React + Vite)

From `frontend/`:

```bash
npm install
npm run dev
```

Default frontend URL: `http://localhost:5173`

## 2) Backend Setup (Flask + Socket.IO)

Create and activate a Python virtual environment, then install dependencies.

From `backend/`:

```bash
python -m venv .venv
```

Activate:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (cmd): `.venv\Scripts\activate.bat`
- macOS/Linux: `source .venv/bin/activate`

Install packages:

```bash
pip install -r requirements.txt
pip install flask flask-cors flask-socketio psutil opencv-python
```

Start the backend server:

```bash
python webserver.py
```

Default backend URL: `http://localhost:5000`

## 3) Detection Worker (YOLO + GPIO)

The detector script is intended for the Pi/device that has camera and GPIO access.

From `backend/` (same virtual environment):

```bash
python yolo.py
```

What it does:

- Captures frames from the camera
- Runs YOLO detection
- Uploads detections to `/upload`
- Sends telemetry to `/api/telemetry`
- Listens for manual horn/light commands over SSE (`/api/manual_commands/stream`)

## Running the Full System Locally

Use 3 terminals:

1. `backend/` -> `python webserver.py`
2. `backend/` -> `python yolo.py` (optional for full end-to-end detection testing)
3. `frontend/` -> `npm run dev`

Then open `http://localhost:5173`.

## Configuration

Main runtime configuration is in `backend/config.json`.

Key fields:

- `uploadUrl`, `telemetryUploadUrl`, `manualCommandUrl` - backend endpoints used by `yolo.py`
- `cameraIndex` - local camera device index
- `hornGpioPin`, `lightGpioPin` - GPIO pins for deterrent devices
- `detect`, `triggerAlarm`, `classNames` - which classes to detect/trigger
- `genInterval`, `detInterval`, `alarmLen`, `imgLimit` - timing and retention behavior

For local-only development, set endpoint URLs in `config.json` to `http://localhost:5000/...`.

## Notes

- The frontend currently connects to Socket.IO at `http://localhost:5000`.
- Run backend scripts from inside `backend/` so relative paths (for `static`, `images.csv`, and logs) resolve correctly.