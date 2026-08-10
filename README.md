
# AI Facility Monitoring Platform - Infrastructure PoC

## Overview
This repository contains the Proof of Concept (PoC) for an AI-powered Computer Vision platform designed for intelligent building monitoring and facility operational analytics. 

This initial build focuses entirely on **infrastructure resilience, data decoupling, and real-time processing pipelines** rather than final model accuracy. It provides a scalable, containerized foundation structured to allow a team of engineers to work in parallel across frontend, AI, and DevOps tasks without infrastructure bottlenecks. 

Please feel free to reuse, fork, or adapt this architecture for enterprise facility management pipelines.

---
## Demo

https://github.com/user-attachments/assets/1c424474-a43a-470e-a051-d2f6675f5a24

---
## The "Why": Architecture & DevOps Strategy
Processing multiple live video feeds through deep learning models (like YOLO) is computationally heavy. A standard monolithic application would quickly suffer from buffering, dropped frames, and memory leaks. This architecture solves those physical constraints through three core principles:

1. **Edge Gateway Proxying:** By using `go2rtc` as the singular entry point, physical IP cameras are shielded from multiple client connections. It transcodes RTSP to WebRTC on the fly for sub-second frontend latency without burdening the client's browser.
2. **Event-Driven Decoupling:** AI inference is entirely detached from video ingestion. An ingestion worker samples frames and pushes them to a RabbitMQ task queue. This allows multiple AI workers to process frames at their own pace without bottlenecking the live stream.
3. **Hardware Simulation:** To ensure development stability and portability, this PoC uses a local video loop to simulate a 24/7 RTSP camera feed. This removes the dependency on external network conditions or physical hardware during the initial development phase.

---

## Phase 1: MVP System Architecture (Current Build)

The following diagram illustrates the data flow and container boundaries of the current PoC. It strips away secondary infrastructure to focus strictly on video ingestion, AI detection simulation, event routing, and storage.

```mermaid
graph LR
    classDef device fill:#e8f4f8,stroke:#2b7b9b,stroke-width:2px;
    classDef ingest fill:#fcf3cf,stroke:#b7950b,stroke-width:2px;
    classDef broker fill:#f5eef8,stroke:#7d3c98,stroke-width:2px;
    classDef ai fill:#fadbd8,stroke:#b03a2e,stroke-width:2px;
    classDef storage fill:#e8daef,stroke:#6c3483,stroke-width:2px;
    classDef core fill:#d4efdf,stroke:#1e8449,stroke-width:2px;
    classDef ui fill:#d6eaf8,stroke:#2874a6,stroke-width:2px;

    subgraph VideoSource [Video Source]
        CAM[Local MP4 / Loop Feed]:::device
    end

    subgraph MediaIngestion [Media Proxy & Ingestion]
        GO2RTC[go2rtc Container<br/>WebRTC / RTSP Proxy]:::ingest
        INGEST_SVC[Frame Sampler Service<br/>Python / OpenCV]:::ingest
    end

    subgraph EventBroker [Task Queue]
        RABBIT[RabbitMQ Container<br/>Message Broker]:::broker
    end

    subgraph AIWorkers [Mock AI Worker]
        AI_YOLO[Python Worker Container<br/>Event Simulation]:::ai
    end

    subgraph MVPStorage [Data & Image Storage]
        PG[(PostgreSQL Container<br/>Events & Logs)]:::storage
        LOCAL_DISK[(Local Media Volume<br/>/app/media Snapshots)]:::storage
    end

    subgraph BackendCore [Core Application API]
        FASTAPI[FastAPI Backend Container<br/>Rules Engine]:::core
    end

    CAM -- "Raw Video" --> GO2RTC
    GO2RTC -- "RTSP Restream" --> INGEST_SVC
    INGEST_SVC -- "Save Raw Frame" --> LOCAL_DISK
    INGEST_SVC -- "Publish Frame Metadata" --> RABBIT
    RABBIT -- "Work Queue: Detection Tasks" --> AI_YOLO
    AI_YOLO -- "JSON Detection Payload" --> RABBIT
    RABBIT -- "Event Consumption" --> FASTAPI
    FASTAPI -- "Read/Write Logs" --> PG

```

---

## Phase 2: Enterprise-Ready Vision (Target Architecture)

