# Deployment Guide (AWS Serverless)

InfraPilot AI is designed for a **low-cost** serverless footprint:

| Layer | Stack |
|-------|--------|
| Frontend | Vite static build → **S3** + **CloudFront** (planned when `frontend/` exists) |
| API | **API Gateway HTTP API** → **Lambda** (FastAPI + **Mangum**) |
| Data | **DynamoDB** (projects) + **S3** (artifacts) |
| AI | **Amazon Bedrock** (optional; use `DEMO_MODE` to avoid Bedrock spend) |
| Ops | **CloudWatch** Logs |

**Status:** Application code and an AWS CLI deploy script (`scripts/deploy.ps1`) are **implemented**. Prefer the script for a low-cost serverless stack; the sections below document the same steps for Console/CLI review and teardown.

**Cost-optimized defaults:** `DEMO_MODE=true` (no Bedrock spend), DynamoDB on-demand, HTTP API, Lambda 512 MB / 60 s, CloudFront `PriceClass_100`, 14-day log retention, Bedrock model default `amazon.nova-micro-v1:0` when enabled.

This guide does **not** invent production IAM policy documents. Use least-privilege sketches below and have a security owner review before production.

---

## Prerequisites

- AWS account with console + CLI access (`aws --version` ≥ 2)
- Region with Bedrock model access if you enable live AI (default suggestion: `us-east-1`)
- Python 3.11+ (for packaging)
- Node.js 20+ (when building the Vite frontend)
- Permission to create IAM roles, Lambda, API Gateway, S3, DynamoDB, CloudFront

Prefer **on-demand DynamoDB**, **HTTP API** (not REST API), **no provisioned Lambda concurrency**, and **short CloudWatch log retention**.

---

## 1. Environment variables (Lambda / local)

| Variable | Required | Description |
|----------|----------|-------------|
| `DEMO_MODE` | No | `true` to force local/mock path (no Bedrock/Dynamo/S3 calls) |
| `AWS_REGION` | Yes (AWS) | e.g. `us-east-1` |
| `BEDROCK_REGION` | No | Defaults to `AWS_REGION` |
| `BEDROCK_MODEL_ID` | No | Default in code: `anthropic.claude-3-haiku-20240307-v1:0` |
| `S3_BUCKET` | For artifacts | Artifacts / uploads bucket name |
| `DYNAMODB_TABLE` | For projects | Projects table name |
| `CORS_ORIGINS` | Recommended | Comma-separated origins (include CloudFront URL) |
| `LOCAL_DATA_DIR` | Local only | Default `data` under backend |

Never put secrets in the repo. Set values in Lambda configuration or a secrets manager of your choosing.

---

## 2. Create data resources (CLI)

Set shell variables (PowerShell or bash-compatible):

```bash
export AWS_REGION=us-east-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ARTIFACTS_BUCKET="infrapilot-artifacts-${ACCOUNT_ID}-${AWS_REGION}"
export FRONTEND_BUCKET="infrapilot-frontend-${ACCOUNT_ID}-${AWS_REGION}"
export DDB_TABLE="infrapilot-projects"
```

### Artifacts bucket

```bash
aws s3api create-bucket \
  --bucket "$ARTIFACTS_BUCKET" \
  --region "$AWS_REGION" \
  $( [ "$AWS_REGION" = "us-east-1" ] || echo "--create-bucket-configuration LocationConstraint=$AWS_REGION" )

aws s3api put-public-access-block \
  --bucket "$ARTIFACTS_BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Optional: expire demo uploads after 30 days
aws s3api put-bucket-lifecycle-configuration \
  --bucket "$ARTIFACTS_BUCKET" \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "expire-uploads",
      "Status": "Enabled",
      "Filter": {"Prefix": ""},
      "Expiration": {"Days": 30}
    }]
  }'
```

### Frontend bucket (static site origin for CloudFront)

```bash
aws s3api create-bucket \
  --bucket "$FRONTEND_BUCKET" \
  --region "$AWS_REGION" \
  $( [ "$AWS_REGION" = "us-east-1" ] || echo "--create-bucket-configuration LocationConstraint=$AWS_REGION" )

aws s3api put-public-access-block \
  --bucket "$FRONTEND_BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

Serve the frontend via **CloudFront + Origin Access Control (OAC)** — do not make the bucket public.

### DynamoDB table (on-demand)

```bash
aws dynamodb create-table \
  --table-name "$DDB_TABLE" \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$AWS_REGION"

