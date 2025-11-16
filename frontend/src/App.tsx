import { useState } from 'react';
import { Container, Box, Typography, Paper } from '@mui/material';
import ControlPanel from './components/ControlPanel';
import SummaryCards from './components/SummaryCards';
import VisualizationPanel from './components/VisualizationPanel';
import ResultsTable from './components/ResultsTable';
import StrategyDrilldown from './components/StrategyDrilldown';
import { BacktestResponse, StrategyResult } from './types';

function App() {
  const [backtestData, setBacktestData] = useState<BacktestResponse | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleBacktestComplete = (data: BacktestResponse) => {
    setBacktestData(data);
  };

  const handleStrategyClick = (strategy: StrategyResult) => {
    setSelectedStrategy(strategy);
  };

  const handleCloseModal = () => {
    setSelectedStrategy(null);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        <Paper elevation={3} sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
          <Typography variant="h3" component="h1" gutterBottom sx={{ color: 'white', fontWeight: 'bold' }}>
            The Strategy Matrix v3.0
          </Typography>
          <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.9)' }}>
            Test 35 strategies with advanced visualization and analytics
          </Typography>
        </Paper>

        <ControlPanel onBacktestComplete={handleBacktestComplete} setIsLoading={setIsLoading} />

        {isLoading && (
          <Paper sx={{ p: 3, mt: 3, textAlign: 'center' }}>
            <Typography variant="h6">Running backtest...</Typography>
          </Paper>
        )}

        {backtestData && !isLoading && (
          <Box sx={{ mt: 3 }}>
            <SummaryCards
              results={backtestData.results}
              ticker={backtestData.ticker}
            />

            <VisualizationPanel results={backtestData.results} />

            <ResultsTable
              results={backtestData.results}
              onStrategyClick={handleStrategyClick}
            />
          </Box>
        )}

        {selectedStrategy && backtestData && (
          <StrategyDrilldown
            open={!!selectedStrategy}
            onClose={handleCloseModal}
            strategy={selectedStrategy}
            priceData={backtestData.price_data}
            ticker={backtestData.ticker}
          />
        )}
      </Box>
    </Container>
  );
}

export default App;
