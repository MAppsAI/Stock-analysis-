#!/usr/bin/env python3
"""
MCP Server for Stock Analysis Backend API

This MCP server wraps all the backend APIs and provides LLM-friendly tools
for stock backtesting, portfolio analysis, and strategy optimization.
"""

import os
import json
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Backend API URL
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# Initialize MCP server
app = Server("stock-analysis-mcp")

# HTTP client for API calls
http_client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for long operations


def format_number(value: float, decimals: int = 2) -> str:
    """Format number for LLM-friendly output"""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage for LLM-friendly output"""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def summarize_backtest_results(results: Dict[str, Any]) -> str:
    """Create LLM-friendly summary of backtest results"""
    summary_parts = []

    # Header
    summary_parts.append(f"# Stock Analysis Results for {results.get('ticker', 'N/A')}")
    summary_parts.append(f"Period: {results.get('startDate')} to {results.get('endDate')}\n")

    # Buy & Hold Baseline
    if 'buy_hold_result' in results and results['buy_hold_result']:
        bh = results['buy_hold_result']
        summary_parts.append("## Buy & Hold Baseline (for comparison)")
        summary_parts.append(f"- Total Return: {format_percentage(bh.get('total_return', 0))}")
        summary_parts.append(f"- Sharpe Ratio: {format_number(bh.get('sharpe_ratio', 0))}")
        summary_parts.append(f"- Max Drawdown: {format_percentage(bh.get('max_drawdown', 0))}\n")

    # Strategy Results
    if 'results' in results and results['results']:
        summary_parts.append(f"## Strategy Results ({len(results['results'])} strategies tested)\n")

        # Sort by total return
        sorted_results = sorted(
            results['results'],
            key=lambda x: x.get('total_return', 0),
            reverse=True
        )

        # Top 5 performers
        summary_parts.append("### Top 5 Performing Strategies:\n")
        for i, strategy in enumerate(sorted_results[:5], 1):
            summary_parts.append(f"**{i}. {strategy.get('strategy', 'Unknown')}**")
            summary_parts.append(f"   - Total Return: {format_percentage(strategy.get('total_return', 0))}")
            summary_parts.append(f"   - Sharpe Ratio: {format_number(strategy.get('sharpe_ratio', 0))}")
            summary_parts.append(f"   - Win Rate: {format_percentage(strategy.get('win_rate', 0))}")
            summary_parts.append(f"   - Max Drawdown: {format_percentage(strategy.get('max_drawdown', 0))}")
            summary_parts.append(f"   - Number of Trades: {strategy.get('num_trades', 0)}\n")

        # Bottom 3 performers (if applicable)
        if len(sorted_results) > 5:
            summary_parts.append("\n### Worst 3 Performing Strategies:\n")
            for i, strategy in enumerate(sorted_results[-3:], 1):
                summary_parts.append(f"**{i}. {strategy.get('strategy', 'Unknown')}**")
                summary_parts.append(f"   - Total Return: {format_percentage(strategy.get('total_return', 0))}")
                summary_parts.append(f"   - Sharpe Ratio: {format_number(strategy.get('sharpe_ratio', 0))}\n")

    # Data availability
    if 'price_data' in results and results['price_data']:
        summary_parts.append(f"\n## Market Data")
        summary_parts.append(f"- Total trading days: {len(results['price_data'])}")
        if results['price_data']:
            first_price = results['price_data'][0]
            last_price = results['price_data'][-1]
            summary_parts.append(f"- Starting price: ${format_number(first_price.get('close', 0))}")
            summary_parts.append(f"- Ending price: ${format_number(last_price.get('close', 0))}")
            price_change = ((last_price.get('close', 0) - first_price.get('close', 1)) / first_price.get('close', 1)) * 100
            summary_parts.append(f"- Price change: {format_percentage(price_change)}")

    return "\n".join(summary_parts)


def summarize_optimization_results(results: Dict[str, Any]) -> str:
    """Create LLM-friendly summary of optimization results"""
    summary_parts = []

    # Header
    summary_parts.append(f"# Strategy Optimization Results for {results.get('ticker', 'N/A')}")
    summary_parts.append(f"Period: {results.get('startDate')} to {results.get('endDate')}\n")

    # Overall summary
    if 'summary' in results and results['summary']:
        summary = results['summary']
        summary_parts.append("## Optimization Summary")
        summary_parts.append(f"- Strategies optimized: {summary.get('strategies_optimized', 0)}")
        summary_parts.append(f"- Total combinations tested: {summary.get('total_combinations_tested', 0)}")
        summary_parts.append(f"- Average improvement: {format_percentage(summary.get('average_improvement', 0))}\n")

    # Individual optimization results
    if 'optimization_results' in results and results['optimization_results']:
        summary_parts.append("## Optimized Strategies\n")

        for strategy_id, opt_result in results['optimization_results'].items():
            if opt_result.get('status') == 'success':
                summary_parts.append(f"### {strategy_id}")
                summary_parts.append(f"**Status:** {opt_result.get('status')}")
                summary_parts.append(f"**Best Score (Sharpe):** {format_number(opt_result.get('best_score', 0))}")
                summary_parts.append(f"**Combinations Tested:** {opt_result.get('total_tested', 0)}")

                if 'best_params' in opt_result:
                    summary_parts.append(f"**Best Parameters:** {json.dumps(opt_result['best_params'], indent=2)}")

                if 'best_metrics' in opt_result:
                    metrics = opt_result['best_metrics']
                    summary_parts.append("**Best Metrics:**")
                    summary_parts.append(f"   - Total Return: {format_percentage(metrics.get('total_return', 0))}")
                    summary_parts.append(f"   - Win Rate: {format_percentage(metrics.get('win_rate', 0))}")
                    summary_parts.append(f"   - Max Drawdown: {format_percentage(metrics.get('max_drawdown', 0))}")
                    summary_parts.append(f"   - Number of Trades: {metrics.get('num_trades', 0)}")

                summary_parts.append("")
            else:
                summary_parts.append(f"### {strategy_id}")
                summary_parts.append(f"**Status:** Failed")
                summary_parts.append("")

    return "\n".join(summary_parts)


def summarize_portfolio_results(results: Dict[str, Any]) -> str:
    """Create LLM-friendly summary of portfolio backtest results"""
    summary_parts = []

    # Header
    tickers = results.get('tickers', [])
    summary_parts.append(f"# Portfolio Analysis Results")
    summary_parts.append(f"Assets: {', '.join(tickers)}")
    summary_parts.append(f"Period: {results.get('startDate')} to {results.get('endDate')}\n")

    # Buy & Hold Baseline
    if 'buy_hold_result' in results and results['buy_hold_result']:
        bh = results['buy_hold_result']
        if 'portfolio_metrics' in bh:
            pm = bh['portfolio_metrics']
            summary_parts.append("## Equal-Weight Buy & Hold Baseline")
            summary_parts.append(f"- Total Return: {format_percentage(pm.get('total_return', 0))}")
            summary_parts.append(f"- Annualized Return: {format_percentage(pm.get('annualized_return', 0))}")
            summary_parts.append(f"- Volatility: {format_percentage(pm.get('volatility', 0))}")
            summary_parts.append(f"- Sharpe Ratio: {format_number(pm.get('sharpe_ratio', 0))}")
            summary_parts.append(f"- Max Drawdown: {format_percentage(pm.get('max_drawdown', 0))}\n")

    # Strategy Results
    if 'results' in results and results['results']:
        summary_parts.append(f"## Portfolio Strategy Results ({len(results['results'])} strategies tested)\n")

        # Sort by Sharpe ratio
        sorted_results = sorted(
            results['results'],
            key=lambda x: x.get('portfolio_metrics', {}).get('sharpe_ratio', 0),
            reverse=True
        )

        for i, strategy in enumerate(sorted_results, 1):
            pm = strategy.get('portfolio_metrics', {})
            summary_parts.append(f"### {i}. {strategy.get('strategy', 'Unknown')}")
            summary_parts.append(f"**Portfolio Metrics:**")
            summary_parts.append(f"   - Total Return: {format_percentage(pm.get('total_return', 0))}")
            summary_parts.append(f"   - Annualized Return: {format_percentage(pm.get('annualized_return', 0))}")
            summary_parts.append(f"   - Volatility: {format_percentage(pm.get('volatility', 0))}")
            summary_parts.append(f"   - Sharpe Ratio: {format_number(pm.get('sharpe_ratio', 0))}")
            summary_parts.append(f"   - Max Drawdown: {format_percentage(pm.get('max_drawdown', 0))}")
            summary_parts.append(f"   - Win Rate: {format_percentage(pm.get('win_rate', 0))}")
            summary_parts.append(f"   - Number of Rebalances: {pm.get('num_rebalances', 0)}")
            summary_parts.append(f"   - Portfolio Turnover: {format_percentage(pm.get('turnover', 0))}")
            summary_parts.append(f"   - Transaction Costs: {format_percentage(pm.get('total_transaction_costs', 0))}")
            summary_parts.append(f"   - Diversification Ratio: {format_number(pm.get('diversification_ratio', 0))}")

            # Asset-level metrics
            if 'asset_metrics' in strategy and strategy['asset_metrics']:
                summary_parts.append(f"\n**Individual Asset Performance:**")
                for asset in strategy['asset_metrics']:
                    summary_parts.append(f"   - **{asset.get('ticker')}**: Return={format_percentage(asset.get('total_return', 0))}, "
                                       f"Weight={format_percentage(asset.get('weight', 0) * 100)}, "
                                       f"Contribution={format_percentage(asset.get('contribution_to_return', 0))}")

            summary_parts.append("")

    return "\n".join(summary_parts)


# Tool 1: List Available Strategies
@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools"""
    return [
        Tool(
            name="list_strategies",
            description="Get a list of all available single-asset trading strategies (203+ strategies including trend-following, mean-reversion, momentum, volatility, and volume-based strategies)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="backtest_stock",
            description="Run backtests on a stock with selected trading strategies. Returns detailed performance metrics, trade signals, equity curves, and comparison to buy-and-hold baseline.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, MSFT, SPY)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (e.g., 2020-01-01)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (e.g., 2023-12-31)"
                    },
                    "strategies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of strategy IDs to backtest (e.g., ['sma_50_200_cross', 'rsi_oversold_overbought']). Use list_strategies to see all available strategy IDs."
                    }
                },
                "required": ["ticker", "start_date", "end_date", "strategies"]
            }
        ),
        Tool(
            name="optimize_strategies",
            description="Optimize strategy parameters to find the best performing configuration. Tests multiple parameter combinations and returns the optimal parameters with performance metrics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, MSFT, SPY)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format"
                    },
                    "strategies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of strategy IDs to optimize"
                    }
                },
                "required": ["ticker", "start_date", "end_date", "strategies"]
            }
        ),
        Tool(
            name="list_portfolio_strategies",
            description="Get a list of all available multi-asset portfolio strategies (9 strategies including equal-weight, sector rotation, risk parity, mean-variance optimization, HRP, Black-Litterman, and CVaR optimization)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="backtest_portfolio",
            description="Run portfolio backtests with multiple assets and allocation strategies. Supports various rebalancing methods, transaction costs, and tax-aware analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock ticker symbols for the portfolio (e.g., ['AAPL', 'MSFT', 'GOOGL'])"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format"
                    },
                    "strategies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of portfolio strategy IDs to backtest"
                    },
                    "allocation_method": {
                        "type": "string",
                        "enum": ["equal", "market_cap", "optimized", "custom"],
                        "description": "Initial allocation method (default: equal)",
                        "default": "equal"
                    },
                    "custom_weights": {
                        "type": "object",
                        "description": "Custom weights for each ticker (only if allocation_method is 'custom'). Format: {\"AAPL\": 0.4, \"MSFT\": 0.6}"
                    },
                    "rebalancing": {
                        "type": "string",
                        "enum": ["none", "monthly", "quarterly", "threshold"],
                        "description": "Rebalancing frequency (default: none)",
                        "default": "none"
                    },
                    "rebalance_threshold": {
                        "type": "number",
                        "description": "Weight drift threshold for rebalancing (default: 0.05 = 5%)",
                        "default": 0.05
                    },
                    "transaction_cost": {
                        "type": "number",
                        "description": "Per-trade transaction cost as decimal (default: 0.001 = 0.1%)",
                        "default": 0.001
                    }
                },
                "required": ["tickers", "start_date", "end_date", "strategies"]
            }
        ),
        Tool(
            name="calculate_correlation",
            description="Calculate correlation and covariance matrices for a portfolio of assets. Useful for understanding diversification and risk relationships.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock ticker symbols"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format"
                    }
                },
                "required": ["tickers", "start_date", "end_date"]
            }
        ),
        Tool(
            name="save_analysis",
            description="Save backtest or optimization results to history for later retrieval",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker or portfolio description"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format"
                    },
                    "run_type": {
                        "type": "string",
                        "enum": ["backtest", "optimization"],
                        "description": "Type of analysis run"
                    },
                    "results_data": {
                        "type": "object",
                        "description": "Full results data from backtest or optimization"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional custom title for this analysis"
                    }
                },
                "required": ["ticker", "start_date", "end_date", "run_type", "results_data"]
            }
        ),
        Tool(
            name="list_history",
            description="List saved analysis history with optional filtering by ticker",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Optional: Filter by ticker symbol"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (default: 100)",
                        "default": 100
                    },
                    "offset": {
                        "type": "number",
                        "description": "Pagination offset (default: 0)",
                        "default": 0
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_history",
            description="Retrieve full details of a saved analysis by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "history_id": {
                        "type": "number",
                        "description": "The ID of the history entry to retrieve"
                    }
                },
                "required": ["history_id"]
            }
        ),
        Tool(
            name="delete_history",
            description="Delete a saved analysis from history",
            inputSchema={
                "type": "object",
                "properties": {
                    "history_id": {
                        "type": "number",
                        "description": "The ID of the history entry to delete"
                    }
                },
                "required": ["history_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""

    try:
        # Tool 1: List Strategies
        if name == "list_strategies":
            response = await http_client.get(f"{BACKEND_URL}/api/v1/strategies")
            response.raise_for_status()
            data = response.json()

            # Format for LLM
            output = ["# Available Trading Strategies\n"]

            # Group by category
            categories = {}
            for strategy in data.get('strategies', []):
                category = strategy.get('category', 'Other')
                if category not in categories:
                    categories[category] = []
                categories[category].append(strategy)

            for category, strategies in categories.items():
                output.append(f"## {category} ({len(strategies)} strategies)\n")
                for strategy in strategies:
                    output.append(f"- **{strategy['id']}**: {strategy['name']}")
                output.append("")

            output.append(f"\n**Total Strategies Available:** {data.get('total', 0)}")

            return [TextContent(
                type="text",
                text="\n".join(output)
            )]

        # Tool 2: Backtest Stock
        elif name == "backtest_stock":
            payload = {
                "ticker": arguments["ticker"],
                "startDate": arguments["start_date"],
                "endDate": arguments["end_date"],
                "strategies": arguments["strategies"]
            }

            response = await http_client.post(
                f"{BACKEND_URL}/api/v1/backtest",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Return only summary, not full data
            summary = summarize_backtest_results(data)

            return [TextContent(type="text", text=summary)]

        # Tool 3: Optimize Strategies
        elif name == "optimize_strategies":
            payload = {
                "ticker": arguments["ticker"],
                "startDate": arguments["start_date"],
                "endDate": arguments["end_date"],
                "strategies": arguments["strategies"]
            }

            response = await http_client.post(
                f"{BACKEND_URL}/api/v1/optimize",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            summary = summarize_optimization_results(data)

            return [TextContent(type="text", text=summary)]

        # Tool 4: List Portfolio Strategies
        elif name == "list_portfolio_strategies":
            response = await http_client.get(f"{BACKEND_URL}/api/v1/portfolio/strategies")
            response.raise_for_status()
            data = response.json()

            output = ["# Available Portfolio Strategies\n"]

            for strategy in data.get('strategies', []):
                output.append(f"## {strategy['id']}")
                output.append(f"**Name:** {strategy['name']}")
                output.append(f"**Description:** {strategy['description']}")
                if 'parameters' in strategy and strategy['parameters']:
                    output.append(f"**Parameters:** {json.dumps(strategy['parameters'], indent=2)}")
                output.append("")

            output.append(f"\n**Total Portfolio Strategies:** {data.get('total', 0)}")

            return [TextContent(type="text", text="\n".join(output))]

        # Tool 5: Backtest Portfolio
        elif name == "backtest_portfolio":
            payload = {
                "tickers": arguments["tickers"],
                "startDate": arguments["start_date"],
                "endDate": arguments["end_date"],
                "strategies": arguments["strategies"],
                "allocation_method": arguments.get("allocation_method", "equal"),
                "rebalancing": arguments.get("rebalancing", "none"),
                "rebalance_threshold": arguments.get("rebalance_threshold", 0.05),
                "transaction_cost": arguments.get("transaction_cost", 0.001)
            }

            if "custom_weights" in arguments:
                payload["custom_weights"] = arguments["custom_weights"]

            response = await http_client.post(
                f"{BACKEND_URL}/api/v1/portfolio/backtest",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            summary = summarize_portfolio_results(data)

            return [TextContent(type="text", text=summary)]

        # Tool 6: Calculate Correlation
        elif name == "calculate_correlation":
            payload = {
                "tickers": arguments["tickers"],
                "startDate": arguments["start_date"],
                "endDate": arguments["end_date"],
                "strategies": []  # Not needed for correlation calculation
            }

            response = await http_client.post(
                f"{BACKEND_URL}/api/v1/portfolio/correlation",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Format correlation matrix
            output = ["# Asset Correlation Analysis\n"]
            output.append(f"**Period:** {data.get('date_range', {}).get('start')} to {data.get('date_range', {}).get('end')}\n")

            output.append("## Correlation Matrix\n")
            tickers = data.get('tickers', [])

            # Header row
            header = "| Asset | " + " | ".join(tickers) + " |"
            separator = "|-------|" + "|".join(["-------" for _ in tickers]) + "|"
            output.append(header)
            output.append(separator)

            # Data rows
            corr_matrix = data.get('correlation_matrix', {})
            for ticker1 in tickers:
                row = f"| **{ticker1}** |"
                for ticker2 in tickers:
                    corr_value = corr_matrix.get(ticker1, {}).get(ticker2, 0)
                    row += f" {format_number(corr_value, 3)} |"
                output.append(row)

            output.append("\n## Individual Asset Volatilities\n")
            volatilities = data.get('volatilities', {})
            for ticker, vol in volatilities.items():
                output.append(f"- **{ticker}**: {format_percentage(vol)}")

            return [TextContent(type="text", text="\n".join(output))]

        # Tool 7: Save Analysis
        elif name == "save_analysis":
            payload = {
                "ticker": arguments["ticker"],
                "start_date": arguments["start_date"],
                "end_date": arguments["end_date"],
                "run_type": arguments["run_type"],
                "results_data": arguments["results_data"]
            }

            if "title" in arguments:
                payload["title"] = arguments["title"]

            response = await http_client.post(
                f"{BACKEND_URL}/api/v1/history",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return [TextContent(
                type="text",
                text=f"✓ Analysis saved successfully!\n\n**ID:** {data.get('id')}\n**Message:** {data.get('message')}"
            )]

        # Tool 8: List History
        elif name == "list_history":
            params = {
                "limit": arguments.get("limit", 100),
                "offset": arguments.get("offset", 0)
            }

            if "ticker" in arguments:
                params["ticker"] = arguments["ticker"]

            response = await http_client.get(
                f"{BACKEND_URL}/api/v1/history",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            output = ["# Saved Analysis History\n"]
            output.append(f"**Total Entries:** {data.get('total_count', 0)}\n")

            for item in data.get('items', []):
                output.append(f"## ID: {item['id']} - {item.get('title', 'Untitled')}")
                output.append(f"- **Ticker:** {item['ticker']}")
                output.append(f"- **Type:** {item['run_type']}")
                output.append(f"- **Period:** {item['start_date']} to {item['end_date']}")
                output.append(f"- **Created:** {item['created_at']}")

                if 'summary_metrics' in item and item['summary_metrics']:
                    output.append(f"- **Summary:** {json.dumps(item['summary_metrics'])}")
                output.append("")

            return [TextContent(type="text", text="\n".join(output))]

        # Tool 9: Get History
        elif name == "get_history":
            history_id = arguments["history_id"]

            response = await http_client.get(
                f"{BACKEND_URL}/api/v1/history/{history_id}"
            )
            response.raise_for_status()
            data = response.json()

            output = [f"# Analysis History - ID {data['id']}\n"]
            output.append(f"**Title:** {data.get('title', 'Untitled')}")
            output.append(f"**Ticker:** {data['ticker']}")
            output.append(f"**Type:** {data['run_type']}")
            output.append(f"**Period:** {data['start_date']} to {data['end_date']}")
            output.append(f"**Created:** {data['created_at']}\n")

            # Generate appropriate summary based on run type
            if data['run_type'] == 'backtest':
                if 'tickers' in data.get('results_data', {}):
                    summary = summarize_portfolio_results(data['results_data'])
                else:
                    summary = summarize_backtest_results(data['results_data'])
            else:
                summary = summarize_optimization_results(data['results_data'])

            return [TextContent(type="text", text="\n".join(output) + "\n" + summary)]

        # Tool 10: Delete History
        elif name == "delete_history":
            history_id = arguments["history_id"]

            response = await http_client.delete(
                f"{BACKEND_URL}/api/v1/history/{history_id}"
            )
            response.raise_for_status()
            data = response.json()

            return [TextContent(
                type="text",
                text=f"✓ {data.get('message', 'History entry deleted successfully')}"
            )]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except httpx.HTTPError as e:
        error_msg = f"API Error: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg += f"\n\nDetails: {json.dumps(error_detail, indent=2)}"
            except:
                error_msg += f"\n\nResponse: {e.response.text}"

        return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
