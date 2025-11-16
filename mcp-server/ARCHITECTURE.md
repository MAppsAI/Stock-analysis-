# MCP Server Architecture

## Overview

The Stock Analysis MCP Server is a wrapper layer that exposes backend APIs as Model Context Protocol (MCP) tools. This allows LLM clients like Claude to interact with the stock analysis backend in a standardized, tool-based manner.

## Architecture Diagram

```
┌──────────────────────────────────────┐
│         LLM Client (Claude)          │
│   - Claude Desktop                    │
│   - Claude Code                       │
│   - Other MCP-compatible clients      │
└───────────────┬──────────────────────┘
                │
                │ MCP Protocol (stdio)
                │ JSON-RPC messages
                │
┌───────────────▼──────────────────────┐
│          MCP Server Layer            │
│  ┌────────────────────────────────┐ │
│  │  Tool Definitions (10 tools)   │ │
│  │  - list_strategies             │ │
│  │  - backtest_stock              │ │
│  │  - optimize_strategies         │ │
│  │  - list_portfolio_strategies   │ │
│  │  - backtest_portfolio          │ │
│  │  - calculate_correlation       │ │
│  │  - save_analysis               │ │
│  │  - list_history                │ │
│  │  - get_history                 │ │
│  │  - delete_history              │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │  LLM-Friendly Formatters       │ │
│  │  - summarize_backtest_results  │ │
│  │  - summarize_optimization_results│ │
│  │  - summarize_portfolio_results │ │
│  │  - format_number               │ │
│  │  - format_percentage           │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │  HTTP Client (httpx)           │ │
│  │  - Async requests              │ │
│  │  - 5 min timeout               │ │
│  │  - Error handling              │ │
│  └────────────────────────────────┘ │
└───────────────┬──────────────────────┘
                │
                │ HTTP/REST
                │ JSON payloads
                │
┌───────────────▼──────────────────────┐
│      FastAPI Backend (Port 8000)     │
│  ┌────────────────────────────────┐ │
│  │  10 REST Endpoints             │ │
│  │  - GET /api/v1/strategies      │ │
│  │  - POST /api/v1/backtest       │ │
│  │  - POST /api/v1/optimize       │ │
│  │  - GET /api/v1/portfolio/...   │ │
│  │  - POST /api/v1/portfolio/...  │ │
│  │  - GET/POST/DELETE /api/v1/history│ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │  Strategy Engine               │ │
│  │  - 203+ trading strategies     │ │
│  │  - 9 portfolio strategies      │ │
│  │  - Parallel optimization       │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │  Data Layer                    │ │
│  │  - yfinance (market data)      │ │
│  │  - SQLite (history)            │ │
│  │  - vectorbt (performance)      │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
```

## Component Details

### 1. MCP Server Layer (`server.py`)

**Responsibilities:**
- Implement MCP protocol (stdio transport)
- Define tool schemas and input validation
- Route tool calls to appropriate backend endpoints
- Transform backend responses into LLM-friendly format
- Handle errors gracefully

**Key Functions:**

```python
list_tools()      # Returns tool definitions
call_tool()       # Handles tool execution
main()            # Runs stdio server
```

**Transport:** stdio (standard input/output)
- Client writes JSON-RPC messages to stdin
- Server writes responses to stdout
- Suitable for subprocess-based integration (Claude Desktop)

### 2. LLM-Friendly Formatters

**Purpose:** Transform technical JSON data into human-readable summaries that LLMs can easily understand and present to users.

**Formatter Functions:**

```python
summarize_backtest_results()
  - Top/bottom performers
  - Key metrics highlighted
  - Comparison to buy-and-hold
  - Markdown formatted tables

summarize_optimization_results()
  - Best parameters found
  - Performance improvements
  - Combinations tested

summarize_portfolio_results()
  - Portfolio-level metrics
  - Asset-level breakdown
  - Correlation insights
  - Rebalancing history

format_number()      # Consistent decimal formatting
format_percentage()  # Percentage with % sign
```

**Output Format:**
- Markdown with headers, lists, and tables
- Both summary (human-readable) and full JSON
- Numbered rankings for easy comparison
- Highlighted key insights

### 3. HTTP Client Layer

