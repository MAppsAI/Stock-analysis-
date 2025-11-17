"""
Pattern Recognizer - VCP and Minervini Chart Patterns

Implementation of Mark Minervini's key chart patterns:
- Volatility Contraction Pattern (VCP)
- Cup-with-Handle / 3C (Cheat) patterns
- High-Tight Flag (Power Play)
- Base identification and pivot point calculation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from minervini_utils import detect_swing_points, is_volume_dry_up

logger = logging.getLogger(__name__)


class VCPPattern:
    """Data class for VCP pattern information"""
    def __init__(self):
        self.is_valid = False
        self.base_start = None
        self.base_end = None
        self.base_duration_weeks = 0
        self.pivot_price = 0.0
        self.contractions = []  # List of contraction dicts
        self.num_contractions = 0
        self.volume_dry_up = False
        self.final_contraction_depth = 0.0


def detect_vcp(
    data: pd.DataFrame,
    min_base_weeks: int = 3,
    max_base_weeks: int = 20,
    min_contractions: int = 2,
    max_final_depth: float = 0.10
) -> Optional[VCPPattern]:
    """
    Detect Volatility Contraction Pattern (VCP)

    A VCP is a consolidation pattern characterized by:
    - A series of progressively smaller price pullbacks (contractions)
    - Each contraction is shallower than the previous one
    - Volume dries up during the final contraction
    - Forms within a Stage 2 uptrend

    Args:
        data: OHLCV DataFrame with indicators
        min_base_weeks: Minimum base duration (default 3 weeks)
        max_base_weeks: Maximum base duration (default 20 weeks)
        min_contractions: Minimum number of contractions (default 2)
        max_final_depth: Maximum depth of final contraction (default 10%)

    Returns:
        VCPPattern object if valid pattern found, None otherwise
    """
    if len(data) < 50:  # Need sufficient data
        return None

    # Detect swing points
    swing_highs, swing_lows = detect_swing_points(data, window=5)

    # Get swing high and low points
    high_points = data[swing_highs].copy()
    low_points = data[swing_lows].copy()

    if len(high_points) < min_contractions + 1 or len(low_points) < min_contractions:
        return None

    # Analyze recent base (last ~100 days)
    recent_data = data.tail(100)
    recent_high_points = high_points[high_points.index.isin(recent_data.index)]
    recent_low_points = low_points[low_points.index.isin(recent_data.index)]

    if len(recent_high_points) < 2 or len(recent_low_points) < 2:
        return None

    # Identify base high (highest point in recent data)
    base_high_idx = recent_high_points['High'].idxmax()
    base_high_price = recent_high_points.loc[base_high_idx, 'High']

    # Find contractions after base high
    contractions = []

    # Get all lows after base high
    lows_after_high = recent_low_points[recent_low_points.index > base_high_idx].copy()
    highs_after_high = recent_high_points[recent_high_points.index > base_high_idx].copy()

    if len(lows_after_high) < min_contractions:
        return None

    # Analyze contractions
    prev_high = base_high_price
    prev_low_depth = float('inf')

    for i, (low_idx, low_row) in enumerate(lows_after_high.iterrows()):
        low_price = low_row['Low']

        # Find the high before this low
        highs_before_low = highs_after_high[highs_after_high.index < low_idx]

        if len(highs_before_low) > 0:
            local_high_price = highs_before_low['High'].iloc[-1]
        else:
            local_high_price = prev_high

        # Calculate contraction depth
        depth = (local_high_price - low_price) / local_high_price

        # Check if this is a valid contraction (shallower than previous)
        is_shallower = depth < prev_low_depth

        contractions.append({
            'low_idx': low_idx,
            'high_price': local_high_price,
            'low_price': low_price,
            'depth': depth,
            'is_shallower': is_shallower
        })

        prev_high = local_high_price
        prev_low_depth = depth

    # Validate VCP criteria
    if len(contractions) < min_contractions:
        return None

    # Check that contractions are progressively shallower
    valid_contractions = []
    for i, contraction in enumerate(contractions):
        if i == 0:
            valid_contractions.append(contraction)
        else:
            # Must be shallower than previous
            if contraction['depth'] < valid_contractions[-1]['depth']:
                valid_contractions.append(contraction)
            else:
                # Not a valid VCP - contractions not tightening
                break

    if len(valid_contractions) < min_contractions:
        return None

    # Check final contraction depth
    final_contraction = valid_contractions[-1]
    if final_contraction['depth'] > max_final_depth:
        return None

    # Check for volume dry-up in final contraction
    final_low_idx = final_contraction['low_idx']
    recent_window = data.loc[final_low_idx:].tail(10)

    volume_dry_up = False
    if len(recent_window) > 0:
        try:
            volume_dry_up = is_volume_dry_up(recent_window).iloc[-1]
        except:
            pass

    # Calculate base duration
    base_start = recent_data.index[0]
    base_end = data.index[-1]
    base_duration_days = (base_end - base_start).days
    base_duration_weeks = base_duration_days / 7

    if base_duration_weeks < min_base_weeks or base_duration_weeks > max_base_weeks:
        return None

    # Create VCP pattern object
    vcp = VCPPattern()
    vcp.is_valid = True
    vcp.base_start = base_start
    vcp.base_end = base_end
    vcp.base_duration_weeks = base_duration_weeks
    vcp.pivot_price = base_high_price
    vcp.contractions = valid_contractions
    vcp.num_contractions = len(valid_contractions)
    vcp.volume_dry_up = volume_dry_up
    vcp.final_contraction_depth = final_contraction['depth']

    logger.info(f"VCP detected: {vcp.num_contractions} contractions, "
                f"base {vcp.base_duration_weeks:.1f} weeks, "
                f"pivot ${vcp.pivot_price:.2f}, "
                f"final depth {vcp.final_contraction_depth:.1%}")

    return vcp


def detect_cup_with_handle(
    data: pd.DataFrame,
    min_cup_weeks: int = 7,
    max_handle_weeks: int = 5,
    handle_depth_pct: float = 0.12
) -> Optional[Dict]:
    """
    Detect Cup-with-Handle pattern

    Similar to VCP but with specific cup and handle characteristics.

    Args:
        data: OHLCV DataFrame
        min_cup_weeks: Minimum cup duration
        max_handle_weeks: Maximum handle duration
        handle_depth_pct: Maximum handle depth (default 12%)

    Returns:
        Dict with pattern info or None
    """
    if len(data) < 50:
        return None

    # Look at recent data (last 6 months)
    recent_data = data.tail(126)

    # Find the highest point (left cup rim)
    left_rim_idx = recent_data['High'].idxmax()
    left_rim_price = recent_data.loc[left_rim_idx, 'High']

    # Find the lowest point after left rim (cup bottom)
    data_after_left = recent_data[recent_data.index > left_rim_idx]

    if len(data_after_left) < 20:
        return None

    cup_bottom_idx = data_after_left['Low'].idxmin()
    cup_bottom_price = data_after_left.loc[cup_bottom_idx, 'Low']

    # Find right rim (recovery high after bottom)
    data_after_bottom = data_after_left[data_after_left.index > cup_bottom_idx]

    if len(data_after_bottom) < 10:
        return None

    right_rim_idx = data_after_bottom['High'].idxmax()
    right_rim_price = data_after_bottom.loc[right_rim_idx, 'High']

    # Check if right rim is near left rim (within 5%)
    if right_rim_price < left_rim_price * 0.95:
        return None

    # Find handle (pullback after right rim)
    data_after_right = data_after_bottom[data_after_bottom.index > right_rim_idx]

    if len(data_after_right) < 5:
        return None

    handle_low_idx = data_after_right['Low'].idxmin()
    handle_low_price = data_after_right.loc[handle_low_idx, 'Low']

    # Calculate handle depth
    handle_depth = (right_rim_price - handle_low_price) / right_rim_price

    if handle_depth > handle_depth_pct:
        return None

    # Calculate durations
    cup_duration = (right_rim_idx - left_rim_idx).days / 7
    handle_duration = (data.index[-1] - right_rim_idx).days / 7

    if cup_duration < min_cup_weeks:
        return None

    if handle_duration > max_handle_weeks:
        return None

    pattern = {
        'type': 'Cup-with-Handle',
        'left_rim': left_rim_price,
        'cup_bottom': cup_bottom_price,
        'right_rim': right_rim_price,
        'handle_low': handle_low_price,
        'pivot_price': right_rim_price,
        'handle_depth': handle_depth,
        'cup_weeks': cup_duration,
        'handle_weeks': handle_duration
    }

    logger.info(f"Cup-with-Handle detected: pivot ${pattern['pivot_price']:.2f}, "
                f"handle depth {handle_depth:.1%}")

    return pattern


def detect_high_tight_flag(
    data: pd.DataFrame,
    min_gain_pct: float = 100.0,
    gain_period_weeks: int = 8,
    flag_max_depth: float = 0.25,
    flag_max_weeks: int = 6
) -> Optional[Dict]:
    """
    Detect High-Tight Flag (Power Play) pattern

    Characteristics:
    - Stock doubles (+100%) in ~8 weeks or less
    - Consolidates in a tight flag (10-25% pullback)
    - Flag duration: 2-6 weeks
    - Very explosive pattern

    Args:
        data: OHLCV DataFrame
        min_gain_pct: Minimum price gain (default 100%)
        gain_period_weeks: Period for gain calculation (default 8 weeks)
        flag_max_depth: Maximum flag depth (default 25%)
        flag_max_weeks: Maximum flag duration (default 6 weeks)

    Returns:
        Dict with pattern info or None
    """
    if len(data) < 60:
        return None

    # Look for explosive move in recent data
    lookback_days = gain_period_weeks * 5  # ~40 trading days for 8 weeks

    if len(data) < lookback_days + 30:
        return None

    recent_data = data.tail(lookback_days + 30)

    # Find the low point before the explosive move
    # Scan for the biggest gain over the lookback period
    max_gain = 0
    explosive_low_idx = None
    explosive_high_idx = None

    for i in range(len(recent_data) - lookback_days):
        window = recent_data.iloc[i:i+lookback_days]
        low_price = window['Low'].min()
        high_price = window['High'].max()

        gain_pct = ((high_price - low_price) / low_price) * 100

        if gain_pct > max_gain:
            max_gain = gain_pct
            explosive_low_idx = window['Low'].idxmin()
            explosive_high_idx = window['High'].idxmax()

    # Check if gain meets threshold
    if max_gain < min_gain_pct:
        return None

    # Verify high comes after low
    if explosive_high_idx <= explosive_low_idx:
        return None

    explosive_low_price = data.loc[explosive_low_idx, 'Low']
    explosive_high_price = data.loc[explosive_high_idx, 'High']

    # Look for flag consolidation after explosive high
    data_after_high = data[data.index > explosive_high_idx]

    if len(data_after_high) < 10:
        return None

    flag_low_idx = data_after_high['Low'].idxmin()
    flag_low_price = data_after_high.loc[flag_low_idx, 'Low']

    # Calculate flag depth
    flag_depth = (explosive_high_price - flag_low_price) / explosive_high_price

    if flag_depth > flag_max_depth:
        return None

    # Calculate flag duration
    flag_duration_weeks = (data.index[-1] - explosive_high_idx).days / 7

    if flag_duration_weeks > flag_max_weeks:
        return None

    pattern = {
        'type': 'High-Tight-Flag',
        'explosive_gain_pct': max_gain,
        'explosive_low': explosive_low_price,
        'explosive_high': explosive_high_price,
        'flag_low': flag_low_price,
        'flag_depth': flag_depth,
        'flag_weeks': flag_duration_weeks,
        'pivot_price': explosive_high_price
    }

    logger.info(f"High-Tight-Flag detected: {max_gain:.0f}% gain, "
                f"flag depth {flag_depth:.1%}, pivot ${pattern['pivot_price']:.2f}")

    return pattern


def detect_all_patterns(data: pd.DataFrame) -> Dict[str, any]:
    """
    Detect all Minervini patterns in the data

    Args:
        data: OHLCV DataFrame with indicators

    Returns:
        Dict with pattern detection results
    """
    results = {
        'vcp': None,
        'cup_with_handle': None,
        'high_tight_flag': None,
        'has_pattern': False,
        'best_pattern': None
    }

    # Detect VCP
    vcp = detect_vcp(data)
    if vcp and vcp.is_valid:
        results['vcp'] = vcp
        results['has_pattern'] = True
        results['best_pattern'] = 'vcp'

    # Detect Cup-with-Handle
    cwh = detect_cup_with_handle(data)
    if cwh:
        results['cup_with_handle'] = cwh
        results['has_pattern'] = True
        if not results['best_pattern']:
            results['best_pattern'] = 'cup_with_handle'

    # Detect High-Tight-Flag
    htf = detect_high_tight_flag(data)
    if htf:
        results['high_tight_flag'] = htf
        results['has_pattern'] = True
        # HTF is highest priority
        results['best_pattern'] = 'high_tight_flag'

    return results


def get_pivot_price(patterns: Dict[str, any]) -> Optional[float]:
    """
    Get the pivot price from detected patterns

    Args:
        patterns: Dict from detect_all_patterns()

    Returns:
        Pivot price or None
    """
    if not patterns['has_pattern']:
        return None

    best_pattern = patterns['best_pattern']

    if best_pattern == 'vcp' and patterns['vcp']:
        return patterns['vcp'].pivot_price
    elif best_pattern == 'cup_with_handle' and patterns['cup_with_handle']:
        return patterns['cup_with_handle']['pivot_price']
    elif best_pattern == 'high_tight_flag' and patterns['high_tight_flag']:
        return patterns['high_tight_flag']['pivot_price']

    return None


def get_pattern_stop_loss(patterns: Dict[str, any], data: pd.DataFrame) -> Optional[float]:
    """
    Calculate appropriate stop-loss based on detected pattern

    Args:
        patterns: Dict from detect_all_patterns()
        data: OHLCV DataFrame

    Returns:
        Stop-loss price or None
    """
    if not patterns['has_pattern']:
        return None

    best_pattern = patterns['best_pattern']

    if best_pattern == 'vcp' and patterns['vcp']:
        # Stop below final contraction low
        vcp = patterns['vcp']
        if len(vcp.contractions) > 0:
            final_low = vcp.contractions[-1]['low_price']
            # Add small buffer using ATR
            if 'ATR' in data.columns:
                atr = data['ATR'].iloc[-1]
                stop = final_low - (0.25 * atr)
            else:
                stop = final_low * 0.98  # 2% buffer
            return stop

    elif best_pattern == 'cup_with_handle' and patterns['cup_with_handle']:
        # Stop below handle low
        cwh = patterns['cup_with_handle']
        handle_low = cwh['handle_low']
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            stop = handle_low - (0.25 * atr)
        else:
            stop = handle_low * 0.98
        return stop

    elif best_pattern == 'high_tight_flag' and patterns['high_tight_flag']:
        # Stop below flag low
        htf = patterns['high_tight_flag']
        flag_low = htf['flag_low']
        if 'ATR' in data.columns:
            atr = data['ATR'].iloc[-1]
            stop = flag_low - (0.25 * atr)
        else:
            stop = flag_low * 0.98
        return stop

    return None
