"""Unit tests for the single validation contract at the CSV/CLI trust boundary."""

import math

import pytest

from asset_manager.validation import (
    MAX_SYMBOL_LENGTH,
    CsvRowSchema,
    is_safe_text_field,
    is_valid_symbol,
    parse_decimal,
)


class TestCsvRowSchema:
    def test_accepts_well_formed_row(self):
        row = CsvRowSchema(
            symbol="AAPL", shares=100, avg_cost=150.0, current_price=175.0, asset_class="equity"
        )
        assert row.symbol == "AAPL"
        assert row.shares == 100
        assert row.avg_cost == 150.0
        assert row.current_price == 175.0

    def test_accepts_zero_values(self):
        row = CsvRowSchema(symbol="AAPL", shares=0, avg_cost=0, current_price=0)
        assert row.shares == 0

    @pytest.mark.parametrize(
        "field,value",
        [
            ("shares", -1),
            ("avg_cost", -0.01),
            ("current_price", -100),
        ],
    )
    def test_rejects_negative_numbers(self, field, value):
        kwargs = {"symbol": "AAPL", "shares": 1, "avg_cost": 1, "current_price": 1}
        kwargs[field] = value
        with pytest.raises(ValueError, match=f"{field} cannot be negative"):
            CsvRowSchema(**kwargs)

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
    def test_rejects_non_finite_numbers(self, value):
        # ``nan < 0`` is False, so finiteness must be checked explicitly.
        with pytest.raises(ValueError, match="shares must be finite"):
            CsvRowSchema(symbol="AAPL", shares=value, avg_cost=1)

    @pytest.mark.parametrize("value", [float("nan"), float("inf")])
    def test_rejects_non_finite_avg_cost_and_current_price(self, value):
        with pytest.raises(ValueError, match="avg_cost must be finite"):
            CsvRowSchema(symbol="AAPL", shares=1, avg_cost=value)
        with pytest.raises(ValueError, match="current_price must be finite"):
            CsvRowSchema(symbol="AAPL", shares=1, avg_cost=1, current_price=value)

    def test_rejects_non_numeric_input(self):
        with pytest.raises(ValueError, match="shares must be a number"):
            CsvRowSchema(symbol="AAPL", shares="100", avg_cost=1)  # type: ignore[arg-type]

    @pytest.mark.parametrize("symbol", ["", "=SUM(A1)", "+cmd", "@import", "AA\tPL", "-lead"])
    def test_rejects_malformed_symbol(self, symbol):
        with pytest.raises(ValueError, match="Invalid symbol"):
            CsvRowSchema(symbol=symbol, shares=1, avg_cost=1)

    def test_rejects_overlong_symbol(self):
        with pytest.raises(ValueError, match="Invalid symbol"):
            CsvRowSchema(symbol="A" * (MAX_SYMBOL_LENGTH + 1), shares=1, avg_cost=1)

    @pytest.mark.parametrize("symbol", ["AAPL", "BTC-USD", "BRK.B", "abc_123"])
    def test_accepts_valid_symbols(self, symbol):
        assert CsvRowSchema(symbol=symbol, shares=1, avg_cost=1).symbol == symbol

    @pytest.mark.parametrize("asset_class", ["=1+1", "+cmd", "@SUM(A1)", "-cmd", "a\nb", "a\x00b"])
    def test_rejects_formula_or_control_chars_in_asset_class(self, asset_class):
        with pytest.raises(ValueError, match="Unsafe value for asset_class"):
            CsvRowSchema(symbol="AAPL", shares=1, avg_cost=1, asset_class=asset_class)

    def test_accepts_unicode_asset_class(self):
        row = CsvRowSchema(symbol="AAPL", shares=1, avg_cost=1, asset_class="équité")
        assert row.asset_class == "équité"


class TestIsValidSymbol:
    @pytest.mark.parametrize("symbol", ["AAPL", "BTC-USD", "BRK.B", "abc_123", "0"])
    def test_valid(self, symbol):
        assert is_valid_symbol(symbol) is True

    @pytest.mark.parametrize("symbol", ["", "=A1", "A" * (MAX_SYMBOL_LENGTH + 1), "AA BB", "AA\t"])
    def test_invalid(self, symbol):
        assert is_valid_symbol(symbol) is False


class TestIsSafeTextField:
    @pytest.mark.parametrize("value", ["equity", "équité", "fixed income", "  spaced  "])
    def test_safe(self, value):
        assert is_safe_text_field(value) is True

    @pytest.mark.parametrize(
        "value", ["=HYPERLINK(...)", "+1", "@cmd", "-2", "a\rb", "a\nb", "a\x1fb", ""]
    )
    def test_unsafe_or_empty(self, value):
        # An empty field is normalised to the default before validation.
        assert is_safe_text_field(value) is (value == "")


class TestParseDecimal:
    @pytest.mark.parametrize(
        "raw,expected", [("100", 100.0), (" 150.25 ", 150.25), ("1e3", 1000.0), ("0", 0.0)]
    )
    def test_valid(self, raw, expected):
        assert parse_decimal(raw, "shares") == pytest.approx(expected)

    @pytest.mark.parametrize("raw", ["nan", "NaN", "inf", "-inf", "Infinity"])
    def test_rejects_non_finite(self, raw):
        with pytest.raises(ValueError, match="not finite"):
            parse_decimal(raw, "shares")

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            parse_decimal("-1", "shares")

    @pytest.mark.parametrize("raw", ["abc", "", "  "])
    def test_rejects_non_numeric(self, raw):
        with pytest.raises(ValueError, match="Invalid numeric value"):
            parse_decimal(raw, "shares")

    def test_result_is_finite_float(self):
        value = parse_decimal("1.5", "shares")
        assert isinstance(value, float)
        assert math.isfinite(value)
