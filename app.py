import math
import os
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, disconnect, emit, join_room


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN")
CAR_ID = os.getenv("CAR_ID", "car-01")
APP_ENV = os.getenv("APP_ENV", "development")

if not SECRET_KEY or not ADMIN_PASSWORD or not DEVICE_TOKEN:
    raise RuntimeError("SECRET_KEY, ADMIN_PASSWORD and DEVICE_TOKEN must be set in .env")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = APP_ENV == "production"

socketio = SocketIO(app, async_mode="threading")

active_pi_sid = None
dashboard_sids = set()

VALID_DRIVE_COMMANDS = {"forward", "backward", "left", "right", "stop"}
VALID_ACCESSORY_STATES = {
    "horn": {"on", "off"},
    "headlights": {"on", "off"},
    "flash": {"trigger"},
    "wiper": {0, 1, 2, 3},
}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def car_online():
    return active_pi_sid is not None


def emit_car_status():
    socketio.emit(
        "car_status",
        {"car_id": CAR_ID, "online": car_online()},
        room="dashboards",
    )


def relay_safe_state_if_online():
    if active_pi_sid:
        socketio.emit("drive_command", {"command": "stop"}, to=active_pi_sid)
        socketio.emit("accessory_command", {"accessory": "horn", "state": "off"}, to=active_pi_sid)
        socketio.emit("accessory_command", {"accessory": "wiper", "state": 0}, to=active_pi_sid)


def is_authenticated_dashboard():
    return bool(session.get("logged_in")) and request.sid in dashboard_sids


def is_active_pi():
    return active_pi_sid == request.sid


def validate_drive_payload(payload):
    if not isinstance(payload, dict):
        return None
    command = payload.get("command")
    if command not in VALID_DRIVE_COMMANDS:
        return None
    return {"command": command}


def validate_accessory_payload(payload):
    if not isinstance(payload, dict):
        return None

    accessory = payload.get("accessory")
    state = payload.get("state")
    allowed_states = VALID_ACCESSORY_STATES.get(accessory)

    if allowed_states is None or state not in allowed_states:
        return None

    return {"accessory": accessory, "state": state}


@app.route("/")
@login_required
def index():
    return render_template("index.html", car_id=CAR_ID)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session.clear()
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Geçersiz parola."

    return render_template("login.html", error=error)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    relay_safe_state_if_online()
    session.clear()
    return redirect(url_for("login"))


@socketio.on("connect")
def handle_connect(auth):
    global active_pi_sid

    auth = auth or {}
    if auth.get("role") == "raspi":
        if (
            auth.get("car_id") != CAR_ID
            or not auth.get("device_token")
            or auth.get("device_token") != DEVICE_TOKEN
        ):
            return False

        if active_pi_sid and active_pi_sid != request.sid:
            relay_safe_state_if_online()
            disconnect(active_pi_sid)

        active_pi_sid = request.sid
        emit_car_status()
        return True

    if session.get("logged_in"):
        dashboard_sids.add(request.sid)
        join_room("dashboards")
        emit(
            "car_status",
            {"car_id": CAR_ID, "online": car_online()},
        )
        return True

    return False


@socketio.on("disconnect")
def handle_disconnect():
    global active_pi_sid

    if request.sid in dashboard_sids:
        dashboard_sids.discard(request.sid)
        relay_safe_state_if_online()
        return

    if request.sid == active_pi_sid:
        active_pi_sid = None
        emit_car_status()


@socketio.on("drive_command")
def handle_drive_command(payload):
    if not is_authenticated_dashboard():
        return

    command_payload = validate_drive_payload(payload)
    if not command_payload:
        emit("status_message", {"message": "Geçersiz hareket komutu."})
        return

    if not active_pi_sid:
        emit("status_message", {"message": "Araç çevrimdışı. Komut gönderilmedi."})
        return

    socketio.emit("drive_command", command_payload, to=active_pi_sid)


@socketio.on("accessory_command")
def handle_accessory_command(payload):
    if not is_authenticated_dashboard():
        return

    accessory_payload = validate_accessory_payload(payload)
    if not accessory_payload:
        emit("status_message", {"message": "Geçersiz aksesuar komutu."})
        return

    if not active_pi_sid:
        emit("status_message", {"message": "Araç çevrimdışı. Komut gönderilmedi."})
        return

    socketio.emit("accessory_command", accessory_payload, to=active_pi_sid)


@socketio.on("telemetry_update")
def handle_telemetry_update(payload):
    if not is_active_pi() or not isinstance(payload, dict):
        return

    distance_cm = payload.get("distance_cm")
    raining = payload.get("raining")

    if (
        isinstance(distance_cm, bool)
        or not isinstance(distance_cm, (int, float))
        or not math.isfinite(distance_cm)
        or distance_cm < 0
        or isinstance(raining, bool) is False
    ):
        return

    socketio.emit(
        "telemetry_update",
        {"distance_cm": float(distance_cm), "raining": raining},
        room="dashboards",
    )


@socketio.on("command_result")
def handle_command_result(payload):
    if not is_active_pi() or not isinstance(payload, dict):
        return

    command_type = payload.get("command_type")
    command = payload.get("command")
    status = payload.get("status")
    message = payload.get("message")

    if (
        command_type not in {"drive", "accessory"}
        or status not in {"executed", "rejected"}
        or not isinstance(command, str)
        or not isinstance(message, str)
    ):
        return

    socketio.emit(
        "command_result",
        {
            "command_type": command_type,
            "command": command,
            "status": status,
            "message": message,
        },
        room="dashboards",
    )


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=False, allow_unsafe_werkzeug=True)
