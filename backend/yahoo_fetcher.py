"""
Alternative data fetcher using direct Yahoo Finance CSV API
Bypasses yfinance library issues while providing the same functionality
"""
import pandas as pd
import requests
from datetime import datetime
import time


def download_yahoo_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download stock data directly from Yahoo Finance CSV API

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format

    Returns:
        DataFrame with OHLCV data
    """
    # Convert dates to timestamps
    start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
    end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())

    # Yahoo Finance download URL
    url = f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}"
    params = {
        'period1': start_ts,
        'period2': end_ts,
        'interval': '1d',
        'events': 'history',
        'includeAdjustedClose': 'true'
    }

    # Add headers to mimic browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse CSV data
        from io import StringIO
        data = pd.read_csv(StringIO(response.text), parse_dates=['Date'], index_col='Date')

        # Rename columns to match yfinance format
        data.columns = [col.replace('Adj Close', 'Adj_Close') for col in data.columns]

        return data

    except Exception as e:
        raise Exception(f"Failed to download data for {ticker}: {str(e)}")


def test_download():
    """Test the download function"""
    print("Testing direct Yahoo Finance data download...")
    print("=" * 60)

    # Test with SPY
    ticker = "SPY"
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = "2023-01-01"

    print(f"Downloading {ticker} from {start_date} to {end_date}...")

    try:
        data = download_yahoo_data(ticker, start_date, end_date)

        print(f"✓ Successfully downloaded {len(data)} days of data")
        print()
        print("First 5 rows:")
        print(data.head())
        print()
        print("Last 5 rows:")
        print(data.tail())
        print()
        print("Data info:")
        print(data.info())

        return data

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


if __name__ == "__main__":
    test_download()
