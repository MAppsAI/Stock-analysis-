import pandas as pd
import numpy as np
from typing import Tuple, List


def extract_signals(data: pd.DataFrame, position_col: str = 'Position') -> List[dict]:
    """Helper function to extract buy/sell signals from position changes

    Position = Signal.diff() captures transitions:
    - Position = 1: 0→1 (enter long) OR -1→0 (exit short to neutral)
    - Position = 2: -1→1 (exit short + enter long)
    - Position = -1: 1→0 (exit long to neutral) OR 0→-1 (enter short)
    - Position = -2: 1→-1 (exit long + enter short)

    We need to look at both current Signal and Position to determine action type.
    """
    signals = []

    # Get previous signal to understand the transition context
    data['Prev_Signal'] = data['Signal'].shift(1).fillna(0)

    for idx, row in data.iterrows():
        pos = row[position_col]
        curr_signal = row['Signal']
        prev_signal = row['Prev_Signal']

        if pd.isna(pos) or pos == 0:
            continue

        # LONG ENTRIES: Transitions that result in Signal = 1
        if pos == 1 and curr_signal == 1:  # 0→1: Enter long from neutral
            signals.append({
                'date': idx.strftime('%Y-%m-%d'),
                'price': float(row['Close']),
                'type': 'buy'
            })
        elif pos == 2:  # -1→1: Exit short + Enter long
            signals.append({
                'date': idx.strftime('%Y-%m-%d'),
                'price': float(row['Close']),
                'type': 'buy'
            })
        # SHORT ENTRIES / LONG EXITS: Transitions that result in Signal = -1 or 0
        elif pos == -1 and curr_signal == -1:  # Either 1→-1 or 0→-1: Enter short
            signals.append({
                'date': idx.strftime('%Y-%m-%d'),
                'price': float(row['Close']),
                'type': 'sell'
            })
        elif pos == -1 and curr_signal == 0:  # 1→0: Exit long to neutral
            signals.append({
                'date': idx.strftime('%Y-%m-%d'),
                'price': float(row['Close']),
                'type': 'sell'
            })
        elif pos == -2:  # 1→-1: Exit long + Enter short
            signals.append({
                'date': idx.strftime('%Y-%m-%d'),
                'price': float(row['Close']),
                'type': 'sell'
            })
        # Note: pos == 1 with curr_signal == 0 (-1→0: exit short) is NOT included
        # as it's not a traditional "buy" - it's just covering a short position

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


# =============================================================================
# ADDITIONAL STRATEGIES FOR V3.0
# =============================================================================

