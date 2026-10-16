# Contributing

Thanks for improving the Asset Management Demo. This document describes the
local workflow and the checks your change must pass.

## Development setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements-dev.lock.txt
pip install -e . --no-deps
```

## Before you open a pull request

Run the full local check suite:

```bash
make check
```

which is equivalent to:

```bash
ruff check src tests
ruff format --check src tests
mypy src
pytest --cov=asset_manager --cov-report=term-missing --cov-fail-under=70
```

All four must pass. CI runs the same checks plus a reproducible-install job and
a `pip-audit` dependency scan.

## Guidelines

- **Keep changes small and focused.** One feature or fix per commit, with the
  tests that pin the new behaviour in the same commit.
- **Add tests for new behaviour**, including the failure paths. Coverage must
  stay at or above 70%.
- **Validate untrusted input** at the boundary (CSV rows and CLI arguments)
  using the helpers in `asset_manager.validation`.
- **Keep the code typed.** `mypy --strict` must stay clean.
- **Update the docs.** Add user-visible changes to `CHANGELOG.md` and update
  `README.md` when behaviour or usage changes.

## Reporting security issues

Do not open a public issue for a suspected vulnerability. Report it privately
to the maintainers so it can be triaged before disclosure.
