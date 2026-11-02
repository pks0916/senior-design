# Security Review of the Inherited Software

Owner: Andy Vo · Reviewed Nov 1, 2026 against commit `77cb5ee` · Method: read `webserver.py`, `yolo.py`, `HomePage.tsx`; ran the server locally and attacked it with simulated clients (no real hardware).

**Bottom line:** nothing in the system checks who is talking to it. Anyone who can reach the server can fire the horn, pose as the Pi, inject fake detections, spoof health data, and plant a web page on the server. That was acceptable for a lab prototype; it is not acceptable for a product sold to homeowners, and the sponsor's goal this year is a commercial prototype.

## Threat model

| Who | How they reach the system | What they could do |
|---|---|---|
| Anyone on the same home Wi-Fi or Tailscale network | Direct HTTP / Socket.IO to port 5000 | Everything below |
| Any website the homeowner visits | The homeowner's own browser opens a cross-site WebSocket to the server (no Origin check) | Fire the horn, read live detections |
| The internet | Only if the homeowner port-forwards 5000 (likely, if they want remote access without Tailscale) | Everything below |

Assets at risk: control of a ~150 dB horn and 12,000-lumen light (safety, neighbors), camera images of the homeowner's yard (privacy), and trust in the alerts (a deterrent people ignore is useless).

## Findings

Severity: High = attacker controls the deterrent or runs code; Medium = attacker misleads the user or reads data; Low = robustness.

| ID | Severity | Finding | Evidence (local test, Nov 1) | OWASP IoT Top 10 (2018) |
|---|---|---|---|---|
| SEC-1 | High | **Anyone can fire the horn.** The Socket.IO `manual_trigger` event has no authentication, and `cors_allowed_origins="*"` lets any website open the socket (cross-site WebSocket hijacking). | A client sending `Origin: http://evil.example` emitted `manual_trigger` and got `ok: True, Queued horn toggle to 1 Pi(s)` | I3 Insecure ecosystem interfaces |
| SEC-2 | High | **Anyone can pose as the Pi.** `/api/manual_commands/stream` accepts any caller; a second connection with the same `pi_id` replaces the real Pi's queue, so the real Pi stops receiving commands and the impostor gets them. | A fake client opened the stream and received the horn command | I3, I8 Lack of device management |
| SEC-3 | High | **Debugger exposed.** The server runs with `debug=True`, on `0.0.0.0`, with `allow_unsafe_werkzeug=True`. Flask's docs: the debugger "allows executing arbitrary Python code from the browser… protected by a pin, but that should not be relied on." | Startup log: `Debug mode: on`, `Running on all addresses`, `Debugger is active!` | I9 Insecure default settings |
| SEC-4 | High | **Unauthenticated uploads of any file type.** `/upload` saves any file into `static/` and serves it back. An `.html` upload is served as `text/html` from the server's own origin, which is stored cross-site scripting. No size limit, so the disk can be filled. | Uploaded `x.html` → `GET /static/x.html` returned `Content-Type: text/html` | I3, I7 Insecure data transfer and storage |
| SEC-5 | Medium | **Fake detections and telemetry.** `/upload` and `/api/telemetry` rebroadcast whatever they receive to every dashboard. | A POST with `cpu_temp: 999` appeared on a listening dashboard client | I3 |
| SEC-6 | Medium | **CORS reflects any origin** with credentials allowed (`supports_credentials=True`, `resources={r"/*": {"origins": "*"}}`). | Preflight from `http://evil.example` returned `Access-Control-Allow-Origin: http://evil.example` | I9 |
| SEC-7 | Medium | **No encryption.** Plain HTTP and WebSocket. Tailscale encrypts traffic when used, but nothing in the code requires it. | Code review | I7 |
| SEC-8 | Medium | **No login on the dashboard.** Anyone who reaches it sees yard images and can press the override buttons. Images can contain people (the committed config detects people). | Code review | I1 (no credentials at all), I6 Insufficient privacy protection |
| SEC-9 | Low | **No input validation.** A non-numeric `confidence` crashes `/upload` with a 500, and the Pi's `requests.post` calls have no timeout. | `confidence=abc` → HTTP 500 | I3 |

## Recommended fixes, in order

| # | Fix | Closes | Effort |
|---|---|---|---|
| 1 | Turn off debug mode; run Flask-SocketIO under a production server | SEC-3 | Minutes |
| 2 | Give each Pi a secret token; require it (header) on `/upload`, `/api/telemetry` and the SSE stream; reject unknown `pi_id`s | SEC-2, SEC-4, SEC-5 | Hours |
| 3 | Restrict CORS and `cors_allowed_origins` to the dashboard's address | SEC-1 (browser path), SEC-6 | Minutes |
| 4 | Add a dashboard login, and check the session in the Socket.IO `connect` handler before accepting `manual_trigger` | SEC-1, SEC-8 | A day |
| 5 | Accept only PNG/JPEG, cap upload size (`MAX_CONTENT_LENGTH`), name files on the server, validate `confidence` | SEC-4, SEC-9 | Hours |
| 6 | Add a cooldown on manual horn triggers as a safety interlock | SEC-1 impact | Hours |
| 7 | Require TLS or Tailscale for any remote access; document it in the setup guide | SEC-7 | Hours |

These line up with the [NIST IR 8259A](https://csrc.nist.gov/pubs/ir/8259/a/final) core baseline for IoT devices. Fix 2 provides **Device Identification**, fixes 1, 3 and 4 provide **Logical Access to Interfaces** and **Device Configuration**, and fixes 5 and 7 provide **Data Protection**.

## Sources

- Flask, [Debugging Application Errors](https://flask.palletsprojects.com/en/stable/debugging/)
- OWASP, [Testing WebSockets (WSTG)](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets)
- OWASP IoT Top 10 2018, as listed in [TechWell](https://www.techwell.com/techwell-insights/2019/01/owasp-releases-latest-top-10-iot-vulnerabilities)
- Fagan et al., [NISTIR 8259A: IoT Device Cybersecurity Capability Core Baseline](https://csrc.nist.gov/pubs/ir/8259/a/final), NIST, May 2020
