"""
Strategy Scanner - Multi-Stock Signal Detection

Scans large universes of stocks to find recent buy/sell signals
across multiple trading strategies.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Optional import for faster downloads
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    logging.warning("yfinance not available - scanner will not work")

from strategies import STRATEGY_MAP
from stock_universe import get_universe_tickers

logger = logging.getLogger(__name__)


class ScanResult:
    """Data class for scan results"""
    def __init__(
        self,
        ticker: str,
        strategy: str,
        signal_type: str,
        signal_date: str,
        signal_price: float,
        current_price: float,
        days_ago: int,
        metadata: Optional[Dict] = None
    ):
        self.ticker = ticker
        self.strategy = strategy
        self.signal_type = signal_type
        self.signal_date = signal_date
        self.signal_price = signal_price
        self.current_price = current_price
        self.days_ago = days_ago
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'ticker': self.ticker,
            'strategy': self.strategy,
            'signal_type': self.signal_type,
            'signal_date': self.signal_date,
            'signal_price': self.signal_price,
            'current_price': self.current_price,
            'days_ago': self.days_ago,
            'price_change_pct': ((self.current_price - self.signal_price) / self.signal_price) * 100,
            'metadata': self.metadata
        }


def download_stock_data(
    ticker: str,
    period: str = '6mo',
    max_retries: int = 2
) -> Optional[pd.DataFrame]:
    """
    Download stock data with retries

    Args:
        ticker: Stock ticker
        period: Data period (default 6 months)
        max_retries: Maximum retry attempts

    Returns:
        DataFrame or None if failed
    """
    if not HAS_YFINANCE:
        return None

    for attempt in range(max_retries):
        try:
            data = yf.download(ticker, period=period, progress=False, timeout=10)

            if data.empty:
                return None

            # Handle multi-level columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            return data
        except Exception as e:
            if attempt == max_retries - 1:
                logger.debug(f"Failed to download {ticker}: {e}")
                return None

    return None


def scan_stock(
    ticker: str,
    strategy_ids: List[str],
    lookback_days: int = 14,
    data_period: str = '6mo'
) -> List[ScanResult]:
    """
    Scan a single stock for signals across multiple strategies

    Args:
        ticker: Stock ticker
        strategy_ids: List of strategy IDs to run
        lookback_days: Days to look back for signals
        data_period: Data period to download

    Returns:
        List of ScanResult objects
    """
    results = []

    # Download data
    data = download_stock_data(ticker, period=data_period)
    if data is None or len(data) < 50:
        return results

    # Calculate cutoff date for recent signals
    cutoff_date = datetime.now() - timedelta(days=lookback_days)

    # Run each strategy
    for strategy_id in strategy_ids:
        if strategy_id not in STRATEGY_MAP:
            continue

        try:
            # Make a copy of data for this strategy
            strategy_data = data.copy()

            # Get strategy function
            strategy_func = STRATEGY_MAP[strategy_id]['func']
            strategy_name = STRATEGY_MAP[strategy_id]['name']

            # Run strategy
            signals, trade_signals = strategy_func(strategy_data)

            # Check for recent buy signals
            for signal in trade_signals:
                signal_date = datetime.strptime(signal['date'], '%Y-%m-%d')

                # Only include signals within lookback period
                if signal_date >= cutoff_date:
                    days_ago = (datetime.now() - signal_date).days
                    current_price = float(data['Close'].iloc[-1])

                    result = ScanResult(
                        ticker=ticker,
                        strategy=strategy_name,
                        signal_type=signal['type'],
                        signal_date=signal['date'],
                        signal_price=signal['price'],
                        current_price=current_price,
                        days_ago=days_ago,
                        metadata={
                            'strategy_id': strategy_id,
                            'strategy_category': STRATEGY_MAP[strategy_id].get('category', 'Unknown')
                        }
                    )

                    results.append(result)

        except Exception as e:
            logger.debug(f"Error running {strategy_id} on {ticker}: {e}")
            continue

    return results


def scan_universe(
    universe: str,
    strategy_ids: List[str],
    lookback_days: int = 14,
    max_workers: int = 10,
    max_stocks: Optional[int] = None
) -> List[ScanResult]:
    """
    Scan an entire universe of stocks for signals

    Args:
        universe: Universe name ('sp500', 'nasdaq100', 'russell2000', 'all')
        strategy_ids: List of strategy IDs to run
        lookback_days: Days to look back for signals
        max_workers: Number of parallel workers
        max_stocks: Maximum number of stocks to scan (for testing)

    Returns:
        List of ScanResult objects
    """
    logger.info(f"Starting scan: universe={universe}, strategies={len(strategy_ids)}, "
                f"lookback={lookback_days} days")

    # Get tickers
    tickers = get_universe_tickers(universe)

    if not tickers:
        logger.error(f"No tickers found for universe: {universe}")
        return []

    if max_stocks:
        tickers = tickers[:max_stocks]

    logger.info(f"Scanning {len(tickers)} stocks...")

    all_results = []
    completed = 0

    # Use ThreadPoolExecutor for parallel scanning
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_ticker = {
            executor.submit(scan_stock, ticker, strategy_ids, lookback_days): ticker
            for ticker in tickers
        }

        # Process completed tasks
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            completed += 1

            if completed % 50 == 0:
                logger.info(f"Progress: {completed}/{len(tickers)} stocks scanned")

            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                logger.debug(f"Error scanning {ticker}: {e}")

    logger.info(f"Scan complete: Found {len(all_results)} signals across {len(tickers)} stocks")

    return all_results


def filter_results(
    results: List[ScanResult],
    signal_type: Optional[str] = None,
    min_days_ago: Optional[int] = None,
    max_days_ago: Optional[int] = None,
    strategies: Optional[List[str]] = None
) -> List[ScanResult]:
    """
    Filter scan results by various criteria

    Args:
        results: List of ScanResult objects
        signal_type: Filter by signal type ('buy' or 'sell')
        min_days_ago: Minimum days ago
        max_days_ago: Maximum days ago
        strategies: Filter by strategy names

    Returns:
        Filtered list of results
    """
    filtered = results

    if signal_type:
        filtered = [r for r in filtered if r.signal_type == signal_type]

    if min_days_ago is not None:
        filtered = [r for r in filtered if r.days_ago >= min_days_ago]

    if max_days_ago is not None:
        filtered = [r for r in filtered if r.days_ago <= max_days_ago]

    if strategies:
        filtered = [r for r in filtered if r.strategy in strategies]

    return filtered


def rank_results(
    results: List[ScanResult],
    by: str = 'recent'
) -> List[ScanResult]:
    """
    Rank and sort scan results

    Args:
        results: List of ScanResult objects
        by: Ranking method ('recent', 'performance', 'ticker')

    Returns:
        Sorted list of results
    """
    if by == 'recent':
        # Most recent first
        return sorted(results, key=lambda r: r.days_ago)
    elif by == 'performance':
        # Best performance first
        return sorted(results, key=lambda r: (r.current_price - r.signal_price) / r.signal_price, reverse=True)
    elif by == 'ticker':
        # Alphabetical by ticker
        return sorted(results, key=lambda r: r.ticker)
    else:
        return results


def group_results_by_ticker(results: List[ScanResult]) -> Dict[str, List[ScanResult]]:
    """
    Group results by ticker

    Args:
        results: List of ScanResult objects

    Returns:
        Dict mapping ticker -> list of results
    """
    grouped = {}
    for result in results:
        if result.ticker not in grouped:
            grouped[result.ticker] = []
        grouped[result.ticker].append(result)

    return grouped


def group_results_by_strategy(results: List[ScanResult]) -> Dict[str, List[ScanResult]]:
    """
    Group results by strategy

    Args:
        results: List of ScanResult objects

    Returns:
        Dict mapping strategy -> list of results
    """
    grouped = {}
    for result in results:
        if result.strategy not in grouped:
            grouped[result.strategy] = []
        grouped[result.strategy].append(result)

    return grouped


def generate_summary(results: List[ScanResult]) -> Dict:
    """
    Generate summary statistics for scan results

    Args:
        results: List of ScanResult objects

    Returns:
        Summary dictionary
    """
    if not results:
        return {
            'total_signals': 0,
            'unique_tickers': 0,
            'unique_strategies': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'avg_performance_pct': 0.0,
            'by_strategy': {}
        }

    buy_signals = [r for r in results if r.signal_type == 'buy']
    sell_signals = [r for r in results if r.signal_type == 'sell']

    unique_tickers = len(set(r.ticker for r in results))
    unique_strategies = len(set(r.strategy for r in results))

    # Calculate average performance for buy signals
    if buy_signals:
        avg_performance = np.mean([
            (r.current_price - r.signal_price) / r.signal_price * 100
            for r in buy_signals
        ])
    else:
        avg_performance = 0.0

    return {
        'total_signals': len(results),
        'unique_tickers': unique_tickers,
        'unique_strategies': unique_strategies,
        'buy_signals': len(buy_signals),
        'sell_signals': len(sell_signals),
        'avg_performance_pct': float(avg_performance),
        'by_strategy': {
            strategy: len(signals)
            for strategy, signals in group_results_by_strategy(results).items()
        }
    }


def export_results_to_dataframe(results: List[ScanResult]) -> pd.DataFrame:
    """
    Export results to pandas DataFrame

    Args:
        results: List of ScanResult objects

    Returns:
        DataFrame with results
    """
    if not results:
        return pd.DataFrame()

    data = [r.to_dict() for r in results]
    df = pd.DataFrame(data)

    # Reorder columns
    column_order = [
        'ticker', 'strategy', 'signal_type', 'signal_date', 'days_ago',
        'signal_price', 'current_price', 'price_change_pct'
    ]

    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]

    return df
