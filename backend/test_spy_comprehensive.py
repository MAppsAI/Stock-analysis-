"""
Comprehensive backtest of all 25 strategies on SPY over the last 10 years
This script tests all strategies and produces a detailed performance report
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from strategies import STRATEGY_MAP, calculate_metrics
import json


def run_comprehensive_backtest():
    """Run all 25 strategies on SPY for the last 10 years"""

    # Set up date range (last 10 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10*365)

    print("=" * 80)
    print("COMPREHENSIVE STRATEGY BACKTEST - SPY (Last 10 Years)")
    print("=" * 80)
    print(f"Ticker: SPY")
    print(f"Start Date: {start_date.strftime('%Y-%m-%d')}")
    print(f"End Date: {end_date.strftime('%Y-%m-%d')}")
    print(f"Total Strategies: {len(STRATEGY_MAP)}")
    print("=" * 80)
    print()

    # Download SPY data
    print("Downloading SPY data...")
    ticker = yf.Ticker("SPY")
    data = ticker.history(start=start_date, end=end_date)

    if data.empty:
        print("ERROR: No data retrieved for SPY")
        return

    print(f"Data points: {len(data)} trading days")
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

        print(f"[{i}/25] Testing: {strategy_name} ({strategy_category})...")

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

            print(f"    ✓ Return: {metrics['total_return']:.2f}% | "
                  f"Sharpe: {metrics['sharpe_ratio']:.2f} | "
                  f"Trades: {metrics['num_trades']}")

        except Exception as e:
            print(f"    ✗ ERROR: {str(e)}")
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
    for i, row in df_sorted.head(10).iterrows():
        print(f"{row['name']:30s} | Return: {row['total_return']:8.2f}% | "
              f"Sharpe: {row['sharpe_ratio']:6.2f} | "
              f"Win Rate: {row['win_rate']:6.2f}% | "
              f"Drawdown: {row['max_drawdown']:7.2f}%")
    print()

    # Print worst performers
    print("BOTTOM 5 WORST PERFORMING STRATEGIES:")
    print("-" * 80)
    for i, row in df_sorted.tail(5).iterrows():
        print(f"{row['name']:30s} | Return: {row['total_return']:8.2f}% | "
              f"Sharpe: {row['sharpe_ratio']:6.2f} | "
              f"Win Rate: {row['win_rate']:6.2f}% | "
              f"Drawdown: {row['max_drawdown']:7.2f}%")
    print()

    # Sort by Sharpe ratio
    df_sharpe = df.sort_values('sharpe_ratio', ascending=False)

    print("TOP 10 BEST RISK-ADJUSTED RETURNS (by Sharpe Ratio):")
    print("-" * 80)
    for i, row in df_sharpe.head(10).iterrows():
        print(f"{row['name']:30s} | Sharpe: {row['sharpe_ratio']:6.2f} | "
              f"Return: {row['total_return']:8.2f}% | "
              f"Win Rate: {row['win_rate']:6.2f}% | "
              f"Drawdown: {row['max_drawdown']:7.2f}%")
    print()

    # Category analysis
    print("PERFORMANCE BY CATEGORY:")
    print("-" * 80)
    category_stats = df.groupby('category').agg({
        'total_return': 'mean',
        'sharpe_ratio': 'mean',
        'win_rate': 'mean',
        'max_drawdown': 'mean',
        'num_trades': 'mean'
    }).round(2)

    for category, stats in category_stats.iterrows():
        print(f"{category:20s} | Avg Return: {stats['total_return']:7.2f}% | "
              f"Avg Sharpe: {stats['sharpe_ratio']:5.2f} | "
              f"Avg Win Rate: {stats['win_rate']:5.2f}%")
    print()

    # Key insights
    print("KEY INSIGHTS:")
    print("-" * 80)
    best_strategy = df_sorted.iloc[0]
    best_sharpe = df_sharpe.iloc[0]
    profitable_strategies = len(df[df['total_return'] > 0])
    avg_return = df['total_return'].mean()
    avg_sharpe = df['sharpe_ratio'].mean()

    print(f"✓ Best Overall Strategy: {best_strategy['name']}")
    print(f"  - Total Return: {best_strategy['total_return']:.2f}%")
    print(f"  - Sharpe Ratio: {best_strategy['sharpe_ratio']:.2f}")
    print(f"  - Category: {best_strategy['category']}")
    print()
    print(f"✓ Best Risk-Adjusted Strategy: {best_sharpe['name']}")
    print(f"  - Sharpe Ratio: {best_sharpe['sharpe_ratio']:.2f}")
    print(f"  - Total Return: {best_sharpe['total_return']:.2f}%")
    print(f"  - Category: {best_sharpe['category']}")
    print()
    print(f"✓ Profitable Strategies: {profitable_strategies}/{len(df)} ({profitable_strategies/len(df)*100:.1f}%)")
    print(f"✓ Average Return Across All Strategies: {avg_return:.2f}%")
    print(f"✓ Average Sharpe Ratio: {avg_sharpe:.2f}")
    print()

    # Best strategy per category
    print("BEST STRATEGY PER CATEGORY:")
    print("-" * 80)
    for category in df['category'].unique():
        cat_df = df[df['category'] == category].sort_values('total_return', ascending=False)
        best = cat_df.iloc[0]
        print(f"{category:20s} | {best['name']:30s} | Return: {best['total_return']:7.2f}%")
    print()

    # Save results to JSON
    output_file = 'spy_backtest_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'ticker': 'SPY',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
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

    print(f"Results saved to: {output_file}")
    print("=" * 80)

    return df_sorted


if __name__ == "__main__":
    results = run_comprehensive_backtest()