As the project scales to support production-level facility management, the MVP is designed to seamlessly evolve into the following enterprise architecture. This integrates advanced state caching, object storage, SLA scheduling, and a full observability stack.

```mermaid
graph LR
    classDef device fill:#e8f4f8,stroke:#2b7b9b,stroke-width:2px;
    classDef ingest fill:#fcf3cf,stroke:#b7950b,stroke-width:2px;
    classDef broker fill:#f5eef8,stroke:#7d3c98,stroke-width:2px;
    classDef ai fill:#fadbd8,stroke:#b03a2e,stroke-width:2px;
    classDef storage fill:#e8daef,stroke:#6c3483,stroke-width:2px;
    classDef core fill:#d4efdf,stroke:#1e8449,stroke-width:2px;
    classDef plg fill:#d5dbdb,stroke:#5d6d7e,stroke-width:2px;
    classDef external fill:#edbb99,stroke:#a04000,stroke-width:2px;
    classDef ui fill:#d6eaf8,stroke:#2874a6,stroke-width:2px;

    subgraph Edge [Edge & Devices]
        CAM_ENT[CCTV IP Cameras]:::device
    end

    subgraph Ingestion [1. Video Ingestion & Gateway]
        GO2RTC_ENT[go2rtc Proxy]:::ingest
        VID_SVC[Ingestion Strategy: ONVIF/RTSP]:::ingest
    end

    subgraph EventBus [2. Message Broker]
        RABBIT_ENT[RabbitMQ Task Queues]:::broker
        DLQ[Dead Letter Queue]:::broker
    end

    subgraph AILayer [3. Distributed AI Vision]
        AI_OBJ[Object Detection Workers: YOLO]:::ai
        AI_SCENE[Scene Analysis Workers: SSIM]:::ai
    end

    subgraph StorageLayer [4. Storage & Cache]
        PG_ENT[(PostgreSQL)]:::storage
        REDIS[(Redis Cache)]:::storage
        MINIO[(MinIO Object Storage)]:::storage
    end

    subgraph CoreBackend [5. Decision Engine]
        PROXY[Reverse Proxy / Nginx]:::core
        FASTAPI_ENT[FastAPI Backend]:::core
        SCHEDULER[SLA Celery Engine]:::core
    end

    subgraph Observability [6. Telemetry]
        PLG[PLG Stack: Prometheus/Loki/Grafana]:::plg
    end

    subgraph ExtSys [7. External Integrations]
        BMS[BMS / IoT / Access Control]:::external
    end
    
    subgraph Frontend [8. User Interface]
        UI_ENT[React / Flutter Dashboard]:::ui
    end

    CAM_ENT -- "Raw RTSP" --> GO2RTC_ENT
    GO2RTC_ENT -- "RTSP Restream" --> VID_SVC
    VID_SVC -- "Publish Metadata" --> RABBIT_ENT
    RABBIT_ENT -. "Failed Tasks" .-> DLQ
    RABBIT_ENT -- "Work Queue" --> AI_OBJ
    RABBIT_ENT -- "Work Queue" --> AI_SCENE
    AI_OBJ -. "Check Rules" .-> REDIS
    AI_SCENE -. "Fetch Baselines" .-> MINIO
    AI_OBJ -- "Detections" --> RABBIT_ENT
    AI_SCENE -- "Scoring" --> RABBIT_ENT
    RABBIT_ENT -- "Consume" --> FASTAPI_ENT
    FASTAPI_ENT <--> REDIS
    FASTAPI_ENT <--> PG_ENT
    FASTAPI_ENT -- "Save Snapshots" --> MINIO
    SCHEDULER -- "SLA Escalations" --> PG_ENT
    UI_ENT -- "HTTPS / WSS" --> PROXY
    PROXY -- "API Traffic" --> FASTAPI_ENT
    PROXY -- "WebRTC Stream" --> GO2RTC_ENT
    FASTAPI_ENT -- "Triggers" --> BMS
    
    GO2RTC_ENT -. "/metrics" .-> PLG
    FASTAPI_ENT -. "/metrics" .-> PLG
    AI_OBJ -. "GPU Stats" .-> PLG

```

### Key Enterprise Upgrades:

