## Summary

Briefly describe why this change is needed.

## Changes

-
-

## Test plan

- [ ] `pytest` passes with `DEMO_MODE=true`
- [ ] `ruff check backend agent rules` (if Python touched)
- [ ] Frontend build (if `frontend/` touched)
- [ ] Manual smoke: `/health` and/or `/api/v1/demo/sample`

## Docs

- [ ] Updated `docs/` if behavior or deploy steps changed
- [ ] Architecture labels (IMPLEMENTED vs PLANNED) still accurate

## Checklist

- [ ] No secrets, `.env`, or credentials in the diff
- [ ] Does not add IaC generation or live infra deployment features
- [ ] Cost/Bedrock impact considered (prefer mocks in tests)
