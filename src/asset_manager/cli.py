import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime

from .asset import Asset
from .metrics import (
    max_drawdown,
    mean,
    sharpe_ratio,
    sortino_ratio,
    value_at_risk,
    volatility,
)
from .portfolio import Portfolio, PortfolioLoadError
from .validation import (
    MAX_CSV_ROWS,
    is_safe_text_field,
    is_valid_symbol,
    parse_non_negative_float,
)

logger = logging.getLogger("asset_manager.cli")


def _non_negative_float(value: str) -> float:
    """Argparse type that rejects negative and non-finite numbers."""
    try:
        return parse_non_negative_float(value, "value")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _symbol(value: str) -> str:
    """Argparse type that rejects malformed asset symbols."""
    symbol = value.strip()
    if not is_valid_symbol(symbol):
        raise argparse.ArgumentTypeError(f"invalid symbol: {value!r}")
    return symbol


def _asset_class(value: str) -> str:
    """Apply the CSV schema's free-text rules to the CLI --class argument.

    CSV rows are checked by ``CsvRowSchema``; without this type the CLI path
    could inject spreadsheet formulas or control characters that the CSV path
    rejects, breaking the single validation contract documented in the README.
    """
    normalized = value.strip() or "equity"
    if not is_safe_text_field(normalized):
        raise argparse.ArgumentTypeError(f"invalid asset class: {value!r}")
    return normalized


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single line of structured JSON.

    Structured output lets downstream tooling (log aggregators, CI, auditors)
    parse level and message without scraping free-form text, while remaining
    human-readable enough for a terminal.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _load_daily_returns(filepath: str) -> list[float]:
    """Read a ``date,value`` history CSV and return its daily simple returns.

    The loader applies the same trust-boundary rules as the holdings loader:
    UTF-8 (with optional BOM), required-column checks, a row cap, strict date
    parsing and finite non-negative values. The first observation has no prior
    value and therefore yields a 0% return.
    """
    if not os.path.exists(filepath):
        raise PortfolioLoadError("History file not found", filepath=filepath)

    values: list[float] = []
    try:
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise PortfolioLoadError(
                    "History file is empty or has no header", filepath=filepath
                )
            missing = {"date", "value"} - set(reader.fieldnames)
            if missing:
                raise PortfolioLoadError(
                    f"Missing required columns: {', '.join(sorted(missing))}",
                    filepath=filepath,
                )

            for row_num, row in enumerate(reader, start=2):
                if row_num - 1 > MAX_CSV_ROWS:
                    raise PortfolioLoadError(
                        f"History file exceeds the maximum of {MAX_CSV_ROWS} rows",
                        filepath=filepath,
                        row=row_num,
                    )
                try:
                    raw_date = (row.get("date") or "").strip()
                    raw_value = (row.get("value") or "").strip()
                    if not raw_date or not raw_value:
                        raise PortfolioLoadError(
                            "Empty date or value in row", filepath=filepath, row=row_num
                        )
                    _ = datetime.fromisoformat(raw_date)
                    values.append(parse_non_negative_float(raw_value, "value"))
                except ValueError as exc:
                    raise PortfolioLoadError(str(exc), filepath=filepath, row=row_num) from exc
                except PortfolioLoadError:
                    raise
    except PortfolioLoadError:
        raise
    except OSError as exc:
        raise PortfolioLoadError(f"Failed to read file: {exc}", filepath=filepath) from exc

    if not values:
        raise PortfolioLoadError("No valid history rows found", filepath=filepath)

    returns: list[float] = [0.0]
    for previous, current in zip(values, values[1:]):
        returns.append((current - previous) / previous if previous > 0 else 0.0)
    return returns


def _configure_logging(verbose: bool, quiet: bool) -> None:
    """Point the package logger at stderr with a level derived from the flags.

    When neither ``--verbose`` nor ``--quiet`` is given, the ``LOG_LEVEL``
    environment variable (if set and valid) selects the level, defaulting to
    ``INFO``. Explicit flags always take precedence.
    """
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
        env_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
        candidate = getattr(logging, env_level, None)
        if isinstance(candidate, int):
            level = candidate
    logger.setLevel(level)
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False


