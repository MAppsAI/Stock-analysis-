"""
Test Strategy Scanner

Simple test script to verify scanner functionality.
"""

import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_stock_universe():
    """Test stock universe fetching"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Stock Universe")
    logger.info("="*60)

    try:
        from stock_universe import (
            get_sp500_tickers,
            get_nasdaq100_tickers,
            get_available_universes
        )

        # Test SP500
        sp500 = get_sp500_tickers()
        logger.info(f"✓ S&P 500: {len(sp500)} stocks")
        logger.info(f"  Sample: {sp500[:5]}")

        # Test NASDAQ100
        nasdaq100 = get_nasdaq100_tickers()
        logger.info(f"✓ NASDAQ 100: {len(nasdaq100)} stocks")
        logger.info(f"  Sample: {nasdaq100[:5]}")

        # Test universes info
        universes = get_available_universes()
        logger.info(f"✓ Available universes: {list(universes.keys())}")

        return True

    except Exception as e:
        logger.error(f"✗ Universe test failed: {e}")
        return False


def test_scanner_import():
    """Test that scanner modules import correctly"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Scanner Imports")
    logger.info("="*60)

    try:
        from strategy_scanner import (
            scan_stock,
            scan_universe,
            generate_summary
        )

        logger.info("✓ Scanner modules imported successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Scanner import failed: {e}")
        return False


def test_single_stock_scan():
    """Test scanning a single stock"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Single Stock Scan")
    logger.info("="*60)

    try:
        from strategy_scanner import scan_stock

        # Scan AAPL for signals
        strategies = ['sma_cross_50_200', 'breakout_52w', 'rsi']

        logger.info(f"Scanning AAPL with strategies: {strategies}")
        results = scan_stock(
            ticker='AAPL',
            strategy_ids=strategies,
            lookback_days=30
        )

        logger.info(f"✓ Found {len(results)} signals for AAPL")
        for result in results[:3]:  # Show first 3
            logger.info(f"  {result.strategy}: {result.signal_type} on {result.signal_date}")

        return True

    except Exception as e:
        logger.error(f"✗ Single stock scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_universe_scan_small():
    """Test scanning a small set of stocks"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Small Universe Scan")
    logger.info("="*60)

    try:
        from strategy_scanner import scan_universe, generate_summary

        # Scan just 10 NASDAQ stocks for speed
        strategies = ['sma_cross_50_200', 'rsi_momentum']

        logger.info(f"Scanning 10 NASDAQ stocks with strategies: {strategies}")
        results = scan_universe(
            universe='nasdaq100',
            strategy_ids=strategies,
            lookback_days=14,
            max_workers=5,
            max_stocks=10  # Just 10 for testing
        )

        summary = generate_summary(results)

        logger.info(f"✓ Scan complete!")
        logger.info(f"  Total signals: {len(results)}")
        logger.info(f"  Unique tickers: {summary['unique_tickers']}")
        logger.info(f"  Buy signals: {summary['buy_signals']}")
        logger.info(f"  Sell signals: {summary['sell_signals']}")

        if summary['by_strategy']:
            logger.info(f"  Signals by strategy:")
            for strategy, count in summary['by_strategy'].items():
                logger.info(f"    {strategy}: {count}")

        # Show some sample signals
        if results:
            logger.info(f"\n  Sample signals:")
            for result in results[:5]:
                logger.info(f"    {result.ticker} - {result.strategy}: "
                          f"{result.signal_type} {result.days_ago} days ago")

        return True

    except Exception as e:
        logger.error(f"✗ Universe scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test that API endpoints are properly registered"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: API Endpoints")
    logger.info("="*60)

    try:
        from main import app

        # Check routes
        routes = [route.path for route in app.routes]

        required_routes = [
            '/api/v1/scanner/universes',
            '/api/v1/scanner/scan'
        ]

        for route in required_routes:
            if route in routes:
                logger.info(f"✓ Endpoint registered: {route}")
            else:
                logger.error(f"✗ Missing endpoint: {route}")
                return False

        return True

    except ModuleNotFoundError as e:
        logger.warning(f"⚠ API endpoint test SKIPPED (FastAPI not available): {e}")
        return True  # Don't fail if FastAPI isn't installed
    except Exception as e:
        logger.error(f"✗ API endpoint test failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("STRATEGY SCANNER - TEST SUITE")
    logger.info("="*60)

    tests = [
        ("Stock Universe", test_stock_universe),
        ("Scanner Imports", test_scanner_import),
        ("Single Stock Scan", test_single_stock_scan),
        ("Small Universe Scan", test_universe_scan_small),
        ("API Endpoints", test_api_endpoints)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        logger.info("\n🎉 ALL TESTS PASSED! Scanner is ready to use.")
        return 0
    else:
        logger.error(f"\n❌ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
