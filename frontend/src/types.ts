export interface TradeSignal {
  date: string;
  price: number;
  type: 'buy' | 'sell';
}

export interface EquityPoint {
  date: string;
  equity: number;  // Cumulative equity value (starts at 1.0 = 100%)
}

export interface StrategyResult {
  strategy: string;
  total_return: number;
  win_rate: number;
  max_drawdown: number;
  sharpe_ratio: number;
  num_trades: number;
  signals: TradeSignal[];
  equity_curve: EquityPoint[];
}

export interface PriceData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BacktestResponse {
  ticker: string;
  startDate: string;
  endDate: string;
  results: StrategyResult[];
  price_data: PriceData[];
  buy_hold_result?: StrategyResult;  // Buy and hold baseline for comparison
}

export interface BacktestRequest {
  ticker: string;
  startDate: string;
  endDate: string;
  strategies: string[];
}

export interface Strategy {
  id: string;
  name: string;
  category: string;
}

export interface OptimizationRequest {
  ticker: string;
  startDate: string;
  endDate: string;
  strategies: string[];
}

export interface OptimizationResult {
  strategy_type: string;
  status: string;
  best_params?: Record<string, any>;
  best_score?: number;
  best_metrics?: Record<string, any>;
  total_tested?: number;
  all_results?: Array<Record<string, any>>;
  param_ranges?: Record<string, any[]>;
  message?: string;
}

export interface OptimizationResponse {
  ticker: string;
  startDate: string;
  endDate: string;
  optimization_results: Record<string, OptimizationResult>;
  summary: Record<string, any>;
  price_data: PriceData[];
}

export interface HistorySummary {
  id: number;
  ticker: string;
  start_date: string;
  end_date: string;
  run_type: 'backtest' | 'optimization';
  created_at: string;
  title: string;
  summary_metrics?: Record<string, any>;
}

export interface HistoryDetail {
  id: number;
  ticker: string;
  start_date: string;
  end_date: string;
  run_type: 'backtest' | 'optimization';
  created_at: string;
  title: string;
  summary_metrics?: Record<string, any>;
  results_data: BacktestResponse | OptimizationResponse;
}

export interface SaveHistoryRequest {
  ticker: string;
  start_date: string;
  end_date: string;
  run_type: 'backtest' | 'optimization';
  results_data: BacktestResponse | OptimizationResponse;
  title?: string;
}

export interface SaveHistoryResponse {
  id: number;
  message: string;
}

export interface HistoryListResponse {
  total_count: number;
  items: HistorySummary[];
}

// =============================================================================
// PORTFOLIO (MULTI-ASSET) TYPES
// =============================================================================

export interface PortfolioBacktestRequest {
  tickers: string[];
  startDate: string;
  endDate: string;
  strategies: string[];
  allocation_method?: string;
  custom_weights?: Record<string, number>;
  rebalancing?: string;
  rebalance_threshold?: number;
  transaction_cost?: number;
}

export interface AssetMetrics {
  ticker: string;
  total_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  weight: number;
  contribution_to_return: number;
}

export interface WeightSnapshot {
  date: string;
  weights: Record<string, number>;
  rebalance?: boolean;
}

export interface PortfolioMetrics {
  total_return: number;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  num_rebalances: number;
  turnover: number;
  diversification_ratio: number;
  correlation_matrix: Record<string, Record<string, number>>;
  rebalance_dates: string[];
  total_transaction_costs?: number;
  transaction_cost_impact_pct?: number;
  estimated_tax_drag_pct?: number;
}

export interface PortfolioStrategyResult {
  strategy: string;
  portfolio_metrics: PortfolioMetrics;
  asset_metrics: AssetMetrics[];
  equity_curve: EquityPoint[];
  weights_timeline: WeightSnapshot[];
}

export interface PortfolioBacktestResponse {
  tickers: string[];
  startDate: string;
  endDate: string;
  results: PortfolioStrategyResult[];
  price_data: Record<string, PriceData[]>;
  buy_hold_result?: PortfolioStrategyResult;
}

export interface PortfolioStrategy {
  id: string;
  name: string;
  category: string;
  description: string;
  parameters?: Record<string, any>;
}

export interface CorrelationResponse {
  tickers: string[];
  correlation_matrix: Record<string, Record<string, number>>;
  covariance_matrix: Record<string, Record<string, number>>;
  volatilities: Record<string, number>;
  date_range: {
    start: string;
    end: string;
  };
}
