import axios from 'axios';
import { BacktestRequest, BacktestResponse, Strategy } from './types';

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
};