**Technology:** `httpx` async client

**Configuration:**
- Timeout: 300 seconds (5 minutes)
- Base URL: Configurable via `BACKEND_API_URL`
- Error handling: HTTPException catching

**Request Flow:**
1. Receive MCP tool call
2. Transform to HTTP request (GET/POST/DELETE)
3. Send to backend API
4. Receive JSON response
5. Format and return to client

### 4. Tool Definitions

Each tool follows this structure:

```python
Tool(
    name="tool_name",
    description="What the tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
            # ...
        },
        "required": ["param1"]
    }
)
```

**Tool Categories:**

**Single-Asset (3 tools):**
- Discovery: list_strategies
- Execution: backtest_stock
- Optimization: optimize_strategies

**Portfolio (3 tools):**
- Discovery: list_portfolio_strategies
- Execution: backtest_portfolio
- Analysis: calculate_correlation

**History (4 tools):**
- Save: save_analysis
- List: list_history
- Retrieve: get_history
- Delete: delete_history

## Data Flow Example

### Example: Backtest Tool Call

1. **User → Claude:**
   ```
   "Backtest AAPL with RSI strategy from 2020 to 2023"
   ```

2. **Claude → MCP Server:**
   ```json
   {
     "jsonrpc": "2.0",
     "method": "tools/call",
     "params": {
       "name": "backtest_stock",
       "arguments": {
         "ticker": "AAPL",
         "start_date": "2020-01-01",
         "end_date": "2023-12-31",
         "strategies": ["rsi_oversold_overbought"]
       }
     }
   }
   ```

3. **MCP Server → Backend:**
   ```
   POST http://localhost:8000/api/v1/backtest
   Content-Type: application/json

   {
     "ticker": "AAPL",
     "startDate": "2020-01-01",
     "endDate": "2023-12-31",
     "strategies": ["rsi_oversold_overbought"]
   }
   ```

4. **Backend → MCP Server:**
   ```json
   {
     "ticker": "AAPL",
     "startDate": "2020-01-01",
     "endDate": "2023-12-31",
     "results": [{
       "strategy": "rsi_oversold_overbought",
       "total_return": 125.5,
       "sharpe_ratio": 1.8,
       "win_rate": 62.5,
       "max_drawdown": -18.3,
       "num_trades": 24,
       "signals": [...],
       "equity_curve": [...]
     }],
     "buy_hold_result": {...},
     "price_data": [...]
   }
   ```

5. **MCP Server → Claude:**
   ```markdown
   # Stock Analysis Results for AAPL
   Period: 2020-01-01 to 2023-12-31

   ## Buy & Hold Baseline
   - Total Return: 95.2%
   - Sharpe Ratio: 1.5
   - Max Drawdown: -25.1%

   ## Strategy Results (1 strategies tested)

   ### Top Performing Strategies:

   **1. rsi_oversold_overbought**
      - Total Return: 125.5%
      - Sharpe Ratio: 1.8
      - Win Rate: 62.5%
      - Max Drawdown: -18.3%
      - Number of Trades: 24

   [+ Full JSON data...]
   ```

6. **Claude → User:**
   Natural language summary with insights

## Docker Deployment

### docker-compose.yml Structure

```yaml
services:
  backend:
    # FastAPI backend on port 8000
    # Healthcheck enabled
    # Network: stock-analysis-network

  mcp-server:
    # MCP server (stdio)
    # Depends on: backend
    # Environment: BACKEND_API_URL=http://backend:8000
    # Network: stock-analysis-network
```

**Network Communication:**
- Both containers on same bridge network
- MCP server accesses backend via hostname `backend`
- Backend health check ensures availability before MCP starts

### Standalone Docker

For running MCP server separately:

```bash
docker run -i --rm \
  -e BACKEND_API_URL=http://host.docker.internal:8000 \
  stock-analysis-mcp
```

## Configuration

### Environment Variables

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `BACKEND_API_URL` | Backend base URL | `http://localhost:8000` | No |

### Configuration Sources (Priority Order)

1. Environment variables
2. `.env` file
3. Hardcoded defaults

## Error Handling

### HTTP Errors

