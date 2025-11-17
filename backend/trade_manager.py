"""
Trade Manager - Risk Management and Exit Logic

Implementation of Mark Minervini's trade management rules:
- Initial stop-loss placement (technical + maximum risk)
- Position sizing based on risk
- Trailing stop-loss (breakeven, 50-day MA)
- Climax top detection for profit-taking
- Distribution and reversal day detection
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TradePosition:
    """Data class to track an open trade position"""
    def __init__(
        self,
        entry_price: float,
        entry_date: pd.Timestamp,
        initial_stop: float,
        shares: int = 0
    ):
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.initial_stop = initial_stop
        self.current_stop = initial_stop
        self.shares = shares
        self.highest_price = entry_price
        self.stop_mode = 'initial'  # 'initial', 'breakeven', 'trailing'

    def update_stop(self, new_stop: float, mode: str):
        """Update stop-loss level"""
        self.current_stop = new_stop
        self.stop_mode = mode

    def update_highest_price(self, price: float):
        """Track highest price achieved"""
        if price > self.highest_price:
            self.highest_price = price


def calculate_initial_stop(
    entry_price: float,
    technical_stop: float,
    max_risk_pct: float = 0.10,
    atr: Optional[float] = None
) -> Tuple[float, bool]:
    """
    Calculate initial stop-loss using technical level and maximum risk rule

    The stop is placed at a technical support level (pattern low) with
    an ATR buffer, but must not exceed maximum risk percentage.

    Args:
        entry_price: Entry price
        technical_stop: Technical stop level (e.g., pattern low)
        max_risk_pct: Maximum risk per trade (default 10%)
        atr: Average True Range for buffer

    Returns:
        Tuple of (stop_price, is_valid)
        is_valid = False if technical stop exceeds max risk
    """
    # Apply ATR buffer to technical stop
    if atr:
        adjusted_stop = technical_stop - (0.25 * atr)
    else:
        adjusted_stop = technical_stop

    # Calculate risk percentage
    risk_pct = (entry_price - adjusted_stop) / entry_price

    # Check if risk exceeds maximum
    if risk_pct > max_risk_pct:
        # Trade is too risky - should reject
        logger.warning(f"Stop-loss risk {risk_pct:.1%} exceeds max {max_risk_pct:.1%}")
        return adjusted_stop, False

    return adjusted_stop, True


def calculate_position_size(
    portfolio_value: float,
    entry_price: float,
    stop_price: float,
    risk_per_trade_pct: float = 0.01
) -> int:
    """
    Calculate position size based on portfolio risk

    Uses fixed fractional position sizing to risk a specific percentage
    of portfolio value per trade.

    Args:
        portfolio_value: Total portfolio value
        entry_price: Entry price per share
        stop_price: Stop-loss price per share
        risk_per_trade_pct: Risk per trade as % of portfolio (default 1%)

    Returns:
        Number of shares to buy
    """
    # Calculate dollar risk per share
    risk_per_share = entry_price - stop_price

    if risk_per_share <= 0:
        return 0

    # Calculate total dollar risk for this trade
    portfolio_risk_dollars = portfolio_value * risk_per_trade_pct

    # Calculate share count
    shares = int(portfolio_risk_dollars / risk_per_share)

    # Ensure we don't over-leverage
    max_shares = int(portfolio_value / entry_price)
    shares = min(shares, max_shares)

    logger.info(f"Position size: {shares} shares, risking ${portfolio_risk_dollars:.2f} "
                f"({risk_per_trade_pct:.1%} of portfolio)")

    return shares


def should_move_to_breakeven(
    position: TradePosition,
    current_price: float,
    breakeven_trigger_r: float = 2.0
) -> bool:
    """
    Check if stop should be moved to breakeven

    Move stop to entry price once profit reaches 2R (2× initial risk).

    Args:
        position: TradePosition object
        current_price: Current stock price
        breakeven_trigger_r: R-multiple trigger for breakeven (default 2.0)

    Returns:
        Boolean indicating if breakeven stop should be set
    """
    if position.stop_mode != 'initial':
        return False

    # Calculate initial risk (R)
    initial_risk = position.entry_price - position.initial_stop

    # Calculate current profit
    current_profit = current_price - position.entry_price

    # Check if profit >= 2R
    if current_profit >= (breakeven_trigger_r * initial_risk):
        logger.info(f"Moving stop to breakeven: profit {current_profit:.2f} >= "
                   f"{breakeven_trigger_r}R ({breakeven_trigger_r * initial_risk:.2f})")
        return True

    return False


def calculate_trailing_stop(
    data: pd.DataFrame,
    position: TradePosition,
    use_50day_ma: bool = True
) -> Optional[float]:
    """
    Calculate trailing stop using 50-day MA or other methods

    Args:
        data: OHLCV DataFrame with indicators
        position: TradePosition object
        use_50day_ma: Use 50-day MA as trailing stop (default True)

    Returns:
        New stop price or None
    """
    if len(data) < 50:
        return None

    current_price = data['Close'].iloc[-1]

    # Only trail if in profit
    if current_price <= position.entry_price:
        return position.current_stop

    if use_50day_ma:
        # Use 50-day SMA as trailing stop
        if 'SMA_50' in data.columns:
            ma_50 = data['SMA_50'].iloc[-1]

            # Only move stop up, never down
            if ma_50 > position.current_stop:
                logger.debug(f"Trailing stop: 50-day MA at ${ma_50:.2f}")
                return ma_50

    return position.current_stop


def is_stop_triggered(
    current_price: float,
    stop_price: float,
    use_close: bool = True
) -> bool:
    """
    Check if stop-loss is triggered

    Args:
        current_price: Current price (close or intraday)
        stop_price: Stop-loss price
        use_close: Use closing price (vs intraday low)

    Returns:
        Boolean indicating if stop is hit
    """
    return current_price < stop_price


def detect_distribution_day(data: pd.DataFrame, lookback: int = 1) -> bool:
    """
    Detect distribution day (institutional selling)

    A distribution day occurs when:
    - Price closes down for the day
    - Volume is higher than previous day

    Args:
        data: OHLCV DataFrame
        lookback: Days to look back (default 1)

    Returns:
        Boolean indicating distribution day
    """
    if len(data) < 2:
        return False

    current = data.iloc[-1]
    previous = data.iloc[-2]

    # Price down
    price_down = current['Close'] < previous['Close']

    # Volume up
    volume_up = current['Volume'] > previous['Volume']

    return price_down and volume_up


def detect_key_reversal_day(data: pd.DataFrame) -> bool:
    """
    Detect key reversal day (potential top signal)

    A key reversal day:
    - Makes a new high
    - Closes below previous day's close
    - Ideally on high volume

    Args:
        data: OHLCV DataFrame

    Returns:
        Boolean indicating key reversal
    """
    if len(data) < 2:
        return False

    current = data.iloc[-1]
    previous = data.iloc[-2]

    # New high
    new_high = current['High'] > previous['High']

    # Close below previous close
    close_down = current['Close'] < previous['Close']

    return new_high and close_down


def detect_climax_top(
    data: pd.DataFrame,
    parabolic_threshold: float = 0.60,
    parabolic_days: int = 10,
    extension_threshold: float = 0.70,
    sma_period: int = 150
) -> Dict[str, bool]:
    """
    Detect climax top signals for profit-taking

    Multiple signals indicate exhaustion and potential reversal:
    - Parabolic price run (60% in 10 days)
    - Extreme extension (70% above 150-day MA)
    - Climactic volume (highest volume since breakout)
    - Reversal day after parabolic move

    Args:
        data: OHLCV DataFrame with indicators
        parabolic_threshold: Price gain threshold for parabolic (default 60%)
        parabolic_days: Days for parabolic calculation (default 10)
        extension_threshold: Extension above MA threshold (default 70%)
        sma_period: MA period for extension (default 150)

    Returns:
        Dict of signal_name -> detected (bool)
    """
    signals = {
        'parabolic_run': False,
        'extreme_extension': False,
        'climactic_volume': False,
        'reversal_day': False,
        'is_climax': False
    }

    if len(data) < sma_period:
        return signals

    # Check parabolic run
    if len(data) >= parabolic_days:
        recent_data = data.tail(parabolic_days)
        price_change_pct = (recent_data['Close'].iloc[-1] - recent_data['Close'].iloc[0]) / recent_data['Close'].iloc[0]

        if price_change_pct >= parabolic_threshold:
            signals['parabolic_run'] = True
            logger.info(f"Parabolic run detected: {price_change_pct:.1%} in {parabolic_days} days")

    # Check extreme extension
    if f'SMA_{sma_period}' in data.columns:
        current_price = data['Close'].iloc[-1]
        sma = data[f'SMA_{sma_period}'].iloc[-1]

        if pd.notna(sma) and sma > 0:
            extension = (current_price - sma) / sma

            if extension >= extension_threshold:
                signals['extreme_extension'] = True
                logger.info(f"Extreme extension: {extension:.1%} above {sma_period}-day MA")

    # Check climactic volume
    if len(data) >= 50:
        recent_volume = data['Volume'].tail(50)
        current_volume = data['Volume'].iloc[-1]

        if current_volume == recent_volume.max():
            signals['climactic_volume'] = True
            logger.info("Climactic volume detected")

    # Check for reversal day
    signals['reversal_day'] = detect_key_reversal_day(data)

    # Overall climax signal
    # Need at least 2 signals, with either parabolic or extension
    signal_count = sum(signals.values())

    if signal_count >= 2 and (signals['parabolic_run'] or signals['extreme_extension']):
        signals['is_climax'] = True
        logger.info("CLIMAX TOP DETECTED - Consider profit-taking")

    return signals


def manage_trade(
    data: pd.DataFrame,
    position: TradePosition,
    portfolio_value: float,
    check_climax: bool = True
) -> Tuple[str, Optional[float], str]:
    """
    Comprehensive trade management logic

    Checks all exit conditions and updates stops.

    Args:
        data: OHLCV DataFrame with indicators
        position: TradePosition object
        portfolio_value: Current portfolio value
        check_climax: Check for climax top signals

    Returns:
        Tuple of (action, exit_price, reason)
        action: 'hold', 'sell_stop', 'sell_climax', 'sell_trailing'
        exit_price: Price if selling
        reason: Description of exit reason
    """
    current_price = data['Close'].iloc[-1]

    # Update position's highest price
    position.update_highest_price(current_price)

    # 1. Check initial stop-loss
    if is_stop_triggered(current_price, position.current_stop):
        logger.info(f"Stop-loss triggered at ${current_price:.2f}")
        return 'sell_stop', current_price, f"Stop-loss at ${position.current_stop:.2f}"

    # 2. Check if should move to breakeven
    if should_move_to_breakeven(position, current_price):
        position.update_stop(position.entry_price, 'breakeven')
        logger.info("Stop moved to breakeven")

    # 3. Check climax top signals
    if check_climax and position.stop_mode in ['breakeven', 'trailing']:
        climax_signals = detect_climax_top(data)

        if climax_signals['is_climax']:
            return 'sell_climax', current_price, "Climax top detected"

    # 4. Update trailing stop (if past breakeven)
    if position.stop_mode in ['breakeven', 'trailing']:
        new_stop = calculate_trailing_stop(data, position)

        if new_stop and new_stop > position.current_stop:
            position.update_stop(new_stop, 'trailing')
            logger.debug(f"Trailing stop updated to ${new_stop:.2f}")

        # Check if trailing stop hit
        if position.stop_mode == 'trailing':
            # Use 50-day MA break as sell signal
            if 'SMA_50' in data.columns:
                ma_50 = data['SMA_50'].iloc[-1]
                if current_price < ma_50:
                    logger.info(f"Price closed below 50-day MA: ${current_price:.2f} < ${ma_50:.2f}")
                    return 'sell_trailing', current_price, "Closed below 50-day MA"

    # 5. Hold position
    return 'hold', None, ""


def calculate_profit_metrics(
    position: TradePosition,
    exit_price: float
) -> Dict[str, float]:
    """
    Calculate profit metrics for closed trade

    Args:
        position: TradePosition object
        exit_price: Exit price

    Returns:
        Dict with profit metrics
    """
    entry_price = position.entry_price
    initial_stop = position.initial_stop

    # Calculate profit/loss
    profit_per_share = exit_price - entry_price
    profit_pct = (profit_per_share / entry_price) * 100

    # Calculate R-multiple
    initial_risk = entry_price - initial_stop
    r_multiple = profit_per_share / initial_risk if initial_risk > 0 else 0

    # Calculate total P&L
    total_profit = profit_per_share * position.shares if position.shares > 0 else 0

    metrics = {
        'entry_price': entry_price,
        'exit_price': exit_price,
        'profit_per_share': profit_per_share,
        'profit_pct': profit_pct,
        'r_multiple': r_multiple,
        'total_profit': total_profit,
        'shares': position.shares
    }

    logger.info(f"Trade closed: {profit_pct:+.1f}% ({r_multiple:+.1f}R), "
                f"total P&L: ${total_profit:+,.2f}")

    return metrics
