from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List

from models import BacktestRequest, BacktestResponse, StrategyResult, TradeSignal
from strategies import STRATEGY_MAP, calculate_metrics

app = FastAPI(title="Stock Analysis API", version="1.0.0")

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
        "message": "Stock Analysis API v1.0",
        "status": "running",
        "endpoints": {
            "/api/v1/backtest": "POST - Run backtest for selected strategies",
            "/api/v1/strategies": "GET - List available strategies"
        }
    }


@app.get("/api/v1/strategies")
def get_strategies():
    """Get list of available strategies"""
    return {
        "strategies": [
            {
                "id": key,
                "name": value['name'],
                "category": "Trend-Following"
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
        # Download stock data
        ticker = yf.Ticker(request.ticker)
        data = ticker.history(start=request.startDate, end=request.endDate)

        if data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for ticker {request.ticker} in the specified date range"
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