```python
try:
    response = await http_client.get(url)
    response.raise_for_status()
except httpx.HTTPError as e:
    # Extract error details
    # Return formatted error to client
```

**Error Response Format:**
```
API Error: <exception message>

Details: <JSON error from backend>
```

### Tool Execution Errors

```python
try:
    # Tool logic
except Exception as e:
    return [TextContent(
        type="text",
        text=f"Error: {str(e)}"
    )]
```

## Performance Characteristics

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| list_strategies | <1s | Fast, no processing |
| backtest_stock | 2-5s | Per strategy |
| optimize_strategies | 1-5min | Parallel processing |
| backtest_portfolio | 10-30s | 3-5 assets |
| calculate_correlation | 2-5s | Matrix calculation |
| save_analysis | <1s | SQLite insert |
| list_history | <1s | SQLite query |

**Timeout:** 300s (5 minutes) to accommodate long optimizations

## Security Considerations

### Current State (Development)

- No authentication
- HTTP (not HTTPS)
- Local deployment assumed

### Production Recommendations

1. **Authentication:** Add API keys or OAuth
2. **Encryption:** Use HTTPS with TLS certificates
3. **Rate Limiting:** Prevent abuse
4. **Input Validation:** Already implemented via Pydantic
5. **Container Security:** Run as non-root user
6. **Network Isolation:** Use Docker networks

## Extensibility

### Adding New Tools

1. **Define Tool Schema** in `list_tools()`:
   ```python
   Tool(
       name="new_tool",
       description="...",
       inputSchema={...}
   )
   ```

2. **Implement Handler** in `call_tool()`:
   ```python
   elif name == "new_tool":
       # Call backend API
       # Format response
       # Return TextContent
   ```

3. **Add Formatter** (if needed):
   ```python
   def summarize_new_tool_results(results):
       # Create LLM-friendly summary
       return markdown_string
   ```

4. **Update Documentation**
   - README.md
   - ARCHITECTURE.md (this file)

### Backend API Changes

If backend adds new endpoints:
1. Add corresponding MCP tool
2. Create appropriate formatters
3. Test end-to-end flow

## Testing Strategy

### Manual Testing

```bash
# 1. Start backend
cd backend && uvicorn main:app

# 2. Start MCP server
cd mcp-server && python server.py

# 3. Use MCP Inspector or Claude Desktop
```

### Automated Testing (Future)

- Unit tests for formatters
- Integration tests with mock backend
- End-to-end tests with real backend

## Monitoring and Debugging

### Logs

**MCP Server:**
- stdout: MCP protocol messages
- stderr: Error messages and exceptions

**Backend:**
- Uvicorn access logs
- Application logs

### Docker Logs

```bash
# View MCP server logs
docker-compose logs -f mcp-server

# View backend logs
docker-compose logs -f backend

# View both
docker-compose logs -f
```

### Debugging Tips

1. **Test backend first:** `curl http://localhost:8000/`
2. **Check env vars:** `echo $BACKEND_API_URL`
3. **Verify network:** `docker network inspect stock-analysis_stock-analysis-network`
4. **Test individual endpoints:** Use curl or Postman

## Dependencies

### Python Packages

```
mcp>=1.0.0           # MCP protocol implementation
httpx>=0.27.0        # Async HTTP client
pydantic>=2.5.0      # Data validation (implicit)
python-dotenv>=1.0.0 # Environment configuration
```

### System Requirements

- Python 3.11+
- Docker (optional, for containerized deployment)
- Network access to backend

## Future Enhancements

### Potential Improvements

1. **Caching:** Cache strategy lists and historical data
2. **Streaming:** Stream long-running operations
3. **Resources:** Add MCP resources for accessing saved analyses
4. **Prompts:** Add MCP prompts for common workflows
5. **Authentication:** OAuth or API key support
6. **Metrics:** Prometheus metrics for monitoring
7. **WebSocket:** Support SSE transport in addition to stdio

### Scalability

For high-load scenarios:
1. Load balance multiple backend instances
2. Add Redis cache layer
3. Queue long-running optimizations
4. Horizontal scaling with multiple MCP server instances

## References

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [httpx Documentation](https://www.python-httpx.org/)
- Backend API Documentation: `http://localhost:8000/docs`
