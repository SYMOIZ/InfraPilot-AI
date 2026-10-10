# InfraPilot AI

AI-powered **AWS architecture design, evaluation, gap analysis, and optimization** for developers, cloud engineers, DevOps, and solution architects.

InfraPilot helps you describe business requirements, generate or upload an architecture, review security/cost/reliability/scalability gaps with evidence, propose an optimized design, compare versions, and export Draw.io, PNG, and Excel artifacts.

**Scope boundary:** This product designs and reviews architectures only. It does **not** deploy customer infrastructure, provision resources for customers, or generate customer-facing Terraform/CloudFormation.

---

## Features

- Business-requirements capture with optional clarification questions
- Architecture generation via **Amazon Bedrock** (or labeled local demo mocks)
- Controlled AWS service catalog (EC2, S3, Lambda, API Gateway, RDS, DynamoDB, VPC, IAM, CloudFront, SQS, SNS, CloudWatch, ECS, EKS, Step Functions, …)
- Interactive diagram canvas (move, select, zoom)
- Upload existing `.drawio` / XML (PNG/JPG stored as reference)
- Deterministic rules engine (`Pass` / `Fail` / `Warning` / `Unknown` / `Not Applicable`) plus separate AI gap suggestions
- Optimization + original-vs-optimized comparison
- Exports: editable Draw.io, PNG placeholder diagram, Excel workbook
- Project history (local files or DynamoDB + S3)

---

## Architecture

```
Browser  →  CloudFront + S3 (Vite SPA)
         →  API Gateway HTTP API → Lambda (FastAPI + Mangum)
                                      ├─ Amazon Bedrock (optional)
                                      ├─ DynamoDB (projects)
                                      ├─ S3 (artifacts)
                                      └─ CloudWatch Logs
```

Reference diagrams and inventory:

- `docs/architecture/drawio/*.drawio`
- `docs/architecture/InfraPilot_AI_Architecture.xlsx`

Agent pipeline: Requirements Interpreter → Architecture Planner → Diagram Builder → Rules Engine → AI Gap Analyst → Optimization Planner → Report/Export.

---

## Screenshots

Run locally and open the landing page at `http://localhost:5173`. The first viewport is brand-forward (InfraPilot AI) with a single CTA into the workflow.

---

## Quick start (local, no AWS)

```powershell
# Backend
cd backend
python -m pip install -r requirements.txt -r requirements-dev.txt
$env:DEMO_MODE="true"
uvicorn app.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Use **Open demo** for labeled sample data.

Health check: http://127.0.0.1:8000/health

Copy `.env.example` → `.env` and keep placeholders; never commit secrets.

More detail: [docs/LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md)

---

## Testing

```powershell
# Backend (mocked Bedrock — no paid AWS calls)
$env:DEMO_MODE="true"
python -m pytest tests -v

# Frontend
cd frontend
npm run lint
npm run test
npm run build
```

| Suite | What it covers | AWS calls |
|-------|----------------|-----------|
| Unit + integration (`tests/`) | Schemas, draw.io parse/build, rules, scoring, optimization, exports, e2e workflow | None (`DEMO_MODE`) |
| Live Bedrock | Manual / optional | Requires credentials + model access |

Never claim a test passed unless it was executed in this environment.

---

## AWS deployment (CLI-optimized)

Preferred low-cost footprint: **S3 + CloudFront**, **API Gateway HTTP API + Lambda**, **DynamoDB on-demand**, **private S3 artifacts**, **Bedrock on demand**, **CloudWatch** with short log retention.

```powershell
# From repo root — DEMO_MODE=true (no Bedrock spend)
powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1

# Enable live Bedrock (Nova Micro by default — low cost)
powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 -EnableBedrock
```

Outputs are written to `deploy-outputs.txt` (API URL, CloudFront URL, resource names).

Full console + CLI walkthrough, IAM sketch, smoke tests, cost drivers, and teardown: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Cost drivers

- Bedrock token usage (largest variable if `DEMO_MODE=false`)
- Lambda invocations + duration
- CloudFront data transfer
- DynamoDB on-demand request units
- S3 storage (artifacts lifecycle can expire uploads)

Default packaging uses **512 MB / 60 s** Lambda, **PriceClass_100** CloudFront, **14-day** log retention, and **Nova Micro** when Bedrock is enabled.

---

## Security

- No access keys in the repository
- Least-privilege Lambda role (S3 artifacts, DynamoDB table, Bedrock invoke, logs)
- Private frontend origin via CloudFront OAC
- Missing evidence is never treated as a security **Pass**
- See [docs/SECURITY.md](docs/SECURITY.md)

---

## Limitations

- PNG export is a functional Pillow placeholder, not full Draw.io visual fidelity
- Image uploads (PNG/JPG) are reference-only; service extraction requires Draw.io/XML
- Excel cost notes are qualitative — no invented AWS list prices or production IAM policy documents
- Prototype auth is not a full multi-tenant IdP

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md)

---

## Repository layout

```
frontend/          React + TypeScript + Vite
backend/           FastAPI + Mangum Lambda handler
agent/             Bedrock-backed planners and analysts
rules/             Deterministic evaluation rules
catalog/           AWS service catalog JSON
tests/             Unit + integration (mocked Bedrock)
docs/architecture/ Draw.io + Excel references
scripts/           AWS CLI deploy helpers
.github/workflows/ CI + deploy scaffolding
```

---

## Sunset — auto-delete 8 November 2026

This prototype AWS stack is scheduled to be **auto-deleted on 8 November 2026**.

| | |
|--|--|
| Pipeline | [`.github/workflows/sunset.yml`](.github/workflows/sunset.yml) |
| Local teardown | `bash scripts/teardown-auto.sh` |
| Cost estimate to sunset | [docs/SUNSET_AND_COST.md](docs/SUNSET_AND_COST.md) |

**Estimated AWS cost until 8 Nov (≈29 days, `DEMO_MODE=true`):** about **$0.50 – $3.50**.  
With light live Bedrock: about **$2 – $15**. Details in the doc above.

## License

MIT — see [LICENSE](LICENSE). Contributions: [CONTRIBUTING.md](CONTRIBUTING.md).
