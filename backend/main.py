from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List

from models import BacktestRequest, BacktestResponse, StrategyResult, TradeSignal, OptimizationRequest, OptimizationResponse
from strategies import STRATEGY_MAP, calculate_metrics
from optimizer import optimize_multiple_strategies, generate_optimization_summary

app = FastAPI(title="Stock Analysis API", version="4.0.0")

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
        "message": "Stock Analysis API v4.0 - 200+ Strategies with Entry/Exit Mix & Match",
        "status": "running",
        "total_strategies": len(STRATEGY_MAP),
        "categories": len(set(s['category'] for s in STRATEGY_MAP.values())),
        "features": [
            "Backtesting",
            "Parameter Optimization",
            "Parallel Processing",
            "Entry/Exit Strategy Combinations (12 entries × 14 exits = 168 combinations)"
        ],
        "endpoints": {
            "/api/v1/backtest": "POST - Run backtest for selected strategies",
            "/api/v1/strategies": "GET - List available strategies",
            "/api/v1/optimize": "POST - Optimize strategy parameters"
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
                signals=[TradeSignal(**sig) for sig in trade_signals]
            )
            results.append(result)

        return BacktestResponse(
            ticker=request.ticker,
            startDate=request.startDate,
            endDate=request.endDate,
            results=results,
            price_data=price_data
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
            summary=summary
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
