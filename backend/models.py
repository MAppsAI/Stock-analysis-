from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class BacktestRequest(BaseModel):
    ticker: str
    startDate: str
    endDate: str
    strategies: List[str]


class TradeSignal(BaseModel):
    date: str
    price: float
    type: str  # "buy" or "sell"


class StrategyResult(BaseModel):
    strategy: str
    total_return: float
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    num_trades: int
    signals: List[TradeSignal]


class BacktestResponse(BaseModel):
    ticker: str
    startDate: str
    endDate: str
    results: List[StrategyResult]
    price_data: List[dict]  # OHLC data for charting
