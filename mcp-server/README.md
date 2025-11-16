# Stock Analysis MCP Server

A Model Context Protocol (MCP) server that wraps the Stock Analysis backend APIs, providing LLM-friendly tools for stock backtesting, portfolio analysis, and strategy optimization.

## Features

- **203+ Trading Strategies**: Access to single-asset strategies including trend-following, mean-reversion, momentum, volatility, and volume-based strategies
- **9 Portfolio Strategies**: Multi-asset portfolio optimization including equal-weight, sector rotation, risk parity, mean-variance optimization, HRP, Black-Litterman, and CVaR
- **Strategy Optimization**: Hyperparameter optimization with parallel processing
- **Portfolio Analysis**: Correlation matrices, rebalancing, transaction costs, and tax-aware analysis
- **History Management**: Save, retrieve, and manage analysis results
- **LLM-Friendly Output**: All responses are formatted for easy consumption by language models

## Architecture

The MCP server acts as a wrapper layer that:
1. Receives tool calls from LLM clients
2. Translates them to backend API calls
3. Formats responses in an LLM-friendly manner
4. Returns both human-readable summaries and full JSON data

```
┌─────────────┐
│  LLM Client │
│  (Claude)   │
└──────┬──────┘
       │ MCP Protocol
       │
┌──────▼──────┐
│ MCP Server  │
│  (Port N/A) │
└──────┬──────┘
       │ HTTP/REST
       │
┌──────▼──────┐
│   Backend   │
│  (Port 8000)│
└─────────────┘
```

## Available MCP Tools

### Single-Asset Analysis

1. **list_strategies** - Get all 203+ available trading strategies
2. **backtest_stock** - Backtest strategies on a single stock
3. **optimize_strategies** - Find optimal parameters for strategies

### Portfolio Analysis

4. **list_portfolio_strategies** - Get all 9 portfolio strategies
5. **backtest_portfolio** - Backtest multi-asset portfolios
6. **calculate_correlation** - Calculate correlation and covariance matrices

### History Management

7. **save_analysis** - Save backtest/optimization results
8. **list_history** - List saved analyses
9. **get_history** - Retrieve saved analysis by ID
10. **delete_history** - Delete saved analysis

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed
- Backend API running on port 8000 (or configured URL)

### Option 1: Docker Compose (Recommended)

Run both the backend and MCP server together:

```bash
# From the root directory of the project
docker-compose up -d

# Check logs
docker-compose logs -f mcp-server
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Option 2: Docker Run (MCP Server Only)

If the backend is already running elsewhere:

```bash
# Build the image
cd mcp-server
docker build -t stock-analysis-mcp .

# Run with default backend URL (http://localhost:8000)
docker run -it --rm \
  -e BACKEND_API_URL=http://host.docker.internal:8000 \
  stock-analysis-mcp

# Or with custom backend URL
docker run -it --rm \
  -e BACKEND_API_URL=http://your-backend:8000 \
  stock-analysis-mcp
```

## Manual Setup (Without Docker)

### Prerequisites

- Python 3.11+
- Backend API running

### Installation

```bash
cd mcp-server

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set BACKEND_API_URL if different from default

# Run the server
python server.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_API_URL` | Backend API base URL | `http://localhost:8000` |

### Docker Networking

When running with docker-compose:
- Backend is accessible at `http://backend:8000` from the MCP server
- Backend is accessible at `http://localhost:8000` from the host

When running MCP server separately:
- Use `http://host.docker.internal:8000` to access backend on host machine (Mac/Windows)
- Use `http://172.17.0.1:8000` for Linux hosts

## Using with Claude Desktop

