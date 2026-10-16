import csv
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from .asset import Asset
from .metrics import max_drawdown, sharpe_ratio, value_at_risk, volatility
from .validation import (
    MAX_CSV_ROWS,
    MAX_SYMBOL_LENGTH,
    is_valid_symbol,
    parse_non_negative_float,
)


class PortfolioLoadError(Exception):
    """Raised when a portfolio cannot be loaded from a CSV file."""

    def __init__(self, message: str, filepath: Optional[str] = None, row: Optional[int] = None):
        self.filepath = filepath
        self.row = row
        if filepath:
            message = f"{message} (file: {filepath}" + (f", row: {row}" if row else "") + ")"
        super().__init__(message)


@dataclass
class DailyReturn:
    date: datetime
    value: float
    return_pct: float


class Portfolio:
    def __init__(self, name: str = "Portfolio"):
        self.name = name
        self.assets: list[Asset] = []
        self.history: list[DailyReturn] = []
        self.created_at = datetime.now()

    def add_asset(self, asset: Asset) -> None:
        existing = next((a for a in self.assets if a.symbol == asset.symbol), None)
        if existing:
            total_shares = existing.shares + asset.shares
            total_cost = existing.cost_basis() + asset.cost_basis()
            existing.shares = total_shares
            existing.avg_cost = total_cost / total_shares if total_shares > 0 else 0
        else:
            self.assets.append(asset)

    def remove_asset(self, symbol: str) -> bool:
        before = len(self.assets)
        self.assets = [a for a in self.assets if a.symbol != symbol]
        return len(self.assets) < before

    def get_asset(self, symbol: str) -> Optional[Asset]:
        return next((a for a in self.assets if a.symbol == symbol), None)

    def total_value(self) -> float:
        return sum(a.market_value() for a in self.assets)

    def total_cost(self) -> float:
        return sum(a.cost_basis() for a in self.assets)

    def total_pnl(self) -> float:
        return self.total_value() - self.total_cost()

    def total_return_pct(self) -> float:
        cost = self.total_cost()
        if cost == 0:
            return 0.0
        return self.total_pnl() / cost

    def asset_allocation(self) -> dict[str, float]:
        total = self.total_value()
        allocation: dict[str, float] = {}
        for asset in self.assets:
            cls = asset.asset_class
            allocation[cls] = allocation.get(cls, 0) + asset.market_value()
        if total > 0:
            allocation = {k: v / total for k, v in allocation.items()}
        return allocation

    def holdings_breakdown(self) -> list[dict[str, Union[float, str]]]:
        total = self.total_value()
        return [
            {
                "symbol": a.symbol,
                "shares": a.shares,
                "avg_cost": a.avg_cost,
                "current_price": a.current_price or a.avg_cost,
                "market_value": a.market_value(),
                "weight": a.weight(total),
                "pnl": a.unrealized_pnl(),
                "return_pct": a.return_pct(),
            }
            for a in sorted(self.assets, key=lambda x: x.market_value(), reverse=True)
        ]

    def record_daily(self, date: Optional[datetime] = None) -> None:
        date = date or datetime.now()
        value = self.total_value()
        if self.history:
            prev = self.history[-1].value
            ret = (value - prev) / prev if prev > 0 else 0.0
        else:
            ret = 0.0
        self.history.append(DailyReturn(date=date, value=value, return_pct=ret))

    def daily_returns(self) -> list[float]:
        return [d.return_pct for d in self.history]

    def sharpe_ratio(self, risk_free_rate: float = 0.05) -> float:
        return sharpe_ratio(self.daily_returns(), risk_free_rate)

    def max_drawdown(self) -> float:
        return max_drawdown(self.daily_returns())

    def volatility(self) -> float:
        return volatility(self.daily_returns())

    def value_at_risk(self, confidence: float = 0.95) -> float:
        return value_at_risk(self.daily_returns(), confidence) * self.total_value()

    def generate_report(self) -> str:
        lines = [
            f"Portfolio: {self.name}",
            f"Total Value: ${self.total_value():,.2f}",
            f"Total Cost: ${self.total_cost():,.2f}",
            f"Unrealized P&L: ${self.total_pnl():,.2f}",
            f"Return: {self.total_return_pct():.2%}",
            "",
            "Holdings:",
        ]
        for h in self.holdings_breakdown():
            lines.append(
                f"  {h['symbol']:6} {h['shares']:>8.1f} shares @ ${h['avg_cost']:>10.2f} "
                f"= ${h['market_value']:>12,.2f} ({h['return_pct']:>+.2%})"
            )
        lines.extend(
            [
                "",
                "Asset Allocation:",
            ]
        )
        for cls, weight in self.asset_allocation().items():
            lines.append(f"  {cls:12} {weight:.1%}")
        return "\n".join(lines)

    @classmethod
    def from_csv(cls, filepath: str, name: str = "Portfolio") -> "Portfolio":
        if not os.path.exists(filepath):
            raise PortfolioLoadError("Portfolio file not found", filepath=filepath)

        portfolio = cls(name=name)
        required_columns = {"symbol", "shares", "avg_cost"}

        try:
            # utf-8-sig transparently strips a leading BOM, which spreadsheet
            # and PowerShell exports commonly add, while still reading plain UTF-8.
            with open(filepath, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    raise PortfolioLoadError(
                        "CSV file is empty or has no header", filepath=filepath
                    )

                missing_columns = required_columns - set(reader.fieldnames)
                if missing_columns:
                    raise PortfolioLoadError(
                        f"Missing required columns: {', '.join(sorted(missing_columns))}",
                        filepath=filepath,
                    )

                for row_num, row in enumerate(reader, start=2):  # start=2 because header is row 1
                    if row_num - 1 > MAX_CSV_ROWS:
                        raise PortfolioLoadError(
                            f"CSV file exceeds the maximum of {MAX_CSV_ROWS} rows",
                            filepath=filepath,
                            row=row_num,
                        )
                    try:
                        symbol = (row.get("symbol") or "").strip()
                        if not symbol:
                            raise PortfolioLoadError(
                                "Empty symbol in row",
                                filepath=filepath,
                                row=row_num,
                            )
                        if not is_valid_symbol(symbol):
                            raise PortfolioLoadError(
                                f"Invalid symbol {symbol!r}: expected 1-{MAX_SYMBOL_LENGTH} "
                                "alphanumeric characters ('.', '_' and '-' allowed after "
                                "the first)",
                                filepath=filepath,
                                row=row_num,
                            )

                        shares_str = (row.get("shares") or "").strip()
                        if not shares_str:
                            raise PortfolioLoadError(
                                "Missing shares value",
                                filepath=filepath,
                                row=row_num,
                            )
                        shares = parse_non_negative_float(shares_str, "shares")

                        avg_cost_str = (row.get("avg_cost") or "").strip()
                        if not avg_cost_str:
                            raise PortfolioLoadError(
                                "Missing avg_cost value",
                                filepath=filepath,
                                row=row_num,
                            )
                        avg_cost = parse_non_negative_float(avg_cost_str, "avg_cost")

                        current_price = None
                        current_price_str = (row.get("current_price") or "").strip()
                        if current_price_str:
                            current_price = parse_non_negative_float(
                                current_price_str, "current_price"
                            )

                        asset_class = (row.get("asset_class") or "equity").strip() or "equity"

                        portfolio.add_asset(
                            Asset(
                                symbol=symbol,
                                shares=shares,
                                avg_cost=avg_cost,
                                current_price=current_price,
                                asset_class=asset_class,
                            )
                        )
                    except ValueError as e:
                        raise PortfolioLoadError(str(e), filepath=filepath, row=row_num) from e
                    except PortfolioLoadError:
                        raise
                    except Exception as e:
                        raise PortfolioLoadError(
                            f"Unexpected error parsing row: {e}",
                            filepath=filepath,
                            row=row_num,
                        ) from e

        except PortfolioLoadError:
            raise
        except OSError as e:
            raise PortfolioLoadError(f"Failed to read file: {e}", filepath=filepath) from e

        if not portfolio.assets:
            raise PortfolioLoadError("No valid assets found in CSV", filepath=filepath)

        return portfolio
