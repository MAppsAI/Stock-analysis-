import React, { useState, useEffect } from 'react';
import {
  Drawer,
  Box,
  TextField,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  Typography,
  Divider,
  Chip,
  InputAdornment,
  CircularProgress,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Search as SearchIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  ShowChart as ShowChartIcon,
} from '@mui/icons-material';
import { api } from '../api';
import { HistorySummary, BacktestResponse, OptimizationResponse } from '../types';

interface HistoryPanelProps {
  onLoadHistory: (data: BacktestResponse | OptimizationResponse, runType: 'backtest' | 'optimization') => void;
  onRefresh?: () => void;
}

const HistoryPanel: React.FC<HistoryPanelProps> = ({ onLoadHistory, onRefresh }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [history, setHistory] = useState<HistorySummary[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const drawerWidth = 320;

  // Load history on mount and when search term changes (debounced)
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      loadHistory();
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [searchTerm]);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getHistory(searchTerm || undefined, 100, 0);
      setHistory(response.items);
    } catch (err) {
      console.error('Error loading history:', err);
      setError('Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryClick = async (item: HistorySummary) => {
    try {
      const detail = await api.getHistoryById(item.id);
      onLoadHistory(detail.results_data, detail.run_type);
    } catch (err) {
      console.error('Error loading history detail:', err);
      setError('Failed to load history details');
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this history entry?')) {
      return;
    }

    try {
      await api.deleteHistory(id);
      await loadHistory();
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Error deleting history:', err);
      setError('Failed to delete history');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  };

  const getRunTypeIcon = (runType: string) => {
    return runType === 'optimization' ? <ShowChartIcon fontSize="small" /> : <TrendingUpIcon fontSize="small" />;
  };

  const getRunTypeColor = (runType: string): 'primary' | 'secondary' => {
    return runType === 'optimization' ? 'secondary' : 'primary';
  };

  return (
    <>
      {/* Toggle button when drawer is closed */}
      {!isOpen && (
        <IconButton
          onClick={() => setIsOpen(true)}
          sx={{
            position: 'fixed',
            left: 0,
            top: '50%',
            transform: 'translateY(-50%)',
            zIndex: 1200,
            bgcolor: 'background.paper',
            boxShadow: 2,
            '&:hover': { bgcolor: 'background.paper' },
          }}
        >
          <ChevronRightIcon />
        </IconButton>
      )}

      {/* Drawer */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={isOpen}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            bgcolor: 'background.default',
            borderRight: '1px solid',
            borderColor: 'divider',
          },
        }}
      >
        <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', height: '100%' }}>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              History
            </Typography>
            <IconButton onClick={() => setIsOpen(false)} size="small">
              <ChevronLeftIcon />
            </IconButton>
          </Box>

          {/* Search */}
          <TextField
            fullWidth
            size="small"
            placeholder="Search ticker..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />

          <Divider sx={{ mb: 2 }} />

          {/* Error message */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Loading indicator */}
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={32} />
            </Box>
          )}

          {/* History list */}
          {!loading && (
            <List sx={{ flexGrow: 1, overflow: 'auto', px: 0 }}>
              {history.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    {searchTerm ? 'No results found' : 'No history yet'}
                  </Typography>
                </Box>
              ) : (
                history.map((item) => (
                  <ListItem
                    key={item.id}
                    disablePadding
                    sx={{ mb: 1 }}
                    secondaryAction={
                      <IconButton
                        edge="end"
                        size="small"
                        onClick={(e) => handleDelete(e, item.id)}
                        sx={{ opacity: 0.6, '&:hover': { opacity: 1, color: 'error.main' } }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    }
                  >
                    <ListItemButton
                      onClick={() => handleHistoryClick(item)}
                      sx={{
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                        '&:hover': {
                          bgcolor: 'action.hover',
                          borderColor: 'primary.main',
                        },
                      }}
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                              {item.ticker}
                            </Typography>
                            <Chip
                              icon={getRunTypeIcon(item.run_type)}
                              label={item.run_type}
                              size="small"
                              color={getRunTypeColor(item.run_type)}
                              sx={{ height: 20, fontSize: '0.65rem' }}
                            />
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 0.5 }}>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {formatDate(item.created_at)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {item.start_date} to {item.end_date}
                            </Typography>
                            {item.summary_metrics && (
                              <Box sx={{ mt: 0.5 }}>
                                {item.run_type === 'backtest' && item.summary_metrics.best_strategy && (
                                  <Tooltip title={`Best: ${item.summary_metrics.best_strategy}`}>
                                    <Typography
                                      variant="caption"
                                      color="success.main"
                                      sx={{ fontWeight: 500 }}
                                    >
                                      {item.summary_metrics.best_return?.toFixed(2)}% return
                                    </Typography>
                                  </Tooltip>
                                )}
                                {item.run_type === 'optimization' && (
                                  <Typography variant="caption" color="secondary.main" sx={{ fontWeight: 500 }}>
                                    {item.summary_metrics.strategies_optimized} strategies optimized
                                  </Typography>
                                )}
                              </Box>
                            )}
                          </Box>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))
              )}
            </List>
          )}

          {/* Footer */}
          {!loading && history.length > 0 && (
            <Box sx={{ pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary">
                Total: {history.length} entries
              </Typography>
            </Box>
          )}
        </Box>
      </Drawer>
    </>
  );
};

export default HistoryPanel;
