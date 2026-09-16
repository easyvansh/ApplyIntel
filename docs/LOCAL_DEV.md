# Local Development Notes

## API
Run from `services/api`:
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

The API applies pending Alembic migrations during startup as a safety net. Use `DATABASE_URL` to select a non-default database.

Health endpoints:

- `/health` keeps deployment compatibility.
- `/health/live` confirms the API process is alive.
- `/health/ready` confirms the database can execute a query.

## Frontend
Run from `apps/frontend`:
```bash
npm ci
npm run dev
```

## Tests

Run from `services/api`:

```bash
pytest
```

Run the production frontend check from `apps/frontend`:

```bash
npm run build
```

## Common Issues
- If `uvicorn` cannot import `main`, you are in the wrong directory.
- If CORS blocks the frontend, set `ALLOWED_ORIGINS=http://localhost:3000`.
- If startup fails during migration, run `alembic upgrade head` directly to see the migration error.
