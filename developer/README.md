# Developer Handoff

This is the backend/simulation part of the SmartBreeze demo.

## Team Architecture

Run two services:

```text
Data Scientist model API  -> http://127.0.0.1:8080
Backend simulation API    -> http://127.0.0.1:8090
```

The model API only counts people.

The backend simulation decides:

```text
person_count -> LOW / MEDIUM / HIGH -> AC state and temperature
```

## AC Rules

```text
0-2 people  -> LOW    -> AC OFF
3-9 people  -> MEDIUM -> AC ON, 24 C
10+ people  -> HIGH   -> AC ON, 20 C
```

The backend does not apply AC temperature changes instantly. The people count and occupancy update immediately, but AC commands use stable-count delays:

```text
AC ON or temperature change -> wait 5 seconds
AC OFF                     -> wait 10 seconds
```

## Start Model API

Terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
python data_science/model_service.py
```

If people are missed, lower the confidence threshold before starting the model service:

```powershell
$env:CONFIDENCE="0.20"
$env:IMAGE_SIZE="960"
python data_science/model_service.py
```

If one person is counted twice because a leg/body part is detected separately, the best fix is cleaner labels and retraining. Runtime box filtering is available for testing, but do not enable it for the main demo if it misses seated or partially visible people.

```powershell
$env:CONFIDENCE="0.30"
$env:IMAGE_SIZE="960"
$env:ENABLE_BOX_FILTER="1"
$env:MIN_BOX_AREA_RATIO="0.006"
$env:MIN_BOX_HEIGHT_RATIO="0.16"
python data_science/model_service.py
```

To turn filtering off again:

```powershell
Remove-Item Env:\ENABLE_BOX_FILTER -ErrorAction SilentlyContinue
Remove-Item Env:\MIN_BOX_AREA_RATIO -ErrorAction SilentlyContinue
Remove-Item Env:\MIN_BOX_HEIGHT_RATIO -ErrorAction SilentlyContinue
```

Check:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health
```

## Start Backend Simulation With Video

Terminal 2:

```powershell
.\.venv\Scripts\Activate.ps1
python developer/backend/backend_simulation_server.py --video "videos\HIGH.MOV"
```

Open dashboard:

```text
http://127.0.0.1:8090
```

The video panel plays the processed classroom video in the dashboard. The backend samples frames every `0.5` seconds by default, sends each sampled frame to the model API, draws person boxes, and updates AC state from the count.

To change the AC delay for testing:

```powershell
python developer/backend/backend_simulation_server.py --video "videos\HIGH.MOV" --ac-on-delay-seconds 5 --ac-off-delay-seconds 10
```

To make playback slower or faster:

```powershell
python developer/backend/backend_simulation_server.py --video "videos\HIGH.MOV" --sample-seconds 0.5
python developer/backend/backend_simulation_server.py --video "videos\HIGH.MOV" --sample-seconds 0.1
```

If the model API times out on a CPU laptop, slow the requests down:

```powershell
python developer/backend/backend_simulation_server.py --video "videos\HIGH.MOV" --sample-seconds 1.0 --model-timeout-seconds 120
```

To process as fast as possible instead of demo playback:

```powershell
python developer/backend/backend_simulation_server.py --video "videos\HIGH.MOV" --no-playback-delay
```

Dashboard features:

```text
Dark control-center UI
Live playing video-style panel with human detection boxes
Live occupancy, people count, AC state, temperature, runtime
Interactive JPG/PNG frame upload
Timeline filter for LOW, MEDIUM, HIGH
Copy current state JSON
Download current state JSON
Pause/resume live polling
```

For a quick test:

```powershell
python developer/backend/backend_simulation_server.py --video "videos\HIGH.MOV" --max-samples 5
```

## Backend Endpoints

Health check:

```text
GET http://127.0.0.1:8090/health
```

Current simulation state:

```text
GET http://127.0.0.1:8090/api/state
```

Process one image frame through model API and simulation:

```text
POST http://127.0.0.1:8090/api/frame
Body: raw JPG/PNG bytes
```

## Test One Image Against Backend

```powershell
$imagePath = "datasets\test\images\HIGH_0015.jpg"
$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $imagePath))
$response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8090/api/frame" -Method Post -Body $bytes -ContentType "image/jpeg"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

## Files Developers Can Own

```text
developer/backend/backend_simulation_server.py
developer/frontend/dashboard.html
developer/README.md
```

The backend service depends on:

```text
data_science/model_service.py
model/best.pt
videos/
datasets/
```

## Presentation Talking Points

- Backend calls AI model API over HTTP.
- Backend receives `person_count`.
- Backend applies occupancy thresholds.
- AC simulation changes state and temperature.
- Dashboard displays occupancy, AC state, temperature, runtime, and timeline.
