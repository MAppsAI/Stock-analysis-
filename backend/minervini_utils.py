"""
Minervini Utilities - RS Rating Calculation and Volume Analysis

Implementation of key metrics for Mark Minervini's SEPA methodology:
- Relative Strength (RS) Rating calculation (IBD-style proxy)
- Volume analysis (dry-up detection and surge confirmation)
- Average True Range (ATR) calculations for risk management
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from scipy.stats import percentileofscore
import logging

logger = logging.getLogger(__name__)


def calculate_rs_rating(
    data: pd.DataFrame,
    universe_data: Optional[Dict[str, pd.DataFrame]] = None
) -> pd.Series:
    """
    Calculate Relative Strength (RS) Rating - IBD-style proxy

    The RS Rating compares a stock's price performance to all other stocks
    over multiple timeframes with weighted emphasis on recent performance.

    Formula:
    - 40% weight on last 3 months (63 trading days)
    - 20% weight on 3-6 months (63-126 days)
    - 20% weight on 6-9 months (126-189 days)
    - 20% weight on 9-12 months (189-252 days)

    Args:
        data: OHLCV DataFrame for the stock
        universe_data: Dict of ticker -> DataFrame for universe comparison
                      If None, returns standalone RS score

    Returns:
        Series of RS ratings (1-99 percentile) or RS scores if no universe
    """
    # Calculate Rate of Change (ROC) over different periods
    roc_3m = data['Close'].pct_change(63)    # ~3 months
    roc_6m = data['Close'].pct_change(126)   # ~6 months
    roc_9m = data['Close'].pct_change(189)   # ~9 months
    roc_12m = data['Close'].pct_change(252)  # ~12 months

    # Calculate weighted RS Score
    rs_score = (
        roc_3m * 0.4 +
        roc_6m * 0.2 +
        roc_9m * 0.2 +
        roc_12m * 0.2
    )

    # If universe data provided, calculate percentile ranking
    if universe_data:
        # Calculate RS scores for all stocks in universe
        universe_scores = []

        for ticker, ticker_data in universe_data.items():
            try:
                ticker_roc_3m = ticker_data['Close'].pct_change(63)
                ticker_roc_6m = ticker_data['Close'].pct_change(126)
                ticker_roc_9m = ticker_data['Close'].pct_change(189)
                ticker_roc_12m = ticker_data['Close'].pct_change(252)

                ticker_rs = (
                    ticker_roc_3m * 0.4 +
                    ticker_roc_6m * 0.2 +
                    ticker_roc_9m * 0.2 +
                    ticker_roc_12m * 0.2
                )

                # Get most recent valid score
                last_score = ticker_rs.dropna().iloc[-1] if len(ticker_rs.dropna()) > 0 else 0
                universe_scores.append(last_score)
            except Exception as e:
                logger.warning(f"Error calculating RS for {ticker}: {e}")
                continue

        # Calculate percentile for each data point
        rs_rating = rs_score.copy()
        for idx in rs_score.index:
            if pd.notna(rs_score.loc[idx]) and len(universe_scores) > 0:
                percentile = percentileofscore(universe_scores, rs_score.loc[idx])
                rs_rating.loc[idx] = min(99, max(1, percentile))
            else:
                rs_rating.loc[idx] = np.nan

        return rs_rating
    else:
        # Return raw RS score (not percentile)
        return rs_score * 100  # Scale for easier interpretation


def is_volume_dry_up(
    data: pd.DataFrame,
    window: int = 10,
    sma_period: int = 50
) -> pd.Series:
    """
    Detect volume dry-up pattern (VDU)

    Volume dry-up indicates seller exhaustion, typically seen in the final
    contraction of a VCP pattern before breakout.

    Criteria:
    - At least 5 days of below-average volume in the window
    - At least 1 day of extremely low volume (< 50% of average)

    Args:
        data: OHLCV DataFrame
        window: Days to analyze for dry-up (default 10)
        sma_period: Period for volume moving average (default 50)

    Returns:
        Boolean Series indicating volume dry-up
    """
    sma_vol = data['Volume'].rolling(window=sma_period).mean()

    # Check for below-average volume days
    below_avg = data['Volume'] < sma_vol

    # Check for extremely low volume days
    extreme_low = data['Volume'] < (sma_vol * 0.5)

    # Count occurrences in rolling window
    low_vol_days = below_avg.rolling(window=window).sum()
    extreme_low_days = extreme_low.rolling(window=window).sum()

    # VDU = at least 5 below-average days AND at least 1 extreme low day
    is_vdu = (low_vol_days >= 5) & (extreme_low_days >= 1)

    return is_vdu


def is_volume_surge(
    data: pd.DataFrame,
    multiplier: float = 1.5,
    sma_period: int = 50
) -> pd.Series:
    """
    Detect volume surge (breakout confirmation)

    A volume surge confirms institutional buying on a pivot breakout.

    Criteria:
    - Current volume is at least multiplier × 50-day average

    Args:
        data: OHLCV DataFrame
        multiplier: Volume multiplier threshold (default 1.5 = 50% above avg)
        sma_period: Period for volume moving average (default 50)

    Returns:
        Boolean Series indicating volume surge
    """
    sma_vol = data['Volume'].rolling(window=sma_period).mean()
    return data['Volume'] >= (sma_vol * multiplier)


def calculate_volume_ud_ratio(
    data: pd.DataFrame,
    period: int = 20
) -> pd.Series:
    """
    Calculate Up/Down Volume Ratio

    A healthy uptrend shows more volume on up days than down days.
    Ratio < 1.0 indicates distribution (bearish).

    Args:
        data: OHLCV DataFrame
        period: Days for ratio calculation (default 20)

    Returns:
        Series of U/D ratios
    """
    # Determine up and down days
    price_change = data['Close'].diff()

    up_days = price_change > 0
    down_days = price_change < 0

    # Calculate up and down volume
    up_volume = (data['Volume'] * up_days).rolling(window=period).sum()
    down_volume = (data['Volume'] * down_days).rolling(window=period).sum()

    # Calculate ratio (avoid division by zero)
    ud_ratio = up_volume / down_volume.replace(0, np.nan)

    return ud_ratio


def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR)

    ATR is used for volatility-adjusted stop-loss placement.

    Args:
        data: OHLCV DataFrame
        period: ATR period (default 14)

    Returns:
        Series of ATR values
    """
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift(1))
    low_close = np.abs(data['Low'] - data['Close'].shift(1))

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr


