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
        strategy_type: Type of strategy to optimize
        data: Historical price data
        max_combinations: Maximum parameter combinations to test

    Returns:
        Dictionary with optimization results
    """
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
