import argparse
import sys
from datetime import datetime

from .portfolio import Portfolio
from .asset import Asset


def main():
    parser = argparse.ArgumentParser(description="Asset Management Toolkit")
    subparsers = parser.add_subparsers(dest="command")

    create_cmd = subparsers.add_parser("create", help="Create a new portfolio")
    create_cmd.add_argument("name", help="Portfolio name")

    add_cmd = subparsers.add_parser("add", help="Add an asset")
    add_cmd.add_argument("portfolio", help="Portfolio file")
    add_cmd.add_argument("symbol", help="Asset symbol")
    add_cmd.add_argument("--shares", type=float, required=True)
    add_cmd.add_argument("--cost", type=float, required=True)
    add_cmd.add_argument("--price", type=float, default=None)
    add_cmd.add_argument("--class", dest="asset_class", default="equity")

    report_cmd = subparsers.add_parser("report", help="Generate report")
    report_cmd.add_argument("portfolio", help="Portfolio file")

    args = parser.parse_args()

    if args.command == "create":
        p = Portfolio(name=args.name)
        print(f"Created portfolio: {args.name}")
    elif args.command == "add":
        p = Portfolio.from_csv(args.portfolio)
        p.add_asset(Asset(
            symbol=args.symbol,
            shares=args.shares,
            avg_cost=args.cost,
            current_price=args.price,
            asset_class=args.asset_class,
        ))
        print(f"Added {args.symbol} to {p.name}")
    elif args.command == "report":
        p = Portfolio.from_csv(args.portfolio)
        print(p.generate_report())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
