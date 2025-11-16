"""
Portfolio Management Engine

This module provides core portfolio management functionality including:
- Position sizing (equal-weight, market-cap, optimized)
- Rebalancing logic (time-based and threshold-based)
- Portfolio-level metrics calculation
- Transaction cost modeling
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Literal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PortfolioEngine:
    """Core engine for portfolio construction and management"""

    def __init__(
        self,
        tickers: List[str],
        asset_data: Dict[str, pd.DataFrame],
        allocation_method: Literal['equal', 'market_cap', 'optimized', 'custom'] = 'equal',
        custom_weights: Optional[Dict[str, float]] = None,
        rebalancing: Literal['none', 'monthly', 'quarterly', 'threshold'] = 'none',
        rebalance_threshold: float = 0.05,  # 5% drift triggers rebalance
        transaction_cost: float = 0.001,  # 0.1% per trade
    ):
        """
        Initialize portfolio engine

        Args:
            tickers: List of asset tickers
            asset_data: Dict mapping ticker -> OHLCV DataFrame
            allocation_method: How to determine position sizes
            custom_weights: Custom weight dict (only used if allocation_method='custom')
            rebalancing: Rebalancing frequency
            rebalance_threshold: Weight drift % that triggers rebalance
            transaction_cost: Transaction cost as fraction (0.001 = 0.1%)
        """
        self.tickers = tickers
        self.asset_data = asset_data
        self.allocation_method = allocation_method
        self.custom_weights = custom_weights or {}
        self.rebalancing = rebalancing
        self.rebalance_threshold = rebalance_threshold
        self.transaction_cost = transaction_cost

        # Align all asset data to common date index
        self._align_data()

        # Calculate initial weights
        self.initial_weights = self._calculate_initial_weights()

    def _align_data(self):
        """Align all asset dataframes to common date index (intersection)"""
        if not self.asset_data:
            raise ValueError("No asset data provided")

        # Get intersection of all date indices
        common_index = None
        for ticker, df in self.asset_data.items():
            if common_index is None:
                common_index = df.index
            else:
                common_index = common_index.intersection(df.index)

        if len(common_index) == 0:
            raise ValueError("No common dates across all assets")

        # Reindex all dataframes to common index
        for ticker in self.tickers:
            self.asset_data[ticker] = self.asset_data[ticker].loc[common_index]

        logger.info(f"Aligned {len(self.tickers)} assets to {len(common_index)} common dates")

    def _calculate_initial_weights(self) -> Dict[str, float]:
        """Calculate initial portfolio weights based on allocation method"""
        if self.allocation_method == 'equal':
            weight = 1.0 / len(self.tickers)
            return {ticker: weight for ticker in self.tickers}

        elif self.allocation_method == 'custom':
            # Normalize custom weights to sum to 1.0
            total = sum(self.custom_weights.values())
            if total == 0:
                raise ValueError("Custom weights sum to zero")
            return {ticker: self.custom_weights.get(ticker, 0) / total
                    for ticker in self.tickers}

        elif self.allocation_method == 'market_cap':
            # Equal weight as placeholder (would need market cap data)
            logger.warning("Market cap weighting not yet implemented, using equal weight")
            weight = 1.0 / len(self.tickers)
            return {ticker: weight for ticker in self.tickers}

        elif self.allocation_method == 'optimized':
            # Calculate optimized weights (Sharpe ratio maximization)
            return self._optimize_weights()

        else:
            raise ValueError(f"Unknown allocation method: {self.allocation_method}")

    def _optimize_weights(self) -> Dict[str, float]:
        """Optimize portfolio weights for maximum Sharpe ratio"""
        # Calculate returns for each asset
        returns = pd.DataFrame({
            ticker: self.asset_data[ticker]['Close'].pct_change()
            for ticker in self.tickers
        }).dropna()

        if len(returns) < 30:
            logger.warning("Insufficient data for optimization, using equal weights")
            weight = 1.0 / len(self.tickers)
            return {ticker: weight for ticker in self.tickers}

        # Calculate mean returns and covariance matrix
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # Simple optimization: equal weight or inverse volatility
        volatilities = returns.std()
        inv_vol = 1.0 / volatilities
        weights = inv_vol / inv_vol.sum()

        return {ticker: weights[ticker] for ticker in self.tickers}

    def should_rebalance(
        self,
        current_date: datetime,
        last_rebalance: datetime,
        current_weights: Dict[str, float]
    ) -> bool:
        """Determine if portfolio should be rebalanced"""
        if self.rebalancing == 'none':
            return False

        elif self.rebalancing == 'monthly':
            # Rebalance on first trading day of each month
            return current_date.month != last_rebalance.month

        elif self.rebalancing == 'quarterly':
            # Rebalance on first trading day of each quarter
            current_quarter = (current_date.month - 1) // 3
            last_quarter = (last_rebalance.month - 1) // 3
            return current_quarter != last_quarter or current_date.year != last_rebalance.year

        elif self.rebalancing == 'threshold':
            # Rebalance if any weight drifts beyond threshold
            for ticker in self.tickers:
                target_weight = self.initial_weights[ticker]
                current_weight = current_weights[ticker]
                drift = abs(current_weight - target_weight)
                if drift > self.rebalance_threshold:
                    return True
            return False

        return False

    def calculate_portfolio_metrics(
        self,
        portfolio_returns: pd.Series,
        asset_returns: Dict[str, pd.Series],
        weights_timeline: List[Dict],
        rebalance_dates: List[str]
    ) -> Dict:
        """Calculate comprehensive portfolio metrics"""

        # Basic return metrics
        total_return = (1 + portfolio_returns).prod() - 1
        annualized_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1

        # Risk metrics
        volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = (annualized_return / volatility) if volatility > 0 else 0

        # Drawdown calculation
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Win rate (percent of positive return days)
        win_rate = (portfolio_returns > 0).sum() / len(portfolio_returns)

        # Correlation matrix
        returns_df = pd.DataFrame(asset_returns)
        correlation_matrix = returns_df.corr().to_dict()

        # Diversification ratio
        # DR = (weighted sum of volatilities) / (portfolio volatility)
        asset_vols = {ticker: returns.std() * np.sqrt(252)
                     for ticker, returns in asset_returns.items()}
        weighted_vol_sum = sum(self.initial_weights[ticker] * asset_vols[ticker]
                               for ticker in self.tickers)
        diversification_ratio = weighted_vol_sum / volatility if volatility > 0 else 1.0

        # Portfolio turnover
        turnover = self._calculate_turnover(weights_timeline, rebalance_dates)

        return {
            'total_return': float(total_return),
            'annualized_return': float(annualized_return),
            'volatility': float(volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'num_rebalances': len(rebalance_dates),
            'turnover': float(turnover),
            'diversification_ratio': float(diversification_ratio),
            'correlation_matrix': correlation_matrix,
            'rebalance_dates': rebalance_dates
        }

    def _calculate_turnover(
        self,
        weights_timeline: List[Dict],
        rebalance_dates: List[str]
    ) -> float:
        """Calculate average portfolio turnover at rebalances"""
        if len(rebalance_dates) == 0:
            return 0.0

        total_turnover = 0.0
        for date in rebalance_dates:
            # Find weights before and after rebalance
            matching_entries = [w for w in weights_timeline if w['date'] == date]
            if len(matching_entries) >= 2:
                before = matching_entries[0]['weights']
                after = matching_entries[-1]['weights']

                # Turnover = sum of absolute weight changes
                turnover = sum(abs(after.get(ticker, 0) - before.get(ticker, 0))
                             for ticker in self.tickers)
                total_turnover += turnover

        avg_turnover = total_turnover / len(rebalance_dates) if rebalance_dates else 0.0
        return avg_turnover

    def calculate_asset_metrics(
        self,
        asset_returns: Dict[str, pd.Series],
        asset_signals: Dict[str, pd.Series]
    ) -> Dict[str, Dict]:
        """Calculate individual metrics for each asset in portfolio"""
        metrics = {}

        for ticker in self.tickers:
            returns = asset_returns[ticker]
            signals = asset_signals.get(ticker, pd.Series([1] * len(returns), index=returns.index))

            # Strategy returns (signal-weighted)
            strategy_returns = returns * signals.shift(1).fillna(0)

            total_return = (1 + strategy_returns).prod() - 1
            volatility = strategy_returns.std() * np.sqrt(252)
            sharpe = (strategy_returns.mean() * 252 / volatility) if volatility > 0 else 0

            # Drawdown
            cumulative = (1 + strategy_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            # Win rate
            win_rate = (strategy_returns > 0).sum() / len(strategy_returns)

            # Contribution to portfolio return
            weight = self.initial_weights[ticker]
            contribution = total_return * weight

            metrics[ticker] = {
                'total_return': float(total_return),
                'volatility': float(volatility),
                'sharpe_ratio': float(sharpe),
                'max_drawdown': float(max_drawdown),
                'win_rate': float(win_rate),
                'weight': float(weight),
                'contribution_to_return': float(contribution)
            }

        return metrics


def calculate_portfolio_returns(
    asset_data: Dict[str, pd.DataFrame],
    asset_signals: Dict[str, pd.Series],
    weights: Dict[str, float],
    rebalancing: str = 'none',
    rebalance_threshold: float = 0.05,
    transaction_cost: float = 0.001
) -> Tuple[pd.Series, List[Dict], List[str]]:
    """
    Calculate portfolio returns with rebalancing

    Returns:
        - portfolio_returns: Series of daily portfolio returns
        - weights_timeline: List of weight snapshots over time
        - rebalance_dates: List of rebalance date strings
    """
    # Get common date index
    tickers = list(asset_data.keys())
    common_index = asset_data[tickers[0]].index
    for ticker in tickers[1:]:
        common_index = common_index.intersection(asset_data[ticker].index)

    # Initialize tracking variables
    current_weights = weights.copy()
    portfolio_values = []
    weights_timeline = []
    rebalance_dates = []
    last_rebalance = common_index[0]

    # Calculate returns for each asset
    asset_returns = {}
    for ticker in tickers:
        returns = asset_data[ticker]['Close'].pct_change().fillna(0)
        signals = asset_signals.get(ticker, pd.Series([1] * len(returns), index=returns.index))
        asset_returns[ticker] = returns * signals.shift(1).fillna(0)

    # Simulate portfolio over time
    portfolio_value = 1.0

    for i, date in enumerate(common_index):
        # Record current weights
        weights_timeline.append({
            'date': date.strftime('%Y-%m-%d'),
            'weights': current_weights.copy()
        })

        # Calculate portfolio return for this period
        period_return = sum(current_weights[ticker] * asset_returns[ticker].loc[date]
                           for ticker in tickers)

        # Update portfolio value
        portfolio_value *= (1 + period_return)
        portfolio_values.append(portfolio_value)

        # Update weights based on asset performance (drift)
        if i < len(common_index) - 1:
            new_weights = {}
            total_value = sum(current_weights[ticker] * (1 + asset_returns[ticker].loc[date])
                            for ticker in tickers)

            for ticker in tickers:
                new_weights[ticker] = (current_weights[ticker] *
                                      (1 + asset_returns[ticker].loc[date]) / total_value)

            # Check if rebalancing needed
            engine = PortfolioEngine(tickers, asset_data, rebalancing=rebalancing,
                                    rebalance_threshold=rebalance_threshold)
            engine.initial_weights = weights

            if engine.should_rebalance(date, last_rebalance, new_weights):
                # Apply transaction costs
                turnover = sum(abs(weights[ticker] - new_weights[ticker])
                             for ticker in tickers)
                transaction_costs = turnover * transaction_cost
                portfolio_value *= (1 - transaction_costs)

                # Rebalance to target weights
                current_weights = weights.copy()
                rebalance_dates.append(date.strftime('%Y-%m-%d'))
                last_rebalance = date

                # Record post-rebalance weights
                weights_timeline.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'weights': current_weights.copy(),
                    'rebalance': True
                })
            else:
                # Let weights drift
                current_weights = new_weights

    # Convert to return series
    portfolio_series = pd.Series(portfolio_values, index=common_index)
    portfolio_returns = portfolio_series.pct_change().fillna(0)

    return portfolio_returns, weights_timeline, rebalance_dates


def create_equity_curve(
    portfolio_returns: pd.Series,
    initial_value: float = 1.0
) -> List[Dict]:
    """Convert return series to equity curve points"""
    cumulative = (1 + portfolio_returns).cumprod() * initial_value

    return [
        {'date': date.strftime('%Y-%m-%d'), 'equity': float(value)}
        for date, value in cumulative.items()
    ]
