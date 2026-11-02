# Setup Guide — Running the Inherited System Locally

Owner: Andy Vo · Tested Nov 1, 2026 on a clean Linux copy of commit `77cb5ee` (Python 3.13, Node 22.22, npm 10.9)

This guide gets the server and dashboard running on a laptop with simulated data, no Pi needed. It lists every problem found along the way, with the workaround. Follow it top to bottom; run everything from the folder shown.

## 1. Backend server (Flask + Socket.IO)

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install flask flask-cors flask-socketio pandas filelock requests psutil
mkdir static                       # REQUIRED on a fresh clone — see S-2
python webserver.py                # serves on http://localhost:5000
```

Check it works with simulated data (second terminal):

```bash
# telemetry → should return 200 and appear on the dashboard
curl -X POST localhost:5000/api/telemetry -H 'Content-Type: application/json' \
  -d '{"cpu_usage":12.5,"cpu_temp":48.2,"memory_total":2000000000,"memory_used":800000000,"disk_usage":30,"uptime":"test"}'

# fake detection → should return 201 and the image should show on the dashboard
curl -X POST localhost:5000/upload -F image=@any.png -F animal=Bear \
  -F timestamp="2026-11-01 20:00:00" -F filename=Bear-test.png -F confidence=0.87
```

## 2. Dashboard (React + Vite)

From the **repo root** first, then `frontend/`:

```bash
npm install            # in the repo root — installs socket.io-client (see S-1)
cd frontend
npm install
npm run dev            # http://localhost:5173
```

The dashboard shows "connected" when the server from step 1 is running on the **same machine** (see S-4).

## 3. Detector (yolo.py) — Pi or laptop with a webcam

From `backend/` in the same virtual environment:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip uninstall -y opencv-python && pip install opencv-python-headless
# edit config.json first — see S-3, S-5, S-7
python yolo.py
```

Last year's team recommends Python 3.10 on the Pi for `ultralytics`. On a laptop, `gpiozero` installs but does nothing with the pins left at `null`, which is the safe default for testing.

## Problems found and workarounds

| ID | Problem | Effect | Workaround / proposed fix | Suggested owner |
|---|---|---|---|---|
| S-1 | `socket.io-client` is listed in the **root** `package.json`, not `frontend/package.json` | Following the README (`npm install` in `frontend/` only), `npm run build` fails: *Cannot find module 'socket.io-client'* | Run `npm install` in the repo root too; proper fix: `npm install socket.io-client` inside `frontend/` | Amareen |
| S-2 | `backend/static/` is not in the repo, and only `yolo.py` creates it | On a fresh clone, every `POST /upload` returns **500** (`FileNotFoundError`) until the folder exists | `mkdir backend/static`; proper fix: `os.makedirs(..., exist_ok=True)` at server start | Parth |
| S-3 | `config.json` has `detect` and `triggerAlarm` set to `[0]` (COCO "Person"); bear is class `21` | The system as committed is a **person** detector and would fire the horn at people | Set both to `[21]` (keep `0` in `detect` only if you want to log people) | Jason |
| S-4 | `localhost:5000` is hard-coded in `HomePage.tsx` and in the image URLs the server sends; `config.json` points the Pi at `100.90.180.25` (last year's Tailscale address) | Dashboard and images only work when everything runs on one machine; the Pi uploads to an address that no longer exists | Edit `config.json` URLs to your server; proper fix: read the server address from an environment variable (`VITE_SERVER_URL`) and build image URLs from `request.host_url` | Amareen / Parth |
| S-5 | `config.json` loads `yolo11n_720_ncnn_model`; last year's report says the final model ran at 480×480 | Slower inference than reported; benchmarks won't match the report | Decide which to use and record it; 480 matches the report | Jason |
| S-6 | `yolo.py` trims `images.csv` with `imgs.size` (rows × columns) instead of `len(imgs)` | Keeps roughly half as many rows as `imgLimit` says; image files are never deleted, so the disk fills over time | Use `len(imgs)`, and delete files that fall off the list | Parth |
| S-7 | `hornGpioPin` and `lightGpioPin` are `null` | No deterrent fires — fine for laptop testing, but the Pi wiring isn't recorded anywhere | Get pin numbers from ECE and record them in the README | ECE / Andy |
| S-8 | `backend/images.csv` and `detection.txt` are committed with last year's "Person" test entries, but the images aren't in the repo | `GET /api/detection` and the dashboard's first load point to images that 404 | Delete both files from git and add them to `.gitignore` | Parth |
| S-9 | Flask, flask-cors, flask-socketio and psutil are missing from `requirements.txt` | A fresh install of the requirements can't run the server | Add them to `requirements.txt` | Parth |
| S-10 | `npm run lint` in `frontend/` reports 3 errors (React hooks rules, e.g. `setState` called inside an effect) | Build still succeeds; code quality only | Fix during the dashboard rework | Amareen |
| S-11 | The manual-command listener connects without `?pi_id=`, so every Pi registers as `default_pi` | With two Pis, the second one replaces the first and the first stops receiving commands | Append `?pi_id=<piId>` to the stream URL | Parth |

Security problems are tracked separately in [security-review.md](security-review.md).

## What was verified

| Check | Result |
|---|---|
| Server starts | Yes (Flask 3.1, Flask-SocketIO 5.7; runs in debug mode on all interfaces — see SEC-3) |
| `POST /api/telemetry` → dashboard | 200; a Socket.IO client received `telemetry_update` |
| `POST /upload` → dashboard | 500 on fresh clone (S-2); 201 after `mkdir static`, and a Socket.IO client received `detection_update` |
| `GET /static/<file>` | 200 for the uploaded image |
| Dashboard build | Fails as documented (S-1); succeeds after root `npm install` |
| Detection models | Both `yolo11n_480_ncnn_model` and `yolo11n_720_ncnn_model` load with `ultralytics` 8.4 + `ncnn`. They are the stock 80-class COCO models (class 0 = person, 21 = bear), not fine-tuned on bears. On a sample street image both found the bus and people. Median time per image on an x86 laptop-class CPU: **61 ms (480) vs 132 ms (720)** — the 720 model is about 2× slower (S-5). Pi timings will be higher. |
| Detector loop (`yolo.py` with a camera) | Not run (no camera in the test environment). Next: laptop webcam, then the Pi (Jason). |
| Physical camera, horn, light | Not tested (no Pi in this setup) |
