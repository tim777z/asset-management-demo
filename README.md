# Asset Management Demo

A Python-based portfolio analytics toolkit for tracking assets, calculating risk metrics, and generating performance reports.

## Features

- **Portfolio Tracking**: Track positions across multiple asset classes (stocks, crypto, bonds, forex)
- **Risk Metrics**: VaR, Sharpe ratio, max drawdown, beta, volatility
- **Performance Reports**: Daily P&L, attribution analysis, benchmark comparison
- **CSV Import**: Load portfolio data from CSV files
- **CLI Interface**: Command-line tool for quick analysis

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```python
from asset_manager import Portfolio, Asset

# Create portfolio
portfolio = Portfolio(name="My Portfolio")
portfolio.add_asset(Asset(symbol="AAPL", shares=100, avg_cost=150.00))
portfolio.add_asset(Asset(symbol="GOOGL", shares=50, avg_cost=2800.00))

# Calculate metrics
print(f"Total Value: ${portfolio.total_value():,.2f}")
print(f"Sharpe Ratio: {portfolio.sharpe_ratio():.2f}")
print(f"Max Drawdown: {portfolio.max_drawdown():.2%}")
```

## License

Proprietary - PreCog Security. All rights reserved.
