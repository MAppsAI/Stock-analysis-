from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List

from models import (
    BacktestRequest, BacktestResponse, StrategyResult, TradeSignal, EquityPoint,
    OptimizationRequest, OptimizationResponse,
    SaveHistoryRequest, SaveHistoryResponse, HistoryListResponse, HistoryDetail,
    PortfolioBacktestRequest, PortfolioBacktestResponse, PortfolioStrategyResult,
    PortfolioMetrics, AssetMetrics, WeightSnapshot
)
from strategies import STRATEGY_MAP, calculate_metrics, calculate_buy_hold_metrics
from optimizer import optimize_multiple_strategies, generate_optimization_summary
from database import db
from portfolio_strategies import PORTFOLIO_STRATEGY_MAP
from portfolio import (
    PortfolioEngine, calculate_portfolio_returns, create_equity_curve
)

app = FastAPI(title="Stock Analysis API", version="4.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "Stock Analysis API v4.1 - 200+ Strategies with Hyperparameter Optimization",
        "status": "running",
        "total_strategies": len(STRATEGY_MAP),
        "categories": len(set(s['category'] for s in STRATEGY_MAP.values())),
        "features": [
            "Backtesting",
            "Hyperparameter Optimization (Original + Combined Strategies)",
            "Parallel Processing",
            "Entry/Exit Strategy Combinations (12 entries × 14 exits = 168 combinations)",
            "Combined Strategy Optimization (Entry params × Exit params)"
        ],
        "endpoints": {
            "/api/v1/backtest": "POST - Run backtest for selected strategies",
            "/api/v1/strategies": "GET - List available strategies",
            "/api/v1/optimize": "POST - Optimize strategy parameters (supports combined strategies)"
        },
        "optimization": {
            "supported": "All 203 strategies (35 original + 168 combined)",
            "example": "Optimize 'combo_rsi_oversold_entry_trailing_stop_exit' to find best RSI threshold and stop %"
        }
    }


@app.get("/api/v1/strategies")
def get_strategies():
    """Get list of available strategies with their categories"""
    return {
        "strategies": [
            {
                "id": key,
                "name": value['name'],
                "category": value['category']
            }
            for key, value in STRATEGY_MAP.items()
        ]
    }


