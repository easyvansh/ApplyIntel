# JobTrackr — Job Application Tracker

JobTrackr is a full-stack job application tracking and analytics dashboard. It helps you manage application workflows, monitor pipeline health, and keep follow-ups on schedule.

**Live Demo:** `ADD_YOUR_DEPLOYED_LINK_HERE`

## Screenshots
![Dashboard overview](docs/screenshots/ss1.png)
![Application form and pipeline table](docs/screenshots/ss2.png)

## Highlights
- Full CRUD workflows with soft delete + undo
- Status analytics and response-rate insights
- Follow-up queue (due today, saved, interviews)
- Search, filter, sort, pagination, and CSV export

## Tech Stack
- **Frontend:** Next.js (TypeScript, App Router), Framer Motion
- **Backend:** FastAPI (Python), SQLAlchemy
- **Database:** SQLite (default), Postgres-compatible via `DATABASE_URL`
- **Charts:** Chart.js + `react-chartjs-2`
- **HTTP:** Axios

## Architecture
- `apps/frontend`: Next.js UI
- `services/api`: FastAPI service + SQLAlchemy models
- `docs/`: Screenshots and deployment notes

## API Endpoints
- `GET /health`
- `POST /applications`
- `GET /applications?q=&status=&has_link=&sort_order=&limit=&offset=`
- `PATCH /applications/{id}`
- `DELETE /applications/{id}`
- `POST /applications/{id}/restore`
- `GET /stats`

### `GET /applications` response shape
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

## Resume Bullet
Built a full-stack job application tracking and analytics dashboard using Next.js (TypeScript), FastAPI, and SQL persistence with CRUD APIs, follow-up queue automation, and interactive outcome visualizations.
