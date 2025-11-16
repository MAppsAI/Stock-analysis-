"""
Test all 25 strategies using synthetic SPY-like data
This workaround allows testing without yfinance dependency
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies import STRATEGY_MAP, calculate_metrics
import json


def generate_spy_like_data(start_date, end_date, initial_price=250, annual_return=0.10, volatility=0.15):
    """
    Generate synthetic stock data that mimics SPY behavior
    Uses geometric Brownian motion with SPY-like characteristics
    """
    # Generate trading days (excluding weekends)
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
    n_days = len(date_range)

    # Parameters for SPY-like movement
    dt = 1/252  # Daily time step (252 trading days per year)
    mu = annual_return  # Annual drift (SPY historical ~10%)
    sigma = volatility  # Annual volatility (SPY historical ~15%)

    # Generate random returns using geometric Brownian motion
    np.random.seed(42)  # For reproducibility
    returns = np.random.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), n_days)

    # Calculate price path
    price = initial_price * np.exp(np.cumsum(returns))

    # Generate OHLC data
    data = pd.DataFrame(index=date_range)
    data['Close'] = price

    # Generate realistic high/low/open based on close
    daily_range = sigma * np.sqrt(dt) * price * np.random.uniform(0.5, 1.5, n_days)
    data['High'] = data['Close'] + daily_range * np.random.uniform(0, 1, n_days)
    data['Low'] = data['Close'] - daily_range * np.random.uniform(0, 1, n_days)
    data['Open'] = data['Low'] + (data['High'] - data['Low']) * np.random.uniform(0.2, 0.8, n_days)

    # Generate volume (SPY typically 50-100M shares/day)
    data['Volume'] = np.random.normal(75_000_000, 25_000_000, n_days).astype(int)
    data['Volume'] = data['Volume'].clip(lower=10_000_000)  # Minimum volume

    # Ensure High is highest, Low is lowest
    data['High'] = data[['Open', 'High', 'Low', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'High', 'Low', 'Close']].min(axis=1)

    return data


def run_synthetic_backtest():
    """Run all 25 strategies on synthetic SPY data for 10 years"""

    # Set up date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10*365 + 50)  # Extra days for weekends

    print("=" * 80)
    print("COMPREHENSIVE STRATEGY BACKTEST - Synthetic SPY Data (Last 10 Years)")
    print("=" * 80)
    print(f"Ticker: SPY (Synthetic)")
    print(f"Start Date: {start_date.strftime('%Y-%m-%d')}")
    print(f"End Date: {end_date.strftime('%Y-%m-%d')}")
    print(f"Total Strategies: {len(STRATEGY_MAP)}")
    print(f"Data Generation: Geometric Brownian Motion (μ=10%, σ=15%)")
    print("=" * 80)
    print()

    # Generate synthetic SPY data
    print("Generating synthetic SPY data...")
    data = generate_spy_like_data(start_date, end_date)
    print(f"Generated {len(data)} trading days")
    print(f"Starting price: ${data['Close'].iloc[0]:.2f}")
    print(f"Ending price: ${data['Close'].iloc[-1]:.2f}")
    print(f"Total return (Buy & Hold): {((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100:.2f}%")
    print()

    # Store results
    all_results = []

    # Run each strategy
    print("Running backtests for all 25 strategies...")
    print()

    for i, (strategy_id, strategy_info) in enumerate(STRATEGY_MAP.items(), 1):
        strategy_name = strategy_info['name']
        strategy_category = strategy_info['category']
        strategy_func = strategy_info['func']

        print(f"[{i}/25] Testing: {strategy_name} ({strategy_category})...", end=" ")

        try:
            # Create a copy of data for this strategy
            strategy_data = data.copy()

            # Run strategy
            signals, trade_signals = strategy_func(strategy_data)

            # Calculate metrics
            metrics = calculate_metrics(strategy_data, signals)

            # Store result
            result = {
                'id': strategy_id,
                'name': strategy_name,
                'category': strategy_category,
                'total_return': metrics['total_return'],
                'win_rate': metrics['win_rate'],
                'max_drawdown': metrics['max_drawdown'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'num_trades': metrics['num_trades'],
                'num_signals': len(trade_signals)
            }
            all_results.append(result)

            print(f"✓ Return: {metrics['total_return']:7.2f}% | "
                  f"Sharpe: {metrics['sharpe_ratio']:5.2f} | "
                  f"Trades: {metrics['num_trades']}")

        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            all_results.append({
                'id': strategy_id,
                'name': strategy_name,
                'category': strategy_category,
                'total_return': 0.0,
                'win_rate': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'num_trades': 0,
                'num_signals': 0,
                'error': str(e)
            })

    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()

    # Create DataFrame for analysis
    df = pd.DataFrame(all_results)

    # Sort by total return
    df_sorted = df.sort_values('total_return', ascending=False)

    # Print top performers
    print("TOP 10 BEST PERFORMING STRATEGIES (by Total Return):")
    print("-" * 80)
    for idx, (i, row) in enumerate(df_sorted.head(10).iterrows(), 1):
        print(f"{idx:2d}. {row['name']:30s} | Return: {row['total_return']:8.2f}% | "
              f"Sharpe: {row['sharpe_ratio']:6.2f} | "
              f"Win Rate: {row['win_rate']:6.2f}% | "
              f"Drawdown: {row['max_drawdown']:7.2f}%")
    print()

    # Print worst performers
    print("BOTTOM 5 WORST PERFORMING STRATEGIES:")
    print("-" * 80)
    for idx, (i, row) in enumerate(df_sorted.tail(5).iterrows(), 1):
        print(f"{idx}. {row['name']:30s} | Return: {row['total_return']:8.2f}% | "
              f"Sharpe: {row['sharpe_ratio']:6.2f} | "
              f"Drawdown: {row['max_drawdown']:7.2f}%")
    print()

    # Sort by Sharpe ratio
    df_sharpe = df.sort_values('sharpe_ratio', ascending=False)

    print("TOP 10 BEST RISK-ADJUSTED RETURNS (by Sharpe Ratio):")
    print("-" * 80)
    for idx, (i, row) in enumerate(df_sharpe.head(10).iterrows(), 1):
        print(f"{idx:2d}. {row['name']:30s} | Sharpe: {row['sharpe_ratio']:6.2f} | "
              f"Return: {row['total_return']:8.2f}% | "
              f"Drawdown: {row['max_drawdown']:7.2f}%")
    print()

    # Category analysis
    print("PERFORMANCE BY CATEGORY:")
    print("-" * 80)
    category_stats = df.groupby('category').agg({
        'total_return': ['mean', 'max'],
        'sharpe_ratio': ['mean', 'max'],
        'num_trades': 'mean'
    }).round(2)

    for category in df['category'].unique():
        cat_data = df[df['category'] == category]
        avg_return = cat_data['total_return'].mean()
        max_return = cat_data['total_return'].max()
        avg_sharpe = cat_data['sharpe_ratio'].mean()
        print(f"{category:20s} | Avg Return: {avg_return:7.2f}% | "
              f"Max Return: {max_return:7.2f}% | Avg Sharpe: {avg_sharpe:5.2f}")
    print()

    # Key insights
    print("KEY INSIGHTS:")
    print("-" * 80)
    best_strategy = df_sorted.iloc[0]
    best_sharpe = df_sharpe.iloc[0]
    profitable_strategies = len(df[df['total_return'] > 0])
    avg_return = df['total_return'].mean()
    avg_sharpe = df['sharpe_ratio'].mean()
    buy_hold_return = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100

    print(f"🏆 BEST OVERALL STRATEGY: {best_strategy['name']}")
    print(f"   Total Return: {best_strategy['total_return']:.2f}%")
    print(f"   Sharpe Ratio: {best_strategy['sharpe_ratio']:.2f}")
    print(f"   Category: {best_strategy['category']}")
    print(f"   Number of Trades: {best_strategy['num_trades']}")
    print()
    print(f"📊 BEST RISK-ADJUSTED STRATEGY: {best_sharpe['name']}")
    print(f"   Sharpe Ratio: {best_sharpe['sharpe_ratio']:.2f}")
    print(f"   Total Return: {best_sharpe['total_return']:.2f}%")
    print(f"   Category: {best_sharpe['category']}")
    print()
    print(f"✅ Profitable Strategies: {profitable_strategies}/{len(df)} ({profitable_strategies/len(df)*100:.1f}%)")
    print(f"📈 Average Return Across All Strategies: {avg_return:.2f}%")
    print(f"📉 Average Sharpe Ratio: {avg_sharpe:.2f}")
    print(f"💰 Buy & Hold Return (SPY): {buy_hold_return:.2f}%")
    print(f"⚡ Outperformance: {profitable_strategies} strategies beat 0% return")
    print()

    # Best strategy per category
    print("BEST STRATEGY PER CATEGORY:")
    print("-" * 80)
    for category in sorted(df['category'].unique()):
        cat_df = df[df['category'] == category].sort_values('total_return', ascending=False)
        best = cat_df.iloc[0]
        print(f"{category:20s} → {best['name']:30s} | "
              f"Return: {best['total_return']:7.2f}% | Sharpe: {best['sharpe_ratio']:5.2f}")
    print()

    # Save results to JSON
    output_file = '/home/user/Stock-analysis-/backend/spy_backtest_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'ticker': 'SPY (Synthetic)',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'trading_days': len(data),
            'buy_hold_return': float(buy_hold_return),
            'results': all_results,
            'summary': {
                'best_strategy': best_strategy['name'],
                'best_return': float(best_strategy['total_return']),
                'best_sharpe_strategy': best_sharpe['name'],
                'best_sharpe': float(best_sharpe['sharpe_ratio']),
                'profitable_count': int(profitable_strategies),
                'total_strategies': len(df),
                'avg_return': float(avg_return),
                'avg_sharpe': float(avg_sharpe)
            }
        }, f, indent=2)

    print(f"✅ Results saved to: {output_file}")
    print("=" * 80)

    return df_sorted


if __name__ == "__main__":
    results = run_synthetic_backtest()
