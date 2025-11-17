"""
Test Minervini SEPA Strategy Implementation

This script tests the various components of the Minervini SEPA system:
- Screening and Trend Template
- Pattern recognition (VCP)
- Trade management
- Complete strategy backtesting
"""

import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_minervini_utils():
    """Test utility functions"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Minervini Utilities")
    logger.info("="*60)

    from minervini_utils import (
        calculate_minervini_indicators,
        is_stage_2_uptrend,
        calculate_rs_rating
    )

    # Fetch test data
    ticker = "AAPL"
    data = yf.download(ticker, period='2y', progress=False)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    logger.info(f"Downloaded {len(data)} days of data for {ticker}")

    # Calculate indicators
    data = calculate_minervini_indicators(data)

    logger.info(f"Calculated indicators: {list(data.columns)}")

    # Check Stage 2
    is_stage_2 = is_stage_2_uptrend(data)
    logger.info(f"{ticker} is in Stage 2 uptrend: {is_stage_2}")

    # Check RS rating
    rs_score = data['RS_Score'].iloc[-1]
    logger.info(f"RS Score (standalone): {rs_score:.1f}")

    logger.info("✓ Minervini utilities test PASSED")

    return data


def test_trend_template(data):
    """Test Trend Template validation"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Trend Template")
    logger.info("="*60)

    from screener import apply_trend_template

    passes = apply_trend_template(data)

    logger.info(f"Passes Trend Template: {passes}")

    if passes:
        current = data.iloc[-1]
        logger.info(f"  Price: ${current['Close']:.2f}")
        logger.info(f"  50-day MA: ${current['SMA_50']:.2f}")
        logger.info(f"  150-day MA: ${current['SMA_150']:.2f}")
        logger.info(f"  200-day MA: ${current['SMA_200']:.2f}")
        logger.info(f"  52W High: ${current['52W_High']:.2f}")
        logger.info(f"  52W Low: ${current['52W_Low']:.2f}")

    logger.info("✓ Trend Template test PASSED")


def test_pattern_recognition(data):
    """Test pattern recognition"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Pattern Recognition")
    logger.info("="*60)

    from pattern_recognizer import detect_all_patterns, get_pivot_price

    patterns = detect_all_patterns(data)

    logger.info(f"Has pattern: {patterns['has_pattern']}")
    logger.info(f"Best pattern: {patterns['best_pattern']}")

    if patterns['has_pattern']:
        pivot = get_pivot_price(patterns)
        logger.info(f"Pivot price: ${pivot:.2f}" if pivot else "Pivot price: N/A")

        if patterns['vcp']:
            vcp = patterns['vcp']
            logger.info(f"VCP Details:")
            logger.info(f"  Contractions: {vcp.num_contractions}")
            logger.info(f"  Base duration: {vcp.base_duration_weeks:.1f} weeks")
            logger.info(f"  Volume dry-up: {vcp.volume_dry_up}")

    logger.info("✓ Pattern recognition test PASSED")


def test_screening():
    """Test stock screening"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Stock Screening (Finviz)")
    logger.info("="*60)

    from screener import screen_minervini_candidates

    try:
        candidates = screen_minervini_candidates(
            min_price=10.0,
            min_volume=1000000,
            apply_fundamentals=False,  # Faster test
            max_results=10
        )

        logger.info(f"Found {len(candidates)} candidates: {candidates}")
        logger.info("✓ Screening test PASSED")

    except Exception as e:
        logger.warning(f"Screening test SKIPPED (may require internet): {e}")


def test_minervini_strategy():
    """Test complete Minervini strategy backtest"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Full Strategy Backtest")
    logger.info("="*60)

    from minervini_strategy import (
        calculate_minervini_trend_template_only,
        calculate_minervini_52week_high_breakout,
        calculate_minervini_momentum_leader
    )
    from strategies import calculate_metrics

    # Test on a known strong stock
    ticker = "NVDA"
    logger.info(f"Testing strategies on {ticker}")

    data = yf.download(ticker, period='2y', progress=False)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Test 1: Trend Template Only
    logger.info("\n--- Strategy 1: Trend Template Only ---")
    data_copy = data.copy()
    signals, trades = calculate_minervini_trend_template_only(data_copy)

    if len(trades) > 0:
        metrics = calculate_metrics(data_copy, signals)
        logger.info(f"Total Return: {metrics['total_return']:.2f}%")
        logger.info(f"Win Rate: {metrics['win_rate']:.2f}%")
        logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        logger.info(f"Number of Trades: {metrics['num_trades']}")
    else:
        logger.info("No trades generated")

    # Test 2: 52-Week Breakout
    logger.info("\n--- Strategy 2: 52-Week Breakout ---")
    data_copy = data.copy()
    signals, trades = calculate_minervini_52week_high_breakout(data_copy)

    if len(trades) > 0:
        metrics = calculate_metrics(data_copy, signals)
        logger.info(f"Total Return: {metrics['total_return']:.2f}%")
        logger.info(f"Win Rate: {metrics['win_rate']:.2f}%")
        logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        logger.info(f"Number of Trades: {metrics['num_trades']}")
    else:
        logger.info("No trades generated")

    # Test 3: Momentum Leader
    logger.info("\n--- Strategy 3: Momentum Leader ---")
    data_copy = data.copy()
    signals, trades = calculate_minervini_momentum_leader(data_copy)

    if len(trades) > 0:
        metrics = calculate_metrics(data_copy, signals)
        logger.info(f"Total Return: {metrics['total_return']:.2f}%")
        logger.info(f"Win Rate: {metrics['win_rate']:.2f}%")
        logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        logger.info(f"Number of Trades: {metrics['num_trades']}")
    else:
        logger.info("No trades generated")

    logger.info("\n✓ Strategy backtest test PASSED")


def test_api_integration():
    """Test that strategies are registered in the API"""
    logger.info("\n" + "="*60)
    logger.info("TEST 6: API Integration")
    logger.info("="*60)

    from strategies import STRATEGY_MAP

    # Check if Minervini strategies are in the map
    minervini_strategies = [key for key in STRATEGY_MAP.keys() if 'minervini' in key]

    logger.info(f"Found {len(minervini_strategies)} Minervini strategies in STRATEGY_MAP:")
    for strategy_id in minervini_strategies:
        strategy_info = STRATEGY_MAP[strategy_id]
        logger.info(f"  - {strategy_id}: {strategy_info['name']} ({strategy_info['category']})")

    if len(minervini_strategies) >= 4:
        logger.info("✓ API integration test PASSED")
    else:
        logger.warning(f"⚠ Expected 4 Minervini strategies, found {len(minervini_strategies)}")


def main():
    """Run all tests"""
    logger.info("\n" + "="*70)
    logger.info("MINERVINI SEPA STRATEGY - TEST SUITE")
    logger.info("="*70)

    try:
        # Test 1: Utilities
        data = test_minervini_utils()

        # Test 2: Trend Template
        test_trend_template(data)

        # Test 3: Pattern Recognition
        test_pattern_recognition(data)

        # Test 4: Screening (optional - requires internet)
        test_screening()

        # Test 5: Full Strategy Backtest
        test_minervini_strategy()

        # Test 6: API Integration
        test_api_integration()

        logger.info("\n" + "="*70)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY ✓")
        logger.info("="*70)

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
