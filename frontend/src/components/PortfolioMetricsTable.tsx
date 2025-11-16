import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material';
import { ExpandMore } from '@mui/icons-material';
import { PortfolioStrategyResult } from '../types';

interface PortfolioMetricsTableProps {
  results: PortfolioStrategyResult[];
  buyHoldResult?: PortfolioStrategyResult;
}

export default function PortfolioMetricsTable({
  results,
  buyHoldResult
}: PortfolioMetricsTableProps) {
  const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`;
  const formatNumber = (value: number) => value.toFixed(2);

  const allResults = buyHoldResult ? [buyHoldResult, ...results] : results;

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Portfolio Strategy Results
      </Typography>

      {/* Portfolio-Level Metrics */}
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Strategy</strong></TableCell>
              <TableCell align="right"><strong>Total Return</strong></TableCell>
              <TableCell align="right"><strong>Annual Return</strong></TableCell>
              <TableCell align="right"><strong>Volatility</strong></TableCell>
              <TableCell align="right"><strong>Sharpe Ratio</strong></TableCell>
              <TableCell align="right"><strong>Max Drawdown</strong></TableCell>
              <TableCell align="right"><strong>Rebalances</strong></TableCell>
              <TableCell align="right"><strong>Diversification</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {allResults.map((result, index) => {
              const isBuyHold = index === 0 && buyHoldResult;
              const metrics = result.portfolio_metrics;

              return (
                <TableRow
                  key={result.strategy}
                  sx={{
                    backgroundColor: isBuyHold ? 'action.hover' : 'inherit',
                  }}
                >
                  <TableCell>
                    {result.strategy}
                    {isBuyHold && (
                      <Chip label="Baseline" size="small" sx={{ ml: 1 }} />
                    )}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      color: metrics.total_return >= 0 ? 'success.main' : 'error.main',
                      fontWeight: 'bold',
                    }}
                  >
                    {formatPercent(metrics.total_return)}
                  </TableCell>
                  <TableCell align="right">
                    {formatPercent(metrics.annualized_return)}
                  </TableCell>
                  <TableCell align="right">
                    {formatPercent(metrics.volatility)}
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                    {formatNumber(metrics.sharpe_ratio)}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ color: 'error.main' }}
                  >
                    {formatPercent(metrics.max_drawdown)}
                  </TableCell>
                  <TableCell align="right">
                    {metrics.num_rebalances}
                  </TableCell>
                  <TableCell align="right">
                    {formatNumber(metrics.diversification_ratio)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Asset-Level Metrics (Expandable) */}
      <Box sx={{ mt: 3 }}>
        {allResults.map((result) => (
          <Accordion key={result.strategy}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography>
                {result.strategy} - Asset Breakdown
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Asset</strong></TableCell>
                      <TableCell align="right"><strong>Weight</strong></TableCell>
                      <TableCell align="right"><strong>Return</strong></TableCell>
                      <TableCell align="right"><strong>Contribution</strong></TableCell>
                      <TableCell align="right"><strong>Volatility</strong></TableCell>
                      <TableCell align="right"><strong>Sharpe</strong></TableCell>
                      <TableCell align="right"><strong>Max DD</strong></TableCell>
                      <TableCell align="right"><strong>Win Rate</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.asset_metrics.map((asset) => (
                      <TableRow key={asset.ticker}>
                        <TableCell>
                          <Chip label={asset.ticker} size="small" color="primary" variant="outlined" />
                        </TableCell>
                        <TableCell align="right">
                          {formatPercent(asset.weight)}
                        </TableCell>
                        <TableCell
                          align="right"
                          sx={{
                            color: asset.total_return >= 0 ? 'success.main' : 'error.main',
                          }}
                        >
                          {formatPercent(asset.total_return)}
                        </TableCell>
                        <TableCell align="right">
                          {formatPercent(asset.contribution_to_return)}
                        </TableCell>
                        <TableCell align="right">
                          {formatPercent(asset.volatility)}
                        </TableCell>
                        <TableCell align="right">
                          {formatNumber(asset.sharpe_ratio)}
                        </TableCell>
                        <TableCell align="right" sx={{ color: 'error.main' }}>
                          {formatPercent(asset.max_drawdown)}
                        </TableCell>
                        <TableCell align="right">
                          {formatPercent(asset.win_rate)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Additional Info */}
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Rebalancing: {result.portfolio_metrics.num_rebalances} times
                  {result.portfolio_metrics.num_rebalances > 0 && (
                    <> | Avg Turnover: {formatPercent(result.portfolio_metrics.turnover)}</>
                  )}
                </Typography>
              </Box>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    </Paper>
  );
}
