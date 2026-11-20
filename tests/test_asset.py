"""Direct edge-case tests for the public Asset value object.

The zero-denominator guards here keep reports free of division-by-zero and
NaN values when a portfolio holds no cost basis or has no total value.
"""

from asset_manager.asset import Asset


class TestAssetEdgeCases:
    def test_zero_cost_basis_returns_zero_pct(self):
        asset = Asset(symbol="AAPL", shares=0, avg_cost=0, current_price=100)
        assert asset.cost_basis() == 0
        assert asset.market_value() == 0
        assert asset.return_pct() == 0.0

    def test_zero_portfolio_value_returns_zero_weight(self):
        asset = Asset(symbol="AAPL", shares=10, avg_cost=5)
        assert asset.weight(0.0) == 0.0

    def test_current_price_defaults_to_avg_cost(self):
        asset = Asset(symbol="AAPL", shares=2, avg_cost=10)
        assert asset.market_value() == 20
        assert asset.unrealized_pnl() == 0
        assert asset.return_pct() == 0.0

    def test_current_price_drives_market_value_and_ratios(self):
        asset = Asset(symbol="AAPL", shares=2, avg_cost=10, current_price=12.5)
        assert asset.market_value() == 25
        assert asset.unrealized_pnl() == 5
        assert asset.return_pct() == 0.25
        assert asset.weight(100) == 0.25
