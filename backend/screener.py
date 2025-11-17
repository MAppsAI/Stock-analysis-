"""
Minervini Screener - Trend Template and Fundamental Filters

Implementation of Mark Minervini's SEPA screening methodology:
- Trend Template (8 technical criteria for Stage 2 identification)
- Fundamental filters (EPS growth, sales growth, margin expansion)
- Industry/sector leadership analysis
- Integration with finvizfinance for screening
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Optional imports - gracefully handle missing dependencies
try:
    from finvizfinance.screener.overview import Overview
    from finvizfinance.quote import finvizfinance as fvf
    HAS_FINVIZ = True
except ImportError:
    logger.warning("finvizfinance not available - screening features will be limited")
    HAS_FINVIZ = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    logger.warning("yfinance not available - validation features will be limited")
    HAS_YFINANCE = False


def apply_trend_template(data: pd.DataFrame, rs_rating: Optional[float] = None) -> bool:
    """
    Apply Mark Minervini's Trend Template - 8 criteria for Stage 2 uptrend

    The Trend Template is a quantifiable checklist to confirm a stock is in
    a valid Stage 2 uptrend (accumulation phase).

    8 Criteria:
    1. Price > 150-day SMA AND Price > 200-day SMA
    2. 150-day SMA > 200-day SMA
    3. 200-day SMA trending up for at least 1 month
    4. 50-day SMA > 150-day SMA AND 50-day SMA > 200-day SMA
    5. Price > 50-day SMA
    6. Price >= 30% above 52-week low
    7. Price within 25% of 52-week high (Price >= 75% of 52W high)
    8. RS Rating > 70 (if provided)

    Args:
        data: OHLCV DataFrame with indicators calculated
        rs_rating: Optional RS rating value (1-99 percentile)

    Returns:
        Boolean indicating if stock passes Trend Template
    """
    # Need at least 200 days of data
    if len(data) < 200:
        return False

    # Get most recent row
    current = data.iloc[-1]

    # Get 200-day SMA from 22 trading days ago (~1 month)
    if len(data) >= 222:
        sma_200_prev_month = data['SMA_200'].iloc[-22]
    else:
        sma_200_prev_month = data['SMA_200'].iloc[0]

    try:
        # Criterion 1: Price > 150 SMA AND Price > 200 SMA
        c1 = (current['Close'] > current['SMA_150']) and (current['Close'] > current['SMA_200'])

        # Criterion 2: 150 SMA > 200 SMA
        c2 = current['SMA_150'] > current['SMA_200']

        # Criterion 3: 200 SMA trending up for at least 1 month
        c3 = current['SMA_200'] > sma_200_prev_month

        # Criterion 4: 50 SMA > 150 SMA AND 50 SMA > 200 SMA
        c4 = (current['SMA_50'] > current['SMA_150']) and (current['SMA_50'] > current['SMA_200'])

        # Criterion 5: Price > 50 SMA
        c5 = current['Close'] > current['SMA_50']

        # Criterion 6: Price >= 30% above 52-week low
        c6 = current['Close'] >= (current['52W_Low'] * 1.30)

        # Criterion 7: Price within 25% of 52-week high
        c7 = current['Close'] >= (current['52W_High'] * 0.75)

        # Criterion 8: RS Rating > 70 (if provided)
        c8 = True if rs_rating is None else rs_rating > 70

        # All criteria must be True
        passes = c1 and c2 and c3 and c4 and c5 and c6 and c7 and c8

        if not passes:
            logger.debug(f"Trend Template failed: c1={c1}, c2={c2}, c3={c3}, c4={c4}, "
                        f"c5={c5}, c6={c6}, c7={c7}, c8={c8}")

        return passes

    except (KeyError, IndexError) as e:
        logger.warning(f"Error applying Trend Template: {e}")
        return False


def check_fundamental_criteria(ticker: str) -> Dict[str, bool]:
    """
    Check fundamental growth criteria for superperformance

    Uses finvizfinance to fetch fundamental data and validate:
    - Annual EPS growth >= 25% (last 3 years)
    - Quarterly EPS growth >= 25% YoY
    - EPS acceleration (current Q > previous Q)
    - Quarterly sales growth >= 20% YoY
    - Sales acceleration
    - Expanding profit margins

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict of criterion_name -> passed (bool)
    """
    results = {
        'eps_annual_growth': False,
        'eps_quarterly_growth': False,
        'eps_acceleration': False,
        'sales_growth': False,
        'sales_acceleration': False,
        'margin_expansion': False
    }

    if not HAS_FINVIZ:
        logger.warning("finvizfinance not available - cannot check fundamentals")
        return results

    try:
        # Fetch fundamental data using finviz
        stock = fvf(ticker)
        fundamentals = stock.ticker_fundament()

        # Extract key metrics (if available)
        eps_growth_5y = fundamentals.get('EPS growth past 5 years', None)
        eps_growth_this_year = fundamentals.get('EPS growth this year', None)
        eps_growth_next_year = fundamentals.get('EPS growth next year', None)
        sales_growth_qoq = fundamentals.get('Sales Q/Q', None)
        sales_growth_past_5y = fundamentals.get('Sales growth past 5 years', None)
        profit_margin = fundamentals.get('Profit Margin', None)

        # Parse percentage strings (e.g., "35.60%" -> 35.6)
        def parse_pct(value):
            if value and isinstance(value, str) and '%' in value:
                return float(value.replace('%', ''))
            return None

        eps_growth_5y = parse_pct(eps_growth_5y)
        eps_growth_this_year = parse_pct(eps_growth_this_year)
        eps_growth_next_year = parse_pct(eps_growth_next_year)
        sales_growth_qoq = parse_pct(sales_growth_qoq)
        sales_growth_past_5y = parse_pct(sales_growth_past_5y)
        profit_margin = parse_pct(profit_margin)

        # Check EPS annual growth >= 25%
        if eps_growth_5y and eps_growth_5y >= 25:
            results['eps_annual_growth'] = True

        # Check EPS quarterly growth >= 25%
        if eps_growth_this_year and eps_growth_this_year >= 25:
            results['eps_quarterly_growth'] = True

        # Check EPS acceleration (simplified: next year > this year)
        if eps_growth_this_year and eps_growth_next_year:
            if eps_growth_next_year > eps_growth_this_year:
                results['eps_acceleration'] = True

        # Check sales growth >= 20%
        if sales_growth_past_5y and sales_growth_past_5y >= 20:
            results['sales_growth'] = True

        # Check sales acceleration (Q/Q positive)
        if sales_growth_qoq and sales_growth_qoq > 0:
            results['sales_acceleration'] = True

        # Check margin expansion (simplified: profit margin > 15%)
        if profit_margin and profit_margin > 15:
            results['margin_expansion'] = True

    except Exception as e:
        logger.warning(f"Error fetching fundamentals for {ticker}: {e}")

    return results


def screen_stocks_finviz(
    filters: Dict[str, any],
    max_results: int = 100
) -> List[str]:
    """
    Screen stocks using finvizfinance

    Args:
        filters: Dict of finviz filter criteria
        max_results: Maximum number of results to return

    Returns:
        List of ticker symbols
    """
    if not HAS_FINVIZ:
        logger.warning("finvizfinance not available - cannot screen stocks")
        return []

    try:
        foverview = Overview()

        # Apply filters
        foverview.set_filter(filters_dict=filters)

        # Get screener results
        df = foverview.screener_view()

        if df is not None and not df.empty:
            tickers = df['Ticker'].tolist()[:max_results]
            logger.info(f"Finviz screener returned {len(tickers)} stocks")
            return tickers
        else:
            logger.warning("Finviz screener returned no results")
            return []

    except Exception as e:
        logger.error(f"Error in finviz screening: {e}")
        return []


def screen_minervini_candidates(
    min_price: float = 5.0,
    min_volume: int = 500000,
    market_cap: str = 'Small Cap',
    apply_fundamentals: bool = True,
    max_results: int = 50
) -> List[str]:
    """
    Screen for Minervini-style candidates using finviz

    Applies basic technical and fundamental filters to find potential
    Stage 2 stocks.

    Args:
        min_price: Minimum stock price
        min_volume: Minimum average volume
        market_cap: Market cap filter (e.g., 'Small Cap', 'Mid Cap', 'Large Cap')
        apply_fundamentals: Whether to apply fundamental filters
        max_results: Maximum number of results

    Returns:
        List of ticker symbols
    """
    # Build finviz filter dict
    filters = {
        'Price': f'Over ${min_price}',
        'Average Volume': f'Over {min_volume/1000000}M',
    }

    # Add market cap filter if specified
    if market_cap:
        filters['Market Cap'] = market_cap

    # Add technical filters
    filters['50-Day Simple Moving Average'] = 'Price above SMA50'
    filters['200-Day Simple Moving Average'] = 'Price above SMA200'
    filters['52-Week High/Low'] = '0-20% below High'  # Within 20% of 52W high

    # Add fundamental filters if enabled
    if apply_fundamentals:
        filters['EPS growth this year'] = 'Over 25%'
        filters['Sales growth past 5 years'] = 'Positive (>0%)'

    logger.info(f"Screening with filters: {filters}")

    # Run screener
    candidates = screen_stocks_finviz(filters, max_results)

    return candidates


def validate_trend_template_batch(
    tickers: List[str],
    period: str = '1y'
) -> Dict[str, bool]:
    """
    Validate Trend Template for a batch of tickers

    Args:
        tickers: List of ticker symbols
        period: Data period to fetch ('6mo', '1y', '2y')

    Returns:
        Dict of ticker -> passes_template (bool)
    """
    if not HAS_YFINANCE:
        logger.warning("yfinance not available - cannot validate trend template")
        return {}

    results = {}

    for ticker in tickers:
        try:
            # Fetch data
            data = yf.download(ticker, period=period, progress=False)

            if data.empty:
                results[ticker] = False
                continue

            # Handle multi-level columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # Calculate indicators
            from minervini_utils import calculate_minervini_indicators

            data = calculate_minervini_indicators(data)

            # Apply Trend Template
            passes = apply_trend_template(data)

            results[ticker] = passes

            if passes:
                logger.info(f"{ticker} PASSES Trend Template")
            else:
                logger.debug(f"{ticker} fails Trend Template")

        except Exception as e:
            logger.error(f"Error validating {ticker}: {e}")
            results[ticker] = False

    return results


def run_full_screening_pipeline(
    min_price: float = 5.0,
    min_volume: int = 500000,
    apply_fundamentals: bool = True,
    validate_template: bool = True,
    max_candidates: int = 50
) -> List[str]:
    """
    Run the complete Minervini screening pipeline

    Steps:
    1. Screen candidates using finviz (basic filters)
    2. Validate Trend Template (8 criteria)
    3. Optionally check fundamental criteria

    Args:
        min_price: Minimum stock price
        min_volume: Minimum average volume
        apply_fundamentals: Apply fundamental filters in initial screen
        validate_template: Validate full Trend Template (downloads data)
        max_candidates: Maximum number of final candidates

    Returns:
        List of ticker symbols that pass all filters
    """
    logger.info("=" * 60)
    logger.info("MINERVINI SCREENING PIPELINE")
    logger.info("=" * 60)

    # Step 1: Initial screen with finviz
    logger.info("\nStep 1: Running finviz screener...")
    candidates = screen_minervini_candidates(
        min_price=min_price,
        min_volume=min_volume,
        apply_fundamentals=apply_fundamentals,
        max_results=max_candidates * 3  # Get more initially for validation
    )

    logger.info(f"Found {len(candidates)} initial candidates")

    if not candidates:
        logger.warning("No candidates found in initial screen")
        return []

    # Step 2: Validate Trend Template (requires downloading data)
    if validate_template:
        logger.info("\nStep 2: Validating Trend Template...")
        validation_results = validate_trend_template_batch(candidates)

        # Filter to only passing stocks
        validated_candidates = [
            ticker for ticker, passes in validation_results.items()
            if passes
        ]

        logger.info(f"{len(validated_candidates)} candidates pass Trend Template")

        final_candidates = validated_candidates[:max_candidates]
    else:
        final_candidates = candidates[:max_candidates]

    logger.info(f"\nFinal candidate list ({len(final_candidates)} stocks):")
    for ticker in final_candidates:
        logger.info(f"  - {ticker}")

    return final_candidates


def get_industry_leaders(
    universe: List[str],
    top_n_industries: int = 5
) -> Dict[str, List[str]]:
    """
    Identify leading industries and their top stocks

    Groups stocks by industry and ranks industries by median RS rating.

    Args:
        universe: List of ticker symbols
        top_n_industries: Number of top industries to return

    Returns:
        Dict of industry_name -> list of tickers
    """
    if not HAS_FINVIZ:
        logger.warning("finvizfinance not available - cannot get industry leaders")
        return {}

    industry_stocks = {}

    for ticker in universe:
        try:
            stock = fvf(ticker)
            fundamentals = stock.ticker_fundament()
            industry = fundamentals.get('Industry', 'Unknown')

            if industry not in industry_stocks:
                industry_stocks[industry] = []

            industry_stocks[industry].append(ticker)

        except Exception as e:
            logger.warning(f"Error getting industry for {ticker}: {e}")
            continue

    # Sort industries by number of stocks (proxy for strength)
    sorted_industries = sorted(
        industry_stocks.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )

    # Return top N industries
    result = dict(sorted_industries[:top_n_industries])

    logger.info(f"Top {top_n_industries} industries:")
    for industry, stocks in result.items():
        logger.info(f"  {industry}: {len(stocks)} stocks")

    return result