aws dynamodb wait table-exists --table-name "$DDB_TABLE" --region "$AWS_REGION"
```

---

## 3. Bedrock model access

1. Open **Amazon Bedrock → Model access** in the console (same region as `BEDROCK_REGION`).
2. Request/enable the model matching `BEDROCK_MODEL_ID` (Haiku-class recommended for cost).
3. Confirm with a tiny invoke only after IAM is scoped — or keep `DEMO_MODE=true` until ready.

**Cost safeguard:** leave `DEMO_MODE=true` for smoke tests that do not need LLM output.

---

## 4. IAM — Lambda execution role (least privilege sketch)

Create a role trusted by Lambda. Attach a **customer-managed** policy scoped to *your* resources. Replace ARNs; do not use `AdministratorAccess`.

**Trust (Lambda):**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

**Permissions sketch (fill ARNs — review before prod):**

- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` on `/aws/lambda/YOUR_FUNCTION_NAME`
- `bedrock:InvokeModel` / `bedrock:Converse` on the specific model ARN in your region
- `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on `arn:aws:s3:::YOUR_ARTIFACTS_BUCKET/*` and `s3:ListBucket` on the bucket
- `dynamodb:GetItem`, `PutItem`, `DeleteItem`, `Scan`, `Query` on `arn:aws:dynamodb:REGION:ACCOUNT:table/YOUR_TABLE`

Example CLI scaffolding (policy document kept intentionally minimal — expand carefully):

```bash
export LAMBDA_ROLE_NAME=infrapilot-lambda-role

aws iam create-role \
  --role-name "$LAMBDA_ROLE_NAME" \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":{"Service":"lambda.amazonaws.com"},
      "Action":"sts:AssumeRole"
    }]
  }'

# Attach AWS managed basic logging only as a starting point, then add a
# CUSTOM managed policy with the Bedrock/S3/DynamoDB statements above.
aws iam attach-role-policy \
  --role-name "$LAMBDA_ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Add a custom inline/managed policy JSON file locally (not committed with secrets) for Bedrock/S3/DynamoDB.

```bash
export LAMBDA_ROLE_ARN=$(aws iam get-role --role-name "$LAMBDA_ROLE_NAME" --query Role.Arn --output text)
```

---

## 5. Package and deploy Lambda (FastAPI + Mangum)

From the **repository root**, build a deployment zip that includes `backend/app`, `agent`, `rules`, `catalog`, and dependencies.

```bash
export FUNC_NAME=infrapilot-api
export BUILD_DIR=/tmp/infrapilot-lambda-build
rm -rf "$BUILD_DIR" && mkdir -p "$BUILD_DIR"

# Install deps into build dir (Linux-compatible wheels recommended for Lambda)
python -m pip install -r backend/requirements.txt -t "$BUILD_DIR"

# Application code
cp -R backend/app "$BUILD_DIR/"
cp -R agent rules catalog "$BUILD_DIR/"

cd "$BUILD_DIR"
zip -r9 /tmp/infrapilot-api.zip .
cd -
```

On Windows PowerShell, use an equivalent copy/`Compress-Archive` flow or build inside a Linux CI runner / container (preferred for Lambda).

Create or update the function:

```bash
# Create (first time)
aws lambda create-function \
  --function-name "$FUNC_NAME" \
  --runtime python3.12 \
  --role "$LAMBDA_ROLE_ARN" \
  --handler app.lambda_handler.handler \
  --timeout 60 \
  --memory-size 512 \
  --zip-file fileb:///tmp/infrapilot-api.zip \
  --environment "Variables={
    DEMO_MODE=false,
    AWS_REGION=$AWS_REGION,
    BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0,
    S3_BUCKET=$ARTIFACTS_BUCKET,
    DYNAMODB_TABLE=$DDB_TABLE,
    CORS_ORIGINS=https://YOUR_CLOUDFRONT_DOMAIN
  }" \
  --region "$AWS_REGION"

# Update code later
aws lambda update-function-code \
  --function-name "$FUNC_NAME" \
  --zip-file fileb:///tmp/infrapilot-api.zip \
  --region "$AWS_REGION"
```

Set CloudWatch log retention (cost control):

```bash
aws logs put-retention-policy \
  --log-group-name "/aws/lambda/$FUNC_NAME" \
  --retention-in-days 14 \
  --region "$AWS_REGION" || true
```

---

## 6. API Gateway HTTP API → Lambda

```bash
export API_NAME=infrapilot-http-api

export API_ID=$(aws apigatewayv2 create-api \
  --name "$API_NAME" \
  --protocol-type HTTP \
  --cors-configuration "AllowOrigins=https://YOUR_CLOUDFRONT_DOMAIN,http://localhost:5173,AllowMethods=GET,POST,PUT,PATCH,DELETE,OPTIONS,AllowHeaders=*" \
  --query ApiId --output text)

export INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "$API_ID" \
  --integration-type AWS_PROXY \
  --integration-uri "arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:${FUNC_NAME}" \
  --payload-format-version 2.0 \
  --query IntegrationId --output text)

aws apigatewayv2 create-route \
  --api-id "$API_ID" \
  --route-key 'ANY /{proxy+}' \
  --target "integrations/$INTEGRATION_ID"

aws apigatewayv2 create-route \
  --api-id "$API_ID" \
  --route-key 'ANY /' \
  --target "integrations/$INTEGRATION_ID"

aws apigatewayv2 create-stage \
  --api-id "$API_ID" \
  --stage-name '$default' \
  --auto-deploy

# Permission for API Gateway to invoke Lambda
aws lambda add-permission \
  --function-name "$FUNC_NAME" \
  --statement-id apigw-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${ACCOUNT_ID}:${API_ID}/*/*"

