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
