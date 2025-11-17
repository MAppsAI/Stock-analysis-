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


class EquityPoint(BaseModel):
    date: str
    equity: float  # Cumulative equity value (starts at 1.0 = 100%)


class StrategyResult(BaseModel):
    strategy: str
    total_return: float
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    num_trades: int
    signals: List[TradeSignal]
    equity_curve: List[EquityPoint]


class BacktestResponse(BaseModel):
    ticker: str
    startDate: str
    endDate: str
    results: List[StrategyResult]
    price_data: List[dict]  # OHLC data for charting
    buy_hold_result: Optional[StrategyResult] = None  # Buy and hold baseline for comparison


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


# =============================================================================
# PORTFOLIO (MULTI-ASSET) MODELS
# =============================================================================

class PortfolioBacktestRequest(BaseModel):
    """Request for multi-asset portfolio backtest"""
    tickers: List[str]  # Multiple tickers for portfolio
    startDate: str
    endDate: str
    strategies: List[str]  # Portfolio strategy IDs
    allocation_method: str = 'equal'  # 'equal', 'market_cap', 'optimized', 'custom'
    custom_weights: Optional[Dict[str, float]] = None  # Custom weights if allocation_method='custom'
    rebalancing: str = 'none'  # 'none', 'monthly', 'quarterly', 'threshold'
    rebalance_threshold: float = 0.05  # 5% drift triggers rebalance
    transaction_cost: float = 0.001  # 0.1% per trade


class AssetMetrics(BaseModel):
    """Metrics for individual asset within portfolio"""
    ticker: str
    total_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    weight: float  # Portfolio weight
    contribution_to_return: float  # Contribution to portfolio return


class WeightSnapshot(BaseModel):
    """Portfolio weight snapshot at a point in time"""
    date: str
    weights: Dict[str, float]  # ticker -> weight
    rebalance: bool = False  # True if this is a rebalance event


class PortfolioMetrics(BaseModel):
    """Portfolio-level metrics"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_rebalances: int
    turnover: float  # Average turnover per rebalance
    diversification_ratio: float
    correlation_matrix: Dict[str, Dict[str, float]]  # ticker -> ticker -> correlation
    rebalance_dates: List[str]
    total_transaction_costs: float = 0.0  # Total transaction costs incurred
    transaction_cost_impact_pct: float = 0.0  # Transaction costs as % of returns
    estimated_tax_drag_pct: float = 0.0  # Estimated tax impact as % of returns


class PortfolioStrategyResult(BaseModel):
    """Results for a single portfolio strategy"""
    strategy: str
    portfolio_metrics: PortfolioMetrics
    asset_metrics: List[AssetMetrics]
    equity_curve: List[EquityPoint]
    weights_timeline: List[WeightSnapshot]


class PortfolioBacktestResponse(BaseModel):
    """Response for portfolio backtest"""
    tickers: List[str]
    startDate: str
    endDate: str
    results: List[PortfolioStrategyResult]
    price_data: Dict[str, List[dict]]  # ticker -> OHLC data
    buy_hold_result: Optional[PortfolioStrategyResult] = None  # Equal-weight buy-hold baseline


class PortfolioOptimizationRequest(BaseModel):
    """Request for portfolio optimization"""
    tickers: List[str]
    startDate: str
    endDate: str
    strategy: str  # Single portfolio strategy to optimize
    optimization_method: str = 'sharpe'  # 'sharpe', 'return', 'volatility'


class PortfolioOptimizationResult(BaseModel):
    """Results from portfolio optimization"""
    strategy: str
    optimal_weights: Dict[str, float]
    optimal_params: Dict[str, Any]
    expected_return: float
    expected_volatility: float
    expected_sharpe: float
    all_results: List[Dict[str, Any]]  # All tested combinations


# =============================================================================
# SCANNER MODELS
# =============================================================================

class ScannerRequest(BaseModel):
    """Request to scan for signals across a universe of stocks"""
    universe: str  # 'sp500', 'nasdaq100', 'russell2000', 'all'
    strategies: List[str]  # List of strategy IDs to scan for
    lookback_days: int = 14  # Days to look back for signals
    max_stocks: Optional[int] = None  # Limit for testing (None = all)
    signal_type: Optional[str] = None  # Filter by 'buy' or 'sell'


class ScanSignal(BaseModel):
    """Individual signal found by scanner"""
    ticker: str
    strategy: str
    strategy_category: str
    signal_type: str  # 'buy' or 'sell'
    signal_date: str
    signal_price: float
    current_price: float
    days_ago: int
    price_change_pct: float


class ScannerResponse(BaseModel):
    """Response from scanner"""
    universe: str
    strategies_scanned: List[str]
    total_stocks_scanned: int
    total_signals_found: int
    unique_tickers: int
    lookback_days: int
    scan_completed_at: str
    signals: List[ScanSignal]
    summary: Dict[str, Any]


class UniverseInfo(BaseModel):
    """Information about a stock universe"""
    id: str
    name: str
    description: str
    approximate_count: int
    note: Optional[str] = None


class UniverseListResponse(BaseModel):
    """List of available universes"""
    universes: List[UniverseInfo]
