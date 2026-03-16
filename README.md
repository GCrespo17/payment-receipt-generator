# payment-receipt-generator

Payment receipt generator for my own use.

## Run as desktop app (from source)

This mode runs everything locally:
- FastAPI backend on `http://127.0.0.1:8000`
- Vue frontend served by the backend from `frontend/dist`
- Native desktop window via `pywebview`

### 1) Build frontend assets

```sh
cd frontend
npm install
npm run build
```

### 2) Install backend dependencies

```sh
cd backend
uv sync
```

### 3) Launch desktop app

From repo root:

```sh
uv run --project backend python desktop/launcher.py
```
