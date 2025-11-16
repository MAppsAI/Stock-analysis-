import pandas as pd
import numpy as np
from typing import Tuple, List


def calculate_sma_cross(data: pd.DataFrame, short_window: int = 50, long_window: int = 200) -> Tuple[pd.Series, List[dict]]:
    """
    Simple Moving Average Crossover Strategy (SMA 50/200 Cross)

    Buy Signal: When the short-term SMA crosses above the long-term SMA (Golden Cross)
    Sell Signal: When the short-term SMA crosses below the long-term SMA (Death Cross)

    Args:
        data: DataFrame with 'Close' price column
        short_window: Short-term SMA period (default: 50)
        long_window: Long-term SMA period (default: 200)

    Returns:
        Tuple of (positions series, list of trade signals)
    """
    # Calculate SMAs
    data['SMA_Short'] = data['Close'].rolling(window=short_window).mean()
    data['SMA_Long'] = data['Close'].rolling(window=long_window).mean()

    # Generate signals
    data['Signal'] = 0
    data.loc[data['SMA_Short'] > data['SMA_Long'], 'Signal'] = 1
    data.loc[data['SMA_Short'] < data['SMA_Long'], 'Signal'] = -1

    # Detect crossovers
    data['Position'] = data['Signal'].diff()

    # Extract trade signals
    signals = []
    buy_signals = data[data['Position'] == 2.0]
    sell_signals = data[data['Position'] == -2.0]

    for idx, row in buy_signals.iterrows():
        signals.append({
            'date': idx.strftime('%Y-%m-%d'),
            'price': float(row['Close']),
            'type': 'buy'
        })

    for idx, row in sell_signals.iterrows():
        signals.append({
            'date': idx.strftime('%Y-%m-%d'),
            'price': float(row['Close']),
            'type': 'sell'
        })

    # Sort signals by date
    signals.sort(key=lambda x: x['date'])

    return data['Signal'], signals


def calculate_metrics(data: pd.DataFrame, signals: pd.Series) -> dict:
    """
    Calculate performance metrics for a strategy

    Args:
        data: DataFrame with price data
        signals: Series with trading signals (1 for long, -1 for short, 0 for neutral)

    Returns:
        Dictionary with performance metrics
    """
    # Calculate returns
    data['Returns'] = data['Close'].pct_change()
    data['Strategy_Returns'] = data['Returns'] * signals.shift(1)

    # Remove NaN values
    strategy_returns = data['Strategy_Returns'].dropna()

    if len(strategy_returns) == 0:
        return {
            'total_return': 0.0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'num_trades': 0
        }

    # Total return
    total_return = (1 + strategy_returns).prod() - 1

    # Win rate
    winning_trades = strategy_returns[strategy_returns > 0]
    win_rate = len(winning_trades) / len(strategy_returns) if len(strategy_returns) > 0 else 0

    # Maximum drawdown
    cumulative_returns = (1 + strategy_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min()

    # Sharpe ratio (assuming 252 trading days, 0% risk-free rate)
    sharpe_ratio = np.sqrt(252) * strategy_returns.mean() / strategy_returns.std() if strategy_returns.std() > 0 else 0

    # Number of trades (count position changes)
    num_trades = (signals.diff() != 0).sum()

    return {
        'total_return': float(total_return * 100),  # Convert to percentage
        'win_rate': float(win_rate * 100),
        'max_drawdown': float(max_drawdown * 100),
        'sharpe_ratio': float(sharpe_ratio),
        'num_trades': int(num_trades)
    }


STRATEGY_MAP = {
    'sma_cross': {
        'name': 'SMA 50/200 Cross',
        'func': calculate_sma_cross
    }
}
