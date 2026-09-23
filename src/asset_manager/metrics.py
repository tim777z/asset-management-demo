import math


def mean(returns: list[float]) -> float:
    if not returns:
        return 0.0
    return sum(returns) / len(returns)


def variance(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    m = mean(returns)
    return sum((r - m) ** 2 for r in returns) / (len(returns) - 1)


def std_dev(returns: list[float]) -> float:
    return math.sqrt(variance(returns))


def sharpe_ratio(returns: list[float], risk_free_rate: float = 0.05) -> float:
    if not returns:
        return 0.0
    excess = mean(returns) - risk_free_rate / 252
    sd = std_dev(returns)
    if sd == 0:
        return 0.0
    return (excess / sd) * math.sqrt(252)


def max_drawdown(returns: list[float]) -> float:
    if not returns:
        return 0.0
    cumulative = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cumulative *= 1 + r
        if cumulative > peak:
            peak = cumulative
        dd = (peak - cumulative) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd


def value_at_risk(returns: list[float], confidence: float = 0.95) -> float:
    if not returns:
        return 0.0
    sorted_returns = sorted(returns)
    index = int((1 - confidence) * len(sorted_returns))
    index = max(0, min(index, len(sorted_returns) - 1))
    return -sorted_returns[index]


def volatility(returns: list[float]) -> float:
    return std_dev(returns) * math.sqrt(252)


def beta(asset_returns: list[float], market_returns: list[float]) -> float:
    if len(asset_returns) != len(market_returns) or len(asset_returns) < 2:
        return 0.0
    cov = sum(
        (a - mean(asset_returns)) * (m - mean(market_returns))
        for a, m in zip(asset_returns, market_returns)
    ) / (len(asset_returns) - 1)
    market_var = variance(market_returns)
    if market_var == 0:
        return 0.0
    return cov / market_var


def alpha(
    asset_returns: list[float],
    market_returns: list[float],
    risk_free_rate: float = 0.05,
) -> float:
    if len(asset_returns) != len(market_returns) or len(asset_returns) < 2:
        return 0.0
    b = beta(asset_returns, market_returns)
    asset_annual = mean(asset_returns) * 252
    market_annual = mean(market_returns) * 252
    return asset_annual - (risk_free_rate + b * (market_annual - risk_free_rate))


def information_ratio(asset_returns: list[float], benchmark_returns: list[float]) -> float:
    if len(asset_returns) != len(benchmark_returns) or len(asset_returns) < 2:
        return 0.0
    active = [a - b for a, b in zip(asset_returns, benchmark_returns)]
    tracking_error = std_dev(active)
    if tracking_error == 0:
        return 0.0
    return mean(active) / tracking_error * math.sqrt(252)


def sortino_ratio(returns: list[float], risk_free_rate: float = 0.05) -> float:
    if not returns:
        return 0.0
    excess = mean(returns) - risk_free_rate / 252
    downside = [r for r in returns if r < 0]
    if not downside:
        return 0.0
    downside_std = std_dev(downside)
    if downside_std == 0:
        return 0.0
    return (excess / downside_std) * math.sqrt(252)
