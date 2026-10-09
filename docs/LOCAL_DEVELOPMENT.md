# Local Development (without AWS)

Run InfraPilot AI entirely on your machine with **no AWS credentials** and **no Bedrock spend**. The backend detects missing AWS auth (or `DEMO_MODE=true`) and uses:

- Local filesystem under `backend/data/` for projects and uploads
- Deterministic **mock Bedrock** responses
- Full **rules engine** and agent modules

---

## Prerequisites

- Python 3.11+
- Git
- (Optional) Node.js 20+ when the Vite frontend is available
- (Optional) AWS credentials only if you intentionally leave `DEMO_MODE=false`

---

## 1. Clone and virtualenv

```bash
cd "InfraPilot AI"
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt
```

---

## 2. Environment

Copy the example env file and force demo mode:

```bash
cp .env.example .env
```

Minimum for local:

```env
DEMO_MODE=true
AWS_REGION=us-east-1
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
LOCAL_DATA_DIR=data
```

Do **not** put real access keys in `.env`. If `DEMO_MODE` is false but no AWS credentials/profile/web identity are present, the app still treats the session as demo (`Settings.is_demo()`).

Place `.env` at the repo root or where `pydantic-settings` can load it when starting uvicorn from `backend/` (see `backend/app/config.py`).

---

## 3. Start the API

From the **backend** directory so imports resolve:

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or from repo root:

```bash
uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
```

Open:

- Health: http://127.0.0.1:8000/health
- OpenAPI UI: http://127.0.0.1:8000/docs
- Demo sample: http://127.0.0.1:8000/api/v1/demo/sample

---

## 4. Frontend (when present)

If `frontend/` exists (Vite):

```bash
cd frontend
npm ci
npm run dev
```

Default Vite port `5173` is already allowed in `CORS_ORIGINS`. Point the SPA at `http://127.0.0.1:8000`.

Until the frontend lands, use `/docs` or `curl` against `/api/v1/*`.

---

## 5. Tests and lint

From repo root (with venv active):

```bash
pytest
ruff check backend agent rules
```

Tests are written to work with demo/mock paths.

---

## 6. Useful API smoke commands

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/api/v1/demo/sample
```

Create a project (example):

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"local-demo\",\"description\":\"DEMO_MODE project\"}"
```

Inspect local persistence:

```text
backend/data/projects/*.json
backend/data/files/<project_id>/
```

---

## 7. Optional: local against real AWS

1. Configure a profile (`aws configure` or SSO) — do not commit credentials.
2. Set `DEMO_MODE=false`, `S3_BUCKET`, `DYNAMODB_TABLE`, and ensure Bedrock model access.
3. Restart uvicorn and confirm `/health` shows `"demo_mode": false`.

Prefer keeping day-to-day work on `DEMO_MODE=true` to control cost.

---

## Related docs

- [DEPLOYMENT.md](./DEPLOYMENT.md) — AWS serverless deploy
- [SECURITY.md](./SECURITY.md)
- [LIMITATIONS.md](./LIMITATIONS.md)
