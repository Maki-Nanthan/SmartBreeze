import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8080"))
MODEL_PATH = os.environ.get("MODEL_PATH", "model/best.pt")
CONFIDENCE = float(os.environ.get("CONFIDENCE", "0.35"))

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


def count_people(image_bytes):
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Request body is not a valid encoded image.")

    result = load_model()(frame, conf=CONFIDENCE, verbose=False)[0]
    detections = []

    for box in result.boxes:
        class_id = int(box.cls[0])
        if class_id != 0:
            continue

        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
        confidence = float(box.conf[0])
        detections.append(
            {
                "class_id": class_id,
                "class_name": "person",
                "confidence": round(confidence, 4),
                "box_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
            }
        )

    return {
        "person_count": len(detections),
        "detections": detections,
        "model_path": MODEL_PATH,
        "confidence_threshold": CONFIDENCE,
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
