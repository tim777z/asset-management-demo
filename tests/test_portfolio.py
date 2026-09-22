import pytest
from asset_manager import Asset, Portfolio


def test_asset_market_value():
    asset = Asset(symbol="AAPL", shares=100, avg_cost=150.00, current_price=175.00)
    assert asset.market_value() == 17500.00


def test_asset_cost_basis():
    asset = Asset(symbol="AAPL", shares=100, avg_cost=150.00)
    assert asset.cost_basis() == 15000.00


def test_asset_unrealized_pnl():
    asset = Asset(symbol="AAPL", shares=100, avg_cost=150.00, current_price=175.00)
    assert asset.unrealized_pnl() == 2500.00


def test_asset_return_pct():
    asset = Asset(symbol="AAPL", shares=100, avg_cost=150.00, current_price=175.00)
    assert asset.return_pct() == pytest.approx(0.1667, rel=1e-3)


def test_portfolio_add_asset():
    p = Portfolio(name="Test")
    p.add_asset(Asset(symbol="AAPL", shares=100, avg_cost=150.00))
    assert len(p.assets) == 1
    assert p.total_value() == 15000.00


def test_portfolio_merge_duplicate():
    p = Portfolio(name="Test")
    p.add_asset(Asset(symbol="AAPL", shares=100, avg_cost=150.00))
    p.add_asset(Asset(symbol="AAPL", shares=50, avg_cost=200.00))
    assert len(p.assets) == 1
    assert p.assets[0].shares == 150
    assert p.assets[0].avg_cost == pytest.approx(166.67, rel=1e-2)


def test_portfolio_remove_asset():
    p = Portfolio(name="Test")
    p.add_asset(Asset(symbol="AAPL", shares=100, avg_cost=150.00))
    assert p.remove_asset("AAPL")
    assert len(p.assets) == 0
    assert not p.remove_asset("MSFT")


def test_portfolio_total_value():
    p = Portfolio(name="Test")
    p.add_asset(Asset(symbol="AAPL", shares=100, avg_cost=150.00, current_price=175.00))
    p.add_asset(Asset(symbol="GOOGL", shares=50, avg_cost=2800.00, current_price=2900.00))
    assert p.total_value() == 17500 + 145000


def test_portfolio_allocation():
    p = Portfolio(name="Test")
    p.add_asset(Asset(symbol="AAPL", shares=1, avg_cost=100.00, current_price=100.00, asset_class="equity"))
    p.add_asset(Asset(symbol="BTC", shares=1, avg_cost=100.00, current_price=100.00, asset_class="crypto"))
    alloc = p.asset_allocation()
    assert alloc["equity"] == pytest.approx(0.5, rel=1e-2)
    assert alloc["crypto"] == pytest.approx(0.5, rel=1e-2)


def test_portfolio_report():
    p = Portfolio(name="Test")
    p.add_asset(Asset(symbol="AAPL", shares=100, avg_cost=150.00, current_price=175.00))
    report = p.generate_report()
    assert "Test" in report
    assert "$17,500.00" in report


def test_portfolio_from_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\nGOOGL,50,2800,2900,equity\n")
    p = Portfolio.from_csv(str(csv_file), name="CSV Portfolio")
    assert len(p.assets) == 2
    assert p.total_value() == pytest.approx(17500 + 145000)
