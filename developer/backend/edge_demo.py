import argparse
import json
import time
from pathlib import Path

import cv2
from ultralytics import YOLO


DEFAULT_MODEL = "yolo11n.pt"
DEFAULT_VIDEO = "videos/MEDIUM.MOV"
DEFAULT_STATE_FILE = "runtime_state.json"


def decide_occupancy(person_count, medium_threshold=3, high_threshold=10):
    if person_count >= high_threshold:
        return "HIGH"
    if person_count >= medium_threshold:
        return "MEDIUM"
    return "LOW"


def decide_ac(occupancy):
    if occupancy == "HIGH":
        return {"state": "ON", "temperature_c": 20}
    if occupancy == "MEDIUM":
        return {"state": "ON", "temperature_c": 24}
    return {"state": "OFF", "temperature_c": None}


def write_state(state_path, state):
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def draw_overlay(frame, person_count, occupancy, ac_state, ac_runtime_sec):
    color = (0, 200, 0)
    if occupancy == "MEDIUM":
        color = (0, 180, 255)
    elif occupancy == "HIGH":
        color = (0, 0, 255)

    lines = [
        f"People: {person_count}",
        f"Occupancy: {occupancy}",
        f"AC: {ac_state['state']}",
        f"Temp: {ac_state['temperature_c'] if ac_state['temperature_c'] else '--'} C",
        f"AC runtime: {int(ac_runtime_sec)} sec",
    ]

    x, y = 20, 35
    for line in lines:
        cv2.putText(frame, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        y += 34


def open_video_source(video_path, use_camera):
    source = 0 if use_camera else str(video_path)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")
    return cap


def run_demo(args):
    model_path = Path(args.model)
    video_path = Path(args.video)
    state_path = Path(args.state_file)

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not args.camera and not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    model = YOLO(str(model_path))
    cap = open_video_source(video_path, args.camera)

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    frame_no = 0
    ac_runtime_sec = 0.0
    last_ac_state = "OFF"
    last_change_time = time.strftime("%Y-%m-%d %H:%M:%S")
    previous_frame_time = time.monotonic()

    print("Starting edge demo. Press 'q' in the video window to stop.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        now = time.monotonic()
        elapsed = now - previous_frame_time if args.camera else 1.0 / fps
        previous_frame_time = now

        results = model(frame, conf=args.confidence, verbose=False)
        person_boxes = []

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            if class_id == 0:
                person_boxes.append(box)
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 220, 80), 2)

        person_count = len(person_boxes)
        occupancy = decide_occupancy(
            person_count,
            medium_threshold=args.medium_threshold,
            high_threshold=args.high_threshold,
        )
        ac_state = decide_ac(occupancy)

        if ac_state["state"] == "ON":
            ac_runtime_sec += elapsed

        if ac_state["state"] != last_ac_state:
            last_change_time = time.strftime("%Y-%m-%d %H:%M:%S")
            last_ac_state = ac_state["state"]

        state = {
            "frame": frame_no,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "person_count": person_count,
            "occupancy": occupancy,
            "ac_state": ac_state["state"],
            "temperature_c": ac_state["temperature_c"],
            "last_ac_change": last_change_time,
            "ac_runtime_seconds": round(ac_runtime_sec, 2),
        }
        write_state(state_path, state)

        draw_overlay(frame, person_count, occupancy, ac_state, ac_runtime_sec)

        if writer:
            writer.write(frame)

        print(
            f"frame={frame_no} people={person_count} "
            f"occupancy={occupancy} ac={ac_state['state']} "
            f"temp={ac_state['temperature_c']}"
        )

        if args.display:
            cv2.imshow("Smart Classroom Edge AI Demo", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        frame_no += 1

        if args.max_frames and frame_no >= args.max_frames:
            break

    cap.release()
    if writer:
        writer.release()
    if args.display:
        cv2.destroyAllWindows()

    print(f"Done. Latest backend state written to: {state_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Smart Classroom Edge AI backend demo: YOLO person count -> occupancy -> AC decision."
    )
    parser.add_argument("--video", default=DEFAULT_VIDEO, help="Path to a classroom video.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Path to YOLO model weights.")
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE, help="JSON state output path.")
    parser.add_argument("--output", default=None, help="Optional annotated MP4 output path.")
    parser.add_argument("--confidence", type=float, default=0.35, help="YOLO confidence threshold.")
    parser.add_argument("--medium-threshold", type=int, default=3, help="People count for MEDIUM occupancy.")
    parser.add_argument("--high-threshold", type=int, default=10, help="People count for HIGH occupancy.")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after this many frames. 0 means full video.")
    parser.add_argument("--camera", action="store_true", help="Use webcam instead of a video file.")
    parser.add_argument("--display", action="store_true", help="Show live video window.")
    return parser.parse_args()


if __name__ == "__main__":
    run_demo(parse_args())
