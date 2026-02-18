# JobTrackr - Full-Stack Job Application Tracker

Deployed link: `ADD_YOUR_DEPLOYED_LINK_HERE`

## What It Does
- Tracks job applications with full lifecycle workflows: create, update status, delete, and undo delete.
- Surfaces decision-making analytics with totals, status breakdown, response rate, and follow-up queues.
- Supports practical operations: search/filter/sort, pagination, and CSV export of filtered data.

## Tech Stack
- Frontend: Next.js (TypeScript, App Router)
- Animation: Framer Motion
- Backend: FastAPI (Python)
- Database: SQLite (default), PostgreSQL-compatible via `DATABASE_URL`
- Charts: Chart.js + `react-chartjs-2`
- HTTP: Axios

## Key Features
- CRUD workflows
  - Create applications
  - Inline status updates (`PATCH`)
  - Delete with confirmation modal
  - Undo delete toast (5 second window)
- Persistence
  - SQLAlchemy-backed storage
  - SQLite local DB file (`services/api/jobtrackr.db`)
- Analytics dashboard
  - Total applications, interviews, offers
  - Status pie chart
  - Response rate
  - Follow-up queue cards: due today, saved jobs, interviews
- Internal dashboard UX
  - Search by company/role
  - Filter by status
  - Has-link toggle
  - Sort by date applied (newest/oldest)
  - Pagination
  - CSV export for current filtered view
  - Loading/empty/error states

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

## Run Locally

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

## Request/Response Notes
### `POST /applications`
```json
{
  "company": "Company",
  "role": "Role",
  "location": "Edmonton, AB",
  "url": "https://...",
  "status": "applied",
  "date_applied": "2026-02-17",
  "next_action_date": "2026-02-20",
  "notes": "optional"
}
```

Allowed status values: `saved`, `applied`, `interview`, `rejected`, `offer`.

## Screenshots
- Dashboard overview: `docs/screenshots/ss1.png`
- Form + table workflows: `docs/screenshots/ss2.png`

## Resume Bullet
Built a full-stack job application tracking and analytics dashboard using Next.js (TypeScript), FastAPI, and SQL persistence with CRUD APIs, follow-up queue automation, and interactive outcome visualizations.