@app.post("/api/v1/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run backtest for selected strategies on a given ticker and date range
    """
    try:
        # Download stock data using yf.download (more reliable than Ticker.history)
        data = yf.download(
            request.ticker,
            start=request.startDate,
            end=request.endDate,
            progress=False,
            auto_adjust=False
        )

        # Handle multi-level columns from yf.download
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for ticker {request.ticker} in the specified date range. "
                       f"This could be due to: invalid ticker, no trading days in range, or Yahoo Finance access issues."
            )

        # Prepare price data for charting
        price_data = []
        for idx, row in data.iterrows():
            price_data.append({
                'date': idx.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })

        # Calculate buy and hold metrics (baseline for comparison)
        buy_hold_data = data.copy()
        buy_hold_metrics = calculate_buy_hold_metrics(buy_hold_data)
        buy_hold_result = StrategyResult(
            strategy="Buy & Hold",
            total_return=buy_hold_metrics['total_return'],
            win_rate=buy_hold_metrics['win_rate'],
            max_drawdown=buy_hold_metrics['max_drawdown'],
            sharpe_ratio=buy_hold_metrics['sharpe_ratio'],
            num_trades=buy_hold_metrics['num_trades'],
            signals=[],  # No trade signals for buy and hold
            equity_curve=[EquityPoint(**point) for point in buy_hold_metrics['equity_curve']]
        )

        # Run backtests for each requested strategy
        results = []
        for strategy_id in request.strategies:
            if strategy_id not in STRATEGY_MAP:
                continue

            # Create a copy of data for this strategy
            strategy_data = data.copy()

            # Get strategy function
            strategy_func = STRATEGY_MAP[strategy_id]['func']

            # Run strategy
            signals, trade_signals = strategy_func(strategy_data)

            # Calculate metrics
            metrics = calculate_metrics(strategy_data, signals)

            # Create result
            result = StrategyResult(
                strategy=STRATEGY_MAP[strategy_id]['name'],
                total_return=metrics['total_return'],
                win_rate=metrics['win_rate'],
                max_drawdown=metrics['max_drawdown'],
                sharpe_ratio=metrics['sharpe_ratio'],
                num_trades=metrics['num_trades'],
                signals=[TradeSignal(**sig) for sig in trade_signals],
                equity_curve=[EquityPoint(**point) for point in metrics['equity_curve']]
            )
            results.append(result)

        return BacktestResponse(
            ticker=request.ticker,
            startDate=request.startDate,
            endDate=request.endDate,
            results=results,
            price_data=price_data,
            buy_hold_result=buy_hold_result
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        error_msg = str(e)
        # Check for common Yahoo Finance access issues
        if "403" in error_msg or "Forbidden" in error_msg or "Access denied" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Yahoo Finance access denied. This may be due to network restrictions, "
                       "rate limiting, or firewall blocks. Please try again later or use a different network."
            )
        raise HTTPException(status_code=500, detail=f"Backtest error: {error_msg}")


@app.post("/api/v1/optimize", response_model=OptimizationResponse)
async def optimize_strategies(request: OptimizationRequest):
    """
    Optimize strategy parameters for selected strategies in parallel
    """
    try:
        # Download stock data
        data = yf.download(
            request.ticker,
            start=request.startDate,
            end=request.endDate,
            progress=False,
            auto_adjust=False
        )

        # Handle multi-level columns
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for ticker {request.ticker} in the specified date range."
            )

        # Prepare price data for charting
        price_data = []
        for idx, row in data.iterrows():
            price_data.append({
                'date': idx.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })

        # Run parallel optimization
        optimization_results = optimize_multiple_strategies(
            strategies=request.strategies,
            data=data,
            max_workers=4
        )

        # Generate summary
        summary = generate_optimization_summary(optimization_results)

        return OptimizationResponse(
            ticker=request.ticker,
            startDate=request.startDate,
            endDate=request.endDate,
            optimization_results=optimization_results,
            summary=summary,
            price_data=price_data
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg or "Access denied" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Yahoo Finance access denied. This may be due to network restrictions."
            )
        raise HTTPException(status_code=500, detail=f"Optimization error: {error_msg}")


# =============================================================================
# PORTFOLIO (MULTI-ASSET) ENDPOINTS
# =============================================================================

@app.get("/api/v1/portfolio/strategies")
def get_portfolio_strategies():
    """Get list of available portfolio (multi-asset) strategies"""
    return {
        "strategies": [
            {
                "id": key,
                "name": value['name'],
                "category": value['category'],
                "description": value.get('description', ''),
                "parameters": value.get('parameters', {})
            }
            for key, value in PORTFOLIO_STRATEGY_MAP.items()
        ]
    }


@app.post("/api/v1/portfolio/backtest", response_model=PortfolioBacktestResponse)
async def run_portfolio_backtest(request: PortfolioBacktestRequest):
    """
    Run backtest for multi-asset portfolio strategies
    """
    try:
        # Download data for all tickers
        asset_data = {}
        price_data = {}

        for ticker in request.tickers:
            data = yf.download(
                ticker,
                start=request.startDate,
                end=request.endDate,
                progress=False,
                auto_adjust=False
            )

            # Handle multi-level columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            if data.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for ticker {ticker} in the specified date range."
                )

            asset_data[ticker] = data

            # Prepare price data for charting
            price_data[ticker] = []
            for idx, row in data.iterrows():
                price_data[ticker].append({
                    'date': idx.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })

        # Run portfolio strategies
        results = []

        for strategy_id in request.strategies:
            if strategy_id not in PORTFOLIO_STRATEGY_MAP:
                continue

            strategy_func = PORTFOLIO_STRATEGY_MAP[strategy_id]['func']

            # Run strategy to get signals and weights
            asset_signals, weights = strategy_func(asset_data)

            # Initialize portfolio engine
            engine = PortfolioEngine(
                tickers=request.tickers,
                asset_data=asset_data,
                allocation_method=request.allocation_method,
                custom_weights=request.custom_weights or weights,
                rebalancing=request.rebalancing,
                rebalance_threshold=request.rebalance_threshold,
                transaction_cost=request.transaction_cost
            )

            # Calculate portfolio returns
            portfolio_returns, weights_timeline, rebalance_dates = calculate_portfolio_returns(
                asset_data=asset_data,
                asset_signals=asset_signals,
                weights=engine.initial_weights,
                rebalancing=request.rebalancing,
                rebalance_threshold=request.rebalance_threshold,
                transaction_cost=request.transaction_cost
            )

            # Calculate asset-level returns for metrics
            asset_returns = {}
            for ticker in request.tickers:
                returns = asset_data[ticker]['Close'].pct_change().fillna(0)
                asset_returns[ticker] = returns

            # Calculate portfolio metrics
            portfolio_metrics_dict = engine.calculate_portfolio_metrics(
                portfolio_returns=portfolio_returns,
                asset_returns=asset_returns,
                weights_timeline=weights_timeline,
                rebalance_dates=rebalance_dates
            )

            # Calculate asset metrics
            asset_metrics_dict = engine.calculate_asset_metrics(
                asset_returns=asset_returns,
                asset_signals=asset_signals
            )

            # Create equity curve
            equity_curve = create_equity_curve(portfolio_returns)

            # Format results
            portfolio_metrics = PortfolioMetrics(**portfolio_metrics_dict)

            asset_metrics_list = [
                AssetMetrics(ticker=ticker, **metrics)
                for ticker, metrics in asset_metrics_dict.items()
            ]

            weights_timeline_list = [
                WeightSnapshot(**snapshot) for snapshot in weights_timeline
            ]

            result = PortfolioStrategyResult(
                strategy=PORTFOLIO_STRATEGY_MAP[strategy_id]['name'],
                portfolio_metrics=portfolio_metrics,
                asset_metrics=asset_metrics_list,
                equity_curve=[EquityPoint(**point) for point in equity_curve],
                weights_timeline=weights_timeline_list
            )

            results.append(result)

        # Calculate equal-weight buy-and-hold baseline
        buy_hold_signals = {ticker: pd.Series([1] * len(asset_data[ticker]),
                                              index=asset_data[ticker].index)
                           for ticker in request.tickers}
        buy_hold_weights = {ticker: 1.0 / len(request.tickers) for ticker in request.tickers}

        engine = PortfolioEngine(
            tickers=request.tickers,
            asset_data=asset_data,
            allocation_method='equal'
        )

        portfolio_returns, weights_timeline, rebalance_dates = calculate_portfolio_returns(
            asset_data=asset_data,
            asset_signals=buy_hold_signals,
            weights=buy_hold_weights,
            rebalancing='none'
        )

        asset_returns = {ticker: asset_data[ticker]['Close'].pct_change().fillna(0)
                        for ticker in request.tickers}

        buy_hold_metrics_dict = engine.calculate_portfolio_metrics(
            portfolio_returns=portfolio_returns,
            asset_returns=asset_returns,
            weights_timeline=weights_timeline,
            rebalance_dates=rebalance_dates
        )

        buy_hold_asset_metrics = engine.calculate_asset_metrics(
            asset_returns=asset_returns,
            asset_signals=buy_hold_signals
        )

        buy_hold_result = PortfolioStrategyResult(
            strategy="Equal-Weight Buy & Hold",
            portfolio_metrics=PortfolioMetrics(**buy_hold_metrics_dict),
            asset_metrics=[AssetMetrics(ticker=ticker, **metrics)
                          for ticker, metrics in buy_hold_asset_metrics.items()],
            equity_curve=[EquityPoint(**point) for point in create_equity_curve(portfolio_returns)],
            weights_timeline=[WeightSnapshot(**s) for s in weights_timeline]
        )

        return PortfolioBacktestResponse(
            tickers=request.tickers,
            startDate=request.startDate,
            endDate=request.endDate,
            results=results,
            price_data=price_data,
            buy_hold_result=buy_hold_result
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg or "Access denied" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Yahoo Finance access denied. Please try again later."
            )
        raise HTTPException(status_code=500, detail=f"Portfolio backtest error: {error_msg}")


@app.post("/api/v1/portfolio/correlation")
async def calculate_correlation(request: PortfolioBacktestRequest):
    """
    Calculate correlation matrix for a set of assets
    """
    try:
        # Download data for all tickers
        asset_data = {}

        for ticker in request.tickers:
            data = yf.download(
                ticker,
                start=request.startDate,
                end=request.endDate,
                progress=False,
                auto_adjust=False
            )

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            if data.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for ticker {ticker}"
                )

            asset_data[ticker] = data

        # Calculate returns
        returns_df = pd.DataFrame({
            ticker: data['Close'].pct_change()
            for ticker, data in asset_data.items()
        }).dropna()

        # Calculate correlation and covariance
        correlation = returns_df.corr().to_dict()
        covariance = returns_df.cov().to_dict()

        # Calculate volatilities
        volatilities = {ticker: float(returns_df[ticker].std() * (252 ** 0.5))
                       for ticker in request.tickers}

        return {
            "tickers": request.tickers,
            "correlation_matrix": correlation,
            "covariance_matrix": covariance,
            "volatilities": volatilities,
            "date_range": {
                "start": request.startDate,
                "end": request.endDate
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correlation calculation error: {str(e)}")


# =============================================================================
# History Management Endpoints
# =============================================================================

@app.post("/api/v1/history", response_model=SaveHistoryResponse)
async def save_history(request: SaveHistoryRequest):
    """
    Save a backtest or optimization result to history
    """
    try:
        if request.run_type == "backtest":
            history_id = db.save_backtest(
                ticker=request.ticker,
                start_date=request.start_date,
                end_date=request.end_date,
                results_data=request.results_data,
                title=request.title
            )
        elif request.run_type == "optimization":
            history_id = db.save_optimization(
                ticker=request.ticker,
                start_date=request.start_date,
                end_date=request.end_date,
                results_data=request.results_data,
                title=request.title
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid run_type: {request.run_type}. Must be 'backtest' or 'optimization'"
            )

        return SaveHistoryResponse(
            id=history_id,
            message=f"{request.run_type.capitalize()} saved successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving history: {str(e)}")


@app.get("/api/v1/history", response_model=HistoryListResponse)
async def get_history(ticker: str = None, limit: int = 100, offset: int = 0):
    """
    Get all history entries, optionally filtered by ticker search
    """
    try:
        items = db.get_all_history(ticker_filter=ticker, limit=limit, offset=offset)
        total_count = db.get_history_count(ticker_filter=ticker)

        return HistoryListResponse(
            total_count=total_count,
            items=items
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@app.get("/api/v1/history/{history_id}", response_model=HistoryDetail)
async def get_history_by_id(history_id: int):
    """
    Get a specific history entry by ID, including full results data
    """
    try:
        history = db.get_history_by_id(history_id)

        if history is None:
            raise HTTPException(
                status_code=404,
                detail=f"History entry with ID {history_id} not found"
            )

        return history

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@app.delete("/api/v1/history/{history_id}")
async def delete_history(history_id: int):
    """
    Delete a history entry by ID
    """
    try:
        deleted = db.delete_history(history_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"History entry with ID {history_id} not found"
            )

        return {"message": f"History entry {history_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting history: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
