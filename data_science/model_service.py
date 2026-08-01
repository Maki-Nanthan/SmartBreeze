import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8080"))
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "data_science" else SCRIPT_DIR
MODEL_PATH = os.environ.get("MODEL_PATH", str(PROJECT_ROOT / "model" / "best.pt"))
CONFIDENCE = float(os.environ.get("CONFIDENCE", "0.35"))
IMAGE_SIZE = int(os.environ.get("IMAGE_SIZE", "960"))
IOU = float(os.environ.get("IOU", "0.45"))
ENABLE_BOX_FILTER = os.environ.get("ENABLE_BOX_FILTER", "0") == "1"
MIN_BOX_AREA_RATIO = float(os.environ.get("MIN_BOX_AREA_RATIO", "0.004"))
MIN_BOX_HEIGHT_RATIO = float(os.environ.get("MIN_BOX_HEIGHT_RATIO", "0.12"))
CONTAINED_BOX_AREA_RATIO = float(os.environ.get("CONTAINED_BOX_AREA_RATIO", "0.70"))

model = None


def load_model():
    global model
    if model is None:
        model_file = Path(MODEL_PATH)
        if not model_file.exists():
            raise FileNotFoundError(
                f"Model not found at {model_file}. Set MODEL_PATH or copy best.pt into model/best.pt."
            )
        model = YOLO(str(model_file))
    return model


def box_area(box):
    x1, y1, x2, y2 = box["box_xyxy"]
    return max(0, x2 - x1) * max(0, y2 - y1)


def box_center(box):
    x1, y1, x2, y2 = box["box_xyxy"]
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def center_inside(inner_box, outer_box):
    cx, cy = box_center(inner_box)
    x1, y1, x2, y2 = outer_box["box_xyxy"]
    return x1 <= cx <= x2 and y1 <= cy <= y2


def suppress_partial_duplicate_boxes(detections, frame_width, frame_height):
    frame_area = frame_width * frame_height
    filtered = []

    for detection in detections:
        x1, y1, x2, y2 = detection["box_xyxy"]
        width = max(0, x2 - x1)
        height = max(0, y2 - y1)
        area_ratio = (width * height) / frame_area if frame_area else 0
        height_ratio = height / frame_height if frame_height else 0

        if area_ratio < MIN_BOX_AREA_RATIO:
            detection["filtered_reason"] = "box_too_small"
            continue
        if height_ratio < MIN_BOX_HEIGHT_RATIO:
            detection["filtered_reason"] = "box_too_short"
            continue

        filtered.append(detection)

    filtered.sort(key=lambda item: (item["confidence"], box_area(item)), reverse=True)
    kept = []

    for detection in filtered:
        detection_area = box_area(detection)
        is_partial_duplicate = False

        for kept_detection in kept:
            kept_area = box_area(kept_detection)
            if not kept_area:
                continue
            if (
                center_inside(detection, kept_detection)
                and detection_area <= kept_area * CONTAINED_BOX_AREA_RATIO
            ):
                detection["filtered_reason"] = "partial_duplicate"
                is_partial_duplicate = True
                break

        if not is_partial_duplicate:
            kept.append(detection)

    kept.sort(key=lambda item: item["box_xyxy"][0])
    return kept


def count_people(image_bytes):
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Request body is not a valid encoded image.")

    frame_height, frame_width = frame.shape[:2]
    result = load_model()(frame, conf=CONFIDENCE, imgsz=IMAGE_SIZE, iou=IOU, verbose=False)[0]
    raw_detections = []

    for box in result.boxes:
        class_id = int(box.cls[0])
        if class_id != 0:
            continue

        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
        confidence = float(box.conf[0])
        raw_detections.append(
            {
                "class_id": class_id,
                "class_name": "person",
                "confidence": round(confidence, 4),
                "box_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
            }
        )

    if ENABLE_BOX_FILTER:
        detections = suppress_partial_duplicate_boxes(raw_detections, frame_width, frame_height)
    else:
        detections = raw_detections

    return {
        "person_count": len(detections),
        "detections": detections,
        "raw_person_detections": len(raw_detections),
        "model_path": MODEL_PATH,
        "confidence_threshold": CONFIDENCE,
        "image_size": IMAGE_SIZE,
        "iou_threshold": IOU,
        "box_filter_enabled": ENABLE_BOX_FILTER,
        "min_box_area_ratio": MIN_BOX_AREA_RATIO,
        "min_box_height_ratio": MIN_BOX_HEIGHT_RATIO,
        "contained_box_area_ratio": CONTAINED_BOX_AREA_RATIO,
    }


class ModelHandler(BaseHTTPRequestHandler):
    def send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            try:
                load_model()
                self.send_json(200, {"status": "ok", "model_path": MODEL_PATH})
            except Exception as exc:
                self.send_json(503, {"status": "error", "message": str(exc)})
            return

        self.send_json(
            404,
            {
                "error": "not_found",
                "usage": "POST a raw JPEG/PNG image body to /count",
            },
        )

    def do_POST(self):
        if self.path != "/count":
            self.send_json(404, {"error": "not_found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            image_bytes = self.rfile.read(content_length)
            if not image_bytes:
                raise ValueError("Empty request body.")
            self.send_json(200, count_people(image_bytes))
        except Exception as exc:
            self.send_json(400, {"error": "count_failed", "message": str(exc)})

    def log_message(self, format, *args):
        return


def main():
    load_model()
    server = ThreadingHTTPServer((HOST, PORT), ModelHandler)
    print(f"Human counting model service running on http://{HOST}:{PORT}")
    print("POST a raw JPEG/PNG image body to /count")
    server.serve_forever()


if __name__ == "__main__":
    main()
