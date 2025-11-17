"""
Minervini SEPA Strategy - Complete Implementation

Mark Minervini's Specific Entry Point Analysis (SEPA) methodology:
1. Macro filter (market timing)
2. Universe screening (Trend Template + Fundamentals)
3. Pattern recognition (VCP, Cup-with-Handle, High-Tight Flag)
4. Entry trigger (pivot breakout with volume)
5. Trade management (stop-loss, trailing stop, climax exits)

This module provides strategy functions compatible with the existing
backtesting infrastructure.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Optional
import logging

from minervini_utils import (
    calculate_minervini_indicators,
    is_volume_surge,
    calculate_rs_rating
)
from screener import apply_trend_template
from pattern_recognizer import (
    detect_all_patterns,
    get_pivot_price,
    get_pattern_stop_loss
)
from trade_manager import (
    TradePosition,
    calculate_initial_stop,
    manage_trade,
    detect_climax_top
)

logger = logging.getLogger(__name__)


def calculate_minervini_vcp_strategy(
    data: pd.DataFrame,
    volume_surge_multiplier: float = 1.5,
    pivot_proximity_pct: float = 0.05,
    check_trend_template: bool = True,
    use_trailing_stop: bool = True
) -> Tuple[pd.Series, List[dict]]:
    """
    Mark Minervini VCP Strategy - VCP pattern with pivot breakout

    Entry Logic:
    1. Stock passes Trend Template (Stage 2 uptrend)
    2. VCP pattern detected
    3. Price breaks above pivot on volume surge (1.5x average)
    4. Entry within 5% of pivot

    Exit Logic:
    1. Initial stop below pattern low
    2. Move to breakeven at 2R profit
    3. Trail with 50-day MA
    4. Exit on climax top signals

    Args:
        data: OHLCV DataFrame
        volume_surge_multiplier: Volume multiplier for breakout (default 1.5)
        pivot_proximity_pct: Max distance from pivot for entry (default 5%)
        check_trend_template: Validate Trend Template (default True)
        use_trailing_stop: Use trailing stop management (default True)

    Returns:
        Tuple of (signals, trade_signals)
    """
    # Calculate indicators
    data = calculate_minervini_indicators(data)

    # Initialize signals
    data['Signal'] = 0
    signals_list = []

    # Check if enough data
    if len(data) < 200:
        logger.warning("Insufficient data for Minervini strategy (need 200+ days)")
        return data['Signal'], signals_list

    # Check Trend Template (Stage 2)
    if check_trend_template:
        passes_template = apply_trend_template(data)
        if not passes_template:
            logger.info("Stock does not pass Trend Template - no trades")
            return data['Signal'], signals_list

    # Detect patterns
    patterns = detect_all_patterns(data)

    if not patterns['has_pattern']:
        logger.info("No valid pattern detected - no trades")
        return data['Signal'], signals_list

    # Get pivot price
    pivot_price = get_pivot_price(patterns)

    if not pivot_price:
        logger.warning("Could not determine pivot price")
        return data['Signal'], signals_list

    # Get pattern stop-loss
    pattern_stop = get_pattern_stop_loss(patterns, data)

    if not pattern_stop:
        logger.warning("Could not determine stop-loss")
        return data['Signal'], signals_list

    logger.info(f"Pattern detected: {patterns['best_pattern']}, "
                f"pivot ${pivot_price:.2f}, stop ${pattern_stop:.2f}")

    # Track position
    position = None
    in_position = False

    # Iterate through data for entry/exit signals
    for i in range(200, len(data)):
        current_date = data.index[i]
        current_data = data.iloc[:i+1]
        current_price = current_data['Close'].iloc[-1]
        current_high = current_data['High'].iloc[-1]
        current_volume = current_data['Volume'].iloc[-1]

        # Entry logic
        if not in_position:
            # Check for pivot breakout
            price_above_pivot = current_high >= pivot_price

            # Check volume surge
            volume_surge = is_volume_surge(current_data.tail(1), multiplier=volume_surge_multiplier).iloc[-1]

            # Check proximity (entry not too far from pivot)
            within_proximity = current_price <= (pivot_price * (1 + pivot_proximity_pct))

            if price_above_pivot and volume_surge and within_proximity:
                # Enter position
                entry_price = current_price
                stop_price, is_valid = calculate_initial_stop(
                    entry_price,
                    pattern_stop,
                    max_risk_pct=0.10,
                    atr=current_data['ATR'].iloc[-1]
                )

                if is_valid:
                    # Create position
                    position = TradePosition(
                        entry_price=entry_price,
                        entry_date=current_date,
                        initial_stop=stop_price
                    )

                    in_position = True
                    data.loc[current_date, 'Signal'] = 1

                    signals_list.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'price': float(entry_price),
                        'type': 'buy'
                    })

                    logger.info(f"BUY: {current_date.strftime('%Y-%m-%d')} @ ${entry_price:.2f}, "
                               f"stop ${stop_price:.2f}, risk {((entry_price-stop_price)/entry_price):.1%}")
                else:
                    logger.warning("Entry rejected: stop-loss risk too high")

        # Exit logic
        elif in_position and position:
            # Manage trade
            action, exit_price, reason = manage_trade(
                current_data,
                position,
                portfolio_value=100000,  # Placeholder
                check_climax=use_trailing_stop
            )

            if action != 'hold':
                # Exit position
                in_position = False
                data.loc[current_date, 'Signal'] = 0

                signals_list.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'price': float(exit_price),
                    'type': 'sell'
                })

                profit_pct = ((exit_price - position.entry_price) / position.entry_price) * 100

                logger.info(f"SELL: {current_date.strftime('%Y-%m-%d')} @ ${exit_price:.2f}, "
                           f"profit {profit_pct:+.1f}%, reason: {reason}")

                position = None
            else:
                # Hold position
                data.loc[current_date, 'Signal'] = 1

    # Calculate position changes
    data['Position'] = data['Signal'].diff()

    return data['Signal'], signals_list


def calculate_minervini_trend_template_only(
    data: pd.DataFrame,
    exit_on_template_fail: bool = True
) -> Tuple[pd.Series, List[dict]]:
    """
    Simple Minervini strategy - Buy when passes Trend Template, sell when fails

    This is a simplified version that only uses the 8-criteria Trend Template
    without pattern recognition.

    Args:
        data: OHLCV DataFrame
        exit_on_template_fail: Exit when Trend Template fails

    Returns:
        Tuple of (signals, trade_signals)
    """
    # Calculate indicators
    data = calculate_minervini_indicators(data)

    # Initialize signals
    data['Signal'] = 0
    signals_list = []

    if len(data) < 200:
        return data['Signal'], signals_list

    # Check Trend Template daily
    in_position = False

    for i in range(200, len(data)):
        current_date = data.index[i]
        current_data = data.iloc[:i+1]
        current_price = current_data['Close'].iloc[-1]

        passes_template = apply_trend_template(current_data)

        if passes_template and not in_position:
            # Enter position
            in_position = True
            data.loc[current_date, 'Signal'] = 1

            signals_list.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'price': float(current_price),
                'type': 'buy'
            })

            logger.info(f"BUY (Template): {current_date.strftime('%Y-%m-%d')} @ ${current_price:.2f}")

        elif not passes_template and in_position and exit_on_template_fail:
            # Exit position
            in_position = False
            data.loc[current_date, 'Signal'] = 0

            signals_list.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'price': float(current_price),
                'type': 'sell'
            })

            logger.info(f"SELL (Template fail): {current_date.strftime('%Y-%m-%d')} @ ${current_price:.2f}")

        elif in_position:
            data.loc[current_date, 'Signal'] = 1

    data['Position'] = data['Signal'].diff()

    return data['Signal'], signals_list


def calculate_minervini_52week_high_breakout(
    data: pd.DataFrame,
    use_trend_template: bool = True
) -> Tuple[pd.Series, List[dict]]:
    """
    Minervini 52-Week High Breakout Strategy

    Buy when:
    1. Stock passes Trend Template (optional)
    2. Price breaks to new 52-week high
    3. Volume surge on breakout

    Exit when:
    1. Price closes below 50-day MA
    2. Climax top detected

    Args:
        data: OHLCV DataFrame
        use_trend_template: Require Trend Template (default True)

    Returns:
        Tuple of (signals, trade_signals)
    """
    # Calculate indicators
    data = calculate_minervini_indicators(data)

    data['Signal'] = 0
    signals_list = []

    if len(data) < 252:
        return data['Signal'], signals_list

    in_position = False

    for i in range(252, len(data)):
        current_date = data.index[i]
        current_data = data.iloc[:i+1]
        current_price = current_data['Close'].iloc[-1]
        current_high = current_data['High'].iloc[-1]

        # Entry logic
        if not in_position:
            # Check Trend Template
            if use_trend_template:
                passes_template = apply_trend_template(current_data)
                if not passes_template:
                    continue

            # Check 52-week high breakout
            week_52_high = current_data['52W_High'].iloc[-2]  # Previous 52W high
            is_breakout = current_high >= week_52_high

            # Check volume surge
            volume_surge = is_volume_surge(current_data.tail(1)).iloc[-1]

            if is_breakout and volume_surge:
                in_position = True
                data.loc[current_date, 'Signal'] = 1

                signals_list.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'price': float(current_price),
                    'type': 'buy'
                })

                logger.info(f"BUY (52W High): {current_date.strftime('%Y-%m-%d')} @ ${current_price:.2f}")

        # Exit logic
        elif in_position:
            # Exit on 50-day MA break
            ma_50 = current_data['SMA_50'].iloc[-1]
            if current_price < ma_50:
                in_position = False
                data.loc[current_date, 'Signal'] = 0

                signals_list.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'price': float(current_price),
                    'type': 'sell'
                })

                logger.info(f"SELL (MA break): {current_date.strftime('%Y-%m-%d')} @ ${current_price:.2f}")

            # Exit on climax top
            elif detect_climax_top(current_data)['is_climax']:
                in_position = False
                data.loc[current_date, 'Signal'] = 0

                signals_list.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'price': float(current_price),
                    'type': 'sell'
                })

                logger.info(f"SELL (Climax): {current_date.strftime('%Y-%m-%d')} @ ${current_price:.2f}")

            else:
                data.loc[current_date, 'Signal'] = 1

    data['Position'] = data['Signal'].diff()

    return data['Signal'], signals_list


def calculate_minervini_momentum_leader(
    data: pd.DataFrame,
    rs_threshold: float = 80,
    volume_surge_multiplier: float = 1.5
) -> Tuple[pd.Series, List[dict]]:
    """
    Minervini Momentum Leader Strategy

    Focus on highest momentum stocks with RS Rating > 80.

    Buy when:
    1. RS Rating > 80 (top 20% of stocks)
    2. Price above all key MAs (50, 150, 200)
    3. Volume surge

    Exit when:
    1. RS Rating falls below 70
    2. Price closes below 50-day MA

    Args:
        data: OHLCV DataFrame
        rs_threshold: Minimum RS rating (default 80)
        volume_surge_multiplier: Volume multiplier (default 1.5)

    Returns:
        Tuple of (signals, trade_signals)
    """
    # Calculate indicators
    data = calculate_minervini_indicators(data)

    data['Signal'] = 0
    signals_list = []

    if len(data) < 252:
        return data['Signal'], signals_list

    in_position = False

    for i in range(252, len(data)):
        current_date = data.index[i]
        current_data = data.iloc[:i+1]
        current_price = current_data['Close'].iloc[-1]

        # Calculate RS rating
        rs_score = current_data['RS_Score'].iloc[-1]

        # Entry logic
        if not in_position:
            # High RS rating
            high_rs = rs_score > rs_threshold

            # Above all MAs
            above_mas = (
                current_price > current_data['SMA_50'].iloc[-1] and
                current_price > current_data['SMA_150'].iloc[-1] and
                current_price > current_data['SMA_200'].iloc[-1]
            )

            # Volume surge
            volume_surge = is_volume_surge(current_data.tail(1), multiplier=volume_surge_multiplier).iloc[-1]

            if high_rs and above_mas and volume_surge:
                in_position = True
                data.loc[current_date, 'Signal'] = 1

                signals_list.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'price': float(current_price),
                    'type': 'buy'
                })

                logger.info(f"BUY (Momentum): {current_date.strftime('%Y-%m-%d')} @ ${current_price:.2f}, RS={rs_score:.0f}")

        # Exit logic
        elif in_position:
            # Exit if RS drops
            if rs_score < 70:
                in_position = False
                data.loc[current_date, 'Signal'] = 0

                signals_list.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'price': float(current_price),
                    'type': 'sell'
                })

                logger.info(f"SELL (RS drop): {current_date.strftime('%Y-%m-%d')} @ ${current_price:.2f}")

            # Exit if below 50-day MA
            elif current_price < current_data['SMA_50'].iloc[-1]:
                in_position = False
                data.loc[current_date, 'Signal'] = 0

                signals_list.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'price': float(current_price),
                    'type': 'sell'
                })

                logger.info(f"SELL (MA break): {current_date.strftime('%Y-%m-%d')} @ ${current_price:.2f}")

            else:
                data.loc[current_date, 'Signal'] = 1

    data['Position'] = data['Signal'].diff()

    return data['Signal'], signals_list


# Strategy registry for Minervini strategies
MINERVINI_STRATEGY_MAP = {
    'minervini_vcp': {
        'name': 'Minervini VCP Strategy',
        'func': calculate_minervini_vcp_strategy,
        'category': 'Minervini SEPA',
        'description': 'Full SEPA implementation with VCP pattern recognition and trade management'
    },
    'minervini_trend_template': {
        'name': 'Minervini Trend Template',
        'func': calculate_minervini_trend_template_only,
        'category': 'Minervini SEPA',
        'description': 'Stage 2 identification using 8-criteria Trend Template'
    },
    'minervini_52w_breakout': {
        'name': 'Minervini 52-Week Breakout',
        'func': calculate_minervini_52week_high_breakout,
        'category': 'Minervini SEPA',
        'description': '52-week high breakout with Trend Template and volume confirmation'
    },
    'minervini_momentum_leader': {
        'name': 'Minervini Momentum Leader',
        'func': calculate_minervini_momentum_leader,
        'category': 'Minervini SEPA',
        'description': 'High RS rating (>80) momentum leaders with MA alignment'
    }
}