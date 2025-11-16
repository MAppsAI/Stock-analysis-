import {
  Paper,
  Typography,
  Box,
  Tooltip,
} from '@mui/material';
import { PortfolioMetrics } from '../types';

interface CorrelationHeatmapProps {
  correlationMatrix: Record<string, Record<string, number>>;
  tickers: string[];
}

export default function CorrelationHeatmap({
  correlationMatrix,
  tickers
}: CorrelationHeatmapProps) {
  // Get color based on correlation value (-1 to 1)
  const getColor = (value: number): string => {
    // Normalize to 0-1 range
    const normalized = (value + 1) / 2;

    if (value > 0.7) {
      // Strong positive - deep green
      return `rgba(0, 255, 0, ${0.3 + normalized * 0.5})`;
    } else if (value > 0.3) {
      // Moderate positive - light green
      return `rgba(144, 238, 144, ${0.3 + normalized * 0.3})`;
    } else if (value > -0.3) {
      // Weak correlation - yellow
      return `rgba(255, 255, 0, ${0.2 + Math.abs(value) * 0.2})`;
    } else if (value > -0.7) {
      // Moderate negative - light red
      return `rgba(255, 182, 193, ${0.3 + (1 - normalized) * 0.3})`;
    } else {
      // Strong negative - deep red
      return `rgba(255, 0, 0, ${0.3 + (1 - normalized) * 0.5})`;
    }
  };

  const getCellStyle = (value: number) => ({
    backgroundColor: getColor(value),
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '12px',
    textAlign: 'center' as const,
    fontWeight: value === 1 ? 'bold' : 'normal',
    fontSize: '0.85rem',
    minWidth: '80px',
    cursor: 'pointer',
  });

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Asset Correlation Matrix
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Correlation ranges from -1 (perfect negative) to +1 (perfect positive).
        Green indicates positive correlation, red indicates negative correlation.
      </Typography>

      <Box sx={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th style={{
                padding: '12px',
                textAlign: 'left',
                fontWeight: 'bold',
                minWidth: '80px'
              }}>
                Asset
              </th>
              {tickers.map(ticker => (
                <th key={ticker} style={{
                  padding: '12px',
                  textAlign: 'center',
                  fontWeight: 'bold',
                  minWidth: '80px'
                }}>
                  {ticker}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tickers.map(rowTicker => (
              <tr key={rowTicker}>
                <td style={{
                  padding: '12px',
                  fontWeight: 'bold',
                  backgroundColor: 'rgba(0, 0, 0, 0.05)'
                }}>
                  {rowTicker}
                </td>
                {tickers.map(colTicker => {
                  const value = correlationMatrix[rowTicker]?.[colTicker] ?? 0;
                  return (
                    <Tooltip
                      key={colTicker}
                      title={`${rowTicker} vs ${colTicker}: ${value.toFixed(3)}`}
                      arrow
                    >
                      <td style={getCellStyle(value)}>
                        {value.toFixed(2)}
                      </td>
                    </Tooltip>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </Box>

      {/* Legend */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{
            width: 20,
            height: 20,
            backgroundColor: 'rgba(255, 0, 0, 0.7)',
            border: '1px solid rgba(0,0,0,0.2)'
          }} />
          <Typography variant="caption">Strong Negative (-1.0 to -0.7)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{
            width: 20,
            height: 20,
            backgroundColor: 'rgba(255, 182, 193, 0.5)',
            border: '1px solid rgba(0,0,0,0.2)'
          }} />
          <Typography variant="caption">Moderate Negative (-0.7 to -0.3)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{
            width: 20,
            height: 20,
            backgroundColor: 'rgba(255, 255, 0, 0.4)',
            border: '1px solid rgba(0,0,0,0.2)'
          }} />
          <Typography variant="caption">Weak (-0.3 to 0.3)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{
            width: 20,
            height: 20,
            backgroundColor: 'rgba(144, 238, 144, 0.5)',
            border: '1px solid rgba(0,0,0,0.2)'
          }} />
          <Typography variant="caption">Moderate Positive (0.3 to 0.7)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{
            width: 20,
            height: 20,
            backgroundColor: 'rgba(0, 255, 0, 0.7)',
            border: '1px solid rgba(0,0,0,0.2)'
          }} />
          <Typography variant="caption">Strong Positive (0.7 to 1.0)</Typography>
        </Box>
      </Box>
    </Paper>
  );
}
