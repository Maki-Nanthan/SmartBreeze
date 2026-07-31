# Smart Classroom Edge AI System

Edge AI prototype for classroom human counting. The trained YOLO model detects people from classroom frames, and the backend can use `person_count` to decide occupancy and AC simulation state.

## Data Scientist Deliverable

- Cloud-trained YOLO human-counting model: `model/best.pt`
- Local model API: `data_science/model_service.py`
- Docker model container: `Dockerfile.model`
- Cloud training dataset config: `data_science/classroom_person.yaml`
- Training helper: `data_science/train_model.py`
- Cloud dataset packaging helper: `data_science/prepare_cloud_dataset.py`

## Developer Deliverable

- Backend + AC simulation: `developer/backend/backend_simulation_server.py`
- Frontend dashboard: `developer/frontend/dashboard.html`
- Developer handoff notes: `developer/README.md`

## Run Model API Locally

```powershell
.\.venv\Scripts\Activate.ps1
python data_science/model_service.py
```

For better recall when people are missed:

```powershell
$env:CONFIDENCE="0.20"
$env:IMAGE_SIZE="960"
python data_science/model_service.py
```

Health check:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health
```

Count people in an image:

```powershell
$imagePath = "datasets\test\images\HIGH_0015.jpg"
$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $imagePath))
$response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/count" -Method Post -Body $bytes -ContentType "image/jpeg"
$response.Content | ConvertFrom-Json
```

## Docker

Docker must be installed before running these commands.

```powershell
docker build -f Dockerfile.model -t smart-classroom-human-counter .
docker run --rm -p 8080:8080 smart-classroom-human-counter
```

## Cloud Training

See [data_science/README.md](data_science/README.md).

## Backend Simulation Dashboard

```powershell
python developer/backend/backend_simulation_server.py --video "videos\HIGH.MOV"
```

Open:

```text
http://127.0.0.1:8090
```

If the model API times out on CPU, use:

```powershell
python developer/backend/backend_simulation_server.py --video "videos\HIGH.MOV" --sample-seconds 1.0 --model-timeout-seconds 120
```

## Dataset Note

Videos, datasets, and model weights are tracked with Git LFS. Generated training runs and `cloud_training_dataset.zip` are excluded from normal commits.
