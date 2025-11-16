"""
Simple test to verify history database functionality.
Run this after installing dependencies with: pip install -r requirements.txt
"""

from database import HistoryDatabase
import os
import json

def test_history_database():
    # Use a test database
    test_db = HistoryDatabase("test_history.db")

    # Test data
    test_backtest_data = {
        "ticker": "AAPL",
        "startDate": "2023-01-01",
        "endDate": "2023-12-31",
        "results": [
            {
                "strategy": "SMA Cross",
                "total_return": 15.5,
                "win_rate": 55.0,
                "max_drawdown": -10.2,
                "sharpe_ratio": 1.2,
                "num_trades": 10,
                "signals": []
            }
        ],
        "price_data": []
    }

    print("Testing backtest history save...")
    backtest_id = test_db.save_backtest(
        ticker="AAPL",
        start_date="2023-01-01",
        end_date="2023-12-31",
        results_data=test_backtest_data
    )
    print(f"✓ Backtest saved with ID: {backtest_id}")

    print("\nTesting history retrieval...")
    history = test_db.get_all_history()
    print(f"✓ Retrieved {len(history)} history entries")

    print("\nTesting history detail retrieval...")
    detail = test_db.get_history_by_id(backtest_id)
    print(f"✓ Retrieved detail for ID {backtest_id}: {detail['ticker']}")

    print("\nTesting ticker search...")
    aapl_history = test_db.get_all_history(ticker_filter="AAPL")
    print(f"✓ Found {len(aapl_history)} entries for AAPL")

    print("\nTesting history deletion...")
    deleted = test_db.delete_history(backtest_id)
    print(f"✓ Deletion {'successful' if deleted else 'failed'}")

    # Cleanup
    os.remove("test_history.db")
    print("\n✓ All tests passed!")

if __name__ == "__main__":
    test_history_database()
