import pytest

from asset_manager.metrics import (
    alpha,
    beta,
    information_ratio,
    max_drawdown,
    mean,
    sharpe_ratio,
    sortino_ratio,
    std_dev,
    value_at_risk,
    variance,
    volatility,
)


class TestMean:
    def test_mean_empty_list(self):
        assert mean([]) == 0.0

    def test_mean_single_value(self):
        assert mean([0.05]) == 0.05

    def test_mean_multiple_values(self):
        assert mean([0.01, 0.02, 0.03]) == pytest.approx(0.02)

    def test_mean_negative_values(self):
        assert mean([-0.01, -0.02, -0.03]) == pytest.approx(-0.02)


class TestVariance:
    def test_variance_empty_list(self):
        assert variance([]) == 0.0

    def test_variance_single_value(self):
        assert variance([0.05]) == 0.0

    def test_variance_two_values(self):
        # variance of [0, 1] = ((0-0.5)^2 + (1-0.5)^2) / 1 = 0.5
        assert variance([0.0, 1.0]) == pytest.approx(0.5)

    def test_variance_multiple_values(self):
        # variance of [1, 2, 3] = ((1-2)^2 + (2-2)^2 + (3-2)^2) / 2 = 1.0
        assert variance([1.0, 2.0, 3.0]) == pytest.approx(1.0)


class TestStdDev:
    def test_std_dev_empty_list(self):
        assert std_dev([]) == 0.0

    def test_std_dev_single_value(self):
        assert std_dev([0.05]) == 0.0

    def test_std_dev_known_values(self):
        # std_dev of [1, 2, 3] = sqrt(1.0) = 1.0
        assert std_dev([1.0, 2.0, 3.0]) == pytest.approx(1.0)


class TestSharpeRatio:
    def test_sharpe_ratio_empty_returns(self):
        assert sharpe_ratio([]) == 0.0

    def test_sharpe_ratio_zero_volatility(self):
        # All returns are the same, so std_dev = 0
        assert sharpe_ratio([0.01, 0.01, 0.01]) == 0.0

    def test_sharpe_ratio_positive(self):
        returns = [0.01, 0.02, 0.015, 0.025, 0.01]
        result = sharpe_ratio(returns, risk_free_rate=0.05)
        # Expected: excess_return = mean - rf/252, sharpe = (excess/sd) * sqrt(252)
        assert result > 0

    def test_sharpe_ratio_negative(self):
        returns = [-0.01, -0.02, -0.015, -0.025, -0.01]
        result = sharpe_ratio(returns, risk_free_rate=0.05)
        assert result < 0

    def test_sharpe_ratio_custom_risk_free(self):
        returns = [0.001] * 100
        result_default = sharpe_ratio(returns, risk_free_rate=0.05)
        result_zero = sharpe_ratio(returns, risk_free_rate=0.0)
        assert result_zero > result_default


class TestMaxDrawdown:
    def test_max_drawdown_empty(self):
        assert max_drawdown([]) == 0.0

    def test_max_drawdown_no_drawdown(self):
        # Monotonically increasing returns
        returns = [0.01, 0.02, 0.015, 0.03]
        assert max_drawdown(returns) == 0.0

    def test_max_drawdown_simple(self):
        # Return sequence: up 10%, down 20%, up 5%
        # Cumulative: 1.1, 0.88, 0.924
        # Peak: 1.1, trough: 0.88, drawdown = (1.1 - 0.88) / 1.1 = 0.2
        returns = [0.1, -0.2, 0.05]
        assert max_drawdown(returns) == pytest.approx(0.2, rel=1e-3)

    def test_max_drawdown_multiple_peaks(self):
        returns = [0.1, -0.05, 0.1, -0.15, 0.05]
        # Peak at 1.1, then 1.155, trough at 0.98175
        # Max drawdown from 1.155 to 0.98175 = (1.155 - 0.98175) / 1.155 ≈ 0.15
        result = max_drawdown(returns)
        assert 0.14 < result < 0.16


class TestValueAtRisk:
    def test_var_empty(self):
        assert value_at_risk([]) == 0.0

    def test_var_single_value(self):
        # VaR returns negative of the sorted return at the percentile index
        # For a single positive return, VaR is negative (loss potential)
        assert value_at_risk([0.01], confidence=0.95) == pytest.approx(-0.01)

    def test_var_known_percentile(self):
        # 100 returns from -0.05 to 0.05
        returns = [i / 1000 - 0.05 for i in range(100)]
        # 95% VaR should be at 5th percentile (index 5)
        var_95 = value_at_risk(returns, confidence=0.95)
        # 5th element (0-indexed) is -0.045, VaR returns negative of that = 0.045
        assert var_95 == pytest.approx(0.045, abs=0.01)

    def test_var_confidence_levels(self):
        returns = [-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03]
        var_99 = value_at_risk(returns, confidence=0.99)
        var_95 = value_at_risk(returns, confidence=0.95)
        var_90 = value_at_risk(returns, confidence=0.90)
        # Higher confidence = higher VaR (more conservative)
        assert var_99 >= var_95 >= var_90


