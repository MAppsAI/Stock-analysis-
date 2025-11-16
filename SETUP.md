# Stock Analysis - Setup Guide

This guide will help you set up and run the Stock Analysis application (v1.0 - The Core Pipeline).

## Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn

## Project Structure

```
Stock-analysis-/
├── backend/          # Python FastAPI backend
│   ├── main.py       # API server
│   ├── models.py     # Pydantic models
│   ├── strategies.py # Trading strategies
│   └── requirements.txt
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── api.ts
│   │   └── types.ts
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the backend server:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - OpenAPI Schema: `http://localhost:8000/openapi.json`

## Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file (optional):
   ```bash
   cp .env.example .env
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:3000`

## Using the Application

1. Make sure both backend and frontend servers are running
2. Open your browser to `http://localhost:3000`
3. Enter a stock ticker (e.g., AAPL, MSFT, GOOGL)
4. Select a date range for backtesting
5. Choose strategies to test (currently: SMA 50/200 Cross)
6. Click "Run Backtest"
7. View results in the table
8. Click any strategy row to see the candlestick chart with buy/sell signals

## Current Features (v1.0)

- **Single Strategy**: SMA 50/200 Crossover (Golden Cross/Death Cross)
- **Interactive Results Table**: Sortable by all metrics
- **Strategy Drilldown Modal**:
  - Candlestick chart with price data
  - Buy/sell signal markers overlaid on the chart
  - Detailed performance metrics
  - List of all trade signals
- **Performance Metrics**:
  - Total Return %
  - Win Rate %
  - Maximum Drawdown %
  - Sharpe Ratio
  - Number of Trades

## API Endpoints

- `GET /` - API health check
- `GET /api/v1/strategies` - List available strategies
- `POST /api/v1/backtest` - Run backtest
  ```json
  {
    "ticker": "AAPL",
    "startDate": "2022-01-01",
    "endDate": "2023-12-31",
    "strategies": ["sma_cross"]
  }
  ```

## Troubleshooting

### Backend Issues

- **Import errors**: Make sure virtual environment is activated and all dependencies are installed
- **Port 8000 already in use**: Change the port in `backend/main.py` (line: `uvicorn.run(app, host="0.0.0.0", port=8000)`)

### Frontend Issues

- **CORS errors**: Ensure backend is running on port 8000, or update `VITE_API_URL` in `.env`
- **Module not found**: Delete `node_modules` and `package-lock.json`, then run `npm install` again
- **Port 3000 already in use**: Update port in `frontend/vite.config.ts`

## Next Steps (Roadmap)

- **v2.0**: Expand to 25 strategies, full filtering and sorting
- **v3.0**: Scale to 100+ strategies, add visualization panel with charts and heatmaps
- **v4.0**: User accounts, strategy combinations, crypto/forex support

## Technology Stack

- **Backend**: Python, FastAPI, yfinance, pandas, numpy
- **Frontend**: React, TypeScript, Vite, Material-UI, TanStack Query, Lightweight Charts
- **Backtesting**: Custom vectorized implementation (future: vectorbt integration)
