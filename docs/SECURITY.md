# Security

InfraPilot AI helps design and evaluate **architecture diagrams**. It does not deploy customer infrastructure. Still treat the API, uploads, and Bedrock usage with least privilege.

---

## Secrets and repository hygiene

- **Never commit** `.env`, AWS access keys, session tokens, or Bedrock API keys.
- Use `.env.example` for **placeholders only**.
- Rely on `.gitignore` for `.env`, `*.pem`, `.aws/`, build artifacts, and virtualenvs.
- Prefer **IAM roles** (Lambda execution role, GitHub Actions **OIDC**) over long-lived access keys.
- If a secret is exposed: rotate immediately, revoke keys, and scrub git history if needed.

---

## Least-privilege IAM (guidance only)

Do **not** attach `AdministratorAccess` to the Lambda or CI deploy roles.

| Role | Intended scope |
|------|----------------|
| Lambda execution | CloudWatch logs for one function; Bedrock invoke/converse on **one model ARN**; S3 object R/W on **artifacts bucket/prefix**; DynamoDB item ops on **one table** |
| CI deploy (OIDC) | `s3:PutObject`/`DeleteObject` on frontend (+ optional artifacts); `lambda:UpdateFunctionCode`; optional `cloudfront:CreateInvalidation`; deny everything else |

Exact production policy JSON is **out of scope** for this repo’s docs — draft from the sketches in [DEPLOYMENT.md](./DEPLOYMENT.md) and review with a security owner.

Trust GitHub OIDC only for your org/repo and the deploy workflow (`workflow_dispatch` / specific refs).

---

## Bedrock rate and cost safeguards

- Default model id targets a **Haiku-class** (lower cost) model; change deliberately.
- Client sets `maxTokens` and low `temperature` on converse calls.
- **`DEMO_MODE=true`** (or missing AWS credentials) skips live Bedrock and uses mocks.
- Enable only required models in the Bedrock console.
- Avoid UI loops that re-invoke planning/gap analysis on every keystroke.
- Monitor CloudWatch / Bedrock usage dashboards; set account budgets/alerts in AWS Billing (outside this app).

InfraPilot does **not** implement a full token quota UI; treat operational rate limiting at API Gateway / WAF / account budgets as recommended for production (**planned**).

---

## Application surface

- **CORS:** configure `CORS_ORIGINS` to known frontends only (localhost for dev; CloudFront domain for prod).
- **Uploads:** Draw.io XML is parsed with **defusedxml**. Enforce payload size limits at API Gateway / Lambda for production.
- **Data:** Prefer not to store secrets, credentials, or PII inside architecture JSON or project notes.
- **Demo data:** `/api/v1/demo/sample` is labeled SAMPLE — not a production environment.
- **Exports:** Treat downloaded reports as advisory design artifacts, not compliance certificates (see [LIMITATIONS.md](./LIMITATIONS.md)).

---

## Logging and monitoring

- Do not log full Bedrock prompts/responses if they may contain sensitive business content.
- Set CloudWatch log retention to limit retention risk and cost.
- Use separate AWS accounts or environments for demos vs production when possible.

---

## Reporting issues

If you discover a security issue in InfraPilot AI, open a private security advisory or contact the maintainers — do not file a public issue with exploit details.
