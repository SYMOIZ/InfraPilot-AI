#!/usr/bin/env bash
# Non-interactive teardown for InfraPilot AI prototype (CI / sunset pipeline).
# Usage: ./scripts/teardown-auto.sh [region]
set -euo pipefail

REGION="${1:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ARTIFACTS_BUCKET="infrapilot-artifacts-${ACCOUNT_ID}-${REGION}"
FRONTEND_BUCKET="infrapilot-frontend-${ACCOUNT_ID}-${REGION}"
DDB_TABLE="infrapilot-projects"
FUNC_NAME="infrapilot-api"
ROLE_NAME="infrapilot-lambda-role"
API_NAME="infrapilot-http-api"
DIST_COMMENT="InfraPilot AI frontend"
OAC_NAME="infrapilot-frontend-oac"
SCHEDULE_NAME="infrapilot-sunset-2026-11-08"

echo "Sunset teardown starting: account=${ACCOUNT_ID} region=${REGION}"

# HTTP APIs
mapfile -t API_IDS < <(aws apigatewayv2 get-apis --region "$REGION" \
  --query "Items[?Name=='${API_NAME}'].ApiId" --output text | tr '\t' '\n' | sed '/^$/d' || true)
for id in "${API_IDS[@]:-}"; do
  echo "Deleting API $id"
  aws apigatewayv2 delete-api --api-id "$id" --region "$REGION" || true
done

# Lambda
aws lambda delete-function --function-name "$FUNC_NAME" --region "$REGION" 2>/dev/null || true

# DynamoDB
aws dynamodb delete-table --table-name "$DDB_TABLE" --region "$REGION" 2>/dev/null || true

# S3 buckets
aws s3 rb "s3://${FRONTEND_BUCKET}" --force 2>/dev/null || true
aws s3 rb "s3://${ARTIFACTS_BUCKET}" --force 2>/dev/null || true

# CloudFront — disable then delete (may need follow-up if still deploying)
DIST_ID="$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='${DIST_COMMENT}'].Id | [0]" \
  --output text 2>/dev/null || true)"
if [[ -n "${DIST_ID}" && "${DIST_ID}" != "None" ]]; then
  echo "Disabling CloudFront ${DIST_ID}"
  ETAG="$(aws cloudfront get-distribution-config --id "$DIST_ID" --query ETag --output text)"
  aws cloudfront get-distribution-config --id "$DIST_ID" --query DistributionConfig \
    > /tmp/cf-config.json
  # set Enabled=false via jq if available
  if command -v jq >/dev/null 2>&1; then
    jq '.Enabled = false' /tmp/cf-config.json > /tmp/cf-disabled.json
    aws cloudfront update-distribution --id "$DIST_ID" --if-match "$ETAG" \
      --distribution-config file:///tmp/cf-disabled.json >/dev/null || true
  fi
  echo "CloudFront ${DIST_ID} disable requested — delete manually after Status=Deployed if needed."
fi

# IAM role
aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name infrapilot-access 2>/dev/null || true
aws iam detach-role-policy --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>/dev/null || true
aws iam delete-role --role-name "$ROLE_NAME" 2>/dev/null || true

# Sunset schedule (self-clean)
aws scheduler delete-schedule --name "$SCHEDULE_NAME" --region "$REGION" 2>/dev/null || true

# Cleanup helper Lambda if present
aws lambda delete-function --function-name infrapilot-sunset-cleaner --region "$REGION" 2>/dev/null || true

echo "Teardown complete (CloudFront may need a final console delete after disable propagates)."
