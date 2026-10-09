# Limitations

InfraPilot AI is an **architecture design, evaluation, and optimization assistant** for AWS-oriented diagrams. It is not an infrastructure control plane.

---

## Out of scope (by design)

- **No infrastructure deployment** — does not create or modify live AWS resources for customer workloads.
- **No Terraform / CloudFormation / CDK generation** — architecture is JSON + Draw.io, not IaC.
- **No guaranteed Well-Architected Review or compliance certification** — rule scores are heuristics.
- **No authoritative AWS pricing** — cost rules and exports use **qualitative** guidance; look up current prices in AWS.
- **No multi-tenant SaaS hardening out of the box** — authN/authZ, tenancy isolation, and WAF are not assumed complete for production SaaS.

---

## Technical limitations

| Area | Limitation |
|------|------------|
| Frontend | Vite SPA may still be **planned / in progress**; API usable via OpenAPI/`curl`. |
| AWS deploy | Lambda packaging and API Gateway/CloudFront wiring are **documented/scaffolded**, not a one-click product installer. |
| Bedrock | Requires account model access; failures fall back to mocks. Output is non-deterministic when live. |
| Rules engine | Deterministic but incomplete vs full AWS service surface; many findings may be `Unknown` / `N/A`. |
| Catalog | `catalog/aws_services.json` is a curated subset, not the full AWS service catalog. |
| Draw.io | Round-trip supports InfraPilot-oriented diagrams; arbitrary complex diagrams may parse partially. |
| DynamoDB | Current adapter uses a simple `id` + document payload; not optimized for large multi-tenant scale. |
| Concurrency | Local demo storage is process-local / filesystem-oriented; not a HA multi-region store. |

---

## Data and safety

- Uploaded diagrams may contain sensitive design information — treat storage and exports carefully.
- SAMPLE / demo endpoints are for illustration only.
- Optimization suggestions can be wrong or incomplete; a human architect must review before adoption.

---

## Cost

Running with live Bedrock incurs AWS usage charges. Prefer `DEMO_MODE=true` for development. See [DEPLOYMENT.md](./DEPLOYMENT.md) cost drivers and [SECURITY.md](./SECURITY.md) Bedrock safeguards.

---

## Version

Documented against the repository state where FastAPI + Mangum, agents, rules, and storage adapters are present; hosting resources and frontend may lag. Labels in `docs/architecture/` distinguish **IMPLEMENTED** vs **PLANNED**.