* **Redis Caching:** AI workers read execution rules directly from memory rather than hitting PostgreSQL on every frame, eliminating database thread contention.
* **MinIO Object Storage:** Replaces the local volume mount with an S3-compatible, distributed storage layer for raw event images and baseline reference models.
* **Dead Letter Queue (DLQ):** Protects the pipeline by automatically routing corrupted "poison pill" frames away from the main inference workers to prevent crashes.
* **PLG Observability:** Integrates Prometheus, Loki, and Grafana to track SLA compliance, GPU temperatures, queue lag, and API response times.

---

## Repository Structure

* `docker-compose.yml`: The core orchestrator. Defines the network, volumes, and 4 primary services (`go2rtc`, `rabbitmq`, `postgres`, `backend`, `ai_worker`).
* `test_video/`: Contains the `sample.mp4` file used by `go2rtc` to generate the local simulated RTSP stream.
* `media/`: A shared Docker volume mapped to the host. The AI worker saves event snapshots here, which the backend can serve or reference.
* `config/init.sql`: The initialization script that automatically generates the relational schema in PostgreSQL on the first boot.
* `backend/`: Contains the FastAPI application (`main.py`) and its `Dockerfile`. This service listens to the message broker and writes validated alerts to the database.
* `ai_worker/`: Contains the OpenCV ingestion and mock AI script (`worker.py`). It captures frames from the proxy, saves them, and publishes simulated JSON detections to RabbitMQ.

---

## Quick Start Guide

**Prerequisites:** Docker and Docker Compose installed (tested on Docker Desktop with WSL2 backend).

1. Clone the repository to your local machine.
2. Place a short testing video named `sample.mp4` inside the `test_video/` directory.
3. Build and launch the container stack:
```bash
docker compose up -d --build

```


4. **Verify the Services:**
* **RabbitMQ Dashboard:** Navigate to `http://localhost:15672` (Credentials: `guest` / `guest`)
* **go2rtc WebRTC Stream:** Navigate to `http://localhost:1984` to view the live video loop.
* **FastAPI Swagger Docs:** Navigate to `http://localhost:8000/docs` to view and interact with the REST API.


5. The `ai_worker` will automatically begin processing the video loop and publishing simulated alert payloads to the database. You can view these processed events via the `/events` API endpoint.

---

## Injecting Custom AI Models

The `ai_worker` directory is designed to be highly modular. To replace the simulation script with a live PyTorch or YOLO model:

1. Update the `ai_worker/requirements.txt` to include `ultralytics`, `torch`, or your framework of choice.
2. Modify `worker.py` to load your pre-trained `.pt` weights.
3. Instead of randomly generating the `event_type` and `confidence`, map these directly to your model's output classes and bounding box confidence scores.
4. The JSON payload contract expected by the backend remains identical:
```json
{
    "camera_id": "test_cam_01",
    "event_type": "occupancy_detected",
    "confidence": 0.89,
    "image_path": "/media/occupancy_detected_20260810_153000.jpg"
}

```
---
## Notes
### Architecture Mapping Note
* In this MVP PoC, the **Frame Sampler Service** and the **AI Event Simulator** are combined inside the `ai_worker` container (`ai_worker/worker.py`) using Python and OpenCV (`cv2.VideoCapture`). 
* In production deployment (Phase 2), frame ingestion and AI inference split into separate microservices so heavy model execution never causes frame sampling lag.


### Message Contract (RabbitMQ Payload)

The `ai_worker` publishes JSON event payloads to the `ai_alerts` queue using the following schema:

```json
{
  "camera_id": "test_cam_01",
  "event_type": "spill_detected",
  "confidence": 0.92,
  "image_path": "/media/spill_detected_20260810_193000.jpg"
}
```
This decoupled schema allows backend services, external BMS platforms, or real-time alert UI components to consume alerts without needing direct access to the computer vision layer.

### Troubleshooting

* **Container Health Checks:** PostgreSQL and RabbitMQ include built-in health checks. The `backend` container will wait for both services to be fully healthy before starting.
* **Missing Video File:** If `go2rtc` fails to start, ensure a valid video file exists at `test_video/sample.mp4`.
* **Database Logs:** To inspect events recorded in PostgreSQL directly from your host terminal:
  ```bash
  docker exec -it postgres psql -U admin -d facility_events -c "SELECT * FROM facility_events;"
