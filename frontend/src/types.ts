export interface TradeSignal {
  date: string;
  price: number;
  type: 'buy' | 'sell';
}

export interface StrategyResult {
  strategy: string;
  total_return: number;
  win_rate: number;
  max_drawdown: number;
  sharpe_ratio: number;
  num_trades: number;
  signals: TradeSignal[];
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
