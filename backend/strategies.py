import pandas as pd
import numpy as np
from typing import Tuple, List


def extract_signals(data: pd.DataFrame, position_col: str = 'Position') -> List[dict]:
    """Helper function to extract buy/sell signals from position changes"""
    signals = []
    buy_signals = data[data[position_col] == 2.0]
    sell_signals = data[data[position_col] == -2.0]

    for idx, row in buy_signals.iterrows():
        signals.append({
            'date': idx.strftime('%Y-%m-%d'),
            'price': float(row['Close']),
            'type': 'buy'
        })

    for idx, row in sell_signals.iterrows():
        signals.append({
            'date': idx.strftime('%Y-%m-%d'),
            'price': float(row['Close']),
            'type': 'sell'
        })

    signals.sort(key=lambda x: x['date'])
    return signals


# =============================================================================
# TREND-FOLLOWING STRATEGIES
# =============================================================================

def calculate_sma_cross_50_200(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """SMA 50/200 Cross - Golden Cross/Death Cross"""
    data['SMA_Short'] = data['Close'].rolling(window=50).mean()
    data['SMA_Long'] = data['Close'].rolling(window=200).mean()
    data['Signal'] = 0
    data.loc[data['SMA_Short'] > data['SMA_Long'], 'Signal'] = 1
    data.loc[data['SMA_Short'] < data['SMA_Long'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_sma_cross_20_50(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """SMA 20/50 Cross - Faster crossover"""
    data['SMA_Short'] = data['Close'].rolling(window=20).mean()
    data['SMA_Long'] = data['Close'].rolling(window=50).mean()
    data['Signal'] = 0
    data.loc[data['SMA_Short'] > data['SMA_Long'], 'Signal'] = 1
    data.loc[data['SMA_Short'] < data['SMA_Long'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_ema_cross(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """EMA 12/26 Cross - Exponential moving average crossover"""
    data['EMA_Short'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA_Long'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_Short'] > data['EMA_Long'], 'Signal'] = 1
    data.loc[data['EMA_Short'] < data['EMA_Long'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_macd(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """MACD Crossover - Moving Average Convergence Divergence"""
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['MACD'] > data['Signal_Line'], 'Signal'] = 1
    data.loc[data['MACD'] < data['Signal_Line'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_triple_ma(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Triple Moving Average - All 3 must align"""
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_100'] = data['Close'].rolling(window=100).mean()
    data['Signal'] = 0
    bullish = (data['SMA_20'] > data['SMA_50']) & (data['SMA_50'] > data['SMA_100'])
    bearish = (data['SMA_20'] < data['SMA_50']) & (data['SMA_50'] < data['SMA_100'])
    data.loc[bullish, 'Signal'] = 1
    data.loc[bearish, 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_donchian_breakout(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Donchian Channel Breakout - 20-day high/low breakout"""
    data['Upper'] = data['High'].rolling(window=20).max()
    data['Lower'] = data['Low'].rolling(window=20).min()
    data['Signal'] = 0
    data.loc[data['Close'] >= data['Upper'].shift(1), 'Signal'] = 1
    data.loc[data['Close'] <= data['Lower'].shift(1), 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_adx_trend(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """ADX Trend Strength - Buy when ADX > 25 and +DI > -DI"""
    period = 14

    # Calculate True Range
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)

    # Calculate Directional Movement
    data['DMplus'] = np.where((data['High'] - data['High'].shift(1)) > (data['Low'].shift(1) - data['Low']),
                              data['High'] - data['High'].shift(1), 0)
    data['DMplus'] = np.where(data['DMplus'] < 0, 0, data['DMplus'])
    data['DMminus'] = np.where((data['Low'].shift(1) - data['Low']) > (data['High'] - data['High'].shift(1)),
                               data['Low'].shift(1) - data['Low'], 0)
    data['DMminus'] = np.where(data['DMminus'] < 0, 0, data['DMminus'])

    # Smooth with EMA
    data['TR_EMA'] = data['TR'].ewm(span=period, adjust=False).mean()
    data['DMplus_EMA'] = data['DMplus'].ewm(span=period, adjust=False).mean()
    data['DMminus_EMA'] = data['DMminus'].ewm(span=period, adjust=False).mean()

    # Calculate DI
    data['DIplus'] = 100 * (data['DMplus_EMA'] / data['TR_EMA'])
    data['DIminus'] = 100 * (data['DMminus_EMA'] / data['TR_EMA'])

    # Calculate ADX
    data['DX'] = 100 * abs(data['DIplus'] - data['DIminus']) / (data['DIplus'] + data['DIminus'])
    data['ADX'] = data['DX'].ewm(span=period, adjust=False).mean()

    data['Signal'] = 0
    data.loc[(data['ADX'] > 25) & (data['DIplus'] > data['DIminus']), 'Signal'] = 1
    data.loc[(data['ADX'] > 25) & (data['DIplus'] < data['DIminus']), 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_trend_channel(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Trend Channel - Buy on upper band break, sell on lower"""
    period = 20
    data['Middle'] = data['Close'].rolling(window=period).mean()
    data['Upper'] = data['High'].rolling(window=period).max()
    data['Lower'] = data['Low'].rolling(window=period).min()
    data['Signal'] = 0
    data.loc[data['Close'] > data['Middle'], 'Signal'] = 1
    data.loc[data['Close'] < data['Middle'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


# =============================================================================
# MEAN-REVERSION STRATEGIES
# =============================================================================

def calculate_rsi(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """RSI Oversold/Overbought - Buy <30, Sell >70"""
    period = 14
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data['Signal'] = 0
    data.loc[data['RSI'] < 30, 'Signal'] = 1
    data.loc[data['RSI'] > 70, 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_bollinger_bands(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Bollinger Bands - Buy at lower band, sell at upper band"""
    period = 20
    data['SMA'] = data['Close'].rolling(window=period).mean()
    data['STD'] = data['Close'].rolling(window=period).std()
    data['Upper_BB'] = data['SMA'] + (2 * data['STD'])
    data['Lower_BB'] = data['SMA'] - (2 * data['STD'])
    data['Signal'] = 0
    data.loc[data['Close'] <= data['Lower_BB'], 'Signal'] = 1
    data.loc[data['Close'] >= data['Upper_BB'], 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_mean_reversion(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Mean Reversion - Buy when price is 2 std below mean"""
    period = 20
    data['Mean'] = data['Close'].rolling(window=period).mean()
    data['Std'] = data['Close'].rolling(window=period).std()
    data['Z_Score'] = (data['Close'] - data['Mean']) / data['Std']
    data['Signal'] = 0
    data.loc[data['Z_Score'] < -2, 'Signal'] = 1
    data.loc[data['Z_Score'] > 2, 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_stochastic(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Stochastic Oscillator - Oversold/Overbought"""
    period = 14
    data['L14'] = data['Low'].rolling(window=period).min()
    data['H14'] = data['High'].rolling(window=period).max()
    data['%K'] = 100 * ((data['Close'] - data['L14']) / (data['H14'] - data['L14']))
    data['%D'] = data['%K'].rolling(window=3).mean()
    data['Signal'] = 0
    data.loc[data['%K'] < 20, 'Signal'] = 1
    data.loc[data['%K'] > 80, 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_cci(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Commodity Channel Index - Mean reversion indicator"""
    period = 20
    data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
    data['SMA_TP'] = data['TP'].rolling(window=period).mean()
    data['MAD'] = data['TP'].rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    data['CCI'] = (data['TP'] - data['SMA_TP']) / (0.015 * data['MAD'])
    data['Signal'] = 0
    data.loc[data['CCI'] < -100, 'Signal'] = 1
    data.loc[data['CCI'] > 100, 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_williams_r(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Williams %R - Momentum indicator"""
    period = 14
    data['HH'] = data['High'].rolling(window=period).max()
    data['LL'] = data['Low'].rolling(window=period).min()
    data['WR'] = -100 * ((data['HH'] - data['Close']) / (data['HH'] - data['LL']))
    data['Signal'] = 0
    data.loc[data['WR'] < -80, 'Signal'] = 1
    data.loc[data['WR'] > -20, 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


# =============================================================================
# MOMENTUM STRATEGIES
# =============================================================================

def calculate_roc(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Rate of Change - Price momentum"""
    period = 12
    data['ROC'] = ((data['Close'] - data['Close'].shift(period)) / data['Close'].shift(period)) * 100
    data['Signal'] = 0
    data.loc[data['ROC'] > 0, 'Signal'] = 1
    data.loc[data['ROC'] < 0, 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_rsi_momentum(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """RSI Momentum - Buy when RSI crosses above 50"""
    period = 14
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data['Signal'] = 0
    data.loc[data['RSI'] > 50, 'Signal'] = 1
    data.loc[data['RSI'] < 50, 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_breakout_52w(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """52-Week High Breakout - Buy on new highs"""
    data['52W_High'] = data['High'].rolling(window=252).max()
    data['52W_Low'] = data['Low'].rolling(window=252).min()
    data['Signal'] = 0
    data.loc[data['Close'] >= data['52W_High'].shift(1) * 0.99, 'Signal'] = 1
    data.loc[data['Close'] <= data['52W_Low'].shift(1) * 1.01, 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_ma_momentum(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Moving Average Momentum - Price vs MA slope"""
    period = 20
    data['MA'] = data['Close'].rolling(window=period).mean()
    data['MA_Slope'] = data['MA'].diff(5)
    data['Signal'] = 0
    data.loc[(data['Close'] > data['MA']) & (data['MA_Slope'] > 0), 'Signal'] = 1
    data.loc[(data['Close'] < data['MA']) & (data['MA_Slope'] < 0), 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_price_momentum(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Price Momentum - Simple price momentum"""
    data['Momentum'] = data['Close'].diff(10)
    data['Signal'] = 0
    data.loc[data['Momentum'] > 0, 'Signal'] = 1
    data.loc[data['Momentum'] < 0, 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


# =============================================================================
# VOLATILITY STRATEGIES
# =============================================================================

def calculate_atr_breakout(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """ATR Breakout - Buy on volatility expansion"""
    period = 14
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    data['ATR'] = data['TR'].rolling(window=period).mean()
    data['ATR_MA'] = data['ATR'].rolling(window=20).mean()
    data['Signal'] = 0
    data.loc[data['ATR'] > data['ATR_MA'] * 1.5, 'Signal'] = 1
    data.loc[data['ATR'] < data['ATR_MA'] * 0.5, 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_bollinger_squeeze(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Bollinger Squeeze - Trade volatility compression/expansion"""
    period = 20
    data['SMA'] = data['Close'].rolling(window=period).mean()
    data['STD'] = data['Close'].rolling(window=period).std()
    data['BB_Width'] = (data['STD'] * 4) / data['SMA']
    data['BB_Width_MA'] = data['BB_Width'].rolling(window=period).mean()
    data['Signal'] = 0
    # Buy when bandwidth expands above average
    data.loc[data['BB_Width'] > data['BB_Width_MA'], 'Signal'] = 1
    data.loc[data['BB_Width'] < data['BB_Width_MA'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_keltner_channel(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Keltner Channel - Volatility-based trend following"""
    period = 20
    data['EMA'] = data['Close'].ewm(span=period, adjust=False).mean()
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    data['ATR'] = data['TR'].rolling(window=period).mean()
    data['Upper'] = data['EMA'] + (2 * data['ATR'])
    data['Lower'] = data['EMA'] - (2 * data['ATR'])
    data['Signal'] = 0
    data.loc[data['Close'] > data['Upper'], 'Signal'] = 1
    data.loc[data['Close'] < data['Lower'], 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


# =============================================================================
# VOLUME STRATEGIES
# =============================================================================

def calculate_volume_breakout(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Volume Breakout - High volume with price movement"""
    period = 20
    data['Volume_MA'] = data['Volume'].rolling(window=period).mean()
    data['Price_Change'] = data['Close'].pct_change()
    data['Signal'] = 0
    data.loc[(data['Volume'] > data['Volume_MA'] * 1.5) & (data['Price_Change'] > 0), 'Signal'] = 1
    data.loc[(data['Volume'] > data['Volume_MA'] * 1.5) & (data['Price_Change'] < 0), 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_obv(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """On-Balance Volume - Volume-based momentum"""
    data['OBV'] = (np.sign(data['Close'].diff()) * data['Volume']).fillna(0).cumsum()
    data['OBV_MA'] = data['OBV'].rolling(window=20).mean()
    data['Signal'] = 0
    data.loc[data['OBV'] > data['OBV_MA'], 'Signal'] = 1
    data.loc[data['OBV'] < data['OBV_MA'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_vpt(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Volume Price Trend - Cumulative volume based on price changes"""
    data['VPT'] = (data['Volume'] * data['Close'].pct_change()).fillna(0).cumsum()
    data['VPT_MA'] = data['VPT'].rolling(window=20).mean()
    data['Signal'] = 0
    data.loc[data['VPT'] > data['VPT_MA'], 'Signal'] = 1
    data.loc[data['VPT'] < data['VPT_MA'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_metrics(data: pd.DataFrame, signals: pd.Series) -> dict:
    """Calculate performance metrics for a strategy"""
    data['Returns'] = data['Close'].pct_change()
    data['Strategy_Returns'] = data['Returns'] * signals.shift(1)
    strategy_returns = data['Strategy_Returns'].dropna()

    if len(strategy_returns) == 0:
        return {
            'total_return': 0.0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'num_trades': 0
        }

    total_return = (1 + strategy_returns).prod() - 1
    winning_trades = strategy_returns[strategy_returns > 0]
    win_rate = len(winning_trades) / len(strategy_returns) if len(strategy_returns) > 0 else 0
    cumulative_returns = (1 + strategy_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min()
    sharpe_ratio = np.sqrt(252) * strategy_returns.mean() / strategy_returns.std() if strategy_returns.std() > 0 else 0
    num_trades = (signals.diff() != 0).sum()

    return {
        'total_return': float(total_return * 100),
        'win_rate': float(win_rate * 100),
        'max_drawdown': float(max_drawdown * 100),
        'sharpe_ratio': float(sharpe_ratio),
        'num_trades': int(num_trades)
    }


# Strategy mapping with categories
STRATEGY_MAP = {
    # Trend-Following
    'sma_cross_50_200': {'name': 'SMA 50/200 Cross', 'func': calculate_sma_cross_50_200, 'category': 'Trend-Following'},
    'sma_cross_20_50': {'name': 'SMA 20/50 Cross', 'func': calculate_sma_cross_20_50, 'category': 'Trend-Following'},
    'ema_cross': {'name': 'EMA 12/26 Cross', 'func': calculate_ema_cross, 'category': 'Trend-Following'},
    'macd': {'name': 'MACD Crossover', 'func': calculate_macd, 'category': 'Trend-Following'},
    'triple_ma': {'name': 'Triple Moving Average', 'func': calculate_triple_ma, 'category': 'Trend-Following'},
    'donchian': {'name': 'Donchian Breakout', 'func': calculate_donchian_breakout, 'category': 'Trend-Following'},
    'adx_trend': {'name': 'ADX Trend', 'func': calculate_adx_trend, 'category': 'Trend-Following'},
    'trend_channel': {'name': 'Trend Channel', 'func': calculate_trend_channel, 'category': 'Trend-Following'},

    # Mean-Reversion
    'rsi': {'name': 'RSI Oversold/Overbought', 'func': calculate_rsi, 'category': 'Mean-Reversion'},
    'bollinger': {'name': 'Bollinger Bands', 'func': calculate_bollinger_bands, 'category': 'Mean-Reversion'},
    'mean_reversion': {'name': 'Mean Reversion', 'func': calculate_mean_reversion, 'category': 'Mean-Reversion'},
    'stochastic': {'name': 'Stochastic Oscillator', 'func': calculate_stochastic, 'category': 'Mean-Reversion'},
    'cci': {'name': 'CCI', 'func': calculate_cci, 'category': 'Mean-Reversion'},
    'williams_r': {'name': 'Williams %R', 'func': calculate_williams_r, 'category': 'Mean-Reversion'},

    # Momentum
    'roc': {'name': 'Rate of Change', 'func': calculate_roc, 'category': 'Momentum'},
    'rsi_momentum': {'name': 'RSI Momentum', 'func': calculate_rsi_momentum, 'category': 'Momentum'},
    'breakout_52w': {'name': '52-Week High Breakout', 'func': calculate_breakout_52w, 'category': 'Momentum'},
    'ma_momentum': {'name': 'MA Momentum', 'func': calculate_ma_momentum, 'category': 'Momentum'},
    'price_momentum': {'name': 'Price Momentum', 'func': calculate_price_momentum, 'category': 'Momentum'},

    # Volatility
    'atr_breakout': {'name': 'ATR Breakout', 'func': calculate_atr_breakout, 'category': 'Volatility'},
    'bollinger_squeeze': {'name': 'Bollinger Squeeze', 'func': calculate_bollinger_squeeze, 'category': 'Volatility'},
    'keltner': {'name': 'Keltner Channel', 'func': calculate_keltner_channel, 'category': 'Volatility'},

    # Volume
    'volume_breakout': {'name': 'Volume Breakout', 'func': calculate_volume_breakout, 'category': 'Volume'},
    'obv': {'name': 'On-Balance Volume', 'func': calculate_obv, 'category': 'Volume'},
    'vpt': {'name': 'Volume Price Trend', 'func': calculate_vpt, 'category': 'Volume'},
}
