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
    if (value > 50) return '#00ffaa';
    if (value > 0) return '#00ffff';
    if (value > -20) return '#ffaa00';
    return '#ff0055';
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper
          sx={{
            p: 2,
            background: 'rgba(10, 10, 10, 0.95)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(0, 255, 255, 0.3)',
          }}
        >
          <Typography
            variant="body2"
            sx={{
              color: '#f5f5f5',
              fontWeight: 700,
              mb: 0.5,
            }}
          >
            {payload[0].payload.fullName}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: '#00ffaa',
              fontFamily: '"JetBrains Mono", monospace',
              display: 'block',
            }}
          >
            Total Return: {payload[0].value}%
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: '#00ffff',
              fontFamily: '"JetBrains Mono", monospace',
              display: 'block',
            }}
          >
            Sharpe Ratio: {payload[0].payload.sharpe}
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  return (
    <Paper
      sx={{
        p: 3,
        mt: 3,
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: 'linear-gradient(90deg, #00ffff 0%, transparent 100%)',
        },
      }}
    >
      <Typography
        variant="h5"
        sx={{
          fontWeight: 700,
          color: '#f5f5f5',
          mb: 3,
        }}
      >
        Performance Visualization
      </Typography>

      <Grid container spacing={3}>
        {/* Top 10 Bar Chart */}
        <Grid item xs={12}>
          <Box
            sx={{
              p: 2,
              background: 'rgba(30, 30, 30, 0.3)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                color: '#f5f5f5',
                mb: 2,
              }}
            >
              Top 10 Best Performing Strategies
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={top10Data} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  stroke="#b0b0b0"
                  style={{
                    fontSize: '12px',
                    fontFamily: '"Manrope", sans-serif',
                  }}
                />
                <YAxis
                  stroke="#b0b0b0"
                  label={{
                    value: 'Total Return (%)',
                    angle: -90,
                    position: 'insideLeft',
                    style: { fill: '#b0b0b0', fontFamily: '"Manrope", sans-serif' },
                  }}
                  style={{
                    fontSize: '12px',
                    fontFamily: '"Manrope", sans-serif',
                  }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{
                    fontFamily: '"Manrope", sans-serif',
                    color: '#b0b0b0',
                  }}
                />
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
          <Box
            sx={{
              p: 2,
              background: 'rgba(30, 30, 30, 0.3)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                color: '#f5f5f5',
                mb: 2,
              }}
            >
              Performance by Category
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                <XAxis
                  dataKey="category"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  stroke="#b0b0b0"
                  style={{
                    fontSize: '12px',
                    fontFamily: '"Manrope", sans-serif',
                  }}
                />
                <YAxis
                  stroke="#b0b0b0"
                  style={{
                    fontSize: '12px',
                    fontFamily: '"Manrope", sans-serif',
                  }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{
                    fontFamily: '"Manrope", sans-serif',
                    color: '#b0b0b0',
                  }}
                />
                <Bar dataKey="avgReturn" name="Avg Return %" fill="#00ffff" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Grid>

        {/* Sharpe Ratio Comparison */}
        <Grid item xs={12} md={6}>
          <Box
            sx={{
              p: 2,
              background: 'rgba(30, 30, 30, 0.3)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                color: '#f5f5f5',
                mb: 2,
              }}
            >
              Risk-Adjusted Returns (Sharpe Ratio)
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={sortedByReturn.slice(0, 5)}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  stroke="#b0b0b0"
                  style={{
                    fontSize: '12px',
                    fontFamily: '"Manrope", sans-serif',
                  }}
                />
                <YAxis
                  stroke="#b0b0b0"
                  style={{
                    fontSize: '12px',
                    fontFamily: '"Manrope", sans-serif',
                  }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{
                    fontFamily: '"Manrope", sans-serif',
                    color: '#b0b0b0',
                  }}
                />
                <Bar dataKey="sharpe" name="Sharpe Ratio" fill="#00ffaa" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
}
