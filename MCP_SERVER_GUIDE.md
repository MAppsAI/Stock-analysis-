# MCP Server Quick Start Guide

This guide will help you set up and use the Model Context Protocol (MCP) server for the Stock Analysis application.

## What is the MCP Server?

The MCP server wraps all the Stock Analysis backend APIs and provides them as LLM-friendly tools. This allows AI assistants like Claude to:
- Backtest trading strategies
- Optimize strategy parameters
- Analyze multi-asset portfolios
- Calculate correlations
- Save and retrieve analysis history

## Quick Start

### Option 1: Docker (Recommended)

**Start both backend and MCP server:**

```bash
# From the project root directory
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**The services will be available at:**
- Backend API: `http://localhost:8000`
- MCP Server: Running in stdio mode (connect via MCP client)

### Option 2: Manual Setup

**Step 1: Start the Backend**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Step 2: Start the MCP Server**

```bash
cd mcp-server
pip install -r requirements.txt
python server.py
```

## Using with Claude Desktop

### Step 1: Build the Docker Image

```bash
cd mcp-server
docker build -t stock-analysis-mcp .
```

### Step 2: Configure Claude Desktop

Add this to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**

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

**For Linux hosts, use:**

```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network=host",
        "-e",
        "BACKEND_API_URL=http://localhost:8000",
        "stock-analysis-mcp"
      ]
    }
  }
}
```

### Step 3: Restart Claude Desktop

Restart Claude Desktop to load the new MCP server configuration.

### Step 4: Verify Connection

In Claude Desktop, you should see a hammer icon (🔨) indicating MCP tools are available. Try asking:

> "What trading strategies are available?"

## Available MCP Tools

### Single-Asset Analysis
1. **list_strategies** - Browse 203+ trading strategies
2. **backtest_stock** - Test strategies on individual stocks
3. **optimize_strategies** - Find optimal strategy parameters

### Portfolio Analysis
4. **list_portfolio_strategies** - Browse 9 portfolio strategies
5. **backtest_portfolio** - Analyze multi-asset portfolios
6. **calculate_correlation** - Study asset correlations

### History Management
7. **save_analysis** - Save backtest results
8. **list_history** - View saved analyses
9. **get_history** - Retrieve saved analysis by ID
10. **delete_history** - Remove saved analysis

## Example Conversations

### Example 1: Simple Backtest

**You:** Backtest Apple stock with the SMA 50/200 crossover strategy from 2020 to 2023.

**Claude:** Uses the `backtest_stock` tool to run the analysis and presents:
- Total return vs buy-and-hold
- Win rate and Sharpe ratio
- Maximum drawdown
- Trade signals with dates and prices
- Equity curve

### Example 2: Strategy Optimization

**You:** What's the best RSI strategy for SPY over the last 3 years?

**Claude:** Uses the `optimize_strategies` tool to:
- Test multiple RSI parameter combinations
- Find the optimal period and thresholds
- Compare performance metrics
- Show the best configuration

### Example 3: Portfolio Analysis

**You:** Create a portfolio with AAPL, MSFT, and GOOGL. Compare equal-weight vs risk parity strategies from 2021 to 2023.

**Claude:** Uses `backtest_portfolio` to:
- Run both strategies
- Show risk-adjusted returns
- Display correlation matrix
- Calculate diversification benefits
- Show rebalancing history

## Troubleshooting

### Backend Not Accessible

**Error:** "Connection refused" or "Cannot connect to backend"

**Solution:**
1. Ensure backend is running: `curl http://localhost:8000/`
2. Check docker logs: `docker-compose logs backend`
3. Verify BACKEND_API_URL in .env or docker-compose.yml

### MCP Server Not Showing in Claude

**Solution:**
1. Check Claude Desktop config file syntax (valid JSON)
2. Restart Claude Desktop completely
3. Check Docker image is built: `docker images | grep stock-analysis-mcp`
4. View MCP server logs if using docker-compose

### No Data for Ticker

**Error:** "No data available for ticker XYZ"

**Solution:**
1. Check internet connection (yfinance needs it)
2. Verify ticker symbol is correct
3. Try a different date range
4. Some tickers may have limited historical data

### Docker Network Issues on Linux

**Solution:**
Use `--network=host` in the Claude Desktop config instead of `http://host.docker.internal:8000`.

## Advanced Configuration

### Custom Backend URL

If your backend runs on a different host or port:

```bash
# In .env file
BACKEND_API_URL=http://your-backend-host:8000

# Or in docker-compose.yml
environment:
  - BACKEND_API_URL=http://your-backend-host:8000
```

### Running Backend and MCP Server on Different Machines

1. Start backend on Machine A
2. Note backend's IP address
3. On Machine B, configure MCP server:

```bash
export BACKEND_API_URL=http://MACHINE_A_IP:8000
python server.py
```

## Performance Tips

- **Optimization** can take 1-5 minutes for complex strategies
- **Portfolio backtests** typically take 10-30 seconds
- **Single backtests** complete in 2-5 seconds
- Use date ranges wisely - longer periods take more time

## What's Next?

- Explore all 203+ strategies with `list_strategies`
- Try portfolio optimization with different allocation methods
- Save your best analyses for future reference
- Compare multiple strategies side-by-side

For detailed tool documentation, see `/mcp-server/README.md`.

## Need Help?

1. Check the main README: `/README.md`
2. Check MCP server README: `/mcp-server/README.md`
3. View backend API docs: `http://localhost:8000/docs` (when running)
4. Check logs: `docker-compose logs -f`
