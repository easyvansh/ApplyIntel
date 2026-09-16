# ApplyIntel: Job Application Tracker

ApplyIntel is a full-stack job application tracking and analytics dashboard. It helps you manage application workflows, monitor pipeline health, and keep follow-ups on schedule.

Live Demo

API Health Check
[Wake Up the Server](https://applyintel.onrender.com/health)

Frontend Application
[Client](https://apply-intel.vercel.app/)

## Overview

ApplyIntel transforms a scattered job search into a structured, trackable system.  
Instead of using spreadsheets or notes, users manage applications through a clean dashboard with analytics, follow-up tracking, and pipeline insights.

The platform simulates a lightweight ATS (Applicant Tracking System) tailored for individual job seekers.

---

## Screenshots
### Dashboard Overview
![Dashboard overview](docs/screenshots/Dashboard.png)

### Application Form + Pipeline Table
![Application form and pipeline table](docs/screenshots/form.png)

## Features

### Product

- Create and organize job applications with company, role, location, job link, notes, status, and follow-up dates
- Track the pipeline across Saved, Applied, Interview, Offer, and Rejected stages
- Search by company or role and filter by status or job-link availability
- Sort by application date and navigate large result sets with API-backed pagination
- Soft-delete applications, then restore them through the five-second undo workflow
- Monitor total applications, interviews, offers, saved jobs, response rate, and follow-ups due today
- Export the currently displayed application data as CSV
- Use the responsive Next.js dashboard with animated UI and Chart.js visualizations

### Engineering and reliability

- Separate liveness and database-readiness probes while retaining the original deployment-compatible health URL
- Request IDs accepted or generated for every API call and returned through `X-Request-ID`
- Structured JSON request logs containing request ID, method, path, response status, and duration
- Stable application-error envelopes with traceable request IDs, without exposing internal exceptions
- Isolated pytest lifecycle tests covering health, creation, listing, search, filters, pagination, updates, soft delete, restore, validation, and analytics
- GitHub Actions checks backend tests and the frontend production build on pull requests and pushes to `main`
- Alembic-managed schema evolution for new and existing SQLite or PostgreSQL-compatible databases
- Automatic migration during API startup, with startup failure instead of serving against a partial schema
- Modular backend infrastructure for database sessions, logging, and API error handling

## Tech Stack

### Frontend
- Next.js 15 (TypeScript, App Router)
- React 19
- Framer Motion (UI animations)
- Chart.js + react-chartjs-2 (analytics visualization)
- Axios (API communication)

### Backend
- FastAPI (Python)
- Pydantic request/response validation
- SQLAlchemy ORM
- Alembic migrations
- Uvicorn (ASGI server)
- Python standard-library structured logging
- Pytest + HTTPX API testing

### Database
- SQLite (default local development)
- PostgreSQL compatible via `DATABASE_URL`

### Deployment
- Vercel — frontend hosting
- Render — backend API hosting
- GitHub Actions — continuous integration

## Architecture

```text
Next.js / TypeScript
        │
        │ REST + X-Request-ID
        ▼
FastAPI
        ├── health and readiness
        ├── request tracing and JSON logs
        ├── standardized application errors
        ├── application workflow and analytics
        └── SQLAlchemy sessions
                 │
                 ▼
        SQLite / PostgreSQL
                 ▲
                 │
              Alembic

Quality gates: pytest + GitHub Actions + Next.js production build
```

- `apps/frontend` contains the Next.js dashboard and API client.
- `services/api` contains FastAPI routes, SQLAlchemy persistence, Alembic migrations, and pytest tests.
- `.github/workflows/ci.yml` defines backend and frontend CI checks.
- `docs` contains local-development and deployment guidance.

## Version 1 → Version 2

| Area | Version 1 | Version 2 |
|---|---|---|
| Health | Single static `/health` response | Compatibility health plus process liveness and database readiness |
| Debugging | Framework access logs | Request IDs, response trace headers, and structured JSON latency logs |
| Errors | Ad hoc FastAPI detail strings | Stable application-error codes with user-safe messages and request IDs |
| Testing | Manual verification | Isolated pytest coverage of the core application lifecycle |
| Delivery | Local build checks | GitHub Actions backend-test and frontend-build quality gates |
| Database changes | Import-time table creation and manual SQLite alters | Version-controlled Alembic migrations for new and existing databases |
| Backend structure | Infrastructure embedded in `main.py` | Dedicated database, logging, and error modules with the same deployment entrypoint |
| Frontend runtime | Next.js 14 and React 18 | Supported Next.js 15.5 and React 19 with audited dependencies |
| Operations UI | Product data only | Live API/database readiness and request-trace indicator in the dashboard |

V2 preserves the original application workflow, search, filters, pagination, analytics, CSV export, and soft-delete/restore behavior while making the repository safer to test, migrate, debug, and deploy.

---

## Core API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/health` | Compatibility health check |
| GET | `/health/live` | Process liveness check |
| GET | `/health/ready` | Database readiness check |
| POST | `/applications` | Create application |
| GET | `/applications` | List/search/filter applications |
| PATCH | `/applications/{id}` | Update application |
| DELETE | `/applications/{id}` | Soft delete |
| POST | `/applications/{id}/restore` | Restore deleted |
| GET | `/stats` | Dashboard analytics |

### Applications Response Shape
```json
{
  "items": [],
  "total": 0
}
```

Application-level failures use a stable envelope:

```json
{
  "error": {
    "code": "APPLICATION_NOT_FOUND",
    "message": "Application 42 was not found.",
    "request_id": "a38c..."
  }
}
```

FastAPI validation failures retain their normal `422` response shape.


## Local Development
### 1) Backend API
From `jobtrackr/services/api`:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

Verify:
- `http://localhost:8000/health` -> `{ "ok": true }`
- `http://localhost:8000/health/live` -> `{ "status": "alive" }`
- `http://localhost:8000/health/ready` -> database connectivity status

The API also runs `alembic upgrade head` during startup. Running it explicitly makes migration failures visible before starting the development server.

### 2) Frontend Web App
From `jobtrackr/apps/frontend`:
```bash
npm ci
npm run dev
```

Open:
- `http://localhost:3000`

### Optional PostgreSQL
Set `DATABASE_URL` before starting the backend:

PowerShell:
```powershell
$env:DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/jobtrackr"
uvicorn main:app --reload --port 8000
```

bash:
```bash
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/jobtrackr"
uvicorn main:app --reload --port 8000
```

## Environment Variables
- `DATABASE_URL` — SQLAlchemy database URL (SQLite by default).
- `ALLOWED_ORIGINS` — comma-separated list of allowed frontend origins.
- `NEXT_PUBLIC_API_BASE_URL` — API base URL for the frontend.

## Testing

From `services/api`, run:

```bash
pytest
```

The tests use a disposable SQLite database and do not modify the normal development database.

To verify the frontend production build, run from `apps/frontend`:

```bash
npm ci
npm run build
```

### Complete local verification

From the repository root in PowerShell:

```powershell
cd services/api
.venv\Scripts\python.exe -m pytest -q
cd ../../apps/frontend
npm ci
npm run build
```

Expected result: all backend tests pass and Next.js reports a successful optimized production build.

### Run locally for screenshots

Start the backend in one terminal:

```powershell
cd services/api
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

Start the frontend in a second terminal:

```powershell
cd apps/frontend
npm ci
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```

Open `http://localhost:3000` and capture the refreshed dashboard and application-workflow screenshots. The API documentation is available at `http://localhost:8000/docs`.

To add an idempotent 12-record demo dataset through the running API:

```powershell
cd services/api
.venv\Scripts\python.exe seed_demo.py
```

Running the command again skips matching demo records instead of deleting or duplicating data.

## Database Migrations

From `services/api`, apply all versioned migrations with:

```bash
alembic upgrade head
```

Alembic reads `DATABASE_URL`; credentials are not stored in the migration configuration. The baseline migration can create a new database or safely adopt an existing ApplyIntel applications table.

## Engineering

- Automated FastAPI lifecycle tests with pytest
- GitHub Actions CI for backend tests and frontend production builds
- Version-controlled SQLAlchemy schema migrations with Alembic
- Separate liveness and database-readiness endpoints
- Request IDs and structured request logging
- Standardized application-level API errors
- Soft-delete and restore workflow
- PostgreSQL-compatible relational persistence

## Deployment
See `docs/DEPLOYMENT.md` for Vercel + Render instructions.
Render uses the Python version in `services/api/runtime.txt` (currently `python-3.12.8`).

### Render V2 settings

Use these settings for the existing ApplyIntel backend service:

```text
Root Directory: services/api
Build Command:  pip install -r requirements.txt
Start Command:  uvicorn main:app --host 0.0.0.0 --port $PORT
Health Check:   /health
```

Keep the existing environment variables:

```text
DATABASE_URL=sqlite:////var/data/jobtrackr.db
ALLOWED_ORIGINS=https://apply-intel.vercel.app
```

Deploy commit `020c0fb` or any newer commit from `main`. V2 applies `alembic upgrade head` during startup, preserves the compatibility `/health` endpoint, and exposes database-aware readiness at `/health/ready`. If Render is still serving V1 after a GitHub push, choose **Manual Deploy → Deploy latest commit** for the existing service; do not create a second backend.

### Vercel V2 settings

Keep `apps/frontend` as the root directory and retain:

```text
NEXT_PUBLIC_API_BASE_URL=https://applyintel.onrender.com
```

After deployment, verify the dashboard shows **API ready · Database connected** and that `https://applyintel.onrender.com/health/ready` returns HTTP 200.

ApplyIntel demonstrates practical full-stack engineering skills:
- Production-style API design
- Database modeling + persistence
- Analytics dashboard development
- Full CRUD lifecycle with UX focus
- Real-world problem solving for job seekers
It simulates internal tools used by recruiting teams and applicant tracking systems.
