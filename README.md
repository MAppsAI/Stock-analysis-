# Stock-analysis-
100 ways to analyze a stock

## Project: The Strategy Matrix
An interactive analysis platform for discovering the "strategy-to-stock fit" in real-time.

## 🚀 Quick Start

**[See SETUP.md for detailed installation and usage instructions](./SETUP.md)**

```bash
# Backend (Terminal 1)
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend (Terminal 2)
cd frontend
npm install
npm run dev
```

Then open `http://localhost:3000` in your browser.

## ✅ Implementation Status

**v1.0 (The Core Pipeline) - COMPLETED** ✓
- ✓ FastAPI backend with SMA 50/200 Cross strategy
- ✓ React frontend with TypeScript and Vite
- ✓ End-to-end flow: Ticker → API → Backtest → JSON → Display
- ✓ Interactive ResultsTable with sorting
- ✓ StrategyDrilldown modal with candlestick chart and buy/sell signals
- ✓ Performance metrics: Total Return, Win Rate, Max Drawdown, Sharpe Ratio, # of Trades

**v2.0 (The MVP Dashboard) - COMPLETED** ✓
- ✓ Expanded Strategy Library to 25 strategies across 5 categories:
  - **Trend-Following (8)**: SMA crosses, EMA, MACD, Triple MA, Donchian, ADX, Trend Channel
  - **Mean-Reversion (6)**: RSI, Bollinger Bands, Mean Reversion, Stochastic, CCI, Williams %R
  - **Momentum (5)**: ROC, RSI Momentum, 52-Week Breakout, MA Momentum, Price Momentum
  - **Volatility (3)**: ATR Breakout, Bollinger Squeeze, Keltner Channel
  - **Volume (3)**: Volume Breakout, OBV, Volume Price Trend
- ✓ Strategy categories for organized selection
- ✓ Comprehensive testing suite with SPY backtest results
- ✓ Proven performance: 14/25 strategies profitable over 10 years

**10-Year SPY Test Results (Best Performers)**:
1. 🏆 52-Week High Breakout: +317.16% (Sharpe: 1.04)
2. 📈 SMA 50/200 Cross: +203.54% (Sharpe: 0.81)
3. 📊 EMA 12/26 Cross: +127.15% (Sharpe: 0.60)

**Next: v3.0 (The 100-Strategy Platform)** - Planned
- Scale library to 100+ strategies
- Add VisualizationPanel (bar charts, heatmaps)
- Optimize for sub-minute response times

---
1. The Vision
The internet is flooded with trading strategies. The problem is, a strategy that works for a stable utility stock will fail miserably on a volatile tech stock.
This application is the solution.
It's not just a script; it's an interactive analysis dashboard. It empowers a user to pick any stock, and in seconds, discover which of 100+ technical strategies actually would have worked for that specific asset. It's a "search engine" for finding what works.
2. The Problem It Solves
 * Eliminates Guesswork: No more "I think RSI works on this." You can know by seeing the data.
 * Filters Noise: Out of 100 strategies, 90 will be noise. This tool finds the 10 signals that matter.
 * Saves Time: What would take an analyst weeks of manual testing, this app does in under a minute.
 * Provides Visual Proof: It doesn't just give you a number. It shows you the buy/sell signals on a chart.
3. The Application: A Feature Breakdown
This is a client-server application composed of a powerful Python backend and a data-rich React frontend.
Frontend: The React Dashboard
This is where the user lives. It's a single-page application (SPA) focused on interactivity and data visualization.
 * ControlPanel Component:
   * Smart Ticker Input: An auto-completing search bar for any stock.
   * Date Range Picker: To define the backtest period.
   * Strategy Filtering: A key feature. A multi-select dropdown to filter the 100+ strategies by category (e.g., "All Trend-Following," "All Mean-Reversion") or to select them individually.
 * ResultsDashboard Component:
   * SummaryCards: High-level metrics post-analysis (e.g., "Best Strategy: SMA 50/200 Cross," "Total Profitable Strategies: 32/100").
   * ResultsTable (The Core): A professional-grade data grid (e.g., using AG Grid or React Table) displaying all selected strategies as rows.
     * Columns: Strategy | Total Return % | Win Rate | Max Drawdown | Sharpe Ratio | # of Trades.
     * Interactivity: This table is fully sortable (click any column to rank) and filterable (e.g., "show me only strategies with >10% return").
 * VisualizationPanel Component:
   * Top 10 Chart: A Recharts bar chart showing the "Top 10 Best-Performing Strategies" and their returns.
   * Strategy Heatmap: A visual grid showing performance across different metrics, providing a quick, color-coded overview.
 * StrategyDrilldown (The "Killer Feature"):
   * When a user clicks any strategy in the ResultsTable, a modal (pop-up) appears.
   * This modal contains a Candlestick Chart (using Lightweight Charts) of the stock's price.
   * Crucially, it overlays the exact buy/sell signals for that one strategy as markers on the chart.
   * This provides instant visual validation, allowing the user to see why a strategy won or lost.
Backend: The Python API
The "headless" engine that does all the heavy lifting. Its only job is to receive a request and return a large JSON object.
 * High-Speed Backtesting Engine: Built in Python, using libraries like vectorbt or backtrader for extremely fast, vectorized backtesting.
 * The Strategy Library: A folder containing 100+ independent, testable Python functions, each representing a single trading strategy.
 * The API: A FastAPI (or Flask) server that exposes a single endpoint: POST /api/v1/backtest.
   * Request: { "ticker": "AAPL", "startDate": "...", "endDate": "...", "strategies": ["sma_cross", "rsi_oversold"] }
   * Response: A large JSON array with the full results and chartable trade data for every strategy.
4. Proposed Tech Stack
| Component | Technology | Why? |
|---|---|---|
| Frontend | React (Vite) + TypeScript | Modern, fast, and type-safe for a complex data app. |
| UI Components | MUI or Chakra UI | Professional, pre-built components to move fast. |
| Data Fetching | React Query (TanStack Query) | Handles caching, loading, and error states flawlessly. |
| Data Grids | React Table or AG Grid | Required for the interactive, sortable, filterable results. |
| Charts | Recharts & Lightweight Charts | Recharts for stats, Lightweight Charts for financial data. |
| Backend API | Python (FastAPI) | Extremely fast, modern, and easy to build APIs. |
| Backtesting | vectorbt | Natively built for vectorized (i.e., extremely fast) analysis. |
| Data Source | yfinance | Free, reliable access to historical stock data. |
5. Roadmap
 * v1.0 (The Core Pipeline):
   * Build the FastAPI backend with one single strategy (e.g., "SMA 50/200 Cross").
   * Build the core React app.
   * Prove the end-to-end flow: Ticker -> API -> Backtest -> JSON -> Display in a simple table.
   * Goal: Get the StrategyDrilldown modal working with the chart and buy/sell signals. This is the #1 priority.
 * v2.0 (The MVP Dashboard):
   * Expand the Strategy Library to 25 core strategies.
   * Implement the full ResultsTable with sorting and filtering.
   * Implement the ControlPanel with date and strategy selection.
 * v3.0 (The 100-Strategy Platform):
   * Scale the library to 100+ strategies.
   * Implement the VisualizationPanel (bar charts, heatmaps).
   * Aggressively optimize the backend for sub-minute response times, even with 100+ strategies.
 * v4.0 (Future):
   * User accounts to save "favorite" strategies per ticker.
   * Allow users to combine strategies (e.This AND That").
   * Expand to crypto and forex markets.
   
