import { Grid, Paper, Typography, Box } from '@mui/material';
import {
  TrendingUp,
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
  // Return early if no results
  if (!results || results.length === 0) {
    return (
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" color="text.secondary">
          No results available
        </Typography>
      </Paper>
    );
  }

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
      color: '#00ffaa',
      gradient: 'linear-gradient(135deg, rgba(0, 255, 170, 0.15) 0%, rgba(0, 200, 140, 0.05) 100%)',
    },
    {
      title: 'Best Risk-Adjusted',
      value: bestSharpe.strategy,
      subtitle: `Sharpe: ${bestSharpe.sharpe_ratio.toFixed(2)}`,
      icon: <ShowChart />,
      color: '#00ffff',
      gradient: 'linear-gradient(135deg, rgba(0, 255, 255, 0.15) 0%, rgba(0, 200, 200, 0.05) 100%)',
    },
    {
      title: 'Profitable Strategies',
      value: `${profitableStrategies}/${results.length}`,
      subtitle: `${profitablePercentage}% success rate`,
      icon: <Assessment />,
      color: profitableStrategies / results.length > 0.5 ? '#00ffaa' : '#ffaa00',
      gradient: profitableStrategies / results.length > 0.5
        ? 'linear-gradient(135deg, rgba(0, 255, 170, 0.15) 0%, rgba(0, 200, 140, 0.05) 100%)'
        : 'linear-gradient(135deg, rgba(255, 170, 0, 0.15) 0%, rgba(200, 140, 0, 0.05) 100%)',
    },
    {
      title: 'Average Performance',
      value: `${parseFloat(avgReturn) >= 0 ? '+' : ''}${avgReturn}%`,
      subtitle: `Avg Sharpe: ${avgSharpe}`,
      icon: <Speed />,
      color: parseFloat(avgReturn) >= 0 ? '#00ffaa' : '#ff0055',
      gradient: parseFloat(avgReturn) >= 0
        ? 'linear-gradient(135deg, rgba(0, 255, 170, 0.15) 0%, rgba(0, 200, 140, 0.05) 100%)'
        : 'linear-gradient(135deg, rgba(255, 0, 85, 0.15) 0%, rgba(200, 0, 70, 0.05) 100%)',
    },
  ];

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
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            color: '#f5f5f5',
            mb: 1,
          }}
        >
          Performance Summary
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <Box
            sx={{
              px: 2,
              py: 0.5,
              background: 'rgba(0, 255, 255, 0.15)',
              border: '1px solid rgba(0, 255, 255, 0.3)',
              borderRadius: '8px',
              backdropFilter: 'blur(10px)',
            }}
          >
            <Typography
              variant="body2"
              sx={{
                color: '#00ffff',
                fontWeight: 700,
                fontFamily: '"JetBrains Mono", monospace',
              }}
            >
              {ticker}
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {results.length} strategies • {totalTrades.toLocaleString()} total trades
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={2}>
        {cards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Paper
              elevation={0}
              sx={{
                p: 3,
                height: '100%',
                position: 'relative',
                overflow: 'hidden',
                background: card.gradient,
                border: `1px solid ${card.color}40`,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  border: `1px solid ${card.color}80`,
                  boxShadow: `0 8px 24px ${card.color}30`,
                },
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '3px',
                  background: card.color,
                  opacity: 0.7,
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                <Box
                  sx={{
                    mr: 2,
                    color: card.color,
                    display: 'flex',
                    alignItems: 'center',
                    fontSize: '2rem',
                    filter: `drop-shadow(0 0 8px ${card.color}60)`,
                  }}
                >
                  {card.icon}
                </Box>
                <Typography
                  variant="overline"
                  sx={{
                    color: 'text.secondary',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    lineHeight: 1.2,
                  }}
                >
                  {card.title}
                </Typography>
              </Box>

              <Typography
                variant="h6"
                sx={{
                  fontWeight: 800,
                  color: card.color,
                  mb: 0.5,
                  fontSize: card.value.length > 25 ? '0.95rem' : '1.3rem',
                  textShadow: `0 0 20px ${card.color}40`,
                  wordBreak: 'break-word',
                }}
              >
                {card.value.length > 30 ? card.value.substring(0, 30) + '...' : card.value}
              </Typography>

              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontWeight: 500,
                }}
              >
                {card.subtitle}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
}
