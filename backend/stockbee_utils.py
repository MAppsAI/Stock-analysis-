"""
Stockbee Utilities - Market Breadth Filter and Position Sizing

Implementation of Pradeep Bonde's (Stockbee) core utilities:
- Market State / Situational Awareness (breadth-based master filter)
- Breadth indicators (BPNYA, BPCOMPQ, T2108, RSI ratios)
- Position sizing calculator
- Risk management utilities
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketState(Enum):
    """Market state classifications"""
    AGGRESSIVE = "aggressive"
    NEUTRAL = "neutral"
    AVOID = "avoid"


def calculate_breadth_pressure(data: pd.DataFrame, period: int = 10) -> pd.Series:
    """
    Calculate Breadth Pressure indicator

    Breadth Pressure = (Advances - Declines) / (Advances + Declines)
    Compared to its moving average

    Args:
        data: DataFrame with 'Advances' and 'Declines' columns
        period: Moving average period (default 10)

    Returns:
        Series of breadth pressure values
    """
    if 'Advances' not in data.columns or 'Declines' not in data.columns:
        logger.warning("Advances/Declines data not available")
        return pd.Series(0, index=data.index)

    bp = (data['Advances'] - data['Declines']) / (data['Advances'] + data['Declines'])
    bp_ma = bp.rolling(window=period).mean()

    return bp - bp_ma


def calculate_t2108(universe_data: Dict[str, pd.DataFrame]) -> float:
    """
    Calculate T2108 indicator

    T2108 = Percentage of stocks above their 40-day moving average

    Args:
        universe_data: Dict of ticker -> DataFrame

    Returns:
        Percentage (0-100) of stocks above 40-day MA
    """
    if not universe_data:
        return 50.0  # Neutral default

    above_ma_count = 0
    total_count = 0

    for ticker, data in universe_data.items():
        if len(data) < 40:
            continue

        try:
            ma_40 = data['Close'].rolling(window=40).mean()
            current_price = data['Close'].iloc[-1]
            current_ma = ma_40.iloc[-1]

            if pd.notna(current_ma):
                total_count += 1
                if current_price > current_ma:
                    above_ma_count += 1
        except Exception:
            continue

    if total_count == 0:
        return 50.0

    return (above_ma_count / total_count) * 100


def calculate_rsi2_ratio(universe_data: Dict[str, pd.DataFrame]) -> float:
    """
    Calculate RSI(2) 5-day ratio

    Ratio = Stocks with RSI(2) > 90 / Stocks with RSI(2) < 10

    - Ratio > 4.0 = Caution (overbought)
    - Ratio < 0.2 = Buy signal (oversold)

    Args:
        universe_data: Dict of ticker -> DataFrame

    Returns:
        RSI(2) ratio
    """
    if not universe_data:
        return 1.0  # Neutral default

    high_rsi_count = 0
    low_rsi_count = 0

    for ticker, data in universe_data.items():
        if len(data) < 10:
            continue

        try:
            # Calculate RSI(2)
            delta = data['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=2).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=2).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi2 = 100 - (100 / (1 + rs))

            current_rsi = rsi2.iloc[-1]

            if pd.notna(current_rsi):
                if current_rsi > 90:
                    high_rsi_count += 1
                elif current_rsi < 10:
                    low_rsi_count += 1
        except Exception:
            continue

    if low_rsi_count == 0:
        return 10.0 if high_rsi_count > 0 else 1.0

    return high_rsi_count / low_rsi_count


def calculate_momentum_breadth(universe_data: Dict[str, pd.DataFrame], days: int = 5) -> float:
    """
    Calculate momentum breadth ratio

    Ratio = Stocks up 4%+ in last N days / Stocks down 4%+ in last N days

    Args:
        universe_data: Dict of ticker -> DataFrame
        days: Lookback period (default 5)

    Returns:
        Momentum breadth ratio
    """
    if not universe_data:
        return 1.0

    up_4pct_count = 0
    down_4pct_count = 0

    for ticker, data in universe_data.items():
        if len(data) < days + 1:
            continue

        try:
            pct_change = (data['Close'].iloc[-1] / data['Close'].iloc[-days-1] - 1) * 100

            if pct_change >= 4.0:
                up_4pct_count += 1
            elif pct_change <= -4.0:
                down_4pct_count += 1
        except Exception:
            continue

    if down_4pct_count == 0:
        return 10.0 if up_4pct_count > 0 else 1.0

    return up_4pct_count / down_4pct_count


def get_market_state(
    breadth_pressure_nyse: float = 0,
    breadth_pressure_nasdaq: float = 0,
    t2108: float = 50,
    rsi2_ratio: float = 1.0,
    momentum_ratio: float = 1.0
) -> MarketState:
    """
    Determine market state based on breadth indicators

    This is the "Master Filter" that modulates all trading activity.

    Logic:
    - AGGRESSIVE: Bullish breadth, T2108 < 70, RSI ratio healthy
    - AVOID: Bearish breadth, T2108 > 70 (caution), RSI ratio extreme
    - NEUTRAL: Everything else

    Args:
        breadth_pressure_nyse: NYSE breadth pressure vs 10-day MA
        breadth_pressure_nasdaq: NASDAQ breadth pressure vs 10-day MA
        t2108: Percentage of stocks above 40-day MA
        rsi2_ratio: RSI(2) extreme ratio
        momentum_ratio: Up 4% vs Down 4% ratio

    Returns:
        MarketState enum
    """
    # Count bullish signals
    bullish_signals = 0
    bearish_signals = 0

    # Breadth pressure (positive = bullish)
    if breadth_pressure_nyse > 0:
        bullish_signals += 1
    elif breadth_pressure_nyse < -0.1:
        bearish_signals += 1

    if breadth_pressure_nasdaq > 0:
        bullish_signals += 1
    elif breadth_pressure_nasdaq < -0.1:
        bearish_signals += 1

    # T2108 (< 70 = healthy, > 70 = caution)
    if t2108 > 70:
        bearish_signals += 2  # Strong signal
    elif t2108 < 50:
        bullish_signals += 1

    # RSI(2) ratio
    if rsi2_ratio > 4.0:
        bearish_signals += 1  # Overbought
    elif rsi2_ratio < 0.2:
        bullish_signals += 2  # Oversold = buy signal

    # Momentum ratio
    if momentum_ratio > 2.0:
        bullish_signals += 1
    elif momentum_ratio < 0.5:
        bearish_signals += 1

    # Determine state
    if bearish_signals >= 3:
        state = MarketState.AVOID
    elif bullish_signals >= 4:
        state = MarketState.AGGRESSIVE
    else:
        state = MarketState.NEUTRAL

    logger.info(f"Market State: {state.value.upper()} "
                f"(bullish={bullish_signals}, bearish={bearish_signals})")
    logger.debug(f"Indicators: BP_NYSE={breadth_pressure_nyse:.3f}, "
                f"BP_NASDAQ={breadth_pressure_nasdaq:.3f}, "
                f"T2108={t2108:.1f}, RSI_Ratio={rsi2_ratio:.2f}, "
                f"Mom_Ratio={momentum_ratio:.2f}")

    return state


def calculate_position_size(
    account_value: float,
    entry_price: float,
    stop_price: float,
    max_risk_pct: float = 0.01,
    market_state: MarketState = MarketState.NEUTRAL
) -> int:
    """
    Calculate position size based on risk

    Formula: Position Size = (Account Value × Risk %) / (Entry Price - Stop Price)

    Position size is modulated by market state:
    - AGGRESSIVE: 1.0× calculated size
    - NEUTRAL: 0.5× calculated size
    - AVOID: 0.0× (no position)

    Args:
        account_value: Total account value
        entry_price: Entry price per share
        stop_price: Stop-loss price per share
        max_risk_pct: Maximum risk per trade (default 1%)
        market_state: Current market state

    Returns:
        Number of shares to trade
    """
    if entry_price <= stop_price:
        logger.warning("Entry price must be > stop price")
        return 0

    if market_state == MarketState.AVOID:
        logger.info("Market state AVOID - no position")
        return 0

    # Calculate base position size
    risk_dollars = account_value * max_risk_pct
    risk_per_share = entry_price - stop_price
    base_shares = int(risk_dollars / risk_per_share)

    # Modulate by market state
    if market_state == MarketState.AGGRESSIVE:
        shares = base_shares
    elif market_state == MarketState.NEUTRAL:
        shares = int(base_shares * 0.5)
    else:
        shares = 0

    # Ensure we don't over-leverage
    max_shares = int(account_value / entry_price)
    shares = min(shares, max_shares)

    logger.info(f"Position size: {shares} shares "
                f"(risk ${risk_dollars:.2f}, state={market_state.value})")

    return shares


def calculate_stop_loss(
    entry_price: float,
    stop_type: str = 'structural',
    structural_level: Optional[float] = None,
    percentage: float = 0.08,
    atr: Optional[float] = None,
    atr_multiplier: float = 2.0
) -> float:
    """
    Calculate stop-loss price

    Supports multiple stop types:
    - structural: At a logical price structure (pattern low)
    - percentage: Fixed percentage below entry
    - atr: ATR-based stop

    Args:
        entry_price: Entry price
        stop_type: Type of stop ('structural', 'percentage', 'atr')
        structural_level: Price level for structural stop
        percentage: Percentage for percentage stop (default 8%)
        atr: Average True Range value
        atr_multiplier: Multiplier for ATR stop (default 2.0)

    Returns:
        Stop-loss price
    """
    if stop_type == 'structural' and structural_level:
        return structural_level
    elif stop_type == 'percentage':
        return entry_price * (1 - percentage)
    elif stop_type == 'atr' and atr:
        return entry_price - (atr * atr_multiplier)
    else:
        # Default to 8% stop
        return entry_price * 0.92


def should_scale_out(
    entry_price: float,
    current_price: float,
    stop_price: float,
    profit_pct: float,
    r_multiple: float
) -> Tuple[bool, float]:
    """
    Determine if position should be scaled out

    Stockbee scaling rules:
    - Move to breakeven at 4% profit
    - Sell half at 2R (2× initial risk)
    - Sell portions at 30-50% profit

    Args:
        entry_price: Entry price
        current_price: Current price
        stop_price: Stop-loss price
        profit_pct: Current profit percentage
        r_multiple: R-multiple (profit / initial risk)

    Returns:
        Tuple of (should_scale, scale_percentage)
    """
    # Check if should move to breakeven
    if profit_pct >= 4.0:
        logger.info(f"Profit {profit_pct:.1f}% >= 4% - move stop to breakeven")
        # This is handled by separate logic, not a scale
        return False, 0.0

    # Check if should sell half at 2R
    if r_multiple >= 2.0:
        logger.info(f"R-multiple {r_multiple:.1f}R >= 2R - sell 50%")
        return True, 0.5

    # Check if should sell portions at 30-50%
    if profit_pct >= 50.0:
        logger.info(f"Profit {profit_pct:.1f}% >= 50% - sell 50%")
        return True, 0.5
    elif profit_pct >= 30.0:
        logger.info(f"Profit {profit_pct:.1f}% >= 30% - sell 25%")
        return True, 0.25

    return False, 0.0


def calculate_r_multiple(entry_price: float, current_price: float, stop_price: float) -> float:
    """
    Calculate R-multiple (reward-to-risk ratio)

    R = Profit / Initial Risk

    Args:
        entry_price: Entry price
        current_price: Current price
        stop_price: Initial stop-loss price

    Returns:
        R-multiple
    """
    initial_risk = entry_price - stop_price
    if initial_risk <= 0:
        return 0.0

    profit = current_price - entry_price
    return profit / initial_risk


def calculate_daily_range_pct(data: pd.DataFrame) -> pd.Series:
    """
    Calculate daily range as percentage of close

    Used for identifying "tight" days

    Args:
        data: OHLCV DataFrame

    Returns:
        Series of daily range percentages
    """
    return ((data['High'] - data['Low']) / data['Close']) * 100


def is_tight_day(data: pd.DataFrame, threshold_pct: float = 2.0) -> pd.Series:
    """
    Identify "tight" days (low volatility)

    A tight day has a range < threshold% of close

    Args:
        data: OHLCV DataFrame
        threshold_pct: Maximum range percentage (default 2%)

    Returns:
        Boolean series indicating tight days
    """
    range_pct = calculate_daily_range_pct(data)
    return range_pct < threshold_pct


def calculate_momentum_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all momentum indicators for Stockbee strategies

    Args:
        data: OHLCV DataFrame

    Returns:
        DataFrame with added indicator columns
    """
    result = data.copy()

    # Moving averages
    result['SMA_10'] = data['Close'].rolling(window=10).mean()
    result['SMA_20'] = data['Close'].rolling(window=20).mean()
    result['SMA_40'] = data['Close'].rolling(window=40).mean()
    result['SMA_50'] = data['Close'].rolling(window=50).mean()
    result['SMA_200'] = data['Close'].rolling(window=200).mean()

    # Daily range percentage
    result['Range_Pct'] = calculate_daily_range_pct(data)

    # Tight day flag
    result['Is_Tight'] = is_tight_day(data)

    # Price change percentage
    result['Pct_Change'] = data['Close'].pct_change() * 100

    # Volume change
    result['Volume_Change'] = data['Volume'].pct_change() * 100

    # ATR for stop-loss
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift(1))
    low_close = np.abs(data['Low'] - data['Close'].shift(1))
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    result['ATR'] = true_range.rolling(window=14).mean()

    return result