def _run_cli() -> None:
    parser = argparse.ArgumentParser(description="Asset Management Toolkit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only log errors")
    subparsers = parser.add_subparsers(dest="command")

    create_cmd = subparsers.add_parser("create", help="Create a new portfolio")
    create_cmd.add_argument("name", help="Portfolio name")

    add_cmd = subparsers.add_parser("add", help="Add an asset")
    add_cmd.add_argument("portfolio", help="Portfolio file")
    add_cmd.add_argument("symbol", type=_symbol, help="Asset symbol")
    add_cmd.add_argument("--shares", type=_non_negative_float, required=True)
    add_cmd.add_argument("--cost", type=_non_negative_float, required=True)
    add_cmd.add_argument("--price", type=_non_negative_float, default=None)
    add_cmd.add_argument("--class", dest="asset_class", type=_asset_class, default="equity")

    report_cmd = subparsers.add_parser("report", help="Generate report")
    report_cmd.add_argument("portfolio", help="Portfolio file")

    history_cmd = subparsers.add_parser(
        "history", help="Compute risk metrics from a date,value history CSV"
    )
    history_cmd.add_argument("history", help="History CSV with date and value columns")

    args = parser.parse_args()
    _configure_logging(args.verbose, args.quiet)

    if args.command == "create":
        p = Portfolio(name=args.name)
        logger.debug("Created in-memory portfolio %r", p.name)
        print(f"Created portfolio: {args.name}")
    elif args.command == "add":
        try:
            p = Portfolio.from_csv(args.portfolio)
        except PortfolioLoadError as e:
            logger.error("Error loading portfolio: %s", e)
            sys.exit(1)
        p.add_asset(
            Asset(
                symbol=args.symbol,
                shares=args.shares,
                avg_cost=args.cost,
                current_price=args.price,
                asset_class=args.asset_class,
            )
        )
        logger.debug("Added %s to portfolio %r (%d holdings)", args.symbol, p.name, len(p.assets))
        print(f"Added {args.symbol} to {p.name}")
    elif args.command == "report":
        try:
            p = Portfolio.from_csv(args.portfolio)
        except PortfolioLoadError as e:
            logger.error("Error loading portfolio: %s", e)
            sys.exit(1)
        logger.debug("Loaded portfolio %r with %d holdings", p.name, len(p.assets))
        print(p.generate_report())
    elif args.command == "history":
        try:
            returns = _load_daily_returns(args.history)
        except PortfolioLoadError as e:
            logger.error("Error loading history: %s", e)
            sys.exit(1)
        logger.debug("Loaded %d history observations", len(returns))
        print(f"Observations: {len(returns)}")
        print(f"Mean daily return: {mean(returns):.2%}")
        print(f"Sharpe ratio: {sharpe_ratio(returns):.4f}")
        print(f"Sortino ratio: {sortino_ratio(returns):.4f}")
        print(f"Volatility (annualized): {volatility(returns):.2%}")
        print(f"Max drawdown: {max_drawdown(returns):.2%}")
        print(f"Value at Risk (95%): {value_at_risk(returns):.2%}")
    else:
        parser.print_help()


def main() -> None:
    """CLI entry point: turn unexpected failures into one structured error.

    Expected errors already exit explicitly with a structured log record.
    Any other exception is logged with traceback detail for operators as a
    single JSON record, then surfaced as a non-zero exit status. This avoids
    leaking local paths and internal state in a bare Python traceback while
    keeping the failure machine-readable for automation and log aggregation.
    """
    try:
        _run_cli()
    except Exception:  # SystemExit/KeyboardInterrupt are BaseException and pass through
        if not logger.handlers:
            _configure_logging(verbose=False, quiet=False)
        logger.error("Unexpected error in asset-manager", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
