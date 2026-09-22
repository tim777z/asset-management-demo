from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
import csv
import os

from .asset import Asset
from .metrics import sharpe_ratio, max_drawdown, value_at_risk, volatility


@dataclass
class DailyReturn:
    date: datetime
    value: float
    return_pct: float


class Portfolio:
    def __init__(self, name: str = "Portfolio"):
        self.name = name
        self.assets: List[Asset] = []
        self.history: List[DailyReturn] = []
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

    def asset_allocation(self) -> Dict[str, float]:
        total = self.total_value()
        allocation = {}
        for asset in self.assets:
            cls = asset.asset_class
            allocation[cls] = allocation.get(cls, 0) + asset.market_value()
        if total > 0:
            allocation = {k: v / total for k, v in allocation.items()}
        return allocation

    def holdings_breakdown(self) -> List[Dict]:
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

    def daily_returns(self) -> List[float]:
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
        lines.extend([
            "",
            "Asset Allocation:",
        ])
        for cls, weight in self.asset_allocation().items():
            lines.append(f"  {cls:12} {weight:.1%}")
        return "\n".join(lines)

    @classmethod
    def from_csv(cls, filepath: str, name: str = "Portfolio") -> "Portfolio":
        portfolio = cls(name=name)
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                portfolio.add_asset(
                    Asset(
                        symbol=row["symbol"],
                        shares=float(row["shares"]),
                        avg_cost=float(row["avg_cost"]),
                        current_price=float(row.get("current_price", 0)) or None,
                        asset_class=row.get("asset_class", "equity"),
                    )
                )
        return portfolio
