# SmartBreeze


<p align="center">
  <strong>Edge-AI smart classroom management system</strong>
</p>

<p align="center">
  Real-time occupancy detection · Environmental monitoring · Automated HVAC & lighting control
</p>

---

## Overview

**SmartBreeze** is an edge-AI powered system designed for smart classroom management. It detects room occupancy in real time, monitors environmental conditions (temperature, CO₂, humidity), and automatically controls HVAC, lighting, and air-quality systems to optimize comfort, energy efficiency, and safety.

The system processes data locally on edge devices for low latency and privacy, while a central **FastAPI** backend and **React** dashboard provide control, monitoring, and analytics.

**Target use cases:** lecture halls, classrooms, training rooms, meeting spaces, and smart buildings.

---

## Table of Contents

1. [Features](#features)
2. [System Architecture](#system-architecture)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Usage](#usage)
6. [API Endpoints](#api-endpoints)
7. [Configuration](#configuration)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Contributing](#contributing)
11. [Team](#team)

---

## Features

- **Real-time occupancy detection** — AI-based people counting using edge cameras and sensors
- **Environmental monitoring** — temperature, humidity, CO₂, and air quality tracking
- **Automated climate control** — smart HVAC, lighting, and fan control based on occupancy and conditions
- **Edge-first processing** — on-device inference (TensorFlow Lite / ONNX) for low latency and privacy
- **Privacy-focused** — video frames processed locally; only metadata is transmitted
- **Live dashboard** — React-based web interface for real-time monitoring and manual overrides
- **Scene presets** — one-click configurations for lectures, exams, meetings, and empty rooms
- **Analytics & reporting** — occupancy trends, energy usage, and space utilization insights
- **Device management** — sensor status, calibration, firmware health, and remote configuration
- **WebSocket support** — live data streaming to the dashboard without polling
- **Dockerized deployment** — easy setup with Docker Compose for development and production

---

## System Architecture

```
         ┌─────────────────────────────────┐
         │      IoT Sensors & Cameras      │
         │  (PIR, temperature, CO₂, camera) │
         └──────────────┬──────────────────┘
                        │
         ┌──────────────┴──────────────┐
         │                             │
  ┌──────▼──────┐              ┌────────▼────────┐
  │  Edge AI    │              │  Data Stream    │
  │  Engine     │              │  Processor      │
  │ (TensorFlow │              │  (MQTT / HTTP)  │
  │  Lite / ONNX)│              └────────┬────────┘
  └──────┬──────┘                       │
         │                             │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │       FastAPI Backend       │
         │   (REST API · logic · DB)   │
         └──────────────┬──────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
  ┌──────▼──────┐ ┌──────▼──────┐ ┌────▼─────┐
  │   React     │ │  PostgreSQL │ │  SQLite  │
  │  Dashboard  │ │    (prod)   │ │   (dev)  │
  └─────────────┘ └─────────────┘ └──────────┘
```

### Data Flow

```
Sensors → Edge Device → FastAPI Backend → Database
                ↓
        Local AI Decisions → IoT Controllers (HVAC, lights, fans)

React Dashboard ⇄ REST API / WebSocket ⇄ FastAPI Backend
```

### Core Components

| Component | Responsibility |
|---|---|
| **Data Acquisition** | Reads occupancy, temperature, CO₂, humidity, and camera data from ESP32/Arduino/Raspberry Pi nodes over MQTT or HTTP |
| **Edge AI Engine** | Runs on-device people counting and anomaly detection using TensorFlow Lite or ONNX models |
| **Backend (FastAPI)** | Provides REST API, business logic, state management, database access, and WebSocket streaming |
| **Frontend (React + TypeScript)** | Displays live metrics, control panels, analytics charts, and device management screens |
| **Database** | Stores time-series sensor readings, classroom state, device metadata, audit logs, and user actions |

---

## Project Structure

```
smartbreeze/
├── frontend/                      # React + TypeScript client
│   ├── src/
│   │   ├── components/            # Reusable UI components
│   │   ├── pages/                 # Dashboard, Settings, Analytics, Devices
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── services/              # API clients and WebSocket handlers
│   │   ├── types/                 # Shared TypeScript interfaces
│   │   ├── utils/                 # Utility functions
│   │   └── App.tsx                # Main application entry
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                       # FastAPI + Python server
│   ├── app/
│   │   ├── routers/               # API route definitions
│   │   ├── services/              # Business logic layer
│   │   ├── schemas/               # Pydantic request/response models
│   │   ├── models/                # SQLAlchemy database models
│   │   ├── database/              # Database connection and migrations
│   │   ├── core/                  # Configuration, settings, utilities
│   │   ├── ml/                    # Inference pipeline and model wrappers
│   │   └── websocket/             # WebSocket handlers
│   ├── tests/                     # Backend test suite
│   ├── main.py                    # Application entry point
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile
│
├── docker-compose.yml             # Full-stack Docker orchestration
├── .env.example                   # Environment variables template
├── .gitignore
└── README.md                      # This file
```

---

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) 18 or higher
- [Python](https://www.python.org/) 3.9 or higher
- npm (comes with Node.js) and pip
- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) (optional, for containerized deployment)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/smartbreeze.git
cd smartbreeze
```

### 2. Set Up the Backend

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate it
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload
```

- API base URL: `http://localhost:8000`
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`

### 3. Set Up the Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

- Dashboard URL: `http://localhost:5173`

### 4. Run with Docker Compose (Recommended for Full-Stack)

```bash
# Copy the environment template
cp .env.example .env

# Start all services (backend, frontend, PostgreSQL)
docker-compose up -d
```

This starts the backend, frontend, and database in a single command.

---

## Usage

Once the services are running:

1. Open the dashboard at `http://localhost:5173`
2. Add a classroom or device via the **Settings** page
3. View live occupancy, temperature, and CO₂ data on the **Dashboard**
4. Use **Scene Presets** to apply one-click HVAC and lighting configurations
5. Explore **Analytics** for historical occupancy and energy trends
6. Use the **API docs** at `http://localhost:8000/docs` to test endpoints directly

### Example: Get Classroom Occupancy

```bash
curl http://localhost:8000/api/occupancy/1
```

### Example: Apply a Lighting Scene

```bash
curl -X POST http://localhost:8000/api/controls/scene \
  -H "Content-Type: application/json" \
  -d '{"classroom_id": 1, "scene": "presentation"}'
```

---

## API Endpoints

### Health & Status

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/status` | Detailed system status |

### Classrooms

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/classrooms` | List all classrooms |
| `GET` | `/api/classrooms/{id}` | Get a single classroom |
| `POST` | `/api/classrooms` | Create a new classroom |
| `PUT` | `/api/classrooms/{id}` | Update a classroom |
| `DELETE` | `/api/classrooms/{id}` | Delete a classroom |

### Occupancy & Sensors

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/occupancy/{classroom_id}` | Get current occupancy |
| `GET` | `/api/sensors/{classroom_id}` | Get latest sensor readings |
| `POST` | `/api/sensors/{classroom_id}/calibrate` | Calibrate a sensor |

### Controls

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/controls/hvac` | Send HVAC command |
| `POST` | `/api/controls/lighting` | Send lighting command |
| `POST` | `/api/controls/scene` | Apply a predefined scene |

### Real-time

| Type | Endpoint | Description |
|---|---|---|
| WebSocket | `/ws/live` | Live sensor and occupancy stream |

---

## Configuration

Create a `.env` file in the `backend/` directory (or use `.env.example` at the project root):

```env
# General
DEBUG=True
SECRET_KEY=your-very-secret-key-here

# Database
DATABASE_URL=sqlite:///./smartbreeze.db
# For production PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/smartbreeze

# CORS
CORS_ORIGINS=["http://localhost:5173"]

# AI / ML
ENABLE_ML_INFERENCE=True
MODEL_PATH=./ml_models/
CONFIDENCE_THRESHOLD=0.5

# MQTT (for IoT sensor integration)
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Logging
LOG_LEVEL=INFO
```

---

## Testing

### Backend

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm run test
```

---

## Deployment

### Docker Compose

```bash
docker-compose up -d --build
```

### Production Checklist

- Use PostgreSQL instead of SQLite
- Set strong `SECRET_KEY`
- Disable `DEBUG` mode
- Configure HTTPS / reverse proxy (e.g., Nginx, Traefik, Caddy)
- Set up environment variables securely
- Configure monitoring and logging
- Use a managed MQTT broker for IoT devices

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit them: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request with a clear description of your changes

Please ensure your code follows the existing style and includes tests where applicable.

---

## Team

| Role | Members |
|---|---|
| **Product Owner** | P. Gowsihan |
| **Scrum Master** | N. Makeja |
| **Data Developers** | K.M.J. Bingusara Abhishek, Yasitha Rukshan Samarasingha, I.G.S.C. Dasanayaka |
| **Data Scientists** | Mohammed Saad, Rajavisahan Kajaanan, Nahananthiny Gnanakrishnabalasingham |
