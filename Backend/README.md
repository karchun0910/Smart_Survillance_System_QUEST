# Smart Surveillance Backend

FastAPI backend for the Smart Surveillance System FYP. The backend currently supports
MySQL policy-rule management and laptop-webcam availability checks through OpenCV.

## Current foundation

- FastAPI with versioned `/api/v1` routes
- Environment-based configuration
- React development CORS support
- MySQL with SQLAlchemy and PyMySQL
- Alembic database migrations
- Policy-rule CRUD endpoints
- Laptop-webcam availability endpoint
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

## Current camera behavior

The camera-status endpoint opens laptop webcam source `0`, attempts to capture one frame,
reports whether capture succeeded, and then releases the camera. It does not currently
stream, store, or analyze video.

## Planned processing flow

Laptop webcam -> OpenCV -> detector -> tracker -> action recognition -> face-recognition
adapter -> database rule engine -> event storage -> React dashboard alerts