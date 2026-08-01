import argparse
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np


HOST = "127.0.0.1"
PORT = 8090
DEFAULT_MODEL_URL = "http://127.0.0.1:8080/count"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = PROJECT_ROOT / "backend_state.json"

state_lock = threading.Lock()
latest_frame_jpeg = None

LEVELS = ("LOW", "MEDIUM", "HIGH")
DEFAULT_POLICY = {
    "LOW": {"min": 0, "max": 2, "ac_state": "OFF", "temperature_c": None},
    "MEDIUM": {"min": 3, "max": 9, "ac_state": "ON", "temperature_c": 24},
    "HIGH": {"min": 10, "max": None, "ac_state": "ON", "temperature_c": 20},
}


def clone_policy(policy=None):
    return json.loads(json.dumps(policy or DEFAULT_POLICY))


latest_state = {
    "status": "waiting",
    "timestamp": None,
    "source": None,
    "frame": 0,
    "person_count": 0,
    "occupancy": "LOW",
    "ac_state": "OFF",
    "temperature_c": None,
    "desired_ac_state": "OFF",
    "desired_temperature_c": None,
    "pending_ac_state": None,
    "pending_temperature_c": None,
    "pending_since": None,
    "pending_seconds_remaining": 0,
    "ac_on_delay_seconds": 5,
    "ac_off_delay_seconds": 10,
    "medium_threshold": 3,
    "high_threshold": 10,
    "policy": clone_policy(),
    "ac_control_mode": "AUTO",
    "last_ac_change": None,
    "ac_runtime_seconds": 0.0,
    "timeline": [],
}


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
DASHBOARD_PATH = FRONTEND_DIR / "dashboard.html"


def load_dashboard_html():
    return DASHBOARD_PATH.read_text(encoding="utf-8")



def policy_from_thresholds(medium_threshold=3, high_threshold=10):
    medium_threshold = int(medium_threshold)
    high_threshold = int(high_threshold)
    if medium_threshold < 1:
        medium_threshold = 1
    if high_threshold <= medium_threshold:
        high_threshold = medium_threshold + 1

    policy = clone_policy()
    policy["LOW"]["min"] = 0
    policy["LOW"]["max"] = medium_threshold - 1
    policy["MEDIUM"]["min"] = medium_threshold
    policy["MEDIUM"]["max"] = high_threshold - 1
    policy["HIGH"]["min"] = high_threshold
    policy["HIGH"]["max"] = None
    return policy


def normalize_policy(policy):
    defaults = clone_policy()
    normalized = {}

    for level in LEVELS:
        source = policy.get(level, {}) if isinstance(policy, dict) else {}
        fallback = defaults[level]
        min_count = int(source.get("min", fallback["min"]))
        raw_max = source.get("max", fallback["max"])
        max_count = None if raw_max in (None, "") else int(raw_max)
        ac_state = str(source.get("ac_state", fallback["ac_state"])).upper()
        if ac_state not in ("ON", "OFF"):
            raise ValueError(f"{level} AC state must be ON or OFF.")
        raw_temperature = source.get("temperature_c", fallback["temperature_c"])
        temperature = None if ac_state == "OFF" else int(raw_temperature)

        if min_count < 0:
            raise ValueError(f"{level} min must be 0 or higher.")
        if max_count is not None and max_count < min_count:
            raise ValueError(f"{level} max must be higher than or equal to min.")
        if temperature is not None and not 16 <= temperature <= 30:
            raise ValueError(f"{level} temperature must be between 16 C and 30 C.")

        normalized[level] = {
            "min": min_count,
            "max": max_count,
            "ac_state": ac_state,
            "temperature_c": temperature,
        }

    if normalized["LOW"]["min"] != 0:
        raise ValueError("LOW range must start at 0.")
    if normalized["LOW"]["max"] is None:
        raise ValueError("LOW max is required.")
    if normalized["MEDIUM"]["max"] is None:
        raise ValueError("MEDIUM max is required.")
    if normalized["MEDIUM"]["min"] != normalized["LOW"]["max"] + 1:
        raise ValueError("MEDIUM min must start immediately after LOW max.")
    if normalized["HIGH"]["min"] != normalized["MEDIUM"]["max"] + 1:
        raise ValueError("HIGH min must start immediately after MEDIUM max.")

    return normalized


