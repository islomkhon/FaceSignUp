from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import httpx
import numpy as np
from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.face_engine import face_engine

DEFAULT_BASE_URL = "http://127.0.0.1:5173"


def encode(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 76])
    if not ok:
        raise RuntimeError("Could not encode the diagnostic image.")
    return encoded.tobytes()


def tint(image: np.ndarray, phase: str) -> np.ndarray:
    factors = {
        "ambient": (1.0, 1.0, 1.0),
        "red": (0.55, 0.65, 1.45),
        "green": (0.55, 1.45, 0.65),
        "blue": (1.45, 0.65, 0.55),
        "white": (1.55, 1.55, 1.55),
    }
    blue, green, red = factors[phase]
    adjusted = image.astype(np.float32)
    adjusted[:, :, 0] *= blue
    adjusted[:, :, 1] *= green
    adjusted[:, :, 2] *= red
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def crop_to_single_face(image_path: Path) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f"Could not read image: {image_path}")
    detection = face_engine.inspect_frame(encode(image))
    x, y, width, height = detection.bbox
    margin = int(max(width, height) * 0.65)
    x1 = max(0, x - margin)
    y1 = max(0, y - margin)
    x2 = min(image.shape[1], x + width + margin)
    y2 = min(image.shape[0], y + height + margin)
    crop = image[y1:y2, x1:x2]
    face_engine.extract_embedding(encode(crop))
    return crop


def receive_until(websocket, event_type: str, timeout: float = 10) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        event = json.loads(websocket.recv(timeout=max(0.1, deadline - time.time())))
        print(f"event={event['type']} step={event.get('step')}")
        if event["type"] == event_type:
            return event
    raise TimeoutError(f"Did not receive {event_type}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument(
        "--weak-lighting",
        action="store_true",
        help="Send unchanged frames to exercise the movement-liveness fallback.",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    image = crop_to_single_face(args.image)
    base_url = args.base_url.rstrip("/")
    origin = "/".join(base_url.split("/")[:3])
    session_response = httpx.post(
        f"{base_url}/api/face/sessions",
        headers={"Origin": origin},
        timeout=10,
    )
    session_response.raise_for_status()
    session = session_response.json()
    action = session["challenge"]["action"]
    print(f"session action={action}")

    websocket_base = base_url.replace("https://", "wss://").replace("http://", "ws://")
    uri = f"{websocket_base}/ws/face?session_id={session['sessionId']}"
    with connect(uri, origin=origin, open_timeout=10) as websocket:
        ready = json.loads(websocket.recv(timeout=10))
        print(f"event={ready['type']} action={ready.get('action')}")
        for _index in range(5):
            websocket.send(encode(image))
            time.sleep(0.11)
        websocket.send(
            json.dumps(
                {
                    "type": "action_detected",
                    "action": action,
                    "confidence": 0.95,
                }
            )
        )
        passed = receive_until(websocket, "action_passed")
        phases = passed["lighting"]["phases"]
        sequence_started = time.perf_counter()
        elapsed_plan = 0.0
        weak_scale = {
            "ambient": 1.0,
            "red": 0.88,
            "green": 1.03,
            "blue": 0.94,
            "white": 1.08,
        }
        for phase in phases:
            elapsed_plan += phase["durationMs"]
            phase_end = sequence_started + elapsed_plan / 1000
            while time.perf_counter() < phase_end:
                if args.weak_lighting:
                    frame = np.clip(
                        image.astype(np.float32) * weak_scale[phase["name"]],
                        0,
                        255,
                    ).astype(np.uint8)
                else:
                    frame = tint(image, phase["name"])
                websocket.send(encode(frame))
                time.sleep(0.11)

        websocket.send(json.dumps({"type": "lighting_complete"}))
        step_three = receive_until(websocket, "step_started", timeout=10)
        print(
            f"lighting result lumaRange={step_three['lighting']['lumaRange']} "
            f"correctColorOrder={step_three['lighting']['correctColorOrder']} "
            f"counts={step_three['lighting']['counts']} "
            f"fallback={step_three['lighting'].get('fallbackUsed', 'none')}"
        )

        repair_started = time.perf_counter()
        while time.perf_counter() - repair_started < 0.8:
            websocket.send(encode(image))
            time.sleep(0.11)
        websocket.send(json.dumps({"type": "capture_final"}))

        deadline = time.time() + 15
        while time.time() < deadline:
            event = json.loads(websocket.recv(timeout=deadline - time.time()))
            print(f"event={event['type']} step={event.get('step')}")
            if event["type"] in {"face_match", "face_no_match", "scan_failed"}:
                print(json.dumps(event, indent=2))
                return
        raise TimeoutError("Final recognition result was not received.")


if __name__ == "__main__":
    main()
