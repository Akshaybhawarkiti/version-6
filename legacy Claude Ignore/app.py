"""
app.py — Browser HMI backend for the EPE Grinding Software.

This file is ONLY a new frontend bridge. It does not talk to hal.py or
planner.py directly, and it does not change any MQTT topic, payload,
JSON key, or command string. It reproduces exactly what the existing
Tkinter UI (new_ui.py) already publishes to MQTT, and forwards
`planner_alerts` messages to the browser over Server-Sent Events (SSE)
so the operator sees them live without reloading the page.

Architecture:

    Browser  <-- HTTP/SSE -->  app.py (this file)  <-- MQTT -->  planner.py --> hal.py --> FluidNC
"""

import json
import queue
import threading

from flask import Flask, Response, jsonify, request, render_template, send_from_directory
import paho.mqtt.client as mqtt

# ==========================================================
# CONFIGURATION
# (edit these to match your setup / assets)
# ==========================================================

BROKER = "localhost"
PORT = 1883

UI_INPUT_TOPIC = "ui_input"
PLANNER_ALERTS_TOPIC = "planner_alerts"

# Filenames inside the assets/ folder. Change these to swap the
# background image or company logo without touching any other code.
BACKGROUND_IMAGE = "background.png"
COMPANY_LOGO = "logo.png"

ASSETS_DIR = "assets"

# ==========================================================
# FLASK APP 
# ==========================================================

app = Flask(__name__)

# ==========================================================
# MQTT BRIDGE
# ==========================================================
#
# One shared MQTT client, connected once at process start and driven by
# its own background network thread (client.loop_start()) so it never
# blocks Flask's request handling.
#
# Incoming planner_alerts messages are fanned out to every currently
# connected browser tab via a per-client queue, and also kept in a
# small rolling history so a tab that opens the SSE stream late still
# sees recent alerts.

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

_alert_subscribers = []
_alert_subscribers_lock = threading.Lock()

_alert_history = []
_ALERT_HISTORY_MAX = 50
_alert_history_lock = threading.Lock()

mqtt_status = {"connected": False}


def _broadcast_alert(message: str) -> None:
    with _alert_history_lock:
        _alert_history.append(message)
        if len(_alert_history) > _ALERT_HISTORY_MAX:
            del _alert_history[0]

    with _alert_subscribers_lock:
        subscribers = list(_alert_subscribers)

    for q in subscribers:
        q.put(message)


def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected to MQTT Broker")
    mqtt_status["connected"] = True
    client.subscribe(PLANNER_ALERTS_TOPIC)


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    mqtt_status["connected"] = False


def on_message(client, userdata, msg):
    if msg.topic == PLANNER_ALERTS_TOPIC:
        message = msg.payload.decode()

        if not message.strip():
            return  # ignore empty/blank payloads (e.g. retained-clear messages)

        _broadcast_alert(message)


mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message

mqtt_client.connect(BROKER, PORT)
mqtt_client.loop_start()


def publish_ui_input(payload: str) -> None:
    """Publish a raw string payload to ui_input — identical to what
    the Tkinter UI's client.publish(UI_INPUT_TOPIC, payload) does."""
    mqtt_client.publish(UI_INPUT_TOPIC, payload)
    print(f"MQTT -> ui_input : {payload}")


# ==========================================================
# ROUTES — PAGE
# ==========================================================

@app.route("/")
def index():
    return render_template(
        "index.html",
        background_image=BACKGROUND_IMAGE,
        company_logo=COMPANY_LOGO,
    )


@app.route(f"/{ASSETS_DIR}/<path:filename>")
def assets(filename):
    return send_from_directory(ASSETS_DIR, filename)


# ==========================================================
# ROUTES — API
# ==========================================================

@app.route("/api/command", methods=["POST"])
def api_command():
    """Generic passthrough for every simple string command the old
    Tkinter UI sends: execute_next, stop, home, holder_home, recover,
    block, A+/A-/B+/B-/C+/C-, P0_ON/P0_OFF/P1_ON/P1_OFF/P2_ON/P2_OFF.
    """
    data = request.get_json(silent=True) or {}
    payload = data.get("payload")

    if not payload or not isinstance(payload, str):
        return jsonify({"ok": False, "error": "missing 'payload' string"}), 400

    publish_ui_input(payload)
    return jsonify({"ok": True, "payload": payload})


@app.route("/api/start", methods=["POST"])
def api_start():
    """Sends the exact same JSON structure the Tkinter Start button sends."""
    data = request.get_json(silent=True) or {}

    try:
        payload = {
            "reciprocation_distance": float(data["reciprocation_distance"]),
            "reciprocation_repetitions": int(data["reciprocation_repetitions"]),
            "vertical_step": float(data["vertical_step"]),
            "total_vertical_travel": float(data["total_vertical_travel"]),
            "grinding_feedrate": float(data["grinding_feedrate"]),

            "cylinder_diameter": float(data["cylinder_diameter"]),
            "slag_depth": float(data["slag_depth"]),
            "hole_diameter": float(data["hole_diameter"]),
            "disk_thickness": float(data["disk_thickness"]),
            "cylinder_thickness": float(data["cylinder_thickness"]),
            "slag_thickness": float(data["slag_thickness"]),

            "tool_diameter": float(data["tool_diameter"]),
            "tool_length": float(data["tool_length"]),
            "probed_length": float(data["probed_length"]),

            "feedrate": float(data["feedrate"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"ok": False, "error": f"invalid parameters: {exc}"}), 400

    mqtt_client.publish(UI_INPUT_TOPIC, json.dumps(payload))
    print("MQTT -> ui_input")
    print(json.dumps(payload, indent=4))

    return jsonify({"ok": True})


@app.route("/api/status")
def api_status():
    return jsonify({"mqtt_connected": mqtt_status["connected"]})


@app.route("/api/alerts")
def api_alerts():
    """Server-Sent Events stream of planner_alerts messages."""

    def stream():
        q = queue.Queue()

        with _alert_subscribers_lock:
            _alert_subscribers.append(q)

        try:
            # Replay recent history so a tab opened late still has context.
            with _alert_history_lock:
                backlog = list(_alert_history)

            for message in backlog:
                yield f"data: {json.dumps(message)}\n\n"

            while True:
                message = q.get()
                yield f"data: {json.dumps(message)}\n\n"
        finally:
            with _alert_subscribers_lock:
                if q in _alert_subscribers:
                    _alert_subscribers.remove(q)

    return Response(stream(), mimetype="text/event-stream")


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    finally:
        mqtt_client.loop_stop()