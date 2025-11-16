from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class BacktestRequest(BaseModel):
    ticker: str
    startDate: str
    endDate: str
    strategies: List[str]


class OptimizationRequest(BaseModel):
    ticker: str
    startDate: str
    endDate: str
    strategies: List[str]  # Strategy types to optimize (e.g., ['sma_cross', 'rsi', 'macd'])


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


class OptimizationResult(BaseModel):
    strategy_type: str
    status: str
    best_params: Optional[Dict[str, Any]] = None
    best_score: Optional[float] = None
    best_metrics: Optional[Dict[str, Any]] = None
    total_tested: Optional[int] = None
    all_results: Optional[List[Dict[str, Any]]] = None
    param_ranges: Optional[Dict[str, List]] = None
    message: Optional[str] = None


class OptimizationResponse(BaseModel):
    ticker: str
    startDate: str
    endDate: str
    optimization_results: Dict[str, Any]
    summary: Dict[str, Any]
    price_data: List[dict]  # OHLC data for charting (same as BacktestResponse)


class HistorySummary(BaseModel):
    """Summary information for a history entry (list view)."""
    id: int
    ticker: str
    start_date: str
    end_date: str
    run_type: str  # "backtest" or "optimization"
    created_at: str
    title: str
    summary_metrics: Optional[Dict[str, Any]] = None


class HistoryDetail(BaseModel):
    """Complete history entry with full results data."""
    id: int
    ticker: str
    start_date: str
    end_date: str
    run_type: str
    created_at: str
    title: str
    summary_metrics: Optional[Dict[str, Any]] = None
    results_data: Dict[str, Any]


class SaveHistoryRequest(BaseModel):
    """Request to save a history entry."""
    ticker: str
    start_date: str
    end_date: str
    run_type: str  # "backtest" or "optimization"
    results_data: Dict[str, Any]
    title: Optional[str] = None


class SaveHistoryResponse(BaseModel):
    """Response after saving a history entry."""
    id: int
    message: str


class HistoryListResponse(BaseModel):
    """Response for listing history entries."""
    total_count: int
    items: List[HistorySummary]
