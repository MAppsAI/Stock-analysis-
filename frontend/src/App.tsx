import { useState } from 'react';
import { Container, Box, Typography, Paper, Tabs, Tab } from '@mui/material';
import ControlPanel from './components/ControlPanel';
import SummaryCards from './components/SummaryCards';
import VisualizationPanel from './components/VisualizationPanel';
import ResultsTable from './components/ResultsTable';
import StrategyDrilldown from './components/StrategyDrilldown';
import OptimizationPanel from './components/OptimizationPanel';
import { BacktestResponse, StrategyResult, OptimizationResponse } from './types';

function App() {
  const [backtestData, setBacktestData] = useState<BacktestResponse | null>(null);
  const [optimizationData, setOptimizationData] = useState<OptimizationResponse | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  const handleBacktestComplete = (data: BacktestResponse) => {
    setBacktestData(data);
    setOptimizationData(null);
    setActiveTab(0);
  };

  const handleOptimizationComplete = (data: OptimizationResponse) => {
    setOptimizationData(data);
    setBacktestData(null);
    setActiveTab(1);
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
            The Strategy Matrix v3.5
          </Typography>
          <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.9)' }}>
            Test 35 strategies with advanced visualization, analytics, and hyperparameter optimization
          </Typography>
        </Paper>

        <ControlPanel
          onBacktestComplete={handleBacktestComplete}
          onOptimizationComplete={handleOptimizationComplete}
          setIsLoading={setIsLoading}
        />

        {isLoading && (
          <Paper sx={{ p: 3, mt: 3, textAlign: 'center' }}>
            <Typography variant="h6">
              {activeTab === 1 ? 'Running optimization...' : 'Running backtest...'}
            </Typography>
          </Paper>
        )}

        {(backtestData || optimizationData) && !isLoading && (
          <Box sx={{ mt: 3 }}>
            <Paper sx={{ mb: 3 }}>
              <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
                <Tab label="Backtest Results" disabled={!backtestData} />
                <Tab label="Optimization Results" disabled={!optimizationData} />
              </Tabs>
            </Paper>

            {activeTab === 0 && backtestData && (
              <Box>
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

            {activeTab === 1 && optimizationData && (
              <OptimizationPanel optimizationData={optimizationData} />
            )}
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
