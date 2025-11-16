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
  Checkbox,
  ListItemText,
  Chip,
  Typography,
  ListItemIcon,
} from '@mui/material';
import { PlayArrow, TuneOutlined, CheckBoxOutlineBlank, CheckBox, SelectAll } from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../api';
import { BacktestResponse, OptimizationResponse } from '../types';

interface ControlPanelProps {
  onBacktestComplete: (data: BacktestResponse) => void;
  onOptimizationComplete: (data: OptimizationResponse) => void;
  setIsLoading: (loading: boolean) => void;
}

export default function ControlPanel({ onBacktestComplete, onOptimizationComplete, setIsLoading }: ControlPanelProps) {
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

  const optimizationMutation = useMutation({
    mutationFn: api.runOptimization,
    onSuccess: (data) => {
      setIsLoading(false);
      onOptimizationComplete(data);
    },
    onError: (error) => {
      setIsLoading(false);
      console.error('Optimization failed:', error);
    },
  });

  const allStrategyIds = strategiesData?.strategies.map((s) => s.id) || [];
  const isAllSelected = allStrategyIds.length > 0 && selectedStrategies.length === allStrategyIds.length;

  const handleStrategyChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    const newValue = typeof value === 'string' ? value.split(',') : value;

    // Handle "Select All" toggle
    if (newValue.includes('__select_all__')) {
      if (isAllSelected) {
        setSelectedStrategies([]);
      } else {
        setSelectedStrategies(allStrategyIds);
      }
    } else {
      setSelectedStrategies(newValue);
    }
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

  const handleRunOptimization = () => {
    if (!ticker || !startDate || !endDate || selectedStrategies.length === 0) {
      return;
    }

    setIsLoading(true);
    optimizationMutation.mutate({
      ticker: ticker.toUpperCase(),
      startDate,
      endDate,
      strategies: selectedStrategies,
    });
  };

  return (
    <Paper
      sx={{
        p: 3,
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
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Header */}
        <Box>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              color: '#f5f5f5',
              mb: 0.5,
            }}
          >
            Configuration
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: 'text.secondary',
            }}
          >
            Configure your backtest parameters and select strategies
          </Typography>
        </Box>

        {/* Input Fields */}
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            label="Ticker Symbol"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="AAPL"
            sx={{
              flex: '1 1 200px',
              '& .MuiInputLabel-root': {
                color: 'text.secondary',
                fontWeight: 600,
              },
              '& .MuiInputLabel-root.Mui-focused': {
                color: '#00ffff',
              },
            }}
          />
          <TextField
            label="Start Date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            sx={{
              flex: '1 1 200px',
              '& .MuiInputLabel-root': {
                color: 'text.secondary',
                fontWeight: 600,
              },
              '& .MuiInputLabel-root.Mui-focused': {
                color: '#00ffff',
              },
            }}
          />
          <TextField
            label="End Date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            sx={{
              flex: '1 1 200px',
              '& .MuiInputLabel-root': {
                color: 'text.secondary',
                fontWeight: 600,
              },
              '& .MuiInputLabel-root.Mui-focused': {
                color: '#00ffff',
              },
            }}
          />
        </Box>

        {/* Strategies Dropdown with Checkboxes and Select All */}
        <FormControl fullWidth>
          <InputLabel
            sx={{
              color: 'text.secondary',
              fontWeight: 600,
              '&.Mui-focused': {
                color: '#00ffff',
              },
            }}
          >
            Strategies
          </InputLabel>
          <Select
            multiple
            value={selectedStrategies}
            onChange={handleStrategyChange}
            label="Strategies"
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                <Chip
                  size="small"
                  label={`${selected.length} selected`}
                  sx={{
                    background: 'linear-gradient(135deg, #00ffff 0%, #00cccc 100%)',
                    color: '#0a0a0a',
                    fontWeight: 700,
                  }}
                />
                {selected.slice(0, 3).map((value) => {
                  const strategy = strategiesData?.strategies.find((s) => s.id === value);
                  return (
                    <Chip
                      key={value}
                      size="small"
                      label={strategy?.name || value}
                      sx={{
                        backgroundColor: 'rgba(0, 255, 255, 0.1)',
                        color: '#00ffff',
                        border: '1px solid rgba(0, 255, 255, 0.3)',
                      }}
                    />
                  );
                })}
                {selected.length > 3 && (
                  <Chip
                    size="small"
                    label={`+${selected.length - 3} more`}
                    sx={{
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      color: 'text.secondary',
                    }}
                  />
                )}
              </Box>
            )}
            MenuProps={{
              PaperProps: {
                sx: {
                  maxHeight: 400,
                  backgroundColor: 'rgba(20, 20, 20, 0.95)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(0, 255, 255, 0.2)',
                  '& .MuiMenuItem-root': {
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 255, 255, 0.1)',
                    },
                    '&.Mui-selected': {
                      backgroundColor: 'rgba(0, 255, 255, 0.15)',
                      '&:hover': {
                        backgroundColor: 'rgba(0, 255, 255, 0.2)',
                      },
                    },
                  },
                },
              },
            }}
          >
            {/* Select All Option */}
            <MenuItem
              value="__select_all__"
              sx={{
                borderBottom: '1px solid rgba(0, 255, 255, 0.2)',
                mb: 1,
                pb: 1,
              }}
            >
              <ListItemIcon>
                <Checkbox
                  icon={<CheckBoxOutlineBlank sx={{ color: '#00ffff' }} />}
                  checkedIcon={<CheckBox sx={{ color: '#00ffff' }} />}
                  checked={isAllSelected}
                  indeterminate={selectedStrategies.length > 0 && !isAllSelected}
                  sx={{
                    color: '#00ffff',
                    '&.Mui-checked': {
                      color: '#00ffff',
                    },
                    '&.MuiCheckbox-indeterminate': {
                      color: '#00ffff',
                    },
                  }}
                />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SelectAll sx={{ fontSize: 20, color: '#00ffff' }} />
                    <Typography sx={{ fontWeight: 700, color: '#00ffff' }}>
                      Select All Strategies
                    </Typography>
                  </Box>
                }
              />
            </MenuItem>

            {/* Individual Strategy Options */}
            {strategiesData?.strategies.map((strategy) => (
              <MenuItem key={strategy.id} value={strategy.id}>
                <ListItemIcon>
                  <Checkbox
                    icon={<CheckBoxOutlineBlank sx={{ color: '#00ffff' }} />}
                    checkedIcon={<CheckBox sx={{ color: '#00ffff' }} />}
                    checked={selectedStrategies.includes(strategy.id)}
                    sx={{
                      color: '#00ffff',
                      '&.Mui-checked': {
                        color: '#00ffff',
                      },
                    }}
                  />
                </ListItemIcon>
                <ListItemText
                  primary={strategy.name}
                  sx={{
                    '& .MuiTypography-root': {
                      fontWeight: selectedStrategies.includes(strategy.id) ? 600 : 400,
                      color: selectedStrategies.includes(strategy.id) ? '#f5f5f5' : 'text.secondary',
                    },
                  }}
                />
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Error Messages */}
        {backtestMutation.isError && (
          <Alert
            severity="error"
            sx={{
              backgroundColor: 'rgba(255, 0, 85, 0.1)',
              border: '1px solid rgba(255, 0, 85, 0.3)',
              color: '#ff0055',
              '& .MuiAlert-icon': {
                color: '#ff0055',
              },
            }}
          >
            Failed to run backtest. Please check your inputs and try again.
          </Alert>
        )}

        {optimizationMutation.isError && (
          <Alert
            severity="error"
            sx={{
              backgroundColor: 'rgba(255, 0, 85, 0.1)',
              border: '1px solid rgba(255, 0, 85, 0.3)',
              color: '#ff0055',
              '& .MuiAlert-icon': {
                color: '#ff0055',
              },
            }}
          >
            Failed to run optimization. Please check your inputs and try again.
          </Alert>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<PlayArrow />}
            onClick={handleRunBacktest}
            disabled={backtestMutation.isPending || optimizationMutation.isPending || !ticker || selectedStrategies.length === 0}
            sx={{ flex: 1 }}
          >
            Run Backtest
          </Button>

          <Button
            variant="contained"
            size="large"
            startIcon={<TuneOutlined />}
            onClick={handleRunOptimization}
            disabled={backtestMutation.isPending || optimizationMutation.isPending || !ticker || selectedStrategies.length === 0}
            sx={{
              flex: 1,
              background: 'linear-gradient(135deg, #c0c0c0 0%, #909090 100%)',
              color: '#0a0a0a',
              '&:hover': {
                background: 'linear-gradient(135deg, #e8e8e8 0%, #c0c0c0 100%)',
              },
            }}
          >
            Optimize Parameters
          </Button>
        </Box>
      </Box>
    </Paper>
  );
}
