"""
Data Cache Manager - Caches stock price data to avoid redundant downloads

Caches stock data locally with configurable expiry times.
"""

import os
import pickle
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Default cache directory
CACHE_DIR = Path('/tmp/stock_data_cache')

# Default cache expiry (in hours)
DEFAULT_CACHE_EXPIRY_HOURS = 4  # Refresh every 4 hours during trading day


class DataCache:
    """Manages caching of stock price data"""

    def __init__(self, cache_dir: Optional[str] = None, expiry_hours: int = DEFAULT_CACHE_EXPIRY_HOURS):
        """
        Initialize data cache

        Args:
            cache_dir: Directory for cache files (default: /tmp/stock_data_cache)
            expiry_hours: Cache expiry time in hours (default: 4)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else CACHE_DIR
        self.expiry_hours = expiry_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, ticker: str, period: str) -> Path:
        """Get cache file path for ticker and period"""
        # Sanitize ticker for filename
        safe_ticker = ticker.replace('/', '_').replace('\\', '_')
        filename = f"{safe_ticker}_{period}.pkl"
        return self.cache_dir / filename

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False

        # Check file modification time
        mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        expiry_time = datetime.now() - timedelta(hours=self.expiry_hours)

        return mod_time > expiry_time

    def get(self, ticker: str, period: str = '6mo') -> Optional[pd.DataFrame]:
        """
        Get cached data for ticker

        Args:
            ticker: Stock ticker
            period: Data period

        Returns:
            DataFrame if cached and valid, None otherwise
        """
        cache_path = self._get_cache_path(ticker, period)

        if not self._is_cache_valid(cache_path):
            return None

        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            logger.debug(f"Cache HIT: {ticker} ({period})")
            return data
        except Exception as e:
            logger.debug(f"Cache read error for {ticker}: {e}")
            return None

    def set(self, ticker: str, data: pd.DataFrame, period: str = '6mo'):
        """
        Cache data for ticker

        Args:
            ticker: Stock ticker
            data: DataFrame to cache
            period: Data period
        """
        cache_path = self._get_cache_path(ticker, period)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            logger.debug(f"Cache SET: {ticker} ({period})")
        except Exception as e:
            logger.debug(f"Cache write error for {ticker}: {e}")

    def clear(self, ticker: Optional[str] = None):
        """
        Clear cache for specific ticker or all tickers

        Args:
            ticker: Stock ticker (None to clear all)
        """
        if ticker:
            # Clear specific ticker (all periods)
            safe_ticker = ticker.replace('/', '_').replace('\\', '_')
            pattern = f"{safe_ticker}_*.pkl"
            for cache_file in self.cache_dir.glob(pattern):
                cache_file.unlink()
                logger.info(f"Cleared cache: {cache_file.name}")
        else:
            # Clear all cache files
            count = 0
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
                count += 1
            logger.info(f"Cleared {count} cache files")

    def get_stats(self) -> dict:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)

        # Count valid vs expired
        valid_count = sum(1 for f in cache_files if self._is_cache_valid(f))
        expired_count = len(cache_files) - valid_count

        return {
            'total_files': len(cache_files),
            'valid_files': valid_count,
            'expired_files': expired_count,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir),
            'expiry_hours': self.expiry_hours
        }

    def cleanup_expired(self):
        """Remove expired cache files"""
        count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            if not self._is_cache_valid(cache_file):
                cache_file.unlink()
                count += 1
        logger.info(f"Cleaned up {count} expired cache files")
        return count


# Global cache instance (configurable via environment)
_global_cache = None


def get_cache(expiry_hours: Optional[int] = None) -> DataCache:
    """
    Get global cache instance

    Args:
        expiry_hours: Override default expiry hours

    Returns:
        DataCache instance
    """
    global _global_cache

    if _global_cache is None or (expiry_hours and _global_cache.expiry_hours != expiry_hours):
        # Check for environment variable
        env_expiry = os.environ.get('STOCK_DATA_CACHE_EXPIRY_HOURS')
        if env_expiry:
            expiry_hours = int(env_expiry)
        elif expiry_hours is None:
            expiry_hours = DEFAULT_CACHE_EXPIRY_HOURS

        _global_cache = DataCache(expiry_hours=expiry_hours)

    return _global_cache
