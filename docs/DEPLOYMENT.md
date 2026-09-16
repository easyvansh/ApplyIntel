# Deployment (Vercel + Render)

This project deploys the frontend to Vercel and the FastAPI backend to Render with a persistent disk for SQLite.

## Backend (Render)
1. Create a new **Web Service** from `services/api`.
2. Build command:
   - `pip install -r requirements.txt`
3. Start command:
   - `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Python version:
   - Use `python-3.12.8` via `services/api/runtime.txt` (already in repo).
5. Add a **persistent disk** mounted at `/var/data`.
6. Set environment variables:
   - `DATABASE_URL=sqlite:////var/data/jobtrackr.db`
   - `ALLOWED_ORIGINS=https://<your-vercel-domain>`
7. Keep the service health-check path at `/health` for backward compatibility. Use `/health/ready` when a database-aware readiness signal is supported.

The API applies `alembic upgrade head` during startup before accepting traffic. A migration failure stops startup instead of running against a partially migrated schema.

For an existing Render service that has not picked up the latest `main` push, use **Manual Deploy → Deploy latest commit**. Keep the same service and persistent disk so the public URL and database remain unchanged.

## Frontend (Vercel)
1. Import the repo and set the root to `apps/frontend`.
2. Set environment variable:
   - `NEXT_PUBLIC_API_BASE_URL=https://<your-render-api>`
3. Deploy.

## Notes
- If you use Postgres instead of SQLite, update `DATABASE_URL` accordingly.
- For local dev, keep `ALLOWED_ORIGINS=http://localhost:3000`.
- Back up persistent production data before applying a new migration.
