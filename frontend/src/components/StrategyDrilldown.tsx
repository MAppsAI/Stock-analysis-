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
import { Close } from '@mui/icons-material';
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
    if (!open || !chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#1e1e1e' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2b2b43' },
        horzLines: { color: '#2b2b43' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#485c7b',
      },
      timeScale: {
        borderColor: '#485c7b',
        timeVisible: true,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candlestickSeriesRef.current = candlestickSeries;

    // Set candlestick data
    const candleData = priceData.map((d) => ({
      time: d.date,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));
    candlestickSeries.setData(candleData);

    // Add buy/sell markers
    const markers = strategy.signals.map((signal) => ({
      time: signal.date,
      position: signal.type === 'buy' ? 'belowBar' : 'aboveBar',
      color: signal.type === 'buy' ? '#2196F3' : '#e91e63',
      shape: signal.type === 'buy' ? 'arrowUp' : 'arrowDown',
      text: signal.type === 'buy' ? 'BUY' : 'SELL',
    }));

    candlestickSeries.setMarkers(markers as any);

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [open, priceData, strategy]);

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5">
            {strategy.strategy} - {ticker}
          </Typography>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Total Return
              </Typography>
              <Typography variant="h6" sx={{ color: strategy.total_return > 0 ? 'success.main' : 'error.main' }}>
                {formatPercent(strategy.total_return)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Win Rate
              </Typography>
              <Typography variant="h6">
                {formatPercent(strategy.win_rate)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Max Drawdown
              </Typography>
              <Typography variant="h6" color="error.main">
                {formatPercent(strategy.max_drawdown)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Sharpe Ratio
              </Typography>
              <Typography variant="h6">
                {strategy.sharpe_ratio.toFixed(2)}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                # of Trades
              </Typography>
              <Typography variant="h6">
                {strategy.num_trades}
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Price Chart with Buy/Sell Signals
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <Chip label="BUY Signal" size="small" sx={{ backgroundColor: '#2196F3', color: 'white' }} />
            <Chip label="SELL Signal" size="small" sx={{ backgroundColor: '#e91e63', color: 'white' }} />
          </Box>
        </Box>

        <div ref={chartContainerRef} style={{ width: '100%' }} />

        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Trade Signals ({strategy.signals.length})
          </Typography>
          <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
            {strategy.signals.map((signal, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  p: 1,
                  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <Typography variant="body2">{signal.date}</Typography>
                <Chip
                  label={signal.type.toUpperCase()}
                  size="small"
                  sx={{
                    backgroundColor: signal.type === 'buy' ? '#2196F3' : '#e91e63',
                    color: 'white',
                  }}
                />
                <Typography variant="body2">${signal.price.toFixed(2)}</Typography>
              </Box>
            ))}
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
