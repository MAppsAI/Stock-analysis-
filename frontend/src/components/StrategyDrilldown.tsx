import { useEffect, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Typography,
  IconButton,
  Grid,
  Paper,
  Chip,
} from '@mui/material';
import { Close, TrendingUp, TrendingDown } from '@mui/icons-material';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';
import { StrategyResult, PriceData } from '../types';

interface StrategyDrilldownProps {
  open: boolean;
  onClose: () => void;
  strategy: StrategyResult;
  priceData: PriceData[];
  ticker: string;
}

export default function StrategyDrilldown({
  open,
  onClose,
  strategy,
  priceData,
  ticker,
}: StrategyDrilldownProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!open || !priceData || priceData.length === 0) {
      return;
    }

    // Add a small delay to ensure Dialog content is fully mounted
    const initTimer = setTimeout(() => {
      if (!chartContainerRef.current) {
        console.log('Chart container not ready');
        return;
      }

      console.log('Initializing chart with data:', {
        priceDataLength: priceData.length,
        firstDate: priceData[0]?.date,
        signalsLength: strategy.signals.length
      });

      // Create chart with glassmorphism theme
      const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: 'transparent' },
        textColor: '#b0b0b0',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: 'rgba(0, 255, 255, 0.2)',
      },
      timeScale: {
        borderColor: 'rgba(0, 255, 255, 0.2)',
        timeVisible: true,
      },
    });

    chartRef.current = chart;

    // Add candlestick series with new colors
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#00ffaa',
      downColor: '#ff0055',
      borderVisible: false,
      wickUpColor: '#00ffaa',
      wickDownColor: '#ff0055',
    });

    candlestickSeriesRef.current = candlestickSeries;

    // Helper function to convert date string to proper format for lightweight-charts
    const formatDateForChart = (dateStr: string): string => {
      // If it's already in YYYY-MM-DD format, return as is
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        return dateStr;
      }

      // Try to parse and convert to YYYY-MM-DD
      try {
        const date = new Date(dateStr);
        if (!isNaN(date.getTime())) {
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          return `${year}-${month}-${day}`;
        }
      } catch (e) {
        console.error('Error parsing date:', dateStr, e);
      }

      return dateStr;
    };

    // Set candlestick data with proper formatting and validation
    const candleData = priceData
      .filter(d => d && d.date && !isNaN(d.open) && !isNaN(d.high) && !isNaN(d.low) && !isNaN(d.close))
      .map((d) => ({
        time: formatDateForChart(d.date),
        open: Number(d.open),
        high: Number(d.high),
        low: Number(d.low),
        close: Number(d.close),
      }))
      .sort((a, b) => a.time.localeCompare(b.time)); // Ensure data is sorted by date

    console.log('Candlestick data prepared:', {
      length: candleData.length,
      firstPoint: candleData[0],
      lastPoint: candleData[candleData.length - 1]
    });

    if (candleData.length > 0) {
      candlestickSeries.setData(candleData);
    } else {
      console.warn('No valid candlestick data to display');
    }

    // Add buy/sell markers with new colors
    if (strategy.signals && strategy.signals.length > 0) {
      const markers = strategy.signals
        .filter(signal => signal && signal.date)
        .map((signal) => ({
          time: formatDateForChart(signal.date),
          position: (signal.type === 'buy' ? 'belowBar' : 'aboveBar') as 'belowBar' | 'aboveBar',
          color: signal.type === 'buy' ? '#00ffff' : '#ff0055',
          shape: (signal.type === 'buy' ? 'arrowUp' : 'arrowDown') as 'arrowUp' | 'arrowDown',
          text: signal.type === 'buy' ? 'BUY' : 'SELL',
        }));

      console.log('Markers prepared:', markers.length);
      candlestickSeries.setMarkers(markers);
    }

      // Fit content with a small delay to ensure chart is ready
      setTimeout(() => {
        chart.timeScale().fitContent();
      }, 100);

      // Handle resize
      const handleResize = () => {
        if (chartContainerRef.current) {
          chart.applyOptions({
            width: chartContainerRef.current.clientWidth,
          });
        }
      };

      window.addEventListener('resize', handleResize);

      // Store cleanup function
      chartRef.current = chart;

      // Cleanup will be handled by the outer return
      return () => {
        window.removeEventListener('resize', handleResize);
        chart.remove();
      };
    }, 50); // 50ms delay to ensure Dialog is mounted

    return () => {
      clearTimeout(initTimer);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [open, priceData, strategy]);

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          background: 'rgba(20, 20, 20, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(0, 255, 255, 0.2)',
        },
      }}
    >
      <DialogTitle
        sx={{
          borderBottom: '1px solid rgba(0, 255, 255, 0.2)',
          background: 'linear-gradient(135deg, rgba(0, 255, 255, 0.1) 0%, rgba(0, 200, 200, 0.05) 100%)',
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 700,
                color: '#f5f5f5',
              }}
            >
              {strategy.strategy}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: '#00ffff',
                fontFamily: '"JetBrains Mono", monospace',
                fontWeight: 600,
                mt: 0.5,
              }}
            >
              {ticker}
            </Typography>
          </Box>
          <IconButton
            onClick={onClose}
            sx={{
              color: '#b0b0b0',
              '&:hover': {
                color: '#00ffff',
                background: 'rgba(0, 255, 255, 0.1)',
              },
            }}
          >
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent sx={{ pt: 3 }}>
        {/* Metric Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                textAlign: 'center',
                background: strategy.total_return > 0
                  ? 'linear-gradient(135deg, rgba(0, 255, 170, 0.15) 0%, rgba(0, 200, 140, 0.05) 100%)'
                  : 'linear-gradient(135deg, rgba(255, 0, 85, 0.15) 0%, rgba(200, 0, 70, 0.05) 100%)',
                border: `1px solid ${strategy.total_return > 0 ? '#00ffaa40' : '#ff005540'}`,
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                }}
              >
                Total Return
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  color: strategy.total_return > 0 ? '#00ffaa' : '#ff0055',
                  fontWeight: 800,
                  mt: 0.5,
                  fontFamily: '"JetBrains Mono", monospace',
                }}
              >
                {formatPercent(strategy.total_return)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                textAlign: 'center',
                background: 'rgba(0, 255, 255, 0.08)',
                border: '1px solid rgba(0, 255, 255, 0.2)',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                }}
              >
                Win Rate
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  color: '#00ffff',
                  fontWeight: 800,
                  mt: 0.5,
                  fontFamily: '"JetBrains Mono", monospace',
                }}
              >
                {formatPercent(strategy.win_rate)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                textAlign: 'center',
                background: 'linear-gradient(135deg, rgba(255, 0, 85, 0.15) 0%, rgba(200, 0, 70, 0.05) 100%)',
                border: '1px solid rgba(255, 0, 85, 0.3)',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                }}
              >
                Max Drawdown
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  color: '#ff0055',
                  fontWeight: 800,
                  mt: 0.5,
                  fontFamily: '"JetBrains Mono", monospace',
                }}
              >
                {formatPercent(strategy.max_drawdown)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                textAlign: 'center',
                background: 'rgba(0, 255, 255, 0.08)',
                border: '1px solid rgba(0, 255, 255, 0.2)',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                }}
              >
                Sharpe Ratio
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  color: '#00ffff',
                  fontWeight: 800,
                  mt: 0.5,
                  fontFamily: '"JetBrains Mono", monospace',
                }}
              >
                {strategy.sharpe_ratio.toFixed(2)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                textAlign: 'center',
                background: 'rgba(192, 192, 192, 0.08)',
                border: '1px solid rgba(192, 192, 192, 0.2)',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                }}
              >
                # of Trades
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  color: '#c0c0c0',
                  fontWeight: 800,
                  mt: 0.5,
                  fontFamily: '"JetBrains Mono", monospace',
                }}
              >
                {strategy.num_trades}
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Chart Section */}
        <Box sx={{ mb: 3 }}>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              color: '#f5f5f5',
              mb: 1,
            }}
          >
            Price Chart with Buy/Sell Signals
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <Chip
              icon={<TrendingUp fontSize="small" />}
              label="BUY Signal"
              size="small"
              sx={{
                background: 'linear-gradient(135deg, rgba(0, 255, 255, 0.2) 0%, rgba(0, 200, 200, 0.1) 100%)',
                color: '#00ffff',
                border: '1px solid rgba(0, 255, 255, 0.3)',
                fontWeight: 700,
              }}
            />
            <Chip
              icon={<TrendingDown fontSize="small" />}
              label="SELL Signal"
              size="small"
              sx={{
                background: 'linear-gradient(135deg, rgba(255, 0, 85, 0.2) 0%, rgba(200, 0, 70, 0.1) 100%)',
                color: '#ff0055',
                border: '1px solid rgba(255, 0, 85, 0.3)',
                fontWeight: 700,
              }}
            />
          </Box>
        </Box>

        {/* Chart Container */}
        <Box
          sx={{
            background: 'rgba(30, 30, 30, 0.4)',
            borderRadius: '12px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            p: 2,
            mb: 3,
          }}
        >
          <div ref={chartContainerRef} style={{ width: '100%', height: '500px' }} />
        </Box>

        {/* Trade Signals List */}
        <Box>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              color: '#f5f5f5',
              mb: 2,
            }}
          >
            Trade Signals ({strategy.signals.length})
          </Typography>
          <Box
            sx={{
              maxHeight: 250,
              overflow: 'auto',
              background: 'rgba(30, 30, 30, 0.3)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              '&::-webkit-scrollbar': {
                width: '8px',
              },
              '&::-webkit-scrollbar-track': {
                background: 'rgba(20, 20, 20, 0.5)',
              },
              '&::-webkit-scrollbar-thumb': {
                background: 'rgba(0, 255, 255, 0.3)',
                borderRadius: '4px',
                '&:hover': {
                  background: 'rgba(0, 255, 255, 0.5)',
                },
              },
            }}
          >
            {strategy.signals.map((signal, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 2,
                  borderBottom: index < strategy.signals.length - 1 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    background: 'rgba(0, 255, 255, 0.05)',
                  },
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    color: '#b0b0b0',
                    fontFamily: '"JetBrains Mono", monospace',
                  }}
                >
                  {signal.date}
                </Typography>
                <Chip
                  icon={signal.type === 'buy' ? <TrendingUp fontSize="small" /> : <TrendingDown fontSize="small" />}
                  label={signal.type.toUpperCase()}
                  size="small"
                  sx={{
                    background: signal.type === 'buy'
                      ? 'linear-gradient(135deg, rgba(0, 255, 255, 0.2) 0%, rgba(0, 200, 200, 0.1) 100%)'
                      : 'linear-gradient(135deg, rgba(255, 0, 85, 0.2) 0%, rgba(200, 0, 70, 0.1) 100%)',
                    color: signal.type === 'buy' ? '#00ffff' : '#ff0055',
                    border: `1px solid ${signal.type === 'buy' ? 'rgba(0, 255, 255, 0.3)' : 'rgba(255, 0, 85, 0.3)'}`,
                    fontWeight: 700,
                    fontFamily: '"JetBrains Mono", monospace',
                  }}
                />
                <Typography
                  variant="body2"
                  sx={{
                    color: '#f5f5f5',
                    fontWeight: 600,
                    fontFamily: '"JetBrains Mono", monospace',
                  }}
                >
                  ${signal.price.toFixed(2)}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
