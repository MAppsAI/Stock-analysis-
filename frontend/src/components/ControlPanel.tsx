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
  Alert,
} from '@mui/material';
import { PlayArrow } from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../api';
import { BacktestResponse } from '../types';

interface ControlPanelProps {
  onBacktestComplete: (data: BacktestResponse) => void;
  setIsLoading: (loading: boolean) => void;
}

export default function ControlPanel({ onBacktestComplete, setIsLoading }: ControlPanelProps) {
  const [ticker, setTicker] = useState('AAPL');
  const [startDate, setStartDate] = useState('2022-01-01');
  const [endDate, setEndDate] = useState('2023-12-31');
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>(['sma_cross']);

  const { data: strategiesData } = useQuery({
    queryKey: ['strategies'],
    queryFn: api.getStrategies,
  });

  const backtestMutation = useMutation({
    mutationFn: api.runBacktest,
    onSuccess: (data) => {
      setIsLoading(false);
      onBacktestComplete(data);
    },
    onError: (error) => {
      setIsLoading(false);
      console.error('Backtest failed:', error);
    },
  });

  const handleStrategyChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setSelectedStrategies(typeof value === 'string' ? value.split(',') : value);
  };

  const handleRunBacktest = () => {
    if (!ticker || !startDate || !endDate || selectedStrategies.length === 0) {
      return;
    }

    setIsLoading(true);
    backtestMutation.mutate({
      ticker: ticker.toUpperCase(),
      startDate,
      endDate,
      strategies: selectedStrategies,
    });
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            label="Ticker Symbol"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="AAPL"
            sx={{ flex: '1 1 200px' }}
          />
          <TextField
            label="Start Date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            sx={{ flex: '1 1 200px' }}
          />
          <TextField
            label="End Date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            sx={{ flex: '1 1 200px' }}
          />
        </Box>

        <FormControl fullWidth>
          <InputLabel>Strategies</InputLabel>
          <Select
            multiple
            value={selectedStrategies}
            onChange={handleStrategyChange}
            label="Strategies"
          >
            {strategiesData?.strategies.map((strategy) => (
              <MenuItem key={strategy.id} value={strategy.id}>
                {strategy.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {backtestMutation.isError && (
          <Alert severity="error">
            Failed to run backtest. Please check your inputs and try again.
          </Alert>
        )}

        <Button
          variant="contained"
          size="large"
          startIcon={<PlayArrow />}
          onClick={handleRunBacktest}
          disabled={backtestMutation.isPending || !ticker || selectedStrategies.length === 0}
          sx={{ alignSelf: 'flex-start' }}
        >
          Run Backtest
        </Button>
      </Box>
    </Paper>
  );
}
