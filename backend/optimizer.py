"""
Hyperparameter Optimization Engine
Parallel testing of strategy parameters to find optimal configurations
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
import warnings
warnings.filterwarnings('ignore')


# Parameter ranges for each strategy type
STRATEGY_PARAMETERS = {
    # SMA Crossover strategies
    'sma_cross': {
        'short_window': [5, 10, 20, 30, 50],
        'long_window': [50, 100, 150, 200, 250],
    },

    # EMA Crossover strategies
    'ema_cross': {
        'short_span': [8, 9, 12, 15, 20],
        'long_span': [21, 26, 30, 40, 50],
    },

    # RSI strategies
    'rsi': {
        'period': [7, 10, 14, 20, 25],
        'oversold': [20, 25, 30, 35],
        'overbought': [65, 70, 75, 80],
    },

    # Bollinger Bands
    'bollinger': {
        'period': [10, 15, 20, 25, 30],
        'std_dev': [1.5, 2.0, 2.5, 3.0],
    },

    # MACD
    'macd': {
        'fast': [8, 10, 12, 15],
        'slow': [20, 26, 30, 35],
        'signal': [5, 7, 9, 12],
    },

    # Stochastic
    'stochastic': {
        'k_period': [10, 14, 20, 25],
        'oversold': [15, 20, 25],
        'overbought': [75, 80, 85],
    },

    # ADX
    'adx': {
        'period': [10, 14, 20, 25],
        'threshold': [20, 25, 30, 35],
    },

    # ATR-based
    'atr': {
        'period': [10, 14, 20, 25],
        'multiplier': [2.0, 2.5, 3.0, 3.5, 4.0],
    },

    # Momentum
    'roc': {
        'period': [5, 10, 12, 15, 20],
    },

    # Volume
    'volume': {
        'period': [10, 15, 20, 25, 30],
        'threshold': [1.2, 1.5, 1.8, 2.0, 2.5],
    },
}


# =============================================================================
# COMBINED STRATEGY OPTIMIZATION PARAMETERS
# =============================================================================

# Entry condition parameters
ENTRY_PARAMETERS = {
    'sma_cross': {
        'short': [10, 20, 30, 50],
        'long': [50, 100, 150, 200],
    },
    'ema_cross': {
        'short': [8, 12, 15, 20],
        'long': [21, 26, 30, 40],
    },
    'rsi_oversold': {
        'period': [10, 14, 20],
        'threshold': [20, 25, 30, 35],
    },
    'bollinger_lower': {
        'period': [15, 20, 25],
        'std_dev': [1.5, 2.0, 2.5],
    },
    'macd_cross': {},  # Uses default MACD parameters
    'stochastic_oversold': {
        'period': [10, 14, 20],
        'threshold': [15, 20, 25],
    },
    'volume_breakout': {
        'period': [15, 20, 25],
        'vol_mult': [1.3, 1.5, 1.8, 2.0],
    },
    'donchian_breakout': {
        'period': [10, 20, 30, 40],
    },
    'price_above_vwap': {},  # No parameters
    'adx_strong': {
        'period': [10, 14, 20],
        'threshold': [20, 25, 30],
    },
    'cci_oversold': {
        'period': [15, 20, 25],
        'threshold': [-120, -100, -80],
    },
    'roc_positive': {
        'period': [5, 10, 12, 15, 20],
    },
}

# Exit condition parameters
EXIT_PARAMETERS = {
    'sma_cross': {
        'short': [10, 20, 30, 50],
        'long': [50, 100, 150, 200],
    },
    'ema_cross': {
        'short': [8, 12, 15, 20],
        'long': [21, 26, 30, 40],
    },
    'rsi_overbought': {
        'period': [10, 14, 20],
        'threshold': [65, 70, 75, 80],
    },
    'bollinger_upper': {
        'period': [15, 20, 25],
        'std_dev': [1.5, 2.0, 2.5],
    },
    'macd_cross': {},  # Uses default MACD parameters
    'stochastic_overbought': {
        'period': [10, 14, 20],
        'threshold': [75, 80, 85],
    },
    'volume_breakout': {
        'period': [15, 20, 25],
        'vol_mult': [1.3, 1.5, 1.8, 2.0],
    },
    'donchian_breakdown': {
        'period': [10, 20, 30, 40],
    },
    'price_below_vwap': {},  # No parameters
    'adx_weak': {
        'period': [10, 14, 20],
        'threshold': [20, 25, 30],
    },
    'cci_overbought': {
        'period': [15, 20, 25],
        'threshold': [80, 100, 120],
    },
    'roc_negative': {
        'period': [5, 10, 12, 15, 20],
    },
    'trailing_stop': {
        'stop_pct': [3.0, 4.0, 5.0, 7.0, 10.0],
    },
    'take_profit': {
        'profit_pct': [5.0, 7.5, 10.0, 12.5, 15.0, 20.0],
    },
}


def optimize_sma_cross(data: pd.DataFrame, params: Dict) -> Tuple[float, Dict]:
    """Optimize SMA crossover strategy"""
    from strategies import calculate_metrics

    short = params['short_window']
    long = params['long_window']

    if short >= long:
        return -999, params  # Invalid combination

    try:
        df = data.copy()
        df['SMA_Short'] = df['Close'].rolling(window=short).mean()
        df['SMA_Long'] = df['Close'].rolling(window=long).mean()
        df['Signal'] = 0
        df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1
        df.loc[df['SMA_Short'] < df['SMA_Long'], 'Signal'] = -1

        metrics = calculate_metrics(df, df['Signal'])

        # Optimization score: weighted combination of return and Sharpe ratio
        score = metrics['total_return'] * 0.6 + metrics['sharpe_ratio'] * 40 * 0.4

        return score, {**params, **metrics}
    except:
        return -999, params


def optimize_rsi(data: pd.DataFrame, params: Dict) -> Tuple[float, Dict]:
    """Optimize RSI strategy"""
    from strategies import calculate_metrics

    period = params['period']
    oversold = params['oversold']
    overbought = params['overbought']

    if oversold >= overbought:
        return -999, params

    try:
        df = data.copy()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        df['Signal'] = 0
        df.loc[df['RSI'] < oversold, 'Signal'] = 1
        df.loc[df['RSI'] > overbought, 'Signal'] = -1
        df['Signal'] = df['Signal'].replace(0, method='ffill').fillna(0)

        metrics = calculate_metrics(df, df['Signal'])
        score = metrics['total_return'] * 0.6 + metrics['sharpe_ratio'] * 40 * 0.4

        return score, {**params, **metrics}
    except:
        return -999, params


def optimize_bollinger(data: pd.DataFrame, params: Dict) -> Tuple[float, Dict]:
    """Optimize Bollinger Bands strategy"""
    from strategies import calculate_metrics

    period = params['period']
    std_dev = params['std_dev']

    try:
        df = data.copy()
        df['SMA'] = df['Close'].rolling(window=period).mean()
        df['STD'] = df['Close'].rolling(window=period).std()
        df['Upper_BB'] = df['SMA'] + (std_dev * df['STD'])
        df['Lower_BB'] = df['SMA'] - (std_dev * df['STD'])

        df['Signal'] = 0
        df.loc[df['Close'] <= df['Lower_BB'], 'Signal'] = 1
        df.loc[df['Close'] >= df['Upper_BB'], 'Signal'] = -1
        df['Signal'] = df['Signal'].replace(0, method='ffill').fillna(0)

        metrics = calculate_metrics(df, df['Signal'])
        score = metrics['total_return'] * 0.6 + metrics['sharpe_ratio'] * 40 * 0.4

        return score, {**params, **metrics}
    except:
        return -999, params


def optimize_macd(data: pd.DataFrame, params: Dict) -> Tuple[float, Dict]:
    """Optimize MACD strategy"""
    from strategies import calculate_metrics

    fast = params['fast']
    slow = params['slow']
    signal = params['signal']

    if fast >= slow:
        return -999, params

    try:
        df = data.copy()
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['Signal_Line'] = df['MACD'].ewm(span=signal, adjust=False).mean()

        df['Signal'] = 0
        df.loc[df['MACD'] > df['Signal_Line'], 'Signal'] = 1
        df.loc[df['MACD'] < df['Signal_Line'], 'Signal'] = -1

        metrics = calculate_metrics(df, df['Signal'])
        score = metrics['total_return'] * 0.6 + metrics['sharpe_ratio'] * 40 * 0.4

        return score, {**params, **metrics}
    except:
        return -999, params


OPTIMIZERS = {
    'sma_cross': optimize_sma_cross,
    'rsi': optimize_rsi,
    'bollinger': optimize_bollinger,
    'macd': optimize_macd,
}


def optimize_strategy(strategy_type: str, data: pd.DataFrame, max_combinations: int = 50) -> Dict[str, Any]:
    """
    Optimize a single strategy's parameters

    Args:
        strategy_type: Type of strategy to optimize (e.g., 'sma_cross' or 'combo_rsi_oversold_entry_trailing_stop_exit')
        data: Historical price data
        max_combinations: Maximum parameter combinations to test

    Returns:
        Dictionary with optimization results
    """
    # Check if this is a combined strategy
    if strategy_type.startswith('combo_'):
        # Parse combined strategy ID: combo_{entry}_entry_{exit}_exit
        parts = strategy_type.replace('combo_', '').split('_entry_')
        if len(parts) == 2:
            entry_type = parts[0]
            exit_type = parts[1].replace('_exit', '')
            return optimize_combined_strategy(entry_type, exit_type, data, max_combinations)
        else:
            return {
                'strategy_type': strategy_type,
                'status': 'error',
                'message': f'Invalid combined strategy format: {strategy_type}'
            }

    # Original strategy optimization
    if strategy_type not in STRATEGY_PARAMETERS:
        return {
            'strategy_type': strategy_type,
            'status': 'unsupported',
            'message': f'Optimization not available for {strategy_type}'
        }

    if strategy_type not in OPTIMIZERS:
        return {
            'strategy_type': strategy_type,
            'status': 'unsupported',
            'message': f'Optimizer not implemented for {strategy_type}'
        }

    # Generate parameter combinations
    param_ranges = STRATEGY_PARAMETERS[strategy_type]
    keys = list(param_ranges.keys())
    values = [param_ranges[k] for k in keys]

    combinations = list(product(*values))

    # Limit combinations if too many
    if len(combinations) > max_combinations:
        # Sample random combinations
        np.random.seed(42)
        indices = np.random.choice(len(combinations), max_combinations, replace=False)
        combinations = [combinations[i] for i in indices]

    # Test each combination
    optimizer = OPTIMIZERS[strategy_type]
    results = []

    for combo in combinations:
        params = dict(zip(keys, combo))
        score, result = optimizer(data, params)

        if score > -999:  # Valid result
            results.append({
                'params': params,
                'score': score,
                'metrics': result
            })

    if not results:
        return {
            'strategy_type': strategy_type,
            'status': 'failed',
            'message': 'No valid parameter combinations found'
        }

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    best_result = results[0]

    return {
        'strategy_type': strategy_type,
        'status': 'success',
        'best_params': best_result['params'],
        'best_score': best_result['score'],
        'best_metrics': best_result['metrics'],
        'total_tested': len(results),
        'all_results': results[:10],  # Top 10 results
        'param_ranges': param_ranges,
    }


def optimize_multiple_strategies(strategies: List[str], data: pd.DataFrame,
                                 max_workers: int = 4) -> Dict[str, Any]:
    """
    Optimize multiple strategies in parallel

    Args:
        strategies: List of strategy types to optimize
        data: Historical price data
        max_workers: Number of parallel workers

    Returns:
        Dictionary with all optimization results
    """
    results = {}

    # Use ProcessPoolExecutor for parallel optimization
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit optimization tasks
        future_to_strategy = {
            executor.submit(optimize_strategy, strategy, data): strategy
            for strategy in strategies
        }

        # Collect results as they complete
        for future in as_completed(future_to_strategy):
            strategy = future_to_strategy[future]
            try:
                result = future.result()
                results[strategy] = result
            except Exception as e:
                results[strategy] = {
                    'strategy_type': strategy,
                    'status': 'error',
                    'message': str(e)
                }

    return results


def generate_optimization_summary(optimization_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a summary of optimization results"""
    successful = []
    failed = []
    total_combinations = 0

    for strategy, result in optimization_results.items():
        if result['status'] == 'success':
            successful.append({
                'strategy': strategy,
                'improvement': result['best_score'],
                'best_params': result['best_params'],
                'return': result['best_metrics'].get('total_return', 0),
                'sharpe': result['best_metrics'].get('sharpe_ratio', 0),
            })
            total_combinations += result.get('total_tested', 0)
        else:
            failed.append(strategy)

    # Sort by improvement
    successful.sort(key=lambda x: x['improvement'], reverse=True)

    # Calculate average improvement
    avg_improvement = sum(s['improvement'] for s in successful) / len(successful) if successful else 0

    # Get best strategy
    best = successful[0] if successful else None

    summary = {
        'total_optimized': len(optimization_results),
        'successful': len(successful),
        'failed': len(failed),
        'total_combinations': total_combinations,
        'avg_improvement': avg_improvement,
        'top_optimized': successful[:5],
        'all_successful': successful,
        'failed_strategies': failed,
    }

    # Add best strategy info if available
    if best:
        summary['best_strategy_type'] = best['strategy']
        summary['best_score'] = best['improvement']
        summary['best_params'] = best['best_params']

    return summary


