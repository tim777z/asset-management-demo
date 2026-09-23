from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Asset:
    symbol: str
    shares: float
    avg_cost: float
    current_price: Optional[float] = None
    asset_class: str = "equity"
    name: Optional[str] = None
    purchase_date: Optional[datetime] = None

    def market_value(self) -> float:
        price = self.current_price if self.current_price is not None else self.avg_cost
        return self.shares * price

    def cost_basis(self) -> float:
        return self.shares * self.avg_cost

    def unrealized_pnl(self) -> float:
        return self.market_value() - self.cost_basis()

    def return_pct(self) -> float:
        cost = self.cost_basis()
        if cost == 0:
            return 0.0
        return self.unrealized_pnl() / cost

    def weight(self, total_portfolio_value: float) -> float:
        if total_portfolio_value == 0:
            return 0.0
        return self.market_value() / total_portfolio_value
