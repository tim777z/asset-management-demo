# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Shared input-validation module (`asset_manager.validation`) with symbol and
  non-negative finite-number checks.
- CLI `--verbose`/`--quiet` flags and structured logging on error paths.
- Dockerfile (non-root runtime image) and `.dockerignore`.
- `Makefile` with `install`, `install-lock`, `test`, `lint`, `typecheck`,
  `check`, `build`, and `clean` targets.
- CI lockfile-verification job and `pip-audit` dependency-audit job.
- Dependabot configuration for pip and GitHub Actions.
- `CONTRIBUTING.md` and this changelog.

### Changed

- `Portfolio.from_csv` now rejects non-finite (`nan`/`inf`) numbers, malformed
  symbols, and files exceeding the row cap, and reads files as UTF-8.
- `PortfolioLoadError` is now exported from the top-level package.
- Ruff lint configuration moved under `[tool.ruff.lint]` (non-deprecated layout).

## [1.0.0] - 2026-09-23

### Added

- Initial portfolio analytics toolkit: `Asset`, `Portfolio`, risk metrics
  (Sharpe, VaR, max drawdown, beta, volatility, and more), CSV import, and a
  command-line interface.
- Pytest suite with coverage enforcement, Ruff linting, and MyPy type checking.