# =============================================================================
# COMBINED STRATEGY OPTIMIZATION
# =============================================================================

def build_parameterized_entry(entry_type: str, params: Dict) -> callable:
    """Build an entry condition function with specific parameters"""
    from strategies import (
        entry_sma_cross_bullish, entry_ema_cross_bullish, entry_rsi_oversold,
        entry_bollinger_lower, entry_macd_cross_bullish, entry_stochastic_oversold,
        entry_volume_breakout_bullish, entry_donchian_breakout, entry_price_above_vwap,
        entry_adx_strong_trend, entry_cci_oversold, entry_roc_positive
    )

    entry_funcs = {
        'sma_cross': entry_sma_cross_bullish,
        'ema_cross': entry_ema_cross_bullish,
        'rsi_oversold': entry_rsi_oversold,
        'bollinger_lower': entry_bollinger_lower,
        'macd_cross': entry_macd_cross_bullish,
        'stochastic_oversold': entry_stochastic_oversold,
        'volume_breakout': entry_volume_breakout_bullish,
        'donchian_breakout': entry_donchian_breakout,
        'price_above_vwap': entry_price_above_vwap,
        'adx_strong': entry_adx_strong_trend,
        'cci_oversold': entry_cci_oversold,
        'roc_positive': entry_roc_positive,
    }

    func = entry_funcs[entry_type]
    return lambda data: func(data, **params) if params else func(data)


