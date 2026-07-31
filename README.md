# SmartBreeze

<p align="center">
  <strong>Edge-AI smart classroom human counting and AC control simulation</strong>
</p>

<p align="center">
  YOLO human detection - Dockerized model API - Interactive dark dashboard - Smart AC policy control
</p>

---

## Overview

**SmartBreeze** is an Edge AI prototype for smart classroom management. It uses a trained YOLO model to count people in classroom video frames, sends the count to a backend simulation service, and controls a simulated AC system based on occupancy.

The project is designed as a working demo pipeline:

```text
classroom video/webcam frame -> AI model API -> person_count -> backend rules -> AC state -> dashboard
```

The AI model is separated from the backend business logic. The model only returns human count and detections. The backend decides LOW, MEDIUM, or HIGH occupancy and applies the AC control policy.

---

## Table of Contents

1. [Features](#features)
2. [System Architecture](#system-architecture)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Running the Demo](#running-the-demo)
6. [Docker Model API](#docker-model-api)
7. [API Endpoints](#api-endpoints)
8. [Configuration](#configuration)
9. [Training Notes](#training-notes)
10. [Git LFS Notes](#git-lfs-notes)
11. [Team Handoff](#team-handoff)

---

## Features

- **Human counting AI model** using YOLO and a trained `best.pt` model.
- **Model API** with `/health` and `/count` endpoints.
- **Dockerized model service** for containerized AI inference.
- **Backend AC simulation** that converts person count into occupancy and AC commands.
- **Dark interactive dashboard** for live demo presentation.
- **Video upload detection** through the browser dashboard.
- **Webcam connection option** when a camera is available.
- **Manual AC control** with `Auto`, `AC ON`, and `AC OFF` modes.
- **Editable LOW/MEDIUM/HIGH policy cards** for people ranges and AC temperature.
- **Stable AC delay logic** so AC changes do not happen instantly.
- **Occupancy timeline** showing recent LOW, MEDIUM, and HIGH events.

---

## System Architecture

```text
              Local Video / Webcam
                       |
                       v
              Browser Dashboard
                       |
                       v
        Backend Simulation Server :8090
                       |
                       v
             Model API /count :8080
                       |
                       v
            YOLO best.pt Human Counter
                       |
                       v
        person_count + detection boxes
                       |
                       v
       Occupancy + AC policy + dashboard
```

### Data Flow

```text
Frame -> model API -> person_count -> backend -> AC command -> dashboard
```

### Core Components

| Component | Responsibility |
|---|---|
| `data_science/model_service.py` | Loads `model/best.pt` and exposes the human-counting API |
| `model/best.pt` | Trained YOLO model used for classroom person detection |
| `developer/backend/backend_simulation_server.py` | Backend state, AC logic, dashboard server, and API endpoints |
| `developer/frontend/dashboard.html` | Dark dashboard UI for video/webcam demo and AC control |
| `Dockerfile.model` | Builds the model API container |
| `datasets/` | YOLO training, validation, and test dataset |
| `videos/` | Demo classroom videos |

---

## Project Structure

```text
SmartBreeze/
  data_science/
    auto_label.py
    classroom_person.yaml
    frame_extractor.py
    model_service.py
    prepare_cloud_dataset.py
    split_dataset.py
    train_model.py
    README.md

  developer/
    backend/
      backend_simulation_server.py
      dashboard_server.py
      edge_demo.py
    frontend/
      dashboard.html
    README.md

  model/
    best.pt
    README.md

  datasets/
    train/
    valid/
    test/

  videos/
    HIGH.MOV
    MEDIUM.MOV
    LOW.MOV
    EMPTY.MOV
    JANITOR.MOV
    ARRIVAL -LEAVING.MOV

  Dockerfile.model
  requirements-docker.txt
  README.md
  .gitignore
  .gitattributes
  .dockerignore
  yolo11n.pt
```

---

## Getting Started

### Prerequisites

- Python 3.11
- Git
- Git LFS
- Docker Desktop
- PowerShell on Windows

### Clone the Repository

```powershell
git clone https://github.com/Maki-Nanthan/SmartBreeze.git
cd SmartBreeze
git switch complete-working-system
```

### Install Git LFS Files

```powershell
git lfs install
git lfs pull
```

### Create Python Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install ultralytics opencv-python numpy
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

## Running the Demo

Run two terminals.

### Terminal 1: Model API

```powershell
.\.venv\Scripts\Activate.ps1
python data_science\model_service.py
```

Check:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health
```

### Terminal 2: Backend and Dashboard

```powershell
.\.venv\Scripts\Activate.ps1
python developer\backend\backend_simulation_server.py
```

Open:

```text
http://127.0.0.1:8090
```

### Dashboard Demo Steps

1. Click `Choose video`.
2. Select a video from `videos/`.
3. Click `Start video`.
4. Watch people count, occupancy, and AC state update.
5. Try `Auto`, `AC ON`, and `AC OFF`.
6. Click LOW, MEDIUM, or HIGH policy cards to edit ranges and temperatures.

---

## Docker Model API

The Docker image runs only the model API service. The backend/dashboard still runs with Python.

### Build

```powershell
docker build -f Dockerfile.model -t smartbreeze-human-counter .
```

### Run

```powershell
docker run --rm -p 8080:8080 smartbreeze-human-counter
```

If port `8080` is already used:

```powershell
docker run --rm -p 8081:8080 smartbreeze-human-counter
```

Then start the backend with:

```powershell
python developer\backend\backend_simulation_server.py --model-url http://127.0.0.1:8081/count
```

### Test Count Endpoint

```powershell
$imagePath = "datasets\test\images\HIGH_0015.jpg"
$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $imagePath))

$response = Invoke-WebRequest `
  -UseBasicParsing `
  -Uri "http://127.0.0.1:8080/count" `
  -Method Post `
  -Body $bytes `
  -ContentType "image/jpeg"

$response.Content | ConvertFrom-Json
```

---

## API Endpoints

### Model API

Base URL:

```text
http://127.0.0.1:8080
```

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check model service health |
| `POST` | `/count` | Count people from raw JPG/PNG image bytes |

Example `/count` response:

```json
{
  "person_count": 2,
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.7726,
      "box_xyxy": [100.1, 50.2, 180.4, 260.7]
    }
  ],
  "model_path": "model/best.pt",
  "confidence_threshold": 0.35
}
```

### Backend/Dashboard API

Base URL:

```text
http://127.0.0.1:8090
```

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Dashboard page |
| `GET` | `/health` | Backend health check |
| `GET` | `/api/state` | Current simulation state |
| `GET` | `/api/latest-frame.jpg` | Latest annotated frame |
| `POST` | `/api/frame` | Process one raw JPG/PNG frame |
| `POST` | `/api/policy` | Update LOW/MEDIUM/HIGH policy |
| `POST` | `/api/ac` | Set AC mode: `AUTO`, `ON`, or `OFF` |
| `POST` | `/api/session` | Update browser video session status |

---

## Configuration

### Model Service Environment Variables

| Variable | Default | Description |
|---|---:|---|
| `MODEL_PATH` | `model/best.pt` | Path to trained model |
| `PORT` | `8080` | Model API port |
| `CONFIDENCE` | `0.35` | Detection confidence threshold |
| `IMAGE_SIZE` | `960` | YOLO inference image size |
| `IOU` | `0.45` | YOLO IOU threshold |
| `ENABLE_BOX_FILTER` | `0` | Optional duplicate/body-part filtering |

Example:

```powershell
$env:CONFIDENCE="0.20"
$env:IMAGE_SIZE="960"
python data_science\model_service.py
```

### Backend Options

```powershell
python developer\backend\backend_simulation_server.py --help
```

Useful options:

```powershell
--model-url http://127.0.0.1:8080/count
--ac-on-delay-seconds 5
--ac-off-delay-seconds 10
--sample-seconds 1.0
--model-timeout-seconds 120
```

Default AC delay:

```text
AC ON or temperature change -> 5 seconds
AC OFF                     -> 10 seconds
```

---

## Training Notes

The data science workflow is documented in:

```text
data_science/README.md
```

Main training files:

```text
data_science/classroom_person.yaml
data_science/train_model.py
data_science/prepare_cloud_dataset.py
```

Current model:

```text
model/best.pt
```

If accuracy becomes weak, clean the YOLO labels before retraining. Auto-labeling is useful as a first draft, but bad labels can teach the model to count one person twice.

---

## Git LFS Notes

Large files are tracked with Git LFS:

```text
datasets/
videos/
model/*.pt
yolo11n.pt
```

Do not commit local/generated files:

```text
.venv/
__pycache__/
runs/
backend_state.json
cloud_training_dataset.zip
model/best_current.pt
```

---

## Team Handoff

### For Demo Presenter

Use the branch:

```text
complete-working-system
```

Recommended demo mode:

```text
Docker -> model API
Python -> backend/dashboard
Browser -> dashboard
```

Commands:

```powershell
docker run --rm -p 8080:8080 smartbreeze-human-counter
```

```powershell
.\.venv\Scripts\Activate.ps1
python developer\backend\backend_simulation_server.py
```

Open:

```text
http://127.0.0.1:8090
```

### Team Responsibilities

| Area | Files |
|---|---|
| Data Science | `data_science/`, `model/`, `datasets/`, `Dockerfile.model` |
| Backend | `developer/backend/` |
| Frontend | `developer/frontend/dashboard.html` |
| Demo Assets | `videos/` |

---

## Project Status

The current branch contains a complete working prototype:

```text
AI model API -> backend simulation -> dashboard -> Docker model container
```

The system is ready for demo testing and GitHub pull request review.
