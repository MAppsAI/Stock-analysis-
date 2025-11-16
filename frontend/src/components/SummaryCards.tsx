import { Grid, Paper, Typography, Box } from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  ShowChart,
  Assessment,
  Speed,
} from '@mui/icons-material';
import { StrategyResult } from '../types';

interface SummaryCardsProps {
  results: StrategyResult[];
  ticker: string;
}

export default function SummaryCards({ results, ticker }: SummaryCardsProps) {
  // Calculate summary statistics
  const bestStrategy = results.reduce((best, current) =>
    current.total_return > best.total_return ? current : best
  , results[0]);

  const bestSharpe = results.reduce((best, current) =>
    current.sharpe_ratio > best.sharpe_ratio ? current : best
  , results[0]);

  const profitableStrategies = results.filter(r => r.total_return > 0).length;
  const profitablePercentage = ((profitableStrategies / results.length) * 100).toFixed(1);

  const avgReturn = (results.reduce((sum, r) => sum + r.total_return, 0) / results.length).toFixed(2);
  const avgSharpe = (results.reduce((sum, r) => sum + r.sharpe_ratio, 0) / results.length).toFixed(2);

  const totalTrades = results.reduce((sum, r) => sum + r.num_trades, 0);

  const cards = [
    {
      title: 'Best Strategy',
      value: bestStrategy.strategy,
      subtitle: `${bestStrategy.total_return > 0 ? '+' : ''}${bestStrategy.total_return.toFixed(2)}%`,
      icon: <TrendingUp />,
      color: '#4caf50',
    },
    {
      title: 'Best Risk-Adjusted',
      value: bestSharpe.strategy,
      subtitle: `Sharpe: ${bestSharpe.sharpe_ratio.toFixed(2)}`,
      icon: <ShowChart />,
      color: '#2196f3',
    },
    {
      title: 'Profitable Strategies',
      value: `${profitableStrategies}/${results.length}`,
      subtitle: `${profitablePercentage}% success rate`,
      icon: <Assessment />,
      color: profitableStrategies / results.length > 0.5 ? '#4caf50' : '#ff9800',
    },
    {
      title: 'Average Performance',
      value: `${parseFloat(avgReturn) >= 0 ? '+' : ''}${avgReturn}%`,
      subtitle: `Avg Sharpe: ${avgSharpe}`,
      icon: <Speed />,
      color: parseFloat(avgReturn) >= 0 ? '#4caf50' : '#f44336',
    },
  ];

  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h5" gutterBottom>
          Performance Summary - {ticker}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Analysis of {results.length} strategies • {totalTrades.toLocaleString()} total trades
        </Typography>
      </Box>

      <Grid container spacing={2}>
        {cards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                height: '100%',
                border: `2px solid ${card.color}`,
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box
                  sx={{
                    mr: 2,
                    color: card.color,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  {card.icon}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {card.title}
                </Typography>
              </Box>

              <Typography
                variant="h6"
                sx={{
                  fontWeight: 'bold',
                  color: card.color,
                  mb: 0.5,
                  fontSize: card.value.length > 25 ? '0.9rem' : '1.25rem',
                }}
              >
                {card.value.length > 30 ? card.value.substring(0, 30) + '...' : card.value}
              </Typography>

              <Typography variant="caption" color="text.secondary">
                {card.subtitle}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
}
