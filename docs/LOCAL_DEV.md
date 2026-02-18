# Local Development Notes

## API
Run from `services/api`:
```bash
uvicorn main:app --reload --port 8000
```

## Frontend
Run from `apps/frontend`:
```bash
npm run dev
```

## Common Issues
- If `uvicorn` cannot import `main`, you are in the wrong directory.
- If CORS blocks the frontend, set `ALLOWED_ORIGINS=http://localhost:3000`.
