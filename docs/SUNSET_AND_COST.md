# Project sunset & cost estimate (through 8 November 2026)

| Item | Value |
|------|--------|
| **Today (reference)** | 10 October 2026 |
| **Auto-delete / sunset** | **8 November 2026** (UTC) |
| **Days remaining** | **~29 days** |
| **Current mode** | `DEMO_MODE=true` (no Bedrock spend) |

## Auto-delete pipeline

1. **GitHub Actions** — [`.github/workflows/sunset.yml`](../.github/workflows/sunset.yml)
   - Cron: `0 12 8 11 *` (08 Nov 12:00 UTC)
   - Runs teardown **only when the calendar date is `2026-11-08`**
   - Manual: *Actions → Sunset auto-delete → Run workflow* with confirm `SUNSET`
   - Needs repo variable `AWS_ROLE_TO_ASSUME` (OIDC). Until then, run locally:

```powershell
# Local immediate teardown (no confirm)
bash scripts/teardown-auto.sh us-east-1
# or
powershell -File scripts\teardown.ps1   # interactive DELETE confirm
```

2. **AWS EventBridge Scheduler** (optional one-shot) — schedule name `infrapilot-sunset-2026-11-08`
   - Created by `scripts/schedule-sunset.ps1` when you have CLI access
   - Invokes cleanup on `2026-11-08T12:00:00` (account timezone / UTC as configured)

3. **What gets deleted**
   - Lambda `infrapilot-api`
   - API Gateway HTTP API `infrapilot-http-api`
   - DynamoDB `infrapilot-projects`
   - S3 `infrapilot-frontend-*` and `infrapilot-artifacts-*`
   - IAM role `infrapilot-lambda-role`
   - CloudFront disable (final delete may need console after propagation)

The **GitHub repo is not deleted** — only AWS prototype resources.

---

## Estimated AWS build / run cost until 8 Nov 2026

Estimates are **qualitative + list-price order of magnitude** for `us-east-1`.  
They are **not invoices**. Free-tier eligibility and exact usage will change the bill.

### Assumptions (prototype)

| Assumption | Value |
|------------|--------|
| Days | 29 |
| Traffic | Low (you + a few demos), ~1k–5k API calls total |
| Storage | Frontend ~1–5 MB; artifacts &lt; 100 MB |
| AI | `DEMO_MODE=true` → **$0 Bedrock** |
| Always-on | None (serverless only) |

### Cost drivers (current stack)

| Service | Role | Est. through 8 Nov (DEMO_MODE) |
|---------|------|--------------------------------|
| Lambda | API | **$0.00 – $0.50** (often free-tier) |
| API Gateway HTTP | Front door | **$0.00 – $0.20** |
| DynamoDB on-demand | Projects | **$0.00 – $0.50** |
| S3 | Frontend + artifacts | **$0.05 – $0.40** |
| CloudFront | CDN (PriceClass_100) | **$0.00 – $1.00** (free tier often covers light demos) |
| CloudWatch Logs | 14-day retention | **$0.10 – $1.00** |
| **Bedrock** | AI Support | **$0.00** while DEMO_MODE=true |
| **Total (DEMO)** | | **≈ $0.50 – $3.50** for ~29 days |

### If you turn on live AI (`DEMO_MODE=false`, Nova Micro)

| Usage | Extra Bedrock (order of magnitude) |
|-------|-------------------------------------|
| Light (dozens of proposes/evals) | **+$1 – $5** |
| Medium (daily demos) | **+$5 – $25** |
| Heavy / long prompts | **+$25 – $100+** |

**Combined estimate to 8 Nov with light Bedrock:** about **$2 – $15**.  
**With medium Bedrock:** about **$8 – $40**.

### Build / development cost (human + CI)

| Item | Note |
|------|------|
| Local build / tests | $0 (your machine) |
| GitHub Actions CI | Free minutes on private repos have limits; light CI ≈ **$0** on free tier |
| Deploy packaging | Covered under Lambda/S3 above |

There is **no always-on EC2** in this prototype, so idle cost stays near zero.

---

## How to stay under budget until sunset

1. Keep **`DEMO_MODE=true`** for demos that do not need live Bedrock.
2. Do not leave large files in the artifacts bucket (lifecycle: 30-day expire if set).
3. Avoid repeated CloudFront invalidations.
4. On **8 Nov 2026**, confirm the sunset workflow ran (or run `teardown-auto.sh`).

## After sunset

- Live URLs stop working once resources are deleted.
- Code remains on GitHub: https://github.com/SYMOIZ/InfraPilot-AI  
- Redeploy later with `scripts/deploy.ps1` if needed.
