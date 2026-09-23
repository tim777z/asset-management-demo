import pytest

from asset_manager import Asset, Portfolio
from asset_manager.portfolio import PortfolioLoadError


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
    p.add_asset(
        Asset(
            symbol="AAPL",
            shares=1,
            avg_cost=100.00,
            current_price=100.00,
            asset_class="equity",
        )
    )
    p.add_asset(
        Asset(
            symbol="BTC",
            shares=1,
            avg_cost=100.00,
            current_price=100.00,
            asset_class="crypto",
        )
    )
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
    csv_file.write_text(
        "symbol,shares,avg_cost,current_price,asset_class\nAAPL,100,150,175,equity\nGOOGL,50,2800,2900,equity\n"
    )
    p = Portfolio.from_csv(str(csv_file), name="CSV Portfolio")
    assert len(p.assets) == 2
    assert p.total_value() == pytest.approx(17500 + 145000)


class TestPortfolioFromCSVErrors:
    def test_from_csv_missing_file(self):
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv("nonexistent.csv")
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.filepath == "nonexistent.csv"

    def test_from_csv_empty_file(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "empty" in str(exc_info.value).lower()

    def test_from_csv_missing_required_columns(self, tmp_path):
        csv_file = tmp_path / "bad_columns.csv"
        csv_file.write_text("symbol,shares\nAAPL,100\n")  # missing avg_cost
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "avg_cost" in str(exc_info.value)

    def test_from_csv_empty_symbol(self, tmp_path):
        csv_file = tmp_path / "empty_symbol.csv"
        csv_file.write_text("symbol,shares,avg_cost\n,100,150\n")
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "empty symbol" in str(exc_info.value).lower()
        assert exc_info.value.row == 2

    def test_from_csv_missing_shares(self, tmp_path):
        csv_file = tmp_path / "missing_shares.csv"
        csv_file.write_text("symbol,shares,avg_cost\nAAPL,,150\n")
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "missing shares" in str(exc_info.value).lower()

    def test_from_csv_negative_shares(self, tmp_path):
        csv_file = tmp_path / "negative_shares.csv"
        csv_file.write_text("symbol,shares,avg_cost\nAAPL,-100,150\n")
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "negative" in str(exc_info.value).lower()

    def test_from_csv_missing_avg_cost(self, tmp_path):
        csv_file = tmp_path / "missing_avg_cost.csv"
        csv_file.write_text("symbol,shares,avg_cost\nAAPL,100,\n")
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "missing avg_cost" in str(exc_info.value).lower()

    def test_from_csv_negative_avg_cost(self, tmp_path):
        csv_file = tmp_path / "negative_avg_cost.csv"
        csv_file.write_text("symbol,shares,avg_cost\nAAPL,100,-150\n")
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "negative" in str(exc_info.value).lower()

    def test_from_csv_negative_current_price(self, tmp_path):
        csv_file = tmp_path / "negative_price.csv"
        csv_file.write_text("symbol,shares,avg_cost,current_price\nAAPL,100,150,-175\n")
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "negative" in str(exc_info.value).lower()

    def test_from_csv_invalid_numeric(self, tmp_path):
        csv_file = tmp_path / "invalid_numeric.csv"
        csv_file.write_text("symbol,shares,avg_cost\nAAPL,abc,150\n")
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "invalid numeric" in str(exc_info.value).lower()

    def test_from_csv_no_valid_assets(self, tmp_path):
        csv_file = tmp_path / "no_assets.csv"
        csv_file.write_text("symbol,shares,avg_cost\n\n")  # header only, no data rows
        with pytest.raises(PortfolioLoadError) as exc_info:
            Portfolio.from_csv(str(csv_file))
        assert "no valid assets" in str(exc_info.value).lower()

    def test_from_csv_whitespace_handling(self, tmp_path):
        csv_file = tmp_path / "whitespace.csv"
        csv_file.write_text("symbol,shares,avg_cost\n  AAPL  ,  100  ,  150.0  \n")
        p = Portfolio.from_csv(str(csv_file))
        assert len(p.assets) == 1
        assert p.assets[0].symbol == "AAPL"
        assert p.assets[0].shares == 100
        assert p.assets[0].avg_cost == 150.0

    def test_from_csv_default_asset_class(self, tmp_path):
        csv_file = tmp_path / "default_class.csv"
        csv_file.write_text("symbol,shares,avg_cost\nAAPL,100,150\n")
        p = Portfolio.from_csv(str(csv_file))
        assert p.assets[0].asset_class == "equity"

    def test_from_csv_custom_asset_class(self, tmp_path):
        csv_file = tmp_path / "custom_class.csv"
        csv_file.write_text("symbol,shares,avg_cost,asset_class\nBTC,1,50000,crypto\n")
        p = Portfolio.from_csv(str(csv_file))
        assert p.assets[0].asset_class == "crypto"
