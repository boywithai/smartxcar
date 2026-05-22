import os
import random
import time

import socketio
from dotenv import load_dotenv


load_dotenv()

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:5000")
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN")
CAR_ID = os.getenv("CAR_ID", "car-01")

if not DEVICE_TOKEN:
    raise RuntimeError("DEVICE_TOKEN must be set in .env")

sio = socketio.Client(reconnection=True)


def send_command_result(command_type, command, status="executed", message="Komut mock araçta işlendi."):
    sio.emit(
        "command_result",
        {
            "command_type": command_type,
            "command": str(command),
            "status": status,
            "message": message,
        },
    )


@sio.event
def connect():
    print(f"Connected to {SERVER_URL} as mock Pi for {CAR_ID}")


@sio.event
def disconnect():
    print("Disconnected from server")


@sio.on("drive_command")
def on_drive_command(data):
    command = data.get("command") if isinstance(data, dict) else None
    print(f"[DRIVE] {command} received")
    send_command_result("drive", command)


@sio.on("accessory_command")
def on_accessory_command(data):
    accessory = data.get("accessory") if isinstance(data, dict) else None
    state = data.get("state") if isinstance(data, dict) else None
    print(f"[ACCESSORY] {accessory}={state} received")
    send_command_result("accessory", f"{accessory}:{state}")


def telemetry_loop():
    raining = False
    while True:
        if not sio.connected:
            time.sleep(1)
            continue

        if random.random() < 0.2:
            raining = not raining

        sio.emit(
            "telemetry_update",
            {
                "distance_cm": round(random.uniform(20.0, 100.0), 1),
                "raining": raining,
            },
        )
        time.sleep(2)


if __name__ == "__main__":
    sio.connect(
        SERVER_URL,
        auth={"role": "raspi", "car_id": CAR_ID, "device_token": DEVICE_TOKEN},
    )
    telemetry_loop()
