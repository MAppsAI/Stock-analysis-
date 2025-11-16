"""
Database manager for storing backtest and optimization history.
Uses SQLite for simple, persistent storage.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


class HistoryDatabase:
    """Manages SQLite database for backtest and optimization history."""

    def __init__(self, db_path: str = "backtest_history.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    run_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    title TEXT,
                    results_data TEXT NOT NULL,
                    summary_metrics TEXT,
                    tickers TEXT,
                    portfolio_config TEXT,
                    asset_weights TEXT
                )
            """)

            # Create index on ticker for faster searches
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticker
                ON backtest_history(ticker)
            """)

            # Create index on created_at for chronological ordering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON backtest_history(created_at DESC)
            """)

            # Migrate existing tables to add new columns if needed
            self._migrate_schema(cursor)

            conn.commit()

    def _migrate_schema(self, cursor):
        """Add new columns to existing tables if they don't exist."""
        # Check if new columns exist
        cursor.execute("PRAGMA table_info(backtest_history)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'tickers' not in columns:
            cursor.execute("ALTER TABLE backtest_history ADD COLUMN tickers TEXT")

        if 'portfolio_config' not in columns:
            cursor.execute("ALTER TABLE backtest_history ADD COLUMN portfolio_config TEXT")

        if 'asset_weights' not in columns:
            cursor.execute("ALTER TABLE backtest_history ADD COLUMN asset_weights TEXT")

    def save_backtest(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        results_data: Dict[str, Any],
        title: Optional[str] = None
    ) -> int:
        """
        Save a backtest result to the database.

        Args:
            ticker: Stock ticker symbol
            start_date: Backtest start date
            end_date: Backtest end date
            results_data: Complete backtest response data
            title: Optional custom title for the backtest

        Returns:
            ID of the saved record
        """
        if title is None:
            title = f"{ticker} Backtest"

        # Extract summary metrics
        summary_metrics = self._extract_summary_metrics(results_data)

        created_at = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backtest_history
                (ticker, start_date, end_date, run_type, created_at, title, results_data, summary_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker.upper(),
                start_date,
                end_date,
                "backtest",
                created_at,
                title,
                json.dumps(results_data),
                json.dumps(summary_metrics)
            ))
            conn.commit()
            return cursor.lastrowid

    def save_optimization(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        results_data: Dict[str, Any],
        title: Optional[str] = None
    ) -> int:
        """
        Save an optimization result to the database.

        Args:
            ticker: Stock ticker symbol
            start_date: Optimization start date
            end_date: Optimization end date
            results_data: Complete optimization response data
            title: Optional custom title for the optimization

        Returns:
            ID of the saved record
        """
        if title is None:
            title = f"{ticker} Optimization"

        # Extract summary metrics
        summary_metrics = self._extract_optimization_summary(results_data)

        created_at = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backtest_history
                (ticker, start_date, end_date, run_type, created_at, title, results_data, summary_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker.upper(),
                start_date,
                end_date,
                "optimization",
                created_at,
                title,
                json.dumps(results_data),
                json.dumps(summary_metrics)
            ))
            conn.commit()
            return cursor.lastrowid

    def save_portfolio_backtest(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        results_data: Dict[str, Any],
        portfolio_config: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None
    ) -> int:
        """
        Save a portfolio backtest result to the database.

        Args:
            tickers: List of stock ticker symbols in portfolio
            start_date: Backtest start date
            end_date: Backtest end date
            results_data: Complete portfolio backtest response data
            portfolio_config: Portfolio configuration (allocation method, rebalancing, etc.)
            title: Optional custom title for the backtest

        Returns:
            ID of the saved record
        """
        if title is None:
            title = f"Portfolio ({', '.join(tickers[:3])}{'...' if len(tickers) > 3 else ''}) Backtest"

        # Extract summary metrics for portfolio
        summary_metrics = self._extract_portfolio_summary_metrics(results_data)

        created_at = datetime.now().isoformat()

        # Store first ticker for backwards compatibility
        primary_ticker = tickers[0] if tickers else "PORTFOLIO"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backtest_history
                (ticker, start_date, end_date, run_type, created_at, title, results_data,
                 summary_metrics, tickers, portfolio_config, asset_weights)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                primary_ticker.upper(),
                start_date,
                end_date,
                "portfolio_backtest",
                created_at,
                title,
                json.dumps(results_data),
                json.dumps(summary_metrics),
                json.dumps(tickers),
                json.dumps(portfolio_config) if portfolio_config else None,
                None  # asset_weights can be extracted from results_data if needed
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_history(
        self,
        ticker_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all history entries, optionally filtered by ticker.

        Args:
            ticker_filter: Optional ticker to filter by
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of history entries (without full results_data)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if ticker_filter:
                cursor.execute("""
                    SELECT id, ticker, start_date, end_date, run_type, created_at, title, summary_metrics
                    FROM backtest_history
                    WHERE ticker LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (f"%{ticker_filter.upper()}%", limit, offset))
            else:
                cursor.execute("""
                    SELECT id, ticker, start_date, end_date, run_type, created_at, title, summary_metrics
                    FROM backtest_history
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

            rows = cursor.fetchall()

            return [
                {
                    "id": row["id"],
                    "ticker": row["ticker"],
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "run_type": row["run_type"],
                    "created_at": row["created_at"],
                    "title": row["title"],
                    "summary_metrics": json.loads(row["summary_metrics"]) if row["summary_metrics"] else None
                }
                for row in rows
            ]

    def get_history_by_id(self, history_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific history entry by ID, including full results data.

        Args:
            history_id: ID of the history entry

        Returns:
            Complete history entry or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT *
                FROM backtest_history
                WHERE id = ?
            """, (history_id,))

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "id": row["id"],
                "ticker": row["ticker"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "run_type": row["run_type"],
                "created_at": row["created_at"],
                "title": row["title"],
                "summary_metrics": json.loads(row["summary_metrics"]) if row["summary_metrics"] else None,
                "results_data": json.loads(row["results_data"])
            }

    def delete_history(self, history_id: int) -> bool:
        """
        Delete a history entry by ID.

        Args:
            history_id: ID of the history entry to delete

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM backtest_history WHERE id = ?", (history_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_history_count(self, ticker_filter: Optional[str] = None) -> int:
        """
        Get total count of history entries.

        Args:
            ticker_filter: Optional ticker to filter by

        Returns:
            Total count of entries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if ticker_filter:
                cursor.execute("""
                    SELECT COUNT(*) FROM backtest_history
                    WHERE ticker LIKE ?
                """, (f"%{ticker_filter.upper()}%",))
            else:
                cursor.execute("SELECT COUNT(*) FROM backtest_history")

            return cursor.fetchone()[0]

    def _extract_summary_metrics(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary metrics from backtest results."""
        results = results_data.get("results", [])

        if not results:
            return {}

        # Find best strategy by total return
        best_strategy = max(results, key=lambda x: x.get("total_return", 0))

        # Calculate average metrics
        total_returns = [r.get("total_return", 0) for r in results]
        win_rates = [r.get("win_rate", 0) for r in results]
        sharpe_ratios = [r.get("sharpe_ratio", 0) for r in results]

        return {
            "num_strategies": len(results),
            "best_strategy": best_strategy.get("strategy"),
            "best_return": best_strategy.get("total_return"),
            "avg_return": sum(total_returns) / len(total_returns) if total_returns else 0,
            "avg_win_rate": sum(win_rates) / len(win_rates) if win_rates else 0,
            "avg_sharpe": sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else 0,
        }

    def _extract_optimization_summary(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary metrics from optimization results."""
        optimization_results = results_data.get("optimization_results", [])
        summary = results_data.get("summary", {})

        return {
            "num_strategies": len(optimization_results),
            "strategies_optimized": summary.get("strategies_optimized", 0),
            "avg_improvement": summary.get("average_improvement", 0),
            "total_combinations_tested": summary.get("total_combinations_tested", 0),
        }

    def _extract_portfolio_summary_metrics(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary metrics from portfolio backtest results."""
        results = results_data.get("results", [])

        if not results:
            return {}

        # Find best strategy by portfolio total return
        best_strategy = max(results, key=lambda x: x.get("portfolio_metrics", {}).get("total_return", 0))

        # Calculate average metrics
        total_returns = [r.get("portfolio_metrics", {}).get("total_return", 0) for r in results]
        sharpe_ratios = [r.get("portfolio_metrics", {}).get("sharpe_ratio", 0) for r in results]
        max_drawdowns = [r.get("portfolio_metrics", {}).get("max_drawdown", 0) for r in results]

        return {
            "num_strategies": len(results),
            "num_assets": len(results_data.get("tickers", [])),
            "best_strategy": best_strategy.get("strategy"),
            "best_return": best_strategy.get("portfolio_metrics", {}).get("total_return"),
            "avg_return": sum(total_returns) / len(total_returns) if total_returns else 0,
            "avg_sharpe": sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else 0,
            "avg_max_drawdown": sum(max_drawdowns) / len(max_drawdowns) if max_drawdowns else 0,
        }


# Global database instance
db = HistoryDatabase()
