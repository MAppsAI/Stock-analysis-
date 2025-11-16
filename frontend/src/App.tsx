import { useState, useEffect } from 'react';
import { Container, Box, Typography, Paper, Tabs, Tab, CircularProgress } from '@mui/material';
import { Insights } from '@mui/icons-material';
import ControlPanel from './components/ControlPanel';
import SummaryCards from './components/SummaryCards';
import VisualizationPanel from './components/VisualizationPanel';
import ResultsTable from './components/ResultsTable';
import StrategyDrilldown from './components/StrategyDrilldown';
import OptimizationPanel from './components/OptimizationPanel';
import HistoryPanel from './components/HistoryPanel';
import { BacktestResponse, StrategyResult, OptimizationResponse } from './types';
import { api } from './api';

function App() {
  const [backtestData, setBacktestData] = useState<BacktestResponse | null>(null);
  const [optimizationData, setOptimizationData] = useState<OptimizationResponse | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const handleBacktestComplete = async (data: BacktestResponse) => {
    setBacktestData(data);
    setOptimizationData(null);
    setActiveTab(0);

    // Auto-save to history
    try {
      await api.saveHistory({
        ticker: data.ticker,
        start_date: data.startDate,
        end_date: data.endDate,
        run_type: 'backtest',
        results_data: data,
      });
      setHistoryRefreshKey((prev) => prev + 1);
    } catch (error) {
      console.error('Failed to save backtest to history:', error);
    }
  };

  const handleOptimizationComplete = async (data: OptimizationResponse) => {
    setOptimizationData(data);
    setBacktestData(null);
    setActiveTab(1);

    // Auto-save to history
    try {
      await api.saveHistory({
        ticker: data.ticker,
        start_date: data.startDate,
        end_date: data.endDate,
        run_type: 'optimization',
        results_data: data,
      });
      setHistoryRefreshKey((prev) => prev + 1);
    } catch (error) {
      console.error('Failed to save optimization to history:', error);
    }
  };

  const handleLoadFromHistory = (data: BacktestResponse | OptimizationResponse, runType: 'backtest' | 'optimization') => {
    if (runType === 'backtest') {
      setBacktestData(data as BacktestResponse);
      setOptimizationData(null);
      setActiveTab(0);
    } else {
      setOptimizationData(data as OptimizationResponse);
      setBacktestData(null);
      setActiveTab(1);
    }
  };

  const handleStrategyClick = (strategy: StrategyResult) => {
    setSelectedStrategy(strategy);
  };

  const handleCloseModal = () => {
    setSelectedStrategy(null);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      {/* History sidebar */}
      <HistoryPanel
        key={historyRefreshKey}
        onLoadHistory={handleLoadFromHistory}
        onRefresh={() => setHistoryRefreshKey((prev) => prev + 1)}
      />

      {/* Main content */}
      <Container maxWidth="xl" sx={{ flexGrow: 1 }}>
        <Box sx={{ my: 4 }}>
        {/* Elegant header with glassmorphism */}
        <Paper
          elevation={0}
          sx={{
            p: 4,
            mb: 3,
            position: 'relative',
            overflow: 'hidden',
            background: 'linear-gradient(135deg, rgba(0, 255, 255, 0.1) 0%, rgba(0, 200, 200, 0.05) 100%)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(0, 255, 255, 0.2)',
            boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 0 60px rgba(0, 255, 255, 0.05)',
            animation: 'fadeInUp 0.8s ease-out',
            '@keyframes fadeInUp': {
              from: {
                opacity: 0,
                transform: 'translateY(30px)',
              },
              to: {
                opacity: 1,
                transform: 'translateY(0)',
              },
            },
          }}
        >
          {/* Animated glow effect */}
          <Box
            sx={{
              position: 'absolute',
              top: '-50%',
              right: '-10%',
              width: '500px',
              height: '500px',
              background: 'radial-gradient(circle, rgba(0, 255, 255, 0.15) 0%, transparent 70%)',
              filter: 'blur(60px)',
              animation: 'glowPulse 4s ease-in-out infinite',
              pointerEvents: 'none',
            }}
          />

          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Insights sx={{ fontSize: 48, color: '#00ffff' }} />
              <Typography
                variant="h3"
                component="h1"
                sx={{
                  color: '#f5f5f5',
                  fontWeight: 800,
                  letterSpacing: '-0.02em',
                  textShadow: '0 0 20px rgba(0, 255, 255, 0.3)',
                }}
              >
                The Strategy Matrix
              </Typography>
              <Box
                sx={{
                  px: 2,
                  py: 0.5,
                  background: 'rgba(0, 255, 255, 0.2)',
                  border: '1px solid rgba(0, 255, 255, 0.4)',
                  borderRadius: '8px',
                  backdropFilter: 'blur(10px)',
                }}
              >
                <Typography
                  variant="overline"
                  sx={{
                    color: '#00ffff',
                    fontWeight: 700,
                    fontSize: '0.75rem',
                  }}
                >
                  v3.5
                </Typography>
              </Box>
            </Box>
            <Typography
              variant="h6"
              sx={{
                color: 'rgba(245, 245, 245, 0.7)',
                fontWeight: 400,
                maxWidth: '800px',
              }}
            >
              Test 200+ strategies with advanced visualization, analytics, and hyperparameter optimization
            </Typography>
          </Box>
        </Paper>

        {/* Control Panel with staggered animation */}
        <Box
          sx={{
            animation: 'fadeInUp 0.8s ease-out 0.1s backwards',
          }}
        >
          <ControlPanel
            onBacktestComplete={handleBacktestComplete}
            onOptimizationComplete={handleOptimizationComplete}
            setIsLoading={setIsLoading}
          />
        </Box>

        {/* Loading state with elegant spinner */}
        {isLoading && (
          <Paper
            sx={{
              p: 4,
              mt: 3,
              textAlign: 'center',
              animation: 'fadeInUp 0.5s ease-out',
            }}
          >
            <CircularProgress
              size={48}
              thickness={3}
              sx={{
                color: '#00ffff',
                mb: 2,
              }}
            />
            <Typography
              variant="h6"
              sx={{
                color: '#00ffff',
                fontWeight: 600,
              }}
            >
              {activeTab === 1 ? 'Running optimization...' : 'Running backtest...'}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'text.secondary',
                mt: 1,
              }}
            >
              {activeTab === 1
                ? 'Testing parameter combinations across strategies... This may take a few minutes.'
                : 'Analyzing market data and computing metrics'}
            </Typography>
          </Paper>
        )}

        {/* Results section with staggered animations */}
        {(backtestData || optimizationData) && !isLoading && (
          <Box
            sx={{
              mt: 3,
              animation: 'fadeInUp 0.8s ease-out 0.2s backwards',
            }}
          >
            <Paper
              sx={{
                mb: 3,
                overflow: 'hidden',
              }}
            >
              <Tabs
                value={activeTab}
                onChange={(_, newValue) => setActiveTab(newValue)}
                sx={{
                  '& .MuiTabs-indicator': {
                    background: 'linear-gradient(90deg, #00ffff 0%, #00cccc 100%)',
                    height: '3px',
                  },
                }}
              >
                <Tab label="Backtest Results" disabled={!backtestData} />
                <Tab label="Optimization Results" disabled={!optimizationData} />
              </Tabs>
            </Paper>

            {activeTab === 0 && backtestData && (
              <Box>
                <Box sx={{ animation: 'fadeInUp 0.6s ease-out 0.1s backwards' }}>
                  <SummaryCards
                    results={backtestData.results}
                    ticker={backtestData.ticker}
                  />
                </Box>

                <Box sx={{ animation: 'fadeInUp 0.6s ease-out 0.2s backwards' }}>
                  <VisualizationPanel results={backtestData.results} />
                </Box>

                <Box sx={{ animation: 'fadeInUp 0.6s ease-out 0.3s backwards' }}>
                  <ResultsTable
                    results={backtestData.results}
                    buyHoldResult={backtestData.buy_hold_result}
                    onStrategyClick={handleStrategyClick}
                  />
                </Box>
              </Box>
            )}

            {activeTab === 1 && optimizationData && (
              <Box sx={{ animation: 'fadeInUp 0.6s ease-out 0.1s backwards' }}>
                <OptimizationPanel optimizationData={optimizationData} />
              </Box>
            )}
          </Box>
        )}

        {/* Strategy drilldown modal */}
        {selectedStrategy && (backtestData || optimizationData) && (
          <StrategyDrilldown
            open={!!selectedStrategy}
            onClose={handleCloseModal}
            strategy={selectedStrategy}
            priceData={backtestData?.price_data || optimizationData?.price_data || []}
            ticker={backtestData?.ticker || optimizationData?.ticker || ''}
            buyHoldResult={backtestData?.buy_hold_result}
          />
        )}
        </Box>
      </Container>
    </Box>
  );
}

export default App;
