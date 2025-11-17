"""
Stock Universe Management

Provides stock lists for different market universes:
- S&P 500
- NASDAQ 100
- Russell 2000
- Custom watchlists

Includes caching to avoid repeated API calls.
"""

import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

# Cache file locations
CACHE_DIR = "/tmp/stock_universe_cache"
CACHE_EXPIRY_DAYS = 7

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


def get_sp500_tickers() -> List[str]:
    """
    Get S&P 500 stock tickers

    Returns:
        List of ticker symbols
    """
    cache_file = os.path.join(CACHE_DIR, "sp500.json")

    # Check cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                cache_date = datetime.fromisoformat(cached['date'])

                if datetime.now() - cache_date < timedelta(days=CACHE_EXPIRY_DAYS):
                    logger.info(f"Using cached S&P 500 list ({len(cached['tickers'])} stocks)")
                    return cached['tickers']
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")

    # Fetch from Wikipedia
    try:
        logger.info("Fetching S&P 500 list from Wikipedia...")
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df['Symbol'].str.replace('.', '-').tolist()

        # Cache the results
        with open(cache_file, 'w') as f:
            json.dump({
                'date': datetime.now().isoformat(),
                'tickers': tickers
            }, f)

        logger.info(f"Fetched {len(tickers)} S&P 500 stocks")
        return tickers
    except Exception as e:
        logger.error(f"Error fetching S&P 500: {e}")
        return []


def get_nasdaq100_tickers() -> List[str]:
    """
    Get NASDAQ 100 stock tickers

    Returns:
        List of ticker symbols
    """
    cache_file = os.path.join(CACHE_DIR, "nasdaq100.json")

    # Check cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                cache_date = datetime.fromisoformat(cached['date'])

                if datetime.now() - cache_date < timedelta(days=CACHE_EXPIRY_DAYS):
                    logger.info(f"Using cached NASDAQ 100 list ({len(cached['tickers'])} stocks)")
                    return cached['tickers']
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")

    # Fetch from Wikipedia
    try:
        logger.info("Fetching NASDAQ 100 list from Wikipedia...")
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tables = pd.read_html(url)
        df = tables[4]  # The component table is usually the 5th table
        tickers = df['Ticker'].tolist()

        # Cache the results
        with open(cache_file, 'w') as f:
            json.dump({
                'date': datetime.now().isoformat(),
                'tickers': tickers
            }, f)

        logger.info(f"Fetched {len(tickers)} NASDAQ 100 stocks")
        return tickers
    except Exception as e:
        logger.error(f"Error fetching NASDAQ 100: {e}")
        # Fallback to common NASDAQ 100 stocks
        return [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA',
            'AVGO', 'COST', 'NFLX', 'AMD', 'PEP', 'ADBE', 'CSCO', 'TMUS',
            'INTC', 'CMCSA', 'QCOM', 'TXN'
        ]


def get_russell2000_tickers() -> List[str]:
    """
    Get Russell 2000 stock tickers

    Note: Full Russell 2000 list requires paid data.
    This returns a representative subset.

    Returns:
        List of ticker symbols
    """
    cache_file = os.path.join(CACHE_DIR, "russell2000.json")

    # Check cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                cache_date = datetime.fromisoformat(cached['date'])

                if datetime.now() - cache_date < timedelta(days=CACHE_EXPIRY_DAYS):
                    logger.info(f"Using cached Russell 2000 list ({len(cached['tickers'])} stocks)")
                    return cached['tickers']
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")

    # Try to fetch from iShares IWM ETF holdings
    try:
        logger.info("Fetching Russell 2000 representative list...")
        # This is a simplified approach - in production, use a proper data provider
        url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf"

        # For now, return a representative subset of small-cap stocks
        # In production, integrate with a Russell 2000 data provider
        tickers = [
            'SIRI', 'HL', 'PLUG', 'AMC', 'UPST', 'OPEN', 'BBBY', 'FUBO',
            'RIDE', 'GOEV', 'RIDE', 'WKHS', 'HYLN', 'BLNK', 'CHPT', 'LCID',
            'RIVN', 'NIO', 'XPEV', 'LI'
        ]

        logger.warning("Using representative Russell 2000 subset (20 stocks). "
                      "Full list requires paid data provider.")

        return tickers
    except Exception as e:
        logger.error(f"Error fetching Russell 2000: {e}")
        return []


def get_universe_tickers(universe: str) -> List[str]:
    """
    Get tickers for a specified universe

    Args:
        universe: One of 'sp500', 'nasdaq100', 'russell2000', 'all'

    Returns:
        List of ticker symbols
    """
    universe = universe.lower()

    if universe == 'sp500':
        return get_sp500_tickers()
    elif universe == 'nasdaq100':
        return get_nasdaq100_tickers()
    elif universe == 'russell2000':
        return get_russell2000_tickers()
    elif universe == 'all':
        # Combine all universes and deduplicate
        all_tickers = set()
        all_tickers.update(get_sp500_tickers())
        all_tickers.update(get_nasdaq100_tickers())
        all_tickers.update(get_russell2000_tickers())
        return sorted(list(all_tickers))
    else:
        logger.error(f"Unknown universe: {universe}")
        return []


def get_available_universes() -> Dict[str, Dict]:
    """
    Get information about available stock universes

    Returns:
        Dict with universe info
    """
    return {
        'sp500': {
            'name': 'S&P 500',
            'description': 'Large-cap US stocks',
            'approximate_count': 500
        },
        'nasdaq100': {
            'name': 'NASDAQ 100',
            'description': 'Top 100 NASDAQ stocks',
            'approximate_count': 100
        },
        'russell2000': {
            'name': 'Russell 2000',
            'description': 'Small-cap US stocks (representative subset)',
            'approximate_count': 20,
            'note': 'Full list requires paid data provider'
        },
        'all': {
            'name': 'All Universes Combined',
            'description': 'S&P 500 + NASDAQ 100 + Russell 2000',
            'approximate_count': 600
        }
    }


def validate_ticker_list(tickers: List[str], max_invalid: int = 50) -> List[str]:
    """
    Validate and clean ticker list

    Removes:
    - Duplicates
    - Invalid characters
    - Known problematic tickers

    Args:
        tickers: List of ticker symbols
        max_invalid: Maximum number of invalid tickers to tolerate

    Returns:
        Cleaned list of tickers
    """
    # Remove duplicates
    tickers = list(set(tickers))

    # Remove tickers with invalid characters
    valid_tickers = []
    for ticker in tickers:
        if ticker and ticker.replace('-', '').replace('.', '').isalnum():
            valid_tickers.append(ticker.upper())

    removed_count = len(tickers) - len(valid_tickers)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} invalid tickers")

    if removed_count > max_invalid:
        logger.warning(f"Too many invalid tickers removed: {removed_count} > {max_invalid}")

    return valid_tickers


def get_sector_leaders(sector: str, universe: str = 'sp500') -> List[str]:
    """
    Get leading stocks in a specific sector

    Args:
        sector: Sector name (e.g., 'Technology', 'Healthcare')
        universe: Stock universe to search

    Returns:
        List of tickers in that sector
    """
    # This would require sector classification data
    # For now, return empty list
    logger.warning("Sector filtering requires additional data provider")
    return []