class TestVolatility:
    def test_volatility_empty(self):
        assert volatility([]) == 0.0

    def test_volatility_single_value(self):
        assert volatility([0.01]) == 0.0

    def test_volatility_annualization(self):
        # Daily std_dev of 0.01 -> annualized = 0.01 * sqrt(252) ≈ 0.1587
        returns = [0.01] * 100  # All same, so std_dev = 0 (or very close due to float precision)
        assert volatility(returns) == pytest.approx(0.0, abs=1e-10)

        returns = [0.01, -0.01, 0.01, -0.01] * 25
        result = volatility(returns)
        # std_dev ≈ 0.01, annualized ≈ 0.1587
        assert result == pytest.approx(0.1587, rel=1e-2)


class TestBeta:
    def test_beta_empty(self):
        assert beta([], []) == 0.0

    def test_beta_mismatched_lengths(self):
        assert beta([0.01, 0.02], [0.01]) == 0.0

    def test_beta_insufficient_data(self):
        assert beta([0.01], [0.01]) == 0.0

    def test_beta_perfect_correlation(self):
        # Asset returns = 2 * market returns
        market = [0.01, 0.02, -0.01, 0.015, -0.005]
        asset = [2 * m for m in market]
        # beta = cov(asset, market) / var(market) = 2 * var(market) / var(market) = 2
        assert beta(asset, market) == pytest.approx(2.0, rel=1e-2)

    def test_beta_zero_market_variance(self):
        market = [0.01, 0.01, 0.01]
        asset = [0.02, 0.03, 0.01]
        assert beta(asset, market) == 0.0

    def test_beta_negative_correlation(self):
        market = [0.01, 0.02, -0.01, 0.015]
        asset = [-m for m in market]
        assert beta(asset, market) == pytest.approx(-1.0, rel=1e-2)


class TestAlpha:
    def test_alpha_empty(self):
        assert alpha([], []) == 0.0

    def test_alpha_mismatched_lengths(self):
        assert alpha([0.01, 0.02], [0.01]) == 0.0

    def test_alpha_insufficient_data(self):
        assert alpha([0.01], [0.01]) == 0.0

    def test_alpha_zero_beta(self):
        # Asset uncorrelated with market
        market = [0.01, 0.02, -0.01, 0.015]
        asset = [0.005, 0.005, 0.005, 0.005]  # Constant returns
        result = alpha(asset, market, risk_free_rate=0.05)
        # alpha = asset_annual - (rf + 0 * (market_annual - rf)) = asset_annual - rf
        asset_annual = 0.005 * 252
        expected = asset_annual - 0.05
        assert result == pytest.approx(expected, rel=1e-2)


class TestInformationRatio:
    def test_ir_empty(self):
        assert information_ratio([], []) == 0.0

    def test_ir_mismatched_lengths(self):
        assert information_ratio([0.01, 0.02], [0.01]) == 0.0

    def test_ir_insufficient_data(self):
        assert information_ratio([0.01], [0.01]) == 0.0

    def test_ir_zero_tracking_error(self):
        # Asset returns = benchmark returns
        benchmark = [0.01, 0.02, -0.01, 0.015]
        asset = [0.01, 0.02, -0.01, 0.015]
        assert information_ratio(asset, benchmark) == 0.0

    def test_ir_positive(self):
        # Asset outperforms benchmark consistently
        benchmark = [0.01] * 100
        asset = [0.015] * 100
        result = information_ratio(asset, benchmark)
        # active return = 0.005, tracking_error = 0, but we handle that above
        # Let's use slightly different returns
        benchmark = [0.01 + i * 0.0001 for i in range(100)]
        asset = [b + 0.001 for b in benchmark]
        result = information_ratio(asset, benchmark)
        assert result > 0


class TestSortinoRatio:
    def test_sortino_empty(self):
        assert sortino_ratio([]) == 0.0

    def test_sortino_no_downside(self):
        # All positive returns
        returns = [0.01, 0.02, 0.015, 0.03]
        result = sortino_ratio(returns, risk_free_rate=0.05)
        # No downside returns, so returns 0.0
        assert result == 0.0

    def test_sortino_with_downside(self):
        returns = [0.02, -0.01, 0.03, -0.02, 0.01]
        result = sortino_ratio(returns, risk_free_rate=0.05)
        # Should compute normally
        assert isinstance(result, float)

    def test_sortino_zero_downside_std(self):
        # All negative returns are the same
        returns = [0.01, -0.01, 0.02, -0.01, 0.015]
        result = sortino_ratio(returns, risk_free_rate=0.05)
        # downside_std = 0, so returns 0.0
        assert result == 0.0


class TestEdgeCases:
    def test_all_functions_handle_nan_gracefully(self):
        # Functions should not crash on edge cases
        returns = [float("nan")]
        # These may return nan or 0, but shouldn't raise
        try:
            mean(returns)
            variance(returns)
            std_dev(returns)
        except (ValueError, ZeroDivisionError):
            pass  # Acceptable to raise on nan

    def test_large_numbers(self):
        returns = [1e6, -1e6, 1e6]
        assert isinstance(sharpe_ratio(returns), float)
        assert isinstance(max_drawdown(returns), float)
        assert isinstance(volatility(returns), float)
