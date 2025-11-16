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
import { TrendingUp, TrendingDown } from '@mui/icons-material';
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
    if (value > 0) return '#00ffaa';
    if (value < 0) return '#ff0055';
    return '#b0b0b0';
  };

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
          Strategy Results
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Click on any strategy to view detailed buy/sell signals on the chart
        </Typography>
      </Box>

      <TableContainer
        sx={{
          '& .MuiTable-root': {
            borderCollapse: 'separate',
            borderSpacing: '0 4px',
          },
        }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell
                sx={{
                  background: 'rgba(0, 255, 255, 0.05)',
                  borderBottom: 'none',
                }}
              >
                <TableSortLabel
                  active={sortField === 'strategy'}
                  direction={sortField === 'strategy' ? sortOrder : 'asc'}
                  onClick={() => handleSort('strategy')}
                  sx={{
                    '&.Mui-active': {
                      color: '#00ffff',
                      '& .MuiTableSortLabel-icon': {
                        color: '#00ffff !important',
                      },
                    },
                    '&:hover': {
                      color: '#00ffff',
                    },
                  }}
                >
                  Strategy
                </TableSortLabel>
              </TableCell>
              <TableCell
                align="right"
                sx={{
                  background: 'rgba(0, 255, 255, 0.05)',
                  borderBottom: 'none',
                }}
              >
                <TableSortLabel
                  active={sortField === 'total_return'}
                  direction={sortField === 'total_return' ? sortOrder : 'asc'}
                  onClick={() => handleSort('total_return')}
                  sx={{
                    '&.Mui-active': {
                      color: '#00ffff',
                      '& .MuiTableSortLabel-icon': {
                        color: '#00ffff !important',
                      },
                    },
                    '&:hover': {
                      color: '#00ffff',
                    },
                  }}
                >
                  Total Return
                </TableSortLabel>
              </TableCell>
              <TableCell
                align="right"
                sx={{
                  background: 'rgba(0, 255, 255, 0.05)',
                  borderBottom: 'none',
                }}
              >
                <TableSortLabel
                  active={sortField === 'win_rate'}
                  direction={sortField === 'win_rate' ? sortOrder : 'asc'}
                  onClick={() => handleSort('win_rate')}
                  sx={{
                    '&.Mui-active': {
                      color: '#00ffff',
                      '& .MuiTableSortLabel-icon': {
                        color: '#00ffff !important',
                      },
                    },
                    '&:hover': {
                      color: '#00ffff',
                    },
                  }}
                >
                  Win Rate
                </TableSortLabel>
              </TableCell>
              <TableCell
                align="right"
                sx={{
                  background: 'rgba(0, 255, 255, 0.05)',
                  borderBottom: 'none',
                }}
              >
                <TableSortLabel
                  active={sortField === 'max_drawdown'}
                  direction={sortField === 'max_drawdown' ? sortOrder : 'asc'}
                  onClick={() => handleSort('max_drawdown')}
                  sx={{
                    '&.Mui-active': {
                      color: '#00ffff',
                      '& .MuiTableSortLabel-icon': {
                        color: '#00ffff !important',
                      },
                    },
                    '&:hover': {
                      color: '#00ffff',
                    },
                  }}
                >
                  Max Drawdown
                </TableSortLabel>
              </TableCell>
              <TableCell
                align="right"
                sx={{
                  background: 'rgba(0, 255, 255, 0.05)',
                  borderBottom: 'none',
                }}
              >
                <TableSortLabel
                  active={sortField === 'sharpe_ratio'}
                  direction={sortField === 'sharpe_ratio' ? sortOrder : 'asc'}
                  onClick={() => handleSort('sharpe_ratio')}
                  sx={{
                    '&.Mui-active': {
                      color: '#00ffff',
                      '& .MuiTableSortLabel-icon': {
                        color: '#00ffff !important',
                      },
                    },
                    '&:hover': {
                      color: '#00ffff',
                    },
                  }}
                >
                  Sharpe Ratio
                </TableSortLabel>
              </TableCell>
              <TableCell
                align="right"
                sx={{
                  background: 'rgba(0, 255, 255, 0.05)',
                  borderBottom: 'none',
                }}
              >
                <TableSortLabel
                  active={sortField === 'num_trades'}
                  direction={sortField === 'num_trades' ? sortOrder : 'asc'}
                  onClick={() => handleSort('num_trades')}
                  sx={{
                    '&.Mui-active': {
                      color: '#00ffff',
                      '& .MuiTableSortLabel-icon': {
                        color: '#00ffff !important',
                      },
                    },
                    '&:hover': {
                      color: '#00ffff',
                    },
                  }}
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
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  '& td': {
                    background: 'rgba(30, 30, 30, 0.4)',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                    borderTop: '1px solid rgba(255, 255, 255, 0.03)',
                  },
                  '& td:first-of-type': {
                    borderLeft: '1px solid rgba(255, 255, 255, 0.03)',
                    borderTopLeftRadius: '8px',
                    borderBottomLeftRadius: '8px',
                  },
                  '& td:last-of-type': {
                    borderRight: '1px solid rgba(255, 255, 255, 0.03)',
                    borderTopRightRadius: '8px',
                    borderBottomRightRadius: '8px',
                  },
                  '&:hover': {
                    '& td': {
                      background: 'rgba(0, 255, 255, 0.08)',
                      borderColor: 'rgba(0, 255, 255, 0.2)',
                    },
                  },
                }}
                onClick={() => onStrategyClick(result)}
              >
                <TableCell>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 600,
                      color: '#f5f5f5',
                    }}
                  >
                    {result.strategy}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Chip
                    icon={result.total_return > 0 ? <TrendingUp fontSize="small" /> : <TrendingDown fontSize="small" />}
                    label={formatPercent(result.total_return)}
                    size="small"
                    sx={{
                      background: result.total_return > 0
                        ? 'linear-gradient(135deg, rgba(0, 255, 170, 0.2) 0%, rgba(0, 200, 140, 0.1) 100%)'
                        : 'linear-gradient(135deg, rgba(255, 0, 85, 0.2) 0%, rgba(200, 0, 70, 0.1) 100%)',
                      color: getReturnColor(result.total_return),
                      border: `1px solid ${getReturnColor(result.total_return)}40`,
                      fontWeight: 700,
                      fontFamily: '"JetBrains Mono", monospace',
                    }}
                  />
                </TableCell>
                <TableCell
                  align="right"
                  sx={{
                    color: getReturnColor(result.win_rate),
                    fontWeight: 600,
                    fontFamily: '"JetBrains Mono", monospace',
                  }}
                >
                  {formatPercent(result.win_rate)}
                </TableCell>
                <TableCell
                  align="right"
                  sx={{
                    color: '#ff0055',
                    fontWeight: 600,
                    fontFamily: '"JetBrains Mono", monospace',
                  }}
                >
                  {formatPercent(result.max_drawdown)}
                </TableCell>
                <TableCell
                  align="right"
                  sx={{
                    color: result.sharpe_ratio > 1 ? '#00ffaa' : '#b0b0b0',
                    fontWeight: 600,
                    fontFamily: '"JetBrains Mono", monospace',
                  }}
                >
                  {result.sharpe_ratio.toFixed(2)}
                </TableCell>
                <TableCell
                  align="right"
                  sx={{
                    color: '#b0b0b0',
                    fontWeight: 600,
                    fontFamily: '"JetBrains Mono", monospace',
                  }}
                >
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
