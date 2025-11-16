import {
  Paper,
  Typography,
  Box,
} from '@mui/material';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ZAxis,
  ReferenceDot,
} from 'recharts';
import { PortfolioStrategyResult } from '../types';

interface EfficientFrontierProps {
  results: PortfolioStrategyResult[];
  buyHoldResult?: PortfolioStrategyResult;
}

export default function EfficientFrontier({
  results,
  buyHoldResult
}: EfficientFrontierProps) {
  // Prepare data for scatter plot
  const allResults = buyHoldResult ? [buyHoldResult, ...results] : results;

  const scatterData = allResults.map((result, index) => ({
    name: result.strategy,
    volatility: result.portfolio_metrics.volatility * 100, // Convert to percentage
    return: result.portfolio_metrics.total_return * 100, // Convert to percentage
    sharpe: result.portfolio_metrics.sharpe_ratio,
    isBuyHold: index === 0 && buyHoldResult !== undefined,
  }));

  // Find the optimal portfolio (highest Sharpe ratio)
  const optimalPortfolio = scatterData.reduce((best, current) =>
    current.sharpe > best.sharpe ? current : best
  , scatterData[0]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #ccc',
            borderRadius: 1,
            p: 1.5,
            boxShadow: 2,
          }}
        >
          <Typography variant="subtitle2" gutterBottom>
            {data.name}
          </Typography>
          <Typography variant="body2">
            Return: {data.return.toFixed(2)}%
          </Typography>
          <Typography variant="body2">
            Volatility: {data.volatility.toFixed(2)}%
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            Sharpe Ratio: {data.sharpe.toFixed(2)}
          </Typography>
        </Box>
      );
    }
    return null;
  };

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Efficient Frontier Analysis
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Risk-return tradeoff visualization. Higher and to the left is better (higher return, lower risk).
        The optimal portfolio (highest Sharpe ratio) is highlighted.
      </Typography>

      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis
            type="number"
            dataKey="volatility"
            name="Volatility"
            unit="%"
            label={{ value: 'Volatility (Risk)', position: 'insideBottom', offset: -10 }}
          />
          <YAxis
            type="number"
            dataKey="return"
            name="Return"
            unit="%"
            label={{ value: 'Total Return', angle: -90, position: 'insideLeft' }}
          />
          <ZAxis type="number" dataKey="sharpe" range={[50, 400]} name="Sharpe Ratio" />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* Buy & Hold baseline */}
          {buyHoldResult && (
            <Scatter
              name="Buy & Hold Baseline"
              data={scatterData.filter(d => d.isBuyHold)}
              fill="#FFA500"
              line={false}
              shape="star"
            />
          )}

          {/* Portfolio strategies */}
          <Scatter
            name="Portfolio Strategies"
            data={scatterData.filter(d => !d.isBuyHold)}
            fill="#8884d8"
          />

          {/* Highlight optimal portfolio */}
          <ReferenceDot
            x={optimalPortfolio.volatility}
            y={optimalPortfolio.return}
            r={10}
            fill="green"
            stroke="darkgreen"
            strokeWidth={3}
            label={{
              value: 'Optimal',
              position: 'top',
              fill: 'green',
              fontWeight: 'bold'
            }}
          />
        </ScatterChart>
      </ResponsiveContainer>

      {/* Optimal Portfolio Info */}
      <Box sx={{ mt: 3, p: 2, backgroundColor: 'rgba(0, 255, 0, 0.1)', borderRadius: 1 }}>
        <Typography variant="subtitle2" gutterBottom>
          Optimal Portfolio (Highest Sharpe Ratio):
        </Typography>
        <Box sx={{ display: 'flex', gap: 4, mt: 1 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Strategy
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {optimalPortfolio.name}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Return
            </Typography>
            <Typography variant="body1" fontWeight="bold" color="success.main">
              {optimalPortfolio.return.toFixed(2)}%
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Volatility
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {optimalPortfolio.volatility.toFixed(2)}%
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Sharpe Ratio
            </Typography>
            <Typography variant="body1" fontWeight="bold" color="primary.main">
              {optimalPortfolio.sharpe.toFixed(2)}
            </Typography>
          </Box>
        </Box>
      </Box>
    </Paper>
  );
}
