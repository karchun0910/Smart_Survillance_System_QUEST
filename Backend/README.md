# Smart Surveillance Backend

FastAPI backend for the Smart Surveillance System FYP. It accepts detector observations,
evaluates editable MySQL policy rules, stores events, and serves the React dashboard.

## Current foundation

- FastAPI with versioned `/api/v1` routes
- Environment-based configuration
- React development CORS support
- MySQL with SQLAlchemy and PyMySQL
- Alembic database migrations
- Policy-rule CRUD endpoints
- Observation ingestion and event review endpoints
- Detector-heartbeat camera status
- Pytest automated tests
- Ruff code-quality checks

## Requirements

- Python 3.12
- MySQL Server 8.0
- MySQL Workbench
- Visual Studio Code

## MySQL setup

Run the following in MySQL Workbench using an administrator account:

```sql
CREATE DATABASE IF NOT EXISTS smart_surveillance
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

CREATE USER IF NOT EXISTS 'smart_surveillance_app'@'localhost'
    IDENTIFIED BY 'choose_a_private_password';

GRANT ALL PRIVILEGES
    ON smart_surveillance.*
    TO 'smart_surveillance_app'@'localhost';

FLUSH PRIVILEGES;
```

Do not commit the real database password to Git.

## Backend setup

Open a terminal inside the `Backend` folder.

Create and activate the virtual environment:

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate
```

Install the CUDA-enabled PyTorch packages:

```cmd
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

Install the backend, development, and computer-vision dependencies:

```cmd
python -m pip install -e ".[dev,vision]"
```

Create the private environment file:

```cmd
copy .env.example .env
```

Open `.env` and replace `your_mysql_password` with the private password created in
MySQL. Keep the real password only in `.env`.

Apply the database migrations:

```cmd
python -m alembic upgrade head
```

Run the automated tests:

```cmd
python -m pytest -v
```

Run the code-quality checks:

```cmd
python -m ruff check app tests migrations
```

Start FastAPI:

```cmd
python -m uvicorn app.main:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Available endpoints

- `GET /api/v1/health`
- `GET /api/v1/cameras/status`
- `GET /api/v1/rules`
- `POST /api/v1/rules`
- `GET /api/v1/rules/{rule_id}`
- `PATCH /api/v1/rules/{rule_id}`
- `GET /api/v1/observations`
- `POST /api/v1/observations`
- `GET /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `PATCH /api/v1/events/{event_id}/review`

## Current camera behavior

The camera-status endpoint does not open the webcam. It reports the detector as available
when a matching observation was stored during the previous five seconds. This prevents
React polling from competing with the live worker for camera access.

## Repeatable Missing Lab Coat demonstration

Use three PowerShell terminals. MySQL must be running and `Backend/.env` must contain the
local database URL.

Terminal 1 - apply migrations and start FastAPI:

```powershell
cd Backend
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Terminal 2 - start the React dashboard:

```powershell
cd frontend
npm.cmd run dev
```

Open the displayed local URL. Create or enable this policy rule:

| Field | Value |
| --- | --- |
| Rule name | `Lab coat required` |
| Observation type | `missing_lab_coat` |
| Severity | `medium` |
| Confidence | `0.50` |
| Visible seconds | `3` |
| Cooldown | `60` |

Terminal 3 - start the detector and tracker:

```powershell
cd Backend
.\.venv\Scripts\Activate.ps1
$env:RFDETR_POST_OBSERVATIONS = "1"
python scripts\rfdetr_live_webcam.py
```

Expected violation path:

1. A person receives a stable ByteTrack ID.
2. No associated `lab_coat` or `lab_gown` is detected for three continuous seconds.
3. The worker displays `MISSING LAB COAT` and posts `missing_lab_coat`.
4. FastAPI applies confidence, duration, and cooldown policy settings.
5. MySQL stores the observation and policy-generated event for human review.
6. React displays the event within its two-second polling interval and permits Confirmed or
   False Alarm review.

For the normal-state check, wear a lab coat and confirm the worker detects `lab_coat` or
`lab_gown`, clears the missing-attire timer, and creates no new event. The pilot attire
model is intentionally small, so record any false alert as an evaluation limitation.

Automated checks do not require webcam access or a live MySQL connection:

```powershell
cd Backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app tests migrations scripts

cd ..\frontend
npm.cmd run lint
npm.cmd run format:check
npm.cmd run build
```

## RF-DETR saved-image baseline

The RF-DETR image-detection baseline was verified on 26 August 2026.

- Package: `rfdetr==1.9.4`
- Model: `RFDETRNano`
- Model weights: `rf-detr-nano.pth`
- Weight cache: `%USERPROFILE%\.roboflow\models\rf-detr-nano.pth`
- Weight source: Roboflow RF-DETR
- PyTorch: `2.11.0+cu128`
- Torchvision: `0.26.0+cu128`
- Inference device: NVIDIA GeForce RTX 3050 Laptop GPU using CUDA
- Baseline confidence threshold: `0.5`

The package automatically downloaded the RF-DETR Nano weights and successfully validated
their MD5 checksum. The webcam test image produced a person detection with `0.897`
confidence. Thresholds `0.3`, `0.5`, and `0.7` all retained the person detection.

Run the saved-image test from the `Backend` folder:

```cmd
python scripts\rfdetr_image_test.py
```
The annotated result is saved to:
```text
outputs\rfdetr_webcam_person.jpg
```

The open-source `rfdetr` package and the Apache-designated RF-DETR Nano model weights are
licensed under Apache License 2.0. The `rfdetr_plus` extension and RF-DETR XL/2XL detection
models use the PML 1.0 licence and are not used by this project.

Licence source:

```text
https://github.com/roboflow/rf-detr#license
```

Start the live webcam:

```cmd
python scripts\rfdetr_live_webcam.py
```

## Processing flow

Laptop webcam -> OpenCV -> RF-DETR -> ByteTrack -> missing-attire observation -> FastAPI
policy engine -> MySQL event storage -> React dashboard review
