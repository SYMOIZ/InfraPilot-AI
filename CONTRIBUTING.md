# Contributing to InfraPilot AI

Thanks for helping improve InfraPilot AI.

## Ground rules

- InfraPilot **designs and evaluates** architectures; it must **not** gain features that auto-deploy customer infra or emit Terraform/CloudFormation as a primary output.
- Do not invent AWS list prices or paste production IAM policies with real account secrets.
- Never commit `.env`, keys, or customer diagrams with sensitive data.
- Prefer `DEMO_MODE` for tests and local demos.

## Development setup

Follow [docs/LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md).

```bash
python -m venv .venv
# activate venv
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
pytest
ruff check backend agent rules
```

## Pull requests

1. Branch from the default branch with a focused change.
2. Include tests for behavior changes under `tests/`.
3. Update docs under `docs/` when behavior or deploy steps change.
4. Fill out the PR template.
5. Ensure CI (lint, test, builds) is green.

## Issues

Use the bug / feature templates under `.github/ISSUE_TEMPLATE/`. Mark items that depend on **planned** AWS hosting clearly.

## Architecture docs

Editable diagrams live in `docs/architecture/drawio/`. Regenerate the Excel workbook with:

```bash
python docs/architecture/_generate_architecture_xlsx.py
```

## License

By contributing, you agree your contributions are licensed under the MIT License (see `LICENSE`).