def calculate_ichimoku(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Ichimoku Cloud - Japanese trend indicator"""
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
    nine_period_high = data['High'].rolling(window=9).max()
    nine_period_low = data['Low'].rolling(window=9).min()
    data['Tenkan'] = (nine_period_high + nine_period_low) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low)/2
    period26_high = data['High'].rolling(window=26).max()
    period26_low = data['Low'].rolling(window=26).min()
    data['Kijun'] = (period26_high + period26_low) / 2

    data['Signal'] = 0
    data.loc[data['Tenkan'] > data['Kijun'], 'Signal'] = 1
    data.loc[data['Tenkan'] < data['Kijun'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_vwap_cross(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """VWAP Cross - Volume Weighted Average Price"""
    data['VWAP'] = (data['Volume'] * (data['High'] + data['Low'] + data['Close']) / 3).cumsum() / data['Volume'].cumsum()
    data['Signal'] = 0
    data.loc[data['Close'] > data['VWAP'], 'Signal'] = 1
    data.loc[data['Close'] < data['VWAP'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_sma_cross_10_20(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """SMA 10/20 Cross - Short-term crossover"""
    data['SMA_Short'] = data['Close'].rolling(window=10).mean()
    data['SMA_Long'] = data['Close'].rolling(window=20).mean()
    data['Signal'] = 0
    data.loc[data['SMA_Short'] > data['SMA_Long'], 'Signal'] = 1
    data.loc[data['SMA_Short'] < data['SMA_Long'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_ema_cross_8_21(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """EMA 8/21 Cross - Fibonacci-based crossover"""
    data['EMA_Short'] = data['Close'].ewm(span=8, adjust=False).mean()
    data['EMA_Long'] = data['Close'].ewm(span=21, adjust=False).mean()
    data['Signal'] = 0
    data.loc[data['EMA_Short'] > data['EMA_Long'], 'Signal'] = 1
    data.loc[data['EMA_Short'] < data['EMA_Long'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_price_above_vwap(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Price Above VWAP - Intraday indicator"""
    data['VWAP'] = (data['Volume'] * (data['High'] + data['Low'] + data['Close']) / 3).cumsum() / data['Volume'].cumsum()
    data['Signal'] = 0
    data.loc[data['Close'] > data['VWAP'], 'Signal'] = 1
    data.loc[data['Close'] < data['VWAP'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_macd_histogram(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """MACD Histogram - Trade histogram crosses"""
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['Histogram'] = data['MACD'] - data['Signal_Line']
    data['Signal'] = 0
    data.loc[data['Histogram'] > 0, 'Signal'] = 1
    data.loc[data['Histogram'] < 0, 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_supertrend(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Supertrend - ATR-based trend following"""
    period = 10
    multiplier = 3

    # Calculate ATR
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    data['ATR'] = data['TR'].rolling(window=period).mean()

    # Calculate bands
    data['HL2'] = (data['High'] + data['Low']) / 2
    data['Upper_ST'] = data['HL2'] + (multiplier * data['ATR'])
    data['Lower_ST'] = data['HL2'] - (multiplier * data['ATR'])

    data['Signal'] = 0
    data.loc[data['Close'] > data['Lower_ST'], 'Signal'] = 1
    data.loc[data['Close'] < data['Upper_ST'], 'Signal'] = -1
    data['Signal'] = data['Signal'].replace(0, method='ffill').fillna(0)
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_hull_ma(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Hull Moving Average - Reduced lag MA"""
    period = 20
    wma_half = data['Close'].rolling(window=int(period/2)).mean()
    wma_full = data['Close'].rolling(window=period).mean()
    raw_hma = 2 * wma_half - wma_full
    data['HMA'] = raw_hma.rolling(window=int(np.sqrt(period))).mean()
    data['Signal'] = 0
    data.loc[data['Close'] > data['HMA'], 'Signal'] = 1
    data.loc[data['Close'] < data['HMA'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_dmi_cross(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """DMI Cross - Directional Movement Index crossover"""
    period = 14
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    data['DMplus'] = np.where((data['High'] - data['High'].shift(1)) > (data['Low'].shift(1) - data['Low']),
                              data['High'] - data['High'].shift(1), 0)
    data['DMplus'] = np.where(data['DMplus'] < 0, 0, data['DMplus'])
    data['DMminus'] = np.where((data['Low'].shift(1) - data['Low']) > (data['High'] - data['High'].shift(1)),
                               data['Low'].shift(1) - data['Low'], 0)
    data['DMminus'] = np.where(data['DMminus'] < 0, 0, data['DMminus'])
    data['TR_EMA'] = data['TR'].ewm(span=period, adjust=False).mean()
    data['DMplus_EMA'] = data['DMplus'].ewm(span=period, adjust=False).mean()
    data['DMminus_EMA'] = data['DMminus'].ewm(span=period, adjust=False).mean()
    data['DIplus'] = 100 * (data['DMplus_EMA'] / data['TR_EMA'])
    data['DIminus'] = 100 * (data['DMminus_EMA'] / data['TR_EMA'])
    data['Signal'] = 0
    data.loc[data['DIplus'] > data['DIminus'], 'Signal'] = 1
    data.loc[data['DIplus'] < data['DIminus'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


def calculate_aroon(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    """Aroon Indicator - Trend strength and direction"""
    period = 25
    data['Aroon_Up'] = data['High'].rolling(window=period + 1).apply(lambda x: x.argmax(), raw=False) / period * 100
    data['Aroon_Down'] = data['Low'].rolling(window=period + 1).apply(lambda x: x.argmin(), raw=False) / period * 100
    data['Signal'] = 0
    data.loc[data['Aroon_Up'] > data['Aroon_Down'], 'Signal'] = 1
    data.loc[data['Aroon_Up'] < data['Aroon_Down'], 'Signal'] = -1
    data['Position'] = data['Signal'].diff()
    return data['Signal'], extract_signals(data)


# =============================================================================
# VOLUME STRATEGIES
# =============================================================================


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
            'num_trades': 0,
            'equity_curve': []
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

    # Build equity curve data points
    equity_curve = []
    for idx, value in cumulative_returns.items():
        equity_curve.append({
            'date': idx.strftime('%Y-%m-%d'),
            'equity': float(value)
        })

    return {
        'total_return': float(total_return * 100),
        'win_rate': float(win_rate * 100),
        'max_drawdown': float(max_drawdown * 100),
        'sharpe_ratio': float(sharpe_ratio),
        'num_trades': int(num_trades),
        'equity_curve': equity_curve
    }


def calculate_buy_hold_metrics(data: pd.DataFrame) -> dict:
    """Calculate buy and hold performance metrics (baseline for comparison)"""
    # Buy and hold means always holding a position (signal = 1)
    data['Returns'] = data['Close'].pct_change()
    returns = data['Returns'].dropna()

    if len(returns) == 0:
        return {
            'total_return': 0.0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'num_trades': 1,  # Buy once and hold
            'equity_curve': []
        }

    total_return = (1 + returns).prod() - 1
    winning_days = returns[returns > 0]
    win_rate = len(winning_days) / len(returns) if len(returns) > 0 else 0
    cumulative_returns = (1 + returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min()
    sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0

    # Build equity curve data points
    equity_curve = []
    for idx, value in cumulative_returns.items():
        equity_curve.append({
            'date': idx.strftime('%Y-%m-%d'),
            'equity': float(value)
        })

    return {
        'total_return': float(total_return * 100),
        'win_rate': float(win_rate * 100),
        'max_drawdown': float(max_drawdown * 100),
        'sharpe_ratio': float(sharpe_ratio),
        'num_trades': 1,
        'equity_curve': equity_curve
    }


# =============================================================================
# ENTRY/EXIT SEPARATION SYSTEM - Mix and Match Strategies
# =============================================================================

def combine_entry_exit(entry_func, exit_func):
    """Combine an entry condition with an exit condition to create a complete strategy"""
    def combined_strategy(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
        # Calculate entry and exit conditions
        entry_condition = entry_func(data)
        exit_condition = exit_func(data)

        # Initialize signal
        data['Signal'] = 0
        data['Entry_Flag'] = entry_condition
        data['Exit_Flag'] = exit_condition

        # Track position state
        in_position = False
        signals = []

        for i in range(len(data)):
            if not in_position and data['Entry_Flag'].iloc[i]:
                # Enter position
                data.loc[data.index[i], 'Signal'] = 1
                in_position = True
            elif in_position and data['Exit_Flag'].iloc[i]:
                # Exit position
                data.loc[data.index[i], 'Signal'] = -1
                in_position = False
            elif in_position:
                # Stay in position
                data.loc[data.index[i], 'Signal'] = 1
            # else: stay out of position (Signal = 0)

        # Convert to position changes
        data['Position'] = data['Signal'].diff()

        return data['Signal'], extract_signals(data)

    return combined_strategy


# =============================================================================
# ENTRY CONDITIONS
# =============================================================================

def entry_sma_cross_bullish(data: pd.DataFrame, short=50, long=200) -> pd.Series:
    """Entry when short SMA crosses above long SMA"""
    data['SMA_Short'] = data['Close'].rolling(window=short).mean()
    data['SMA_Long'] = data['Close'].rolling(window=long).mean()
    return data['SMA_Short'] > data['SMA_Long']


def entry_ema_cross_bullish(data: pd.DataFrame, short=12, long=26) -> pd.Series:
    """Entry when short EMA crosses above long EMA"""
    data['EMA_Short'] = data['Close'].ewm(span=short, adjust=False).mean()
    data['EMA_Long'] = data['Close'].ewm(span=long, adjust=False).mean()
    return data['EMA_Short'] > data['EMA_Long']


def entry_rsi_oversold(data: pd.DataFrame, period=14, threshold=30) -> pd.Series:
    """Entry when RSI is oversold"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data['RSI'] < threshold


def entry_bollinger_lower(data: pd.DataFrame, period=20, std_dev=2) -> pd.Series:
    """Entry when price touches lower Bollinger Band"""
    data['SMA'] = data['Close'].rolling(window=period).mean()
    data['STD'] = data['Close'].rolling(window=period).std()
    data['Lower_BB'] = data['SMA'] - (std_dev * data['STD'])
    return data['Close'] <= data['Lower_BB']


def entry_macd_cross_bullish(data: pd.DataFrame) -> pd.Series:
    """Entry when MACD crosses above signal line"""
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    return data['MACD'] > data['Signal_Line']


def entry_stochastic_oversold(data: pd.DataFrame, period=14, threshold=20) -> pd.Series:
    """Entry when Stochastic is oversold"""
    data['L14'] = data['Low'].rolling(window=period).min()
    data['H14'] = data['High'].rolling(window=period).max()
    data['%K'] = 100 * ((data['Close'] - data['L14']) / (data['H14'] - data['L14']))
    return data['%K'] < threshold


def entry_volume_breakout_bullish(data: pd.DataFrame, period=20, vol_mult=1.5) -> pd.Series:
    """Entry on high volume with positive price change"""
    data['Volume_MA'] = data['Volume'].rolling(window=period).mean()
    data['Price_Change'] = data['Close'].pct_change()
    return (data['Volume'] > data['Volume_MA'] * vol_mult) & (data['Price_Change'] > 0)


def entry_donchian_breakout(data: pd.DataFrame, period=20) -> pd.Series:
    """Entry on Donchian channel upper breakout"""
    data['Upper'] = data['High'].rolling(window=period).max()
    return data['Close'] >= data['Upper'].shift(1)


def entry_price_above_vwap(data: pd.DataFrame) -> pd.Series:
    """Entry when price crosses above VWAP"""
    data['VWAP'] = (data['Volume'] * (data['High'] + data['Low'] + data['Close']) / 3).cumsum() / data['Volume'].cumsum()
    return data['Close'] > data['VWAP']


def entry_adx_strong_trend(data: pd.DataFrame, period=14, threshold=25) -> pd.Series:
    """Entry when ADX shows strong trend and +DI > -DI"""
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

    data['TR_EMA'] = data['TR'].ewm(span=period, adjust=False).mean()
    data['DMplus_EMA'] = data['DMplus'].ewm(span=period, adjust=False).mean()
    data['DMminus_EMA'] = data['DMminus'].ewm(span=period, adjust=False).mean()

    data['DIplus'] = 100 * (data['DMplus_EMA'] / data['TR_EMA'])
    data['DIminus'] = 100 * (data['DMminus_EMA'] / data['TR_EMA'])

    data['DX'] = 100 * abs(data['DIplus'] - data['DIminus']) / (data['DIplus'] + data['DIminus'])
    data['ADX'] = data['DX'].ewm(span=period, adjust=False).mean()

    return (data['ADX'] > threshold) & (data['DIplus'] > data['DIminus'])


def entry_cci_oversold(data: pd.DataFrame, period=20, threshold=-100) -> pd.Series:
    """Entry when CCI is oversold"""
    data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
    data['SMA_TP'] = data['TP'].rolling(window=period).mean()
    data['MAD'] = data['TP'].rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    data['CCI'] = (data['TP'] - data['SMA_TP']) / (0.015 * data['MAD'])
    return data['CCI'] < threshold


def entry_roc_positive(data: pd.DataFrame, period=12) -> pd.Series:
    """Entry when Rate of Change is positive"""
    data['ROC'] = ((data['Close'] - data['Close'].shift(period)) / data['Close'].shift(period)) * 100
    return data['ROC'] > 0


# =============================================================================
# EXIT CONDITIONS
# =============================================================================

def exit_sma_cross_bearish(data: pd.DataFrame, short=50, long=200) -> pd.Series:
    """Exit when short SMA crosses below long SMA"""
    data['SMA_Short'] = data['Close'].rolling(window=short).mean()
    data['SMA_Long'] = data['Close'].rolling(window=long).mean()
    return data['SMA_Short'] < data['SMA_Long']


def exit_ema_cross_bearish(data: pd.DataFrame, short=12, long=26) -> pd.Series:
    """Exit when short EMA crosses below long EMA"""
    data['EMA_Short'] = data['Close'].ewm(span=short, adjust=False).mean()
    data['EMA_Long'] = data['Close'].ewm(span=long, adjust=False).mean()
    return data['EMA_Short'] < data['EMA_Long']


def exit_rsi_overbought(data: pd.DataFrame, period=14, threshold=70) -> pd.Series:
    """Exit when RSI is overbought"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data['RSI'] > threshold


def exit_bollinger_upper(data: pd.DataFrame, period=20, std_dev=2) -> pd.Series:
    """Exit when price touches upper Bollinger Band"""
    data['SMA'] = data['Close'].rolling(window=period).mean()
    data['STD'] = data['Close'].rolling(window=period).std()
    data['Upper_BB'] = data['SMA'] + (std_dev * data['STD'])
    return data['Close'] >= data['Upper_BB']


def exit_macd_cross_bearish(data: pd.DataFrame) -> pd.Series:
    """Exit when MACD crosses below signal line"""
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    return data['MACD'] < data['Signal_Line']


def exit_stochastic_overbought(data: pd.DataFrame, period=14, threshold=80) -> pd.Series:
    """Exit when Stochastic is overbought"""
    data['L14'] = data['Low'].rolling(window=period).min()
    data['H14'] = data['High'].rolling(window=period).max()
    data['%K'] = 100 * ((data['Close'] - data['L14']) / (data['H14'] - data['L14']))
    return data['%K'] > threshold


def exit_volume_breakout_bearish(data: pd.DataFrame, period=20, vol_mult=1.5) -> pd.Series:
    """Exit on high volume with negative price change"""
    data['Volume_MA'] = data['Volume'].rolling(window=period).mean()
    data['Price_Change'] = data['Close'].pct_change()
    return (data['Volume'] > data['Volume_MA'] * vol_mult) & (data['Price_Change'] < 0)


def exit_donchian_breakdown(data: pd.DataFrame, period=20) -> pd.Series:
    """Exit on Donchian channel lower breakdown"""
    data['Lower'] = data['Low'].rolling(window=period).min()
    return data['Close'] <= data['Lower'].shift(1)


def exit_price_below_vwap(data: pd.DataFrame) -> pd.Series:
    """Exit when price crosses below VWAP"""
    data['VWAP'] = (data['Volume'] * (data['High'] + data['Low'] + data['Close']) / 3).cumsum() / data['Volume'].cumsum()
    return data['Close'] < data['VWAP']


def exit_adx_weak_trend(data: pd.DataFrame, period=14, threshold=25) -> pd.Series:
    """Exit when ADX shows weak trend or -DI > +DI"""
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

    data['TR_EMA'] = data['TR'].ewm(span=period, adjust=False).mean()
    data['DMplus_EMA'] = data['DMplus'].ewm(span=period, adjust=False).mean()
    data['DMminus_EMA'] = data['DMminus'].ewm(span=period, adjust=False).mean()

    data['DIplus'] = 100 * (data['DMplus_EMA'] / data['TR_EMA'])
    data['DIminus'] = 100 * (data['DMminus_EMA'] / data['TR_EMA'])

    data['DX'] = 100 * abs(data['DIplus'] - data['DIminus']) / (data['DIplus'] + data['DIminus'])
    data['ADX'] = data['DX'].ewm(span=period, adjust=False).mean()

    return (data['ADX'] < threshold) | (data['DIplus'] < data['DIminus'])


def exit_cci_overbought(data: pd.DataFrame, period=20, threshold=100) -> pd.Series:
    """Exit when CCI is overbought"""
    data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
    data['SMA_TP'] = data['TP'].rolling(window=period).mean()
    data['MAD'] = data['TP'].rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    data['CCI'] = (data['TP'] - data['SMA_TP']) / (0.015 * data['MAD'])
    return data['CCI'] > threshold


def exit_roc_negative(data: pd.DataFrame, period=12) -> pd.Series:
    """Exit when Rate of Change is negative"""
    data['ROC'] = ((data['Close'] - data['Close'].shift(period)) / data['Close'].shift(period)) * 100
    return data['ROC'] < 0


def exit_trailing_stop(data: pd.DataFrame, stop_pct=5.0) -> pd.Series:
    """Exit on trailing stop loss"""
    data['Trailing_High'] = data['Close'].expanding().max()
    data['Stop_Level'] = data['Trailing_High'] * (1 - stop_pct / 100)
    return data['Close'] < data['Stop_Level']


def exit_take_profit(data: pd.DataFrame, profit_pct=10.0) -> pd.Series:
    """Exit on take profit target"""
    # This is a simplified version - in practice would need to track entry price
    data['MA_20'] = data['Close'].rolling(window=20).mean()
    data['Profit_Target'] = data['MA_20'] * (1 + profit_pct / 100)
    return data['Close'] > data['Profit_Target']


# =============================================================================
# ENTRY/EXIT MAPPINGS
# =============================================================================

ENTRY_CONDITIONS = {
    'sma_cross': {'name': 'SMA Cross', 'func': entry_sma_cross_bullish},
    'ema_cross': {'name': 'EMA Cross', 'func': entry_ema_cross_bullish},
    'rsi_oversold': {'name': 'RSI Oversold', 'func': entry_rsi_oversold},
    'bollinger_lower': {'name': 'Bollinger Lower', 'func': entry_bollinger_lower},
    'macd_cross': {'name': 'MACD Cross', 'func': entry_macd_cross_bullish},
    'stochastic_oversold': {'name': 'Stochastic Oversold', 'func': entry_stochastic_oversold},
    'volume_breakout': {'name': 'Volume Breakout', 'func': entry_volume_breakout_bullish},
    'donchian_breakout': {'name': 'Donchian Breakout', 'func': entry_donchian_breakout},
    'price_above_vwap': {'name': 'Price Above VWAP', 'func': entry_price_above_vwap},
    'adx_strong': {'name': 'ADX Strong Trend', 'func': entry_adx_strong_trend},
    'cci_oversold': {'name': 'CCI Oversold', 'func': entry_cci_oversold},
    'roc_positive': {'name': 'ROC Positive', 'func': entry_roc_positive},
}

EXIT_CONDITIONS = {
    'sma_cross': {'name': 'SMA Cross', 'func': exit_sma_cross_bearish},
    'ema_cross': {'name': 'EMA Cross', 'func': exit_ema_cross_bearish},
    'rsi_overbought': {'name': 'RSI Overbought', 'func': exit_rsi_overbought},
    'bollinger_upper': {'name': 'Bollinger Upper', 'func': exit_bollinger_upper},
    'macd_cross': {'name': 'MACD Cross', 'func': exit_macd_cross_bearish},
    'stochastic_overbought': {'name': 'Stochastic Overbought', 'func': exit_stochastic_overbought},
    'volume_breakout': {'name': 'Volume Breakout', 'func': exit_volume_breakout_bearish},
    'donchian_breakdown': {'name': 'Donchian Breakdown', 'func': exit_donchian_breakdown},
    'price_below_vwap': {'name': 'Price Below VWAP', 'func': exit_price_below_vwap},
    'adx_weak': {'name': 'ADX Weak Trend', 'func': exit_adx_weak_trend},
    'cci_overbought': {'name': 'CCI Overbought', 'func': exit_cci_overbought},
    'roc_negative': {'name': 'ROC Negative', 'func': exit_roc_negative},
    'trailing_stop': {'name': 'Trailing Stop', 'func': exit_trailing_stop},
    'take_profit': {'name': 'Take Profit', 'func': exit_take_profit},
}


def generate_combined_strategies():
    """Generate all combinations of entry and exit strategies"""
    combined = {}

    for entry_key, entry_info in ENTRY_CONDITIONS.items():
        for exit_key, exit_info in EXIT_CONDITIONS.items():
            # Create unique strategy ID
            strategy_id = f"combo_{entry_key}_entry_{exit_key}_exit"

            # Create strategy name
            strategy_name = f"{entry_info['name']} Entry + {exit_info['name']} Exit"

            # Determine category based on entry condition
            if entry_key in ['sma_cross', 'ema_cross', 'macd_cross', 'adx_strong', 'donchian_breakout']:
                category = 'Trend-Following'
            elif entry_key in ['rsi_oversold', 'bollinger_lower', 'stochastic_oversold', 'cci_oversold']:
                category = 'Mean-Reversion'
            elif entry_key in ['roc_positive', 'volume_breakout']:
                category = 'Momentum'
            else:
                category = 'Hybrid'

            # Create combined strategy function
            combined[strategy_id] = {
                'name': strategy_name,
                'func': combine_entry_exit(entry_info['func'], exit_info['func']),
                'category': f'{category} (Combined)'
            }

    return combined


# Original strategy mapping with categories
ORIGINAL_STRATEGIES = {
    # Trend-Following (15 strategies)
    'sma_cross_50_200': {'name': 'SMA 50/200 Cross', 'func': calculate_sma_cross_50_200, 'category': 'Trend-Following'},
    'sma_cross_20_50': {'name': 'SMA 20/50 Cross', 'func': calculate_sma_cross_20_50, 'category': 'Trend-Following'},
    'sma_cross_10_20': {'name': 'SMA 10/20 Cross', 'func': calculate_sma_cross_10_20, 'category': 'Trend-Following'},
    'ema_cross': {'name': 'EMA 12/26 Cross', 'func': calculate_ema_cross, 'category': 'Trend-Following'},
    'ema_cross_8_21': {'name': 'EMA 8/21 Cross', 'func': calculate_ema_cross_8_21, 'category': 'Trend-Following'},
    'macd': {'name': 'MACD Crossover', 'func': calculate_macd, 'category': 'Trend-Following'},
    'macd_histogram': {'name': 'MACD Histogram', 'func': calculate_macd_histogram, 'category': 'Trend-Following'},
    'triple_ma': {'name': 'Triple Moving Average', 'func': calculate_triple_ma, 'category': 'Trend-Following'},
    'donchian': {'name': 'Donchian Breakout', 'func': calculate_donchian_breakout, 'category': 'Trend-Following'},
    'adx_trend': {'name': 'ADX Trend', 'func': calculate_adx_trend, 'category': 'Trend-Following'},
    'trend_channel': {'name': 'Trend Channel', 'func': calculate_trend_channel, 'category': 'Trend-Following'},
    'supertrend': {'name': 'Supertrend', 'func': calculate_supertrend, 'category': 'Trend-Following'},
    'hull_ma': {'name': 'Hull Moving Average', 'func': calculate_hull_ma, 'category': 'Trend-Following'},
    'dmi_cross': {'name': 'DMI Cross', 'func': calculate_dmi_cross, 'category': 'Trend-Following'},
    'aroon': {'name': 'Aroon Indicator', 'func': calculate_aroon, 'category': 'Trend-Following'},

    # Mean-Reversion (6 strategies)
    'rsi': {'name': 'RSI Oversold/Overbought', 'func': calculate_rsi, 'category': 'Mean-Reversion'},
    'bollinger': {'name': 'Bollinger Bands', 'func': calculate_bollinger_bands, 'category': 'Mean-Reversion'},
    'mean_reversion': {'name': 'Mean Reversion', 'func': calculate_mean_reversion, 'category': 'Mean-Reversion'},
    'stochastic': {'name': 'Stochastic Oscillator', 'func': calculate_stochastic, 'category': 'Mean-Reversion'},
    'cci': {'name': 'CCI', 'func': calculate_cci, 'category': 'Mean-Reversion'},
    'williams_r': {'name': 'Williams %R', 'func': calculate_williams_r, 'category': 'Mean-Reversion'},

    # Momentum (5 strategies)
    'roc': {'name': 'Rate of Change', 'func': calculate_roc, 'category': 'Momentum'},
    'rsi_momentum': {'name': 'RSI Momentum', 'func': calculate_rsi_momentum, 'category': 'Momentum'},
    'breakout_52w': {'name': '52-Week High Breakout', 'func': calculate_breakout_52w, 'category': 'Momentum'},
    'ma_momentum': {'name': 'MA Momentum', 'func': calculate_ma_momentum, 'category': 'Momentum'},
    'price_momentum': {'name': 'Price Momentum', 'func': calculate_price_momentum, 'category': 'Momentum'},

    # Volatility (3 strategies)
    'atr_breakout': {'name': 'ATR Breakout', 'func': calculate_atr_breakout, 'category': 'Volatility'},
    'bollinger_squeeze': {'name': 'Bollinger Squeeze', 'func': calculate_bollinger_squeeze, 'category': 'Volatility'},
    'keltner': {'name': 'Keltner Channel', 'func': calculate_keltner_channel, 'category': 'Volatility'},

    # Volume (5 strategies)
    'volume_breakout': {'name': 'Volume Breakout', 'func': calculate_volume_breakout, 'category': 'Volume'},
    'obv': {'name': 'On-Balance Volume', 'func': calculate_obv, 'category': 'Volume'},
    'vpt': {'name': 'Volume Price Trend', 'func': calculate_vpt, 'category': 'Volume'},
    'vwap_cross': {'name': 'VWAP Cross', 'func': calculate_vwap_cross, 'category': 'Volume'},
    'price_above_vwap': {'name': 'Price Above VWAP', 'func': calculate_price_above_vwap, 'category': 'Volume'},

    # Advanced/Hybrid (2 strategies)
    'ichimoku': {'name': 'Ichimoku Cloud', 'func': calculate_ichimoku, 'category': 'Advanced'},
}

# Generate combined strategies (Entry/Exit Mix & Match)
# This creates 12 entry conditions × 14 exit conditions = 168 combined strategies
COMBINED_STRATEGIES = generate_combined_strategies()

# Import Minervini SEPA strategies
try:
    from minervini_strategy import MINERVINI_STRATEGY_MAP
    logger = __import__('logging').getLogger(__name__)
    logger.info(f"Loaded {len(MINERVINI_STRATEGY_MAP)} Minervini SEPA strategies")
except ImportError as e:
    logger = __import__('logging').getLogger(__name__)
    logger.warning(f"Could not load Minervini strategies: {e}")
    MINERVINI_STRATEGY_MAP = {}

# Merge all strategies into the final STRATEGY_MAP
STRATEGY_MAP = {**ORIGINAL_STRATEGIES, **COMBINED_STRATEGIES, **MINERVINI_STRATEGY_MAP}
