import argparse
import logging
import sys

from .asset import Asset
from .portfolio import Portfolio, PortfolioLoadError
from .validation import is_valid_symbol, parse_non_negative_float

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


def _configure_logging(verbose: bool, quiet: bool) -> None:
    """Point the package logger at stderr with a level derived from the flags."""
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    logger.setLevel(level)
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def main() -> None:
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
    add_cmd.add_argument("--class", dest="asset_class", default="equity")

    report_cmd = subparsers.add_parser("report", help="Generate report")
    report_cmd.add_argument("portfolio", help="Portfolio file")

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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
