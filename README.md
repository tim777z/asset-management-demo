# Asset Management Demo

A Python-based portfolio analytics toolkit for tracking assets, calculating risk metrics, and generating performance reports.

## Features

- **Portfolio Tracking**: Track positions across multiple asset classes (stocks, crypto, bonds, forex)
- **Risk Metrics**: VaR, Sharpe ratio, max drawdown, beta, volatility
- **Performance Reports**: Daily P&L, attribution analysis, benchmark comparison
- **CSV Import**: Load portfolio data from CSV files
- **CLI Interface**: Command-line tool for quick analysis

## Installation

### Standard Installation

```bash
pip install -e ".[dev]"
```

### Reproducible Installation (Recommended for Production)

For exact dependency reproduction, use the committed lockfile:

```bash
pip install -r requirements-dev.lock.txt
pip install -e . --no-deps
```

This ensures all dependencies are pinned to specific versions, guaranteeing identical environments across development, CI, and production.

## Usage

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

## CLI Usage

```bash
# Create a new portfolio
asset-manager create "My Portfolio"

# Generate report from CSV
asset-manager report portfolio.csv

# Add asset to portfolio
asset-manager add portfolio.csv AAPL --shares 100 --cost 150.00 --price 175.00
```

## Testing

Run the test suite with coverage:

```bash
pytest --cov=asset_manager --cov-report=term-missing --cov-fail-under=70
```

## Code Quality

Lint and format checks:

```bash
ruff check src tests
ruff format --check src tests
```

Type checking:

```bash
mypy src
```

## Continuous Integration

This project uses GitHub Actions for CI. The pipeline runs on every push and pull request:

- **Lint**: Ruff checks for style and correctness
- **Type Check**: MyPy static type analysis
- **Test**: Pytest with coverage enforcement (minimum 70%)

See `.github/workflows/ci.yml` for details.

## License

Proprietary - PreCog Security. All rights reserved.