def build_parameterized_exit(exit_type: str, params: Dict) -> callable:
    """Build an exit condition function with specific parameters"""
    from strategies import (
        exit_sma_cross_bearish, exit_ema_cross_bearish, exit_rsi_overbought,
        exit_bollinger_upper, exit_macd_cross_bearish, exit_stochastic_overbought,
        exit_volume_breakout_bearish, exit_donchian_breakdown, exit_price_below_vwap,
        exit_adx_weak_trend, exit_cci_overbought, exit_roc_negative,
        exit_trailing_stop, exit_take_profit
    )

    exit_funcs = {
        'sma_cross': exit_sma_cross_bearish,
        'ema_cross': exit_ema_cross_bearish,
        'rsi_overbought': exit_rsi_overbought,
        'bollinger_upper': exit_bollinger_upper,
        'macd_cross': exit_macd_cross_bearish,
        'stochastic_overbought': exit_stochastic_overbought,
        'volume_breakout': exit_volume_breakout_bearish,
        'donchian_breakdown': exit_donchian_breakdown,
        'price_below_vwap': exit_price_below_vwap,
        'adx_weak': exit_adx_weak_trend,
        'cci_overbought': exit_cci_overbought,
        'roc_negative': exit_roc_negative,
        'trailing_stop': exit_trailing_stop,
        'take_profit': exit_take_profit,
    }

    func = exit_funcs[exit_type]
    return lambda data: func(data, **params) if params else func(data)


