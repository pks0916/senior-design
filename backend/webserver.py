from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit
import queue as queue_module
import requests
import time
import logging
import threading
import json
import pandas as pd
import os
from filelock import FileLock, Timeout
from werkzeug.utils import secure_filename


pi_command_queue = {}
pi_command_queue_lock = threading.RLock()

app = Flask(__name__) # create flask instance
CORS(app, supports_credentials=True, origins=["http://localhost:5173"], resources={r"/*": {"origins": "*"}}) # enable CORS for all routes
# Use threading so the server works without eventlet/gevent installed.
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@socketio.on('connect')
def handle_connect():
    print('Client connected')

    try:
        csv_path = os.path.join(BASE_DIR, "images.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if len(df) > 0:
                latest_image = df.iloc[-1]
                filename = latest_image['filename']
                # Use consistent relative URL format
                image_url = f'http://localhost:5000/{filename}'
                confidence = latest_image['confidence']
                animal = filename.split("/")[1].split("-")[0] if "/" in filename else filename.split("-")[0]
                
                payload = {
                    'image_url': image_url,
                    'animal': animal,
                    'confidence': float(confidence),
                    'deterrent': 'Horn + Lights'
                }
                emit('detection_update', payload)
    except Exception as e:
        print(f"Error sending initial data: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')



@app.route('/api/manual_commands/stream', methods=['GET'])
def stream_manual_commands():
    pi_id = request.args.get('pi_id', 'default_pi')

    queue = queue_module.Queue()
    
    with pi_command_queue_lock:
        pi_command_queue[pi_id] = queue

    print(f"Pi '{pi_id}' connected for manual commands")

    def event_generator():
        try:
            while True:
                try:
                    command = queue.get(timeout=30)
                    yield f"data: {json.dumps(command)}\n\n"
                except queue_module.Empty:
                    yield f": keep-alive\n\n"
        except GeneratorExit:
            with pi_command_queue_lock:
                if pi_id in pi_command_queue:
                    del pi_command_queue[pi_id]
            print(f"Pi '{pi_id}' disconnected from manual commands")

    response = Response(event_generator(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@socketio.on('manual_trigger')
def handle_manual_trigger(data):
    device = (data or {}).get('device')
    action = (data or {}).get('action')

    if device not in {'horn', 'light'}:
        emit('manual_trigger_result', {'ok': False, 'message': 'Invalid device'})
        return

    if action not in {'toggle', 'test'}:
        emit('manual_trigger_result', {'ok': False, 'message': 'Invalid action'})
        return

    try:
        command = {
            'device': device,
            'action': action,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }

        with pi_command_queue_lock:
            for pi_id, queue in list(pi_command_queue.items()):
                try:
                    queue.put(command, block=False)
                    print(f"Queued {device} {action} to Pi '{pi_id}'")
                except Exception as e:
                    print(f"Error queuing command for Pi '{pi_id}': {e}")

        emit('manual_trigger_result', {
            'ok': True,
            'device': device,
            'action': action,
            'message': f'Queued {device} {action} to {len(pi_command_queue)} Pi(s)'
        })

    except Exception as e:
        emit('manual_trigger_result', {'ok': False, 'message': str(e)})

@app.route('/api/telemetry', methods=['POST'])
def telemetry():
    data = request.get_json()
    print(f"Received telemetry: {data}")

    socketio.emit('telemetry_update', data)

    response = {
        "message": "Telemetry data received successfully",
        "data": data
    }
    return jsonify(response), 200

import hashlib
from sqlite_store import save_detection, detection_exists

@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    animal = request.form['animal']
    timestamp = request.form['timestamp']
    filename = secure_filename(request.form['filename'])
    confidence = request.form['confidence']

    # if animal.lower() != "bear":
    #     return jsonify({"message": "Only bear detections are stored"}), 200

    filepath = os.path.join("static", filename)
    event_identity = f'{animal}|{timestamp}|{filename}'
    event_key = hashlib.sha256(event_identity.encode('utf-8')).hexdigest()

    # Reject duplicate events before touching the image
    if detection_exists(event_key):
        return jsonify({"message": "Duplicate detection ignored"}), 200

    # Never overwrite an existing image filename
    try:
        with open(filepath, "xb") as destination:
            file.save(destination)
    except FileExistsError:
        return jsonify({"error": "Image filename already exists"}), 409

    if not save_detection(event_key, animal, timestamp, float(confidence), filepath):
        return jsonify({"message": "Duplicate detection ignored"}), 200
    
    with open('detection.txt', 'a') as f:
        f.write(f"{animal} Detected: {timestamp} (Confidence: {confidence})\n")
    
    try:
        imgs = pd.read_csv("images.csv")
    except FileNotFoundError:
        imgs = pd.DataFrame(columns=["filename", "confidence"])

    imgs = pd.concat([imgs, pd.DataFrame([[filepath, confidence]], columns=["filename", "confidence"])], ignore_index=True)

    image_limit = 10
    if len(imgs) > image_limit:
        imgs = imgs.iloc[-image_limit:]
    
    imgs.to_csv("images.csv", index=False)



    # Use consistent absolute URL format
    payload = {
        'image_url': f'http://localhost:5000/static/{os.path.basename(filename)}',
        'animal': animal,
        'confidence': float(confidence),
        'deterrent': 'Horn + Lights'
    }

    socketio.emit('detection_update', payload)

    response = {
        "message": "Bear image uploaded successfully",
        "animal": animal,
        "timestamp": timestamp,
        "filename": filename,
        "confidence": confidence
    }
    return jsonify(response), 201


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Serve actual image files to frontend
@app.route('/api/detection', methods=['GET'])
@cross_origin()
def serve_image():
    try:
        df = pd.read_csv("./images.csv")
        latest_image = df.iloc[-1]
        filename = latest_image['filename']
        image_url = request.host_url + filename.replace(chr(92), "/")
        confidence = latest_image['confidence']

        animal = os.path.basename(latest_image['filename'].replace("\\", "/")).split("-")[0]
        payload = {
            'image': image_url,
            'threat': animal,
            'confidence': confidence,
            'deterrentActive': 'Horn + Lights'
        }

        return jsonify(payload), 200
    except Exception as e:
        print(f"Error serving image: {e}")
        return jsonify({"error": str(e)}), 404



if __name__ == '__main__':
    socketio.run(app=app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
