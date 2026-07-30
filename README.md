# Smart Classroom Edge AI System

Edge AI prototype for classroom human counting. The trained YOLO model detects people from classroom frames, and the backend can use `person_count` to decide occupancy and AC simulation state.

## Data Scientist Deliverable

- Cloud-trained YOLO human-counting model: `model/best.pt`
- Local model API: `model_service.py`
- Docker model container: `Dockerfile.model`
- Cloud training dataset config: `classroom_person.yaml`
- Training helper: `train_model.py`
- Cloud dataset packaging helper: `prepare_cloud_dataset.py`

## Run Model API Locally

```powershell
.\.venv\Scripts\Activate.ps1
python model_service.py
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

See [DATA_SCIENTIST_README.md](DATA_SCIENTIST_README.md).

## Dataset Note

Raw videos, extracted datasets, training runs, and `cloud_training_dataset.zip` are excluded from Git because they are large generated assets. Store them in Google Drive, Git LFS, or another approved secure storage location and document the link for the team.
