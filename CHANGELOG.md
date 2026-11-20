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
- New `history` CLI subcommand: computes mean return, Sharpe, Sortino, annualized
  volatility, max drawdown and 95% VaR from a validated `date,value` history CSV,
  with tests covering success and malformed-input paths.
- Dedicated `tests/test_validation.py` covering `CsvRowSchema`, symbol rules and
  numeric parsing at the trust boundary.
- Dedicated `tests/test_asset.py` covering zero-cost/zero-value guards and the
  current-price fallback used by market-value calculations.
- Conventional `requirements.txt` / `requirements-dev.txt` entry points for tools
  that discover dependencies by filename; the pinned `.lock.txt` stays authoritative.
- `build` added to pinned dev dependencies so `make build` works from a fresh clone.
- Packaging metadata uses the SPDX `LicenseRef-Proprietary` expression and
  `license-files`; `setuptools>=77.0.3` is required so builds stay supported
  after the legacy `project.license` table is removed in Feb 2027.

### Changed

- `Portfolio.from_csv` now uses `parse_non_negative_float` (alias for
  `parse_decimal`) for consistent numeric parsing.
- Validation module reorganised: `parse_non_negative_float` now delegates to
  `parse_decimal`; `math` import removed in favour of `decimal.Decimal`.
- `Portfolio.from_csv` now actually constructs `CsvRowSchema` for every row, making
  the documented single validation contract real instead of dead code, and removes
  the duplicated ad-hoc symbol check.

### Fixed

- `is_valid_symbol` now uses a full-string match instead of a `$`-anchored pattern;
  a trailing newline (e.g. `"AAPL\n"`) previously passed validation and could
  forge an extra row in an exported CSV.
- `parse_decimal` now rejects values that overflow to `inf` on float conversion,
  preserving its finite-float contract for CLI and CSV input.
- Unexpected CLI exceptions are now emitted as one structured JSON error record
  and exit with status 1 instead of surfacing a bare Python traceback.
- CI lint, typecheck and test jobs now install from `requirements-dev.lock.txt`,
  matching the documented reproducible-install path and the dedicated lockfile job.

### Security

- Free-text validation also rejects DEL (0x7F) and Unicode line/paragraph
  separators (U+2028/U+2029), and the CLI `--class` argument now uses the same
  formula/control-character rules as CSV input.
- `.env` and `.env.*` are gitignored and excluded from the Docker build context;
  only `.env.example` remains tracked.
- `CsvRowSchema` now rejects NaN and infinities explicitly. Previously `nan < 0` is
  false, so non-finite values could pass the schema's bounds checks.
- Free-text CSV fields (`asset_class`) are now checked for spreadsheet formula
  prefixes (`=`, `+`, `-`, `@`) and control characters before reaching reports or
  exported CSV, closing a CSV-injection path that the symbol allowlist did not cover.
- README documents the structured JSON logging contract and classification metadata.

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
