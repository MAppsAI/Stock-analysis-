import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts';
import { OptimizationResponse, OptimizationResult } from '../types';

interface OptimizationPanelProps {
  optimizationData: OptimizationResponse;
}

export default function OptimizationPanel({ optimizationData }: OptimizationPanelProps) {
  const { optimization_results, summary } = optimizationData;

  // Prepare data for improvement chart
  const improvementData = Object.entries(optimization_results)
    .filter(([_, result]) => result.status === 'success' && result.best_metrics)
    .map(([strategyType, result]) => ({
      strategy: strategyType.replace(/_/g, ' ').toUpperCase(),
      improvement: result.best_score || 0,
      return: result.best_metrics?.total_return || 0,
      sharpe: result.best_metrics?.sharpe_ratio || 0,
    }))
    .sort((a, b) => b.improvement - a.improvement);

  // Prepare parameter heatmap data for scatter visualization
  const getParameterScatterData = (result: OptimizationResult) => {
    if (!result.all_results || result.all_results.length === 0) return [];

    return result.all_results.slice(0, 50).map((r: any) => ({
      x: Object.values(r.params)[0] as number,
      y: r.score,
      params: r.params,
    }));
  };

  const getScoreColor = (score: number): string => {
    if (score > 100) return '#4caf50';
    if (score > 50) return '#8bc34a';
    if (score > 0) return '#ff9800';
    return '#f44336';
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 2, backgroundColor: 'rgba(0, 0, 0, 0.9)' }}>
          <Typography variant="body2" sx={{ color: 'white', fontWeight: 'bold' }}>
            {payload[0].payload.strategy}
          </Typography>
          <Typography variant="body2" sx={{ color: '#4caf50' }}>
            Improvement Score: {payload[0].value.toFixed(2)}
          </Typography>
          <Typography variant="body2" sx={{ color: '#2196f3' }}>
            Total Return: {payload[0].payload.return.toFixed(2)}%
          </Typography>
          <Typography variant="body2" sx={{ color: '#ff9800' }}>
            Sharpe Ratio: {payload[0].payload.sharpe.toFixed(2)}
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 1 }}>
                Strategies Optimized
              </Typography>
              <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>
                {summary.total_optimized || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 1 }}>
                Avg Improvement
              </Typography>
              <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>
                {summary.avg_improvement ? summary.avg_improvement.toFixed(1) : '0'}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 1 }}>
                Best Strategy
              </Typography>
              <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                {summary.best_strategy_type?.replace(/_/g, ' ') || 'N/A'}
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                Score: {summary.best_score?.toFixed(2) || '0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 1 }}>
                Parameters Tested
              </Typography>
              <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>
                {summary.total_combinations || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Improvement Chart */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Optimization Improvement Scores
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Higher scores indicate better optimization results (combining returns and risk-adjusted performance)
        </Typography>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={improvementData} margin={{ top: 20, right: 30, left: 20, bottom: 100 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
            <XAxis
              dataKey="strategy"
              angle={-45}
              textAnchor="end"
              height={120}
              stroke="#888"
            />
            <YAxis stroke="#888" label={{ value: 'Improvement Score', angle: -90, position: 'insideLeft' }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="improvement" name="Optimization Score" radius={[8, 8, 0, 0]}>
              {improvementData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getScoreColor(entry.improvement)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Paper>

      {/* Optimized Parameters Table */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Optimized Parameters
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Strategy</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Best Parameters</strong></TableCell>
                <TableCell align="right"><strong>Total Return</strong></TableCell>
                <TableCell align="right"><strong>Sharpe Ratio</strong></TableCell>
                <TableCell align="right"><strong>Win Rate</strong></TableCell>
                <TableCell align="right"><strong>Tested</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(optimization_results).map(([strategyType, result]) => (
                <TableRow key={strategyType}>
                  <TableCell>{strategyType.replace(/_/g, ' ').toUpperCase()}</TableCell>
                  <TableCell>
                    <Chip
                      label={result.status}
                      color={result.status === 'success' ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {result.best_params ? (
                      <Box>
                        {Object.entries(result.best_params).map(([key, value]) => (
                          <Typography key={key} variant="body2">
                            {key}: <strong>{typeof value === 'object' && value !== null ? JSON.stringify(value) : value}</strong>
                          </Typography>
                        ))}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        {result.message || 'N/A'}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {result.best_metrics?.total_return !== undefined ? (
                      <Typography
                        variant="body2"
                        sx={{
                          color: result.best_metrics.total_return > 0 ? '#4caf50' : '#f44336',
                          fontWeight: 'bold',
                        }}
                      >
                        {result.best_metrics.total_return.toFixed(2)}%
                      </Typography>
                    ) : (
                      'N/A'
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {result.best_metrics?.sharpe_ratio !== undefined
                      ? result.best_metrics.sharpe_ratio.toFixed(2)
                      : 'N/A'}
                  </TableCell>
                  <TableCell align="right">
                    {result.best_metrics?.win_rate !== undefined
                      ? `${result.best_metrics.win_rate.toFixed(1)}%`
                      : 'N/A'}
                  </TableCell>
                  <TableCell align="right">{result.total_tested || 0}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Parameter Performance Scatter Plots */}
      {Object.entries(optimization_results)
        .filter(([_, result]) => result.status === 'success' && result.all_results && result.all_results.length > 0)
        .slice(0, 4)
        .map(([strategyType, result]) => {
          const scatterData = getParameterScatterData(result);
          if (scatterData.length === 0) return null;

          const paramName = Object.keys(result.best_params || {})[0] || 'parameter';

          return (
            <Paper key={strategyType} sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                {strategyType.replace(/_/g, ' ').toUpperCase()} - Parameter Performance
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Showing how different {paramName} values affect optimization score
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis
                    type="number"
                    dataKey="x"
                    name={paramName}
                    stroke="#888"
                    label={{ value: paramName, position: 'insideBottom', offset: -10 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="y"
                    name="score"
                    stroke="#888"
                    label={{ value: 'Score', angle: -90, position: 'insideLeft' }}
                  />
                  <ZAxis range={[50, 200]} />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    content={({ active, payload }: any) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <Paper sx={{ p: 2, backgroundColor: 'rgba(0, 0, 0, 0.9)' }}>
                            <Typography variant="body2" sx={{ color: 'white' }}>
                              {Object.entries(data.params).map(([key, value]: [string, any]) => (
                                <div key={key}>
                                  {key}: {value}
                                </div>
                              ))}
                            </Typography>
                            <Typography variant="body2" sx={{ color: '#4caf50', mt: 1 }}>
                              Score: {data.y.toFixed(2)}
                            </Typography>
                          </Paper>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter data={scatterData} fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </Paper>
          );
        })}
    </Box>
  );
}