export API_ENDPOINT=$(aws apigatewayv2 get-api --api-id "$API_ID" --query ApiEndpoint --output text)
echo "API: $API_ENDPOINT"
```

---

## 7. Frontend: S3 + CloudFront (console + CLI outline)

When `frontend/` exists:

```bash
cd frontend
npm ci
npm run build
aws s3 sync dist/ "s3://${FRONTEND_BUCKET}/" --delete
```

**Console checklist (CloudFront):**

1. Create **Origin Access Control** for S3.
2. Create distribution with S3 origin = `$FRONTEND_BUCKET`, OAC enabled.
3. Update bucket policy to allow that distribution’s OAC (AWS console “Copy policy” helper).
4. Default root object: `index.html`.
5. For SPA routing, add custom error responses 403/404 → `/index.html` with 200 (if using client-side routes).
6. Set Lambda `CORS_ORIGINS` to `https://YOUR_DISTRIBUTION_DOMAIN`.

Invalidate after deploy:

```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

---

## 8. Health checks and smoke test

```bash
# Health (no Bedrock required)
curl -sS "${API_ENDPOINT}/health"

# Root
curl -sS "${API_ENDPOINT}/"

# Demo sample (safe labeled data)
curl -sS "${API_ENDPOINT}/api/v1/demo/sample"
```

Expected `/health` JSON includes `"status":"ok"` and `"demo_mode": true|false`.

With `DEMO_MODE=false` and Bedrock enabled, optionally exercise a requirements → architecture path via OpenAPI at `${API_ENDPOINT}/docs` — watch Bedrock usage.

---

## 9. Cost drivers (qualitative)

| Driver | Notes |
|--------|--------|
| **Bedrock** | Usually the largest variable cost. Prefer Haiku; use `DEMO_MODE` locally; avoid chatty loops. |
| Lambda | Memory × duration × invocations. Keep timeout modest; no provisioned concurrency for demos. |
| API Gateway | HTTP API pricing; low for light traffic. |
| DynamoDB | On-demand for demos; avoid unused provisioned RCU/WCU. |
| S3 / CloudFront | Small for a static SPA; lifecycle on artifacts; minimize invalidations. |
| CloudWatch Logs | Set retention (e.g. 7–14 days). |

**Do not treat any number in docs as an AWS list price.** Use the AWS Pricing Calculator / console for estimates.

---

## 10. Deploy via GitHub Actions (OIDC)

See `.github/workflows/deploy.yml`. Configure:

- GitHub variable/secret placeholders: `AWS_ROLE_TO_ASSUME`, region, bucket, function name
- IAM OIDC identity provider for `token.actions.githubusercontent.com`
- Deploy role trust limited to this repo + `workflow_dispatch`

Prefer OIDC over long-lived `AWS_ACCESS_KEY_ID` in GitHub secrets.

---

## 11. Teardown (stop spend)

Order matters: API → Lambda → CloudFront → buckets → table → roles.

```bash
# API Gateway
aws apigatewayv2 delete-api --api-id "$API_ID"

# Lambda
aws lambda delete-function --function-name "$FUNC_NAME"

# CloudFront: disable then delete distribution in console (propagation delay), then:
# aws cloudfront delete-distribution --id YOUR_DISTRIBUTION_ID --if-match ETAG

# Empty and delete buckets
aws s3 rm "s3://${ARTIFACTS_BUCKET}" --recursive
aws s3api delete-bucket --bucket "$ARTIFACTS_BUCKET"
aws s3 rm "s3://${FRONTEND_BUCKET}" --recursive
aws s3api delete-bucket --bucket "$FRONTEND_BUCKET"

# DynamoDB
aws dynamodb delete-table --table-name "$DDB_TABLE"

# Log group
aws logs delete-log-group --log-group-name "/aws/lambda/$FUNC_NAME" || true

# IAM role: detach policies then delete-role
# aws iam detach-role-policy ...
# aws iam delete-role --role-name "$LAMBDA_ROLE_NAME"
```

Disable Bedrock model access if no longer needed to reduce accidental invoke risk.

---

## Console-only quick path (summary)

1. Create S3 buckets (artifacts + frontend) with Block Public Access.
2. Create DynamoDB table `id` (S), on-demand.
3. Enable Bedrock model (or skip and set `DEMO_MODE=true`).
4. Create Lambda role (basic logs + custom least privilege).
5. Upload zip; handler `app.lambda_handler.handler`; set env vars.
6. Create HTTP API with Lambda proxy + CORS.
7. Create CloudFront + OAC for frontend bucket; sync Vite `dist/`.
8. Hit `/health` and `/api/v1/demo/sample`.

---

## Related docs

- [LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md) — zero-AWS setup
- [SECURITY.md](./SECURITY.md) — secrets, IAM, Bedrock safeguards
- [LIMITATIONS.md](./LIMITATIONS.md) — what InfraPilot does not do
- Architecture diagrams under `docs/architecture/drawio/`
