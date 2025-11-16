"""
Test script for the Stock Analysis API
"""
import requests
import json
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

def test_health_check():
    """Test the root endpoint"""
    print("Testing health check...")
    response = requests.get(f"{API_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.status_code == 200

def test_get_strategies():
    """Test the strategies endpoint"""
    print("Testing get strategies...")
    response = requests.get(f"{API_URL}/api/v1/strategies")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Available strategies: {len(data['strategies'])}")
    for strategy in data['strategies']:
        print(f"  - {strategy['name']} ({strategy['id']})")
    print()
    return response.status_code == 200

def test_backtest():
    """Test the backtest endpoint"""
    print("Testing backtest...")

    # Calculate date range (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    payload = {
        "ticker": "AAPL",
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "strategies": ["sma_cross"]
    }

    print(f"Request: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{API_URL}/api/v1/backtest", json=payload)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Ticker: {data['ticker']}")
        print(f"Period: {data['startDate']} to {data['endDate']}")
        print(f"Price data points: {len(data['price_data'])}")
        print(f"\nResults:")
        for result in data['results']:
            print(f"  Strategy: {result['strategy']}")
            print(f"  Total Return: {result['total_return']:.2f}%")
            print(f"  Win Rate: {result['win_rate']:.2f}%")
            print(f"  Max Drawdown: {result['max_drawdown']:.2f}%")
            print(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            print(f"  Trades: {result['num_trades']}")
            print(f"  Signals: {len(result['signals'])}")
    else:
        print(f"Error: {response.text}")

    print()
    return response.status_code == 200

if __name__ == "__main__":
    print("=" * 60)
    print("Stock Analysis API Test Suite")
    print("=" * 60)
    print()

    try:
        results = {
            "Health Check": test_health_check(),
            "Get Strategies": test_get_strategies(),
            "Backtest": test_backtest()
        }

        print("=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        for test_name, passed in results.items():
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{test_name}: {status}")

        all_passed = all(results.values())
        print()
        if all_passed:
            print("All tests passed! ✓")
        else:
            print("Some tests failed. ✗")

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"ERROR: {e}")
