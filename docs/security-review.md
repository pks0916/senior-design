# Security Review

Written by Andy, Nov 1, 2026, against commit `77cb5ee`. I read through `webserver.py`, `yolo.py`, and `HomePage.tsx`, then ran the server locally and tried attacking it with fake clients. No real hardware was involved.

The short version: nothing in the system checks who it's talking to. Anyone who can reach the server can fire the horn, pretend to be the Pi, send fake detections and health data, and upload a web page that the server will then host. That was fine for a lab prototype, but the sponsor wants a product people can buy this year, so it needs to be fixed.

## Who could attack it

- **Someone on the same Wi-Fi or Tailscale network.** They can talk to port 5000 directly and do everything below.
- **Any website the homeowner visits.** The server doesn't check where WebSocket connections come from, so a random site could use the homeowner's own browser to connect and fire the horn.
- **Anyone on the internet**, if the homeowner forwards port 5000 so they can check the dashboard away from home. People would probably do this if there's no easier way to get remote access.

What's at risk: control of a really loud horn and a 12,000-lumen light (safety, and annoying the neighbors), photos of the homeowner's yard (privacy), and whether people trust the alerts at all. If it goes off for no reason all the time, people will just ignore it.

## What I found

I rated them High if someone can control the horn or run code on the server, Medium if they can mislead the user or see data, and Low if it's more of a robustness issue.

| # | How bad | What's wrong | How I tested it | OWASP IoT Top 10 (2018) |
|---|---|---|---|---|
| SEC-1 | High | **Anyone can fire the horn.** The `manual_trigger` Socket.IO event has no login check, and `cors_allowed_origins="*"` lets any website open the socket (cross-site WebSocket hijacking) | I connected a client pretending to be from `http://evil.example` and sent `manual_trigger`. The server replied `ok: True, Queued horn toggle to 1 Pi(s)` | I3 Insecure ecosystem interfaces |
| SEC-2 | High | **Anyone can pretend to be the Pi.** Anyone can open `/api/manual_commands/stream`, and if a second connection uses the same `pi_id` it replaces the real Pi. Then the real Pi stops getting commands and the fake one gets them | A fake client opened the stream and received the horn command | I3, I8 Lack of device management |
| SEC-3 | High | **The debugger is exposed.** The server runs with `debug=True` on `0.0.0.0` with `allow_unsafe_werkzeug=True`. Flask's docs say the debugger "allows executing arbitrary Python code from the browser" and the PIN "should not be relied on" | The startup log says `Debug mode: on`, `Running on all addresses`, `Debugger is active!` | I9 Insecure default settings |
| SEC-4 | High | **You can upload any kind of file.** `/upload` saves whatever you send into `static/` and serves it back. If you upload an `.html` file it gets served as a real web page from the server, which is stored cross-site scripting. There's also no size limit, so someone could fill the disk | I uploaded `x.html` and `GET /static/x.html` came back as `Content-Type: text/html` | I3, I7 Insecure data transfer and storage |
| SEC-5 | Medium | **Fake detections and fake health data.** `/upload` and `/api/telemetry` pass along whatever they get to every dashboard | I posted `cpu_temp: 999` and it showed up on a listening dashboard client | I3 |
| SEC-6 | Medium | **CORS allows any website**, with credentials allowed (`supports_credentials=True` and `origins "*"`) | A preflight request from `http://evil.example` came back with `Access-Control-Allow-Origin: http://evil.example` | I9 |
| SEC-7 | Medium | **Nothing is encrypted.** It's plain HTTP and WebSocket. Tailscale encrypts traffic if you use it, but nothing in the code requires it | Read through the code | I7 |
| SEC-8 | Medium | **No login on the dashboard.** Anyone who can open it can see the yard photos and press the horn button. Photos can have people in them too, since the current config detects people | Read through the code | I1, I6 Insufficient privacy protection |
| SEC-9 | Low | **No input checking.** If `confidence` isn't a number, `/upload` crashes with a 500. The Pi's `requests.post` calls also have no timeout | Sent `confidence=abc` and got a 500 | I3 |

## How I'd fix it, easiest first

1. Turn off debug mode and run Flask-SocketIO on a real production server. That fixes SEC-3 and only takes a few minutes.
2. Give each Pi a secret token and check it on `/upload`, `/api/telemetry`, and the command stream. Reject any `pi_id` the server doesn't know. That fixes SEC-2, SEC-4, and SEC-5 and takes a few hours.
3. Lock CORS and `cors_allowed_origins` down to just the dashboard's address. That fixes SEC-6 and the browser part of SEC-1, and only takes a few minutes.
4. Add a login to the dashboard, and have the Socket.IO `connect` handler check it before accepting `manual_trigger`. That fixes SEC-1 and SEC-8 and is probably about a day of work.
5. Only accept PNG and JPEG uploads, cap the file size (`MAX_CONTENT_LENGTH`), have the server pick the file names, and check that `confidence` is a real number. That fixes SEC-4 and SEC-9 and takes a few hours.
6. Add a cooldown on the manual horn button so it can't be spammed. That limits the damage from SEC-1 and takes a few hours.
7. Require TLS or Tailscale for any remote access, and write that in the setup guide. That fixes SEC-7 and takes a few hours.

These line up pretty well with NIST's baseline for IoT devices ([NISTIR 8259A](https://csrc.nist.gov/pubs/ir/8259/a/final)). Fix 2 covers **device identification**, fixes 1, 3, and 4 cover **logical access to interfaces** and **device configuration**, and fixes 5 and 7 cover **data protection**.

## Sources

- Flask, [Debugging Application Errors](https://flask.palletsprojects.com/en/stable/debugging/)
- OWASP, [Testing WebSockets](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets)
- OWASP IoT Top 10 (2018), summarized by [TechWell](https://www.techwell.com/techwell-insights/2019/01/owasp-releases-latest-top-10-iot-vulnerabilities)
- Fagan et al., [NISTIR 8259A: IoT Device Cybersecurity Capability Core Baseline](https://csrc.nist.gov/pubs/ir/8259/a/final), NIST, May 2020
