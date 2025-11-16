import axios from 'axios';
import {
  BacktestRequest,
  BacktestResponse,
  Strategy,
  OptimizationRequest,
  OptimizationResponse,
  SaveHistoryRequest,
  SaveHistoryResponse,
  HistoryListResponse,
  HistoryDetail,
  PortfolioBacktestRequest,
  PortfolioBacktestResponse,
  PortfolioStrategy,
  CorrelationResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  async getStrategies(): Promise<{ strategies: Strategy[] }> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/strategies`);
    return response.data;
  },

  async runBacktest(request: BacktestRequest): Promise<BacktestResponse> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/backtest`, request);
    return response.data;
  },

  async runOptimization(request: OptimizationRequest): Promise<OptimizationResponse> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/optimize`, request);
    return response.data;
  },

  // History endpoints
  async saveHistory(request: SaveHistoryRequest): Promise<SaveHistoryResponse> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/history`, request);
    return response.data;
  },

  async getHistory(ticker?: string, limit = 100, offset = 0): Promise<HistoryListResponse> {
    const params = new URLSearchParams();
    if (ticker) params.append('ticker', ticker);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response = await axios.get(`${API_BASE_URL}/api/v1/history?${params.toString()}`);
    return response.data;
  },

  async getHistoryById(id: number): Promise<HistoryDetail> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/history/${id}`);
    return response.data;
  },

  async deleteHistory(id: number): Promise<{ message: string }> {
    const response = await axios.delete(`${API_BASE_URL}/api/v1/history/${id}`);
    return response.data;
  },

  // Portfolio endpoints
  async getPortfolioStrategies(): Promise<{ strategies: PortfolioStrategy[] }> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/portfolio/strategies`);
    return response.data;
  },

  async runPortfolioBacktest(request: PortfolioBacktestRequest): Promise<PortfolioBacktestResponse> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/portfolio/backtest`, request);
    return response.data;
  },

  async getCorrelation(request: PortfolioBacktestRequest): Promise<CorrelationResponse> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/portfolio/correlation`, request);
    return response.data;
  },
};
