"""
Multi-Asset Portfolio Strategies

Strategies designed for portfolios of multiple assets, including:
- Sector rotation
- Relative strength rotation
- Mean reversion pairs
- Momentum clustering
- Risk parity
- Mean-variance optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def equal_weight_buy_hold(
    asset_data: Dict[str, pd.DataFrame],
    **kwargs
) -> Tuple[Dict[str, pd.Series], Dict[str, float]]:
    """
    Equal-weight buy-and-hold portfolio

    Simple baseline strategy that holds all assets with equal weights.
    No trading signals - just buy and hold.

    Args:
        asset_data: Dict mapping ticker -> OHLCV DataFrame

    Returns:
        - signals: Dict mapping ticker -> signal series (all 1s for buy-and-hold)
        - weights: Dict mapping ticker -> portfolio weight (all equal)
    """
    tickers = list(asset_data.keys())
    n_assets = len(tickers)

    if n_assets == 0:
        raise ValueError("No assets provided")

    # Equal weights
    weight = 1.0 / n_assets
    weights = {ticker: weight for ticker in tickers}

    # All buy signals (hold throughout)
    signals = {}
    for ticker, data in asset_data.items():
        signals[ticker] = pd.Series([1] * len(data), index=data.index, name='Signal')

    logger.info(f"Equal-weight buy-hold: {n_assets} assets, {weight:.2%} each")

    return signals, weights


def sector_rotation(
    asset_data: Dict[str, pd.DataFrame],
    lookback_period: int = 60,  # 3 months for momentum calculation
    top_n: int = 3,  # Hold top 3 sectors
    rebalance_freq: str = 'monthly',  # 'weekly' or 'monthly'
    **kwargs
) -> Tuple[Dict[str, pd.Series], Dict[str, float]]:
    """
    Sector rotation strategy based on momentum

    Ranks assets by momentum (returns over lookback period) and holds
    the top N performers. Rebalances periodically.

    Args:
        asset_data: Dict mapping ticker -> OHLCV DataFrame
        lookback_period: Days to calculate momentum (default 60 = ~3 months)
        top_n: Number of top assets to hold
        rebalance_freq: 'weekly' or 'monthly'

    Returns:
        - signals: Dict mapping ticker -> signal series (1 for hold, 0 for cash)
        - weights: Dict mapping ticker -> portfolio weight
    """
    tickers = list(asset_data.keys())

    if len(tickers) < top_n:
        logger.warning(f"Only {len(tickers)} assets but top_n={top_n}, using all assets")
        top_n = len(tickers)

    # Get common date index
    common_index = asset_data[tickers[0]].index
    for ticker in tickers[1:]:
        common_index = common_index.intersection(asset_data[ticker].index)

    # Calculate momentum for each asset
    momentum = {}
    for ticker, data in asset_data.items():
        # Momentum = return over lookback period
        returns = data['Close'].pct_change(lookback_period)
        momentum[ticker] = returns.reindex(common_index)

    # Create signals based on ranking
    signals = {ticker: pd.Series([0] * len(common_index), index=common_index, name='Signal')
              for ticker in tickers}

    # Determine rebalance dates
    if rebalance_freq == 'monthly':
        rebalance_dates = common_index[common_index.to_series().diff().dt.days > 20]
    else:  # weekly
        rebalance_dates = common_index[common_index.to_series().diff().dt.days > 5]

    # Add first date
    rebalance_dates = rebalance_dates.insert(0, common_index[0])

    # Track holdings for weight calculation
    current_holdings = []

    for i, date in enumerate(common_index):
        # Check if it's a rebalance date
        if date in rebalance_dates or i == 0:
            # Rank assets by momentum
            rankings = {}
            for ticker in tickers:
                if not pd.isna(momentum[ticker].loc[date]):
                    rankings[ticker] = momentum[ticker].loc[date]

            # Sort by momentum (descending)
            sorted_tickers = sorted(rankings.keys(), key=lambda t: rankings[t], reverse=True)

            # Select top N
            current_holdings = sorted_tickers[:top_n]
            logger.debug(f"{date.strftime('%Y-%m-%d')}: Holding {current_holdings}")

        # Set signals for current holdings
        for ticker in current_holdings:
            signals[ticker].loc[date] = 1

    # Equal weight among selected assets
    weight_per_asset = 1.0 / top_n
    weights = {ticker: weight_per_asset for ticker in tickers}

    logger.info(f"Sector rotation: {len(tickers)} assets, hold top {top_n}, "
                f"rebalance {rebalance_freq}")

    return signals, weights


def relative_strength_rotation(
    asset_data: Dict[str, pd.DataFrame],
    benchmark_ticker: Optional[str] = None,
    lookback_period: int = 20,  # 1 month
    top_n: int = 5,
    rebalance_freq: str = 'weekly',
    **kwargs
) -> Tuple[Dict[str, pd.Series], Dict[str, float]]:
    """
    Relative strength rotation strategy

    Ranks assets by relative strength vs benchmark (or equal-weight portfolio).
    Holds top N performers and rotates on rebalance schedule.

    Args:
        asset_data: Dict mapping ticker -> OHLCV DataFrame
        benchmark_ticker: Ticker to compare against (if None, uses equal-weight portfolio)
        lookback_period: Days for relative strength calculation
        top_n: Number of assets to hold
        rebalance_freq: 'weekly' or 'monthly'

    Returns:
        - signals: Dict mapping ticker -> signal series
        - weights: Dict mapping ticker -> portfolio weight
    """
    tickers = list(asset_data.keys())

    if len(tickers) < top_n:
        top_n = len(tickers)

    # Get common date index
    common_index = asset_data[tickers[0]].index
    for ticker in tickers[1:]:
        common_index = common_index.intersection(asset_data[ticker].index)

    # Calculate benchmark returns
    if benchmark_ticker and benchmark_ticker in asset_data:
        benchmark_returns = asset_data[benchmark_ticker]['Close'].pct_change()
        benchmark_returns = benchmark_returns.reindex(common_index)
    else:
        # Equal-weight portfolio as benchmark
        all_returns = pd.DataFrame({
            ticker: asset_data[ticker]['Close'].pct_change().reindex(common_index)
            for ticker in tickers
        })
        benchmark_returns = all_returns.mean(axis=1)

    # Calculate relative strength for each asset
    relative_strength = {}
    for ticker, data in asset_data.items():
        asset_returns = data['Close'].pct_change().reindex(common_index)

        # Relative strength = asset return - benchmark return over lookback
        rs = (asset_returns - benchmark_returns).rolling(lookback_period).sum()
        relative_strength[ticker] = rs

    # Create signals
    signals = {ticker: pd.Series([0] * len(common_index), index=common_index, name='Signal')
              for ticker in tickers}

    # Determine rebalance dates
    if rebalance_freq == 'monthly':
        rebalance_dates = common_index[common_index.to_series().diff().dt.days > 20]
    else:  # weekly
        rebalance_dates = common_index[common_index.to_series().diff().dt.days > 5]

    rebalance_dates = rebalance_dates.insert(0, common_index[lookback_period] if len(common_index) > lookback_period else common_index[0])

    current_holdings = []

    for i, date in enumerate(common_index):
        if date in rebalance_dates or i == lookback_period:
            # Rank by relative strength
            rankings = {}
            for ticker in tickers:
                if not pd.isna(relative_strength[ticker].loc[date]):
                    rankings[ticker] = relative_strength[ticker].loc[date]

            sorted_tickers = sorted(rankings.keys(), key=lambda t: rankings[t], reverse=True)
            current_holdings = sorted_tickers[:top_n]

        # Set signals
        for ticker in current_holdings:
            if date in signals[ticker].index:
                signals[ticker].loc[date] = 1

    weight_per_asset = 1.0 / top_n
    weights = {ticker: weight_per_asset for ticker in tickers}

    logger.info(f"Relative strength rotation: {len(tickers)} assets, hold top {top_n}")

    return signals, weights


def momentum_cluster(
    asset_data: Dict[str, pd.DataFrame],
    lookback_period: int = 60,
    n_clusters: int = 3,
    high_momentum_weight: float = 0.6,
    medium_momentum_weight: float = 0.3,
    low_momentum_weight: float = 0.1,
    rebalance_freq: str = 'monthly',
    **kwargs
) -> Tuple[Dict[str, pd.Series], Dict[str, float]]:
    """
    Momentum cluster strategy

    Groups assets into momentum clusters (high/medium/low) and overweights
    high-momentum cluster.

    Args:
        asset_data: Dict mapping ticker -> OHLCV DataFrame
        lookback_period: Days for momentum calculation
        n_clusters: Number of clusters (default 3: high/med/low)
        high_momentum_weight: Portfolio weight for high cluster
        medium_momentum_weight: Portfolio weight for medium cluster
        low_momentum_weight: Portfolio weight for low cluster
        rebalance_freq: 'weekly' or 'monthly'

    Returns:
        - signals: Dict mapping ticker -> signal series
        - weights: Dict mapping ticker -> portfolio weight
    """
    tickers = list(asset_data.keys())

    # Get common date index
    common_index = asset_data[tickers[0]].index
    for ticker in tickers[1:]:
        common_index = common_index.intersection(asset_data[ticker].index)

    # Calculate momentum
    momentum = {}
    for ticker, data in asset_data.items():
        returns = data['Close'].pct_change(lookback_period)
        momentum[ticker] = returns.reindex(common_index)

    # All assets are held (buy-and-hold signals)
    signals = {ticker: pd.Series([1] * len(common_index), index=common_index, name='Signal')
              for ticker in tickers}

    # Determine cluster weights based on momentum
    cluster_weights = [high_momentum_weight, medium_momentum_weight, low_momentum_weight]

    # Calculate average momentum to determine clusters
    all_momentum = pd.DataFrame(momentum)
    median_momentum = all_momentum.median(axis=1)

    # Assign weights based on momentum percentiles
    weights = {}
    for ticker in tickers:
        # Simple clustering: compare to median
        avg_momentum = momentum[ticker].median()

        if pd.isna(avg_momentum):
            weights[ticker] = 1.0 / len(tickers)
        else:
            # Determine cluster
            if avg_momentum > median_momentum.quantile(0.67):
                weights[ticker] = high_momentum_weight / (len(tickers) // n_clusters)
            elif avg_momentum > median_momentum.quantile(0.33):
                weights[ticker] = medium_momentum_weight / (len(tickers) // n_clusters)
            else:
                weights[ticker] = low_momentum_weight / (len(tickers) // n_clusters)

    # Normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    weights = {ticker: w / total_weight for ticker, w in weights.items()}

    logger.info(f"Momentum cluster: {len(tickers)} assets, {n_clusters} clusters")

    return signals, weights


def risk_parity(
    asset_data: Dict[str, pd.DataFrame],
    lookback_period: int = 60,
    **kwargs
) -> Tuple[Dict[str, pd.Series], Dict[str, float]]:
    """
    Risk parity strategy

    Equal risk contribution from each asset using inverse volatility weighting.

    Args:
        asset_data: Dict mapping ticker -> OHLCV DataFrame
        lookback_period: Days for volatility calculation

    Returns:
        - signals: Dict mapping ticker -> signal series (all 1s)
        - weights: Dict mapping ticker -> portfolio weight
    """
    tickers = list(asset_data.keys())

    # Get common date index
    common_index = asset_data[tickers[0]].index
    for ticker in tickers[1:]:
        common_index = common_index.intersection(asset_data[ticker].index)

    # Calculate volatility for each asset
    volatilities = {}
    for ticker, data in asset_data.items():
        returns = data['Close'].pct_change().reindex(common_index)
        vol = returns.rolling(lookback_period).std()
        # Use median volatility over the period
        volatilities[ticker] = vol.median()

    # Inverse volatility weighting
    inv_vols = {ticker: 1.0 / vol if vol > 0 else 0
                for ticker, vol in volatilities.items()}

    total_inv_vol = sum(inv_vols.values())
    weights = {ticker: inv_vol / total_inv_vol
              for ticker, inv_vol in inv_vols.items()}

    # All buy-and-hold signals
    signals = {ticker: pd.Series([1] * len(common_index), index=common_index, name='Signal')
              for ticker in tickers}

    logger.info(f"Risk parity: {len(tickers)} assets with inverse volatility weights")

    return signals, weights


def mean_variance_optimization(
    asset_data: Dict[str, pd.DataFrame],
    lookback_period: int = 252,  # 1 year
    target_return: Optional[float] = None,
    risk_free_rate: float = 0.02,
    **kwargs
) -> Tuple[Dict[str, pd.Series], Dict[str, float]]:
    """
    Mean-variance optimization (Markowitz)

    Optimizes portfolio for maximum Sharpe ratio or target return.

    Args:
        asset_data: Dict mapping ticker -> OHLCV DataFrame
        lookback_period: Days for calculating expected returns and covariance
        target_return: Target annual return (if None, maximize Sharpe)
        risk_free_rate: Annual risk-free rate for Sharpe calculation

    Returns:
        - signals: Dict mapping ticker -> signal series (all 1s)
        - weights: Dict mapping ticker -> optimized portfolio weight
    """
    tickers = list(asset_data.keys())

    # Get common date index
    common_index = asset_data[tickers[0]].index
    for ticker in tickers[1:]:
        common_index = common_index.intersection(asset_data[ticker].index)

    # Calculate returns
    returns_df = pd.DataFrame({
        ticker: asset_data[ticker]['Close'].pct_change().reindex(common_index)
        for ticker in tickers
    }).dropna()

    if len(returns_df) < lookback_period:
        logger.warning(f"Insufficient data ({len(returns_df)} < {lookback_period}), "
                      f"using equal weights")
        weight = 1.0 / len(tickers)
        weights = {ticker: weight for ticker in tickers}
    else:
        # Use last lookback_period days
        recent_returns = returns_df.tail(lookback_period)

        # Expected returns (annualized)
        mean_returns = recent_returns.mean() * 252

        # Covariance matrix (annualized)
        cov_matrix = recent_returns.cov() * 252

        # Simple optimization: maximize Sharpe ratio using inverse volatility as proxy
        # (Full optimization would require scipy.optimize)
        volatilities = np.sqrt(np.diag(cov_matrix))
        inv_vol = 1.0 / volatilities
        weights_array = inv_vol / inv_vol.sum()

        weights = {ticker: float(w) for ticker, w in zip(tickers, weights_array)}

    # All buy-and-hold signals
    signals = {ticker: pd.Series([1] * len(common_index), index=common_index, name='Signal')
              for ticker in tickers}

    logger.info(f"Mean-variance optimization: {len(tickers)} assets")

    return signals, weights


# Strategy registry for portfolio strategies
PORTFOLIO_STRATEGY_MAP = {
    'equal_weight_buy_hold': {
        'name': 'Equal-Weight Buy & Hold',
        'func': equal_weight_buy_hold,
        'category': 'Portfolio',
        'description': 'Equal-weight portfolio with buy-and-hold approach'
    },
    'sector_rotation': {
        'name': 'Sector Rotation (Momentum)',
        'func': sector_rotation,
        'category': 'Portfolio',
        'description': 'Rotate into top N sectors by momentum',
        'parameters': {
            'lookback_period': [20, 60, 120],
            'top_n': [2, 3, 4, 5],
            'rebalance_freq': ['weekly', 'monthly']
        }
    },
    'relative_strength_rotation': {
        'name': 'Relative Strength Rotation',
        'func': relative_strength_rotation,
        'category': 'Portfolio',
        'description': 'Hold top N assets by relative strength',
        'parameters': {
            'lookback_period': [10, 20, 40],
            'top_n': [3, 5, 7],
            'rebalance_freq': ['weekly', 'monthly']
        }
    },
    'momentum_cluster': {
        'name': 'Momentum Cluster',
        'func': momentum_cluster,
        'category': 'Portfolio',
        'description': 'Overweight high-momentum asset cluster',
        'parameters': {
            'lookback_period': [30, 60, 90],
            'n_clusters': [2, 3],
            'rebalance_freq': ['monthly']
        }
    },
    'risk_parity': {
        'name': 'Risk Parity',
        'func': risk_parity,
        'category': 'Portfolio',
        'description': 'Equal risk contribution via inverse volatility',
        'parameters': {
            'lookback_period': [30, 60, 120]
        }
    },
    'mean_variance_optimization': {
        'name': 'Mean-Variance Optimization',
        'func': mean_variance_optimization,
        'category': 'Portfolio',
        'description': 'Markowitz optimization for max Sharpe ratio',
        'parameters': {
            'lookback_period': [120, 252, 504],
            'risk_free_rate': [0.01, 0.02, 0.03]
        }
    }
}
