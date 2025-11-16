import { useState } from 'react';
import {
  Paper,
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
  Typography,
  Checkbox,
  ListItemText,
  Stack,
  Alert,
} from '@mui/material';
import { PlayArrow, Add, Delete } from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../api';
import { PortfolioBacktestResponse } from '../types';

interface PortfolioControlPanelProps {
  onBacktestComplete: (data: PortfolioBacktestResponse) => void;
  setIsLoading: (loading: boolean) => void;
}

// Preset portfolio templates
const PORTFOLIO_PRESETS = {
  'tech_5': { name: 'Tech 5', tickers: ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA'] },
  'dow_5': { name: 'Dow 5', tickers: ['JNJ', 'JPM', 'V', 'UNH', 'WMT'] },
  'sector_etfs': { name: 'Sector ETFs', tickers: ['XLK', 'XLF', 'XLE', 'XLV', 'XLY'] },
  '60_40': { name: '60/40 Portfolio', tickers: ['SPY', 'AGG'] },
  'custom': { name: 'Custom', tickers: [] },
};

export default function PortfolioControlPanel({
  onBacktestComplete,
  setIsLoading
}: PortfolioControlPanelProps) {
  const [tickers, setTickers] = useState<string[]>(['AAPL', 'MSFT', 'GOOGL']);
  const [newTicker, setNewTicker] = useState('');
  const [startDate, setStartDate] = useState('2022-01-01');
  const [endDate, setEndDate] = useState('2023-12-31');
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>(['equal_weight_buy_hold']);
  const [allocationMethod, setAllocationMethod] = useState('equal');
  const [rebalancing, setRebalancing] = useState('none');
  const [preset, setPreset] = useState('custom');

  const { data: strategiesData } = useQuery({
    queryKey: ['portfolio-strategies'],
    queryFn: api.getPortfolioStrategies,
  });

  const backtestMutation = useMutation({
    mutationFn: api.runPortfolioBacktest,
    onSuccess: (data) => {
      setIsLoading(false);
      onBacktestComplete(data);
    },
    onError: (error) => {
      setIsLoading(false);
      console.error('Portfolio backtest failed:', error);
    },
  });

  const handleAddTicker = () => {
    const ticker = newTicker.trim().toUpperCase();
    if (ticker && !tickers.includes(ticker)) {
      setTickers([...tickers, ticker]);
      setNewTicker('');
    }
  };

  const handleRemoveTicker = (tickerToRemove: string) => {
    setTickers(tickers.filter(t => t !== tickerToRemove));
  };

  const handlePresetChange = (event: SelectChangeEvent) => {
    const presetKey = event.target.value;
    setPreset(presetKey);

    if (presetKey !== 'custom' && PORTFOLIO_PRESETS[presetKey as keyof typeof PORTFOLIO_PRESETS]) {
      setTickers(PORTFOLIO_PRESETS[presetKey as keyof typeof PORTFOLIO_PRESETS].tickers);
    }
  };

  const handleStrategyChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setSelectedStrategies(typeof value === 'string' ? value.split(',') : value);
  };

  const handleRunBacktest = () => {
    if (tickers.length < 2 || !startDate || !endDate || selectedStrategies.length === 0) {
      return;
    }

    setIsLoading(true);
    backtestMutation.mutate({
      tickers: tickers.map(t => t.toUpperCase()),
      startDate,
      endDate,
      strategies: selectedStrategies,
      allocation_method: allocationMethod,
      rebalancing: rebalancing,
    });
  };

  const strategies = strategiesData?.strategies || [];

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Portfolio Backtest Configuration
      </Typography>

      {tickers.length < 2 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Portfolio backtesting requires at least 2 assets. Add more tickers below.
        </Alert>
      )}

      {/* Portfolio Preset Selector */}
      <Box sx={{ mb: 2 }}>
        <FormControl fullWidth>
          <InputLabel>Portfolio Preset</InputLabel>
          <Select value={preset} onChange={handlePresetChange} label="Portfolio Preset">
            {Object.entries(PORTFOLIO_PRESETS).map(([key, { name }]) => (
              <MenuItem key={key} value={key}>{name}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Ticker Management */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Portfolio Assets ({tickers.length})
        </Typography>

        <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
          <TextField
            size="small"
            label="Add Ticker"
            value={newTicker}
            onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleAddTicker();
              }
            }}
            sx={{ flexGrow: 1 }}
          />
          <Button
            variant="outlined"
            onClick={handleAddTicker}
            startIcon={<Add />}
            disabled={!newTicker.trim()}
          >
            Add
          </Button>
        </Stack>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {tickers.map((ticker) => (
            <Chip
              key={ticker}
              label={ticker}
              onDelete={() => handleRemoveTicker(ticker)}
              color="primary"
              variant="outlined"
            />
          ))}
        </Box>
      </Box>

      {/* Date Range */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField
          label="Start Date"
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          fullWidth
        />
        <TextField
          label="End Date"
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          fullWidth
        />
      </Box>

      {/* Portfolio Configuration */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <FormControl fullWidth>
          <InputLabel>Allocation Method</InputLabel>
          <Select
            value={allocationMethod}
            onChange={(e) => setAllocationMethod(e.target.value)}
            label="Allocation Method"
          >
            <MenuItem value="equal">Equal Weight</MenuItem>
            <MenuItem value="optimized">Optimized (Sharpe)</MenuItem>
            <MenuItem value="market_cap">Market Cap Weighted</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Rebalancing</InputLabel>
          <Select
            value={rebalancing}
            onChange={(e) => setRebalancing(e.target.value)}
            label="Rebalancing"
          >
            <MenuItem value="none">No Rebalancing</MenuItem>
            <MenuItem value="monthly">Monthly</MenuItem>
            <MenuItem value="quarterly">Quarterly</MenuItem>
            <MenuItem value="threshold">Threshold (5%)</MenuItem>
            <MenuItem value="tax_aware">Tax-Aware (Minimize Tax Impact)</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Strategy Selection */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Portfolio Strategies</InputLabel>
        <Select
          multiple
          value={selectedStrategies}
          onChange={handleStrategyChange}
          label="Portfolio Strategies"
          renderValue={(selected) => (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {selected.map((value) => {
                const strategy = strategies.find((s) => s.id === value);
                return <Chip key={value} label={strategy?.name || value} size="small" />;
              })}
            </Box>
          )}
        >
          {strategies.map((strategy) => (
            <MenuItem key={strategy.id} value={strategy.id}>
              <Checkbox checked={selectedStrategies.includes(strategy.id)} />
              <ListItemText
                primary={strategy.name}
                secondary={strategy.description}
              />
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          onClick={handleRunBacktest}
          startIcon={<PlayArrow />}
          disabled={
            tickers.length < 2 ||
            !startDate ||
            !endDate ||
            selectedStrategies.length === 0 ||
            backtestMutation.isPending
          }
          fullWidth
        >
          {backtestMutation.isPending ? 'Running...' : 'Run Portfolio Backtest'}
        </Button>
      </Box>

      {backtestMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {backtestMutation.error instanceof Error
            ? backtestMutation.error.message
            : 'Failed to run portfolio backtest'}
        </Alert>
      )}
    </Paper>
  );
}