def decide_occupancy(person_count, medium_threshold=3, high_threshold=10, policy=None):
    policy = normalize_policy(policy or policy_from_thresholds(medium_threshold, high_threshold))
    for level in LEVELS:
        rule = policy[level]
        max_count = rule["max"]
        if person_count >= rule["min"] and (max_count is None or person_count <= max_count):
            return level
    return "HIGH"


def decide_ac(occupancy, policy=None):
    policy = normalize_policy(policy or DEFAULT_POLICY)
    rule = policy[occupancy]
    return {"ac_state": rule["ac_state"], "temperature_c": rule["temperature_c"]}


def encode_dashboard_frame(frame, model_result, person_count, occupancy, ac_decision):
    annotated = frame.copy()
    detections = model_result.get("detections", []) if model_result else []

    if occupancy == "HIGH":
        color = (70, 70, 255)
    elif occupancy == "MEDIUM":
        color = (60, 180, 255)
    else:
        color = (120, 210, 160)

    for detection in detections:
        x1, y1, x2, y2 = [int(v) for v in detection.get("box_xyxy", [0, 0, 0, 0])]
        confidence = detection.get("confidence", 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated,
            f"person {confidence:.2f}",
            (x1, max(24, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    panel_color = (8, 12, 18)
    cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 86), panel_color, -1)
    cv2.putText(
        annotated,
        f"People: {person_count}   Occupancy: {occupancy}",
        (20, 34),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        color,
        2,
    )
    temp = ac_decision["temperature_c"] if ac_decision["temperature_c"] else "--"
    cv2.putText(
        annotated,
        f"AC: {ac_decision['ac_state']}   Temp: {temp} C",
        (20, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        color,
        2,
    )

    ok, encoded = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
    if not ok:
        return None
    return encoded.tobytes()


def call_model_api(model_url, frame, timeout_seconds=90, retries=1):
    ok, encoded = cv2.imencode(".jpg", frame)
    if not ok:
        raise RuntimeError("Could not encode frame as JPEG.")

    payload = encoded.tobytes()
    last_error = None

    for attempt in range(retries + 1):
        request = urllib.request.Request(
            model_url,
            data=payload,
            headers={"Content-Type": "image/jpeg"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (TimeoutError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1)

    raise RuntimeError(
        f"Model API did not respond after {retries + 1} attempt(s). "
        f"Try increasing --sample-seconds or --model-timeout-seconds. Last error: {last_error}"
    )


def update_state(
    person_count,
    source,
    frame_no,
    medium_threshold,
    high_threshold,
    elapsed_seconds,
    ac_on_delay_seconds,
    ac_off_delay_seconds,
    frame=None,
    model_result=None,
    status="running",
):
    global latest_frame_jpeg
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    now = time.time()
    encoded_frame = None

    with state_lock:
        policy = normalize_policy(latest_state.get("policy") or policy_from_thresholds(medium_threshold, high_threshold))
        occupancy = decide_occupancy(person_count, medium_threshold, high_threshold, policy)
        desired_ac_decision = decide_ac(occupancy, policy)
        ac_control_mode = latest_state.get("ac_control_mode", "AUTO")
        if ac_control_mode == "ON":
            desired_ac_decision = {"ac_state": "ON", "temperature_c": desired_ac_decision["temperature_c"] or 24}
        elif ac_control_mode == "OFF":
            desired_ac_decision = {"ac_state": "OFF", "temperature_c": None}
        runtime = float(latest_state["ac_runtime_seconds"])
        current_ac_state = latest_state["ac_state"]
        current_temperature = latest_state["temperature_c"]
        pending_ac_state = latest_state.get("pending_ac_state")
        pending_temperature = latest_state.get("pending_temperature_c")
        pending_since = latest_state.get("pending_since")

        desired_ac_state = desired_ac_decision["ac_state"]
        desired_temperature = desired_ac_decision["temperature_c"]
        target_delay_seconds = (
            ac_off_delay_seconds if desired_ac_state == "OFF" else ac_on_delay_seconds
        )

        desired_matches_current = (
            desired_ac_state == current_ac_state
            and desired_temperature == current_temperature
        )

        if desired_matches_current:
            pending_ac_state = None
            pending_temperature = None
            pending_since = None
            pending_remaining = 0
        else:
            pending_target_changed = (
                pending_ac_state != desired_ac_state
                or pending_temperature != desired_temperature
                or pending_since is None
            )

            if pending_target_changed:
                pending_ac_state = desired_ac_state
                pending_temperature = desired_temperature
                pending_since = now

            elapsed_pending = now - pending_since
            pending_remaining = max(0, target_delay_seconds - elapsed_pending)

            if elapsed_pending >= target_delay_seconds:
                current_ac_state = desired_ac_state
                current_temperature = desired_temperature
                latest_state["last_ac_change"] = timestamp
                pending_ac_state = None
                pending_temperature = None
                pending_since = None
                pending_remaining = 0

        applied_ac_decision = {"ac_state": current_ac_state, "temperature_c": current_temperature}

        if current_ac_state == "ON":
            runtime += max(elapsed_seconds, 0)

        if frame is not None:
            encoded_frame = encode_dashboard_frame(
                frame,
                model_result or {},
                person_count,
                occupancy,
                applied_ac_decision,
            )

        timeline_item = {
            "timestamp": timestamp,
            "person_count": person_count,
            "occupancy": occupancy,
            "ac_state": current_ac_state,
            "temperature_c": current_temperature,
            "desired_ac_state": desired_ac_state,
            "desired_temperature_c": desired_temperature,
            "pending_seconds_remaining": round(pending_remaining, 1),
            "ac_control_mode": ac_control_mode,
        }

        latest_state.update(
            {
                "status": status,
                "timestamp": timestamp,
                "source": source,
                "frame": frame_no,
                "person_count": person_count,
                "occupancy": occupancy,
                "ac_state": current_ac_state,
                "temperature_c": current_temperature,
                "desired_ac_state": desired_ac_state,
                "desired_temperature_c": desired_temperature,
                "pending_ac_state": pending_ac_state,
                "pending_temperature_c": pending_temperature,
                "pending_since": pending_since,
                "pending_seconds_remaining": round(pending_remaining, 1),
                "ac_on_delay_seconds": ac_on_delay_seconds,
                "ac_off_delay_seconds": ac_off_delay_seconds,
                "medium_threshold": policy["MEDIUM"]["min"],
                "high_threshold": policy["HIGH"]["min"],
                "policy": clone_policy(policy),
                "ac_control_mode": ac_control_mode,
                "ac_runtime_seconds": round(runtime, 2),
            }
        )
        latest_state["timeline"].append(timeline_item)
        latest_state["timeline"] = latest_state["timeline"][-100:]

        if encoded_frame is not None:
            latest_frame_jpeg = encoded_frame

        STATE_FILE.write_text(json.dumps(latest_state, indent=2), encoding="utf-8")


def set_session_status(status):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with state_lock:
        latest_state["status"] = status
        latest_state["timestamp"] = timestamp
        STATE_FILE.write_text(json.dumps(latest_state, indent=2), encoding="utf-8")
        return dict(latest_state)


def set_policy(server, policy):
    policy = normalize_policy(policy)
    server.policy = clone_policy(policy)
    server.medium_threshold = policy["MEDIUM"]["min"]
    server.high_threshold = policy["HIGH"]["min"]

    with state_lock:
        latest_state["policy"] = clone_policy(policy)
        person_count = int(latest_state.get("person_count", 0))
        frame_no = int(latest_state.get("frame", 0))
        source = latest_state.get("source") or "policy_update"
        previous_status = latest_state.get("status") or "policy_updated"

    update_state(
        person_count,
        source=source,
        frame_no=frame_no,
        medium_threshold=server.medium_threshold,
        high_threshold=server.high_threshold,
        elapsed_seconds=0,
        ac_on_delay_seconds=server.ac_on_delay_seconds,
        ac_off_delay_seconds=server.ac_off_delay_seconds,
        status=previous_status,
    )

    with state_lock:
        return dict(latest_state)


def set_ac_control(server, mode):
    mode = str(mode or "AUTO").upper()
    if mode not in ("AUTO", "ON", "OFF"):
        raise ValueError("AC control mode must be AUTO, ON, or OFF.")

    with state_lock:
        latest_state["ac_control_mode"] = mode
        person_count = int(latest_state.get("person_count", 0))
        frame_no = int(latest_state.get("frame", 0))
        source = latest_state.get("source") or "manual_ac"
        previous_status = latest_state.get("status") or "manual_ac"

    update_state(
        person_count,
        source=source,
        frame_no=frame_no,
        medium_threshold=server.medium_threshold,
        high_threshold=server.high_threshold,
        elapsed_seconds=0,
        ac_on_delay_seconds=server.ac_on_delay_seconds,
        ac_off_delay_seconds=server.ac_off_delay_seconds,
        status=previous_status,
    )

    with state_lock:
        return dict(latest_state)


def process_video(args):
    video_path = Path(args.video)
    if not video_path.is_absolute():
        video_path = PROJECT_ROOT / video_path
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_interval = max(1, int(fps * args.sample_seconds))
    frame_no = 0
    processed = 0

    print(f"Processing video through backend simulation: {video_path}")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_no % frame_interval == 0:
            try:
                model_result = call_model_api(
                    args.model_url,
                    frame,
                    timeout_seconds=args.model_timeout_seconds,
                    retries=args.model_retries,
                )
                person_count = int(model_result.get("person_count", 0))
                update_state(
                    person_count,
                    source=str(video_path),
                    frame_no=frame_no,
                    medium_threshold=args.medium_threshold,
                    high_threshold=args.high_threshold,
                    elapsed_seconds=args.sample_seconds,
                    ac_on_delay_seconds=args.ac_on_delay_seconds,
                    ac_off_delay_seconds=args.ac_off_delay_seconds,
                    frame=frame,
                    model_result=model_result,
                )
                print(
                    f"frame={frame_no} people={person_count} "
                    f"occupancy={latest_state['occupancy']} ac={latest_state['ac_state']}"
                )
                processed += 1
                if args.playback_delay:
                    time.sleep(args.sample_seconds)
            except Exception as exc:
                print(f"Model/backend processing failed on frame {frame_no}: {exc}")

            if args.max_samples and processed >= args.max_samples:
                break

        frame_no += 1

    cap.release()
    with state_lock:
        latest_state["status"] = "video_complete"
        STATE_FILE.write_text(json.dumps(latest_state, indent=2), encoding="utf-8")

    print("Video processing complete.")


class BackendHandler(BaseHTTPRequestHandler):
    def safe_write(self, body):
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            # Browsers can cancel image requests when the dashboard refreshes quickly.
            pass

    def send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.safe_write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            body = load_dashboard_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/health":
            self.send_json(200, {"status": "ok", "service": "backend_simulation"})
            return

        if path == "/api/state":
            with state_lock:
                self.send_json(200, latest_state)
            return

        if path == "/api/latest-frame.jpg":
            with state_lock:
                frame_bytes = latest_frame_jpeg

            if frame_bytes is None:
                self.send_json(404, {"error": "no_frame_available"})
                return

            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(frame_bytes)))
            self.end_headers()
            self.safe_write(frame_bytes)
            return

        self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/session":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = {}
                if length:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                status = payload.get("status", "stopped")
                self.send_json(200, set_session_status(status))
            except Exception as exc:
                self.send_json(400, {"error": "session_update_failed", "message": str(exc)})
            return

        if path == "/api/policy":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                policy = payload.get("policy", payload)
                self.send_json(200, set_policy(self.server, policy))
            except Exception as exc:
                self.send_json(400, {"error": "policy_update_failed", "message": str(exc)})
            return

        if path == "/api/ac":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(200, set_ac_control(self.server, payload.get("mode", "AUTO")))
            except Exception as exc:
                self.send_json(400, {"error": "ac_control_failed", "message": str(exc)})
            return

        if path != "/api/frame":
            self.send_json(404, {"error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            image_bytes = self.rfile.read(length)
            image_array = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image_array is None:
                raise ValueError("Request body is not a valid image.")

            model_result = call_model_api(
                self.server.model_url,
                image_array,
                timeout_seconds=self.server.model_timeout_seconds,
                retries=self.server.model_retries,
            )
            person_count = int(model_result.get("person_count", 0))
            update_state(
                person_count,
                source="api_frame",
                frame_no=latest_state["frame"] + 1,
                medium_threshold=self.server.medium_threshold,
                high_threshold=self.server.high_threshold,
                elapsed_seconds=1,
                ac_on_delay_seconds=self.server.ac_on_delay_seconds,
                ac_off_delay_seconds=self.server.ac_off_delay_seconds,
                frame=image_array,
                model_result=model_result,
            )
            with state_lock:
                self.send_json(200, latest_state)
        except Exception as exc:
            self.send_json(400, {"error": "frame_processing_failed", "message": str(exc)})

    def log_message(self, format, *args):
        return


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backend AC simulation service that consumes the human-counting model API."
    )
    parser.add_argument("--video", default=None, help="Optional video path for demo processing.")
    parser.add_argument("--model-url", default=DEFAULT_MODEL_URL, help="Human-counting model /count URL.")
    parser.add_argument("--host", default=HOST, help="Backend dashboard host.")
    parser.add_argument("--port", type=int, default=PORT, help="Backend dashboard port.")
    parser.add_argument("--medium-threshold", type=int, default=3, help="People count for MEDIUM occupancy.")
    parser.add_argument("--high-threshold", type=int, default=10, help="People count for HIGH occupancy.")
    parser.add_argument("--ac-on-delay-seconds", type=float, default=5.0, help="Delay before applying AC ON or temperature changes.")
    parser.add_argument("--ac-off-delay-seconds", type=float, default=10.0, help="Delay before applying AC OFF.")
    parser.add_argument("--sample-seconds", type=float, default=0.5, help="Sample video every N seconds.")
    parser.add_argument("--model-timeout-seconds", type=float, default=90.0, help="Wait this long for the model API before failing a frame.")
    parser.add_argument("--model-retries", type=int, default=1, help="Retry model API calls this many times after timeout/network errors.")
    parser.add_argument("--max-samples", type=int, default=0, help="Stop video loop after N samples. 0 means full video.")
    parser.add_argument(
        "--no-playback-delay",
        dest="playback_delay",
        action="store_false",
        help="Process video as fast as possible instead of playing it at demo speed.",
    )
    parser.set_defaults(playback_delay=True)
    return parser.parse_args()


def main():
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), BackendHandler)
    server.model_url = args.model_url
    server.policy = policy_from_thresholds(args.medium_threshold, args.high_threshold)
    server.medium_threshold = server.policy["MEDIUM"]["min"]
    server.high_threshold = server.policy["HIGH"]["min"]
    server.ac_on_delay_seconds = args.ac_on_delay_seconds
    server.ac_off_delay_seconds = args.ac_off_delay_seconds
    server.model_timeout_seconds = args.model_timeout_seconds
    server.model_retries = args.model_retries

    with state_lock:
        latest_state["medium_threshold"] = server.medium_threshold
        latest_state["high_threshold"] = server.high_threshold
        latest_state["policy"] = clone_policy(server.policy)
        latest_state["ac_control_mode"] = "AUTO"
        latest_state["ac_on_delay_seconds"] = args.ac_on_delay_seconds
        latest_state["ac_off_delay_seconds"] = args.ac_off_delay_seconds

    if args.video:
        worker = threading.Thread(target=process_video, args=(args,), daemon=True)
        worker.start()

    print(f"Backend dashboard running at http://{args.host}:{args.port}")
    print(f"Model API: {args.model_url}")
    server.serve_forever()


if __name__ == "__main__":
    main()
