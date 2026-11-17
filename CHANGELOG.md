# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-11-17

### Added

- Enhanced input validation: `CsvRowSchema` dataclass in `validation.py` with
  explicit field types and bounds, and `parse_decimal` using `decimal.Decimal`
  for exact arithmetic.
- Structured CSV row schema validation at the trust boundary, replacing ad-hoc
  manual checks in `Portfolio.from_csv`.
- `docker-compose.yml` for one-command reproducibility: `docker compose up --build`
  builds from the existing Dockerfile and mounts `./data` to `/data` for CSV input.
- New unreleased changes summarised above.

### Changed

- `Portfolio.from_csv` now uses `parse_non_negative_float` (alias for
  `parse_decimal`) for consistent numeric parsing.
- Validation module reorganised: `parse_non_negative_float` now delegates to
  `parse_decimal`; `math` import removed in favour of `decimal.Decimal`.

## [1.0.0] - 2026-09-23

### Added

- Initial portfolio analytics toolkit: `Asset`, `Portfolio`, risk metrics
  (Sharpe, VaR, max drawdown, beta, volatility, and more), CSV import, and a
  command-line interface.
- Pytest suite with coverage enforcement, Ruff linting, and MyPy type checking.

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
