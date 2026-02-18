# Deployment (Vercel + Render)

This project deploys the frontend to Vercel and the FastAPI backend to Render with a persistent disk for SQLite.

## Backend (Render)
1. Create a new **Web Service** from `services/api`.
2. Build command:
   - `pip install -r requirements.txt`
3. Start command:
   - `uvicorn main:app --host 0.0.0.0 --port 8000`
4. Add a **persistent disk** mounted at `/var/data`.
5. Set environment variables:
   - `DATABASE_URL=sqlite:////var/data/jobtrackr.db`
   - `ALLOWED_ORIGINS=https://<your-vercel-domain>`

## Frontend (Vercel)
1. Import the repo and set the root to `apps/frontend`.
2. Set environment variable:
   - `NEXT_PUBLIC_API_BASE_URL=https://<your-render-api>`
3. Deploy.

## Notes
- If you use Postgres instead of SQLite, update `DATABASE_URL` accordingly.
- For local dev, keep `ALLOWED_ORIGINS=http://localhost:3000`.
