from __future__ import annotations

import argparse
import json
import urllib.request
from urllib.parse import quote

from websockets.sync.client import connect


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    origin = "/".join(base_url.split("/")[:3])

    with urllib.request.urlopen(f"{base_url}/api/ready", timeout=10) as response:
        ready = json.loads(response.read())
    print(f"ready={ready.get('ready')}")

    request = urllib.request.Request(
        f"{base_url}/api/face/sessions",
        data=b"{}",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Origin": origin,
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        session = json.loads(response.read())

    websocket_url = (
        base_url.replace("https://", "wss://").replace("http://", "ws://")
        + f"/ws/face?session_id={quote(session['sessionId'])}"
    )
    with connect(websocket_url, origin=origin, open_timeout=10) as websocket:
        event = json.loads(websocket.recv(timeout=10))
    print(f"websocket={event['type']} action={event.get('action')}")


if __name__ == "__main__":
    main()
