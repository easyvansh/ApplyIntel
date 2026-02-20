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

## Highlights
- Full CRUD job application tracking with soft delete + undo
- Application pipeline tracking (Applied → Interview → Offer → Rejected)
- Follow-up management queue (due today, upcoming, saved)
- Search, filter, sort, and pagination across applications
- CSV export for external tracking or reporting
- Status analytics and response-rate visualization
- Clean dashboard UI with interactive charts

## Tech Stack

### Frontend
- Next.js (TypeScript, App Router)
- Framer Motion (UI animations)
- Chart.js + react-chartjs-2 (analytics visualization)
- Axios (API communication)

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- Uvicorn (ASGI server)

### Database
- SQLite (default local development)
- PostgreSQL compatible via `DATABASE_URL`

### Deployment
- Vercel — frontend hosting
- Render — backend API hosting

## Architecture
- `apps/frontend`: Next.js UI
- `services/api`: FastAPI service + SQLAlchemy models
- `docs/`: Screenshots and deployment notes


Architecture follows a modern full-stack separation:
- Frontend consumes REST APIs
- Backend handles business logic + analytics
- Database persists applications and metrics

---

## Core API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/health` | API health check |
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


## Local Development
### 1) Backend API
From `jobtrackr/services/api`:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Verify:
- `http://localhost:8000/health` -> `{ "ok": true }`

### 2) Frontend Web App
From `jobtrackr/apps/frontend`:
```bash
npm install
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

## Deployment
See `docs/DEPLOYMENT.md` for Vercel + Render instructions.
Render uses the Python version in `services/api/runtime.txt` (currently `python-3.12.8`).

ApplyIntel demonstrates practical full-stack engineering skills:
- Production-style API design
- Database modeling + persistence
- Analytics dashboard development
- Full CRUD lifecycle with UX focus
- Real-world problem solving for job seekers
It simulates internal tools used by recruiting teams and applicant tracking systems.
