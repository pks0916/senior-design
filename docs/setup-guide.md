# Setup Guide

Written by Andy. These are the steps I used to get last year's code running from a fresh clone (commit `77cb5ee`), plus every problem I ran into along the way. I tested on Linux with Python 3.13 and Node 22, using fake data, so no Pi or camera was involved.

If you're on Windows or Mac and something's different, add it here.

## 1. Backend server

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install flask flask-cors flask-socketio pandas filelock requests psutil
mkdir static
python webserver.py
```

The `mkdir static` part matters. Without it every upload fails (see S-2 below). The server runs on http://localhost:5000.

To check it's working, open a second terminal and send it some fake data:

```bash
curl -X POST localhost:5000/api/telemetry -H 'Content-Type: application/json' \
  -d '{"cpu_usage":12.5,"cpu_temp":48.2,"memory_total":2000000000,"memory_used":800000000,"disk_usage":30,"uptime":"test"}'

curl -X POST localhost:5000/upload -F image=@any.png -F animal=Bear \
  -F timestamp="2026-11-01 20:00:00" -F filename=Bear-test.png -F confidence=0.87
```

The first one should return 200 and the second should return 201. Both should show up on the dashboard if it's open.

## 2. Dashboard

You have to run `npm install` in the repo root first, not just in `frontend/` (see S-1):

```bash
npm install
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173. It only connects if the server is running on the same computer (see S-4).

## 3. Detector (yolo.py)

This one is meant for the Pi, but it should also work on a laptop with a webcam. From `backend/`, in the same virtual environment:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip uninstall -y opencv-python && pip install opencv-python-headless
python yolo.py
```

Fix `config.json` before you run it (see S-3, S-5, and S-7). Last year's team said to use Python 3.10 on the Pi because of `ultralytics`. On a laptop the GPIO stuff doesn't do anything as long as the pins are left as `null`, which is what you want for testing.

## Problems I found

| # | What's wrong | What happens | How to get around it | Who should fix it |
|---|---|---|---|---|
| S-1 | `socket.io-client` is in the root `package.json` instead of `frontend/package.json` | If you only run `npm install` in `frontend/` like the README says, the build fails with "Cannot find module 'socket.io-client'" | Run `npm install` in the root too. Real fix: `npm install socket.io-client` inside `frontend/` | Amareen |
| S-2 | There's no `backend/static/` folder in the repo, and only `yolo.py` creates it | On a fresh clone every upload returns a 500 error | `mkdir backend/static`. Real fix: have the server create the folder when it starts | Parth |
| S-3 | `detect` and `triggerAlarm` in `config.json` are set to `[0]`, which is "person". Bear is `21` | Right now it's a person detector and would fire the horn at people | Change both to `[21]` | Jason |
| S-4 | `localhost:5000` is hardcoded in `HomePage.tsx` and in the image URLs the server sends. `config.json` also points the Pi at `100.90.180.25`, last year's Tailscale address | The dashboard only works on the same machine as the server, and the Pi would upload to an address that doesn't exist anymore | Change the URLs in `config.json` to your server. Real fix: put the server address in an environment variable | Amareen / Parth |
| S-5 | `config.json` uses the 720 model, but last year's report says they used 480 | It's slower than what they reported | Pick one and write it down. 480 matches the report | Jason |
| S-6 | `yolo.py` trims `images.csv` using `imgs.size` (rows × columns) instead of `len(imgs)` | It keeps about half as many rows as it should, and old images never get deleted, so the disk fills up eventually | Use `len(imgs)` and delete the old image files | Parth |
| S-7 | `hornGpioPin` and `lightGpioPin` are `null` | Nothing fires. That's fine for testing, but nobody wrote down the real pin numbers | Get the pins from ECE and put them in the README | ECE / Andy |
| S-8 | `images.csv` and `detection.txt` are committed with last year's "Person" test data, but the images aren't in the repo | `/api/detection` and the dashboard's first load point to images that don't exist | Remove both from git and add them to `.gitignore` | Parth |
| S-9 | Flask, flask-cors, flask-socketio, and psutil aren't in `requirements.txt` | Installing from requirements alone isn't enough to run the server | Add them to `requirements.txt` | Parth |
| S-10 | `npm run lint` in `frontend/` gives 3 errors (React hooks rules) | Doesn't break the build, it's just code quality | Clean up during the dashboard rework | Amareen |
| S-11 | The Pi connects to the command stream without `?pi_id=`, so every Pi shows up as `default_pi` | With two Pis, the second one kicks the first one off and the first stops getting commands | Add `?pi_id=<piId>` to the stream URL | Parth |

The security problems are in [security-review.md](security-review.md).

## What I actually tested

- **Server:** starts fine (Flask 3.1, Flask-SocketIO 5.7). It runs in debug mode on all network interfaces though, which is a security problem (SEC-3).
- **Telemetry:** posting to `/api/telemetry` returned 200, and a test Socket.IO client got the `telemetry_update`.
- **Uploads:** got a 500 on a fresh clone (S-2). After `mkdir static` it returned 201, and the test client got the `detection_update`.
- **Images:** the uploaded image loaded fine from `/static/`.
- **Dashboard build:** failed following the README (S-1), then worked after running `npm install` in the root.
- **Models:** both `yolo11n_480_ncnn_model` and `yolo11n_720_ncnn_model` load and run with `ultralytics` 8.4 and `ncnn`. They're the regular 80-class COCO models (0 = person, 21 = bear), not trained on bears. On a sample image they both found the bus and the people. On my test CPU the 480 model took about 61 ms per image and the 720 took about 132 ms, so 720 is roughly twice as slow. It'll be slower on the Pi.
- **Not tested yet:** the full `yolo.py` loop with a camera, since I didn't have one hooked up (Jason's next step), and the actual camera, horn, and light on the Pi.
