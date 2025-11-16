import {
  Paper,
  Typography,
  Box,
  Chip,
} from '@mui/material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { WeightSnapshot } from '../types';

interface AssetAllocationChartProps {
  weightsTimeline: WeightSnapshot[];
  tickers: string[];
}

// Generate distinct colors for each asset
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#a4de6c',
  '#d0ed57', '#83a6ed', '#8dd1e1', '#d084d0', '#ffbb28',
  '#ff8042', '#00C49F', '#FFBB28', '#FF8042', '#0088FE'
];

export default function AssetAllocationChart({
  weightsTimeline,
  tickers
}: AssetAllocationChartProps) {
  // Transform data for stacked area chart
  const chartData = weightsTimeline.map(snapshot => {
    const dataPoint: any = {
      date: new Date(snapshot.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      fullDate: snapshot.date,
      rebalance: snapshot.rebalance || false,
    };

    // Add weight for each ticker (as percentage)
    tickers.forEach(ticker => {
      dataPoint[ticker] = (snapshot.weights[ticker] || 0) * 100;
    });

    return dataPoint;
  });

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const isRebalance = payload[0]?.payload?.rebalance;

      return (
        <Box
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #ccc',
            borderRadius: 1,
            p: 1.5,
            boxShadow: 2,
          }}
        >
          <Typography variant="subtitle2" gutterBottom>
            {label}
            {isRebalance && (
              <Chip
                label="Rebalance"
                size="small"
                color="warning"
                sx={{ ml: 1 }}
              />
            )}
          </Typography>
          {payload.map((entry: any, index: number) => (
            <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  backgroundColor: entry.color,
                  borderRadius: '2px',
                }}
              />
              <Typography variant="body2">
                {entry.name}: {entry.value?.toFixed(2)}%
              </Typography>
            </Box>
          ))}
        </Box>
      );
    }
    return null;
  };

  // Find rebalance dates for reference lines
  const rebalanceDates = weightsTimeline
    .filter(snapshot => snapshot.rebalance)
    .map(snapshot => snapshot.date);

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Portfolio Composition Over Time
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Stacked area chart showing portfolio weight allocation across assets.
        {rebalanceDates.length > 0 && ` ${rebalanceDates.length} rebalancing events marked.`}
      </Typography>

      <ResponsiveContainer width="100%" height={400}>
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          stackOffset="expand"
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="square"
          />

          {/* Add reference lines for rebalancing events */}
          {rebalanceDates.map((date, idx) => {
            const dataIndex = chartData.findIndex(d => d.fullDate === date);
            if (dataIndex >= 0) {
              return (
                <ReferenceLine
                  key={idx}
                  x={chartData[dataIndex].date}
                  stroke="orange"
                  strokeDasharray="3 3"
                  strokeWidth={2}
                  label={{
                    value: 'Rebalance',
                    position: 'top',
                    fontSize: 10,
                    fill: 'orange'
                  }}
                />
              );
            }
            return null;
          })}

          {/* Create stacked areas for each ticker */}
          {tickers.map((ticker, index) => (
            <Area
              key={ticker}
              type="monotone"
              dataKey={ticker}
              stackId="1"
              stroke={COLORS[index % COLORS.length]}
              fill={COLORS[index % COLORS.length]}
              fillOpacity={0.7}
              name={ticker}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>

      {/* Summary stats */}
      <Box sx={{ mt: 3, display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        <Box>
          <Typography variant="caption" color="text.secondary">
            Timeline Points
          </Typography>
          <Typography variant="h6">
            {weightsTimeline.length}
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary">
            Rebalancing Events
          </Typography>
          <Typography variant="h6">
            {rebalanceDates.length}
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary">
            Assets in Portfolio
          </Typography>
          <Typography variant="h6">
            {tickers.length}
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
}
