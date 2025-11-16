import { useState } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Typography,
  Box,
  Chip,
} from '@mui/material';
import { StrategyResult } from '../types';

interface ResultsTableProps {
  results: StrategyResult[];
  onStrategyClick: (strategy: StrategyResult) => void;
}

type SortField = keyof StrategyResult;
type SortOrder = 'asc' | 'desc';

export default function ResultsTable({ results, onStrategyClick }: ResultsTableProps) {
  const [sortField, setSortField] = useState<SortField>('total_return');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const handleSort = (field: SortField) => {
    const isAsc = sortField === field && sortOrder === 'asc';
    setSortOrder(isAsc ? 'desc' : 'asc');
    setSortField(field);
  };

  const sortedResults = [...results].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    }

    return 0;
  });

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getReturnColor = (value: number) => {
    if (value > 0) return 'success.main';
    if (value < 0) return 'error.main';
    return 'text.secondary';
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Strategy Results
      </Typography>

      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Click on any strategy to view detailed buy/sell signals on the chart
        </Typography>
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'strategy'}
                  direction={sortField === 'strategy' ? sortOrder : 'asc'}
                  onClick={() => handleSort('strategy')}
                >
                  Strategy
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'total_return'}
                  direction={sortField === 'total_return' ? sortOrder : 'asc'}
                  onClick={() => handleSort('total_return')}
                >
                  Total Return
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'win_rate'}
                  direction={sortField === 'win_rate' ? sortOrder : 'asc'}
                  onClick={() => handleSort('win_rate')}
                >
                  Win Rate
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'max_drawdown'}
                  direction={sortField === 'max_drawdown' ? sortOrder : 'asc'}
                  onClick={() => handleSort('max_drawdown')}
                >
                  Max Drawdown
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'sharpe_ratio'}
                  direction={sortField === 'sharpe_ratio' ? sortOrder : 'asc'}
                  onClick={() => handleSort('sharpe_ratio')}
                >
                  Sharpe Ratio
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'num_trades'}
                  direction={sortField === 'num_trades' ? sortOrder : 'asc'}
                  onClick={() => handleSort('num_trades')}
                >
                  # of Trades
                </TableSortLabel>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedResults.map((result, index) => (
              <TableRow
                key={index}
                hover
                sx={{ cursor: 'pointer' }}
                onClick={() => onStrategyClick(result)}
              >
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {result.strategy}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={formatPercent(result.total_return)}
                    size="small"
                    sx={{
                      backgroundColor: result.total_return > 0 ? 'success.main' : 'error.main',
                      color: 'white',
                    }}
                  />
                </TableCell>
                <TableCell align="right" sx={{ color: getReturnColor(result.win_rate) }}>
                  {formatPercent(result.win_rate)}
                </TableCell>
                <TableCell align="right" sx={{ color: 'error.main' }}>
                  {formatPercent(result.max_drawdown)}
                </TableCell>
                <TableCell align="right">
                  {result.sharpe_ratio.toFixed(2)}
                </TableCell>
                <TableCell align="right">
                  {result.num_trades}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