Add this to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "BACKEND_API_URL=http://host.docker.internal:8000",
        "stock-analysis-mcp"
      ]
    }
  }
}
```

Or if running without Docker:

```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "python",
      "args": ["/path/to/Stock-analysis-/mcp-server/server.py"],
      "env": {
        "BACKEND_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Example Usage

### Example 1: List and Backtest Strategies

**User:** What trading strategies are available?

**MCP Server:** Uses `list_strategies` tool and returns categorized list of 203+ strategies.

**User:** Backtest Apple stock with SMA crossover and RSI strategies from 2020 to 2023.

**MCP Server:** Uses `backtest_stock` tool with:
- ticker: "AAPL"
- start_date: "2020-01-01"
- end_date: "2023-12-31"
- strategies: ["sma_50_200_cross", "rsi_oversold_overbought"]

Returns performance metrics, trade signals, and comparison to buy-and-hold.

### Example 2: Portfolio Analysis

**User:** Create a portfolio with AAPL, MSFT, and GOOGL. Show me the correlation matrix.

**MCP Server:** Uses `calculate_correlation` tool to analyze asset relationships.

**User:** Now backtest this portfolio using risk parity and mean-variance optimization from 2021 to 2023.

**MCP Server:** Uses `backtest_portfolio` tool with portfolio strategies.

### Example 3: Strategy Optimization

**User:** Optimize the RSI strategy for SPY over the past 3 years.

**MCP Server:** Uses `optimize_strategies` tool to find best RSI parameters (period, oversold/overbought thresholds) that maximize Sharpe ratio.

## Tool Details

### list_strategies

Returns all available single-asset trading strategies grouped by category.

**Parameters:** None

**Returns:** Markdown-formatted list with strategy IDs, names, and categories.

### backtest_stock

Run backtests on a stock with selected strategies.

**Parameters:**
- `ticker` (string): Stock ticker symbol
- `start_date` (string): YYYY-MM-DD format
- `end_date` (string): YYYY-MM-DD format
- `strategies` (array): List of strategy IDs

**Returns:**
- Human-readable summary with top performers
- Full JSON data with metrics, signals, equity curves

**Key Metrics:**
- Total Return (%)
- Sharpe Ratio (risk-adjusted return)
- Win Rate (%)
- Max Drawdown (%)
- Number of Trades
- Trade Signals (buy/sell with dates and prices)
- Equity Curve (portfolio value over time)

### optimize_strategies

Find optimal parameters for strategies.

**Parameters:**
- `ticker` (string): Stock ticker symbol
- `start_date` (string): YYYY-MM-DD format
- `end_date` (string): YYYY-MM-DD format
- `strategies` (array): List of strategy IDs to optimize

**Returns:**
- Best parameters for each strategy
- Performance comparison
- Number of combinations tested

### list_portfolio_strategies

Returns all available multi-asset portfolio strategies.

**Parameters:** None

**Returns:** List of 9 portfolio strategies with descriptions and parameters.

### backtest_portfolio

Run portfolio backtests with multiple assets.

**Parameters:**
- `tickers` (array): List of ticker symbols
- `start_date` (string): YYYY-MM-DD format
- `end_date` (string): YYYY-MM-DD format
- `strategies` (array): Portfolio strategy IDs
- `allocation_method` (string, optional): "equal", "market_cap", "optimized", "custom"
- `custom_weights` (object, optional): Custom weights per ticker
- `rebalancing` (string, optional): "none", "monthly", "quarterly", "threshold"
- `rebalance_threshold` (number, optional): Weight drift % for rebalancing
- `transaction_cost` (number, optional): Per-trade cost as decimal

**Returns:**
- Portfolio-level metrics (return, volatility, Sharpe, drawdown)
- Asset-level performance
- Rebalancing history
- Transaction costs and tax impact

### calculate_correlation

Calculate correlation and covariance matrices.

**Parameters:**
- `tickers` (array): List of ticker symbols
- `start_date` (string): YYYY-MM-DD format
- `end_date` (string): YYYY-MM-DD format

**Returns:**
- Correlation matrix (table format)
- Covariance matrix
- Individual asset volatilities

### save_analysis

Save backtest or optimization results to history.

**Parameters:**
- `ticker` (string): Ticker or portfolio description
- `start_date` (string): YYYY-MM-DD format
- `end_date` (string): YYYY-MM-DD format
- `run_type` (string): "backtest" or "optimization"
- `results_data` (object): Full results from analysis
- `title` (string, optional): Custom title

**Returns:** Confirmation with saved ID

### list_history

List saved analyses with optional filtering.

**Parameters:**
- `ticker` (string, optional): Filter by ticker
- `limit` (number, optional): Results per page (default: 100)
- `offset` (number, optional): Pagination offset (default: 0)

**Returns:** List of saved analyses with metadata

### get_history

Retrieve full details of a saved analysis.

**Parameters:**
- `history_id` (number): ID of the history entry

**Returns:** Complete analysis data including results

### delete_history

Delete a saved analysis.

**Parameters:**
- `history_id` (number): ID of the history entry

**Returns:** Confirmation message

## Development

### Project Structure

```
mcp-server/
├── server.py           # Main MCP server implementation
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker image definition
├── .env.example       # Environment variable template
└── README.md          # This file
```

### Adding New Tools

To add a new tool:

1. Add tool definition to `list_tools()` function
2. Implement tool handler in `call_tool()` function
3. Add helper formatting functions if needed
4. Update README documentation

### Testing

```bash
# Start the backend
cd backend
uvicorn main:app --reload

# In another terminal, test the MCP server
cd mcp-server
python server.py
```

## Troubleshooting

### Backend Connection Issues

**Error:** `Connection refused` or `Cannot connect to backend`

**Solutions:**
- Ensure backend is running on the configured URL
- Check `BACKEND_API_URL` environment variable
- For Docker: Use `http://backend:8000` or `http://host.docker.internal:8000`

### Docker Networking Issues

**Error:** `MCP server can't reach backend in Docker`

**Solutions:**
- Use `docker-compose` for automatic networking
- Check that both containers are on the same network
- Verify backend health: `docker-compose logs backend`

### Missing Data

**Error:** `No data available for ticker`

**Solutions:**
- Check internet connection (yfinance needs internet)
- Verify ticker symbol is correct
- Try a different date range
- Some tickers may not have data for certain periods

## Performance Considerations

- **Optimization**: Can take 1-5 minutes depending on parameter combinations
- **Portfolio Backtests**: ~10-30 seconds for 3-5 assets
- **Single Backtests**: ~2-5 seconds per strategy
- **Concurrent Requests**: Backend supports async processing

## Security Notes

- MCP server connects to backend via HTTP (consider HTTPS in production)
- No authentication implemented (add if deploying publicly)
- Docker containers run with default security settings
- Database stored in Docker volume (backed up separately if needed)

## License

Same as the main Stock Analysis project.

## Support

For issues or questions:
1. Check backend logs: `docker-compose logs backend`
2. Check MCP server logs: `docker-compose logs mcp-server`
3. Verify API is accessible: `curl http://localhost:8000/`
4. Review this README for configuration