def calculate_moving_averages(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all moving averages needed for Minervini Trend Template

    Args:
        data: OHLCV DataFrame

    Returns:
        DataFrame with additional MA columns
    """
    result = data.copy()

    # Simple Moving Averages
    result['SMA_50'] = data['Close'].rolling(window=50).mean()
    result['SMA_150'] = data['Close'].rolling(window=150).mean()
    result['SMA_200'] = data['Close'].rolling(window=200).mean()

    # Volume MA
    result['Volume_MA_50'] = data['Volume'].rolling(window=50).mean()

    return result


def calculate_52week_high_low(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 52-week high and low

    Args:
        data: OHLCV DataFrame

    Returns:
        DataFrame with 52-week high/low columns
    """
    result = data.copy()

    result['52W_High'] = data['High'].rolling(window=252).max()
    result['52W_Low'] = data['Low'].rolling(window=252).min()

    return result


def detect_swing_points(
    data: pd.DataFrame,
    window: int = 5
) -> tuple[pd.Series, pd.Series]:
    """
    Detect swing highs and swing lows using a local extrema approach

    A swing high is a local maximum where the price is higher than
    surrounding prices within the window.

    Args:
        data: OHLCV DataFrame
        window: Window size for swing detection (default 5)

    Returns:
        Tuple of (swing_highs, swing_lows) as boolean Series
    """
    highs = data['High']
    lows = data['Low']

    # Find local maxima (swing highs)
    swing_highs = pd.Series(False, index=data.index)
    for i in range(window, len(data) - window):
        center_high = highs.iloc[i]
        window_highs = highs.iloc[i-window:i+window+1]

        if center_high == window_highs.max():
            swing_highs.iloc[i] = True

    # Find local minima (swing lows)
    swing_lows = pd.Series(False, index=data.index)
    for i in range(window, len(data) - window):
        center_low = lows.iloc[i]
        window_lows = lows.iloc[i-window:i+window+1]

        if center_low == window_lows.min():
            swing_lows.iloc[i] = True

    return swing_highs, swing_lows


def calculate_price_strength_vs_market(
    stock_data: pd.DataFrame,
    market_data: pd.DataFrame,
    period: int = 60
) -> pd.Series:
    """
    Calculate relative price strength vs market (e.g., S&P 500)

    Args:
        stock_data: OHLCV DataFrame for the stock
        market_data: OHLCV DataFrame for market index
        period: Lookback period for comparison

    Returns:
        Series of relative strength values
    """
    stock_returns = stock_data['Close'].pct_change(period)
    market_returns = market_data['Close'].pct_change(period)

    # Reindex to match dates
    market_returns_aligned = market_returns.reindex(stock_data.index, method='ffill')

    # Relative strength = stock return - market return
    relative_strength = stock_returns - market_returns_aligned

    return relative_strength


def is_stage_2_uptrend(data: pd.DataFrame) -> bool:
    """
    Quick check if a stock is in Stage 2 uptrend (last available data point)

    This is a simplified version of the full Trend Template check.

    Args:
        data: OHLCV DataFrame with MAs calculated

    Returns:
        Boolean indicating Stage 2 status
    """
    # Get most recent row
    if len(data) < 200:
        return False

    last_row = data.iloc[-1]

    # Check basic Stage 2 criteria
    try:
        is_stage_2 = (
            last_row['Close'] > last_row['SMA_50'] and
            last_row['Close'] > last_row['SMA_150'] and
            last_row['Close'] > last_row['SMA_200'] and
            last_row['SMA_50'] > last_row['SMA_150'] and
            last_row['SMA_150'] > last_row['SMA_200']
        )
        return is_stage_2
    except KeyError:
        # MAs not calculated
        return False


def calculate_minervini_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all Minervini-specific indicators at once

    This is a convenience function that adds all necessary columns
    for the Minervini strategy.

    Args:
        data: OHLCV DataFrame

    Returns:
        DataFrame with all Minervini indicators added
    """
    result = calculate_moving_averages(data)
    result = calculate_52week_high_low(result)

    # Add RS score (standalone, no universe comparison)
    result['RS_Score'] = calculate_rs_rating(result)

    # Add volume indicators
    result['Volume_Surge'] = is_volume_surge(result)
    result['Volume_Dry_Up'] = is_volume_dry_up(result)
    result['Volume_UD_Ratio'] = calculate_volume_ud_ratio(result)

    # Add ATR for stop-loss calculations
    result['ATR'] = calculate_atr(result)

    return result
