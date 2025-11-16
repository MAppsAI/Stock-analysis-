import {
  Paper,
  Typography,
  Box,
  Grid,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { StrategyResult } from '../types';

interface VisualizationPanelProps {
  results: StrategyResult[];
}

export default function VisualizationPanel({ results }: VisualizationPanelProps) {
  // Prepare data for top 10 chart
  const sortedByReturn = [...results]
    .sort((a, b) => b.total_return - a.total_return)
    .slice(0, 10);

  const top10Data = sortedByReturn.map((result) => ({
    name: result.strategy.length > 20
      ? result.strategy.substring(0, 20) + '...'
      : result.strategy,
    fullName: result.strategy,
    return: parseFloat(result.total_return.toFixed(2)),
    sharpe: parseFloat(result.sharpe_ratio.toFixed(2)),
  }));

  // Prepare data for heatmap (using table format since true heatmap is complex in Recharts)
  const categorizePerformance = () => {
    const categories: { [key: string]: { count: number; avgReturn: number; avgSharpe: number } } = {};

    results.forEach((result) => {
      // Extract category from strategy name or use a default
      const category = getCategoryFromStrategy(result.strategy);

      if (!categories[category]) {
        categories[category] = { count: 0, avgReturn: 0, avgSharpe: 0 };
      }

      categories[category].count += 1;
      categories[category].avgReturn += result.total_return;
      categories[category].avgSharpe += result.sharpe_ratio;
    });

    return Object.entries(categories).map(([category, stats]) => ({
      category,
      avgReturn: (stats.avgReturn / stats.count).toFixed(2),
      avgSharpe: (stats.avgSharpe / stats.count).toFixed(2),
      count: stats.count,
    }));
  };

  const getCategoryFromStrategy = (strategyName: string): string => {
    if (strategyName.includes('SMA') || strategyName.includes('EMA') || strategyName.includes('MACD') ||
        strategyName.includes('Moving Average') || strategyName.includes('ADX') || strategyName.includes('Trend') ||
        strategyName.includes('Donchian') || strategyName.includes('Supertrend') || strategyName.includes('Hull') ||
        strategyName.includes('DMI') || strategyName.includes('Aroon')) {
      return 'Trend-Following';
    }
    if (strategyName.includes('RSI') && strategyName.includes('Oversold') || strategyName.includes('Bollinger') ||
        strategyName.includes('Mean Reversion') || strategyName.includes('Stochastic') ||
        strategyName.includes('CCI') || strategyName.includes('Williams')) {
      return 'Mean-Reversion';
    }
    if (strategyName.includes('Momentum') || strategyName.includes('ROC') || strategyName.includes('Breakout')) {
      return 'Momentum';
    }
    if (strategyName.includes('ATR') || strategyName.includes('Volatility') || strategyName.includes('Keltner') ||
        strategyName.includes('Squeeze')) {
      return 'Volatility';
    }
    if (strategyName.includes('Volume') || strategyName.includes('OBV') || strategyName.includes('VPT') ||
        strategyName.includes('VWAP')) {
      return 'Volume';
    }
    return 'Other';
  };

  const categoryData = categorizePerformance();

  const getBarColor = (value: number): string => {
    if (value > 50) return '#4caf50'; // Green
    if (value > 0) return '#8bc34a';  // Light green
    if (value > -20) return '#ff9800'; // Orange
    return '#f44336'; // Red
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 2, backgroundColor: 'rgba(0, 0, 0, 0.9)' }}>
          <Typography variant="body2" sx={{ color: 'white', fontWeight: 'bold' }}>
            {payload[0].payload.fullName}
          </Typography>
          <Typography variant="body2" sx={{ color: '#4caf50' }}>
            Total Return: {payload[0].value}%
          </Typography>
          <Typography variant="body2" sx={{ color: '#2196f3' }}>
            Sharpe Ratio: {payload[0].payload.sharpe}
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Typography variant="h5" gutterBottom>
        Performance Visualization
      </Typography>

      <Grid container spacing={3}>
        {/* Top 10 Bar Chart */}
        <Grid item xs={12}>
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top 10 Best Performing Strategies
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={top10Data} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  stroke="#888"
                />
                <YAxis stroke="#888" label={{ value: 'Total Return (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="return" name="Total Return %" radius={[8, 8, 0, 0]}>
                  {top10Data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getBarColor(entry.return)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Grid>

        {/* Category Performance */}
        <Grid item xs={12} md={6}>
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Performance by Category
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis
                  dataKey="category"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  stroke="#888"
                />
                <YAxis stroke="#888" />
                <Tooltip />
                <Legend />
                <Bar dataKey="avgReturn" name="Avg Return %" fill="#8884d8" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Grid>

        {/* Sharpe Ratio Comparison */}
        <Grid item xs={12} md={6}>
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Risk-Adjusted Returns (Sharpe Ratio)
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={sortedByReturn.slice(0, 5)}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  stroke="#888"
                />
                <YAxis stroke="#888" />
                <Tooltip />
                <Legend />
                <Bar dataKey="sharpe" name="Sharpe Ratio" fill="#82ca9d" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
}
