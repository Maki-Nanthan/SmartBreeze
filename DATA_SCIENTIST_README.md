# Data Scientist Deliverable

This part of the project owns the human-counting AI model.

## Responsibility Boundary

The model container returns:

```json
{
  "person_count": 5,
  "detections": []
}
```

The backend team decides:

```text
person_count -> LOW / MEDIUM / HIGH -> AC simulation state
```

This keeps the AI model independent from business rules.

## Current Dataset

YOLO dataset config:

```text
classroom_person.yaml
```

Class list:

```text
0: person
```

The dataset is already split into:

```text
datasets/train
datasets/valid
datasets/test
```

## Prepare Dataset For Cloud Training

Run:

```powershell
.\.venv\Scripts\python.exe prepare_cloud_dataset.py
```

This creates:

```text
cloud_training_dataset.zip
```

Upload this zip to Google Colab or another approved cloud ML platform.

## Cloud Training Command

In the cloud notebook:

```python
!pip install ultralytics
```

Upload and unzip `cloud_training_dataset.zip`, then run:

```python
from ultralytics import YOLO

model = YOLO("yolo11n.pt")
results = model.train(
    data="classroom_person.yaml",
    epochs=20,
    imgsz=640,
    batch=8,
)
```

If the cloud GPU memory is low, reduce `batch`:

```python
batch=4
```

After training, download:

```text
runs/detect/train/weights/best.pt
```

Save it in this project as:

```text
model/best.pt
```

## Build Docker Model Container

After `model/best.pt` exists:

```powershell
docker build -f Dockerfile.model -t smart-classroom-human-counter .
```

Run:

```powershell
docker run --rm -p 8080:8080 smart-classroom-human-counter
```

Health check:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health
```

## Count API

Endpoint:

```text
POST http://127.0.0.1:8080/count
```

Request body:

```text
Raw JPEG or PNG image bytes
```

Response:

```json
{
  "person_count": 5,
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.8123,
      "box_xyxy": [100.1, 50.2, 180.4, 260.7]
    }
  ],
  "model_path": "model/best.pt",
  "confidence_threshold": 0.35
}
```

## Evidence To Show In Demo

- Dataset upload to cloud.
- Training command/configuration.
- Training progress/results screen.
- Evaluation metrics: precision, recall, mAP.
- Exported `best.pt`.
- Docker build.
- `/health` endpoint.
- `/count` endpoint returning `person_count`.