def optimize_combined_strategy(entry_type: str, exit_type: str, data: pd.DataFrame,
                               max_combinations: int = 100) -> Dict[str, Any]:
    """
    Optimize parameters for a combined entry/exit strategy

    Args:
        entry_type: Type of entry condition (e.g., 'sma_cross', 'rsi_oversold')
        exit_type: Type of exit condition (e.g., 'rsi_overbought', 'trailing_stop')
        data: Historical price data
        max_combinations: Maximum parameter combinations to test

    Returns:
        Dictionary with optimization results
    """
    from strategies import calculate_metrics, combine_entry_exit

    # Get parameter ranges
    entry_params = ENTRY_PARAMETERS.get(entry_type, {})
    exit_params = EXIT_PARAMETERS.get(exit_type, {})

    # Generate parameter combinations
    entry_combinations = [{}]  # Start with empty dict for no-param strategies
    if entry_params:
        entry_keys = list(entry_params.keys())
        entry_values = [entry_params[k] for k in entry_keys]
        entry_combinations = [dict(zip(entry_keys, combo)) for combo in product(*entry_values)]

    exit_combinations = [{}]
    if exit_params:
        exit_keys = list(exit_params.keys())
        exit_values = [exit_params[k] for k in exit_keys]
        exit_combinations = [dict(zip(exit_keys, combo)) for combo in product(*exit_values)]

    # Create all entry × exit combinations
    all_combinations = []
    for entry_combo in entry_combinations:
        for exit_combo in exit_combinations:
            # Validate parameter constraints
            valid = True

            # SMA/EMA: short must be < long
            if 'short' in entry_combo and 'long' in entry_combo:
                if entry_combo['short'] >= entry_combo['long']:
                    valid = False
            if 'short' in exit_combo and 'long' in exit_combo:
                if exit_combo['short'] >= exit_combo['long']:
                    valid = False

            # RSI/Stochastic: oversold < overbought
            if 'threshold' in entry_combo and entry_type in ['rsi_oversold', 'stochastic_oversold']:
                if 'threshold' in exit_combo and exit_type in ['rsi_overbought', 'stochastic_overbought']:
                    # Only compare if same period
                    if entry_combo.get('period') == exit_combo.get('period'):
                        if entry_combo['threshold'] >= exit_combo['threshold']:
                            valid = False

            if valid:
                all_combinations.append({
                    'entry': entry_combo,
                    'exit': exit_combo
                })

    # Limit combinations if too many
    if len(all_combinations) > max_combinations:
        np.random.seed(42)
        indices = np.random.choice(len(all_combinations), max_combinations, replace=False)
        all_combinations = [all_combinations[i] for i in indices]

    # Test each combination
    results = []
    for combo in all_combinations:
        try:
            df = data.copy()

            # Build parameterized entry and exit functions
            entry_func = build_parameterized_entry(entry_type, combo['entry'])
            exit_func = build_parameterized_exit(exit_type, combo['exit'])

            # Create combined strategy
            combined_func = combine_entry_exit(entry_func, exit_func)

            # Run strategy
            signals, _ = combined_func(df)

            # Calculate metrics
            metrics = calculate_metrics(df, signals)

            # Calculate score
            score = metrics['total_return'] * 0.6 + metrics['sharpe_ratio'] * 40 * 0.4

            if score > -999:
                results.append({
                    'params': combo,
                    'score': score,
                    'metrics': metrics
                })
        except Exception as e:
            # Skip failed combinations
            continue

    if not results:
        return {
            'strategy_type': f'{entry_type}_entry_{exit_type}_exit',
            'status': 'failed',
            'message': 'No valid parameter combinations found'
        }

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    best_result = results[0]

    return {
        'strategy_type': f'{entry_type}_entry_{exit_type}_exit',
        'entry_type': entry_type,
        'exit_type': exit_type,
        'status': 'success',
        'best_params': best_result['params'],
        'best_score': best_result['score'],
        'best_metrics': best_result['metrics'],
        'total_tested': len(results),
        'all_results': results[:10],  # Top 10 results
        'param_ranges': {
            'entry': entry_params,
            'exit': exit_params
        },
    }
